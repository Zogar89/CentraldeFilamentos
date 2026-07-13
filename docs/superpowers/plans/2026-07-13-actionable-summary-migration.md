# Actionable Summary Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the complete quote and provider-specific stock-watch workflow into the compact Summary table, then make Summary the default route while retaining a legacy Catalog route.

**Architecture:** Instance-based Svelte writable-store controllers extract stateful quote/watch orchestration from `CatalogApp.svelte` without changing storage schemas. Summary consumes those controllers and existing quote components in an actionable table. Route ownership changes only after feature parity, responsive behavior and persistence compatibility pass.

**Tech Stack:** Svelte 5 legacy syntax, Svelte writable stores, JavaScript ES modules, Node.js 24 test runner, Vite 8, pytest source-contract tests, browser localStorage.

## Global Constraints

- Preserve `centraldefilamentos.quoteList.v1` and `centraldefilamentos.stockSubscriptions.v1` payloads.
- Preserve unknown-schema read-only behavior and failed-catalog no-write behavior.
- `+1` acts on a product/presentation; a bell acts on a product-provider pair.
- Rows without a provider offer have no bell for that provider.
- Keep unknown stock distinct from confirmed zero.
- Reuse existing quote panel, drawer, import/export, coverage and WhatsApp components.
- Preserve the current local user change `showQuickControls: true` in `CatalogApp.svelte` and `src/lib/quoteList.js`.
- Keep Catalog available at `catalogo.html` but remove it from primary navigation.
- Validate desktop and mobile before the root-route cutover.

---

### Task 1: Extract the quote workspace controller

**Files:**
- Create: `src/lib/quoteWorkspace.js`
- Create: `tests/quoteWorkspace.test.js`
- Modify: `package.json`

**Interfaces:**
- Produces: `createQuoteWorkspace({ products, catalogAvailable, storage })`.
- Store state: `{items, settings, storageWarning, reconcileNotice, readOnly, preservedPayload}`.
- Actions: `addProduct`, `setQuantity`, `removeProduct`, `clear`, `toggleQuickControls`, `previewImport`, `applyImport`, `exportJson`.

- [ ] **Step 1: Write failing controller tests**

```javascript
test("quote workspace preserves existing storage and adds a product", () => {
  const storage = memoryStorage(EXISTING_V1_PAYLOAD);
  const workspace = createQuoteWorkspace({ products: [PRODUCT], catalogAvailable: true, storage });
  workspace.addProduct(PRODUCT);
  const state = get(workspace.state);
  assert.equal(state.items[0].quantity, 2);
  assert.equal(JSON.parse(storage.value).schemaVersion, 1);
});

test("failed catalog initialization does not overwrite the stored list", () => {
  const storage = memoryStorage(EXISTING_V1_PAYLOAD);
  createQuoteWorkspace({ products: [], catalogAvailable: false, storage });
  assert.equal(storage.writeCount, 0);
});
```

- [ ] **Step 2: Add the test to the Node script and verify failure**

Change `test:quote-list` to include `tests/quoteWorkspace.test.js`. Run: `npm run test:quote-list`.

Expected: FAIL because `quoteWorkspace.js` is absent.

- [ ] **Step 3: Implement an instance-based writable controller**

```javascript
import { writable } from "svelte/store";
import {
  combineQuoteListItems,
  initializeQuoteList,
  loadQuoteList,
  normalizeQuoteList,
  previewQuoteListImport,
  saveQuoteList,
  serializeQuoteListExport,
  snapshotQuoteItem,
} from "./quoteList.js";

export function createQuoteWorkspace({ products, catalogAvailable, storage = globalThis.localStorage }) {
  const loaded = loadQuoteList(storage);
  const initialized = initializeQuoteList(loaded, { ok: catalogAvailable, products });
  const state = writable({
    items: initialized.items,
    settings: initialized.settings,
    storageWarning: "",
    reconcileNotice: initialized.removedCount ? `Quitamos ${initialized.removedCount} item(s) que ya no aparecen en el catálogo publicado.` : "",
    readOnly: loaded.readOnly,
    preservedPayload: loaded.preservedPayload,
  });
  return { state, addProduct, setQuantity, removeProduct, clear, toggleQuickControls, previewImport, applyImport, exportJson };
}
```

Implement each returned action with the existing pure helpers. Accept an injectable storage adapter by extending `loadQuoteList`/`saveQuoteList` with an optional storage argument, defaulting to `globalThis.localStorage`; keep existing callers compatible.

- [ ] **Step 4: Run all quote tests**

Run: `npm run test:quote-list`.

Expected: PASS.

- [ ] **Step 5: Commit the quote controller**

```powershell
git add package.json src/lib/quoteList.js src/lib/quoteWorkspace.js tests/quoteList.test.js tests/quoteWorkspace.test.js
git commit -m "refactor: extract quote workspace controller"
```

### Task 2: Extract the provider-specific stock-watch controller

**Files:**
- Create: `src/lib/stockWatchWorkspace.js`
- Create: `tests/stockWatchWorkspace.test.js`
- Modify: `src/lib/stockSubscriptions.js`
- Modify: `package.json`

**Interfaces:**
- Produces: `createStockWatchWorkspace({ products, storage })`.
- Store state: `{subscriptions, alerts}`.
- Actions: `toggle(product, offer)`, `isSubscribed(product, offer)`, `dismissAlerts()`.

- [ ] **Step 1: Write failing alert and provider-specific tests**

```javascript
test("watch subscriptions remain product-provider specific", () => {
  const workspace = createStockWatchWorkspace({ products: [PRODUCT], storage: memoryStorage() });
  workspace.toggle(PRODUCT, NORTH_OFFER);
  assert.equal(workspace.isSubscribed(PRODUCT, NORTH_OFFER), true);
  assert.equal(workspace.isSubscribed(PRODUCT, WEST_OFFER), false);
});

test("reappearing provider stock creates an alert", () => {
  const storage = memoryStorage(subscriptionPayload({ quantity: 0, signature: "out" }));
  const workspace = createStockWatchWorkspace({ products: [PRODUCT_WITH_NORTH_STOCK], storage });
  assert.equal(get(workspace.state).alerts[0].quantity, 4);
});
```

- [ ] **Step 2: Run Node tests and verify failure**

Run: `npm run test:quote-list`.

Expected: FAIL because the controller is absent.

- [ ] **Step 3: Move reconciliation behind a writable controller**

Reuse `subscriptionKey`, `stockSignature`, `loadStockSubscriptions` and `saveStockSubscriptions`. Add optional storage injection to load/save helpers. Reproduce the exact current rules from `CatalogApp.svelte:572-640`: alert when stock returns or quantity increases, update observed signatures, and acknowledge current quantities on dismiss.

- [ ] **Step 4: Run Node tests**

Run: `npm run test:quote-list`.

Expected: PASS.

- [ ] **Step 5: Commit the watch controller**

```powershell
git add package.json src/lib/stockSubscriptions.js src/lib/stockWatchWorkspace.js tests/stockWatchWorkspace.test.js
git commit -m "refactor: extract stock watch controller"
```

### Task 3: Refactor legacy Catalog onto shared controllers

**Files:**
- Modify: `src/CatalogApp.svelte:1-122,369-640,649-902`
- Modify: `tests/test_frontend_assets.py:1-240`

**Interfaces:**
- Consumes both controllers from Tasks 1 and 2.
- Preserves existing Catalog rendering and component props.

- [ ] **Step 1: Add failing source assertions that ban duplicated orchestration**

```python
def test_catalog_uses_shared_interaction_controllers():
    catalog = (SRC / "CatalogApp.svelte").read_text(encoding="utf-8")
    assert "createQuoteWorkspace" in catalog
    assert "createStockWatchWorkspace" in catalog
    assert "function reconcileStockSubscriptions" not in catalog
    assert "function saveQuoteListState" not in catalog
    assert "showQuickControls: true" in catalog
```

- [ ] **Step 2: Run the focused source test**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_frontend_assets.py -k "shared_interaction"`.

Expected: FAIL.

- [ ] **Step 3: Initialize and subscribe to controller state**

After `stock.json` loads, create both controller instances. Subscribe during `onMount` and unsubscribe in `onDestroy`. Replace local mutation functions with thin calls such as `quoteWorkspace.addProduct(product)` and `watchWorkspace.toggle(product, offer)`. Keep visual feedback timers and import-file DOM handling in the component; keep persistence/reconciliation in controllers.

Do not revert the user's current `showQuickControls: true` defaults.

- [ ] **Step 4: Verify no behavior regression**

Run:

```powershell
npm run test:quote-list
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_frontend_assets.py
npm run build
```

Expected: PASS.

- [ ] **Step 5: Commit the legacy refactor**

```powershell
git add src/CatalogApp.svelte tests/test_frontend_assets.py
git commit -m "refactor: share Catalog interaction state"
```

### Task 4: Add the actionable Summary table and full quote workflow

**Files:**
- Modify: `src/SummaryApp.svelte:1-224`
- Modify: `src/styles/global.css`
- Modify: `tests/test_frontend_assets.py:240-310`

**Interfaces:**
- Consumes `createQuoteWorkspace`, `createStockWatchWorkspace`, `QuoteListPanel`, `QuoteListDrawer` and existing quote coverage components.
- Product row action: `quoteWorkspace.addProduct(row.product)`.
- Provider cell action: `watchWorkspace.toggle(row.product, cell.offer)`.

- [ ] **Step 1: Add failing Summary parity assertions**

```python
def test_summary_contains_actionable_quote_and_watch_surfaces():
    summary = (SRC / "SummaryApp.svelte").read_text(encoding="utf-8")
    for token in [
        "createQuoteWorkspace", "createStockWatchWorkspace", "QuoteListPanel",
        "QuoteListDrawer", "quote-summary-add", "summary-stock-watch",
        "stockAlerts", "previewQuoteListImport", "QuoteProviderCoverage",
    ]:
        assert token in summary
```

- [ ] **Step 2: Run focused frontend tests and verify failure**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_frontend_assets.py -k "summary_contains_actionable"`.

Expected: FAIL.

- [ ] **Step 3: Retain the exact provider offer in each Summary cell**

Change cell construction to:

```javascript
const cells = Object.fromEntries(sources.map((source) => [source.id, { units: 0, unknown: false, offer: null }]));
(product.offers || []).forEach((offer) => {
  const cell = cells[offer.source_id];
  if (!cell) return;
  cell.offer = offer;
  if (Number(offer.stock_quantity) > 0) cell.units += Number(offer.stock_quantity);
  else if (offer.stock_status === "unknown") cell.unknown = true;
});
```

Render a small official thumbnail beside the color swatch, SKU/EAN/Pantone as secondary metadata, a row-level `+1`, and a bell only when `cell.offer` exists. Give bells `aria-pressed`, provider-specific labels and 44px mobile tap targets. Show unknown stock as `—`, not `0`.

- [ ] **Step 4: Mount complete quote surfaces and alerts**

Initialize both controllers after payload load. Pass alerts to `SiteHeader`. Reuse the Catalog import dialog, live feedback region, side panel, floating trigger and drawer. On desktop, apply the existing `quote-list-layout-active` two-column shell; on mobile, hide the side panel and use the drawer.

- [ ] **Step 5: Run parity tests and build**

Run:

```powershell
npm run test:quote-list
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_frontend_assets.py
npm run build
```

Expected: PASS.

- [ ] **Step 6: Commit actionable Summary**

```powershell
git add src/SummaryApp.svelte src/styles/global.css tests/test_frontend_assets.py
git commit -m "feat: move quote and stock actions to Summary"
```

### Task 5: Cut over root routing and retain the legacy Catalog

**Files:**
- Create: `catalogo.html`
- Modify: `index.html`
- Modify: `resumen.html`
- Modify: `vite.config.js:9-17`
- Modify: `src/components/SiteHeader.svelte:1-63`
- Modify: `src/components/SiteFooter.svelte`
- Modify: `tests/test_frontend_assets.py`

**Interfaces:**
- `/CentraldeFilamentos/` mounts Summary.
- `/CentraldeFilamentos/catalogo.html` mounts Catalog.
- `/CentraldeFilamentos/resumen.html` replaces to root while preserving query/hash.

- [ ] **Step 1: Add failing route ownership tests**

```python
def test_summary_is_root_and_catalog_is_legacy_route():
    assert '/src/summary.js' in (ROOT / "index.html").read_text(encoding="utf-8")
    assert '/src/catalog.js' in (ROOT / "catalogo.html").read_text(encoding="utf-8")
    redirect = (ROOT / "resumen.html").read_text(encoding="utf-8")
    assert "location.replace" in redirect
    header = (SRC / "components" / "SiteHeader.svelte").read_text(encoding="utf-8")
    assert 'label: "Catálogo"' not in header
```

- [ ] **Step 2: Run route tests and verify failure**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_frontend_assets.py -k "root_and_catalog"`.

Expected: FAIL.

- [ ] **Step 3: Change route entry ownership**

Copy the current Catalog HTML shell to `catalogo.html`. Change `index.html` to load `/src/summary.js` and use Summary title/description. Make `resumen.html` a small compatibility page whose module script computes the root from `import.meta.env.BASE_URL` through a dedicated `src/summary-redirect.js`, then calls `location.replace(target + location.search + location.hash)`.

Update Vite inputs to `index`, `catalogo`, `resumen`, `estadisticas`. Remove Catalog from `SiteHeader` primary `navItems`; keep `Resumen` and `Proveedores`. Add `Catálogo anterior` as a secondary footer link to `catalogo.html`.

- [ ] **Step 4: Verify built route artifacts**

Run: `npm run build`.

Expected: `dist/index.html`, `dist/catalogo.html`, `dist/resumen.html` and `dist/estadisticas.html` all exist; built root references Summary assets.

- [ ] **Step 5: Commit route cutover**

```powershell
git add index.html catalogo.html resumen.html src/summary-redirect.js vite.config.js src/components/SiteHeader.svelte src/components/SiteFooter.svelte tests/test_frontend_assets.py
git commit -m "feat: make Summary the default view"
```

### Task 6: Responsive, accessibility and complete release verification

**Files:**
- Verify and modify only for reproduced acceptance failures: `src/SummaryApp.svelte`
- Verify and modify only for reproduced acceptance failures: `src/styles/global.css`
- Add a regression assertion for every reproduced failure: `tests/test_frontend_assets.py`

**Interfaces:**
- Validates the completed feature; introduces no new product contract.

- [ ] **Step 1: Run the complete automated suite**

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos
npm run test:quote-list
npm run build
```

Expected: PASS.

- [ ] **Step 2: Test legacy localStorage payloads in root Summary**

Seed existing v1 quote and stock-subscription JSON in DevTools, reload root Summary and verify quantities, watched provider cells and alerts survive. Seed an unknown future quote schema and verify read-only warning plus zero writes.

- [ ] **Step 3: Verify desktop and mobile behavior**

At 1440px, verify table plus side panel without overlapping provider columns. At 390px and 320px, verify readable product identity, horizontally scrollable provider columns if needed, 44px action targets, drawer focus trap and restored focus after close.

- [ ] **Step 4: Verify accessibility states**

Keyboard through search, quick lines, `+1`, every bell, floating list and drawer. Confirm visible focus, provider-specific bell labels, accurate `aria-pressed`, live quote feedback and alert announcements.

- [ ] **Step 5: Commit only verified fixes from the acceptance pass**

```powershell
git add src/SummaryApp.svelte src/styles/global.css tests/test_frontend_assets.py
git commit -m "fix: harden actionable Summary responsiveness"
```

If acceptance required no changes, do not create an empty commit. Finish with `git status --short` and confirm all pre-existing unrelated user files remain untouched.
