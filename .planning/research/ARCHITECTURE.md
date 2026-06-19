# Architecture Research

**Domain:** Browser-local quote/shopping list for a static Svelte catalog
**Researched:** 2026-06-18
**Confidence:** HIGH

## Standard Architecture

### System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                  Static Svelte Catalog Page                  │
│                    `src/CatalogApp.svelte`                   │
├──────────────────┬──────────────────┬───────────────────────┤
│ Product rows     │ Quote controls   │ Quote list panel      │
│ existing catalog │ add/update qty   │ coverage/messages     │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Browser-only Quote Domain                 │
├──────────────────┬──────────────────┬───────────────────────┤
│ `quoteList.js`   │ `quoteCoverage.js` │ `quoteMessages.js`   │
│ persistence      │ provider checks  │ copy/WhatsApp text    │
│ import/export    │ derived state    │ provider URLs         │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Existing Static Data Boundary              │
│          `public/data/stock.json` via `fetchJson()`           │
├─────────────────────────────────────────────────────────────┤
│ products[]: catalog identity, normalized fields, offers[]    │
│ sources[]: provider metadata and contact_whatsapp_url        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 Existing Generated Data Pipeline             │
│       Python ingestion, normalization, providers, caches      │
└─────────────────────────────────────────────────────────────┘
```

The feature should be a browser-local planning layer on top of the existing static catalog payload. It should not introduce accounts, server endpoints, checkout semantics, or manual edits to generated stock data.

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Catalog integration shell | Owns loaded `products`, `sources`, quote-list state, and passes actions into child components. | Extend `src/CatalogApp.svelte` after `fetchJson("data/stock.json")`; keep mount script unchanged. |
| Quote list persistence | Normalizes list payloads, saves/loads `localStorage`, exports/imports JSON, reconciles stale items. | New `src/lib/quoteList.js`, following the shape of `src/lib/stockSubscriptions.js`. |
| Quote coverage engine | Calculates provider coverage from current catalog products/offers and list items. | New pure helper `src/lib/quoteCoverage.js`; no DOM or storage access. |
| Quote message engine | Builds general copy text, provider-specific WhatsApp text, and WhatsApp URLs. | New pure helper `src/lib/quoteMessages.js`, reusing `sourceWhatsappUrl()` from `src/lib/shared.js`. |
| Add/update controls | Lets users add a presentation to the list and adjust quantity with `+1 kg`, `+12 kg`, and editable kg input. | New `src/components/QuoteAddControls.svelte`, rendered near each presentation row in `CatalogApp`. |
| Quote list panel | Shows current items, quantities, stale warnings, local-only notice, import/export, copy all, and clear/remove actions. | New `src/components/QuoteListPanel.svelte`; desktop sticky side panel or in-flow section, mobile drawer/bottom section. |
| Provider coverage view | Shows `X/Y`, item checks, full-coverage state, provider-specific covered items, and WhatsApp action. | New `src/components/ProviderCoverageTabs.svelte` or a section inside `QuoteListPanel.svelte` if simpler for v1. |
| Import/export dialog | Validates pasted/uploaded JSON and exposes download/copy export. | New focused component only if the panel becomes crowded; otherwise keep UI inside `QuoteListPanel.svelte`. |
| Existing shared helpers | Provide product labels, presentation labels, provider anchors, base URLs, and WhatsApp URL composition. | Extend `src/lib/shared.js` only for helpers reused across catalog, footer, and quote feature. |
| Existing stock pipeline | Remains the source of truth for products, offers, provider contact data, SKU/EAN, and stock counts. | No feature code writes `public/data/stock.json`; durable data changes go through Python pipeline modules. |

## Recommended Project Structure

```text
src/
├── CatalogApp.svelte                    # Integrates quote state with catalog products and sources
├── components/
│   ├── QuoteAddControls.svelte          # Add/update quantity controls per product presentation
│   ├── QuoteListPanel.svelte            # Local list, item editing, import/export, copy all
│   └── ProviderCoverageTabs.svelte      # Provider coverage and WhatsApp actions
├── lib/
│   ├── quoteList.js                     # Data model, localStorage, import/export normalization
│   ├── quoteCoverage.js                 # Provider coverage derived from items + products + sources
│   ├── quoteMessages.js                 # General and provider-specific message generation
│   ├── stockSubscriptions.js            # Existing stock-watch persistence, unchanged
│   └── shared.js                        # Existing shared formatting, URLs, provider helpers
└── styles/
    └── global.css                       # Quote panel, compact controls, provider coverage styles
```

### Structure Rationale

- **`src/lib/quoteList.js`:** keep persistence, versioning, migration, import/export, and quantity normalization out of `CatalogApp.svelte`; this mirrors the existing stock subscription storage boundary.
- **`src/lib/quoteCoverage.js`:** provider coverage is derived state, not persisted state. Keeping it pure makes coverage easy to test and prevents stale provider results in `localStorage`.
- **`src/lib/quoteMessages.js`:** copy generation has product/domain rules and should not live in Svelte markup. Provider-specific WhatsApp messages must be deterministic and independently testable.
- **`src/components/Quote*.svelte`:** UI belongs under existing `src/components/` because the catalog already uses shared Svelte components there.
- **`src/styles/global.css`:** the current app uses global CSS rather than component-scoped design tokens; quote styles should join the existing stylesheet and class naming style.

## Architectural Patterns

### Pattern 1: Persist Snapshots, Derive Coverage

**What:** Store only the user's intended quote-list items in `localStorage`; calculate provider coverage from the latest `products` and `sources` after the catalog payload loads.

**When to use:** Always for this feature. Provider stock changes over time, so persisted coverage would become misleading.

**Trade-offs:** Recomputing coverage on every state change is cheap at current catalog size and keeps results current. The list item needs a product snapshot so imported/stale items remain readable even if the product disappears from the current catalog.

**Example:**

```javascript
export const quoteListStorageKey = "centraldefilamentos.quoteList.v1";

export function quoteItemFromProduct(product, quantityKg = 1) {
  return {
    key: product.id,
    productId: product.id,
    productName: product.display_name || "Filamento",
    material: product.material || "",
    variant: product.variant || "",
    color: product.color || "",
    brand: product.brand || "",
    diameterMm: Number(product.diameter_mm || 0),
    weightG: Number(product.weight_g || 0),
    sku: product.sku || "",
    ean: product.ean || "",
    quantityKg: normalizeQuantityKg(quantityKg),
    addedAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}
```

### Pattern 2: Product-Level List Items, Offer-Level Coverage

**What:** A list item represents the desired normalized product/presentation. Provider coverage is determined by checking that product's `offers[]` for each provider.

**When to use:** Use this because the user is asking for "PLA negro Grilon3 1 kg" rather than binding the request to a provider at add time.

**Trade-offs:** Product identity depends on the existing normalized `product.id`, so normalization quality directly affects coverage quality. The benefit is that one list item can be evaluated across Filamentos3D, Grupo Senz, MundoInsumos, and future providers.

**Example:**

```javascript
export function coverageForSource(source, items, productsById) {
  const checks = items.map((item) => {
    const product = productsById.get(item.productId);
    const offer = (product?.offers || []).find((entry) => entry.source_id === source.id);
    return coverageCheck(item, product, offer);
  });

  return {
    source,
    totalCount: items.length,
    coveredCount: checks.filter((check) => check.covered).length,
    coversAll: items.length > 0 && checks.every((check) => check.covered),
    checks,
  };
}
```

### Pattern 3: Versioned Import/Export Contract

**What:** Export a small JSON envelope with schema/version metadata and normalized items. Import should accept both the envelope and a raw `items[]` array, then pass everything through `normalizeQuoteList()`.

**When to use:** Use this to compensate for no accounts/cloud sync while keeping old exports recoverable.

**Trade-offs:** Exported snapshots can contain products that are no longer in the catalog. Preserve readable labels, but mark them as not currently matchable during coverage.

**Example:**

```javascript
export function exportQuoteList(items) {
  return {
    app: "centraldefilamentos",
    type: "quote-list",
    version: 1,
    exportedAt: new Date().toISOString(),
    items: normalizeQuoteItems(items),
  };
}
```

## Data Model

### Persisted Payload

```json
{
  "app": "centraldefilamentos",
  "type": "quote-list",
  "version": 1,
  "items": [
    {
      "key": "pla-negro-175-1000-grilon3",
      "productId": "pla-negro-175-1000-grilon3",
      "productName": "PLA Negro Grilon3 1 kg",
      "material": "PLA",
      "variant": "",
      "color": "Negro",
      "brand": "Grilon3",
      "diameterMm": 1.75,
      "weightG": 1000,
      "sku": "M09INE175CJ",
      "ean": "7798049653037",
      "quantityKg": 12,
      "addedAt": "2026-06-18T12:00:00.000Z",
      "updatedAt": "2026-06-18T12:00:00.000Z"
    }
  ]
}
```

Recommended rules:

- Use `product.id` as `productId` and as the default item key. The current catalog already encodes material/color/diameter/weight/brand into product identity.
- Store quantity in kg as `quantityKg`, not units, because the product requirement is kg-based.
- Keep `weightG` in the snapshot so conversion from kg to reels remains possible even after export/import.
- Keep `sku` and `ean` as optional article identifiers. In UI copy, label `sku` as "codigo" when present; do not require it.
- Do not persist provider coverage, covered provider ids, WhatsApp URLs, or stock quantities.
- Normalize imported quantities to a bounded positive number. Suggested v1 bounds: minimum `0.1`, maximum `999`, rounded to one decimal for storage/display unless the UI chooses whole kg only.
- Reject non-array payloads, items without a `productId`/`key`, and obviously hostile oversized imports. Suggested cap: 100 items.

### Derived Coverage Shape

```javascript
{
  source,
  totalCount: 3,
  coveredCount: 2,
  coversAll: false,
  coveredItems: [/* checks where covered === true */],
  missingItems: [/* checks where covered === false */],
  checks: [
    {
      item,
      product,
      offer,
      covered: true,
      reason: "covered",
      requiredKg: 12,
      requiredUnits: 12,
      availableUnits: 18,
      availableKg: 18
    }
  ]
}
```

Coverage rules:

1. If the product is missing from current `products`, mark the check `covered: false`, `reason: "product_missing"`.
2. If the provider has no offer for that product, mark `reason: "provider_missing"`.
3. If the offer is not `in_stock` or `stock_quantity <= 0`, mark `reason: "out_of_stock"`.
4. If `weightG > 0`, calculate `requiredUnits = Math.ceil(quantityKg / (weightG / 1000))` and require `stock_quantity >= requiredUnits`.
5. If `weightG` is missing, allow stock-status coverage but mark quantity confidence as unknown. Prefer excluding sampler/lapiz products from quote-list v1 unless there is a clear kg conversion.
6. `coversAll` is true only when every item is covered by that provider.

## Data Flow

### List Creation Flow

```text
User clicks add / +1 kg / +12 kg
    ↓
QuoteAddControls emits product + quantity delta
    ↓
CatalogApp calls quoteList action from quoteList.js
    ↓
quoteList.js normalizes item and merges by productId
    ↓
CatalogApp updates local `quoteItems`
    ↓
saveQuoteList(quoteItems) writes localStorage
    ↓
QuoteListPanel and ProviderCoverageTabs re-render from derived state
```

### Coverage Flow

```text
fetchJson("data/stock.json")
    ↓
CatalogApp has products[] + sources[]
    ↓
quoteItems loaded from localStorage
    ↓
quoteCoverage.js builds productsById and checks offers[] per source.id
    ↓
ProviderCoverageTabs displays X/Y, per-item checks, full-provider check
    ↓
quoteMessages.js receives only covered checks for provider message generation
```

### WhatsApp Message Flow

```text
User selects provider WhatsApp action
    ↓
ProviderCoverageTabs passes source + coverage.coveredItems
    ↓
quoteMessages.js formats provider-specific consultative message
    ↓
shared.js sourceWhatsappUrl(source, message)
    ↓
Browser opens wa.me link in a new tab
```

Provider messages should include only covered items for that provider. Missing items belong in the UI coverage explanation, not in the WhatsApp message.

### Import/Export Flow

```text
Export button
    ↓
quoteList.js exportQuoteList(quoteItems)
    ↓
Download Blob or copy JSON text

Import file/paste
    ↓
JSON.parse with try/catch
    ↓
normalizeQuoteList(payload)
    ↓
Optional merge/replace user choice
    ↓
saveQuoteList(nextItems)
    ↓
Coverage recalculates against current products[]
```

## State Management

```text
localStorage: centraldefilamentos.quoteList.v1
    ↓ load on mount
CatalogApp local state: quoteItems
    ↓ derived
productsById, sourceCoverage, totalKg, itemCount
    ↓ props
QuoteListPanel / ProviderCoverageTabs / QuoteAddControls
    ↓ events/callbacks
CatalogApp actions
    ↓ save
localStorage
```

Use Svelte component state in `CatalogApp.svelte` rather than introducing an app-wide store. The current project uses component-local state plus small JS helper modules; keeping that pattern avoids global state complexity for a single-page feature.

## Build Order And Dependencies

1. **Quote data model and persistence**
   - Add `src/lib/quoteList.js`.
   - Implement `loadQuoteList`, `saveQuoteList`, `normalizeQuoteItems`, `upsertQuoteItem`, `removeQuoteItem`, `clearQuoteList`, `exportQuoteList`, and `parseImportedQuoteList`.
   - Dependency: existing product fields from `stock.json`; no UI dependency.

2. **Catalog add/update integration**
   - Add `QuoteAddControls.svelte`.
   - Wire `CatalogApp.svelte` to create/update items from each product presentation.
   - Dependency: `quoteList.js`, `formatPresentation()`, `productBaseName()`.

3. **Provider coverage engine**
   - Add `src/lib/quoteCoverage.js`.
   - Build coverage from `quoteItems`, `products`, and `sources`.
   - Dependency: quote item schema and current `product.offers[]`.

4. **Quote list panel**
   - Add `QuoteListPanel.svelte` for current items, editable quantities, remove/clear, local-only notice, copy full list, and import/export.
   - Dependency: persistence actions and coverage summary.

5. **Provider-specific messages**
   - Add `src/lib/quoteMessages.js`.
   - Reuse `sourceWhatsappUrl(source, message)` from `shared.js`.
   - Dependency: coverage checks so messages include only covered items.

6. **Provider coverage UI**
   - Add `ProviderCoverageTabs.svelte` or keep provider blocks inside `QuoteListPanel.svelte` for v1.
   - Show `X/Y`, per-item checks, full-provider check, covered item list, copy provider message, and WhatsApp button.
   - Dependency: `quoteCoverage.js` and `quoteMessages.js`.

7. **Responsive polish and copy review**
   - Add styles in `src/styles/global.css`.
   - Ensure copy says StockCentral/Central de Filamentos helps plan and consult, not sell or process orders.
   - Dependency: all user-visible surfaces are present.

## Anti-Patterns

### Persisting Provider Coverage

**What people do:** Store `coveredProviders`, `stockQuantity`, or generated WhatsApp URLs inside the saved list.

**Why it's wrong:** Stock and provider contact data change whenever `stock.json` is regenerated. Persisting derived coverage makes the UI lie after a data refresh.

**Do this instead:** Persist only item intent and snapshots; derive coverage from current `products` and `sources` after every load/update.

### Binding List Items To A Provider Too Early

**What people do:** Add "PLA negro from Filamentos3D" as the primary list item.

**Why it's wrong:** The feature's value is comparing which provider covers the desired product list. Provider binding at add time hides alternatives.

**Do this instead:** Add normalized products/presentations to the list, then calculate offer-level coverage per provider.

### Treating The Feature Like Checkout

**What people do:** Use cart/checkout/order language, totals, buy buttons, or confirmed availability wording.

**Why it's wrong:** The project explicitly does not sell, process orders, or confirm live stock.

**Do this instead:** Use "lista", "cotizacion", "consulta", "pedir precio y disponibilidad", and provider-specific WhatsApp messages with a consultative tone.

### Editing Generated Data For UI Needs

**What people do:** Patch `public/data/stock.json` directly to add list fields, contact details, or provider coverage.

**Why it's wrong:** The file is generated and will be overwritten by the data capture pipeline.

**Do this instead:** For frontend-only behavior, derive from current payload. For durable provider/contact/product data gaps, update `centraldefilamentos/providers.py`, metadata caches, normalization, connectors, or build mapping.

### Duplicating WhatsApp URL Logic

**What people do:** Reimplement `wa.me` URL encoding in the quote component.

**Why it's wrong:** `src/lib/shared.js` already has `sourceWhatsappUrl(source, message)` and handles existing query strings.

**Do this instead:** Put message text in `quoteMessages.js` and pass it to `sourceWhatsappUrl()`.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| WhatsApp / wa.me | Existing provider `contact_whatsapp_url` plus `sourceWhatsappUrl(source, message)`. | Open in new tab. Message must be URL-encoded and consultative. If a provider lacks WhatsApp, show copy action only. |
| Browser localStorage | Versioned key `centraldefilamentos.quoteList.v1`, try/catch on load/save. | Local to one browser/device. UI must say this clearly and provide import/export. |
| Browser download/upload | `Blob` download for export; file input or paste area for import. | Avoid File System Access API so GitHub Pages/mobile browsers keep working. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `CatalogApp.svelte` <-> `quoteList.js` | Direct function calls. | `CatalogApp` owns state; helper owns normalization and storage. |
| `CatalogApp.svelte` <-> quote components | Props plus callback props/events. | Keep DOM/UI in Svelte components, not helper modules. |
| `quoteCoverage.js` <-> `stock.json` payload | Plain arrays/maps passed from `CatalogApp`. | Coverage does not fetch data or read storage. |
| `quoteMessages.js` <-> `shared.js` | Import formatting helpers and WhatsApp URL helper only when reused. | Keep message text generation separate from URL generation. |
| Quote feature <-> Python data pipeline | Read-only via generated `products` and `sources`. | No backend assumptions; no generated-data edits. |

## Testing Implications

| Area | Recommended Tests | Why |
|------|-------------------|-----|
| Quote list normalization | Pure JS tests for invalid payloads, duplicate product ids, quantity bounds, snake_case/camelCase import compatibility, export envelope. | Prevents localStorage/import corruption. |
| Quantity conversion | Tests for `requiredUnits = ceil(quantityKg / unitKg)` across 1 kg and 2.5 kg products. | Coverage depends on kg-to-reel conversion. |
| Provider coverage | Pure JS tests for full coverage, partial coverage, missing product, missing provider offer, out-of-stock, insufficient stock, unknown weight. | This is the core decision logic for checks and `X/Y`. |
| Message generation | Tests that provider messages include only covered items, include quantity/product/code when present, and use consultative wording. | Prevents accidental checkout/confirmed-stock language. |
| Import/export UI | Component or integration smoke coverage if a frontend test runner exists; otherwise keep logic in pure modules and rely on `npm run build`. | Current repo has no JS test runner configured. |
| Static invariants | Extend `tests/test_frontend_assets.py` to assert new modules/components are referenced, storage key exists, and no generated data write path is introduced. | Matches current repo testing style. |
| Build verification | Run `npm run build`; run existing `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos` if frontend static invariant tests are added. | Current CI quality gates are pytest plus Vite build. |

If adding a JS test script is acceptable during implementation, prefer Node's built-in test runner to avoid new dependencies:

```json
{
  "scripts": {
    "test:frontend": "node --test src/lib/*.test.js"
  }
}
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Current static catalog | Component-local Svelte state plus pure helper modules is enough. Coverage can recompute on each list/product change. |
| Larger catalog or many providers | Memoize `productsById` and coverage inputs in `CatalogApp`; keep coverage pure and synchronous. |
| Multi-device/account future | Replace `quoteList.js` persistence adapter only; preserve item schema and coverage/message engines. This is explicitly out of scope for v1. |

### Scaling Priorities

1. **First bottleneck:** UI density on mobile if the list panel competes with catalog rows. Fix with a collapsible panel/drawer and concise provider summaries.
2. **Second bottleneck:** Coverage readability when providers grow. Fix with sorted provider coverage blocks and a "cubre todo" first sort, not backend changes.
3. **Third bottleneck:** Export/import compatibility after schema changes. Fix with `version` and migration in `normalizeQuoteItems()`.

## Sources

- `.planning/PROJECT.md` - project scope, active requirements, constraints, and product wording.
- `.planning/codebase/ARCHITECTURE.md` - current static frontend/data-pipeline boundaries and generated data rules.
- `.planning/codebase/STRUCTURE.md` - where frontend helpers/components and tests belong.
- `.planning/codebase/CONVENTIONS.md` - JavaScript/Svelte naming, formatting, module boundaries, and test/build gates.
- `src/CatalogApp.svelte` - current catalog state, product/offers rendering, and stock-watch integration point.
- `src/lib/stockSubscriptions.js` - existing localStorage persistence pattern.
- `src/lib/shared.js` - existing formatting helpers and `sourceWhatsappUrl()`.
- `src/components/SiteFooter.svelte` - current provider contact and WhatsApp behavior.
- `centraldefilamentos/models.py` and `centraldefilamentos/build_data.py` - public payload shape and generated stock/source contract.

---
*Architecture research for: browser-local quote list in the static Svelte catalog*
*Researched: 2026-06-18*
