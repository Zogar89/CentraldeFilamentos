# Phase 1: Quote List Foundation - Context

**Gathered:** 2026-06-19
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers the foundation of the local quote list inside the existing catalog: users can add filament presentations to a browser-local "Lista de cotizacion", adjust whole-spool quantities, see a non-commerce/local-only framing, and rely on automatic local persistence. This phase does not implement import/export, provider coverage views, or WhatsApp message generation; those are later phases.

</domain>

<decisions>
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Planning Context
- `.planning/PROJECT.md` - Product boundary, no-commerce positioning, local-only persistence constraint.
- `.planning/REQUIREMENTS.md` - Phase 1 requirements and traceability. Interpret kg quantity wording as superseded by this context's `carrete` decision.
- `.planning/ROADMAP.md` - Phase 1 scope and success criteria.
- `.planning/STATE.md` - Current phase/session state.
- `.planning/research/SUMMARY.md` - Research-backed architecture and pitfalls for quote list, local persistence, coverage, and WhatsApp flow.

### Codebase Maps
- `.planning/codebase/CONVENTIONS.md` - Naming, Svelte/JS style, localStorage helper conventions, and test expectations.
- `.planning/codebase/STRUCTURE.md` - Where frontend utilities, components, and styles belong.
- `.planning/codebase/STACK.md` - Svelte/Vite/static hosting constraints.

### Existing Code
- `src/CatalogApp.svelte` - Main integration point for adding presentations and rendering list controls.
- `src/lib/stockSubscriptions.js` - Existing localStorage pattern to mirror for load/save/normalize safety.
- `src/lib/shared.js` - Shared formatting helpers, product presentation helpers, and provider WhatsApp URL helper.
- `src/styles/global.css` - Existing compact catalog/list/card/offers styling patterns and responsive rules.
- `public/data/stock.json` - Current generated product payload shape; planner should inspect exact fields before finalizing item snapshot.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/lib/stockSubscriptions.js`: Demonstrates localStorage key naming, safe JSON parsing, normalization, and defensive fallback to empty state.
- `src/lib/shared.js`: Provides `formatPresentation`, `formatWeightLabel`, `diameterLabel`, `productBaseName`, `sourceWhatsappUrl`, and text/slug helpers.
- `src/CatalogApp.svelte`: Already groups products into base product cards and presentation rows; each presentation row is the chosen add-action location.
- `src/styles/global.css`: Has compact grid, product row, presentation row, offer, button, and responsive patterns that should be reused or extended.

### Established Patterns
- Frontend source is plain JavaScript and Svelte, not TypeScript.
- Svelte components use 2-space indentation, double quotes, semicolons, and named helper imports.
- Local browser state should be stored with a versioned key under the `centraldefilamentos.*.vN` pattern.
- Generated `public/data/stock.json` is read-only for frontend work; do not manually edit generated data for this phase.
- User-facing copy is Spanish/Argentina and compact.

### Integration Points
- Add quote-list state and reconciliation after `stock.json` loads in `src/CatalogApp.svelte`.
- Add a focused quote-list persistence/helper module under `src/lib/` rather than expanding `stockSubscriptions.js`.
- Add one or more quote-list UI components for the side panel, mobile drawer, floating button, and presentation add controls.
- Add CSS in `src/styles/global.css`, taking care not to disturb existing catalog layout and current uncommitted user changes in that file.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly corrected the unit from kg to `carrete`; `+1`, `+6`, and `+12` are whole-spool increments.
- The list should feel like planning/cotizacion, not buying. "Lista de cotizacion" is the locked UI name.
- The side panel should not be visible on desktop until there are items, preserving the current clean catalog.
- The mobile pattern should be a floating checklist/list button with count, opening a bottom drawer.
- Extended controls should be hideable through a toggle to keep the catalog clean, but hiding them must not delete or disable the list.

</specifics>

<deferred>
## Deferred Ideas

- Import/export belongs to Phase 2.
- Provider coverage, per-provider checks, and provider sections belong to Phase 3.
- WhatsApp messages, message previews, and WhatsApp fallbacks belong to Phase 4.
- Provider ranking refinements, duplicate/similar detection, named lists, editable templates, and quote tracking remain v2 unless promoted.

</deferred>

---

*Phase: 1-Quote List Foundation*
*Context gathered: 2026-06-19*
