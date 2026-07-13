import hashlib
import json
import sys

from centraldefilamentos.connectors.grilon3_catalog import CatalogProduct, CatalogProductDetail
from centraldefilamentos.grilon3_scan import main, scan_grilon3_catalog, write_grilon3_scan


ACTIVE_NEGRO_URL = "https://grilon3.com.ar/producto/pla-negro/"
ACTIVE_ROJO_URL = "https://grilon3.com.ar/producto/pla-rojo/"
LEGACY_URL = "https://grilon3.com.ar/producto/pla-legado/"


def product(product_id, title, url):
    return CatalogProduct(
        product_id=product_id,
        title=title,
        product_url=url,
        image_url="",
    )


def detail(url, gallery_urls=()):
    return CatalogProductDetail(
        product_url=url,
        category_path=("Básicos", "PLA"),
        gallery_image_urls=gallery_urls,
        pantone="Pantone Black" if "negro" in url else "",
        sku="SKU-NEGRO" if "negro" in url else "SKU-ROJO",
        ean="7790000000001" if "negro" in url else "7790000000002",
    )


def install_catalog_stubs(monkeypatch, *, reported_total=2, sitemap_extra=True, failing_url=""):
    active = {
        "pla-negro-175-1000-grilon3": product(
            "pla-negro-175-1000-grilon3",
            "PLA Negro Grilon3 1 kg",
            ACTIVE_NEGRO_URL.rstrip("/"),
        ),
        "pla-rojo-175-1000-grilon3": product(
            "pla-rojo-175-1000-grilon3",
            "PLA Rojo Grilon3 1 kg",
            ACTIVE_ROJO_URL,
        ),
    }
    sitemap = dict(active)
    if sitemap_extra:
        sitemap["pla-legado-175-1000-grilon3"] = product(
            "pla-legado-175-1000-grilon3",
            "PLA Legado Grilon3 1 kg",
            LEGACY_URL.rstrip("/"),
        )

    monkeypatch.setattr(
        "centraldefilamentos.grilon3_scan.fetch_grilon3_active_catalog",
        lambda **kwargs: (active, reported_total),
    )
    monkeypatch.setattr(
        "centraldefilamentos.grilon3_scan.fetch_grilon3_sitemap_catalog",
        lambda **kwargs: sitemap,
    )

    def fetch_detail(product_url, timeout_seconds):
        if product_url == failing_url:
            raise RuntimeError("detalle no disponible")
        return detail(
            product_url,
            gallery_urls=(
                f"{product_url}imagen-caja.jpg",
                f"{product_url}imagen-bobina.jpg",
            ),
        )

    monkeypatch.setattr(
        "centraldefilamentos.grilon3_scan.fetch_grilon3_product_detail",
        fetch_detail,
    )


def test_scan_retains_unclassified_sitemap_only_and_is_incomplete(monkeypatch):
    install_catalog_stubs(monkeypatch)

    payload = scan_grilon3_catalog(timeout_seconds=7, max_workers=1)

    assert payload["summary"]["active_count"] == 2
    assert payload["summary"]["reported_total"] == 2
    assert payload["sitemap_only"] == [
        {"url": LEGACY_URL, "classification": "unclassified"}
    ]
    assert payload["complete"] is False


def test_scan_is_complete_when_counts_details_and_sitemap_classifications_are_resolved(monkeypatch):
    install_catalog_stubs(monkeypatch)

    payload = scan_grilon3_catalog(
        max_workers=1,
        sitemap_classifications={LEGACY_URL.rstrip("/"): "legacy"},
    )

    assert payload["summary"]["detail_success_count"] == 2
    assert payload["summary"]["unclassified_sitemap_only_count"] == 0
    assert payload["sitemap_only"] == [
        {"url": LEGACY_URL, "classification": "legacy"}
    ]
    assert payload["complete"] is True


def test_scan_is_incomplete_when_reported_total_does_not_match(monkeypatch):
    install_catalog_stubs(monkeypatch, reported_total=3, sitemap_extra=False)

    payload = scan_grilon3_catalog(max_workers=1)

    assert payload["summary"]["active_count"] == 2
    assert payload["summary"]["reported_total"] == 3
    assert payload["complete"] is False


def test_scan_retains_detail_failure_and_marks_incomplete(monkeypatch):
    install_catalog_stubs(monkeypatch, sitemap_extra=False, failing_url=ACTIVE_ROJO_URL)

    payload = scan_grilon3_catalog(max_workers=1)

    assert payload["summary"]["detail_success_count"] == 1
    assert payload["summary"]["detail_error_count"] == 1
    assert payload["detail_errors"] == [
        {
            "url": ACTIVE_ROJO_URL,
            "error_type": "RuntimeError",
            "message": "detalle no disponible",
        }
    ]
    failed = next(item for item in payload["products"] if item["product_url"] == ACTIVE_ROJO_URL)
    assert failed["gallery_image_urls"] == []
    assert "detail_request_failed" in failed["warnings"]
    assert payload["complete"] is False


def test_gallery_fingerprint_is_deterministic_and_order_sensitive(monkeypatch):
    install_catalog_stubs(monkeypatch, sitemap_extra=False)

    first = scan_grilon3_catalog(max_workers=1)
    second = scan_grilon3_catalog(max_workers=1)
    negro = next(item for item in first["products"] if item["product_url"] == ACTIVE_NEGRO_URL)
    expected = hashlib.sha256(
        "\n".join(negro["gallery_image_urls"]).encode("utf-8")
    ).hexdigest()

    assert first == second
    assert negro["gallery_fingerprint"] == expected
    assert expected != hashlib.sha256(
        "\n".join(reversed(negro["gallery_image_urls"])).encode("utf-8")
    ).hexdigest()


def test_write_grilon3_scan_writes_only_requested_draft_and_preserves_complete(tmp_path):
    output_path = tmp_path / "nested" / "grilon3-scan.json"
    payload = {"complete": False, "products": [], "summary": {"active_count": 0}}

    write_grilon3_scan(payload, output_path)

    assert json.loads(output_path.read_text(encoding="utf-8")) == payload
    assert list(tmp_path.rglob("*")) == [output_path.parent, output_path]


def test_cli_writes_incomplete_scan_and_returns_nonzero(monkeypatch, tmp_path):
    output_path = tmp_path / "grilon3-scan.json"
    incomplete = {
        "summary": {"active_count": 2},
        "products": [],
        "sitemap_only": [],
        "detail_errors": [],
        "warnings": ["incomplete_scan"],
        "complete": False,
    }
    monkeypatch.setattr(
        "centraldefilamentos.grilon3_scan.scan_grilon3_catalog",
        lambda **kwargs: incomplete,
    )

    exit_code = main(["--output", str(output_path), "--timeout-seconds", "5", "--max-workers", "2"])

    assert exit_code == 1
    assert json.loads(output_path.read_text(encoding="utf-8")) == incomplete


def test_legacy_full_cache_refresh_prints_deprecation_notice(monkeypatch, capsys):
    from centraldefilamentos import cache_grilon3_metadata

    monkeypatch.setattr(sys, "argv", ["cache_grilon3_metadata", "--skip-image-download"])
    monkeypatch.setattr(
        cache_grilon3_metadata,
        "write_grilon3_metadata_cache",
        lambda **kwargs: {},
    )

    cache_grilon3_metadata.main()

    output = capsys.readouterr().out
    assert "deprecado" in output
    assert "scan → curate → apply" in output
