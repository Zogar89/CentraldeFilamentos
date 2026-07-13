from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from centraldefilamentos.apply_grilon3_curation import (
    apply_grilon3_plan,
    build_apply_plan,
)
from centraldefilamentos.build_data import build_grilon3_enrichments, load_grilon3_metadata
from centraldefilamentos.cache_grilon3_metadata import grilon3_asset_filename
from centraldefilamentos.models import RawStockItem


PRODUCT_URL = "https://grilon3.com.ar/producto/pla-negro/"
IMAGE_URL = "https://grilon3.com.ar/wp-content/uploads/pla-negro-angle.jpg"
SECOND_URL = "https://grilon3.com.ar/wp-content/uploads/pla-negro-front.jpg"
FINGERPRINT = "a" * 64


def product(**overrides):
    value = {
        "product_id": "pla-negro-175-1000-grilon3",
        "title": "PLA Negro Grilon3 1 kg 1.75 mm",
        "product_url": PRODUCT_URL,
        "gallery_image_urls": [IMAGE_URL],
        "gallery_fingerprint": FINGERPRINT,
        "sku": "SKU-NUEVO",
        "ean": "7790000000001",
        "pantone": "Black C",
    }
    value.update(overrides)
    return value


def scan(*products, complete=True):
    return {"complete": complete, "products": list(products or [product()])}


def review(**overrides):
    value = {
        "product_url": PRODUCT_URL,
        "selected_image_remote_url": IMAGE_URL,
        "selection_reason": "preferred_angle",
        "gallery_fingerprint": FINGERPRINT,
        "reviewed_at": "2026-07-13T12:00:00.000Z",
    }
    value.update(overrides)
    return value


def reviews(*values):
    records = values or (review(),)
    return {record["product_url"]: record for record in records}


def png_bytes(color="black"):
    output = BytesIO()
    Image.new("RGB", (20, 20), color).save(output, "PNG")
    return output.getvalue()


def production_paths(tmp_path):
    metadata = tmp_path / "centraldefilamentos" / "data" / "grilon3_metadata.json"
    selections = tmp_path / "centraldefilamentos" / "data" / "grilon3_image_selections.json"
    assets = tmp_path / "public" / "assets" / "grilon3"
    metadata.parent.mkdir(parents=True)
    assets.mkdir(parents=True)
    return metadata, selections, assets


def test_incomplete_scan_is_rejected():
    with pytest.raises(ValueError, match="scan incompleto"):
        build_apply_plan(scan(product(), complete=False), reviews(), {}, {})


def test_every_product_with_gallery_requires_a_review():
    with pytest.raises(ValueError, match="revisi.n pendiente"):
        build_apply_plan(scan(product()), {}, {}, {})


@pytest.mark.parametrize("fingerprint", [None, "", "b" * 64])
def test_missing_or_stale_review_fingerprint_is_rejected(fingerprint):
    current = review()
    if fingerprint is None:
        current.pop("gallery_fingerprint")
    else:
        current["gallery_fingerprint"] = fingerprint

    with pytest.raises(ValueError, match="fingerprint"):
        build_apply_plan(scan(product()), reviews(current), {}, {})


def test_selected_image_must_belong_to_exact_gallery():
    with pytest.raises(ValueError, match="galer.a oficial"):
        build_apply_plan(
            scan(product()),
            reviews(review(selected_image_remote_url=SECOND_URL)),
            {},
            {},
        )


def test_unknown_selection_reason_is_rejected():
    with pytest.raises(ValueError, match="motivo"):
        build_apply_plan(
            scan(product()),
            reviews(review(selection_reason="automatic_guess")),
            {},
            {},
        )


def test_product_without_gallery_needs_no_review_and_gets_no_selection():
    plan = build_apply_plan(
        scan(product(gallery_image_urls=[], gallery_fingerprint="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")),
        {},
        {},
        {},
    )

    assert plan["selections"]["selections"] == {}
    assert "image_url" not in plan["metadata"]["pla-negro-175-1000-grilon3"]


def test_official_empty_codes_replace_stale_metadata_in_plan():
    plan = build_apply_plan(
        scan(product(sku="", ean="", pantone="")),
        reviews(),
        {},
        {
            "pla-negro-175-1000-grilon3": {
                "manufacturer_product_url": PRODUCT_URL,
                "sku": "STALE",
                "ean": "STALE",
                "pantone": "STALE",
                "image_url": "assets/grilon3/approved-old.jpg",
            }
        },
    )

    metadata = plan["metadata"]["pla-negro-175-1000-grilon3"]
    assert metadata["sku"] == ""
    assert metadata["ean"] == ""
    assert metadata["pantone"] == ""
    assert metadata["image_url"].startswith("assets/grilon3/pla-negro-angle-")


def test_review_product_url_mismatch_is_rejected():
    mismatched = review(product_url="https://grilon3.com.ar/producto/pla-blanco/")
    with pytest.raises(ValueError, match="desconocido|no coincide"):
        build_apply_plan(scan(product()), {PRODUCT_URL: mismatched}, {}, {})


def test_invalid_review_date_is_rejected():
    with pytest.raises(ValueError, match="reviewed_at"):
        build_apply_plan(scan(product()), reviews(review(reviewed_at="ayer")), {}, {})


def test_non_official_image_host_is_rejected():
    evil = "https://example.com/private.jpg"
    with pytest.raises(ValueError, match="oficial invalida"):
        build_apply_plan(
            scan(product(gallery_image_urls=[evil])),
            reviews(review(selected_image_remote_url=evil)),
            {},
            {},
        )


def test_product_url_canonicalizes_www_and_trailing_slash():
    www_url = "https://www.grilon3.com.ar/producto/pla-negro"
    canonical_review = review(product_url=www_url)
    plan = build_apply_plan(
        scan(product(product_url=www_url)),
        {www_url: canonical_review},
        {},
        {},
    )

    assert list(plan["selections"]["selections"]) == [PRODUCT_URL]
    assert plan["metadata"]["pla-negro-175-1000-grilon3"]["manufacturer_product_url"] == PRODUCT_URL


@pytest.mark.parametrize(
    "bad_url",
    [
        "https://grilon3.com.ar/producto/pla-negro/?preview=1",
        "https://grilon3.com.ar/producto/pla-negro/?",
        "https://grilon3.com.ar/producto/pla-negro/#gallery",
        "https://grilon3.com.ar/producto/pla-negro/#",
        "https://grilon3.com.ar./producto/pla-negro/",
        "https://user@grilon3.com.ar/producto/pla-negro/",
        "https://grilon3.com.ar:443/producto/pla-negro/",
        "https://grilon3.com.ar/producto/../admin/",
        "https://grilon3.com.ar/producto/pla-negro/extra/",
        "https://grilon3.com.ar/producto/pla%2Dnegro/",
        "https://grilon3.com.ar/PRODUCTO/pla-negro/",
    ],
)
def test_product_url_rejects_query_fragment_and_ambiguous_paths(bad_url):
    with pytest.raises(ValueError, match="URL de producto"):
        build_apply_plan(scan(product(product_url=bad_url)), {}, {}, {})


def test_canonical_product_aliases_are_detected_as_duplicates():
    alias = product(product_url="https://www.grilon3.com.ar/producto/pla-negro")
    with pytest.raises(ValueError, match="duplicado|conflictivo"):
        build_apply_plan(scan(product(), alias), reviews(), {}, {})


def test_dry_run_reports_exact_changes_without_writes_or_downloads(tmp_path, monkeypatch):
    metadata, selections, assets = production_paths(tmp_path)
    before = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))
    monkeypatch.setattr(
        "centraldefilamentos.apply_grilon3_curation._download_image_bytes",
        lambda _: pytest.fail("dry-run must not download"),
    )
    plan = build_apply_plan(scan(product()), reviews(), {}, {})

    report = apply_grilon3_plan(
        plan,
        apply=False,
        metadata_path=metadata,
        selections_path=selections,
        assets_dir=assets,
    )

    assert report == {
        "mode": "dry-run",
        "metadata_changes": plan["metadata_changes"],
        "selection_changes": plan["selection_changes"],
        "asset_changes": plan["asset_changes"],
        "metadata": plan["metadata"],
        "selections": plan["selections"],
    }
    assert sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*")) == before


def test_apply_rejects_asset_change_not_backed_by_approved_selection(tmp_path, monkeypatch):
    metadata, selections, assets = production_paths(tmp_path)
    plan = build_apply_plan(scan(product()), reviews(), {}, {})
    plan["asset_changes"][0]["remote_url"] = SECOND_URL
    plan["asset_changes"][0]["image_url"] = f"assets/grilon3/{grilon3_asset_filename(SECOND_URL)}"
    monkeypatch.setattr(
        "centraldefilamentos.apply_grilon3_curation._download_image_bytes",
        lambda _: pytest.fail("tampered plan must not download"),
    )

    with pytest.raises(ValueError, match="seleccion aprobada"):
        apply_grilon3_plan(
            plan,
            apply=True,
            metadata_path=metadata,
            selections_path=selections,
            assets_dir=assets,
        )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda plan: plan.update(version=2), "version"),
        (
            lambda plan: plan["selections"]["selections"][PRODUCT_URL].update(selection_reason="automatic"),
            "motivo",
        ),
        (
            lambda plan: plan["selections"]["selections"][PRODUCT_URL].update(gallery_fingerprint="b" * 64),
            "fingerprint",
        ),
        (
            lambda plan: plan["selections"]["selections"][PRODUCT_URL].update(reviewed_at="ayer"),
            "reviewed_at",
        ),
        (
            lambda plan: plan["selections"]["selections"][PRODUCT_URL].update(selected_image_remote_url=SECOND_URL),
            "galeria|asset",
        ),
        (lambda plan: plan.update(asset_changes=[]), "asset"),
        (lambda plan: plan.update(metadata_changes=None), "metadata_changes"),
        (
            lambda plan: plan["metadata"]["pla-negro-175-1000-grilon3"].update(sku=["not", "text"]),
            "metadata|sku",
        ),
    ],
)
def test_apply_revalidates_untrusted_plan_before_downloading(tmp_path, monkeypatch, mutate, message):
    metadata, selections, assets = production_paths(tmp_path)
    plan = build_apply_plan(scan(product()), reviews(), {}, {})
    mutate(plan)
    monkeypatch.setattr(
        "centraldefilamentos.apply_grilon3_curation._download_image_bytes",
        lambda _: pytest.fail("invalid plan must fail before download"),
    )

    with pytest.raises(ValueError, match=message):
        apply_grilon3_plan(
            plan,
            apply=True,
            metadata_path=metadata,
            selections_path=selections,
            assets_dir=assets,
        )


def test_successful_apply_writes_deterministic_json_assets_and_thumbnail(tmp_path, monkeypatch):
    metadata, selections, assets = production_paths(tmp_path)
    monkeypatch.setattr(
        "centraldefilamentos.apply_grilon3_curation._download_image_bytes",
        lambda _: png_bytes(),
    )
    plan = build_apply_plan(scan(product()), reviews(), {}, {})

    result = apply_grilon3_plan(
        plan,
        apply=True,
        metadata_path=metadata,
        selections_path=selections,
        assets_dir=assets,
    )

    assert result["mode"] == "apply"
    assert metadata.read_text(encoding="utf-8").endswith("\n")
    assert selections.read_text(encoding="utf-8").endswith("\n")
    assert json.loads(selections.read_text(encoding="utf-8"))["version"] == 1
    applied = json.loads(metadata.read_text(encoding="utf-8"))["pla-negro-175-1000-grilon3"]
    assert applied["image_remote_url"] == IMAGE_URL
    assert applied["image_url"].startswith("assets/grilon3/")
    assert (tmp_path / "public" / applied["image_url"]).read_bytes() == png_bytes()
    thumbnail = tmp_path / "public" / "assets" / "thumbs" / "grilon3" / (Path(applied["image_url"]).stem + ".webp")
    assert thumbnail.is_file() and thumbnail.stat().st_size > 0
    assert not list(tmp_path.rglob(".grilon3-apply-*"))


def test_apply_persists_only_validated_canonical_payload_when_plan_uses_www_aliases(tmp_path, monkeypatch):
    metadata_path, selections_path, assets = production_paths(tmp_path)
    plan = build_apply_plan(scan(product()), reviews(), {}, {})
    selection = plan["selections"]["selections"].pop(PRODUCT_URL)
    alias_product_url = "https://www.grilon3.com.ar/producto/pla-negro"
    alias_image_url = "https://www.grilon3.com.ar/wp-content/uploads/pla-negro-angle.jpg"
    selection["product_url"] = alias_product_url
    selection["selected_image_remote_url"] = alias_image_url
    plan["selections"]["selections"][alias_product_url] = selection
    plan["metadata"]["pla-negro-175-1000-grilon3"]["manufacturer_product_url"] = alias_product_url
    monkeypatch.setattr(
        "centraldefilamentos.apply_grilon3_curation._download_image_bytes",
        lambda _: png_bytes(),
    )

    report = apply_grilon3_plan(
        plan,
        apply=True,
        metadata_path=metadata_path,
        selections_path=selections_path,
        assets_dir=assets,
    )

    persisted_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    persisted_selections = json.loads(selections_path.read_text(encoding="utf-8"))
    approved = persisted_selections["selections"][PRODUCT_URL]
    assert list(persisted_selections["selections"]) == [PRODUCT_URL]
    assert approved["product_url"] == PRODUCT_URL
    assert approved["selected_image_remote_url"] == IMAGE_URL
    assert persisted_metadata["pla-negro-175-1000-grilon3"]["manufacturer_product_url"] == PRODUCT_URL
    assert persisted_metadata["pla-negro-175-1000-grilon3"]["image_remote_url"] == IMAGE_URL
    assert report["metadata"] == persisted_metadata
    assert report["selections"] == persisted_selections


@pytest.mark.parametrize("failure", ["second-download", "thumbnail"])
def test_apply_failure_preserves_every_production_file_byte_for_byte(tmp_path, monkeypatch, failure):
    metadata, selections, assets = production_paths(tmp_path)
    old_asset = assets / "approved-old.png"
    old_thumb = tmp_path / "public" / "assets" / "thumbs" / "grilon3" / "approved-old.webp"
    old_thumb.parent.mkdir(parents=True)
    metadata.write_bytes(b'{"old":"metadata"}\n')
    selections.write_bytes(b'{"version":1,"selections":{}}\n')
    old_asset.write_bytes(b"old-image")
    old_thumb.write_bytes(b"old-thumb")
    original = {path: path.read_bytes() for path in [metadata, selections, old_asset, old_thumb]}
    second_product = product(
        product_id="pla-blanco-175-1000-grilon3",
        title="PLA Blanco",
        product_url="https://grilon3.com.ar/producto/pla-blanco/",
        gallery_image_urls=[SECOND_URL],
        gallery_fingerprint="b" * 64,
    )
    second_review = review(
        product_url=second_product["product_url"],
        selected_image_remote_url=SECOND_URL,
        gallery_fingerprint=second_product["gallery_fingerprint"],
    )
    plan = build_apply_plan(scan(product(), second_product), reviews(review(), second_review), {}, {})
    calls = []

    def download(url):
        calls.append(url)
        if failure == "second-download" and len(calls) == 2:
            raise RuntimeError("download failed")
        return png_bytes("white")

    monkeypatch.setattr("centraldefilamentos.apply_grilon3_curation._download_image_bytes", download)
    if failure == "thumbnail":
        monkeypatch.setattr(
            "centraldefilamentos.apply_grilon3_curation.ensure_thumbnail_for_url",
            lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("thumbnail failed")),
        )

    with pytest.raises(RuntimeError):
        apply_grilon3_plan(
            plan,
            apply=True,
            metadata_path=metadata,
            selections_path=selections,
            assets_dir=assets,
        )

    assert {path: path.read_bytes() for path in original} == original
    assert sorted(path.name for path in assets.iterdir()) == ["approved-old.png"]
    assert not list(tmp_path.rglob(".grilon3-apply-*"))


def test_commit_failure_after_partial_replacements_rolls_back_every_file(tmp_path, monkeypatch):
    metadata, selections, assets = production_paths(tmp_path)
    plan = build_apply_plan(scan(product()), reviews(), {}, {})
    image_url = plan["asset_changes"][0]["image_url"]
    thumb_url = plan["asset_changes"][0]["thumbnail_url"]
    image_path = tmp_path / "public" / image_url
    thumb_path = tmp_path / "public" / thumb_url
    thumb_path.parent.mkdir(parents=True)
    metadata.write_bytes(b'{"old":"metadata"}\n')
    selections.write_bytes(b'{"version":1,"selections":{}}\n')
    image_path.write_bytes(b"old-image")
    thumb_path.write_bytes(b"old-thumb")
    original = {path: path.read_bytes() for path in [metadata, selections, image_path, thumb_path]}
    monkeypatch.setattr(
        "centraldefilamentos.apply_grilon3_curation._download_image_bytes",
        lambda _: png_bytes(),
    )
    real_replace = Path.replace
    calls = 0

    def fail_third_replace(source, target):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("simulated commit failure")
        return real_replace(source, target)

    monkeypatch.setattr("centraldefilamentos.apply_grilon3_curation._replace_path", fail_third_replace)

    with pytest.raises(OSError, match="simulated commit failure"):
        apply_grilon3_plan(
            plan,
            apply=True,
            metadata_path=metadata,
            selections_path=selections,
            assets_dir=assets,
        )

    assert calls >= 3
    assert {path: path.read_bytes() for path in original} == original
    assert not list(tmp_path.rglob("*.tmp"))
    assert not list(tmp_path.rglob(".grilon3-apply-*"))


def test_cleanup_failure_preserves_primary_error_and_reports_cleanup(tmp_path, monkeypatch):
    metadata, selections, assets = production_paths(tmp_path)
    plan = build_apply_plan(scan(product()), reviews(), {}, {})
    monkeypatch.setattr(
        "centraldefilamentos.apply_grilon3_curation._download_image_bytes",
        lambda _: (_ for _ in ()).throw(RuntimeError("primary download failure")),
    )
    monkeypatch.setattr(
        "centraldefilamentos.apply_grilon3_curation._cleanup_staging",
        lambda _: (_ for _ in ()).throw(OSError("cleanup failure")),
    )

    with pytest.raises(RuntimeError, match="primary download failure") as captured:
        apply_grilon3_plan(
            plan,
            apply=True,
            metadata_path=metadata,
            selections_path=selections,
            assets_dir=assets,
        )

    assert any("limpieza" in note and "cleanup failure" in note for note in captured.value.__notes__)


def test_build_data_consumes_versioned_approved_metadata_without_scratch(tmp_path, monkeypatch):
    metadata = tmp_path / "grilon3_metadata.json"
    metadata.write_text(
        json.dumps({
            "pla-negro-175-1000-grilon3": {
                "manufacturer_product_url": PRODUCT_URL,
                "sku": "SKU-APPROVED",
                "ean": "",
                "pantone": "",
                "image_url": "assets/grilon3/approved.png",
                "image_remote_url": IMAGE_URL,
            }
        }),
        encoding="utf-8",
    )
    loaded = load_grilon3_metadata(metadata)
    monkeypatch.setattr("centraldefilamentos.build_data.load_grilon3_metadata", lambda: loaded)
    item = RawStockItem(
        source_id="test",
        provider_name="Test",
        provider_zone="",
        provider_url="https://example.com",
        original_name="GRILON3 PLA Negro 1kg 1.75mm",
        stock_quantity=1,
        source_url="https://example.com/stock",
        brand_hint="Grilon3",
    )

    enrichment = build_grilon3_enrichments([item], catalog={})["pla-negro-175-1000-grilon3"]

    assert enrichment["sku"] == "SKU-APPROVED"
    assert enrichment["image_url"] == "assets/grilon3/approved.png"
