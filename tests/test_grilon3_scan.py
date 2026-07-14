import hashlib
import json
import sys
from types import SimpleNamespace

import pytest

from centraldefilamentos.connectors.grilon3_catalog import (
    CatalogProduct,
    CatalogProductDetail,
    CatalogRejection,
)
from centraldefilamentos.grilon3_scan import (
    main,
    resolve_grilon3_product_identities,
    scan_grilon3_catalog,
    write_grilon3_scan,
)


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
        "centraldefilamentos.grilon3_scan.fetch_grilon3_active_catalog_audit",
        lambda **kwargs: SimpleNamespace(
            catalog=active,
            reported_total=reported_total,
            pages=(),
            raw_link_count=len(active),
            raw_unique_url_count=len(active),
            rejections=(),
        ),
        raising=False,
    )
    monkeypatch.setattr(
        "centraldefilamentos.grilon3_scan.fetch_grilon3_sitemap_catalog_audit",
        lambda **kwargs: SimpleNamespace(
            catalog=sitemap,
            raw_loc_count=len(sitemap),
            raw_unique_url_count=len(sitemap),
            rejections=(),
        ),
        raising=False,
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
    return active, sitemap


IDENTITY_CONFLICT_CASES = (
    (
        "petg-blanco-unknown-unknown-grilon3",
        (
            ("PETG Blanco", ("Básicos", "PETG"), "M77IBL175CJ", "petg-blanco-175-1000-grilon3"),
            ("Maxicarrete PETG Blanco", ("Maxicarrete PETG",), "M77IBL175CJ-1", "petg-blanco-175-2500-grilon3"),
            ("PETG Blanco Megafill", ("Megafill", "Megafill PETG"), "M77IBL175C4", "petg-blanco-175-4000-grilon3"),
        ),
    ),
    (
        "petg-petg-clear-clear-verde-unknown-unknown-grilon3",
        (
            ("PETG Clear Verde", ("Básicos", "PETG"), "M77IVR175CJ", "petg-petg-clear-clear-verde-175-1000-grilon3"),
            ("PETG Clear Verde Megafill", ("Megafill", "Megafill PETG"), "M77IVR175C4", "petg-petg-clear-clear-verde-175-4000-grilon3"),
        ),
    ),
    (
        "petg-negro-unknown-unknown-grilon3",
        (
            ("PETG Negro", ("Básicos", "PETG"), "M77ING175CJ", "petg-negro-175-1000-grilon3"),
            ("Maxicarrete PETG Negro", ("Maxicarrete PETG",), "M77IBL175CJ-1-1", "petg-negro-175-2500-grilon3"),
        ),
    ),
    *(
        (
            f"pla-pla-850-{color}-unknown-unknown-grilon3",
            (
                (f"PLA 850 {label}", ("PLA 850",), f"M11I{sku_color}175CJ", f"pla-pla-850-{color}-175-1000-grilon3"),
                (f"Maxicarrete PLA 850 {label}", ("Maxicarrete PLA 850",), f"M11I{sku_color}175C2", f"pla-pla-850-{color}-175-2500-grilon3"),
            ),
        )
        for color, label, sku_color in (
            ("azul", "Azul", "AZ"),
            ("blanco", "Blanco", "BL"),
            ("bronce", "Bronce", "BR"),
            ("gris-plata", "Gris Plata", "GR"),
            ("negro", "Negro", "NG"),
            ("rojo", "Rojo", "RJ"),
        )
    ),
    (
        "pla-piel-162-unknown-unknown-grilon3",
        (
            ("PLA Piel 162", ("PLA",), "M10IPI175CJ", "pla-piel-162-175-1000-grilon3"),
            ("PLA Piel 162 Megafill", ("Megafill", "Megafill PLA"), "M10IPI175C4", "pla-piel-162-175-4000-grilon3"),
        ),
    ),
)


def conflict_payload(product_id, title, category_path, sku, index):
    normalized = product_id.rsplit("-unknown-unknown-grilon3", 1)[0]
    if normalized.startswith("pla-"):
        material = "PLA"
        remainder = normalized.removeprefix("pla-")
        if remainder.startswith("pla-850-"):
            variant = "PLA 850"
            color = remainder.removeprefix("pla-850-")
        else:
            variant = ""
            color = remainder
    else:
        material = "PETG"
        remainder = normalized.removeprefix("petg-")
        if remainder.startswith("petg-clear-clear-"):
            variant = "PETG Clear"
            color = f"Clear {remainder.removeprefix('petg-clear-clear-').title()}"
        else:
            variant = ""
            color = remainder
    return {
        "product_id": product_id,
        "title": title,
        "product_url": f"https://grilon3.com.ar/producto/conflict-{index}/",
        "category_path": list(category_path),
        "material": material,
        "variant": variant,
        "color": color,
        "diameter_mm": None,
        "weight_g": None,
        "brand": "Grilon3",
        "manufacturer_name": "Grilon3",
        "subrange": "PLA 850" if variant == "PLA 850" else "",
        "finish": "Mate" if variant == "PLA 850" else "",
        "sku": sku,
    }


@pytest.mark.parametrize(("original_id", "records"), IDENTITY_CONFLICT_CASES)
def test_conflicting_official_presentations_resolve_to_existing_stock_ids(original_id, records):
    products = [
        conflict_payload(original_id, title, category_path, sku, index)
        for index, (title, category_path, sku, _expected_id) in enumerate(records)
    ]

    resolved, conflicts = resolve_grilon3_product_identities(products)

    assert conflicts == []
    assert [product["product_id"] for product in resolved] == [
        expected_id for _title, _category_path, _sku, expected_id in records
    ]
    assert [(product["diameter_mm"], product["weight_g"]) for product in resolved] == [
        (1.75, 2500 if "maxicarrete" in title.lower() else 4000 if "megafill" in title.lower() else 1000)
        for title, _category_path, _sku, _expected_id in records
    ]


def test_unresolved_duplicate_product_ids_are_audited_and_block_complete(monkeypatch):
    active, sitemap = install_catalog_stubs(monkeypatch, sitemap_extra=False)
    duplicate = product(
        "pla-negro-175-1000-grilon3",
        "PLA Negro Grilon3 1 kg",
        "https://grilon3.com.ar/producto/pla-negro-alternativo/",
    )
    active["duplicate-catalog-key"] = duplicate
    sitemap["duplicate-catalog-key"] = duplicate
    monkeypatch.setattr(
        "centraldefilamentos.grilon3_scan.fetch_grilon3_active_catalog_audit",
        lambda **kwargs: SimpleNamespace(
            catalog=active,
            reported_total=3,
            pages=(),
            raw_link_count=3,
            raw_unique_url_count=3,
            rejections=(),
        ),
    )
    monkeypatch.setattr(
        "centraldefilamentos.grilon3_scan.fetch_grilon3_sitemap_catalog_audit",
        lambda **kwargs: SimpleNamespace(
            catalog=sitemap,
            raw_loc_count=3,
            raw_unique_url_count=3,
            rejections=(),
        ),
    )

    payload = scan_grilon3_catalog(max_workers=1)

    assert payload["summary"]["product_id_unique_count"] == 2
    assert payload["summary"]["product_id_conflict_count"] == 1
    assert payload["summary"]["product_id_conflict_excess_count"] == 1
    assert payload["product_id_conflicts"] == [{
        "product_id": "pla-negro-175-1000-grilon3",
        "product_urls": [
            "https://grilon3.com.ar/producto/pla-negro-alternativo/",
            ACTIVE_NEGRO_URL,
        ],
    }]
    assert "duplicate_product_ids" in payload["warnings"]
    assert payload["complete"] is False


def test_identity_resolution_does_not_invent_standard_format_without_official_sku():
    standard = conflict_payload(
        "petg-blanco-unknown-unknown-grilon3",
        "PETG Blanco",
        ("Básicos", "PETG"),
        "M77IBL175CI",
        0,
    )
    maxicarrete = conflict_payload(
        "petg-blanco-unknown-unknown-grilon3",
        "Maxicarrete PETG Blanco",
        ("Maxicarrete PETG",),
        "M77IBL175CJ-1",
        1,
    )

    resolved, conflicts = resolve_grilon3_product_identities([standard, maxicarrete])

    assert [product["product_id"] for product in resolved] == [
        "petg-blanco-unknown-unknown-grilon3",
        "petg-blanco-unknown-unknown-grilon3",
    ]
    assert conflicts[0]["product_id"] == "petg-blanco-unknown-unknown-grilon3"


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


def test_scan_is_incomplete_and_auditable_when_active_raw_card_is_rejected(monkeypatch):
    active, _ = install_catalog_stubs(monkeypatch, reported_total=3, sitemap_extra=False)
    rejection = CatalogRejection(
        title="PLA Grilon3 1 kg",
        url="https://grilon3.com.ar/producto/pla-sin-color/",
        reasons=("color_missing",),
    )
    page = SimpleNamespace(
        page_url="https://grilon3.com.ar/productos/",
        raw_link_count=3,
        raw_unique_url_count=3,
        page=SimpleNamespace(products=tuple(active.values())),
        rejections=(rejection,),
    )
    monkeypatch.setattr(
        "centraldefilamentos.grilon3_scan.fetch_grilon3_active_catalog_audit",
        lambda **kwargs: SimpleNamespace(
            catalog=active,
            reported_total=3,
            pages=(page,),
            raw_link_count=3,
            raw_unique_url_count=3,
            rejections=(rejection,),
        ),
        raising=False,
    )

    payload = scan_grilon3_catalog(max_workers=1)

    assert payload["summary"]["active_raw_link_count"] == 3
    assert payload["summary"]["active_raw_unique_url_count"] == 3
    assert payload["summary"]["active_rejected_count"] == 1
    assert payload["active_catalog_audit"]["rejections"] == [rejection.to_dict()]
    assert "active_catalog_products_rejected" in payload["warnings"]
    assert payload["complete"] is False


def test_scan_is_incomplete_when_active_raw_unique_count_misses_reported_total(monkeypatch):
    active, _ = install_catalog_stubs(monkeypatch, reported_total=3, sitemap_extra=False)
    monkeypatch.setattr(
        "centraldefilamentos.grilon3_scan.fetch_grilon3_active_catalog_audit",
        lambda **kwargs: SimpleNamespace(
            catalog=active,
            reported_total=3,
            pages=(),
            raw_link_count=2,
            raw_unique_url_count=2,
            rejections=(),
        ),
        raising=False,
    )

    payload = scan_grilon3_catalog(max_workers=1)

    assert payload["summary"]["active_raw_unique_url_count"] == 2
    assert "active_raw_unique_count_mismatch" in payload["warnings"]
    assert payload["complete"] is False


def test_scan_reports_non_product_sitemap_loc_without_blocking_active_completeness(monkeypatch):
    active, sitemap = install_catalog_stubs(monkeypatch, sitemap_extra=False)
    rejection = CatalogRejection(
        title="",
        url="https://grilon3.com.ar/productos/",
        reasons=("not_product_url",),
    )
    monkeypatch.setattr(
        "centraldefilamentos.grilon3_scan.fetch_grilon3_sitemap_catalog_audit",
        lambda **kwargs: SimpleNamespace(
            catalog=sitemap,
            raw_loc_count=3,
            raw_unique_url_count=3,
            rejections=(rejection,),
        ),
    )

    payload = scan_grilon3_catalog(max_workers=1)

    assert payload["sitemap_audit"]["rejections"] == [rejection.to_dict()]
    assert "sitemap_urls_rejected" in payload["warnings"]
    assert payload["complete"] is True


def test_scan_retains_detail_failure_and_marks_incomplete(monkeypatch):
    install_catalog_stubs(monkeypatch, sitemap_extra=False, failing_url=ACTIVE_ROJO_URL)

    payload = scan_grilon3_catalog(max_workers=1)

    assert payload["summary"]["detail_success_count"] == 1
    assert payload["summary"]["detail_initial_error_count"] == 1
    assert payload["summary"]["detail_retry_attempt_count"] == 1
    assert payload["summary"]["detail_retry_error_count"] == 1
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


def test_scan_retries_initial_detail_failure_once_and_uses_recovered_detail(monkeypatch):
    install_catalog_stubs(monkeypatch, sitemap_extra=False)
    calls = {ACTIVE_NEGRO_URL: 0, ACTIVE_ROJO_URL: 0}

    def fetch_detail(product_url, timeout_seconds):
        calls[product_url] += 1
        if product_url == ACTIVE_ROJO_URL and calls[product_url] == 1:
            raise RuntimeError("timeout inicial")
        return detail(product_url, gallery_urls=(f"{product_url}bobina.jpg",))

    monkeypatch.setattr(
        "centraldefilamentos.grilon3_scan.fetch_grilon3_product_detail",
        fetch_detail,
    )

    payload = scan_grilon3_catalog(max_workers=1)

    assert calls == {ACTIVE_NEGRO_URL: 1, ACTIVE_ROJO_URL: 2}
    assert payload["summary"] == {
        "active_count": 2,
        "active_raw_link_count": 2,
        "active_raw_unique_url_count": 2,
        "active_rejected_count": 0,
        "reported_total": 2,
        "detail_success_count": 2,
        "detail_error_count": 0,
        "detail_initial_error_count": 1,
        "detail_retry_attempt_count": 1,
        "detail_retry_success_count": 1,
        "detail_retry_error_count": 0,
        "sitemap_count": 2,
        "sitemap_raw_loc_count": 2,
        "sitemap_raw_unique_url_count": 2,
        "sitemap_rejected_count": 0,
        "sitemap_only_count": 0,
        "unclassified_sitemap_only_count": 0,
        "product_id_unique_count": 2,
        "product_id_conflict_count": 0,
        "product_id_conflict_excess_count": 0,
    }
    assert payload["detail_errors"] == []
    assert payload["detail_attempts"] == [
        {
            "url": ACTIVE_NEGRO_URL,
            "attempts": [{"attempt": 1, "status": "success"}],
        },
        {
            "url": ACTIVE_ROJO_URL,
            "attempts": [
                {
                    "attempt": 1,
                    "status": "error",
                    "error_type": "RuntimeError",
                    "message": "timeout inicial",
                },
                {"attempt": 2, "status": "success"},
            ],
        },
    ]
    recovered = next(item for item in payload["products"] if item["product_url"] == ACTIVE_ROJO_URL)
    assert recovered["gallery_image_urls"] == [f"{ACTIVE_ROJO_URL}bobina.jpg"]
    assert "detail_request_failed" not in recovered["warnings"]
    assert payload["complete"] is True


def test_scan_never_calls_successful_or_twice_failed_detail_more_than_allowed(monkeypatch):
    install_catalog_stubs(monkeypatch, sitemap_extra=False)
    calls = {ACTIVE_NEGRO_URL: 0, ACTIVE_ROJO_URL: 0}

    def fetch_detail(product_url, timeout_seconds):
        calls[product_url] += 1
        if product_url == ACTIVE_ROJO_URL:
            raise RuntimeError(f"fallo {calls[product_url]}")
        return detail(product_url)

    monkeypatch.setattr(
        "centraldefilamentos.grilon3_scan.fetch_grilon3_product_detail",
        fetch_detail,
    )

    payload = scan_grilon3_catalog(max_workers=1)

    assert calls == {ACTIVE_NEGRO_URL: 1, ACTIVE_ROJO_URL: 2}
    assert payload["detail_attempts"] == [
        {
            "url": ACTIVE_NEGRO_URL,
            "attempts": [{"attempt": 1, "status": "success"}],
        },
        {
            "url": ACTIVE_ROJO_URL,
            "attempts": [
                {
                    "attempt": 1,
                    "status": "error",
                    "error_type": "RuntimeError",
                    "message": "fallo 1",
                },
                {
                    "attempt": 2,
                    "status": "error",
                    "error_type": "RuntimeError",
                    "message": "fallo 2",
                },
            ],
        },
    ]
    assert payload["detail_errors"] == [
        {
            "url": ACTIVE_ROJO_URL,
            "error_type": "RuntimeError",
            "message": "fallo 2",
        }
    ]


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
