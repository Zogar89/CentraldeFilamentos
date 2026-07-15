import json
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

from centraldefilamentos.material_swatches import (
    apply_material_swatches_to_stock,
    estimated_material_swatch_url,
    material_swatch_url,
    render_material_swatch,
)


def test_asset_name_is_stable() -> None:
    assert material_swatch_url("179 C", "satin") == (
        "assets/material-swatches/pantone-179-c-satin-v1.webp"
    )
    assert estimated_material_swatch_url("pla-acqua-175-1000", "satin") == (
        "assets/material-swatches/estimated-pla-acqua-175-1000-satin-v1.webp"
    )


def test_render_has_transparent_rounded_corners_and_upper_left_light(tmp_path: Path) -> None:
    output = tmp_path / "swatch.webp"

    render_material_swatch("#E03C31", "satin", output)
    image = Image.open(output).convert("RGBA")

    assert image.size == (160, 160)
    assert image.getpixel((0, 0))[3] == 0
    assert image.getpixel((80, 80))[3] == 255
    upper_left = ImageStat.Stat(image.crop((24, 24, 64, 64)).convert("RGB")).mean
    lower_right = ImageStat.Stat(image.crop((96, 96, 136, 136)).convert("RGB")).mean
    assert sum(upper_left) > sum(lower_right)


def test_finish_profiles_are_visually_distinct_and_deterministic(tmp_path: Path) -> None:
    satin = tmp_path / "satin.webp"
    satin_copy = tmp_path / "satin-copy.webp"
    metallic = tmp_path / "metallic.webp"

    render_material_swatch("#D89B2B", "satin", satin)
    render_material_swatch("#D89B2B", "satin", satin_copy)
    render_material_swatch("#D89B2B", "metallic", metallic)

    assert satin.read_bytes() == satin_copy.read_bytes()
    difference = ImageChops.difference(
        Image.open(satin).convert("RGB"),
        Image.open(metallic).convert("RGB"),
    )
    assert sum(ImageStat.Stat(difference).mean) > 8


def test_apply_material_swatches_updates_only_resolved_products_idempotently(tmp_path: Path) -> None:
    stock_json = tmp_path / "data" / "stock.json"
    public_dir = tmp_path / "public"
    stock_json.parent.mkdir(parents=True)
    stock_json.write_text(
        json.dumps(
            {
                "products": [
                    {
                        "id": "pla-rojo",
                        "pantone": "Pantone 179",
                        "variant": "",
                        "color": "Rojo",
                        "offers": [{"original_name": "PLA rojo"}],
                        "material_finish": "metallic",
                        "material_swatch_url": "",
                    },
                    {
                        "id": "pla-perla",
                        "pantone": "Pantone Perla",
                        "pantone_hex": "",
                        "material_finish": "pearl",
                        "material_swatch_url": "stale.webp",
                    },
                ]
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    assert apply_material_swatches_to_stock(stock_json, public_dir) == 1
    first_run = stock_json.read_bytes()
    assert apply_material_swatches_to_stock(stock_json, public_dir) == 0

    payload = json.loads(stock_json.read_text(encoding="utf-8"))
    assert stock_json.read_bytes() == first_run
    assert payload["products"][0]["material_swatch_url"] == (
        "assets/material-swatches/pantone-179-c-satin-v1.webp"
    )
    assert payload["products"][0]["pantone_hex"] == "#E03C31"
    assert payload["products"][0]["material_finish"] == "satin"
    assert payload["products"][1]["material_swatch_url"] == ""
    assert len(list((public_dir / "assets" / "material-swatches").glob("*.webp"))) == 1


def test_apply_material_swatches_prioritizes_pantone_and_renders_estimate(tmp_path: Path) -> None:
    stock_json = tmp_path / "stock.json"
    public_dir = tmp_path / "public"
    stock_json.write_text(
        json.dumps(
            {
                "products": [
                    {
                        "id": "pla-rojo",
                        "pantone": "Pantone 179",
                        "estimated_color_hex": "#FFFFFF",
                        "variant": "",
                        "color": "Rojo",
                        "offers": [],
                    },
                    {
                        "id": "pla-acqua",
                        "pantone": "",
                        "estimated_color_hex": "#009DCE",
                        "material_finish": "satin",
                        "variant": "",
                        "color": "Acqua",
                        "offers": [],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    progress = []

    assert apply_material_swatches_to_stock(
        stock_json, public_dir, progress=lambda completed, total: progress.append((completed, total))
    ) == 2

    products = json.loads(stock_json.read_text(encoding="utf-8"))["products"]
    assert products[0]["material_swatch_url"].startswith("assets/material-swatches/pantone-")
    assert products[1]["material_swatch_url"] == (
        "assets/material-swatches/estimated-pla-acqua-satin-v1.webp"
    )
    assert (public_dir / products[1]["material_swatch_url"]).is_file()
    assert progress == [(1, 1)]


def test_estimated_swatch_replaces_stale_bytes_and_then_is_idempotent(tmp_path: Path) -> None:
    stock_json = tmp_path / "stock.json"
    public_dir = tmp_path / "public"
    product = {
        "id": "pla-acqua",
        "pantone": "",
        "estimated_color_hex": "#009DCE",
        "material_finish": "satin",
        "variant": "",
        "color": "Acqua",
        "offers": [],
    }
    stock_json.write_text(json.dumps({"products": [product]}), encoding="utf-8")

    assert apply_material_swatches_to_stock(stock_json, public_dir) == 1
    url = json.loads(stock_json.read_text(encoding="utf-8"))["products"][0]["material_swatch_url"]
    asset = public_dir / url
    first_bytes = asset.read_bytes()

    payload = json.loads(stock_json.read_text(encoding="utf-8"))
    payload["products"][0]["estimated_color_hex"] = "#D6007B"
    stock_json.write_text(json.dumps(payload), encoding="utf-8")
    assert apply_material_swatches_to_stock(stock_json, public_dir) == 1
    second_bytes = asset.read_bytes()
    assert second_bytes != first_bytes

    assert apply_material_swatches_to_stock(stock_json, public_dir) == 0
    assert asset.read_bytes() == second_bytes
