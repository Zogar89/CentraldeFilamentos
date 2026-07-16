# UI/UX Automation Audit Design

## Objective

Create a repeatable Chrome-based audit that proves Central de Filamentos remains usable, accessible, responsive, and visually stable across desktop and mobile screens. The audit covers the current production build without changing product behavior.

## Source of truth

- Application code and static data from commit `c26b868`.
- Production-equivalent Vite preview served under `/CentraldeFilamentos/`.
- Current public surfaces: summary (`index.html` and `resumen.html`), Color Picker (`color-picker.html`), and vendor statistics (`estadisticas.html`).
- Chrome is the only interactive browser used for visual inspection, matching the repository instruction.

## Viewport matrix

| Profile | Viewport |
|---|---:|
| 4K desktop | 3840 × 2160 |
| 2K desktop | 2560 × 1440 |
| 1080p desktop | 1920 × 1080 |
| Small laptop | 1366 × 768 |
| Large mobile portrait | 412 × 915 |
| Mobile portrait | 390 × 844 |
| Small mobile portrait | 360 × 800 |
| Mobile landscape | 844 × 390 |

All profiles use Chrome with a device scale factor of 1 so layout assertions operate in CSS pixels and screenshots remain directly comparable.

## Automated coverage

### Cross-viewport smoke checks

Every public surface must:

- return a successful document response;
- render one visible `h1` and a visible main region;
- avoid uncaught page errors, console errors, failed same-origin requests, and broken rendered images;
- avoid horizontal document overflow;
- keep all visible interactive controls inside the viewport;
- expose an accessible name for every visible interactive control.

### Summary and quote workflow

The deep flow runs at 1920 × 1080 and 390 × 844:

1. Load the catalog and confirm products render.
2. Search and apply material, color, provider, and secondary filters.
3. Remove individual filter chips and clear all filters.
4. Add a product to the quote list.
5. Open the desktop side panel or mobile drawer.
6. Change quantity, complete a box of twelve, and verify the persisted state after reload.
7. Inspect provider coverage and the send step.
8. Toggle a provider-specific stock watch.
9. Open and close an image preview.
10. Verify keyboard entry, tab movement, Escape behavior, and focus restoration for dialogs.

### Color Picker workflow

The deep flow runs at 1920 × 1080 and 390 × 844:

1. Switch between continuous, family, and map views.
2. Toggle stock and sampler filters.
3. Select colors for comparison and enforce the four-color limit.
4. Search for similar colors.
5. Add an available presentation to the quote list.
6. Confirm the quote persists when navigating back to the summary.

### Accessibility

`@axe-core/playwright` scans the initial state of each route and the dynamic quote drawer, image modal, provider step, and Color Picker comparison state. The gate rejects serious and critical violations. Separate keyboard tests cover focus behavior that axe cannot prove.

### Visual regression

Stable screenshots are stored per Windows/Chrome project for:

- summary initial state;
- filtered summary;
- open quote drawer or panel;
- Color Picker palette;
- Color Picker comparison;
- statistics page or its disabled state.

Animations are disabled, local storage is cleared, and network idle plus image completion are required before capture. A small pixel tolerance absorbs font rasterization noise without accepting layout changes.

### Performance

Lighthouse CI audits the summary and Color Picker production builds in mobile emulation. Accessibility, best-practices, SEO, layout shift, and resource-size budgets are recorded. Performance is initially reported as a warning so the first measured baseline can be reviewed before becoming a hard gate.

## Evidence and reporting

The run writes Playwright HTML output, traces on failure, Lighthouse reports, and accepted screenshots. A concise report under `docs/ui-audit/2026-07-16/` records scope, strengths, issues by severity, viewport evidence, accessibility limits, and the exact commands and outcomes.

## Failure policy

Each distinct failure receives at most three evidence-driven attempts. Test-infrastructure faults may be corrected. Product defects are reproduced, captured, and reported; they are not silently fixed during this audit. The suite never retries indefinitely.
