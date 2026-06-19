# Phase 01: quote-list-foundation - Research

**Researched:** 2026-06-19
**Domain:** Svelte static frontend, localStorage persistence, quote-list UI
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
## Implementation Decisions

### Where The List Appears
- **D-01:** On desktop, the list appears as a right-side panel only after the list has at least one item.
- **D-02:** On mobile, the list is accessed through a floating button with a checklist/list icon and item counter.
- **D-03:** Opening the mobile list shows a bottom drawer, not a full-screen modal or side drawer.
- **D-04:** The visual metaphor is checklist/list. Avoid cart, bag, checkout, and purchase metaphors.

### Adding Filaments
- **D-05:** The add action appears on each product presentation, not on each provider offer and not only at the base product/color level.
- **D-06:** Phase 1 does not ask the user to choose a provider when adding an item.
- **D-07:** Tapping add increments the item by `+1 carrete`; if the same item already exists, increment its quantity.
- **D-08:** After an item is added, the action can become compact quantity controls for that item.
- **D-09:** Presentations with no online stock registered can still be added, but must be marked as needing confirmation.

### Item Identity And Stored Snapshot
- **D-10:** Store `product.id` as the stable reconciliation key for local list items.
- **D-11:** Also store visible provider-facing snapshot data when available: SKU, EAN, article code, `original_name`, product name, material/line, color, brand, diameter, presentation, and quantity.
- **D-12:** SKU/EAN/article code are not reliable as the only key because the current catalog does not have SKU for every product and some SKUs repeat across presentations.
- **D-13:** Local list payloads must include a schema/version field so incompatible changes can be handled deliberately.
- **D-14:** If a saved item no longer reconciles to the current catalog, remove that item automatically and show a non-blocking notice with the count removed.
- **D-15:** If the saved schema/version is incompatible, reset or reject it in a controlled way rather than trying to use unknown data.
- **D-16:** Each visible list item shows name, brand, diameter, presentation, article code when present, and quantity.
- **D-17:** Missing key fields should be shown as per-field badges such as `sin codigo` or `sin diametro`.

### Quantity And Controls
- **D-18:** The unit is `carrete`, not kg. Existing requirements/roadmap wording that mentions kg should be interpreted as whole-spool quantity for this phase.
- **D-19:** Quantities are whole integers only; no fractional quantities.
- **D-20:** Minimum quantity is 1. If a decrement would go below 1, remove the item.
- **D-21:** Extended controls are `- / editable number / + / +6 / +12`.
- **D-22:** The catalog remains clean by default: each presentation can show a minimal `+1` action.
- **D-23:** After the first item is added, the list experience is active.
- **D-24:** A toggle controls whether extended controls are shown or hidden. Hiding extended controls does not disable autosave and does not delete the list.
- **D-25:** Samplers, unknown weight, and presentations without full data can still be added as whole units/carreteles, with badges or confirmation wording where appropriate.

### Framing And Notices
- **D-26:** The feature name in the UI is `Lista de cotizacion`.
- **D-27:** The main notice text is: `Usa esta lista para planificar tu compra. Confirma stock y precio final con cada proveedor.`
- **D-28:** The local-only notice appears inside the side panel/drawer below the title.
- **D-29:** Copy must avoid suggesting StockCentral sells products, processes orders, confirms purchase, or guarantees stock.

### Autosave And Clearing
- **D-30:** Save automatically on every list change: add, remove, edit quantity, toggle relevant persisted settings, or clear.
- **D-31:** Clearing the list requires a simple confirmation.
- **D-32:** If `localStorage` is unavailable or throws, keep the list in memory for the current session and warn that it will not be saved after closing.
- **D-33:** If catalog changes cause saved items to be removed during reconciliation, show a non-blocking notice inside the panel.

### the agent's Discretion
- The exact component split is left to the planner, but it should respect existing project conventions: shared JS helpers in `src/lib/`, Svelte components in `src/components/` or near the catalog if only catalog-specific, and styling in `src/styles/global.css`.
- The exact responsive breakpoint for showing the desktop side panel is left to the planner/designer, provided the mobile bottom drawer remains the mobile pattern.
- The exact icon implementation is flexible, but it must read as checklist/list and must not read as a shopping cart.

### the agent's Discretion
See locked section above; CONTEXT.md nests the discretion bullets under `Implementation Decisions`. [VERIFIED: .planning/phases/01-quote-list-foundation/01-CONTEXT.md]

### Deferred Ideas (OUT OF SCOPE)
## Deferred Ideas

- Import/export belongs to Phase 2.
- Provider coverage, per-provider checks, and provider sections belong to Phase 3.
- WhatsApp messages, message previews, and WhatsApp fallbacks belong to Phase 4.
- Provider ranking refinements, duplicate/similar detection, named lists, editable templates, and quote tracking remain v2 unless promoted.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LIST-01 | Usuario puede agregar un filamento a la lista desde el catalogo. | Add control belongs in each `presentation-row` and stores by `product.id`. [VERIFIED: src/CatalogApp.svelte + CONTEXT.md] |
| LIST-02 | Usuario puede ver la lista como herramienta de compra/cotizacion, no como carrito. | Use locked copy and checklist/list metaphor; avoid cart/checkout words and icons. [VERIFIED: 01-UI-SPEC.md + CONTEXT.md] |
| LIST-03 | Usuario puede editar cantidad en kg por item. | Superseded by `carrete`; implement editable whole integer quantity. [VERIFIED: CONTEXT.md] |
| LIST-04 | Usuario puede sumar rapido `+1 kg` y `+12 kg`. | Superseded by `+1`, `+6`, `+12` carretes. [VERIFIED: CONTEXT.md] |
| LIST-05 | Usuario puede quitar items y limpiar la lista. | Item remove is immediate; clear list needs confirmation. [VERIFIED: 01-UI-SPEC.md] |
| ITEM-01 | Cada item conserva material, color, marca, diametro y cantidad. | Store snapshot fields from current `stock.json` product shape plus quantity. [VERIFIED: public/data/stock.json sample inspection] |
| ITEM-02 | Cada item conserva codigo de articulo cuando el catalogo lo provee. | Store SKU/EAN/article/original name snapshot, but keep `product.id` as key. [VERIFIED: CONTEXT.md + public/data/stock.json sample inspection] |
| ITEM-03 | La UI indica cuando algun dato clave no esta disponible o debe confirmarse. | Use locked missing-data badges and `confirmar stock`. [VERIFIED: 01-UI-SPEC.md] |
| PERS-01 | La lista se guarda automaticamente en este navegador/dispositivo. | Use versioned `localStorage` helper with save on every state mutation. [VERIFIED: src/lib/stockSubscriptions.js + MDN localStorage] |
| PERS-02 | La UI avisa que la lista local no se sincroniza y puede no estar disponible desde otra PC/navegador. | Show locked local-only notice inside panel/drawer. [VERIFIED: 01-UI-SPEC.md] |
| DISC-01 | La UI comunica que StockCentral no vende productos ni procesa pedidos. | Show locked non-commerce notice. [VERIFIED: 01-UI-SPEC.md] |
</phase_requirements>

## Summary

Implement Phase 1 as a browser-only Svelte feature inside the existing catalog page. The planner should add a focused quote-list persistence module under `src/lib/`, quote-list components for presentation controls, side panel, mobile floating button, drawer, list items, and quantity controls, and CSS in `src/styles/global.css`. This phase must not add backend code, generated data edits, provider selection, coverage logic, WhatsApp generation, import/export, or new package dependencies. [VERIFIED: CONTEXT.md + .planning/codebase/STRUCTURE.md + package.json]

The durable key is `product.id`; `stock.json` currently exposes product fields including `id`, `brand`, `color`, `diameter_mm`, `display_name`, `ean`, `material`, `offers`, `sku`, `variant`, and `weight_g`. A sample audit found 370 products, 223 without SKU, 225 without EAN, 15 without diameter, 66 without weight, 10 without offers, and repeated SKU examples across presentations, so SKU/EAN must be snapshot fields only. [VERIFIED: public/data/stock.json sample inspection]

**Primary recommendation:** Build a new `src/lib/quoteList.js` helper plus Svelte components integrated at `.presentation-row`, with schema-versioned localStorage, reconciliation after `stock.json` loads, in-memory fallback on storage failure, and planner-owned tests in `tests/test_frontend_assets.py`. [VERIFIED: src/CatalogApp.svelte + src/lib/stockSubscriptions.js + tests/test_frontend_assets.py]

## Project Constraints (from AGENTS.md)

- Responder en español; code and technical names may stay in English when the project already uses them. [VERIFIED: AGENTS.md]
- Before large or multi-file changes, explain the plan and ask confirmation; small scoped changes may be made directly. [VERIFIED: AGENTS.md]
- On this Windows 10 machine, do not assume Codex bundled workspace dependencies are available; use system Node/Python/tools or another route. [VERIFIED: AGENTS.md]
- Static hosting on GitHub Pages means no server endpoints or sessions. [VERIFIED: AGENTS.md]
- Persistence is limited to `localStorage` or cookies; data is local and not synced. [VERIFIED: AGENTS.md]
- StockCentral does not sell or process orders; copy/icons must reinforce planning/cotizacion. [VERIFIED: AGENTS.md]
- `public/data/stock.json` is generated; do not manually edit it for durable product/offers changes. [VERIFIED: AGENTS.md]
- Availability and price must be confirmed with providers; messages must ask for cotizacion/disponibilidad, not promise final stock. [VERIFIED: AGENTS.md]
- Mobile first UX, with desktop opportunity for right-side list panel. [VERIFIED: AGENTS.md]
- Local Windows pytest command should use `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos` or another writable temp. [VERIFIED: AGENTS.md]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Add presentation to quote list | Browser / Client | Static data | The add action is triggered from Svelte-rendered `presentation-row` and reads current `stock.json` product data. [VERIFIED: src/CatalogApp.svelte] |
| Quote-list persistence | Browser / Client | localStorage | Existing stock-watch persistence is local browser state under `src/lib/stockSubscriptions.js`; no backend exists. [VERIFIED: src/lib/stockSubscriptions.js + AGENTS.md] |
| Schema validation and reconciliation | Browser / Client | Static data | Saved items reconcile against loaded `products` after `fetchJson("data/stock.json")`. [VERIFIED: src/CatalogApp.svelte + CONTEXT.md] |
| Desktop side panel | Browser / Client | CSS | Existing catalog layout and responsive rules live in Svelte plus `src/styles/global.css`. [VERIFIED: src/CatalogApp.svelte + src/styles/global.css] |
| Mobile drawer and floating button | Browser / Client | CSS/accessibility JS | Drawer state, Escape handling, backdrop close, focus behavior, and rendering are browser concerns. [CITED: https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-modal] |
| Product identity and display snapshot | Static data contract | Browser / Client | `stock.json` supplies `product.id` and visible fields; frontend stores a snapshot for resilience. [VERIFIED: public/data/stock.json sample inspection + CONTEXT.md] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Svelte | Installed 5.55.7; npm latest 5.56.3 modified 2026-06-07 | Existing catalog UI framework. | Already used by `src/CatalogApp.svelte`; do not migrate syntax during this phase. [VERIFIED: npm ls + npm registry + src/CatalogApp.svelte] |
| Vite | Installed 8.0.13; npm latest 8.0.16 modified 2026-06-15 | Static frontend build/dev server. | Existing `npm run build` and GitHub Pages build path use Vite. [VERIFIED: npm ls + npm registry + package.json] |
| @sveltejs/vite-plugin-svelte | Installed/latest 7.1.2 modified 2026-05-07 | Vite/Svelte compiler integration. | Existing Vite integration. [VERIFIED: npm ls + npm registry + vite.config.js] |
| Browser localStorage | Web platform API | Browser-local persistence. | Project requires static/local-only persistence and existing stock-watch helper uses localStorage. [VERIFIED: AGENTS.md + src/lib/stockSubscriptions.js] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| None new | N/A | Keep phase dependency-neutral. | Use plain Svelte, JavaScript, CSS, and existing helpers. [VERIFIED: package.json + 01-UI-SPEC.md] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New state library | Svelte store package | Not needed for a page-local list and would add dependency surface. [ASSUMED] |
| IndexedDB | Browser IndexedDB | Overkill for a small versioned list; localStorage matches project constraint. [VERIFIED: AGENTS.md] |
| Server persistence | API/backend | Disallowed by static GitHub Pages constraint. [VERIFIED: AGENTS.md] |
| Provider-level add | Add per offer/provider | Contradicts Phase 1 locked decision; provider coverage belongs to Phase 3. [VERIFIED: CONTEXT.md] |

**Installation:**
```bash
# No new packages for Phase 1.
npm ci
```

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `svelte` | npm | latest published 2026-06-07 | 4,824,776/week | github.com/sveltejs/svelte | SUS: too-new | Existing locked dependency only; do not upgrade in Phase 1. [VERIFIED: package-legitimacy + npm registry] |
| `vite` | npm | latest published 2026-06-01 | 142,402,157/week | github.com/vitejs/vite | SUS: too-new | Existing locked dependency only; do not upgrade in Phase 1. [VERIFIED: package-legitimacy + npm registry] |
| `@sveltejs/vite-plugin-svelte` | npm | latest published 2026-05-07 | 2,517,802/week | github.com/sveltejs/vite-plugin-svelte | OK | Existing dependency approved; no install change. [VERIFIED: package-legitimacy + npm registry] |

**Packages removed due to [SLOP] verdict:** none. [VERIFIED: package-legitimacy]
**Packages flagged as suspicious [SUS]:** `svelte`, `vite` due latest-version recency only; planner should not install or upgrade them in this phase. [VERIFIED: package-legitimacy]

## Architecture Patterns

### System Architecture Diagram

```text
Browser loads catalog page
  -> CatalogApp fetches data/stock.json through fetchJson/dataUrl
  -> Products render grouped by line/brand/diameter
  -> Each presentation-row exposes +1 quote-list action
     -> add/update item in Svelte state
     -> normalize/clamp quantity as whole carretes
     -> save schema-versioned payload to localStorage
        -> success: persisted local list
        -> failure: keep in-memory list and show warning
  -> On initial load after stock.json
     -> load localStorage payload
     -> reject incompatible schema or malformed payload
     -> reconcile saved productId values against current products
        -> found: refresh display snapshot
        -> missing: remove item and show non-blocking notice
  -> If item count > 0
     -> desktop > 960px: show right panel
     -> mobile <= 820px: show floating list button -> bottom drawer
```

### Recommended Project Structure

```text
src/
├── CatalogApp.svelte                 # integration point for list state and presentation controls
├── components/
│   ├── QuoteListPanel.svelte         # shared panel/drawer content
│   ├── QuoteListDrawer.svelte        # mobile bottom drawer shell
│   ├── QuoteListItem.svelte          # item metadata, badges, quantity, remove
│   └── QuoteQuantityControl.svelte   # - / input / + / +6 / +12
├── lib/
│   └── quoteList.js                  # schema, load/save, normalize, snapshot, reconcile
└── styles/
    └── global.css                    # quote-list layout and responsive styles
```

### Pattern 1: Focused Versioned Persistence Helper

**What:** Create a new helper rather than expanding `stockSubscriptions.js`; use a key like `centraldefilamentos.quoteList.v1`, `{ schemaVersion, items, settings }`, defensive parsing, and explicit load/save status. [VERIFIED: src/lib/stockSubscriptions.js + CONTEXT.md]

**When to use:** Use for all quote-list load/save/reconcile operations. [VERIFIED: CONTEXT.md]

**Example:**
```javascript
// Source: src/lib/stockSubscriptions.js pattern, adapted for quote list.
export const quoteListStorageKey = "centraldefilamentos.quoteList.v1";
export const quoteListSchemaVersion = 1;

export function loadQuoteList() {
  if (typeof localStorage === "undefined") {
    return { items: [], settings: {}, storageAvailable: false, resetReason: "" };
  }
  try {
    const payload = JSON.parse(localStorage.getItem(quoteListStorageKey) || "null");
    return normalizeQuoteListPayload(payload);
  } catch {
    return { items: [], settings: {}, storageAvailable: false, resetReason: "storage-error" };
  }
}
```

### Pattern 2: Snapshot from Current Product

**What:** Build a quote item from the current presentation product, using `product.id` as `productId` and storing visible metadata. [VERIFIED: public/data/stock.json sample inspection + CONTEXT.md]

**When to use:** On add, increment, reconciliation refresh, and import/export in later phases. [VERIFIED: CONTEXT.md]

**Example:**
```javascript
// Source: stock.json product fields inspected 2026-06-19.
export function snapshotQuoteItem(product, quantity = 1) {
  return {
    productId: product.id,
    quantity: clampQuoteQuantity(quantity),
    snapshot: {
      productName: productBaseName(product),
      displayName: product.display_name || "",
      material: product.material || "",
      line: lineLabel(product),
      color: product.color || "",
      brand: product.brand || "",
      diameterMm: product.diameter_mm || null,
      presentation: formatPresentation(product),
      sku: product.sku || "",
      ean: product.ean || "",
      originalName: (product.offers || []).find((offer) => offer.original_name)?.original_name || "",
    },
  };
}
```

### Pattern 3: Reconcile After Static Data Load

**What:** Load saved list after `stock.json` is available, drop missing `productId`s, refresh snapshots for matched products, and surface a count notice. [VERIFIED: src/CatalogApp.svelte + CONTEXT.md]

**When to use:** In `onMount` after `products = payload.products || []`. [VERIFIED: src/CatalogApp.svelte]

### Anti-Patterns to Avoid

- **Using SKU/EAN as primary key:** Current data has many missing SKU/EAN values and repeated SKUs across presentations. [VERIFIED: public/data/stock.json sample inspection]
- **Putting quote state in `stockSubscriptions.js`:** Stock watches are provider-specific and keyed by `productId::sourceId`; quote list is presentation-specific and provider-neutral. [VERIFIED: src/lib/stockSubscriptions.js + CONTEXT.md]
- **Editing `public/data/stock.json`:** It is generated and frontend work should consume it read-only. [VERIFIED: AGENTS.md]
- **Adding cart language or cart icons:** This violates locked product framing. [VERIFIED: CONTEXT.md + 01-UI-SPEC.md]
- **Marking drawer modal without behavior:** `aria-modal` does not implement focus or background behavior; code must do that. [CITED: https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-modal]
- **Using Svelte 5 syntax migration opportunistically:** Project files currently use `on:click`; preserve local style unless a separate migration is planned. [VERIFIED: src/CatalogApp.svelte + CITED: https://svelte.dev/docs/svelte/v5-migration-guide]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Catalog URL resolution | Manual string concatenation for static JSON | `dataUrl` and `fetchJson` | Vite base path `/CentraldeFilamentos/` is already handled there. [VERIFIED: src/lib/shared.js + vite.config.js] |
| Product labels | Duplicate formatter logic | `productBaseName`, `formatPresentation`, `diameterLabel`, `lineLabel` | Existing helpers encode sampler/presentation/line rules. [VERIFIED: src/lib/shared.js] |
| Color display | New swatch rules | `colorSwatchStyle` and `colorSwatchLabel` | Existing catalog uses these for product visuals. [VERIFIED: src/lib/shared.js + src/CatalogApp.svelte] |
| Storage failure detection | Assume `localStorage` always works | `try/catch` around read/write plus in-memory fallback | MDN documents `SecurityError` and policy failures. [CITED: https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage] |
| Modal accessibility | Visual-only drawer | Dialog semantics plus close button, Escape, focus return, backdrop/inert behavior | ARIA alone does not make a modal functional. [CITED: https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-modal] |

**Key insight:** The hard part is not rendering a list; it is preserving user trust when static catalog data changes, storage fails, or commerce language accidentally implies StockCentral sells products. [VERIFIED: CONTEXT.md + MDN localStorage]

## Common Pitfalls

### Pitfall 1: Quantity Unit Regression
**What goes wrong:** Planner follows roadmap/requirements wording and implements kg quantity. [VERIFIED: REQUIREMENTS.md + ROADMAP.md]
**Why it happens:** Requirements still contain old kg language. [VERIFIED: REQUIREMENTS.md]
**How to avoid:** Treat `carrete` as locked for quote-list quantity and keep kg only as product presentation text like `1 kg`. [VERIFIED: CONTEXT.md + 01-UI-SPEC.md]
**Warning signs:** Buttons say `+1 kg`, `+12 kg`, or item quantity renders as kg. [VERIFIED: 01-UI-SPEC.md]

### Pitfall 2: Storage Errors Are Invisible
**What goes wrong:** User thinks the list is saved but browser policy/private mode prevents persistence. [CITED: https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage]
**Why it happens:** Existing `stockSubscriptions.js` returns empty arrays on errors and does not expose warnings. [VERIFIED: src/lib/stockSubscriptions.js]
**How to avoid:** New helper should return `storageAvailable` and `resetReason`/`saveError`, and panel/drawer should show the locked error copy. [VERIFIED: 01-UI-SPEC.md]
**Warning signs:** Save function has no return value or UI never reads a storage error flag. [VERIFIED: src/lib/stockSubscriptions.js]

### Pitfall 3: Drawer Accessibility Drift
**What goes wrong:** Mobile drawer looks correct but keyboard/screen reader users can interact with background content or lose focus. [CITED: https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/]
**Why it happens:** `aria-modal="true"` is added without actual JS behavior. [CITED: https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-modal]
**How to avoid:** Plan Escape close, close button, focus on open, focus return to floating button, backdrop handling, and background scroll control. [CITED: https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-modal]
**Warning signs:** Drawer has `role="dialog"` but no `svelte:window` keydown or focus management. [VERIFIED: src/CatalogApp.svelte pattern for keydown]

### Pitfall 4: Provider Logic Sneaks Into Phase 1
**What goes wrong:** Add flow asks provider or builds coverage counts. [VERIFIED: CONTEXT.md]
**Why it happens:** Offers are visually nested inside each presentation row. [VERIFIED: src/CatalogApp.svelte]
**How to avoid:** Add control belongs beside presentation header or row-level controls, not inside each `.offer`. [VERIFIED: CONTEXT.md + src/CatalogApp.svelte]
**Warning signs:** Quote item key includes `source_id`, `provider_name`, or coverage count. [VERIFIED: src/lib/stockSubscriptions.js is provider-specific and should not be reused]

## Code Examples

### Quantity Clamp

```javascript
// Source: 01-CONTEXT.md D-19/D-20/D-21.
export function clampQuoteQuantity(value) {
  const next = Math.floor(Number(value));
  if (!Number.isFinite(next) || next < 1) return 1;
  return next;
}
```

### Reconciliation Return Shape

```javascript
// Source: 01-CONTEXT.md D-14/D-15 and src/CatalogApp.svelte load pattern.
export function reconcileQuoteList(items, products) {
  const byId = new Map(products.map((product) => [product.id, product]));
  const reconciled = [];
  let removedCount = 0;

  for (const item of items) {
    const product = byId.get(item.productId);
    if (!product) {
      removedCount += 1;
      continue;
    }
    reconciled.push(snapshotQuoteItem(product, item.quantity));
  }

  return { items: reconciled, removedCount };
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Svelte 4 style event handlers as primary docs pattern | Svelte 5 docs recommend event attributes like `onclick`, while this codebase still uses `on:click` consistently | Svelte 5 migration docs current as of 2026-06-19 | Do not mix syntax unnecessarily; local convention wins for Phase 1. [CITED: https://svelte.dev/docs/svelte/v5-migration-guide + VERIFIED: src/CatalogApp.svelte] |
| Silent localStorage fallback | User-visible persistence status for quote list | Required by Phase 1 context | Storage helper must expose errors instead of swallowing them. [VERIFIED: CONTEXT.md + src/lib/stockSubscriptions.js] |
| Cart/checkout metaphor | Checklist/list cotizacion metaphor | Locked in UI spec/context | Copy and icons are part of requirements, not decoration. [VERIFIED: 01-UI-SPEC.md + CONTEXT.md] |

**Deprecated/outdated:**
- Requirement wording `kg` for quote-list quantity is superseded by `carrete`. [VERIFIED: CONTEXT.md + REQUIREMENTS.md]
- Building WhatsApp copy in Phase 1 is out of scope. [VERIFIED: CONTEXT.md + ROADMAP.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A new Svelte store/state library is unnecessary for this page-local list. [ASSUMED] | Standard Stack | If list complexity grows unexpectedly, planner may need a shared store abstraction later. |

## Open Questions (RESOLVED)

1. **Exact component split — RESOLVED**
   - Resolution: Use `src/lib/quoteList.js` for persistence/reconciliation helpers, `QuoteListPanel.svelte` as the shared list content shell, `QuoteListItem.svelte` for item metadata/badges, `QuoteQuantityControl.svelte` for quantity editing, and `QuoteListDrawer.svelte` as the thin mobile shell. `CatalogApp.svelte` owns page state and callbacks. [RESOLVED: 01-01-PLAN.md + 01-02-PLAN.md + 01-03-PLAN.md]
   - Rationale: This follows the pattern map: shared JS helpers mirror `stockSubscriptions.js`; content components mirror `SiteHeader`/`SiteFooter` prop-driven components; quantity controls mirror `QuickLines`; drawer shell mirrors the existing preview modal pattern without mixing provider logic into quote-list state. [VERIFIED: 01-PATTERNS.md]

2. **Focus-trap strictness for mobile drawer — RESOLVED**
   - Resolution: Phase 1 implements a bottom drawer with close button, Escape close, backdrop close, focus return to the floating list button, and background scroll control. If implementation uses `role="dialog" aria-modal="true"`, it must include the corresponding focus/background behavior; otherwise it must omit `aria-modal`. [RESOLVED: 01-03-PLAN.md]
   - Rationale: This keeps the drawer accessible enough for the phase without relying on ARIA alone or introducing a broader modal framework. [CITED: https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-modal]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Node.js | Vite build/dev | yes | v24.15.0 | Use CI Node 24 if local mismatch appears. [VERIFIED: command probe + STACK.md] |
| npm | Dependency install/build | yes | 11.13.0 | Use `npm ci` from lockfile. [VERIFIED: command probe + package.json] |
| Python | Pytest suite | yes, version mismatch | local 3.13.5; project/CI expects 3.12 | Prefer Python 3.12 env if Python-version bugs appear. [VERIFIED: command probe + STACK.md] |
| pytest | Validation | yes | 9.0.2 | Install dev deps if missing. [VERIFIED: `python -m pytest --version`] |
| Git | Optional research commit | yes | 2.35.1.windows.2 | Manual file handoff if commit tool fails. [VERIFIED: command probe] |

**Missing dependencies with no fallback:** none found. [VERIFIED: command probes]

**Missing dependencies with fallback:** local Python is 3.13.5 while project declares Python 3.12; use a 3.12 environment if a version-specific failure appears. [VERIFIED: command probe + STACK.md]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 local; project declares pytest >=8.2.0. [VERIFIED: command probe + pyproject.toml/STACK.md] |
| Config file | `pyproject.toml` pytest config. [VERIFIED: STACK.md] |
| Quick run command | `python -m pytest -v tests/test_frontend_assets.py --basetemp C:\tmp\pytest-centraldefilamentos` [VERIFIED: AGENTS.md + tests/test_frontend_assets.py] |
| Full suite command | `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos` and `npm run build` [VERIFIED: AGENTS.md + package.json] |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| LIST-01 | Add control exists at presentation row and not provider offer. | source invariant | `python -m pytest -v tests/test_frontend_assets.py -x --basetemp C:\tmp\pytest-centraldefilamentos` | yes, extend. [VERIFIED: tests/test_frontend_assets.py] |
| LIST-02 | Copy/metaphor says lista de cotizacion and avoids cart/checkout/order. | source invariant | same as above | yes, extend. [VERIFIED: tests/test_frontend_assets.py] |
| LIST-03 | Editable whole-carrete quantity exists. | source invariant | same as above | yes, extend. [VERIFIED: tests/test_frontend_assets.py] |
| LIST-04 | `+1`, `+6`, `+12` controls exist and no kg quote quantity labels. | source invariant | same as above | yes, extend. [VERIFIED: tests/test_frontend_assets.py] |
| LIST-05 | Remove item and clear with confirmation exist. | source invariant | same as above | yes, extend. [VERIFIED: tests/test_frontend_assets.py] |
| ITEM-01 | Snapshot stores material/color/brand/diameter/quantity. | source/helper invariant | same as above or new focused test | yes, extend. [VERIFIED: tests/test_frontend_assets.py] |
| ITEM-02 | Snapshot stores SKU/EAN/original/article fields when present. | source/helper invariant | same as above or new focused test | yes, extend. [VERIFIED: public/data/stock.json sample inspection] |
| ITEM-03 | Missing-data and confirm-stock badges exist. | source invariant | same as above | yes, extend. [VERIFIED: 01-UI-SPEC.md] |
| PERS-01 | Versioned localStorage key, schema, autosave, load/reconcile. | source invariant | same as above | yes, extend. [VERIFIED: src/lib/stockSubscriptions.js pattern] |
| PERS-02 | Local-only notice appears in panel/drawer. | source invariant | same as above | yes, extend. [VERIFIED: 01-UI-SPEC.md] |
| DISC-01 | Non-commerce notice appears. | source invariant | same as above | yes, extend. [VERIFIED: 01-UI-SPEC.md] |

### Sampling Rate

- **Per task commit:** `python -m pytest -v tests/test_frontend_assets.py -x --basetemp C:\tmp\pytest-centraldefilamentos` [VERIFIED: AGENTS.md]
- **Per wave merge:** `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos` plus `npm run build` [VERIFIED: AGENTS.md + package.json]
- **Phase gate:** Full suite and Vite build green before `$gsd-verify-work`. [VERIFIED: .planning/config.json]

### Wave 0 Gaps

- [ ] Extend `tests/test_frontend_assets.py` with quote-list source invariants for copy, storage key, schema handling, controls, no cart language, drawer/panel classes, and no kg quantity text. [VERIFIED: tests/test_frontend_assets.py]
- [ ] Consider a small JavaScript helper test path if planner wants behavior-level tests for `quoteList.js`; no JS test runner exists today. [VERIFIED: package.json + STACK.md]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No accounts or sessions in phase. [VERIFIED: AGENTS.md] |
| V3 Session Management | no | Browser-only local state, no server session. [VERIFIED: AGENTS.md] |
| V4 Access Control | no | Public static catalog. [VERIFIED: STACK.md] |
| V5 Input Validation | yes | Clamp editable quantity to whole integer >= 1; reject incompatible schema. [VERIFIED: CONTEXT.md] |
| V6 Cryptography | no | No secrets or crypto in phase. [VERIFIED: AGENTS.md + STACK.md] |

### Known Threat Patterns for Static Svelte/localStorage

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed saved JSON crashes UI | Tampering | Defensive parse, schema version check, controlled reset/reject. [VERIFIED: CONTEXT.md + src/lib/stockSubscriptions.js] |
| Browser policy blocks persistence | Reliability/DoS | Catch read/write errors, keep in-memory state, show warning. [CITED: https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage] |
| Misleading commerce copy | Spoofing/user trust | Locked no-commerce notice and banned cart/checkout/order metaphors. [VERIFIED: CONTEXT.md + 01-UI-SPEC.md] |
| Drawer traps or loses keyboard focus | Accessibility | Implement close, Escape, focus return, and background behavior if modal. [CITED: https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-modal] |

## Sources

### Primary (HIGH confidence)
- `AGENTS.md` - project constraints, static hosting, persistence, no-commerce framing, Windows test command. [VERIFIED: AGENTS.md]
- `.planning/phases/01-quote-list-foundation/01-CONTEXT.md` - locked decisions and deferred scope. [VERIFIED: CONTEXT.md]
- `.planning/phases/01-quote-list-foundation/01-UI-SPEC.md` - UI/copy/accessibility contract. [VERIFIED: 01-UI-SPEC.md]
- `src/CatalogApp.svelte` - current catalog integration, presentation rows, stock-watch pattern. [VERIFIED: codebase grep]
- `src/lib/stockSubscriptions.js` - localStorage key/normalize/save pattern. [VERIFIED: codebase grep]
- `src/lib/shared.js` - reusable display/data helpers. [VERIFIED: codebase grep]
- `public/data/stock.json` - sample product payload shape and missing/repeated code audit. [VERIFIED: node JSON inspection]

### Secondary (MEDIUM confidence)
- https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage - localStorage persistence and exceptions. [CITED: MDN]
- https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-modal - modal behavior requirements. [CITED: MDN]
- https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/ - APG dialog modal pattern notes. [CITED: W3C WAI]
- https://svelte.dev/docs/svelte/v5-migration-guide - Svelte 5 event handler note. [CITED: Svelte docs]
- https://svelte.dev/docs/svelte/if - conditional rendering syntax. [CITED: Svelte docs]

### Tertiary (LOW confidence)
- No tertiary sources used for implementation decisions; only A1 is an assumption. [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - versions verified locally and on npm; package-legitimacy flagged latest `svelte`/`vite` as too-new, so recommendation is no dependency changes. [VERIFIED: npm ls + npm registry + package-legitimacy]
- Architecture: HIGH - integration points are directly visible in code and phase context is locked. [VERIFIED: src/CatalogApp.svelte + CONTEXT.md]
- Pitfalls: MEDIUM - local pitfalls are code/context verified; accessibility/storage pitfalls are official-doc cited via websearch provider classified MEDIUM. [VERIFIED: codebase grep + CITED: MDN/WAI]

**Research date:** 2026-06-19
**Valid until:** 2026-07-19 for codebase-specific findings; re-check npm/docs before dependency upgrades. [ASSUMED]
