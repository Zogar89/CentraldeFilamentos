# AI Color Estimation Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a 12-product comparison board that tests whether image-and-name analysis can supply useful approximate RGB colors for products without Pantone data.

**Architecture:** A temporary Python utility reads the existing stock payload, extracts an explicit reviewed sample, validates structured color estimates, calls the existing deterministic material renderer, and creates a comparison board under `C:\tmp`. The repository's public data, metadata caches, generated assets and in-progress frontend remain untouched.

**Tech Stack:** Python 3.12, Pillow, existing `centraldefilamentos.material_swatches.render_material_swatch`, Codex local-image inspection.

## Global Constraints

- The experiment must not call the OpenAI API or add an API key.
- The experiment must not claim that the current Codex session is running `gpt-5.6-luna`.
- Every selected product must have an empty `pantone_hex` and a local `image_url`.
- Estimated colors must be uppercase `#RRGGBB` values and must never be published as Pantone values.
- All generated files must stay under `C:\tmp\stockcentral-ai-color-pilot`.
- No production file, public JSON payload, metadata cache, generated public asset or frontend file may be modified.
- The success threshold is at least 9 accepted estimates out of 12.
- Windows verification uses the repository's existing Python environment and writable `C:\tmp` path.

## File Structure

- Create `C:\tmp\stockcentral-ai-color-pilot\pilot.py`: temporary manifest validation, estimate validation, swatch rendering and board composition.
- Create `C:\tmp\stockcentral-ai-color-pilot\sample.json`: immutable snapshot of the 12 selected product records.
- Create `C:\tmp\stockcentral-ai-color-pilot\estimates.json`: structured visual estimates produced during inspection.
- Create `C:\tmp\stockcentral-ai-color-pilot\swatches\*.webp`: temporary rendered material swatches.
- Create `C:\tmp\stockcentral-ai-color-pilot\comparison-board.webp`: final visual review board.
- Create `C:\tmp\stockcentral-ai-color-pilot\review.json`: user acceptance decisions and observed failure modes.

---

### Task 1: Prepare and Validate the Pilot Sample

**Files:**
- Create: `C:\tmp\stockcentral-ai-color-pilot\pilot.py`
- Create: `C:\tmp\stockcentral-ai-color-pilot\sample.json`
- Read: `public/data/stock.json`

**Interfaces:**
- Consumes: repository root path and the current `public/data/stock.json` schema.
- Produces: `prepare_sample() -> list[dict[str, object]]` and a 12-record `sample.json` used by Tasks 2 and 3.

- [ ] **Step 1: Record the repository status before generating temporary artifacts**

Run:

```powershell
git status --short
```

Expected: the existing summary-migration changes are visible; no path under `C:\tmp\stockcentral-ai-color-pilot` can appear because it is outside the repository.

- [ ] **Step 2: Create the temporary pilot utility**

Create `C:\tmp\stockcentral-ai-color-pilot\pilot.py` with:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont, ImageOps


REPO = Path(r"C:\Users\Gabriel\Documents\GitHub\StockCentral")
WORK = Path(r"C:\tmp\stockcentral-ai-color-pilot")
SAMPLE_PATH = WORK / "sample.json"
ESTIMATES_PATH = WORK / "estimates.json"
REVIEW_PATH = WORK / "review.json"
SWATCH_DIR = WORK / "swatches"
BOARD_PATH = WORK / "comparison-board.webp"
HEX_PATTERN = re.compile(r"^#[0-9A-F]{6}$")
CONFIDENCE_VALUES = {"high", "medium", "low"}
SAMPLE_IDS = (
    "pla-pla-boutique-acqua-175-1000-grilon3",
    "pla-pla-boutique-arena-175-1000-grilon3",
    "pla-pla-zeta-azabache-175-1000-grilon3",
    "pla-fucsia-175-1000-3n3",
    "pla-amarillo-fluo-175-1000-3n3",
    "pet-e-pet-azul-traful-175-1000-3n3",
    "pet-e-pet-gris-espacial-175-1000-3n3",
    "pla-pla-boutique-lavanda-175-1000-grilon3",
    "pla-pla-silk-cobre-175-1000-grilon3",
    "pla-pla-wood-caoba-175-1000-grilon3",
    "pp-pp-t-natural-175-1000-grilon3",
    "pla-pla-silk-tutti-frutti-175-1000-grilon3",
)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_sample() -> list[dict[str, object]]:
    payload = load_json(REPO / "public" / "data" / "stock.json")
    if not isinstance(payload, dict) or not isinstance(payload.get("products"), list):
        raise ValueError("stock.json does not contain a products list")
    by_id = {
        str(product.get("id", "")): product
        for product in payload["products"]
        if isinstance(product, dict)
    }
    sample: list[dict[str, object]] = []
    for product_id in SAMPLE_IDS:
        product = by_id.get(product_id)
        if product is None:
            raise ValueError(f"Missing sample product: {product_id}")
        if str(product.get("pantone_hex", "")):
            raise ValueError(f"Sample product already has pantone_hex: {product_id}")
        image_url = str(product.get("image_url", ""))
        image_path = REPO / "public" / image_url
        if not image_url.startswith("assets/") or not image_path.is_file():
            raise ValueError(f"Sample product lacks a local image: {product_id}")
        sample.append(
            {
                "id": product_id,
                "display_name": str(product.get("display_name", "")),
                "color": str(product.get("color", "")),
                "material": str(product.get("material", "")),
                "variant": str(product.get("variant", "")),
                "brand": str(product.get("brand", "")),
                "material_finish": str(product.get("material_finish", "satin")),
                "image_url": image_url,
                "image_path": str(image_path),
            }
        )
    if len(sample) != 12 or len({item["id"] for item in sample}) != 12:
        raise ValueError("Pilot sample must contain 12 unique products")
    write_json(SAMPLE_PATH, sample)
    return sample


def validate_estimates() -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    sample = load_json(SAMPLE_PATH)
    estimates = load_json(ESTIMATES_PATH)
    if not isinstance(sample, list) or not isinstance(estimates, list):
        raise ValueError("sample.json and estimates.json must contain lists")
    sample_ids = {str(item.get("id", "")) for item in sample if isinstance(item, dict)}
    estimate_by_id: dict[str, dict[str, object]] = {}
    for estimate in estimates:
        if not isinstance(estimate, dict):
            raise ValueError("Every estimate must be an object")
        product_id = str(estimate.get("id", ""))
        if product_id in estimate_by_id:
            raise ValueError(f"Duplicate estimate: {product_id}")
        hex_color = str(estimate.get("estimated_hex", ""))
        confidence = str(estimate.get("confidence", ""))
        if product_id not in sample_ids:
            raise ValueError(f"Estimate is outside the sample: {product_id}")
        if not HEX_PATTERN.fullmatch(hex_color):
            raise ValueError(f"Invalid estimated_hex for {product_id}: {hex_color}")
        if confidence not in CONFIDENCE_VALUES:
            raise ValueError(f"Invalid confidence for {product_id}: {confidence}")
        if not str(estimate.get("evidence", "")).strip():
            raise ValueError(f"Missing evidence for {product_id}")
        estimate_by_id[product_id] = estimate
    if set(estimate_by_id) != sample_ids:
        missing = sorted(sample_ids - set(estimate_by_id))
        raise ValueError(f"Missing estimates: {missing}")
    return sample, estimate_by_id


def load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(str(Path(r"C:\Windows\Fonts") / name), size)


def fit_image(path: Path, size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    return ImageOps.pad(image, size, method=Image.Resampling.LANCZOS, color="#F4F1E8")


def render_outputs() -> None:
    sys.path.insert(0, str(REPO))
    from centraldefilamentos.material_swatches import render_material_swatch

    sample, estimate_by_id = validate_estimates()
    SWATCH_DIR.mkdir(parents=True, exist_ok=True)
    card_width, card_height = 760, 286
    board = Image.new("RGB", (card_width * 2, card_height * 6), "#EDE9DF")
    title_font = load_font(21, bold=True)
    body_font = load_font(17)
    small_font = load_font(15)

    for index, product in enumerate(sample):
        product_id = str(product["id"])
        estimate = estimate_by_id[product_id]
        swatch_path = SWATCH_DIR / f"{product_id}.webp"
        render_material_swatch(
            str(estimate["estimated_hex"]),
            str(product["material_finish"]),
            swatch_path,
        )
        swatch = Image.open(swatch_path).convert("RGBA")
        if swatch.size != (160, 160):
            raise ValueError(f"Unexpected swatch size for {product_id}: {swatch.size}")
        card = Image.new("RGB", (card_width - 16, card_height - 16), "#FFFFFF")
        photo = fit_image(Path(str(product["image_path"])), (250, 250))
        card.paste(photo, (10, 10))
        swatch_background = Image.new("RGB", (180, 180), "#F4F1E8")
        swatch_background.paste(swatch, (10, 10), swatch)
        card.paste(swatch_background, (276, 10))
        draw = ImageDraw.Draw(card)
        draw.multiline_text(
            (474, 16),
            textwrap.fill(str(product["display_name"]), width=25),
            font=title_font,
            fill="#1B211F",
            spacing=3,
        )
        draw.text(
            (474, 78),
            f"{estimate['estimated_hex']} · {estimate['confidence']}",
            font=body_font,
            fill="#1B211F",
        )
        draw.text(
            (474, 110),
            f"Acabado: {product['material_finish']}",
            font=small_font,
            fill="#5A625E",
        )
        draw.multiline_text(
            (474, 142),
            textwrap.fill(str(estimate["evidence"]), width=32),
            font=small_font,
            fill="#5A625E",
            spacing=4,
        )
        warning = str(estimate.get("warning", "")).strip()
        if warning:
            draw.multiline_text(
                (474, 208),
                textwrap.fill(warning, width=32),
                font=small_font,
                fill="#A4492E",
                spacing=4,
            )
        x = (index % 2) * card_width + 8
        y = (index // 2) * card_height + 8
        board.paste(card, (x, y))

    board.save(BOARD_PATH, "WEBP", lossless=True, quality=100, method=6)
    print(f"Rendered {len(sample)} swatches to {BOARD_PATH}")


def validate_review() -> None:
    review = load_json(REVIEW_PATH)
    if not isinstance(review, list) or len(review) != 12:
        raise ValueError("review.json must contain 12 decisions")
    sample = load_json(SAMPLE_PATH)
    if not isinstance(sample, list):
        raise ValueError("sample.json must contain a list")
    sample_ids = {str(item.get("id", "")) for item in sample if isinstance(item, dict)}
    review_ids: set[str] = set()
    accepted = 0
    for item in review:
        if not isinstance(item, dict):
            raise ValueError("Every review decision must be an object")
        product_id = str(item.get("id", ""))
        if product_id in review_ids:
            raise ValueError(f"Duplicate review decision: {product_id}")
        if not isinstance(item.get("accepted"), bool):
            raise ValueError(f"accepted must be boolean for {product_id}")
        review_ids.add(product_id)
        accepted += int(item["accepted"])
    if review_ids != sample_ids:
        raise ValueError("review.json ids must exactly match sample.json ids")
    print(f"Accepted {accepted}/12; threshold {'met' if accepted >= 9 else 'not met'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "validate", "render", "review"))
    command = parser.parse_args().command
    if command == "prepare":
        sample = prepare_sample()
        print(f"Prepared {len(sample)} products at {SAMPLE_PATH}")
    elif command == "validate":
        sample, _ = validate_estimates()
        print(f"Validated {len(sample)} estimates")
    elif command == "render":
        render_outputs()
    else:
        validate_review()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Generate the sample manifest**

Run:

```powershell
python C:\tmp\stockcentral-ai-color-pilot\pilot.py prepare
```

Expected: `Prepared 12 products at C:\tmp\stockcentral-ai-color-pilot\sample.json`.

- [ ] **Step 4: Verify sample eligibility**

Run:

```powershell
$sample = Get-Content -Raw C:\tmp\stockcentral-ai-color-pilot\sample.json | ConvertFrom-Json
$sample.Count
$sample | Where-Object { -not (Test-Path $_.image_path) }
```

Expected: count `12` and no missing-image rows.

### Task 2: Inspect Images and Record Structured Estimates

**Files:**
- Read: `C:\tmp\stockcentral-ai-color-pilot\sample.json`
- Read: the 12 local image paths recorded in `sample.json`
- Create: `C:\tmp\stockcentral-ai-color-pilot\estimates.json`

**Interfaces:**
- Consumes: sample records from `prepare_sample()`.
- Produces: exactly 12 objects accepted by `validate_estimates()`.

- [ ] **Step 1: Inspect every source image at original detail**

For each `image_path` in `sample.json`, use the local image viewer with original detail. Identify the filament region before considering the normalized name. Treat labels, cardboard, spool plastic, background, highlights and shadows as distractors.

- [ ] **Step 2: Record one estimate per product**

Create `C:\tmp\stockcentral-ai-color-pilot\estimates.json` as a JSON list with this exact schema for every sample id:

```json
[
  {
    "id": "pla-pla-boutique-acqua-175-1000-grilon3",
    "estimated_hex": "#RRGGBB",
    "confidence": "high",
    "evidence": "The visible wound filament is the sampled region; the Acqua name supports the cyan-green reading.",
    "warning": ""
  }
]
```

Use `high` only when a clean filament region is visible, `medium` when lighting or packaging materially affects it, and `low` when the image cannot support a trustworthy single base color. `PLA Silk Tutti Frutti` must be flagged when its mixed-color appearance cannot be represented honestly by one RGB value.

- [ ] **Step 3: Validate the estimates before rendering**

Run:

```powershell
python C:\tmp\stockcentral-ai-color-pilot\pilot.py validate
```

Expected: `Validated 12 estimates`. Fix the temporary JSON if validation reports a missing id, duplicate id, malformed hex, unsupported confidence or empty evidence.

### Task 3: Render and Present the Comparison Board

**Files:**
- Read: `C:\tmp\stockcentral-ai-color-pilot\sample.json`
- Read: `C:\tmp\stockcentral-ai-color-pilot\estimates.json`
- Create: `C:\tmp\stockcentral-ai-color-pilot\swatches\*.webp`
- Create: `C:\tmp\stockcentral-ai-color-pilot\comparison-board.webp`

**Interfaces:**
- Consumes: the validated sample and estimate maps.
- Produces: 12 deterministic 160 by 160 WebP swatches and one two-column review board.

- [ ] **Step 1: Render all estimates with the existing material renderer**

Run:

```powershell
python C:\tmp\stockcentral-ai-color-pilot\pilot.py render
```

Expected: `Rendered 12 swatches to C:\tmp\stockcentral-ai-color-pilot\comparison-board.webp`.

- [ ] **Step 2: Verify generated artifacts**

Run:

```powershell
$swatches = Get-ChildItem C:\tmp\stockcentral-ai-color-pilot\swatches\*.webp
$board = Get-Item C:\tmp\stockcentral-ai-color-pilot\comparison-board.webp
$swatches.Count
$board.Length
```

Expected: swatch count `12` and board size greater than `0` bytes.

- [ ] **Step 3: Inspect the board at original detail**

Open `C:\tmp\stockcentral-ai-color-pilot\comparison-board.webp` with the local image viewer. Confirm every row contains the correct product photo, readable product name, uppercase hex, confidence, finish and rendered swatch. Confirm warning text is visible for ambiguous cases.

- [ ] **Step 4: Confirm repository isolation**

Run:

```powershell
git status --short
```

Expected: status matches the baseline from Task 1; no new or modified production path was introduced by the pilot.

### Task 4: Record the Review Outcome

**Files:**
- Read: `C:\tmp\stockcentral-ai-color-pilot\comparison-board.webp`
- Create: `C:\tmp\stockcentral-ai-color-pilot\review.json`

**Interfaces:**
- Consumes: the comparison board and the user's visual decisions.
- Produces: 12 review decisions and a final acceptance count from `validate_review()`.

- [ ] **Step 1: Present the comparison board to the user**

Display the board in Codex using its absolute local path. Ask the user to identify estimates that are not useful orientation colors; do not silently treat the model's own visual judgment as acceptance.

- [ ] **Step 2: Record all 12 decisions**

Create `C:\tmp\stockcentral-ai-color-pilot\review.json` with one entry per product:

```json
[
  {
    "id": "pla-pla-boutique-acqua-175-1000-grilon3",
    "accepted": true,
    "failure_mode": "",
    "note": "Useful orientation color."
  }
]
```

For rejected or uncertain cases, use a concrete `failure_mode`: `colored_packaging`, `white_balance`, `reflection`, `mixed_color`, `translucent_material`, `generic_image`, or `other`.

- [ ] **Step 3: Calculate the outcome**

Run:

```powershell
python C:\tmp\stockcentral-ai-color-pilot\pilot.py review
```

Expected: `Accepted N/12; threshold met` when `N >= 9`, otherwise `Accepted N/12; threshold not met`.

- [ ] **Step 4: Report the decision without changing production data**

Report the acceptance count, confidence distribution and observed failure modes. If the threshold is met, recommend a separately designed reviewed metadata cache and actual `gpt-5.6-luna` API benchmark. If it is not met, recommend retaining the current CSS fallback and using manual overrides or deterministic segmentation for priority products.
