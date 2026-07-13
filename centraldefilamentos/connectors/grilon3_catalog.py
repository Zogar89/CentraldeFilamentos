from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html.parser import HTMLParser
import json
import re
from urllib.parse import urljoin

import requests

from centraldefilamentos.models import NormalizedFields, RawStockItem
from centraldefilamentos.normalize import build_product_id, normalize_record

BASE_URL = "https://grilon3.com.ar/productos/"
SITEMAP_URL = "https://grilon3.com.ar/product-sitemap.xml"
EMPTY_ENRICHMENT = {"manufacturer_product_url": "", "image_url": "", "image_source": "", "pantone": "", "sku": "", "ean": ""}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


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


def fetch_grilon3_catalog(products_url: str = BASE_URL, timeout_seconds: int = 30) -> dict[str, CatalogProduct]:
    response = requests.get(products_url, timeout=timeout_seconds)
    response.raise_for_status()
    return parse_grilon3_catalog(response.text, base_url=products_url)


def fetch_grilon3_active_catalog(
    products_url: str = BASE_URL,
    timeout_seconds: int = 30,
) -> tuple[dict[str, CatalogProduct], int | None]:
    response = requests.get(products_url, timeout=timeout_seconds)
    response.raise_for_status()
    first_page = parse_grilon3_catalog_page(response.text, base_url=products_url)

    pages = [first_page]
    for page_url in first_page.pagination_urls:
        response = requests.get(page_url, timeout=timeout_seconds)
        response.raise_for_status()
        pages.append(parse_grilon3_catalog_page(response.text, base_url=page_url))

    catalog: dict[str, CatalogProduct] = {}
    seen_urls: set[str] = set()
    for page in pages:
        for product in page.products:
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

    return catalog, first_page.reported_total


def fetch_grilon3_sitemap_catalog(sitemap_url: str = SITEMAP_URL, timeout_seconds: int = 30) -> dict[str, CatalogProduct]:
    response = requests.get(sitemap_url, timeout=timeout_seconds)
    response.raise_for_status()
    return parse_grilon3_sitemap(response.text)


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
    links = _ProductLinkParser.parse(html_text, base_url)
    metadata = _CatalogPageMetadataParser.parse(html_text, base_url)
    products: list[CatalogProduct] = []

    for link in links:
        title = _clean_text(link["title"])
        if not title:
            continue
        item = RawStockItem(
            source_id="grilon3_catalog",
            provider_name="Grilon3",
            provider_zone="",
            provider_url="https://grilon3.com.ar/",
            original_name=title,
            stock_quantity=None,
            source_url=link["product_url"],
            brand_hint="Grilon3",
        )
        fields = normalize_record(item)
        product_id = build_product_id(fields)
        if fields.brand != "Grilon3" or fields.material == "Sin clasificar" or fields.color == "Sin color":
            continue
        products.append(CatalogProduct(
            product_id=product_id,
            title=title,
            product_url=link["product_url"],
            image_url=link["image_url"],
            pantone="",
            sku="",
            ean="",
        ))

    return CatalogPage(
        products=tuple(products),
        pagination_urls=metadata["pagination_urls"],
        reported_total=metadata["reported_total"],
    )


def parse_grilon3_sitemap(xml_text: str) -> dict[str, CatalogProduct]:
    catalog: dict[str, CatalogProduct] = {}
    for url in re.findall(r"<loc>(.*?)</loc>", xml_text):
        if "/producto/" not in url:
            continue
        title = _title_from_product_url(url)
        if not title:
            continue
        item = RawStockItem(
            source_id="grilon3_catalog",
            provider_name="Grilon3",
            provider_zone="",
            provider_url="https://grilon3.com.ar/",
            original_name=title,
            stock_quantity=None,
            source_url=url,
            brand_hint="Grilon3",
        )
        fields = normalize_record(item)
        if fields.brand != "Grilon3" or fields.material == "Sin clasificar" or fields.color == "Sin color":
            continue
        product_id = build_product_id(fields)
        catalog[_unique_catalog_key(catalog, product_id, url)] = CatalogProduct(
            product_id=product_id,
            title=title,
            product_url=url,
            image_url="",
            pantone="",
            sku="",
            ean="",
        )
    return catalog


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
