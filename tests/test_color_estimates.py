import json

import pytest

from centraldefilamentos.color_estimates import (
    ColorEstimate,
    apply_color_estimates_to_stock,
    estimate_public_fields,
    load_color_estimates,
    resolve_color_estimate,
)


def _write_estimates(tmp_path, records):
    path = tmp_path / "color_estimates.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


def _valid_record(**overrides):
    record = {
        "estimated_hex": "#009DCE",
        "confidence_band": "high",
        "confidence_interval": [0.8, 1.0],
        "source": "image_and_name",
        "material_finish": "satin",
        "evidence": "Imagen local y nombre Acqua.",
        "warning": "Color estimado; puede variar según pantalla e iluminación.",
    }
    record.update(overrides)
    return record


def test_load_color_estimates_parses_a_valid_record(tmp_path):
    path = _write_estimates(tmp_path, {"pla-acqua": _valid_record()})

    estimate = load_color_estimates(path)["pla-acqua"]

    assert estimate.estimated_hex == "#009DCE"
    assert estimate.confidence_interval == (0.8, 1.0)
    assert estimate.material_finish == "satin"


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"estimated_hex": "#009dce"}, "uppercase #RRGGBB"),
        ({"confidence_interval": [0.79, 1.0]}, "confidence_interval"),
        ({"material_finish": "plastic"}, "material_finish"),
        ({"evidence": ""}, "evidence"),
        ({"source": "name_only", "confidence_band": "medium", "confidence_interval": [0.5, 0.79]}, "name_only"),
    ],
)
def test_load_color_estimates_rejects_invalid_records(tmp_path, override, message):
    path = _write_estimates(tmp_path, {"pla-acqua": _valid_record(**override)})

    with pytest.raises(ValueError, match=message):
        load_color_estimates(path)


def test_resolve_color_estimate_requires_local_image_for_image_evidence(tmp_path):
    estimates = load_color_estimates(
        _write_estimates(tmp_path, {"pla-acqua": _valid_record()})
    )

    with pytest.raises(ValueError, match="local image"):
        resolve_color_estimate(
            product_id="pla-acqua",
            pantone_hex="",
            image_url="assets/products/missing.webp",
            material_finish="satin",
            estimates=estimates,
            public_dir=tmp_path,
        )


def test_resolve_and_serialize_estimate_without_pantone(tmp_path):
    image = tmp_path / "assets" / "products" / "acqua.webp"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"image")
    estimates = load_color_estimates(
        _write_estimates(tmp_path, {"pla-acqua": _valid_record()})
    )

    estimate = resolve_color_estimate(
        product_id="pla-acqua",
        pantone_hex="",
        image_url="assets/products/acqua.webp",
        material_finish="satin",
        estimates=estimates,
        public_dir=tmp_path,
    )

    assert estimate_public_fields(estimate) == {
        "estimated_color_hex": "#009DCE",
        "estimated_color_confidence_band": "high",
        "estimated_color_confidence_interval": [0.8, 1.0],
        "estimated_color_source": "image_and_name",
        "estimated_color_warning": "Color estimado; puede variar según pantalla e iluminación.",
    }


def test_resolve_color_estimate_returns_none_when_pantone_exists(tmp_path):
    estimates = load_color_estimates(
        _write_estimates(tmp_path, {"pla-acqua": _valid_record(source="name_only", confidence_band="low", confidence_interval=[0.2, 0.49])})
    )

    assert resolve_color_estimate(
        product_id="pla-acqua",
        pantone_hex="#FFFFFF",
        image_url="",
        material_finish="satin",
        estimates=estimates,
        public_dir=tmp_path,
    ) is None


def test_apply_color_estimates_to_stock_enriches_only_no_pantone_products(tmp_path):
    stock_path = tmp_path / "stock.json"
    stock_path.write_text(
        json.dumps(
            {
                "products": [
                    {
                        "id": "pla-acqua",
                        "pantone_hex": "",
                        "image_url": "",
                        "material_finish": "satin",
                    },
                    {
                        "id": "pla-rojo",
                        "pantone_hex": "#E03C31",
                        "image_url": "",
                        "material_finish": "satin",
                        "estimated_color_hex": "#FFFFFF",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    estimate = ColorEstimate(
        "#009DCE", "low", (0.2, 0.49), "name_only", "satin", "Nombre Acqua.", "Color estimado."
    )

    applied = apply_color_estimates_to_stock(
        stock_path,
        {"pla-acqua": estimate, "pla-rojo": estimate},
        public_dir=tmp_path,
    )
    payload = json.loads(stock_path.read_text(encoding="utf-8"))

    assert applied == 1
    assert payload["products"][0]["estimated_color_hex"] == "#009DCE"
    assert not any(key.startswith("estimated_color_") for key in payload["products"][1])
    first_bytes = stock_path.read_bytes()
    apply_color_estimates_to_stock(stock_path, {"pla-acqua": estimate}, public_dir=tmp_path)
    assert stock_path.read_bytes() == first_bytes
