# High-Resolution Material Swatches Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Regenerate every referenced material swatch at 320 x 320 pixels so the existing design remains sharp in the 336-pixel preview modal.

**Architecture:** Keep the existing procedural shader and public data contract. Change only renderer output size, supersampling ratio and asset version, then regenerate Pantone and estimated WebPs and update their URLs deterministically.

**Tech Stack:** Python 3.12+, Pillow, pytest, existing Svelte/Vite frontend.

## Global Constraints

- Preserve the approved material shader, lighting, finish profiles and rounded mask.
- Set native output to exactly 320 x 320 pixels.
- Set `RENDERER_VERSION = 2` and `SUPERSAMPLING = 1`.
- Keep summary swatches at 24 x 24 CSS pixels and the preview modal unchanged.
- Preserve Pantone exclusion and every RGB estimate, confidence interval and finish value.
- Regenerate both Pantone and estimated referenced assets as version 2 WebPs.
- Do not stage or alter the user's unrelated UI work in `master`.

---

### Task 1: Version 2 Renderer Contract

**Files:**
- Modify: `tests/test_material_swatches.py`
- Modify: `centraldefilamentos/material_swatches.py`

**Interfaces:**
- Consumes: `material_swatch_url`, `estimated_material_swatch_url`, `render_material_swatch`.
- Produces: version 2 URLs and 320 x 320 lossless WebPs using the unchanged shader.

- [ ] **Step 1: Write failing size and URL tests**

Update the stable URL assertions to require `v2.webp` and the render-size assertion to require:

```python
assert image.size == (320, 320)
```

Keep the transparent-corner, opaque-center, deterministic-output and lighting-direction assertions unchanged.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
python -m pytest tests/test_material_swatches.py -v --basetemp C:\tmp\pytest-swatches-320-red
```

Expected: URL assertions report `v1` instead of `v2` and image size reports `(160, 160)` instead of `(320, 320)`.

- [ ] **Step 3: Implement the minimal renderer change**

Change only these constants in `centraldefilamentos/material_swatches.py`:

```python
RENDERER_VERSION = 2
SWATCH_SIZE = 320
SUPERSAMPLING = 1
```

The existing render path then saves the same 320-pixel internal shader result without the previous 160-pixel downsample.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the Step 2 command. Expected: every test in `tests/test_material_swatches.py` passes.

- [ ] **Step 5: Commit the renderer contract**

```powershell
git add centraldefilamentos/material_swatches.py tests/test_material_swatches.py
git commit -m "fix: render sharp material swatches"
```

### Task 2: Regenerate and Verify Public Assets

**Files:**
- Modify: `public/data/stock.json`
- Create: `public/assets/material-swatches/*-v2.webp`
- Remove after successful coverage verification: unreferenced `public/assets/material-swatches/*-v1.webp`

**Interfaces:**
- Consumes: version 2 renderer from Task 1 and the current public stock payload.
- Produces: complete version 2 asset coverage with no stale public references.

- [ ] **Step 1: Regenerate all public material swatches**

Run:

```powershell
python -m centraldefilamentos.generate_material_swatches --stock-json public/data/stock.json --public-dir public
```

Expected: every product with a resolved Pantone or estimated color receives a `v2.webp` URL.

- [ ] **Step 2: Verify exact output coverage and dimensions**

Read `public/data/stock.json` and assert for every non-empty `material_swatch_url`:

```python
assert url.endswith("-v2.webp")
assert path.is_file()
assert Image.open(path).size == (320, 320)
```

Also assert all Pantone products have no `estimated_color_` fields and all 301 no-Pantone products retain their five estimated-color fields.

- [ ] **Step 3: Remove only unreferenced version 1 generated assets**

After Step 2 passes, remove files matching `public/assets/material-swatches/*-v1.webp`. Re-run the coverage assertion to prove no public URL references a removed file.

- [ ] **Step 4: Verify tests and frontend build**

Run:

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos-swatches-320
npm.cmd run build
```

Expected: the complete Python suite passes and Vite exits successfully.

- [ ] **Step 5: Commit generated outputs**

```powershell
git add public/data/stock.json public/assets/material-swatches
git commit -m "data: regenerate high-resolution swatches"
```
