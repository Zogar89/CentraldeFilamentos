# Catalog Color, Brand and Presentation Order Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `Color · Marca · Presentación` the default catalog result order while retaining total availability as a selectable alternative.

**Architecture:** Add a pure product comparator to `src/lib/catalogExplorer.js` and keep `buildSummaryRows()` order-preserving. Wire `src/SummaryApp.svelte` to select between the new comparator and the existing availability comparator, with source-level contract coverage for the default selector state.

**Tech Stack:** Svelte 5, JavaScript ES modules, Node `node:test`, pytest, Vite 8.

## Global Constraints

- Affect only catalog results; do not reorder the quote list, Color Picker, color ribbon, or filter options.
- Compare color and brand with the `es-AR` locale.
- Sort known weights numerically ascending, then diameter numerically ascending, then visible identity.
- Place samplers after known weights and products without a recognized presentation after samplers.
- Keep `Disponibilidad total` available and behaviorally unchanged.
- Use plain JavaScript; do not introduce TypeScript syntax.
- Run Python tests on Windows with `--basetemp C:\tmp\pytest-centraldefilamentos-order`.

---

### Task 1: Pure catalog identity comparator

**Files:**
- Modify: `tests/catalogExplorer.test.js`
- Modify: `src/lib/catalogExplorer.js`

**Interfaces:**
- Consumes: `presentationRank(product)` from `src/lib/shared.js` and product fields `color`, `brand`, `weight_g`, `diameter_mm`, `display_name`, and `id`.
- Produces: `compareCatalogProducts(left, right) -> number`, an `Array.prototype.sort()` comparator ordered by color, brand, presentation, diameter, and stable identity.

- [ ] **Step 1: Write the failing comparator test**

Add `compareCatalogProducts` to the existing import from `../src/lib/catalogExplorer.js` and append:

```js
test("catalog products sort by color, brand, presentation, and diameter", () => {
  const product = (id, color, brand, weight_g, diameter_mm) => ({
    id,
    color,
    brand,
    weight_g,
    diameter_mm,
    display_name: id,
    offers: [],
  });
  const sorted = [
    product("rojo-liviano", "Rojo", "3N3", 250, 1.75),
    product("azul-grilon-liviano", "Azul", "Grilon3", 250, 1.75),
    product("azul-3n3-pesado", "Azul", "3N3", 2500, 1.75),
    product("azul-3n3-medio-285", "Azul", "3N3", 1000, 2.85),
    product("azul-3n3-medio-175", "Azul", "3N3", 1000, 1.75),
  ].sort(compareCatalogProducts);

  assert.deepEqual(sorted.map((item) => item.id), [
    "azul-3n3-medio-175",
    "azul-3n3-medio-285",
    "azul-3n3-pesado",
    "azul-grilon-liviano",
    "rojo-liviano",
  ]);
});

test("catalog products place samplers before unknown presentations", () => {
  const base = {
    color: "Azul",
    brand: "3N3",
    diameter_mm: 1.75,
    offers: [],
  };
  const sorted = [
    { ...base, id: "unknown", display_name: "unknown", weight_g: null },
    {
      ...base,
      id: "sampler",
      display_name: "sampler",
      weight_g: null,
      offers: [{ original_name: "SAMPLER X 5 M" }],
    },
    { ...base, id: "weighted", display_name: "weighted", weight_g: 1000 },
  ].sort(compareCatalogProducts);

  assert.deepEqual(sorted.map((item) => item.id), ["weighted", "sampler", "unknown"]);
});
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
node --test tests/catalogExplorer.test.js
```

Expected: FAIL because `src/lib/catalogExplorer.js` does not export `compareCatalogProducts`.

- [ ] **Step 3: Implement the minimal comparator**

Add the shared import at the top of `src/lib/catalogExplorer.js`:

```js
import { presentationRank } from "./shared.js";
```

Add these helpers and export near `compareExplorerProducts`:

```js
function compareCatalogText(left, right) {
  return String(left || "").localeCompare(String(right || ""), "es-AR", {
    numeric: true,
    sensitivity: "base",
  });
}

function compareOptionalNumber(left, right) {
  const leftNumber = Number(left);
  const rightNumber = Number(right);
  const leftRank = Number.isFinite(leftNumber) && leftNumber > 0 ? leftNumber : Number.POSITIVE_INFINITY;
  const rightRank = Number.isFinite(rightNumber) && rightNumber > 0 ? rightNumber : Number.POSITIVE_INFINITY;
  if (leftRank === rightRank) return 0;
  return leftRank - rightRank;
}

export function compareCatalogProducts(left, right) {
  return compareCatalogText(left?.color, right?.color)
    || compareCatalogText(left?.brand, right?.brand)
    || presentationRank(left || {}) - presentationRank(right || {})
    || compareOptionalNumber(left?.diameter_mm, right?.diameter_mm)
    || compareCatalogText(left?.display_name || left?.id, right?.display_name || right?.id);
}
```

- [ ] **Step 4: Run the focused tests and verify GREEN**

Run:

```powershell
node --test tests/catalogExplorer.test.js
```

Expected: all catalog explorer tests PASS, including the unchanged availability test.

- [ ] **Step 5: Commit the pure behavior**

```powershell
git add tests/catalogExplorer.test.js src/lib/catalogExplorer.js
git commit -m "feat: add catalog identity order"
```

### Task 2: Make the identity order the catalog default

**Files:**
- Modify: `tests/test_frontend_assets.py`
- Modify: `src/SummaryApp.svelte`

**Interfaces:**
- Consumes: `compareCatalogProducts(left, right)` and `compareExplorerProducts(left, right)` from `src/lib/catalogExplorer.js`.
- Produces: catalog UI state where `sortOrder === "identity"` selects color-brand-presentation ordering and `sortOrder === "availability"` selects the previous total-availability ordering.

- [ ] **Step 1: Write the failing source-contract test**

Append this focused test to `tests/test_frontend_assets.py` without modifying existing local tests:

```python
def test_catalog_defaults_to_color_brand_presentation_order():
    summary = (SRC / "SummaryApp.svelte").read_text(encoding="utf-8")

    assert "compareCatalogProducts," in summary
    assert 'let sortOrder = "identity";' in summary
    assert '? compareExplorerProducts(left, right)' in summary
    assert ': compareCatalogProducts(left, right)' in summary
    assert '<option value="identity">Color · Marca · Presentación</option>' in summary
    assert '<option value="availability">Disponibilidad total</option>' in summary
```

- [ ] **Step 2: Run the focused contract test and verify RED**

Run:

```powershell
python -m pytest tests/test_frontend_assets.py::test_catalog_defaults_to_color_brand_presentation_order -v --basetemp C:\tmp\pytest-centraldefilamentos-order-red
```

Expected: FAIL because `SummaryApp.svelte` still defaults to `availability` and does not import or use `compareCatalogProducts`.

- [ ] **Step 3: Wire the new comparator and selector default**

Add `compareCatalogProducts` to the import from `./lib/catalogExplorer.js`.

Change the initial state to:

```js
let sortOrder = "identity";
```

Replace the inline fallback comparator in `filteredProducts` with:

```js
sortOrder === "availability"
  ? compareExplorerProducts(left, right)
  : compareCatalogProducts(left, right)
```

Replace the selector options with:

```svelte
<option value="identity">Color · Marca · Presentación</option>
<option value="availability">Disponibilidad total</option>
```

- [ ] **Step 4: Run the focused contract and JavaScript tests**

Run:

```powershell
python -m pytest tests/test_frontend_assets.py::test_catalog_defaults_to_color_brand_presentation_order -v --basetemp C:\tmp\pytest-centraldefilamentos-order-green
node --test tests/catalogExplorer.test.js
```

Expected: both commands PASS.

- [ ] **Step 5: Run project verification**

Run:

```powershell
npm run build
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos-order
```

Expected: Vite build succeeds and the complete Python suite passes.

- [ ] **Step 6: Commit the catalog default**

```powershell
git add tests/test_frontend_assets.py src/SummaryApp.svelte
git commit -m "feat: default catalog to identity order"
```
