# Estimated Color Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist validated RGB estimates for all products without resolved Pantone values and generate a material swatch for each estimate while leaving Pantone products unchanged.

**Architecture:** A focused `color_estimates` module owns the durable cache contract and validation. `build_data` conditionally adds estimated fields only after Pantone resolution, while `material_swatches` keeps the existing Pantone path and adds a separate estimated-asset path. Initial cache population is an offline, reviewed data operation performed in batches of ten; normal builds remain network-independent.

**Tech Stack:** Python 3.12+, frozen dataclasses, JSON, Pillow, pytest, existing Svelte/Vite static frontend.

## Global Constraints

- Products with non-empty `pantone_hex` are never estimated and receive no estimated-color fields.
- Estimated colors never populate or overwrite `pantone` or `pantone_hex`.
- The durable cache is `centraldefilamentos/data/color_estimates.json` keyed by `product_id`.
- Confidence bands are `high`, `medium`, and `low`; their exact operational intervals are `[0.8, 1.0]`, `[0.5, 0.79]`, and `[0.2, 0.49]`.
- `name_only` records must use low confidence.
- Cached `material_finish` must equal the finish resolved by the existing appearance resolver.
- Pantone assets retain their existing paths and behavior.
- Estimated assets use `assets/material-swatches/estimated-<product-id>-<finish>-v1.webp`.
- Initial population processes the 301 current no-Pantone products and reports progress after every ten.
- No comparison board, contact sheet, runtime API or build-time AI call is added.
- Windows tests use `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos`.

## File Structure

- Create `centraldefilamentos/color_estimates.py`: cache dataclass, loader, validation, conditional resolution and public-field serialization.
- Create `centraldefilamentos/apply_color_estimates.py`: offline CLI that enriches the existing public stock payload without fetching providers.
- Create `centraldefilamentos/data/color_estimates.json`: 301 reviewed product estimates.
- Modify `centraldefilamentos/models.py`: optional estimated-color fields omitted from Pantone product dictionaries.
- Modify `centraldefilamentos/build_data.py`: load cache in `main`, apply estimates only after Pantone resolution.
- Modify `centraldefilamentos/material_swatches.py`: estimated asset naming and rendering fallback.
- Modify `centraldefilamentos/generate_material_swatches.py`: report estimated rendering progress every ten; no API behavior.
- Create `tests/test_color_estimates.py`: cache validation and Pantone exclusion tests.
- Modify `tests/test_models.py`: conditional serialization tests.
- Modify `tests/test_build_data.py`: build integration tests.
- Modify `tests/test_material_swatches.py`: estimated rendering, overwrite and idempotence tests.
- Modify `public/data/stock.json`: generated estimated fields and URLs only on no-Pantone products.
- Create `public/assets/material-swatches/estimated-*.webp`: rendered estimated swatches.

---

### Task 1: Durable Cache Contract and Validation

**Files:**
- Create: `centraldefilamentos/color_estimates.py`
- Create: `tests/test_color_estimates.py`

**Interfaces:**
- Produces: `ColorEstimate`, `load_color_estimates(path)`, `resolve_color_estimate(...)`, `estimate_public_fields(estimate)`.
- Consumes later: `build_data._product_from_group` uses the validated `ColorEstimate` result.

- [ ] **Step 1: Write failing cache contract tests**

Add tests that define the exact public API:

```python
from pathlib import Path

import pytest

from centraldefilamentos.color_estimates import (
    ColorEstimate,
    estimate_public_fields,
    load_color_estimates,
    resolve_color_estimate,
)


def test_load_color_estimates_validates_complete_record(tmp_path: Path) -> None:
    path = tmp_path / "estimates.json"
    path.write_text(
        '{"product-1":{"estimated_hex":"#12ABEF","confidence_band":"high",'
        '"confidence_interval":[0.8,1.0],"source":"image_and_name",'
        '"material_finish":"satin","evidence":"Visible filament.","warning":""}}',
        encoding="utf-8",
    )
    estimates = load_color_estimates(path)
    assert estimates["product-1"].estimated_hex == "#12ABEF"
    assert estimates["product-1"].confidence_interval == (0.8, 1.0)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("estimated_hex", "blue", "estimated_hex"),
        ("confidence_band", "certain", "confidence_band"),
        ("confidence_interval", [0.7, 1.0], "confidence_interval"),
        ("source", "guessed", "source"),
        ("material_finish", "plastic", "material_finish"),
        ("evidence", "", "evidence"),
    ],
)
def test_load_color_estimates_rejects_invalid_fields(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    record = {
        "estimated_hex": "#12ABEF",
        "confidence_band": "high",
        "confidence_interval": [0.8, 1.0],
        "source": "image_and_name",
        "material_finish": "satin",
        "evidence": "Visible filament.",
        "warning": "",
    }
    record[field] = value
    path = tmp_path / "estimates.json"
    import json
    path.write_text(json.dumps({"product-1": record}), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_color_estimates(path)


def test_name_only_requires_low_confidence(tmp_path: Path) -> None:
    path = tmp_path / "estimates.json"
    path.write_text(
        '{"product-1":{"estimated_hex":"#12ABEF","confidence_band":"medium",'
        '"confidence_interval":[0.5,0.79],"source":"name_only",'
        '"material_finish":"satin","evidence":"Name only.","warning":""}}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="name_only"):
        load_color_estimates(path)


def test_resolve_color_estimate_ignores_cache_when_pantone_exists() -> None:
    estimate = ColorEstimate("#12ABEF", "high", (0.8, 1.0), "image_and_name", "satin", "Visible.", "")
    assert resolve_color_estimate(
        product_id="product-1",
        pantone_hex="#0033A0",
        image_url="assets/product.jpg",
        material_finish="satin",
        estimates={"product-1": estimate},
        public_dir=Path("public"),
    ) is None


def test_estimate_public_fields_uses_estimated_namespace() -> None:
    estimate = ColorEstimate("#12ABEF", "high", (0.8, 1.0), "image_and_name", "satin", "Visible.", "")
    assert estimate_public_fields(estimate) == {
        "estimated_color_hex": "#12ABEF",
        "estimated_color_confidence_band": "high",
        "estimated_color_confidence_interval": [0.8, 1.0],
        "estimated_color_source": "image_and_name",
        "estimated_color_warning": "",
    }
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
python -m pytest tests/test_color_estimates.py -v --basetemp C:\tmp\pytest-centraldefilamentos-color-estimates
```

Expected: collection fails because `centraldefilamentos.color_estimates` does not exist.

- [ ] **Step 3: Implement the cache contract**

Create `centraldefilamentos/color_estimates.py` with a frozen `ColorEstimate` dataclass, exact band-to-interval validation, uppercase six-digit RGB validation, source validation, existing `MATERIAL_FINISHES` validation, non-empty evidence validation, `name_only` low-confidence enforcement, image existence validation for `image_and_name`, finish equality validation, and Pantone-first early return.

The exact signatures are:

```python
@dataclass(frozen=True)
class ColorEstimate:
    estimated_hex: str
    confidence_band: Literal["high", "medium", "low"]
    confidence_interval: tuple[float, float]
    source: Literal["image_and_name", "name_only"]
    material_finish: MaterialFinish
    evidence: str
    warning: str


def load_color_estimates(path: Path = COLOR_ESTIMATES_PATH) -> dict[str, ColorEstimate]: ...


def resolve_color_estimate(
    *,
    product_id: str,
    pantone_hex: str,
    image_url: str,
    material_finish: str,
    estimates: Mapping[str, ColorEstimate],
    public_dir: Path = Path("public"),
) -> ColorEstimate | None: ...


def estimate_public_fields(estimate: ColorEstimate | None) -> dict[str, object]: ...
```

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run the Step 2 command. Expected: all `tests/test_color_estimates.py` tests pass.

- [ ] **Step 5: Commit the cache contract**

```powershell
git add centraldefilamentos/color_estimates.py tests/test_color_estimates.py
git commit -m "feat: validate estimated color cache"
```

### Task 2: Conditional Public Product Fields

**Files:**
- Modify: `centraldefilamentos/models.py`
- Modify: `centraldefilamentos/build_data.py`
- Create: `centraldefilamentos/apply_color_estimates.py`
- Modify: `tests/test_models.py`
- Modify: `tests/test_build_data.py`
- Modify: `tests/test_color_estimates.py`

**Interfaces:**
- Consumes: Task 1 `ColorEstimate`, `resolve_color_estimate`, `estimate_public_fields`.
- Produces: conditional estimated fields in `ProductGroup.to_dict()`, `build_payload(..., color_estimates=...)`, and `apply_color_estimates_to_stock(...)` for the current checked-in payload.

- [ ] **Step 1: Write failing serialization and build tests**

Add one model test proving an estimate serializes all five public fields, one model test proving empty estimated values are omitted, one build test proving an estimate applies to an empty-Pantone product, and one build test proving a Pantone product remains unchanged even if the cache contains its id.

The build test must assert:

```python
assert product["pantone_hex"] == ""
assert product["estimated_color_hex"] == "#12ABEF"
assert product["estimated_color_confidence_band"] == "high"
assert product["estimated_color_confidence_interval"] == [0.8, 1.0]
assert product["estimated_color_source"] == "image_and_name"
assert product["material_finish"] == "satin"
```

The Pantone test must assert every key beginning with `estimated_color_` is absent.

- [ ] **Step 2: Run focused tests and verify RED**

```powershell
python -m pytest tests/test_models.py tests/test_build_data.py -v --basetemp C:\tmp\pytest-centraldefilamentos-model-build
```

Expected: failures because ProductGroup and `build_payload` do not accept estimated-color data.

- [ ] **Step 3: Implement conditional serialization**

Add these `ProductGroup` fields before `sku`:

```python
estimated_color_hex: str
estimated_color_confidence_band: str
estimated_color_confidence_interval: list[float]
estimated_color_source: str
estimated_color_warning: str
```

In `to_dict()`, remove all five fields when `estimated_color_hex` is empty. Do not remove or alter Pantone fields.

Add `color_estimates: Mapping[str, ColorEstimate] | None = None` to `build_payload`, carry it into `_product_from_group`, resolve the estimate after `resolve_material_appearance`, and fill ProductGroup from `estimate_public_fields`.

In `main()`, call `load_color_estimates()` once and pass the result to `build_payload`.

Add this offline interface to `color_estimates.py`:

```python
def apply_color_estimates_to_stock(
    stock_json: Path,
    estimates: Mapping[str, ColorEstimate],
    public_dir: Path = Path("public"),
) -> int: ...
```

It reads the existing payload, skips every product with non-empty `pantone_hex`, validates and applies matching estimates, removes stale estimated fields from Pantone products, writes stable sorted JSON only when content changes, and returns the number of no-Pantone products enriched.

Create `centraldefilamentos/apply_color_estimates.py` with arguments `--stock-json`, `--cache`, and `--public-dir`. It loads the cache, calls `apply_color_estimates_to_stock`, and prints `Applied estimated colors to N products`.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run Step 2. Expected: all model and build-data tests pass.

- [ ] **Step 5: Commit conditional public fields**

```powershell
git add centraldefilamentos/models.py centraldefilamentos/build_data.py centraldefilamentos/apply_color_estimates.py tests/test_models.py tests/test_build_data.py tests/test_color_estimates.py
git commit -m "feat: publish estimated color metadata"
```

### Task 3: Estimated Material Swatch Rendering

**Files:**
- Modify: `centraldefilamentos/material_swatches.py`
- Modify: `centraldefilamentos/generate_material_swatches.py`
- Modify: `tests/test_material_swatches.py`

**Interfaces:**
- Consumes: public `estimated_color_hex`, confidence metadata and existing `material_finish`.
- Produces: `estimated_material_swatch_url(product_id, finish)` and estimated WebP assets.

- [ ] **Step 1: Write failing renderer tests**

Add tests proving:

```python
assert estimated_material_swatch_url("pla-acqua-175-1000", "satin") == (
    "assets/material-swatches/estimated-pla-acqua-175-1000-satin-v1.webp"
)
```

Create a two-product fixture where the first has Pantone plus a conflicting estimated value and the second has only an estimated value. Assert the Pantone URL remains `pantone-...`, the estimate URL uses `estimated-...`, and the estimate asset exists.

Add a stale-asset test: render an estimated product, change `estimated_color_hex` without changing its URL, run again, and assert the WebP bytes changed. Run a third time without data changes and assert bytes remain identical.

- [ ] **Step 2: Run renderer tests and verify RED**

```powershell
python -m pytest tests/test_material_swatches.py -v --basetemp C:\tmp\pytest-centraldefilamentos-estimated-swatches
```

Expected: failures because estimated asset naming and rendering do not exist.

- [ ] **Step 3: Implement estimated rendering**

Add:

```python
def estimated_material_swatch_url(product_id: str, finish: str) -> str:
    product_slug = re.sub(r"[^a-z0-9]+", "-", product_id.lower()).strip("-")
    finish_slug = re.sub(r"[^a-z0-9]+", "-", finish.lower()).strip("-")
    return f"assets/material-swatches/estimated-{product_slug}-{finish_slug}-v{RENDERER_VERSION}.webp"
```

In `apply_material_swatches_to_stock`, preserve the current Pantone branch exactly. Only when `pantone_hex` is empty, read `estimated_color_hex`. Render the estimated asset to a temporary sibling path, compare bytes with an existing output, replace only when content differs, then set `material_swatch_url`. This guarantees estimate changes overwrite the stable URL while repeated identical generation produces no content change.

Extend the function with `progress: Callable[[int, int], None] | None = None`. Invoke it after each estimated product and provide completed/total estimated counts. In `generate_material_swatches.py`, pass a callback that prints `Rendered estimated colors N/T` when `N % 10 == 0` or `N == T`. Pantone rendering does not increment this progress counter.

- [ ] **Step 4: Run renderer tests and verify GREEN**

Run Step 2. Expected: all material swatch tests pass.

- [ ] **Step 5: Commit estimated rendering**

```powershell
git add centraldefilamentos/material_swatches.py centraldefilamentos/generate_material_swatches.py tests/test_material_swatches.py
git commit -m "feat: render estimated material swatches"
```

### Task 4: Populate and Validate All Missing Estimates

**Files:**
- Create: `centraldefilamentos/data/color_estimates.json`
- Read: `public/data/stock.json`
- Read: local paths under `public/assets/`

**Interfaces:**
- Consumes: Task 1 cache schema and the current 301-product no-Pantone set.
- Produces: exactly one valid cache record for every current product whose `pantone_hex` is empty, and no record for any product whose `pantone_hex` is non-empty.

- [ ] **Step 1: Export an ordered work queue**

Read `public/data/stock.json`, select only products with empty `pantone_hex`, sort by product id, and group into batches of ten. Capture product id, display name, normalized color, material, variant, brand, image URL, local image existence and resolved finish.

- [ ] **Step 2: Seed the twelve approved pilot records**

Copy the approved values from `C:\tmp\stockcentral-ai-color-pilot\estimates.json`, translate confidence bands to the exact intervals, preserve finish from the current product, and omit every product with Pantone.

- [ ] **Step 3: Process image-backed records in batches of ten**

For each batch, inspect the local images at original detail, estimate base RGB using image plus name, record evidence and warnings, apply high/medium/low bands conservatively, append records through `apply_patch`, run `load_color_estimates`, and report `Procesados N/301` after each ten.

- [ ] **Step 4: Process name-only records in batches of ten**

For each remaining product, infer from normalized color and contextual names, set `source: name_only`, `confidence_band: low`, `confidence_interval: [0.2, 0.49]`, record evidence and any physical-effect warning, append through `apply_patch`, validate, and report after each ten.

- [ ] **Step 5: Verify exact coverage and Pantone exclusion**

Run a read-only verification that asserts:

```python
missing_ids == set(color_estimates)
pantone_ids.isdisjoint(color_estimates)
len(color_estimates) == len(missing_ids) == 301
```

Expected: all assertions pass.

- [ ] **Step 6: Commit the reviewed cache**

```powershell
git add centraldefilamentos/data/color_estimates.json
git commit -m "data: estimate missing filament colors"
```

### Task 5: Generate Public Data and Estimated Assets

**Files:**
- Modify: `public/data/stock.json`
- Create: `public/assets/material-swatches/estimated-*.webp`

**Interfaces:**
- Consumes: Tasks 1-4.
- Produces: public estimated metadata and 301 valid rendered assets.

- [ ] **Step 1: Apply cache records to the existing public payload deterministically**

Run:

```powershell
python -m centraldefilamentos.apply_color_estimates --stock-json public/data/stock.json --cache centraldefilamentos/data/color_estimates.json --public-dir public
```

Expected: `Applied estimated colors to 301 products`, preserving product order and stable JSON formatting.

- [ ] **Step 2: Render estimated assets**

Run:

```powershell
python -m centraldefilamentos.generate_material_swatches --stock-json public/data/stock.json --public-dir public
```

Report rendering progress after each ten completed estimated assets. Do not generate any aggregate image.

- [ ] **Step 3: Verify generated coverage**

Assert all no-Pantone products have the five estimated fields, valid confidence intervals, existing non-empty WebP paths and a matching finish. Assert all Pantone products have no keys beginning with `estimated_color_` and retain Pantone-prefixed swatch URLs.

- [ ] **Step 4: Verify idempotence**

Hash `public/data/stock.json` and every referenced material WebP, rerun generation, and assert all hashes are unchanged.

- [ ] **Step 5: Commit generated outputs**

```powershell
git add public/data/stock.json public/assets/material-swatches
git commit -m "data: generate estimated color swatches"
```

### Task 6: Full Verification and Closeout

**Files:**
- Verify all intended implementation, cache, JSON and WebP files.

**Interfaces:**
- Consumes: completed Tasks 1-5.
- Produces: evidence that the feature is correct and isolated from existing UI work.

- [ ] **Step 1: Run the complete Python suite**

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos
```

Expected: all tests pass.

- [ ] **Step 2: Build the frontend**

```powershell
npm run build
```

Expected: Vite build succeeds without errors.

- [ ] **Step 3: Run final data invariants**

Confirm exactly 301 current no-Pantone products have estimates and rendered assets; zero Pantone products have estimated fields; every confidence band matches its interval; every `name_only` record is low; every cache finish matches the public finish.

- [ ] **Step 4: Review Git scope**

Use `git status --short` and commit diffs to ensure existing summary/quote-list changes were not staged or altered by this feature.

- [ ] **Step 5: Report completion**

Report total products processed, image-and-name versus name-only counts, confidence distribution, rendered asset count, test count and build result. Do not create a comparison board.
