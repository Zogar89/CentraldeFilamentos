from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html.parser import HTMLParser
import json
import re
from urllib.parse import urljoin, urlparse

import requests

from centraldefilamentos.models import NormalizedFields, RawStockItem
from centraldefilamentos.normalize import build_product_id, normalize_record

BASE_URL = "https://grilon3.com.ar/productos/"
SITEMAP_URL = "https://grilon3.com.ar/product-sitemap.xml"
EMPTY_ENRICHMENT = {"manufacturer_product_url": "", "image_url": "", "image_source": "", "pantone": "", "sku": "", "ean": ""}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
COLOR_OPTIONAL_MATERIALS = {"PVA"}


@dataclass(frozen=True)
class CatalogProduct:
    product_id: str
    title: str
    product_url: str
    image_url: str
    pantone: str = ""
    sku: str = ""
    ean: str = ""


@dataclass(frozen=True)
class CatalogPage:
    products: tuple[CatalogProduct, ...]
    pagination_urls: tuple[str, ...]
    reported_total: int | None


@dataclass(frozen=True)
class CatalogProductDetail:
    product_url: str
    category_path: tuple[str, ...]
    gallery_image_urls: tuple[str, ...]
    pantone: str = ""
    sku: str = ""
    ean: str = ""

    @property
    def primary_image_url(self) -> str:
        return self.gallery_image_urls[0] if self.gallery_image_urls else ""


@dataclass(frozen=True)
class CatalogRejection:
    title: str
    url: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "url": self.url,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class CatalogPageAudit:
    page_url: str
    page: CatalogPage
    raw_link_count: int
    raw_unique_url_count: int
    raw_urls: tuple[str, ...]
    rejections: tuple[CatalogRejection, ...]


@dataclass(frozen=True)
class ActiveCatalogAudit:
    catalog: dict[str, CatalogProduct]
    reported_total: int | None
    pages: tuple[CatalogPageAudit, ...]
    raw_link_count: int
    raw_unique_url_count: int
    rejections: tuple[CatalogRejection, ...]


@dataclass(frozen=True)
class SitemapCatalogAudit:
    catalog: dict[str, CatalogProduct]
    raw_loc_count: int
    raw_unique_url_count: int
    rejections: tuple[CatalogRejection, ...]


def fetch_grilon3_catalog(products_url: str = BASE_URL, timeout_seconds: int = 30) -> dict[str, CatalogProduct]:
    response = requests.get(products_url, timeout=timeout_seconds)
    response.raise_for_status()
    return parse_grilon3_catalog(response.text, base_url=products_url)


def fetch_grilon3_active_catalog(
    products_url: str = BASE_URL,
    timeout_seconds: int = 30,
) -> tuple[dict[str, CatalogProduct], int | None]:
    audit = fetch_grilon3_active_catalog_audit(products_url, timeout_seconds)
    return audit.catalog, audit.reported_total


def fetch_grilon3_active_catalog_audit(
    products_url: str = BASE_URL,
    timeout_seconds: int = 30,
) -> ActiveCatalogAudit:
    response = requests.get(products_url, timeout=timeout_seconds)
    response.raise_for_status()
    first_audit = parse_grilon3_catalog_page_audit(response.text, base_url=products_url)

    page_audits = [first_audit]
    visited_page_urls = {_canonical_product_url(products_url)}
    pending_page_urls = list(first_audit.page.pagination_urls)
    while pending_page_urls:
        page_url = pending_page_urls.pop(0)
        canonical_page_url = _canonical_product_url(page_url)
        if canonical_page_url in visited_page_urls:
            continue
        visited_page_urls.add(canonical_page_url)
        if not _is_allowed_catalog_page_url(page_url, products_url):
            continue
        response = requests.get(page_url, timeout=timeout_seconds)
        response.raise_for_status()
        page_audit = parse_grilon3_catalog_page_audit(response.text, base_url=page_url)
        page_audits.append(page_audit)
        pending_page_urls.extend(page_audit.page.pagination_urls)

    catalog: dict[str, CatalogProduct] = {}
    seen_urls: set[str] = set()
    for page_audit in page_audits:
        for product in page_audit.page.products:
            canonical_url = _canonical_product_url(product.product_url)
            if canonical_url in seen_urls:
                continue
            seen_urls.add(canonical_url)
            canonical_product = CatalogProduct(
                product_id=product.product_id,
                title=product.title,
                product_url=canonical_url,
                image_url=product.image_url,
                pantone=product.pantone,
                sku=product.sku,
                ean=product.ean,
            )
            key = _unique_catalog_key(catalog, product.product_id, canonical_url)
            catalog[key] = canonical_product

    raw_urls = {
        url
        for page_audit in page_audits
        for url in page_audit.raw_urls
    }
    return ActiveCatalogAudit(
        catalog=catalog,
        reported_total=first_audit.page.reported_total,
        pages=tuple(page_audits),
        raw_link_count=sum(page.raw_link_count for page in page_audits),
        raw_unique_url_count=len(raw_urls),
        rejections=tuple(
            rejection
            for page in page_audits
            for rejection in page.rejections
        ),
    )


def fetch_grilon3_sitemap_catalog(sitemap_url: str = SITEMAP_URL, timeout_seconds: int = 30) -> dict[str, CatalogProduct]:
    response = requests.get(sitemap_url, timeout=timeout_seconds)
    response.raise_for_status()
    return parse_grilon3_sitemap_audit(response.text).catalog


def fetch_grilon3_sitemap_catalog_audit(
    sitemap_url: str = SITEMAP_URL,
    timeout_seconds: int = 30,
) -> SitemapCatalogAudit:
    response = requests.get(sitemap_url, timeout=timeout_seconds)
    response.raise_for_status()
    return parse_grilon3_sitemap_audit(response.text)


def enrich_grilon3_catalog_details(
    catalog: dict[str, CatalogProduct],
    timeout_seconds: int = 4,
    max_workers: int = 12,
) -> dict[str, CatalogProduct]:
    enriched = dict(catalog)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_grilon3_product_detail, product.product_url, timeout_seconds): (product_id, product)
            for product_id, product in catalog.items()
        }
        for future in as_completed(futures):
            product_id, product = futures[future]
            try:
                detail = future.result()
            except Exception:
                continue
            enriched[product_id] = CatalogProduct(
                product_id=product.product_id,
                title=product.title,
                product_url=product.product_url,
                image_url=detail.primary_image_url or product.image_url,
                pantone=detail.pantone,
                sku=detail.sku,
                ean=detail.ean,
            )
    return enriched


def enrich_grilon3_selected_details(
    catalog: dict[str, CatalogProduct],
    product_ids: set[str],
    timeout_seconds: int = 4,
    max_workers: int = 12,
) -> dict[str, CatalogProduct]:
    selected = {
        product_id: product
        for product_id, product in catalog.items()
        if product_id in product_ids and not product.pantone
    }
    if not selected:
        return dict(catalog)

    enriched = dict(catalog)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_grilon3_product_detail, product.product_url, timeout_seconds): (product_id, product)
            for product_id, product in selected.items()
        }
        for future in as_completed(futures):
            product_id, product = futures[future]
            try:
                detail = future.result()
            except Exception:
                continue
            enriched[product_id] = CatalogProduct(
                product_id=product.product_id,
                title=product.title,
                product_url=product.product_url,
                image_url=detail.primary_image_url or product.image_url,
                pantone=detail.pantone,
                sku=detail.sku,
                ean=detail.ean,
            )
    return enriched


def apply_grilon3_metadata(
    catalog: dict[str, CatalogProduct],
    metadata: dict[str, dict[str, str]],
) -> dict[str, CatalogProduct]:
    if not metadata:
        return dict(catalog)
    enriched: dict[str, CatalogProduct] = {}
    for product_id, product in catalog.items():
        data = metadata.get(product_id, {})
        enriched[product_id] = CatalogProduct(
            product_id=product.product_id,
            title=product.title,
            product_url=product.product_url,
            image_url=product.image_url or data.get("image_url", ""),
            pantone=product.pantone or data.get("pantone", ""),
            sku=product.sku or data.get("sku", ""),
            ean=product.ean or data.get("ean", ""),
        )
    return enriched


def fetch_grilon3_product_detail(product_url: str, timeout_seconds: int = 10) -> CatalogProductDetail:
    response = requests.get(product_url, timeout=timeout_seconds)
    response.raise_for_status()
    return parse_grilon3_product_detail(response.text, base_url=product_url)


def parse_grilon3_product_detail(html_text: str, base_url: str = BASE_URL) -> CatalogProductDetail:
    parser = _ProductDetailParser.parse(html_text, base_url)
    json_ld_sku, json_ld_ean = _extract_json_ld_codes(parser.json_ld_blocks)
    fallback_sku, fallback_ean = _extract_sku_ean(_clean_text(" ".join(parser.visible_text)))
    return CatalogProductDetail(
        product_url=base_url,
        category_path=tuple(dict.fromkeys(parser.category_path)),
        gallery_image_urls=tuple(dict.fromkeys(parser.gallery_image_urls)),
        pantone=parser.pantone,
        sku=parser.sku or json_ld_sku or fallback_sku,
        ean=parser.ean or json_ld_ean or fallback_ean,
    )


def parse_grilon3_catalog(html_text: str, base_url: str = BASE_URL) -> dict[str, CatalogProduct]:
    page = parse_grilon3_catalog_page(html_text, base_url)
    catalog: dict[str, CatalogProduct] = {}

    for product in page.products:
        catalog[_unique_catalog_key(catalog, product.product_id, product.product_url)] = product

    return catalog


def parse_grilon3_catalog_page(html_text: str, base_url: str = BASE_URL) -> CatalogPage:
    return parse_grilon3_catalog_page_audit(html_text, base_url).page


def parse_grilon3_catalog_page_audit(
    html_text: str,
    base_url: str = BASE_URL,
) -> CatalogPageAudit:
    links = _ProductLinkParser.parse(html_text, base_url)
    metadata = _CatalogPageMetadataParser.parse(html_text, base_url)
    products: list[CatalogProduct] = []
    rejections: list[CatalogRejection] = []
    raw_urls: list[str] = []

    for link in links:
        canonical_url = _canonical_product_url(link["product_url"])
        raw_urls.append(canonical_url)
        product, rejection = _catalog_product_from_raw(
            title=link["title"],
            product_url=canonical_url,
            image_url=link["image_url"],
        )
        if rejection:
            rejections.append(rejection)
        elif product:
            products.append(product)

    page = CatalogPage(
        products=tuple(products),
        pagination_urls=metadata["pagination_urls"],
        reported_total=metadata["reported_total"],
    )
    return CatalogPageAudit(
        page_url=_canonical_product_url(base_url),
        page=page,
        raw_link_count=len(links),
        raw_unique_url_count=len(set(raw_urls)),
        raw_urls=tuple(raw_urls),
        rejections=tuple(rejections),
    )


def parse_grilon3_sitemap(xml_text: str) -> dict[str, CatalogProduct]:
    return parse_grilon3_sitemap_audit(xml_text).catalog


def parse_grilon3_sitemap_audit(xml_text: str) -> SitemapCatalogAudit:
    catalog: dict[str, CatalogProduct] = {}
    raw_locs = re.findall(r"<loc>(.*?)</loc>", xml_text)
    unique_urls = tuple(dict.fromkeys(_canonical_product_url(url) for url in raw_locs))
    rejections: list[CatalogRejection] = []
    for url in unique_urls:
        if "/producto/" not in url:
            rejections.append(CatalogRejection("", url, ("not_product_url",)))
            continue
        title = _title_from_product_url(url)
        if not title:
            rejections.append(CatalogRejection("", url, ("missing_title",)))
            continue
        product, rejection = _catalog_product_from_raw(
            title=title,
            product_url=url,
            image_url="",
        )
        if rejection:
            rejections.append(rejection)
            continue
        assert product is not None
        catalog[_unique_catalog_key(catalog, product.product_id, url)] = product
    return SitemapCatalogAudit(
        catalog=catalog,
        raw_loc_count=len(raw_locs),
        raw_unique_url_count=len(unique_urls),
        rejections=tuple(rejections),
    )


def _catalog_product_from_raw(
    title: str,
    product_url: str,
    image_url: str,
) -> tuple[CatalogProduct | None, CatalogRejection | None]:
    cleaned_title = _clean_text(title)
    if not cleaned_title:
        return None, CatalogRejection("", product_url, ("missing_title",))
    item = RawStockItem(
        source_id="grilon3_catalog",
        provider_name="Grilon3",
        provider_zone="",
        provider_url="https://grilon3.com.ar/",
        original_name=cleaned_title,
        stock_quantity=None,
        source_url=product_url,
        brand_hint="Grilon3",
    )
    fields = normalize_record(item)
    reasons: list[str] = []
    if fields.brand != "Grilon3":
        reasons.append("brand_not_grilon3")
    if fields.material == "Sin clasificar":
        reasons.append("material_unclassified")
    if fields.color == "Sin color" and fields.material not in COLOR_OPTIONAL_MATERIALS:
        reasons.append("color_missing")
    if reasons:
        return None, CatalogRejection(
            cleaned_title,
            product_url,
            tuple(reasons),
        )
    return CatalogProduct(
        product_id=build_product_id(fields),
        title=cleaned_title,
        product_url=product_url,
        image_url=image_url,
        pantone="",
        sku="",
        ean="",
    ), None


def _is_allowed_catalog_page_url(page_url: str, products_url: str) -> bool:
    page = urlparse(page_url)
    root = urlparse(products_url)
    if (page.scheme, page.netloc) != (root.scheme, root.netloc):
        return False
    root_path = root.path.rstrip("/")
    page_path = page.path.rstrip("/")
    return page_path == root_path or bool(
        re.fullmatch(rf"{re.escape(root_path)}/page/[0-9]+", page_path)
    )


def _unique_catalog_key(catalog: dict[str, CatalogProduct], product_id: str, product_url: str) -> str:
    existing = catalog.get(product_id)
    if existing is None or existing.product_url == product_url:
        return product_id
    suffix = re.sub(r"[^a-z0-9]+", "-", product_url.rstrip("/").rsplit("/", 1)[-1].lower()).strip("-")
    return f"{product_id}-{suffix}"


def _canonical_product_url(product_url: str) -> str:
    return product_url.rstrip("/") + "/"


def enrich_with_grilon3_catalog(
    fields: NormalizedFields,
    catalog: dict[str, CatalogProduct],
) -> dict[str, str]:
    if fields.brand != "Grilon3":
        return dict(EMPTY_ENRICHMENT)

    product = catalog.get(build_product_id(fields))
    if product is None:
        return dict(EMPTY_ENRICHMENT)

    return {
        "manufacturer_product_url": product.product_url,
        "image_url": product.image_url,
        "image_source": "manufacturer" if product.image_url else "",
        "pantone": getattr(product, "pantone", ""),
        "sku": getattr(product, "sku", ""),
        "ean": getattr(product, "ean", ""),
    }


class _ProductLinkParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.links: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._text_stack: list[str] = []

    @classmethod
    def parse(cls, html_text: str, base_url: str) -> list[dict[str, str]]:
        parser = cls(base_url)
        parser.feed(html_text)
        return parser.links

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if tag == "a" and "href" in attributes:
            href = attributes["href"]
            if "/producto/" in href:
                self._current = {
                    "product_url": urljoin(self.base_url, href),
                    "image_url": "",
                    "title": "",
                }
                self._text_stack = []
            return

        if self._current is not None and tag == "img" and not self._current["image_url"]:
            src = attributes.get("src") or attributes.get("data-src") or ""
            if src:
                self._current["image_url"] = urljoin(self.base_url, src)
            alt = attributes.get("alt", "")
            if alt:
                self._text_stack.append(alt)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current is not None:
            self._current["title"] = _clean_text(" ".join(self._text_stack))
            self.links.append(self._current)
            self._current = None
            self._text_stack = []

    def handle_data(self, data: str) -> None:
        if self._current is not None:
            self._text_stack.append(data)


class _CatalogPageMetadataParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.pagination_urls: list[str] = []
        self.visible_text: list[str] = []

    @classmethod
    def parse(cls, html_text: str, base_url: str) -> dict[str, tuple[str, ...] | int | None]:
        parser = cls(base_url)
        parser.feed(html_text)
        text = _clean_text(" ".join(parser.visible_text))
        total_match = re.search(r"\bde\s+([0-9][0-9.,]*)\s+resultados?\b", text, flags=re.IGNORECASE)
        reported_total = None
        if total_match:
            reported_total = int(re.sub(r"[^0-9]", "", total_match.group(1)))
        return {
            "pagination_urls": tuple(dict.fromkeys(parser.pagination_urls)),
            "reported_total": reported_total,
        }

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag != "a":
            return
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        href = attributes.get("href", "")
        if "page-numbers" in classes and href:
            self.pagination_urls.append(urljoin(self.base_url, href))

    def handle_data(self, data: str) -> None:
        self.visible_text.append(data)


class _ProductDetailParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.pantone = ""
        self.gallery_image_urls: list[str] = []
        self.category_path: list[str] = []
        self.visible_text: list[str] = []
        self.json_ld_blocks: list[str] = []
        self._gallery_depth = 0
        self._breadcrumb_depth = 0
        self._category_anchor_depth = 0
        self._category_anchor_text: list[str] = []
        self._field_depth = 0
        self._field_name = ""
        self._field_text: list[str] = []
        self._json_ld_depth = 0
        self._json_ld_text: list[str] = []
        self.sku = ""
        self.ean = ""

    @classmethod
    def parse(cls, html_text: str, base_url: str) -> _ProductDetailParser:
        parser = cls(base_url)
        parser.feed(html_text)
        parser.close()
        return parser

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())

        if self._gallery_depth > 0 and tag not in VOID_TAGS:
            self._gallery_depth += 1
        elif "woocommerce-product-gallery" in classes:
            self._gallery_depth = 1

        if self._breadcrumb_depth > 0 and tag not in VOID_TAGS:
            self._breadcrumb_depth += 1
        elif "woocommerce-breadcrumb" in classes:
            self._breadcrumb_depth = 1

        if self._breadcrumb_depth > 0 and tag == "a" and "/categoria-producto/" in attributes.get("href", ""):
            self._category_anchor_depth = 1
            self._category_anchor_text = []
        elif self._category_anchor_depth > 0 and tag not in VOID_TAGS:
            self._category_anchor_depth += 1

        field_name = "sku" if "sku" in classes else "ean" if "ean" in classes else ""
        if field_name and not self._field_depth:
            self._field_depth = 1
            self._field_name = field_name
            self._field_text = []
        elif self._field_depth > 0 and tag not in VOID_TAGS:
            self._field_depth += 1

        if tag == "script" and attributes.get("type", "").lower() == "application/ld+json":
            self._json_ld_depth = 1
            self._json_ld_text = []
        elif self._json_ld_depth > 0 and tag not in VOID_TAGS:
            self._json_ld_depth += 1

        if self._gallery_depth > 0 and tag == "img":
            image_url = attributes.get("data-large_image", "")
            if image_url:
                self.gallery_image_urls.append(urljoin(self.base_url, image_url))

    def handle_endtag(self, tag: str) -> None:
        if self._category_anchor_depth > 0:
            self._category_anchor_depth -= 1
            if not self._category_anchor_depth:
                label = _clean_text(" ".join(self._category_anchor_text))
                if label:
                    self.category_path.append(label)
                self._category_anchor_text = []

        if self._field_depth > 0:
            self._field_depth -= 1
            if not self._field_depth:
                value = _clean_text(" ".join(self._field_text)).strip()
                if self._field_name == "sku" and value and not self.sku:
                    self.sku = value
                elif self._field_name == "ean" and value and not self.ean:
                    self.ean = value
                self._field_name = ""
                self._field_text = []

        if self._json_ld_depth > 0:
            self._json_ld_depth -= 1
            if not self._json_ld_depth:
                block = "".join(self._json_ld_text).strip()
                if block:
                    self.json_ld_blocks.append(block)
                self._json_ld_text = []

        if self._gallery_depth > 0 and tag not in VOID_TAGS:
            self._gallery_depth -= 1
        if self._breadcrumb_depth > 0 and tag not in VOID_TAGS:
            self._breadcrumb_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._json_ld_depth:
            self._json_ld_text.append(data)
            return
        self.visible_text.append(data)
        if self._category_anchor_depth:
            self._category_anchor_text.append(data)
        if self._field_depth:
            self._field_text.append(data)
        if not self.pantone:
            pantone = _extract_pantone(data)
            if pantone:
                self.pantone = pantone


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _extract_pantone(value: str) -> str:
    match = re.search(r"\bPANTONE\s+([^*<\n\r]+)", value, flags=re.IGNORECASE)
    if not match:
        return ""
    color = _clean_text(match.group(1)).strip(" .:-")
    return f"Pantone {color}" if color else ""


def _extract_sku_ean(value: str) -> tuple[str, str]:
    text = _clean_text(value)
    sku_match = re.search(r"\bSKU:\s*([A-Z0-9_-]+)", text, flags=re.IGNORECASE)
    ean_match = re.search(r"\bEAN:\s*([0-9]{8,14})", text, flags=re.IGNORECASE)
    return (
        sku_match.group(1).strip() if sku_match else "",
        ean_match.group(1).strip() if ean_match else "",
    )


def _extract_json_ld_codes(blocks: list[str]) -> tuple[str, str]:
    sku = ""
    ean = ""

    def visit(value: object) -> None:
        nonlocal sku, ean
        if isinstance(value, dict):
            if not sku and isinstance(value.get("sku"), (str, int)):
                sku = str(value["sku"]).strip()
            if not ean and isinstance(value.get("gtin13"), (str, int)):
                candidate = str(value["gtin13"]).strip()
                if re.fullmatch(r"[0-9]{8,14}", candidate):
                    ean = candidate
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for block in blocks:
        try:
            visit(json.loads(block))
        except (json.JSONDecodeError, TypeError):
            continue
    return sku, ean


def _title_from_product_url(url: str) -> str:
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    if slug in {"producto", ""}:
        return ""

    parts = slug.split("-")
    diameter = ""
    if parts and parts[-1] == "285":
        diameter = "2.85 mm"
        parts = parts[:-1]
    title = " ".join(part.upper() if part in {"pla", "petg", "abs", "hips"} else part.title() for part in parts)
    pieces = [title, "Grilon3", "1 kg"]
    if diameter:
        pieces.append(diameter)
    return " ".join(pieces)
