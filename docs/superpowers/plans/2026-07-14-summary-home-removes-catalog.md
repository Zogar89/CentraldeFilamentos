# Summary Home with Catalog Interactions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir Resumen en la portada unica, migrando antes filtros, ayuda, cotizacion, alertas y preview del Catalogo, y eliminar `CatalogApp.svelte`.

**Architecture:** `SummaryApp` conserva su tabla y agrupacion, pero adopta el estado de filtros y los controladores locales ya probados de cotizacion/seguimiento. Las acciones se ubican sobre la unidad correcta: `+1` por producto y campana por oferta de proveedor. `index.html` y `resumen.html` montan el mismo entrypoint.

**Tech Stack:** Svelte 5, Vite 8, JavaScript ES modules, CSS, pytest.

## Global Constraints

- La raiz publica es `/CentraldeFilamentos/`.
- `/resumen.html` permanece como alias.
- No eliminar `CatalogApp.svelte` hasta que las pruebas demuestren la migracion.
- Reutilizar sin cambiar esquemas `quoteList.js` y `stockSubscriptions.js`.
- Foto y render material miden 28 x 28 px y ofrecen preview con hover.
- Preservar cambios locales ajenos y no stagear `src/lib/quoteList.js`.
- Verificar con pytest usando `C:\tmp\pytest-centraldefilamentos` y con `npm run build`.

---

### Task 1: Migrate Full Filters to Summary

**Files:**
- Modify: `tests/test_frontend_assets.py`
- Modify: `src/SummaryApp.svelte`

- [ ] Add failing assertions to the Summary test:

```python
for filter_id in [
    "summary-search", "material-filter", "color-filter", "provider-filter",
    "variant-filter", "diameter-filter", "weight-filter", "brand-filter",
    "stock-filter",
]:
    assert filter_id in view
assert "filters, rows.filter(matchesFilters)" in view
assert "activeFilterChips" in view
assert "clearAllFilters" in view
```

- [ ] Run the focused test and confirm RED.

```powershell
python -m pytest tests/test_frontend_assets.py::test_summary_svelte_uses_carretes_totals_and_provider_order -v --basetemp C:\tmp\pytest-centraldefilamentos
```

- [ ] Replace scalar `query` with the exact filter state:

```javascript
let filters = {
  query: "",
  material: "",
  variant: "",
  color: "",
  diameter: "",
  weight: "",
  brand: "",
  provider: "",
  stock: "all",
};
let showMoreFilters = false;
```

Add derived option collections from `products`, and implement `matchesFilters(product)` using the existing comparisons from Catalog: search fields, exact material/variant/color/brand, numeric diameter/weight, provider offer membership, and stock status.

Build rows only from filtered products:

```javascript
$: filteredProducts = (filters, products.filter(matchesFilters));
$: rows = (filteredProducts, buildRows(filteredProducts));
$: visibleRows = rows;
```

Change `buildRows()` to `buildRows(items)` and map `items`.

- [ ] Replace the single search field with the complete controls from Catalog, preserving the listed ids. Use Summary group targets when changing `variant`.

- [ ] Run the focused test; expected GREEN.

### Task 2: Migrate Quote List, Stock Watch and Help

**Files:**
- Modify: `tests/test_frontend_assets.py`
- Modify: `src/SummaryApp.svelte`
- Modify: `src/components/SiteHeader.svelte`

- [ ] Add failing Summary assertions:

```python
for identifier in [
    "showCatalogHelp", "QuoteListPanel", "QuoteListDrawer",
    "loadQuoteList", "saveQuoteList", "snapshotQuoteItem",
    "loadStockSubscriptions", "saveStockSubscriptions",
    "addQuoteItem", "toggleStockSubscription",
    "quote-add-button", "stock-watch-button",
]:
    assert identifier in view
```

- [ ] Confirm RED with the focused Summary test.

- [ ] Import `onDestroy`, QuoteList components/functions and stock-subscription functions already used by Catalog.

- [ ] Migrate these state variables unchanged:

```javascript
let stockSubscriptions = [];
let stockAlerts = [];
let quoteItems = [];
let quoteSettings = { showQuickControls: true };
let quoteStorageWarning = "";
let quoteReconcileNotice = "";
let quoteDrawerOpen = false;
let quoteListReadOnly = false;
let preservedQuotePayload = null;
let quoteImportInput;
let quoteImportPreview = null;
let quoteImportError = "";
let quoteImportFileName = "";
let quoteAddFeedback = {};
let quoteFeedbackMessage = "";
let quotePulseKey = 0;
let stockWatchFeedback = {};
```

Also migrate both timer maps and the four quote warning strings.

- [ ] Extend `onMount` with the existing order: load subscriptions, reconcile, load quote list, initialize against `{ok, products}`, save when requested. Extend `onDestroy` to clear both timer maps.

- [ ] Migrate from Catalog without semantic changes the controller functions from `isSubscribed` through `stockWatchTargetId`, plus quote import/export/drawer handlers.

- [ ] Set the header call to:

```svelte
<SiteHeader
  active="summary"
  updatedAt={generatedAt}
  subtitle="Resumen por proveedor"
  showCatalogHelp
  {stockAlerts}
  onDismissStockAlerts={dismissStockAlerts}
/>
```

- [ ] Place `+1` beside each product name:

```svelte
<button
  class="quote-add-button summary-quote-add"
  class:confirmed={Boolean(quoteAddFeedback[row.product.id])}
  type="button"
  aria-label="Agregar 1 unidad a la lista de cotizacion"
  on:click={() => addQuoteItem(row.product)}
>
  {quoteAddFeedback[row.product.id] ? `✓ ${quoteAddFeedback[row.product.id]}` : "+1"}
</button>
```

- [ ] In every provider cell, find the offer with `source_id === source.id`; render its quantity and the existing bell button bound to `toggleStockSubscription(row.product, offer)`. No bell is rendered when no offer exists.

- [ ] Append the existing `QuoteListPanel`, floating button, `QuoteListDrawer`, import input and import dialog blocks after the table/main, using the same props and handlers as Catalog.

- [ ] Run the focused test; expected GREEN.

### Task 3: Add Paired Images and Hover Preview

**Files:**
- Modify: `tests/test_frontend_assets.py`
- Modify: `src/SummaryApp.svelte`
- Modify: `src/styles/global.css`

- [ ] Add failing assertions:

```python
for identifier in [
    "summary-product-visuals", "summary-product-photo",
    "row.product.thumbnail_url || row.product.image_url",
    "row.product.material_swatch_url", "showPreview",
    "movePreview", "hideHoverPreview", "image-preview",
]:
    assert identifier in view
```

CSS assertions:

```python
assert ".summary-product-visuals" in css
assert ".summary-product-photo" in css
assert "width: 28px" in css
assert "height: 28px" in css
```

- [ ] Confirm RED.

- [ ] Add preview state and generic image handlers:

```javascript
let preview = null;

function showPreview(event, src, title, meta) {
  preview = { src, title, meta, x: event.clientX + 16, y: event.clientY + 16, modal: false };
}

function movePreview(event) {
  if (!preview || preview.modal) return;
  preview = { ...preview, x: event.clientX + 16, y: event.clientY + 16 };
}

function hideHoverPreview() {
  if (!preview?.modal) preview = null;
}
```

- [ ] Render `.summary-product-visuals` with photo first and material render second. Bind `pointerenter`, `pointermove`, and `pointerleave` on both images. Use the original `image_url` for photo preview when available.

- [ ] Reuse the existing `.image-preview` floating markup from Catalog, without click-modal behavior because the requirement is hover.

- [ ] Add exact compact styles:

```css
.summary-product-visuals {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.summary-product-photo,
.summary-color-swatch {
  width: 28px;
  height: 28px;
  border: 1px solid color-mix(in srgb, var(--line) 82%, black);
  border-radius: 6px;
}

.summary-product-photo {
  display: block;
  object-fit: cover;
  background: var(--surface-soft);
}
```

- [ ] Run frontend tests and `npm run build`; expected GREEN.

### Task 4: Make Summary the Root and Remove Catalog

**Files:**
- Modify: `tests/test_frontend_assets.py`
- Modify: `index.html`
- Modify: `vite.config.js`
- Modify: `src/components/SiteHeader.svelte`
- Delete: `src/CatalogApp.svelte`
- Delete: `src/catalog.js`

- [ ] Update the static route test to require both HTML files to load `/src/summary.js`, absence of Catalog files, Summary nav pointing to `index.html`, and no Catalog nav label.

- [ ] Confirm RED.

- [ ] Change `index.html` title/description and script to Summary. Rename the Vite input key to `principal`.

- [ ] Reduce header nav to Summary and Proveedores; change brand aria-label to `Ir al resumen`.

- [ ] Delete `CatalogApp.svelte` and `catalog.js` only now.

- [ ] Remove the Catalog-only test and Catalog source concatenation from quote tests. Keep direct quote-module/component contracts.

- [ ] Run all frontend tests; expected GREEN.

- [ ] Commit only cleanly separable files:

```powershell
git add index.html vite.config.js src/components/SiteHeader.svelte src/CatalogApp.svelte src/catalog.js
git diff --cached --check
git commit -m "feat: make summary the primary view"
```

Leave mixed Summary/CSS/test files unstaged.

### Task 5: Full Verification

- [ ] Search for obsolete references:

```powershell
rg -n "CatalogApp|src/catalog.js|label: \"Catálogo\"" index.html resumen.html src vite.config.js tests
```

Expected: no runtime/test reference.

- [ ] Run:

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos
npm run build
git diff --check
git status --short
```

Expected: all tests pass; build emits index/resumen/estadisticas; only intended mixed local changes and unrelated pre-existing untracked files remain.
