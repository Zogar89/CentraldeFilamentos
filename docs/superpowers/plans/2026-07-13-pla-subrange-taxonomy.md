# PLA Subrange Taxonomy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add stable commercial PLA subranges and finish descriptors without changing existing product identities or stored user data.

**Architecture:** Python normalization becomes the single source of truth for additive `subrange` and `finish` fields. The public payload serializes both fields while `variant` and product-ID inputs remain unchanged. Shared frontend helpers provide backward-compatible labels, and Summary gains a material-to-subrange hierarchy.

**Tech Stack:** Python 3.12 dataclasses and pytest, Svelte 5, plain JavaScript, Vite 8.

## Global Constraints

- Do not change existing `variant` values or `build_product_id()` inputs.
- Preserve all existing product IDs and localStorage quote/watch references.
- Do not infer finishes from colors or marketing names outside the explicit mapping.
- Keep non-PLA `subrange` and `finish` empty.
- Use JavaScript, not TypeScript, under `src/`.
- Run pytest on Windows with `--basetemp C:\tmp\pytest-centraldefilamentos`.

---

### Task 1: Normalize additive PLA subrange fields

**Files:**
- Modify: `centraldefilamentos/models.py:24-33`
- Modify: `centraldefilamentos/normalize.py:39-67,173-224`
- Modify: `tests/test_normalize.py:21-145`

**Interfaces:**
- Changes: `NormalizedFields` gains `subrange: str` and `finish: str` after `manufacturer_name`.
- Produces: `pla_subrange(variant: str, material: str) -> tuple[str, str]`.
- Preserves: `build_product_id(fields: NormalizedFields) -> str` output.

- [ ] **Step 1: Write failing mapping and identity tests**

```python
@pytest.mark.parametrize(
    ("name", "subrange", "finish"),
    [
        ("PLA NEGRO GRILON3 1KG 1.75", "Standard", ""),
        ("PLA ASTRA CALIPSO GRILON3 1KG 1.75", "Astra", "Glitter"),
        ("PLA SILK AZUL GRILON3 1KG 1.75", "Silk", "Brillo metálico"),
        ("PLA WOOD CAOBA GRILON3 1KG 1.75", "Wood", "Madera"),
        ("PLA BOUTIQUE ACQUA GRILON3 1KG 1.75", "Boutique", ""),
        ("PLA 850 NEGRO GRILON3 1KG 1.75", "PLA 850", ""),
    ],
)
def test_normalizes_pla_commercial_subranges(name, subrange, finish):
    fields = normalize_record(raw(name, brand_hint="Grilon3"))
    assert (fields.subrange, fields.finish) == (subrange, finish)


def test_subrange_fields_do_not_change_existing_product_ids():
    fields = normalize_record(raw("PLA SILK AZUL GRILON3 1KG 1.75", brand_hint="Grilon3"))
    assert build_product_id(fields) == "pla-pla-silk-azul-175-1000-grilon3"
```

- [ ] **Step 2: Run normalization tests and verify failure**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_normalize.py`

Expected: FAIL because the fields are absent.

- [ ] **Step 3: Add the explicit mapping**

```python
PLA_SUBRANGES = {
    "": ("Standard", ""),
    "PLA Astra": ("Astra", "Glitter"),
    "PLA Silk": ("Silk", "Brillo metálico"),
    "PLA Wood": ("Wood", "Madera"),
    "PLA Boutique": ("Boutique", ""),
    "PLA 850": ("PLA 850", ""),
    "PLA 870": ("PLA 870", ""),
    "PLA Zeta": ("Zeta", ""),
}


def pla_subrange(variant: str, material: str) -> tuple[str, str]:
    if material != "PLA":
        return "", ""
    return PLA_SUBRANGES.get(variant, (variant, ""))
```

In `normalize_record()`, detect the existing material/variant first, call `pla_subrange()`, and pass both values to `NormalizedFields`. Leave `build_product_id()` unchanged.

- [ ] **Step 4: Run normalization and connector tests**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_normalize.py tests/test_grilon3_catalog.py`

Expected: PASS.

- [ ] **Step 5: Commit normalization**

```powershell
git add centraldefilamentos/models.py centraldefilamentos/normalize.py tests/test_normalize.py
git commit -m "feat: classify PLA commercial subranges"
```

### Task 2: Serialize the additive public contract

**Files:**
- Modify: `centraldefilamentos/models.py:51-75`
- Modify: `centraldefilamentos/build_data.py:55-130`
- Modify: `tests/test_models.py:4-49`
- Modify: `tests/test_build_data.py:48-100`

**Interfaces:**
- Changes: `ProductGroup` gains non-optional `subrange: str` and `finish: str` before `display_name`.
- Changes: every product JSON object includes both strings.

- [ ] **Step 1: Write failing serialization tests**

```python
def test_product_group_serializes_subrange_and_finish():
    product = product_group(subrange="Astra", finish="Glitter")
    payload = product.to_dict()
    assert payload["subrange"] == "Astra"
    assert payload["finish"] == "Glitter"


def test_build_payload_carries_normalized_subrange():
    payload = build_payload([raw(original_name="PLA ASTRA CALIPSO GRILON3 1KG 1.75")], generated_at="2026-07-13T00:00:00Z")
    assert payload["products"][0]["subrange"] == "Astra"
    assert payload["products"][0]["finish"] == "Glitter"
```

- [ ] **Step 2: Run model/build tests and confirm failure**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_models.py tests/test_build_data.py -k "subrange or groups_products"`

Expected: FAIL because `ProductGroup` does not accept the fields.

- [ ] **Step 3: Thread fields through product construction**

Add `subrange=fields.subrange` and `finish=fields.finish` to every `ProductGroup(...)` construction, including catalog-only official products. Update test factories and explicit constructors with empty strings where appropriate.

- [ ] **Step 4: Run the backend suite**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos`.

Expected: PASS.

- [ ] **Step 5: Commit the public contract**

```powershell
git add centraldefilamentos/models.py centraldefilamentos/build_data.py tests/test_models.py tests/test_build_data.py
git commit -m "feat: publish PLA subrange metadata"
```

### Task 3: Present the material-to-subrange hierarchy in Summary

**Files:**
- Modify: `src/lib/shared.js:30-118`
- Modify: `src/SummaryApp.svelte:6-132,137-218`
- Modify: `src/styles/global.css`
- Modify: `tests/test_frontend_assets.py:240-310`

**Interfaces:**
- Produces: `subrangeLabel(product) -> string` with legacy fallback.
- Produces: `finishLabel(product) -> string`.
- Summary grouping key includes material, subrange, brand, diameter and existing line.

- [ ] **Step 1: Add failing source-contract assertions**

```python
def test_summary_groups_pla_by_commercial_subrange():
    view = (SRC / "SummaryApp.svelte").read_text(encoding="utf-8")
    shared = (SRC / "lib" / "shared.js").read_text(encoding="utf-8")
    assert "subrangeLabel" in shared
    assert "finishLabel" in shared
    assert "product.material" in view
    assert "product.subrange" in view
    assert "group.finish" in view
```

- [ ] **Step 2: Run the focused frontend asset test**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_frontend_assets.py -k "summary"`

Expected: FAIL on the new assertions.

- [ ] **Step 3: Add backward-compatible helpers and hierarchy**

```javascript
export function subrangeLabel(product) {
  if (product?.subrange) return product.subrange;
  if (product?.material !== "PLA") return "";
  return lineLabel(product).replace(/^PLA\s+/, "") || "Standard";
}

export function finishLabel(product) {
  return product?.finish || "";
}
```

Make Summary's outer group the material (`PLA`, `PETG`, etc.) and the inner heading `[subrange, finish, brand, diameter]`. Do not merge rows or offers; only reorganize presentation. Show the finish as muted descriptive copy beside the subrange.

- [ ] **Step 4: Verify frontend contracts and build**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_frontend_assets.py`.

Run: `npm run build`.

Expected: both PASS.

- [ ] **Step 5: Commit Summary taxonomy**

```powershell
git add src/lib/shared.js src/SummaryApp.svelte src/styles/global.css tests/test_frontend_assets.py
git commit -m "feat: organize Summary by PLA subrange"
```

### Task 4: Regenerate and verify static data compatibility

**Files:**
- Generated: `public/data/stock.json`
- Inspect but do not stage unless the build reports a legitimate new event: `public/data/build_business_log.json`, `public/data/build_technical_log.json`

**Interfaces:**
- Consumes the unchanged build CLI.
- Produces public products with `subrange` and `finish`.

- [ ] **Step 1: Capture current product IDs before regeneration**

Run a read-only script that writes IDs to ignored `.image-curation/pla-product-ids-before.txt`; do not stage that file.

- [ ] **Step 2: Regenerate through the trusted pipeline**

Run: `python -m centraldefilamentos.build_data --output public/data/stock.json`.

Expected: successful quality gate and a stock payload where every product has both additive fields.

- [ ] **Step 3: Compare product identities**

Assert the sorted IDs for representative Standard, Astra, Silk, Wood, Boutique, 850, 870 and Zeta entries match the pre-change snapshot exactly. Investigate any removal/addition as source-data drift; do not attribute an ID change to taxonomy.

- [ ] **Step 4: Run complete verification**

Run:

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos
npm run test:quote-list
npm run build
```

Expected: PASS.

- [ ] **Step 5: Commit only legitimate generated changes**

```powershell
git add public/data/stock.json
git commit -m "data: publish PLA subrange metadata"
```

Do not stage unrelated stock-history, planning, attachment or pre-existing user files.
