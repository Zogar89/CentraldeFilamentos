# Codebase Structure

**Analysis Date:** 2026-06-18

## Directory Layout

```text
StockCentral/
├── .github/workflows/          # CI, data capture, UI publish, and thumbnail publish workflows
├── .planning/codebase/         # GSD codebase maps
├── centraldefilamentos/        # Python package for ingestion, normalization, enrichment, caches, and thumbnails
│   ├── connectors/             # Provider and catalog parsers/fetchers
│   └── data/                   # Versioned metadata caches and generated provider snapshots/history
├── docs/                       # Project documentation and operational workflow notes
│   └── superpowers/            # Product/spec/planning artifacts
├── public/                     # Static files served by Vite and GitHub Pages
│   ├── assets/                 # Versioned product images and generated thumbnails
│   └── data/                   # Public JSON consumed by frontend pages
├── src/                        # Svelte frontend source
│   ├── components/             # Shared Svelte UI components
│   ├── lib/                    # Shared frontend helpers and localStorage utilities
│   └── styles/                 # Global CSS
├── tests/                      # Pytest suite and fixtures
│   └── fixtures/               # HTML/CSV test fixtures
├── tools/image-curation/       # Local Node image review tool
├── dist/                       # Vite build output
├── index.html                  # Catalog HTML entry
├── resumen.html                # Summary HTML entry
├── estadisticas.html           # Internal vendor stats HTML entry
├── package.json                # Node/Vite/Svelte package manifest
├── pyproject.toml              # Python package and pytest config
├── vite.config.js              # Vite multi-page build config
└── svelte.config.js            # Svelte config
```

## Directory Purposes

**`centraldefilamentos/`:**
- Purpose: Python package for all non-UI domain logic and build-time data generation.
- Contains: Data orchestration, dataclasses, normalization rules, provider registry, thumbnail utilities, metadata cache scripts, and image update scripts.
- Key files: `centraldefilamentos/build_data.py`, `centraldefilamentos/models.py`, `centraldefilamentos/normalize.py`, `centraldefilamentos/providers.py`, `centraldefilamentos/thumbnails.py`.

**`centraldefilamentos/connectors/`:**
- Purpose: Isolate source-specific fetching and parsing.
- Contains: HTML table parsing for Filamentos3D stock, Google Sheets CSV parsing, Grilon3 catalog parsing, and Filamentos3D/3N3 catalog parsing.
- Key files: `centraldefilamentos/connectors/filamentos3d.py`, `centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/grilon3_catalog.py`, `centraldefilamentos/connectors/filamentos3d_catalog.py`.

**`centraldefilamentos/data/`:**
- Purpose: Store versioned metadata caches and generated internal snapshots/history that feed future builds.
- Contains: `centraldefilamentos/data/grilon3_metadata.json`, `centraldefilamentos/data/filamentos3d_metadata.json`, `centraldefilamentos/data/daily_provider_stock_snapshot.json`, `centraldefilamentos/data/provider_stock_history.json`.
- Key files: Use metadata cache files for durable enrichment; use snapshot/history files as generated build state.

**`src/`:**
- Purpose: Svelte frontend source for the static site.
- Contains: Three app components, three mount scripts, shared components, shared JS helpers, and global CSS.
- Key files: `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, `src/VendorStatsApp.svelte`, `src/catalog.js`, `src/summary.js`, `src/vendor-stats.js`.

**`src/components/`:**
- Purpose: Shared Svelte UI components used across pages.
- Contains: Header/navigation, footer/provider contact area, and quick line navigation.
- Key files: `src/components/SiteHeader.svelte`, `src/components/SiteFooter.svelte`, `src/components/QuickLines.svelte`.

**`src/lib/`:**
- Purpose: Shared browser-side helpers.
- Contains: Data URL handling, formatting, line metadata, search helpers, sorting/ranking, color swatches, WhatsApp URL composition, and localStorage persistence for stock watches.
- Key files: `src/lib/shared.js`, `src/lib/stockSubscriptions.js`.

**`src/styles/`:**
- Purpose: Global CSS for all Svelte entry pages.
- Contains: Shared page layout, header, filters, catalog rows, summary table, vendor stats, responsive rules, and visual tokens.
- Key files: `src/styles/global.css`.

**`public/data/`:**
- Purpose: Public static JSON read by frontend pages and published to `gh-pages/data/`.
- Contains: `public/data/stock.json`, `public/data/provider_stock_history.json`, `public/data/build_business_log.json`, `public/data/build_technical_log.json`, `public/data/feature_flags.json`.
- Key files: Treat `public/data/stock.json`, `public/data/provider_stock_history.json`, and build logs as generated outputs; edit `public/data/feature_flags.json` for static feature toggles.

**`public/assets/`:**
- Purpose: Public product image assets.
- Contains: Original Grilon3 images in `public/assets/grilon3/`, original Filamentos3D/3N3 images in `public/assets/filamentos3d/`, and generated WebP thumbnails in `public/assets/thumbs/`.
- Key files: Source images are referenced from metadata caches and `stock.json`; thumbnails are generated by `centraldefilamentos/thumbnails.py`.

**`tests/`:**
- Purpose: Pytest coverage for Python data pipeline, parsers, normalization, provider config, snapshots/history, and frontend asset invariants.
- Contains: Test modules and fixture files.
- Key files: `tests/test_build_data.py`, `tests/test_normalize.py`, `tests/test_providers.py`, `tests/test_google_sheet.py`, `tests/test_filamentos3d.py`, `tests/test_grilon3_catalog.py`, `tests/test_filamentos3d_catalog.py`, `tests/test_frontend_assets.py`.

**`tests/fixtures/`:**
- Purpose: Fixture data for parser and connector tests.
- Contains: `tests/fixtures/filamentos3d_stock.html`, `tests/fixtures/google_sheet_stock.csv`, `tests/fixtures/grilon3_catalog.html`.
- Key files: Add fixture files here when connector behavior needs stable sample input.

**`tools/image-curation/`:**
- Purpose: Local human-in-the-loop image curation app.
- Contains: Node HTTP server, static tool HTML/CSS/JS, candidate capture/review UI.
- Key files: `tools/image-curation/server.mjs`, `tools/image-curation/app.js`, `tools/image-curation/index.html`, `tools/image-curation/styles.css`.

**`docs/`:**
- Purpose: Project and operating documentation.
- Contains: Publishing workflow docs, image curation protocol, Superpowers planning/spec artifacts.
- Key files: `docs/publishing-workflows.md`, `docs/image-curation.md`, `docs/superpowers/specs/2026-05-12-centraldefilamentos-design.md`, `docs/superpowers/plans/2026-05-12-centraldefilamentos-mvp.md`.

**`.github/workflows/`:**
- Purpose: GitHub Actions automation.
- Contains: CI, stock capture, UI publish, and thumbnail publish workflows.
- Key files: `.github/workflows/ci.yml`, `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, `.github/workflows/thumbnails.yml`.

**`dist/`:**
- Purpose: Vite build output produced by `npm run build`.
- Contains: Static HTML/JS/CSS/assets ready for GitHub Pages.
- Key files: Generated output; do not add source code here.

## Key File Locations

**Entry Points:**
- `index.html`: Public catalog HTML entry loading `src/catalog.js`.
- `resumen.html`: Public compact summary HTML entry loading `src/summary.js`.
- `estadisticas.html`: Internal vendor stats HTML entry loading `src/vendor-stats.js`.
- `src/catalog.js`: Svelte mount script for `src/CatalogApp.svelte`.
- `src/summary.js`: Svelte mount script for `src/SummaryApp.svelte`.
- `src/vendor-stats.js`: Svelte mount script for `src/VendorStatsApp.svelte`.
- `centraldefilamentos/build_data.py`: Python module entry for stock data build.
- `centraldefilamentos/generate_thumbnails.py`: Python module entry for thumbnail generation.
- `tools/image-curation/server.mjs`: Node entry for local image curation tool.

**Configuration:**
- `package.json`: Node scripts and Svelte/Vite dependencies.
- `package-lock.json`: Locked Node dependency graph.
- `pyproject.toml`: Python package metadata, dependencies, setuptools package discovery, and pytest config.
- `vite.config.js`: Vite base path, Svelte plugin, output dir, and multi-page Rollup inputs.
- `svelte.config.js`: Svelte config.
- `.github/workflows/ci.yml`: Test/build workflow.
- `.github/workflows/data-capture.yml`: Stock capture and data publish workflow.
- `.github/workflows/pages.yml`: UI build and publish workflow.
- `.github/workflows/thumbnails.yml`: Thumbnail build and publish workflow.

**Core Logic:**
- `centraldefilamentos/build_data.py`: Build pipeline orchestration and public JSON contract.
- `centraldefilamentos/models.py`: Dataclass schema for raw items, normalized fields, offers, products, providers, statuses, and manufacturers.
- `centraldefilamentos/providers.py`: Provider and manufacturer registry.
- `centraldefilamentos/normalize.py`: Product normalization rules and product id/display-name builders.
- `centraldefilamentos/connectors/google_sheet.py`: Google Sheets CSV connector.
- `centraldefilamentos/connectors/filamentos3d.py`: Filamentos3D stock HTML connector.
- `centraldefilamentos/connectors/grilon3_catalog.py`: Grilon3 catalog and product detail metadata connector.
- `centraldefilamentos/connectors/filamentos3d_catalog.py`: Filamentos3D/3N3 catalog metadata connector.
- `centraldefilamentos/thumbnails.py`: Thumbnail URL mapping, generation, and stock payload thumbnail updates.
- `src/lib/shared.js`: Shared frontend domain helpers.
- `src/lib/stockSubscriptions.js`: Browser stock watch persistence.

**Frontend Pages:**
- `src/CatalogApp.svelte`: Main catalog UI.
- `src/SummaryApp.svelte`: Compact stock summary table.
- `src/VendorStatsApp.svelte`: Internal provider history and build health dashboard.
- `src/components/SiteHeader.svelte`: Header, navigation, and stock alert banner.
- `src/components/SiteFooter.svelte`: Footer/provider contact section.
- `src/components/QuickLines.svelte`: Popular line navigation.
- `src/styles/global.css`: Shared styling for all pages.

**Data and Assets:**
- `public/data/stock.json`: Public product/source/manufacturer payload consumed by catalog and summary.
- `public/data/provider_stock_history.json`: Public provider history consumed by vendor stats.
- `public/data/build_business_log.json`: Public business-readable build health log consumed by vendor stats.
- `public/data/build_technical_log.json`: Technical build health log.
- `public/data/feature_flags.json`: Static frontend feature flags.
- `centraldefilamentos/data/grilon3_metadata.json`: Grilon3 metadata cache.
- `centraldefilamentos/data/filamentos3d_metadata.json`: Filamentos3D/3N3 metadata cache.
- `centraldefilamentos/data/daily_provider_stock_snapshot.json`: Internal daily baseline snapshot.
- `centraldefilamentos/data/provider_stock_history.json`: Internal provider history source.
- `public/assets/grilon3/`: Local Grilon3 original images.
- `public/assets/filamentos3d/`: Local Filamentos3D/3N3 original images.
- `public/assets/thumbs/`: Generated WebP thumbnails.

**Testing:**
- `tests/test_build_data.py`: Build payload, quality gates, enrichment, metadata, and thumbnail integration tests.
- `tests/test_daily_snapshot.py`: Daily snapshot update behavior.
- `tests/test_provider_stock_history.py`: Provider history append/trim/export behavior.
- `tests/test_normalize.py`: Product normalization rules.
- `tests/test_models.py`: Dataclass serialization.
- `tests/test_providers.py`: Source and manufacturer registry invariants.
- `tests/test_google_sheet.py`: Google Sheets CSV parsing.
- `tests/test_filamentos3d.py`: Filamentos3D stock parsing.
- `tests/test_grilon3_catalog.py`: Grilon3 catalog/detail parsing.
- `tests/test_filamentos3d_catalog.py`: Filamentos3D/3N3 catalog parsing.
- `tests/test_frontend_assets.py`: Frontend/static asset invariants.

**Documentation:**
- `README.md`: Development, data, workflows, and project overview.
- `docs/publishing-workflows.md`: GitHub Pages and workflow responsibility boundaries.
- `docs/image-curation.md`: Manual image curation protocol and tool notes.

## Naming Conventions

**Files:**
- Python modules use snake_case: `centraldefilamentos/build_data.py`, `centraldefilamentos/cache_grilon3_metadata.py`, `centraldefilamentos/connectors/google_sheet.py`.
- Python tests use `test_*.py`: `tests/test_build_data.py`, `tests/test_normalize.py`.
- Svelte components use PascalCase: `src/CatalogApp.svelte`, `src/components/SiteHeader.svelte`.
- Frontend mount scripts use lower-case or kebab-case by page: `src/catalog.js`, `src/summary.js`, `src/vendor-stats.js`.
- Static HTML entries use root-level page names: `index.html`, `resumen.html`, `estadisticas.html`.
- Generated/public JSON uses snake_case: `public/data/provider_stock_history.json`, `public/data/build_business_log.json`.
- Product image files are slug plus short digest: `public/assets/grilon3/pla-negro-1-600x600-be7e9893.jpg`, `public/assets/filamentos3d/3n3-box-pla-175mm-negro-x1kg-3583212a.jpg`.

**Directories:**
- Python package directories use lowercase: `centraldefilamentos/`, `centraldefilamentos/connectors/`.
- Frontend subdirectories use conventional names: `src/components/`, `src/lib/`, `src/styles/`.
- Public asset provider directories match source/manufacturer ids: `public/assets/grilon3/`, `public/assets/filamentos3d/`.
- Generated thumbnail directories mirror provider asset directories under `public/assets/thumbs/`.
- Tool directories use kebab-case: `tools/image-curation/`.

## Where to Add New Code

**New Provider Source:**
- Primary code: add provider config to `centraldefilamentos/providers.py`.
- Connector implementation: add a module under `centraldefilamentos/connectors/`, or extend an existing connector if the format is shared.
- Dispatch: update `_fetch_source_items` in `centraldefilamentos/build_data.py`.
- Tests: add parser/provider tests under `tests/`, using fixtures in `tests/fixtures/` when parsing HTML/CSV.

**New Product Normalization Rule:**
- Primary code: update rule lists or detector functions in `centraldefilamentos/normalize.py`.
- Tests: add cases to `tests/test_normalize.py`.
- Regenerated data: run `python -m centraldefilamentos.build_data --output public/data/stock.json` after tests pass.

**New Public Product Field:**
- Primary code: update dataclasses in `centraldefilamentos/models.py`.
- Build mapping: update `centraldefilamentos/build_data.py` where `ProductGroup`, `Offer`, or `SourceStatus` instances are built.
- Frontend consumption: update relevant app in `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, or `src/VendorStatsApp.svelte`.
- Tests: update `tests/test_models.py` and `tests/test_build_data.py`.

**New Manufacturer or Catalog Metadata Source:**
- Primary code: add manufacturer config to `centraldefilamentos/providers.py` and create/extend connector in `centraldefilamentos/connectors/`.
- Enrichment: add merge logic in `centraldefilamentos/build_data.py`.
- Cache script: add script under `centraldefilamentos/` only if metadata must persist between stock captures.
- Tests: add connector and build enrichment tests under `tests/`.

**New Frontend Page:**
- HTML entry: add root HTML file similar to `index.html`, `resumen.html`, or `estadisticas.html`.
- Mount script: add `src/<page>.js`.
- Svelte app: add `src/<PageApp>.svelte`.
- Vite config: add Rollup input in `vite.config.js`.
- Publishing paths: add the HTML/mount/app paths to `.github/workflows/pages.yml` if not covered by `src/**`.

**New Shared Frontend Component:**
- Implementation: add Svelte component to `src/components/`.
- Shared logic: put non-UI helpers in `src/lib/shared.js` or a focused module under `src/lib/`.
- Styling: add shared classes to `src/styles/global.css`.

**New Frontend Utility:**
- Shared helpers: use `src/lib/shared.js` for broadly reused domain/display logic.
- Browser persistence: use `src/lib/stockSubscriptions.js` only for stock-watch localStorage behavior; create a focused module in `src/lib/` for unrelated persistent browser state.

**New Static Data File:**
- Public frontend data: add under `public/data/`.
- Build writer: write from `centraldefilamentos/build_data.py` or a focused Python module in `centraldefilamentos/`.
- Workflow publishing: update `.github/workflows/data-capture.yml` or `.github/workflows/thumbnails.yml` so the file reaches `gh-pages`.

**New Product Image Asset:**
- Original image: place under `public/assets/grilon3/` or `public/assets/filamentos3d/` according to source.
- Thumbnail: generate through `centraldefilamentos/thumbnails.py` or `python -m centraldefilamentos.generate_thumbnails --stock-json public/data/stock.json`.
- Metadata link: update the relevant cache in `centraldefilamentos/data/` or the build enrichment that emits `image_url`.

**Image Curation Enhancements:**
- Local server/API code: update `tools/image-curation/server.mjs`.
- Browser tool UI: update `tools/image-curation/app.js`, `tools/image-curation/index.html`, or `tools/image-curation/styles.css`.
- Operating rules: update `docs/image-curation.md`.

**Utilities:**
- Python shared helpers for build/domain logic: add to `centraldefilamentos/` when used by build pipeline modules.
- Python connector-only helpers: keep private in `centraldefilamentos/connectors/<source>.py` unless shared by multiple connectors.
- Frontend shared helpers: add named exports to `src/lib/shared.js` when used by multiple Svelte pages.

## Special Directories

**`.planning/codebase/`:**
- Purpose: GSD codebase mapping documents.
- Generated: Yes.
- Committed: Yes, when orchestrator includes planning artifacts.

**`.github/workflows/`:**
- Purpose: GitHub Actions workflow definitions.
- Generated: No.
- Committed: Yes.

**`centraldefilamentos/data/`:**
- Purpose: Versioned metadata caches plus generated snapshot/history state used by stock builds.
- Generated: Mixed. Metadata caches are maintained by scripts/manual review; snapshot/history files are generated by stock capture.
- Committed: Yes.

**`public/data/`:**
- Purpose: Static JSON API for frontend pages.
- Generated: Mostly yes. `public/data/feature_flags.json` is a hand-edited static config file.
- Committed: Yes.

**`public/assets/`:**
- Purpose: Static product images and generated thumbnails.
- Generated: Mixed. Original images are downloaded/curated assets; `public/assets/thumbs/` is generated.
- Committed: Yes.

**`dist/`:**
- Purpose: Vite build output for static site publishing.
- Generated: Yes.
- Committed: Present in workspace; treat as build output and avoid source edits here.

**`tests/fixtures/`:**
- Purpose: Stable parser inputs for tests.
- Generated: No.
- Committed: Yes.

**`tools/image-curation/`:**
- Purpose: Local-only review tool for image decisions.
- Generated: No.
- Committed: Yes.

**`.image-curation/`:**
- Purpose: Ignored local state for image curation selections and candidate cache.
- Generated: Yes.
- Committed: No.

**`.codex-remote-attachments/`:**
- Purpose: Local Codex attachment workspace.
- Generated: Yes.
- Committed: No.

**`.pytest_cache/`, `__pycache__/`:**
- Purpose: Python test/runtime caches.
- Generated: Yes.
- Committed: No.

---

*Structure analysis: 2026-06-18*
