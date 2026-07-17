# Option 1 Catalog Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the approved material-first Option 1 experience on the real StockCentral home route while preserving quote, provider, and local persistence behavior.

**Architecture:** Pure catalog exploration rules live in `src/lib/catalogExplorer.js` and are covered by Node tests. Focused Svelte components render material selection, color exploration, product rows, and the desktop quote rail, while `SummaryApp.svelte` remains the state owner and connects the existing quote workflow. New styles are scoped under `catalog-explorer-*` classes in the shared stylesheet.

**Tech Stack:** Svelte 5, JavaScript ES modules, Vite 8, CSS, Node test runner, Playwright, pytest.

## Global Constraints

- Hosting remains static GitHub Pages with no server endpoints.
- Material is always a hard filter and defaults to `PLA`.
- Quote state remains browser-local under the current schema and storage key.
- Stock and price remain subject to provider confirmation.
- Existing page URLs, navigation targets, data payloads, and source order remain stable.
- Real catalog images and the existing favicon are used; no placeholder or handmade vector assets are introduced.
- Desktop uses a persistent quote rail; mobile uses the existing quote drawer.

---

### Task 1: Pure material and color exploration model

**Files:**
- Create: `src/lib/catalogExplorer.js`
- Create: `tests/catalogExplorer.test.js`

**Interfaces:**
- Produces: `materialChoices(products): MaterialChoice[]`
- Produces: `matchesMaterialSelection(product, selectedMaterial): boolean`
- Produces: `colorChoices(products, selectedMaterial): ColorChoice[]`
- Produces: `productStockTotal(product): number`
- Produces: `compareExplorerProducts(left, right): number`

- [ ] **Step 1: Write failing tests** for core material ordering, `Otros`, material-scoped colors, representative HEX selection, stock totals, and availability sorting.
- [ ] **Step 2: Run `node --test tests/catalogExplorer.test.js`** and confirm failure because the module does not exist.
- [ ] **Step 3: Implement the pure helpers** with the exact exports above and no UI dependencies.
- [ ] **Step 4: Run `node --test tests/catalogExplorer.test.js`** and confirm all tests pass.

### Task 2: Material and color controls

**Files:**
- Create: `src/components/MaterialSelector.svelte`
- Create: `src/components/ColorRibbon.svelte`
- Modify: `src/components/SiteHeader.svelte`

**Interfaces:**
- `MaterialSelector` consumes `choices`, `selected`, and `onSelect`.
- `ColorRibbon` consumes `choices`, `selected`, `material`, `onSelect`, and `onClear`.
- `SiteHeader` adds optional catalog props `catalogMode`, `query`, `onQueryChange`, `quoteCount`, and `onOpenQuote`; existing call sites keep their current rendering.

- [ ] **Step 1: Add source-contract assertions** to `tests/test_frontend_assets.py` for the new components and material-first copy; run the focused test and confirm failure.
- [ ] **Step 2: Build the two controls** with real product images, semantic pressed states, keyboard focus, and material-scoped copy.
- [ ] **Step 3: Add the catalog header variant** while preserving the header used by Color Picker and internal statistics.
- [ ] **Step 4: Run the focused source tests and `npm.cmd run build`** and confirm both pass.

### Task 3: Product result rows and quote workspace

**Files:**
- Create: `src/components/CatalogExplorerResults.svelte`
- Modify: `src/components/QuoteListPanel.svelte`
- Modify: `src/SummaryApp.svelte`

**Interfaces:**
- `CatalogExplorerResults` consumes `rows`, `sources`, format and image helpers, and `onAdd`, `onPreview`, `onHoverPreview`, `onMovePreview`, `onHidePreview` callbacks.
- `QuoteListPanel` accepts an empty list and renders an explanatory empty state with its workflow action disabled.
- `SummaryApp` owns selected material, selected color, filters, product sorting, quote state, and responsive quote presentation.

- [ ] **Step 1: Add a Playwright expectation** that the default material is PLA, a selected color only yields PLA rows, and the desktop quote rail updates after adding a product; run it against the current UI and confirm failure.
- [ ] **Step 2: Replace the table-first markup** with material selection, color ribbon, secondary filters, compact product rows, and persistent desktop quote rail.
- [ ] **Step 3: Preserve existing actions** for image preview, import/export, quantity changes, provider coverage, WhatsApp preparation, stock watch, and quote persistence.
- [ ] **Step 4: Keep the quote drawer as the mobile interaction** and avoid opening it after desktop additions.
- [ ] **Step 5: Run the new Playwright flow** on desktop and mobile and confirm it passes.

### Task 4: Responsive visual implementation

**Files:**
- Modify: `src/styles/global.css`
- Modify: `tests/e2e/responsive.spec.js`
- Modify: `tests/e2e/touch-targets.spec.js`

**Interfaces:**
- Produces: stable layout classes prefixed with `catalog-explorer-` and `catalog-quote-`.

- [ ] **Step 1: Add layout assertions** for the persistent desktop rail, mobile drawer fallback, no document overflow, and minimum mobile control sizes; run them and confirm failure.
- [ ] **Step 2: Implement the approved light neutral and teal visual system** at 1440 x 1024 with the reference proportions.
- [ ] **Step 3: Implement responsive collapse rules** for 1080 desktop, 768 tablet, and 390 mobile.
- [ ] **Step 4: Run responsive, touch-target, accessibility, and runtime Playwright suites** and fix regressions.

### Task 5: Verification and design QA

**Files:**
- Create: `design-qa.md`
- Create: `docs/qa/evidence/option-1/option-1-desktop.png`
- Create: `docs/qa/evidence/option-1/option-1-mobile.png`

**Interfaces:**
- Produces: a browser-verified implementation and a blocking Product Design QA report.

- [ ] **Step 1: Run `node --test tests/catalogExplorer.test.js tests/colorPicker.test.js tests/quoteList.test.js tests/quoteCoverage.test.js`.**
- [ ] **Step 2: Run focused Python frontend tests** with a unique writable `--basetemp` and cache disabled.
- [ ] **Step 3: Run `npm.cmd run build`.**
- [ ] **Step 4: Test the primary journey in Chrome** at 1440 x 1024 and 390 x 844, including material, color, quote, provider coverage, WhatsApp message, focus, and console errors.
- [ ] **Step 5: Capture the implementation and compare it with the approved source in one combined visual.**
- [ ] **Step 6: Fix every P0, P1, and P2 issue, repeat comparison, and write `design-qa.md` with `final result: passed`.**

## Self-review

- Spec coverage: material-first navigation, scoped colors, exact stock, quote workflow, desktop rail, mobile drawer, accessibility, responsive behavior, and QA all map to explicit tasks.
- Placeholder scan: no deferred behavior or ambiguous implementation steps remain.
- Interface consistency: helper names and component props are consistent across all tasks.
