# Pantone Material Swatches Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task with review checkpoints.

**Goal:** Reemplazar las muestras planas por muestras WebP prerenderizadas que combinen el Pantone disponible con una apariencia material coherente, usando el cono cenital sobredimensionado y recortado aprobado.

**Architecture:** El productor Python resuelve Pantone y acabado, agrega tres campos al contrato público y genera una imagen determinista por combinación Pantone/acabado. El frontend Svelte consume esos archivos estáticos; no incorpora WebGL ni lógica PBR en el navegador. La captura automática genera y publica las muestras junto con `stock.json`.

**Tech Stack:** Python 3.12, Pillow, dataclasses, pytest, Svelte 5, CSS, GitHub Actions.

## Global Constraints

- Mantener GitHub Pages como hosting completamente estático.
- Usar sólo equivalencias Pantone gratuitas y versionadas. La fuente inicial es `pborman/colors/pantone` (Apache-2.0); el archivo local contiene únicamente el subconjunto necesario y su procedencia.
- Interpretar códigos sin sufijo como Solid Coated (`C`). No inventar equivalencias para nombres no numéricos como `Perla`.
- El color de pantalla es orientativo: Pantone aporta el sRGB base y el perfil de acabado modifica luz, reflexión, rugosidad y textura.
- Cámara, geometría y luz quedan fijas: cono circular cenital al 150%, recortado por un cuadrado redondeado; luz principal arriba a la izquierda y sombra abajo a la derecha.
- Preservar los cambios locales del usuario en `src/CatalogApp.svelte` y `src/lib/quoteList.js` sobre `showQuickControls`.
- No versionar `.codex-remote-attachments/`, `.planning/` ni `.superpowers/`.

## File Structure

Create:

- `centraldefilamentos/data/pantone_srgb.json`: subconjunto gratuito, alias y metadatos de procedencia/licencia.
- `centraldefilamentos/data/material_finish_overrides.json`: overrides revisados por `product_id`.
- `centraldefilamentos/material_appearance.py`: normalización de Pantone y resolución auditable del acabado.
- `centraldefilamentos/material_swatches.py`: render analítico y aplicación sobre `stock.json`.
- `centraldefilamentos/generate_material_swatches.py`: CLI.
- `tests/test_material_appearance.py` y `tests/test_material_swatches.py`: reglas e invariantes.

Modify:

- Modelo/build: `centraldefilamentos/models.py`, `centraldefilamentos/build_data.py`, `tests/test_models.py`, `tests/test_build_data.py`.
- UI: `src/lib/shared.js`, `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, `src/components/QuoteListItem.svelte`, `src/lib/quoteList.js`, `src/styles/global.css`, `tests/test_frontend_assets.py`.
- Automatización: `.github/workflows/data-capture.yml`, `.github/workflows/thumbnails.yml`.
- Generados: `public/data/stock.json`, `public/assets/material-swatches/*.webp`.

## Task 1: Resolve Pantone and Material Finish

**Files:** create `centraldefilamentos/data/pantone_srgb.json`, `centraldefilamentos/data/material_finish_overrides.json`, `centraldefilamentos/material_appearance.py`, `tests/test_material_appearance.py`.

- [ ] Write failing tests for normalization and priority:

```python
from centraldefilamentos.material_appearance import (
    load_pantone_table,
    normalize_pantone_key,
    resolve_material_finish,
)


def test_missing_suffix_defaults_to_solid_coated() -> None:
    table = load_pantone_table()
    assert normalize_pantone_key("179", table.aliases) == "179 C"
    assert normalize_pantone_key("Pantone 179C", table.aliases) == "179 C"


def test_non_numeric_pantone_name_is_not_invented() -> None:
    table = load_pantone_table()
    assert normalize_pantone_key("Perla", table.aliases) == ""


def test_finish_resolution_priority() -> None:
    assert resolve_material_finish(
        product_id="pla-cobre",
        variant="Silk",
        color="Cobre",
        original_names=["PLA metalizado cobre"],
        overrides={"pla-cobre": "matte"},
    ) == ("matte", "override")
    assert resolve_material_finish(
        product_id="pla-silk",
        variant="Silk",
        color="Oro",
        original_names=[],
        overrides={},
    ) == ("silk", "variant")
    assert resolve_material_finish(
        product_id="pla-basic",
        variant="",
        color="Azul",
        original_names=[],
        overrides={},
    ) == ("satin", "default")
```

- [ ] Run and confirm RED:

```powershell
python -m pytest tests/test_material_appearance.py -v --basetemp C:\tmp\pytest-centraldefilamentos
```

Expected: import failure.

- [ ] Add the curated table with this schema and every numeric code currently present in `grilon3_metadata.json`:

```json
{
  "source": {
    "name": "pborman/colors pantone",
    "url": "https://github.com/pborman/colors/tree/master/pantone",
    "license": "Apache-2.0",
    "retrieved_at": "2026-07-14",
    "note": "Approximate sRGB values for on-screen use"
  },
  "aliases": {
    "179": "179 C",
    "179C": "179 C",
    "PANTONE 179 C": "179 C"
  },
  "colors": {
    "179 C": "#E03C31"
  }
}
```

Aliases sólo normalizan formato. No deben inventar valores ausentes. Inicializar `material_finish_overrides.json` como `{}`.

- [ ] Implement immutable contracts:

```python
MaterialFinish = Literal[
    "matte", "satin", "gloss", "silk", "metallic",
    "pearl", "glitter", "translucent", "fluorescent", "wood",
]


@dataclass(frozen=True)
class PantoneTable:
    aliases: dict[str, str]
    colors: dict[str, str]


@dataclass(frozen=True)
class MaterialAppearance:
    pantone_key: str
    pantone_hex: str
    finish: MaterialFinish
    pantone_source: str
    finish_source: str
```

Normalize whitespace/case, strip optional `PANTONE`, preserve `C`/`U`, and append ` C` only to numeric codes without suffix. Finish priority: override by product id, known normalized variant/line, reviewed keyword over variant+color+original names, then satin.

- [ ] Run the focused test; expected GREEN.
- [ ] Commit:

```powershell
git add centraldefilamentos/data/pantone_srgb.json centraldefilamentos/data/material_finish_overrides.json centraldefilamentos/material_appearance.py tests/test_material_appearance.py
git commit -m "feat: resolve Pantone material appearances"
```

## Task 2: Expose Appearance in the Public Contract

**Files:** modify `centraldefilamentos/models.py`, `centraldefilamentos/build_data.py`, `tests/test_models.py`, `tests/test_build_data.py`.

- [ ] First extend model/build tests:

```python
assert payload["pantone_hex"] == "#E03C31"
assert payload["material_finish"] == "satin"
assert payload["material_swatch_url"] == ""
```

Build fixture: one raw item with `pantone="179"` must preserve the raw label and expose resolved sRGB/finish.

- [ ] Run:

```powershell
python -m pytest tests/test_models.py tests/test_build_data.py -v --basetemp C:\tmp\pytest-centraldefilamentos
```

Expected: constructor/assertion failures.

- [ ] Add after `pantone` in `ProductGroup` and `to_dict()`:

```python
pantone_hex: str
material_finish: str
material_swatch_url: str
```

- [ ] Resolve once while constructing a group:

```python
appearance = resolve_material_appearance(
    product_id=product_id,
    pantone=str(enrichment["pantone"]),
    variant=fields.variant,
    color=fields.color,
    original_names=[offer.original_name for offer in offers],
)
```

Populate the three fields; `material_swatch_url` remains empty until the postprocessor renders the file.

- [ ] Re-run focused tests; expected GREEN.
- [ ] Commit:

```powershell
git add centraldefilamentos/models.py centraldefilamentos/build_data.py tests/test_models.py tests/test_build_data.py
git commit -m "feat: expose product material appearance"
```

## Task 3: Render Deterministic Material Swatches

**Files:** create `centraldefilamentos/material_swatches.py`, `centraldefilamentos/generate_material_swatches.py`, `tests/test_material_swatches.py`.

- [ ] Write failing invariants:

```python
def test_asset_name_is_stable() -> None:
    assert material_swatch_url("179 C", "satin") == (
        "assets/material-swatches/pantone-179-c-satin-v1.webp"
    )


def test_render_has_transparent_corners_and_upper_left_light(tmp_path) -> None:
    output = tmp_path / "swatch.webp"
    render_material_swatch("#E03C31", "satin", output)
    image = Image.open(output).convert("RGBA")
    assert image.size == (160, 160)
    assert image.getpixel((0, 0))[3] == 0
    upper_left = sum(image.getpixel((x, y))[0] for x in range(24, 64) for y in range(24, 64))
    lower_right = sum(image.getpixel((x, y))[0] for x in range(96, 136) for y in range(96, 136))
    assert upper_left > lower_right


def test_finish_profiles_are_visually_distinct(tmp_path) -> None:
    satin = tmp_path / "satin.webp"
    metallic = tmp_path / "metallic.webp"
    render_material_swatch("#D89B2B", "satin", satin)
    render_material_swatch("#D89B2B", "metallic", metallic)
    difference = ImageChops.difference(
        Image.open(satin).convert("RGB"),
        Image.open(metallic).convert("RGB"),
    )
    assert sum(ImageStat.Stat(difference).mean) > 8
```

Add integration coverage: one known and one unknown Pantone, exactly one WebP, URL only for the known value, second run leaves JSON unchanged.

- [ ] Run focused pytest; expected RED.

- [ ] Implement stable profiles and versioned filenames:

```python
RENDERER_VERSION = 1
SWATCH_SIZE = 160

FINISH_PROFILES = {
    "matte": {"roughness": 0.90, "metallic": 0.00, "clearcoat": 0.00},
    "satin": {"roughness": 0.55, "metallic": 0.00, "clearcoat": 0.10},
    "gloss": {"roughness": 0.22, "metallic": 0.00, "clearcoat": 0.55},
    "silk": {"roughness": 0.32, "metallic": 0.15, "clearcoat": 0.35},
    "metallic": {"roughness": 0.28, "metallic": 0.55, "clearcoat": 0.25},
    "pearl": {"roughness": 0.38, "metallic": 0.12, "clearcoat": 0.42},
    "glitter": {"roughness": 0.36, "metallic": 0.30, "clearcoat": 0.30},
    "translucent": {"roughness": 0.18, "metallic": 0.00, "clearcoat": 0.70},
    "fluorescent": {"roughness": 0.48, "metallic": 0.00, "clearcoat": 0.12},
    "wood": {"roughness": 0.82, "metallic": 0.00, "clearcoat": 0.02},
}
```

- [ ] Implement the approved analytic render at 320px, downsampled to 160px:

  1. Cone radius `0.75 * canvas_width` (150% diameter).
  2. Fixed view `(0, 0, 1)` and upper-left light `(-0.55, -0.55, 0.63)`.
  3. Lambert diffuse + Schlick Fresnel + roughness-controlled GGX/Blinn specular.
  4. Deterministic layers: silk anisotropy, metallic micro-noise, pearl lobe, glitter points, translucent edge transmission, fluorescent lift and wood grain.
  5. Soft shadow shifted down-right.
  6. Rounded-square alpha mask, 22% corner radius.
  7. Lossless RGBA WebP.

Derive any random-looking detail from `sha256(f"{hex_color}:{finish}:v1")`; never use global randomness.

- [ ] Implement idempotent application:

```python
def apply_material_swatches_to_stock(stock_json: Path, public_dir: Path) -> int:
    payload = json.loads(stock_json.read_text(encoding="utf-8"))
    generated = 0
    for product in payload.get("products", []):
        hex_color = str(product.get("pantone_hex", ""))
        finish = str(product.get("material_finish", ""))
        if not hex_color or finish not in FINISH_PROFILES:
            product["material_swatch_url"] = ""
            continue
        url = material_swatch_url(str(product["pantone"]), finish)
        output = public_dir / url
        if not output.exists():
            render_material_swatch(hex_color, finish, output)
            generated += 1
        product["material_swatch_url"] = url
    write_json_if_changed(stock_json, payload)
    return generated
```

CLI defaults: `--stock-json public/data/stock.json --public-dir public`.

- [ ] Run focused tests; expected GREEN.
- [ ] Commit:

```powershell
git add centraldefilamentos/material_swatches.py centraldefilamentos/generate_material_swatches.py tests/test_material_swatches.py
git commit -m "feat: render material swatches"
```

## Task 4: Integrate Generation and Publication

**Files:** modify `.github/workflows/data-capture.yml`, `.github/workflows/thumbnails.yml`, `tests/test_frontend_assets.py`.

- [ ] Add failing workflow assertions:

```python
assert "python -m centraldefilamentos.generate_material_swatches" in data_capture
assert "public/assets/material-swatches" in data_capture
assert "python -m centraldefilamentos.generate_material_swatches" in thumbnails_workflow
```

- [ ] Run focused test; expected RED.
- [ ] In `data-capture.yml`, after stock build:

```yaml
      - name: Generate material swatches
        run: >-
          python -m centraldefilamentos.generate_material_swatches
          --stock-json public/data/stock.json
          --public-dir public
```

Include `public/assets/material-swatches` in `DATA_FILES`; publish by copying that directory into `$pages_dir/assets/material-swatches` and staging it with `data`.

- [ ] In `thumbnails.yml`, add renderer/data paths to the trigger, run material generation before thumbnails, and include `public/assets/material-swatches` in the commit. Keep publishing the complete assets tree.

- [ ] Run focused tests; expected GREEN.
- [ ] Commit:

```powershell
git add .github/workflows/data-capture.yml .github/workflows/thumbnails.yml tests/test_frontend_assets.py
git commit -m "ci: generate and publish material swatches"
```

## Task 5: Display the Prerendered Swatches

**Files:** modify `src/lib/shared.js`, `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, `src/components/QuoteListItem.svelte`, `src/lib/quoteList.js`, `src/styles/global.css`, `tests/test_frontend_assets.py`.

- [ ] Add failing source assertions:

```python
assert "material_swatch_url" in catalog_source
assert "material_swatch_url" in summary_source
assert "materialSwatchUrl" in quote_list_source
assert "materialSwatchUrl" in quote_item_source
assert "colorSwatchStyle(product)" in catalog_source
```

- [ ] Run focused test; expected RED.

- [ ] Add shared helpers:

```javascript
export function materialSwatchAlt(product) {
  const pantone = pantoneSwatchLabel(product?.pantone);
  const finish = String(product?.material_finish || "satin");
  return pantone
    ? `Muestra orientativa ${pantone}, acabado ${finish}`
    : `Muestra orientativa, acabado ${finish}`;
}

export function materialSwatchPath(product) {
  return String(product?.material_swatch_url || "");
}
```

- [ ] Catalog:
  - With photo: retain 64×64 photo and add a 34×34 chip at lower-right without obscuring the spool.
  - Without photo but with render: use render as primary.
  - Without both: retain `colorSwatchStyle`.
  - Preserve Pantone label and modal behavior.

- [ ] Summary: rendered sample in existing 24×24 slot, CSS fallback.

- [ ] Quote list:
  - Keep 48×48 photo and add 24×24 chip; without photo use render as primary.
  - Persist `pantone`, `materialFinish`, `materialSwatchUrl` in both `quoteItemFromProduct()` and hydration.
  - Do not alter `showQuickControls: true`.

- [ ] CSS: neutral border/radius; optional subtle sheen only on rendered chips, disabled under `prefers-reduced-motion`. Never recolor the bitmap.

- [ ] Verify:

```powershell
python -m pytest tests/test_frontend_assets.py -v --basetemp C:\tmp\pytest-centraldefilamentos
npm run build
```

- [ ] Stage named files, inspect staged diff to preserve the user's existing edits, then commit:

```powershell
git add src/lib/shared.js src/CatalogApp.svelte src/SummaryApp.svelte src/components/QuoteListItem.svelte src/lib/quoteList.js src/styles/global.css tests/test_frontend_assets.py
git diff --cached --check
git diff --cached
git commit -m "feat: display prerendered material swatches"
```

## Task 6: Generate Current Assets and Verify End to End

**Files:** modify `public/data/stock.json`; create `public/assets/material-swatches/*.webp`.

- [ ] Generate:

```powershell
python -m centraldefilamentos.generate_material_swatches --stock-json public/data/stock.json --public-dir public
```

- [ ] Audit: total products, products with Pantone, resolved sRGB, generated swatches, unresolved raw values, finish counts. Only genuinely unsupported/non-numeric labels may remain unresolved; add any missing numeric code first.

- [ ] Full verification:

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos
npm run build
git diff --check
git status --short
```

- [ ] Visually inspect representative `satin`, `silk`, `metallic`, `translucent`, and `wood` outputs when present. Confirm rounded transparent corners, oversized clipped cone, upper-left light, lower-right falloff, curved form in non-metals and distinct metallic/silk response.

- [ ] Commit generated artifacts without unrelated files:

```powershell
git add public/data/stock.json public/assets/material-swatches
git diff --cached --check
git commit -m "data: generate catalog material swatches"
```

## Final Review Checklist

- Every approved behavior maps to a test or visual check.
- No runtime WebGL/Three.js dependency.
- Public contract only adds `pantone_hex`, `material_finish`, `material_swatch_url`.
- Renderer deterministic and filename-versioned.
- Scheduled capture and manual regeneration both publish assets.
- Unknown Pantones fall back to current CSS.
- `C` and `U` stay distinct; absent suffix defaults only to `C`.
- Existing user edits remain intact.
