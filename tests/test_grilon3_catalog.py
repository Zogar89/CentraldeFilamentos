from pathlib import Path

import centraldefilamentos.connectors.grilon3_catalog as grilon_catalog
import pytest

from centraldefilamentos.connectors.grilon3_catalog import (
    enrich_with_grilon3_catalog,
    fetch_grilon3_active_catalog,
    fetch_grilon3_catalog,
    fetch_grilon3_product_detail,
    fetch_grilon3_sitemap_catalog,
    parse_grilon3_catalog,
    parse_grilon3_catalog_page,
    parse_grilon3_product_detail,
    parse_grilon3_sitemap,
)
from centraldefilamentos.models import NormalizedFields


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "grilon3_catalog.html"


def fields(
    material: str = "PLA",
    color: str = "Negro",
    brand: str = "Grilon3",
    variant: str = "",
    weight_g: int | None = 1000,
) -> NormalizedFields:
    return NormalizedFields(
        material=material,
        variant=variant,
        color=color,
        diameter_mm=1.75,
        weight_g=weight_g,
        brand=brand,
        manufacturer_name=brand,
    )


def test_parse_grilon3_catalog_indexes_official_links_and_images():
    catalog = parse_grilon3_catalog(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert set(catalog) == {
        "pla-negro-175-1000-grilon3",
        "petg-cristal-175-1000-grilon3",
        "pla-rojo-175-1000-grilon3",
    }
    assert catalog["pla-negro-175-1000-grilon3"].product_url == "https://grilon3.com.ar/producto/pla-negro/"
    assert catalog["pla-negro-175-1000-grilon3"].image_url == "https://grilon3.com.ar/wp-content/uploads/pla-negro.jpg"
    assert catalog["pla-negro-175-1000-grilon3"].pantone == ""
    assert catalog["pla-rojo-175-1000-grilon3"].image_url == ""


def test_parse_grilon3_catalog_keeps_distinct_urls_that_normalize_equal():
    html = """
    <html><body>
      <a href="https://grilon3.com.ar/producto/filamento-3d-pla-amarillo/">
        <img src="/wp-content/uploads/pla_amarillo.jpg" alt="PLA Amarillo Grilon3">
      </a>
      <a href="https://grilon3.com.ar/producto/megafill-pla-amarillo/">
        <img src="/wp-content/uploads/megafill_amarillo.jpg" alt="PLA Amarillo Grilon3">
      </a>
    </body></html>
    """

    catalog = parse_grilon3_catalog(html)
    urls = {product.product_url for product in catalog.values()}

    assert urls == {
        "https://grilon3.com.ar/producto/filamento-3d-pla-amarillo/",
        "https://grilon3.com.ar/producto/megafill-pla-amarillo/",
    }


def test_parse_grilon3_catalog_page_extracts_pagination_and_reported_total():
    html = """
    <html><body>
      <p class="woocommerce-result-count">Mostrando 1â€“12 de 167 resultados</p>
      <a href="/producto/pla-negro/">
        <img src="/wp-content/uploads/pla-negro.jpg" alt="PLA Negro Grilon3 1 kg">
      </a>
      <a class="page-numbers" href="/productos/page/2/">2</a>
      <a class="next page-numbers" href="/productos/page/2/">Siguiente</a>
    </body></html>
    """

    page = parse_grilon3_catalog_page(html, base_url="https://grilon3.com.ar/productos/")

    assert page.reported_total == 167
    assert page.pagination_urls == ("https://grilon3.com.ar/productos/page/2/",)
    assert tuple(product.product_url for product in page.products) == (
        "https://grilon3.com.ar/producto/pla-negro/",
    )


def test_fetch_grilon3_active_catalog_deduplicates_canonical_urls_across_pagination(monkeypatch):
    pages = {
        "https://grilon3.com.ar/productos/": """
          <p class="woocommerce-result-count">Mostrando 1-2 de 167 resultados</p>
          <a href="/producto/pla-negro"><img alt="PLA Negro Grilon3 1 kg"></a>
          <a class="page-numbers" href="/productos/page/2/">2</a>
        """,
        "https://grilon3.com.ar/productos/page/2/": """
          <a href="https://grilon3.com.ar/producto/pla-negro/">
            <img alt="PLA Negro Grilon3 1 kg">
          </a>
          <a href="/producto/pla-amarillo/">
            <img alt="PLA Amarillo Grilon3 1 kg">
          </a>
        """,
    }
    calls = []

    class Response:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            calls.append("raise_for_status")

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return Response(pages[url])

    monkeypatch.setattr("centraldefilamentos.connectors.grilon3_catalog.requests.get", fake_get)

    catalog, reported_total = fetch_grilon3_active_catalog(timeout_seconds=6)

    assert reported_total == 167
    assert {product.product_url for product in catalog.values()} == {
        "https://grilon3.com.ar/producto/pla-negro/",
        "https://grilon3.com.ar/producto/pla-amarillo/",
    }
    assert calls == [
        ("https://grilon3.com.ar/productos/", 6),
        "raise_for_status",
        ("https://grilon3.com.ar/productos/page/2/", 6),
        "raise_for_status",
    ]


def test_fetch_grilon3_active_catalog_follows_pagination_links_discovered_later(monkeypatch):
    pages = {
        "https://grilon3.com.ar/productos/": """
          <p class="woocommerce-result-count">Mostrando 1-1 de 4 resultados</p>
          <a href="/producto/pla-negro/"><img alt="PLA Negro Grilon3 1 kg"></a>
          <a class="page-numbers" href="/productos/page/2/">2</a>
          <a class="page-numbers" href="/productos/page/4/">4</a>
        """,
        "https://grilon3.com.ar/productos/page/2/": """
          <a href="/producto/pla-amarillo/"><img alt="PLA Amarillo Grilon3 1 kg"></a>
          <a class="page-numbers" href="/productos/page/3/">3</a>
        """,
        "https://grilon3.com.ar/productos/page/3/": """
          <a href="/producto/pla-rojo/"><img alt="PLA Rojo Grilon3 1 kg"></a>
        """,
        "https://grilon3.com.ar/productos/page/4/": """
          <a href="/producto/pla-verde/"><img alt="PLA Verde Grilon3 1 kg"></a>
        """,
    }
    calls = []

    class Response:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            pass

    def fake_get(url, timeout):
        calls.append(url)
        return Response(pages[url])

    monkeypatch.setattr("centraldefilamentos.connectors.grilon3_catalog.requests.get", fake_get)

    catalog, reported_total = fetch_grilon3_active_catalog(timeout_seconds=6)

    assert reported_total == 4
    assert {product.product_url for product in catalog.values()} == {
        "https://grilon3.com.ar/producto/pla-negro/",
        "https://grilon3.com.ar/producto/pla-amarillo/",
        "https://grilon3.com.ar/producto/pla-rojo/",
        "https://grilon3.com.ar/producto/pla-verde/",
    }
    assert calls == [
        "https://grilon3.com.ar/productos/",
        "https://grilon3.com.ar/productos/page/2/",
        "https://grilon3.com.ar/productos/page/4/",
        "https://grilon3.com.ar/productos/page/3/",
    ]


def test_parse_grilon3_catalog_page_audit_records_raw_links_and_exact_rejections():
    html = """
    <html><body>
      <p class="woocommerce-result-count">Mostrando 1-4 de 4 resultados</p>
      <a href="/producto/pla-negro/"><img alt="PLA Negro Grilon3 1 kg"></a>
      <a href="/producto/sin-titulo/"><img alt=""></a>
      <a href="/producto/sin-material/"><img alt="Filamento Amarillo Grilon3 1 kg"></a>
      <a href="/producto/sin-color/"><img alt="PLA Grilon3 1 kg"></a>
    </body></html>
    """

    audit = grilon_catalog.parse_grilon3_catalog_page_audit(
        html,
        base_url="https://grilon3.com.ar/productos/",
    )

    assert audit.raw_link_count == 4
    assert audit.raw_unique_url_count == 4
    assert len(audit.page.products) == 1
    assert [rejection.to_dict() for rejection in audit.rejections] == [
        {
            "title": "",
            "url": "https://grilon3.com.ar/producto/sin-titulo/",
            "reasons": ["missing_title"],
        },
        {
            "title": "Filamento Amarillo Grilon3 1 kg",
            "url": "https://grilon3.com.ar/producto/sin-material/",
            "reasons": ["material_unclassified"],
        },
        {
            "title": "PLA Grilon3 1 kg",
            "url": "https://grilon3.com.ar/producto/sin-color/",
            "reasons": ["color_missing"],
        },
    ]


def test_parse_grilon3_catalog_page_audit_accepts_magenta_and_colorless_pva_only():
    html = """
    <html><body>
      <p class="woocommerce-result-count">Mostrando 1-5 de 5 resultados</p>
      <a href="/producto/pla-magenta/">
        <img alt="GRILON3 PLA MAGENTA 1.75 MM X 1 KG">
      </a>
      <a href="/producto/filamento-3d-pva/">
        <img alt="GRILON3 PVA SOLUBLE 1.75 MM X 500 GR">
      </a>
      <a href="/producto/pla-sin-color/"><img alt="GRILON3 PLA 1 KG"></a>
      <a href="/producto/abs-sin-color/"><img alt="GRILON3 ABS 1 KG"></a>
      <a href="/producto/material-sin-color/"><img alt="GRILON3 FILAMENTO 1 KG"></a>
    </body></html>
    """

    audit = grilon_catalog.parse_grilon3_catalog_page_audit(
        html,
        base_url="https://grilon3.com.ar/productos/",
    )

    assert [product.product_id for product in audit.page.products] == [
        "pla-magenta-175-1000-grilon3",
        "pva-pva-soluble-sin-color-175-500-grilon3",
    ]
    assert [rejection.to_dict() for rejection in audit.rejections] == [
        {
            "title": "GRILON3 PLA 1 KG",
            "url": "https://grilon3.com.ar/producto/pla-sin-color/",
            "reasons": ["color_missing"],
        },
        {
            "title": "GRILON3 ABS 1 KG",
            "url": "https://grilon3.com.ar/producto/abs-sin-color/",
            "reasons": ["color_missing"],
        },
        {
            "title": "GRILON3 FILAMENTO 1 KG",
            "url": "https://grilon3.com.ar/producto/material-sin-color/",
            "reasons": ["material_unclassified", "color_missing"],
        },
    ]


def test_fetch_grilon3_active_catalog_audit_ignores_external_pagination_and_cycles(monkeypatch):
    pages = {
        "https://grilon3.com.ar/productos/": """
          <p class="woocommerce-result-count">Mostrando 1-2 de 2 resultados</p>
          <a href="/producto/pla-negro/"><img alt="PLA Negro Grilon3 1 kg"></a>
          <a class="page-numbers" href="/productos/page/2/">2</a>
          <a class="page-numbers" href="https://example.com/productos/page/9/">externa</a>
        """,
        "https://grilon3.com.ar/productos/page/2/": """
          <a href="/producto/pla-rojo/"><img alt="PLA Rojo Grilon3 1 kg"></a>
          <a class="page-numbers" href="/productos/">inicio</a>
          <a class="page-numbers" href="/productos/page/2/">2</a>
        """,
    }
    calls = []

    class Response:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            pass

    def fake_get(url, timeout):
        calls.append(url)
        return Response(pages[url])

    monkeypatch.setattr("centraldefilamentos.connectors.grilon3_catalog.requests.get", fake_get)

    audit = grilon_catalog.fetch_grilon3_active_catalog_audit(timeout_seconds=6)

    assert calls == [
        "https://grilon3.com.ar/productos/",
        "https://grilon3.com.ar/productos/page/2/",
    ]
    assert audit.raw_link_count == 2
    assert audit.raw_unique_url_count == 2
    assert len(audit.catalog) == 2
    assert audit.rejections == ()
    assert [page.page_url for page in audit.pages] == [
        "https://grilon3.com.ar/productos/",
        "https://grilon3.com.ar/productos/page/2/",
    ]


def test_parse_grilon3_sitemap_audit_records_raw_unique_and_rejected_locs():
    xml = """
    <urlset>
      <url><loc>https://grilon3.com.ar/producto/pla-negro/</loc></url>
      <url><loc>https://grilon3.com.ar/producto/pla-negro</loc></url>
      <url><loc>https://grilon3.com.ar/producto/filamento-amarillo/</loc></url>
      <url><loc>https://grilon3.com.ar/otra-ruta/</loc></url>
    </urlset>
    """

    audit = grilon_catalog.parse_grilon3_sitemap_audit(xml)

    assert audit.raw_loc_count == 4
    assert audit.raw_unique_url_count == 3
    assert len(audit.catalog) == 1
    assert [rejection.to_dict() for rejection in audit.rejections] == [
        {
            "title": "Filamento Amarillo Grilon3 1 kg",
            "url": "https://grilon3.com.ar/producto/filamento-amarillo/",
            "reasons": ["material_unclassified"],
        },
        {
            "title": "",
            "url": "https://grilon3.com.ar/otra-ruta/",
            "reasons": ["not_product_url"],
        },
    ]


def test_enrich_with_grilon3_catalog_matches_only_confident_grilon3_products():
    catalog = parse_grilon3_catalog(FIXTURE_PATH.read_text(encoding="utf-8"))

    enriched = enrich_with_grilon3_catalog(fields(), catalog)
    not_grilon3 = enrich_with_grilon3_catalog(fields(brand="3N3"), catalog)
    unknown = enrich_with_grilon3_catalog(fields(color="Azul"), catalog)

    assert enriched == {
        "manufacturer_product_url": "https://grilon3.com.ar/producto/pla-negro/",
        "image_url": "https://grilon3.com.ar/wp-content/uploads/pla-negro.jpg",
        "image_source": "manufacturer",
        "pantone": "",
        "sku": "",
        "ean": "",
    }
    assert not_grilon3 == {"manufacturer_product_url": "", "image_url": "", "image_source": "", "pantone": "", "sku": "", "ean": ""}
    assert unknown == {"manufacturer_product_url": "", "image_url": "", "image_source": "", "pantone": "", "sku": "", "ean": ""}


def test_parse_grilon3_product_detail_preserves_official_gallery_and_fields():
    html = """
    <html><body>
      <nav class="woocommerce-breadcrumb">
        <a href="/">Inicio</a> / <a href="/categoria-producto/basicos/">Básicos</a> /
        <a href="/categoria-producto/basicos/abs/">ABS</a> / ABS Amarillo
      </nav>
      <div class="woocommerce-product-gallery">
        <img data-large_image="/wp-content/uploads/abs-amarillo-boxed.jpg" alt="ABS Amarillo caja">
        <img data-large_image="/wp-content/uploads/abs-amarillo-angled.jpg" alt="ABS Amarillo bobina">
        <img data-large_image="/wp-content/uploads/abs-amarillo-frontal.jpg" alt="ABS Amarillo frente">
        <img data-large_image="/wp-content/uploads/abs-range.jpg" alt="Gama ABS">
        <img data-large_image="/wp-content/uploads/abs-amarillo-angled.jpg" alt="ABS Amarillo bobina repetida">
      </div>
      <span class="sku">M09IAM175CJ</span>
      <script type="application/ld+json">
        {"@type": "Product", "sku": "JSON-SKU", "gtin13": "7798049653051"}
      </script>
      <p>PANTONE Yellow</p>
      <section class="related products">
        <img data-large_image="/wp-content/uploads/related.jpg" alt="Producto relacionado">
      </section>
    </body></html>
    """

    detail = parse_grilon3_product_detail(html, base_url="https://grilon3.com.ar/producto/abs-amarillo/")

    assert detail.product_url == "https://grilon3.com.ar/producto/abs-amarillo/"
    assert detail.category_path == ("Básicos", "ABS")
    assert detail.gallery_image_urls == (
        "https://grilon3.com.ar/wp-content/uploads/abs-amarillo-boxed.jpg",
        "https://grilon3.com.ar/wp-content/uploads/abs-amarillo-angled.jpg",
        "https://grilon3.com.ar/wp-content/uploads/abs-amarillo-frontal.jpg",
        "https://grilon3.com.ar/wp-content/uploads/abs-range.jpg",
    )
    assert detail.primary_image_url == detail.gallery_image_urls[0]
    assert detail.pantone == "Pantone Yellow"
    assert detail.sku == "M09IAM175CJ"
    assert detail.ean == "7798049653051"


def test_parse_grilon3_product_detail_uses_json_ld_codes_after_visible_fields():
    html = """
    <html><body>
      <script type="application/ld+json">
        {"@context": "https://schema.org", "@type": "Product",
         "sku": "M10ICA175CJ", "gtin13": "7798049653000"}
      </script>
    </body></html>
    """

    detail = parse_grilon3_product_detail(html, base_url="https://grilon3.com.ar/producto/pla-astra-calipso/")

    assert detail.sku == "M10ICA175CJ"
    assert detail.ean == "7798049653000"


def test_parse_grilon3_product_detail_returns_empty_unpublished_fields():
    html = """
    <html><body>
      <h1>PLA Turquesa</h1>
    </body></html>
    """

    detail = parse_grilon3_product_detail(html, base_url="https://grilon3.com.ar/producto/filamento-3d-pla-turquesa-2/")

    assert (detail.pantone, detail.sku, detail.ean) == ("", "", "")


def test_parse_grilon3_product_detail_extracts_published_diameter_and_presentation():
    html = """
    <html><body>
      <div class="woocommerce-product-details__short-description">
        <p>Diámetro: 1,75 mm</p><p>Presentación: bobina de 500 gr</p>
      </div>
    </body></html>
    """

    detail = parse_grilon3_product_detail(html, base_url="https://grilon3.com.ar/producto/filamento-3d-pva/")

    assert detail.diameter_mm == 1.75
    assert detail.weight_g == 500


@pytest.mark.parametrize(("published", "expected"), [("1 kg", 1000), ("2,5Kg", 2500), ("4 KG", 4000), ("750 g", 750)])
def test_parse_grilon3_product_detail_accepts_other_published_presentations(published, expected):
    detail = parse_grilon3_product_detail(f"<p>Presentación: {published}</p>")

    assert detail.weight_g == expected


def test_parse_grilon3_product_detail_ignores_related_product_images_when_gallery_exists():
    html = """
    <html><body>
      <div class="woocommerce-product-gallery woocommerce-product-gallery--with-images">
        <div class="woocommerce-product-gallery__wrapper">
          <img data-large_image="/wp-content/uploads/2020/09/pla_amarillo-600x600.jpg" alt="Grilon3 PLA">
          <img data-large_image="/wp-content/uploads/2020/09/pla_amarillo2-600x600.jpg" alt="Grilon3 PLA">
        </div>
      </div>
      <section class="related products">
        <img data-large_image="/wp-content/uploads/2024/10/abs_maxicarrete_turquesa_web-600x600.webp" alt="Producto relacionado">
      </section>
    </body></html>
    """

    detail = parse_grilon3_product_detail(html, base_url="https://grilon3.com.ar/producto/filamento-3d-pla-amarillo/")

    assert detail.gallery_image_urls == (
        "https://grilon3.com.ar/wp-content/uploads/2020/09/pla_amarillo-600x600.jpg",
        "https://grilon3.com.ar/wp-content/uploads/2020/09/pla_amarillo2-600x600.jpg",
    )


def test_fetch_grilon3_product_detail_downloads_product_page(monkeypatch):
    calls = []

    class Response:
        text = "<html><body><p>SKU: M09IAM175CJ EAN: 7798049653051</p><p>PANTONE Yellow</p></body></html>"

        def raise_for_status(self):
            calls.append("raise_for_status")

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return Response()

    monkeypatch.setattr("centraldefilamentos.connectors.grilon3_catalog.requests.get", fake_get)

    detail = fetch_grilon3_product_detail("https://grilon3.com.ar/producto/abs-amarillo/", timeout_seconds=7)

    assert calls == [("https://grilon3.com.ar/producto/abs-amarillo/", 7), "raise_for_status"]
    assert detail.pantone == "Pantone Yellow"
    assert detail.sku == "M09IAM175CJ"
    assert detail.ean == "7798049653051"


def test_enrich_grilon3_catalog_details_prefers_product_page_image(monkeypatch):
    from centraldefilamentos.connectors.grilon3_catalog import CatalogProduct, enrich_grilon3_catalog_details

    def fake_detail(product_url, timeout_seconds):
        assert product_url == "https://grilon3.com.ar/producto/pla-negro/"
        from centraldefilamentos.connectors.grilon3_catalog import CatalogProductDetail

        return CatalogProductDetail(
            product_url=product_url,
            category_path=("Básicos", "PLA"),
            gallery_image_urls=("https://grilon3.com.ar/wp-content/uploads/pla_negro_web-600x600.jpg",),
            pantone="Pantone Black",
            sku="M09INE175CJ",
            ean="7798049653037",
        )

    monkeypatch.setattr("centraldefilamentos.connectors.grilon3_catalog.fetch_grilon3_product_detail", fake_detail)

    enriched = enrich_grilon3_catalog_details(
        {
            "pla-negro-175-1000-grilon3": CatalogProduct(
                product_id="pla-negro-175-1000-grilon3",
                title="PLA Negro Grilon3 1 kg 1.75 mm",
                product_url="https://grilon3.com.ar/producto/pla-negro/",
                image_url="https://grilon3.com.ar/wp-content/uploads/pla_negro_con_caja-350x350.jpg",
            )
        },
        max_workers=1,
    )

    assert enriched["pla-negro-175-1000-grilon3"].image_url == "https://grilon3.com.ar/wp-content/uploads/pla_negro_web-600x600.jpg"


def test_fetch_grilon3_catalog_downloads_products_url(monkeypatch):
    fixture_html = FIXTURE_PATH.read_text(encoding="utf-8")
    calls = []

    class Response:
        text = fixture_html

        def raise_for_status(self):
            calls.append("raise_for_status")

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return Response()

    monkeypatch.setattr("centraldefilamentos.connectors.grilon3_catalog.requests.get", fake_get)

    catalog = fetch_grilon3_catalog("https://grilon3.com.ar/productos/", timeout_seconds=8)

    assert calls == [("https://grilon3.com.ar/productos/", 8), "raise_for_status"]
    assert "pla-negro-175-1000-grilon3" in catalog


def test_parse_grilon3_sitemap_adds_285_catalog_products():
    xml = """
    <urlset>
      <url><loc>https://grilon3.com.ar/producto/pla-blanco-285/</loc></url>
      <url><loc>https://grilon3.com.ar/producto/petg-negro-285/</loc></url>
      <url><loc>https://grilon3.com.ar/no-producto/pla/</loc></url>
    </urlset>
    """

    catalog = parse_grilon3_sitemap(xml)

    assert catalog["pla-blanco-285-1000-grilon3"].title == "PLA Blanco Grilon3 1 kg 2.85 mm"
    assert catalog["pla-blanco-285-1000-grilon3"].product_url == "https://grilon3.com.ar/producto/pla-blanco-285/"
    assert catalog["petg-negro-285-1000-grilon3"].title == "PETG Negro Grilon3 1 kg 2.85 mm"


def test_fetch_grilon3_sitemap_catalog_downloads_sitemap(monkeypatch):
    calls = []

    class Response:
        text = "<urlset><url><loc>https://grilon3.com.ar/producto/pla-blanco-285/</loc></url></urlset>"

        def raise_for_status(self):
            calls.append("raise_for_status")

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return Response()

    monkeypatch.setattr("centraldefilamentos.connectors.grilon3_catalog.requests.get", fake_get)

    catalog = fetch_grilon3_sitemap_catalog("https://grilon3.com.ar/product-sitemap.xml", timeout_seconds=9)

    assert calls == [("https://grilon3.com.ar/product-sitemap.xml", 9), "raise_for_status"]
    assert "pla-blanco-285-1000-grilon3" in catalog
