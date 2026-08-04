import importlib
import json

import pytest

from centraldefilamentos.models import RawStockItem
from centraldefilamentos.normalize import normalize_record


def supplier_item(title: str, material: str = "PLA") -> RawStockItem:
    return RawStockItem(
        source_id="grupo_senz",
        provider_name="Grupo Senz",
        provider_zone="Zona Oeste",
        provider_url="https://gruposenz.example/",
        original_name=f"3N3 SILK {title} 1.75 MM X 1 KG" if material == "PLA" else title,
        stock_quantity=2,
        source_url="https://gruposenz.example/catalogo",
        brand_hint="3N3",
        updated_at="2026-08-03T14:11:26-03:00",
    )


def color_registry_module():
    return importlib.import_module("centraldefilamentos.color_registry")


def test_unknown_supplier_color_is_recorded_with_stable_identity_and_provenance(tmp_path):
    module = color_registry_module()
    registry = module.ColorRegistry.empty()
    item = supplier_item("CASCADA")

    first = module.resolve_provisional_color(
        item,
        normalize_record(item),
        registry,
        "2026-08-03T14:11:26-03:00",
    )
    second = module.resolve_provisional_color(
        item,
        normalize_record(item),
        registry,
        "2026-08-03T15:11:26-03:00",
    )
    path = tmp_path / "color_registry.json"
    module.write_color_registry(registry, path)
    loaded = module.load_color_registry(path)

    assert first.key == "grupo_senz|3n3|pla-silk|cascada"
    assert first.display_color == "Cascada"
    assert first.review_status == "provisional"
    assert second.key == first.key
    assert loaded.candidates[first.key].status == "provisional"
    assert loaded.candidates[first.key].first_seen_at == "2026-08-03T14:11:26-03:00"
    assert loaded.candidates[first.key].last_seen_at == "2026-08-03T15:11:26-03:00"
    assert list(loaded.candidates[first.key].examples) == [item.original_name]
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert persisted["version"] == 1
    assert persisted["candidates"][first.key]["examples"] == [item.original_name]


@pytest.mark.parametrize(
    "payload",
    [
        {"version": 2, "candidates": {}},
        {
            "version": 1,
            "candidates": {
                "grupo_senz|3n3|pla-silk|cascada": {
                    "display_color": "Cascada",
                    "status": "not-a-status",
                    "source_id": "grupo_senz",
                    "brand": "3N3",
                    "variant": "PLA Silk",
                    "first_seen_at": "2026-08-03T14:11:26-03:00",
                    "last_seen_at": "2026-08-03T14:11:26-03:00",
                    "examples": ["3N3 SILK CASCADA 1.75 MM X 1 KG"],
                }
            },
        },
    ],
)
def test_registry_rejects_invalid_version_or_candidate_status(tmp_path, payload):
    module = color_registry_module()
    path = tmp_path / "color_registry.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError):
        module.load_color_registry(path)


def test_missing_registry_starts_empty(tmp_path):
    module = color_registry_module()

    registry = module.load_color_registry(tmp_path / "does-not-exist.json")

    assert registry.candidates == {}


def test_registry_rejects_candidate_dates_without_timezone(tmp_path):
    module = color_registry_module()
    path = tmp_path / "color_registry.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "candidates": {
                    "grupo_senz|3n3|pla-silk|cascada": {
                        "display_color": "Cascada",
                        "status": "provisional",
                        "source_id": "grupo_senz",
                        "brand": "3N3",
                        "variant": "PLA Silk",
                        "first_seen_at": "2026-08-03T14:11:26-03:00",
                        "last_seen_at": "2026-08-03T15:11:26",
                        "examples": ["3N3 SILK CASCADA 1.75 MM X 1 KG"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid ISO timestamp"):
        module.load_color_registry(path)


def test_registry_rejects_display_color_that_does_not_match_immutable_key(tmp_path):
    module = color_registry_module()
    path = tmp_path / "color_registry.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "candidates": {
                    "grupo_senz|3n3|pla-silk|cascada": {
                        "display_color": "Zirconia",
                        "status": "approved",
                        "source_id": "grupo_senz",
                        "brand": "3N3",
                        "variant": "PLA Silk",
                        "first_seen_at": "2026-08-03T14:11:26-03:00",
                        "last_seen_at": "2026-08-03T15:11:26-03:00",
                        "examples": ["3N3 SILK CASCADA 1.75 MM X 1 KG"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="display_color does not match immutable key"):
        module.load_color_registry(path)
