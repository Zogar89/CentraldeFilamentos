<!-- refreshed: 2026-06-18 -->
# Architecture

**Analysis Date:** 2026-06-18

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                    Static Svelte Frontend                    │
├──────────────────┬──────────────────┬───────────────────────┤
│ Catalog view     │ Summary view     │ Vendor stats view     │
│ `src/CatalogApp.svelte` │ `src/SummaryApp.svelte` │ `src/VendorStatsApp.svelte` │
│ `index.html`     │ `resumen.html`   │ `estadisticas.html`   │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 Static JSON and Asset Boundary               │
│ `public/data/stock.json`, `public/data/provider_stock_history.json` │
│ `public/assets/`, `public/assets/thumbs/`                    │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  Python Data Build Pipeline                  │
│ `centraldefilamentos/build_data.py`                          │
├──────────────────┬──────────────────┬───────────────────────┤
│ Source configs   │ Connectors       │ Normalization/models  │
│ `centraldefilamentos/providers.py` │ `centraldefilamentos/connectors/` │ `centraldefilamentos/normalize.py` |
└──────────────────┴──────────────────┴───────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ Provider pages, Google Sheets, metadata caches, GitHub Pages │
│ `centraldefilamentos/data/`, `.github/workflows/*.yml`       │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Data build orchestrator | Collect source rows, normalize products, enrich metadata, gate bad builds, update snapshots/history, and write public JSON. | `centraldefilamentos/build_data.py` |
| Source registry | Define providers, zones, connector type, contact metadata, Google Sheet ids, and manufacturer metadata. | `centraldefilamentos/providers.py` |
| Public data schema | Define dataclasses serialized into public JSON: raw items, normalized fields, offers, product groups, provider stats, source status, and manufacturers. | `centraldefilamentos/models.py` |
| Normalization engine | Convert provider-specific product names into canonical material, variant, color, diameter, weight, brand, product id, and display name. | `centraldefilamentos/normalize.py` |
| Provider stock connectors | Fetch and parse provider inventory from Filamentos3D HTML and Google Sheets CSV. | `centraldefilamentos/connectors/filamentos3d.py`, `centraldefilamentos/connectors/google_sheet.py` |
| Catalog metadata connectors | Fetch manufacturer/provider catalog pages for official URLs, images, Pantone, SKU, EAN, and 3N3 provider images. | `centraldefilamentos/connectors/grilon3_catalog.py`, `centraldefilamentos/connectors/filamentos3d_catalog.py` |
| Thumbnail pipeline | Map local `assets/...` image URLs to `assets/thumbs/...` WebP thumbnails and update `stock.json`. | `centraldefilamentos/thumbnails.py`, `centraldefilamentos/generate_thumbnails.py` |
| Catalog frontend | Load `stock.json`, filter/group products, show product cards, images, provider offers, and local stock alerts. | `src/CatalogApp.svelte`, `src/catalog.js` |
| Summary frontend | Load `stock.json` and render compact provider-by-product totals. | `src/SummaryApp.svelte`, `src/summary.js` |
| Vendor stats frontend | Load feature flags, provider history, and build health logs for the internal vendor movement view. | `src/VendorStatsApp.svelte`, `src/vendor-stats.js` |
| Shared frontend utilities | Centralize data URL handling, formatting, line metadata, search, sort ranking, color swatches, and provider links. | `src/lib/shared.js` |
| Stock watch persistence | Persist watched product/provider pairs and stock signatures in browser `localStorage`. | `src/lib/stockSubscriptions.js` |
| Image curation tool | Serve a local human-in-the-loop image review UI without publishing or mutating production data automatically. | `tools/image-curation/server.mjs`, `tools/image-curation/app.js` |
| CI/CD workflows | Run tests/builds, capture stock data, publish UI, and publish thumbnails to `gh-pages`. | `.github/workflows/ci.yml`, `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, `.github/workflows/thumbnails.yml` |

## Pattern Overview

**Overall:** Static site with offline data generation and file-based deployment.

**Key Characteristics:**
- Use Python as the trusted data producer. `centraldefilamentos/build_data.py` owns the public JSON contract written to `public/data/stock.json`.
- Use Svelte as a read-only static client. `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, and `src/VendorStatsApp.svelte` fetch static JSON through `src/lib/shared.js`.
- Keep provider-specific parsing behind connector modules. Add source-specific HTML/CSV logic under `centraldefilamentos/connectors/` and dispatch through `centraldefilamentos/build_data.py`.
- Keep durable product identity in normalized fields. `centraldefilamentos/normalize.py` and `centraldefilamentos/models.py` define how different provider rows collapse into one product.
- Publish UI, data, and thumbnails through separate workflows. `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, and `.github/workflows/thumbnails.yml` each own one deployment surface.

## Layers

**Source Configuration Layer:**
- Purpose: Store provider and manufacturer facts used by scraping, public source status, contact UI, and tests.
- Location: `centraldefilamentos/providers.py`
- Contains: `SourceConfig`, `SOURCES`, and `MANUFACTURERS`.
- Depends on: `centraldefilamentos/models.py`.
- Used by: `centraldefilamentos/build_data.py`, `centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/filamentos3d.py`, tests in `tests/test_providers.py`.

**Connector Layer:**
- Purpose: Convert external provider formats into `RawStockItem` objects or catalog metadata objects.
- Location: `centraldefilamentos/connectors/`
- Contains: Stock fetchers (`fetch_filamentos3d_items`, `fetch_sheet_items`) and catalog metadata fetchers (`fetch_grilon3_catalog`, `fetch_filamentos3d_catalog`).
- Depends on: `centraldefilamentos/models.py`, `centraldefilamentos/providers.py`, `centraldefilamentos/normalize.py`, `requests`, `httpx`, and BeautifulSoup.
- Used by: Lazy dispatch in `centraldefilamentos/build_data.py` and cache scripts in `centraldefilamentos/cache_grilon3_metadata.py`, `centraldefilamentos/cache_filamentos3d_metadata.py`.

**Normalization Layer:**
- Purpose: Canonicalize raw names into stable product fields and ids.
- Location: `centraldefilamentos/normalize.py`
- Contains: `MATERIAL_RULES`, `VARIANT_RULES`, `COLOR_RULES`, `BRAND_RULES`, `normalize_record`, `build_product_id`, and `build_display_name`.
- Depends on: `centraldefilamentos/models.py`.
- Used by: `centraldefilamentos/build_data.py`, `centraldefilamentos/connectors/grilon3_catalog.py`, `centraldefilamentos/connectors/filamentos3d_catalog.py`, tests in `tests/test_normalize.py`.

**Build Orchestration Layer:**
- Purpose: Coordinate data collection, enrichment, grouping, quality checks, snapshot/history updates, and file writes.
- Location: `centraldefilamentos/build_data.py`
- Contains: `collect_raw_items`, `_fetch_source_items`, `build_payload`, `evaluate_build_quality`, `maybe_update_daily_provider_stock_snapshot`, `maybe_update_provider_stock_history`, `write_public_provider_stock_history`, and `main`.
- Depends on: `centraldefilamentos/models.py`, `centraldefilamentos/normalize.py`, `centraldefilamentos/providers.py`, `centraldefilamentos/thumbnails.py`.
- Used by: CLI command `python -m centraldefilamentos.build_data --output public/data/stock.json`, `.github/workflows/data-capture.yml`, and tests in `tests/test_build_data.py`.

**Metadata Cache and Asset Layer:**
- Purpose: Persist enriched metadata and local images between stock captures.
- Location: `centraldefilamentos/data/`, `public/assets/`, `public/assets/thumbs/`
- Contains: `centraldefilamentos/data/grilon3_metadata.json`, `centraldefilamentos/data/filamentos3d_metadata.json`, `centraldefilamentos/data/daily_provider_stock_snapshot.json`, `centraldefilamentos/data/provider_stock_history.json`, original images, and generated thumbnails.
- Depends on: Cache scripts and thumbnail utilities in `centraldefilamentos/cache_grilon3_metadata.py`, `centraldefilamentos/cache_filamentos3d_metadata.py`, `centraldefilamentos/thumbnails.py`.
- Used by: `centraldefilamentos/build_data.py`, `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, `src/VendorStatsApp.svelte`, `.github/workflows/thumbnails.yml`.

**Frontend App Layer:**
- Purpose: Render static data into public catalog, compact summary, and internal stats pages.
- Location: `src/`, root HTML entry files.
- Contains: Svelte app components, mount scripts, shared utilities, shared components, and global CSS.
- Depends on: Static JSON under `public/data/` and assets under `public/assets/`.
- Used by: Vite multi-page build in `vite.config.js` and publish workflow `.github/workflows/pages.yml`.

**Publishing Layer:**
- Purpose: Run CI, capture data, build UI, generate thumbnails, and publish to `gh-pages`.
- Location: `.github/workflows/`
- Contains: `.github/workflows/ci.yml`, `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, `.github/workflows/thumbnails.yml`.
- Depends on: Python package config in `pyproject.toml`, Node package config in `package.json`, Vite config in `vite.config.js`.
- Used by: GitHub Actions and GitHub Pages.

## Data Flow

### Primary Stock Capture Path

1. GitHub Actions or local CLI invokes `python -m centraldefilamentos.build_data --output public/data/stock.json` (`centraldefilamentos/build_data.py:866`, `.github/workflows/data-capture.yml:39`).
2. `main` calls `collect_raw_items`, which iterates `SOURCES` and records per-source errors without aborting the whole run (`centraldefilamentos/build_data.py:514`).
3. `_fetch_source_items` dispatches by `SourceConfig.connector` to `fetch_sheet_items` or `fetch_filamentos3d_items` (`centraldefilamentos/build_data.py:980`, `centraldefilamentos/connectors/google_sheet.py:23`, `centraldefilamentos/connectors/filamentos3d.py:16`).
4. Connectors parse CSV/HTML rows into `RawStockItem` records (`centraldefilamentos/connectors/google_sheet.py:35`, `centraldefilamentos/connectors/filamentos3d.py:26`, `centraldefilamentos/models.py:12`).
5. `build_filamentos3d_enrichments`, `fetch_grilon3_catalog_products`, and `build_grilon3_enrichments` merge provider/manufacturer metadata and caches into enrichment dictionaries (`centraldefilamentos/build_data.py:545`, `centraldefilamentos/build_data.py:577`, `centraldefilamentos/build_data.py:610`).
6. `build_payload` normalizes each item, groups offers by product id, adds eligible catalog-only Grilon3 products, sorts products/sources, and serializes dataclasses (`centraldefilamentos/build_data.py:55`, `centraldefilamentos/normalize.py:176`, `centraldefilamentos/models.py:52`).
7. `evaluate_build_quality` validates source errors, schema shape, empty catalog, product drop ratio, and provider stock drop ratio before publishing (`centraldefilamentos/build_data.py:156`).
8. If publishing is allowed, snapshots/history/logs are written and `write_payload` writes `public/data/stock.json` (`centraldefilamentos/build_data.py:403`, `centraldefilamentos/build_data.py:444`, `centraldefilamentos/build_data.py:494`, `centraldefilamentos/build_data.py:132`).
9. `.github/workflows/data-capture.yml` commits changed data files and copies `public/data/*.json` into `gh-pages/data/` (`.github/workflows/data-capture.yml:45`, `.github/workflows/data-capture.yml:80`).

### Frontend Catalog Path

1. `index.html` loads `src/catalog.js`, which mounts `src/CatalogApp.svelte` into `#app` (`index.html:8`, `src/catalog.js:5`).
2. `CatalogApp` calls `fetchJson("data/stock.json")` through `src/lib/shared.js` on mount (`src/CatalogApp.svelte:55`, `src/lib/shared.js:60`).
3. `src/lib/shared.js` builds static URLs using `import.meta.env.BASE_URL`, matching Vite base `/CentraldeFilamentos/` (`src/lib/shared.js:38`, `vite.config.js:6`).
4. Reactive statements derive filters, option lists, groups, and subscribed keys from loaded products (`src/CatalogApp.svelte:64`, `src/CatalogApp.svelte:66`).
5. Stock watch state is loaded and saved in browser `localStorage` through `src/lib/stockSubscriptions.js` (`src/CatalogApp.svelte:60`, `src/lib/stockSubscriptions.js:15`, `src/lib/stockSubscriptions.js:24`).

### Frontend Summary Path

1. `resumen.html` loads `src/summary.js`, which mounts `src/SummaryApp.svelte` (`resumen.html:8`, `src/summary.js:5`).
2. `SummaryApp` fetches `data/stock.json`, sorts providers by zone, builds row cells per provider, and groups products by brand/diameter/line (`src/SummaryApp.svelte:29`, `src/SummaryApp.svelte:43`, `src/SummaryApp.svelte:70`).
3. Shared line metadata and formatting come from `src/lib/shared.js` (`src/SummaryApp.svelte:4`, `src/lib/shared.js:4`).

### Vendor Stats Path

1. `estadisticas.html` loads `src/vendor-stats.js`, which mounts `src/VendorStatsApp.svelte` (`estadisticas.html:9`, `src/vendor-stats.js:5`).
2. `VendorStatsApp` fetches `data/feature_flags.json` with no-cache and exits early when `vendorStatsEnabled` is false (`src/VendorStatsApp.svelte:12`, `src/VendorStatsApp.svelte:13`).
3. When enabled, it fetches `data/provider_stock_history.json` and `data/build_business_log.json` for provider charts and build health (`src/VendorStatsApp.svelte:18`, `src/VendorStatsApp.svelte:19`).
4. Provider history is produced by `write_public_provider_stock_history` from internal history snapshots (`centraldefilamentos/build_data.py:494`).

### UI Publish Path

1. Vite defines three HTML inputs: `index.html`, `resumen.html`, and `estadisticas.html` (`vite.config.js:11`, `vite.config.js:13`, `vite.config.js:14`, `vite.config.js:15`).
2. `.github/workflows/pages.yml` installs Node dependencies and runs `npm run build` (`.github/workflows/pages.yml:49`).
3. The workflow copies `dist/` to the root of `gh-pages` without scraping providers or rewriting stock data (`.github/workflows/pages.yml:52`).

### Thumbnail Publish Path

1. `.github/workflows/thumbnails.yml` runs `python -m centraldefilamentos.generate_thumbnails --stock-json public/data/stock.json` (`.github/workflows/thumbnails.yml:43`).
2. `centraldefilamentos/generate_thumbnails.py` delegates to `centraldefilamentos/thumbnails.py` (`centraldefilamentos/generate_thumbnails.py`, `centraldefilamentos/thumbnails.py:110`).
3. `apply_thumbnails_to_stock` generates WebP thumbs for local assets and rewrites thumbnail URLs in `public/data/stock.json` (`centraldefilamentos/thumbnails.py:78`).
4. The workflow publishes `public/assets/` and `public/data/stock.json` to `gh-pages` (`.github/workflows/thumbnails.yml:79`).

**State Management:**
- Backend durable state lives in versioned JSON files under `centraldefilamentos/data/` and public JSON under `public/data/`.
- Frontend runtime state is component-local Svelte state in `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, and `src/VendorStatsApp.svelte`.
- Frontend persistent user state is limited to `localStorage` key `centraldefilamentos.stockSubscriptions.v1` in `src/lib/stockSubscriptions.js`.
- Image curation scratch state lives in ignored `.image-curation/*.json` via `tools/image-curation/server.mjs`.

## Key Abstractions

**SourceConfig:**
- Purpose: Declarative provider registry entry containing ids, URLs, connector type, sheet metadata, contact info, and brand hints.
- Examples: `centraldefilamentos/providers.py`
- Pattern: Frozen dataclass plus `SOURCES` map. Add providers by adding a `SourceConfig` and tests in `tests/test_providers.py`.

**ManufacturerInfo:**
- Purpose: Declarative manufacturer registry for official metadata sources.
- Examples: `centraldefilamentos/models.py`, `centraldefilamentos/providers.py`
- Pattern: Frozen dataclass plus `MANUFACTURERS` map.

**RawStockItem:**
- Purpose: Connector-neutral row emitted by stock sources before normalization.
- Examples: `centraldefilamentos/models.py`, `centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/filamentos3d.py`
- Pattern: Frozen dataclass; connectors return `list[RawStockItem]`.

**NormalizedFields:**
- Purpose: Canonical product identity fields derived from raw names and brand hints.
- Examples: `centraldefilamentos/models.py`, `centraldefilamentos/normalize.py`
- Pattern: Rules table plus detector functions, then `build_product_id` for durable ids.

**ProductGroup and Offer:**
- Purpose: Public catalog product plus provider offers serialized into `public/data/stock.json`.
- Examples: `centraldefilamentos/models.py`, `centraldefilamentos/build_data.py`
- Pattern: Frozen dataclasses with `to_dict` methods; `ProductGroup.offers` is sorted and de-duplicated before serialization.

**SourceStatus and ProviderStats:**
- Purpose: Public provider health/contact/stats payload used by frontend provider summaries and build health.
- Examples: `centraldefilamentos/models.py`, `centraldefilamentos/build_data.py`
- Pattern: Derived from raw items and source errors in `_source_status`.

**CatalogProduct and ProviderCatalogProduct:**
- Purpose: Metadata-only product records for manufacturer/provider catalog enrichment.
- Examples: `centraldefilamentos/connectors/grilon3_catalog.py`, `centraldefilamentos/connectors/filamentos3d_catalog.py`
- Pattern: Frozen dataclasses keyed by normalized product id.

**Shared Frontend Helpers:**
- Purpose: Keep URL building, line labels, ranks, formatting, color swatches, search, and sort helpers consistent across Svelte apps.
- Examples: `src/lib/shared.js`
- Pattern: Named ES module exports consumed directly by Svelte components.

**QuickLines Component:**
- Purpose: Shared navigation widget for popular material/line jumps.
- Examples: `src/components/QuickLines.svelte`, `src/CatalogApp.svelte`, `src/SummaryApp.svelte`
- Pattern: Component receives available line names and a target selector; it queries visible target nodes by `data-line`.

## Entry Points

**Public Catalog Page:**
- Location: `index.html`, `src/catalog.js`, `src/CatalogApp.svelte`
- Triggers: Browser navigation to `/CentraldeFilamentos/` or local Vite `index.html`.
- Responsibilities: Load stock data, filter/search, group product rows, show images and provider offers, manage local stock alerts.

**Public Summary Page:**
- Location: `resumen.html`, `src/summary.js`, `src/SummaryApp.svelte`
- Triggers: Browser navigation to `/resumen.html`.
- Responsibilities: Render compact provider stock totals and product presentation rows.

**Internal Vendor Stats Page:**
- Location: `estadisticas.html`, `src/vendor-stats.js`, `src/VendorStatsApp.svelte`
- Triggers: Browser navigation to `/estadisticas.html`; page is `noindex,nofollow`.
- Responsibilities: Show provider history, movement charts, and build health when feature flag allows it.

**Stock Data Build CLI:**
- Location: `centraldefilamentos/build_data.py`
- Triggers: `python -m centraldefilamentos.build_data --output public/data/stock.json`.
- Responsibilities: Produce `public/data/stock.json`, logs, snapshots, and public provider history.

**Thumbnail CLI:**
- Location: `centraldefilamentos/generate_thumbnails.py`, `centraldefilamentos/thumbnails.py`
- Triggers: `python -m centraldefilamentos.generate_thumbnails --stock-json public/data/stock.json`.
- Responsibilities: Generate thumbnails and update `thumbnail_url` fields for local product images.

**Metadata Cache CLIs:**
- Location: `centraldefilamentos/cache_grilon3_metadata.py`, `centraldefilamentos/cache_filamentos3d_metadata.py`
- Triggers: Manual Python module commands documented in `README.md`.
- Responsibilities: Refresh metadata caches and local image assets for Grilon3 and Filamentos3D/3N3.

**Image Update CLIs:**
- Location: `centraldefilamentos/update_grilon3_images.py`, `centraldefilamentos/update_filamentos3d_images.py`
- Triggers: Manual scripts for applying existing refreshed cache data.
- Responsibilities: Apply image metadata to caches and stock payloads when explicitly used.

**Image Curation Tool:**
- Location: `tools/image-curation/server.mjs`, `tools/image-curation/index.html`, `tools/image-curation/app.js`
- Triggers: `npm run curate-images`.
- Responsibilities: Serve local product image review and persist ignored review state in `.image-curation/`.

**CI Workflow:**
- Location: `.github/workflows/ci.yml`
- Triggers: Pushes except data/assets-only paths, and pull requests.
- Responsibilities: Install Python/Node dependencies, run pytest, and build frontend.

**Data Capture Workflow:**
- Location: `.github/workflows/data-capture.yml`
- Triggers: Manual dispatch and weekday cron.
- Responsibilities: Run stock build, commit generated data, and publish data files to `gh-pages`.

**UI Publish Workflow:**
- Location: `.github/workflows/pages.yml`
- Triggers: Manual dispatch and pushes affecting UI/config files.
- Responsibilities: Build frontend and publish `dist/` to `gh-pages`.

**Thumbnail Publish Workflow:**
- Location: `.github/workflows/thumbnails.yml`
- Triggers: Manual dispatch and source asset changes.
- Responsibilities: Generate thumbnails, commit generated thumbnails, and publish assets plus `stock.json`.

## Architectural Constraints

- **Threading:** The main stock build path is synchronous Python. Grilon3 detail enrichment uses `ThreadPoolExecutor` in `centraldefilamentos/connectors/grilon3_catalog.py`; use it only for independent network detail fetches.
- **Frontend runtime:** The Svelte frontend runs entirely in the browser and reads static files; do not add server-only assumptions to `src/*.svelte` or `src/lib/*.js`.
- **Global state:** Provider/manufacturer config lives in module-level maps in `centraldefilamentos/providers.py`; normalization rules live in module-level lists in `centraldefilamentos/normalize.py`; frontend line metadata lives in `src/lib/shared.js`.
- **Circular imports:** Keep connector imports lazy inside `centraldefilamentos/build_data.py` for enrichment and source dispatch. `centraldefilamentos/cache_grilon3_metadata.py` imports constants from `centraldefilamentos/build_data.py`, so moving connector imports to build-data module top level risks import cycles.
- **Generated data:** Treat `public/data/stock.json`, `public/data/provider_stock_history.json`, `public/data/build_business_log.json`, `public/data/build_technical_log.json`, `centraldefilamentos/data/daily_provider_stock_snapshot.json`, and `centraldefilamentos/data/provider_stock_history.json` as generated build outputs.
- **Static URL base:** Use `src/lib/shared.js:dataUrl` for frontend JSON/asset URLs so `/CentraldeFilamentos/` from `vite.config.js` is respected.
- **Deployment separation:** Data capture, UI publish, and thumbnail publish are independent workflows. Do not combine scraping, Vite builds, and thumbnail generation into one routine.
- **Feature flags:** The vendor stats page is controlled by `public/data/feature_flags.json`; preserve the no-cache fetch in `src/VendorStatsApp.svelte`.

## Anti-Patterns

### Editing Generated Stock JSON Directly

**What happens:** Product, offer, image, or provider changes are made directly in `public/data/stock.json`.
**Why it's wrong:** The next `centraldefilamentos/build_data.py` run rewrites `public/data/stock.json`, and durable fixes disappear.
**Do this instead:** Change normalization in `centraldefilamentos/normalize.py`, source config in `centraldefilamentos/providers.py`, connector parsing in `centraldefilamentos/connectors/`, metadata caches in `centraldefilamentos/data/*.json`, or image tooling in `centraldefilamentos/thumbnails.py`, then regenerate data.

### Bypassing SourceConfig Connector Dispatch

**What happens:** A new provider is hardcoded directly inside `centraldefilamentos/build_data.py` without a `SourceConfig` entry or connector module.
**Why it's wrong:** Provider contact/status metadata, tests, source sorting, and `_fetch_source_items` dispatch depend on `centraldefilamentos/providers.py`.
**Do this instead:** Add the provider to `SOURCES` in `centraldefilamentos/providers.py`, implement parsing in `centraldefilamentos/connectors/`, and extend `_fetch_source_items` in `centraldefilamentos/build_data.py`.

### Duplicating Frontend Line/Search Logic

**What happens:** A Svelte app redefines line rank, line label, zone order, formatting, or search behavior locally.
**Why it's wrong:** Catalog, summary, quick-line navigation, and internal stats become inconsistent.
**Do this instead:** Add shared helpers or metadata to `src/lib/shared.js` and import them from `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, or `src/VendorStatsApp.svelte`.

### Running Bulk Image Refresh for One Product

**What happens:** A point image fix uses full-cache scripts such as `centraldefilamentos/cache_grilon3_metadata.py`, `centraldefilamentos/cache_filamentos3d_metadata.py`, `centraldefilamentos/update_grilon3_images.py`, or `centraldefilamentos/update_filamentos3d_images.py`.
**Why it's wrong:** Bulk refreshes can rewrite many cache/image fields for unrelated products and make review unsafe.
**Do this instead:** Follow `docs/image-curation.md`, use `tools/image-curation/` to inspect candidates, patch only the chosen product/cache fields, and regenerate only the needed thumbnail through `centraldefilamentos/thumbnails.py`.

### Fetching Static JSON Without dataUrl

**What happens:** Frontend code fetches `/data/stock.json` or hardcoded GitHub Pages URLs directly.
**Why it's wrong:** Local Vite dev and GitHub Pages base path `/CentraldeFilamentos/` differ.
**Do this instead:** Use `fetchJson("data/stock.json")` from `src/lib/shared.js`, which uses `dataUrl` and `import.meta.env.BASE_URL`.

## Error Handling

**Strategy:** Backend errors are captured into build quality reports and publishing gates; frontend fetch errors fall back to empty/default payloads.

**Patterns:**
- Connector collection retries each source and records source-specific failures in `source_errors` (`centraldefilamentos/build_data.py:514`, `centraldefilamentos/build_data.py:532`).
- Build quality blocks publishing on source errors, schema errors, empty catalogs, suspicious total product drops, and suspicious provider stock drops (`centraldefilamentos/build_data.py:156`).
- Enrichment errors are warnings that allow stock publication with available data (`centraldefilamentos/build_data.py:545`, `centraldefilamentos/build_data.py:577`, `centraldefilamentos/build_data.py:610`).
- Frontend `fetchJson` catches network/parse errors and returns caller-provided fallbacks (`src/lib/shared.js:60`).
- Parser modules use defensive parsing for unknown stock values and non-product rows (`centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/filamentos3d.py`).

## Cross-Cutting Concerns

**Logging:** Build health logs are file-based JSON outputs in `public/data/build_business_log.json` and `public/data/build_technical_log.json`, written by `write_build_logs` in `centraldefilamentos/build_data.py`.

**Validation:** Data validation lives in `evaluate_build_quality` and `_stock_payload_schema_errors` in `centraldefilamentos/build_data.py`; unit tests in `tests/test_build_data.py`, `tests/test_models.py`, and connector tests assert core behavior.

**Authentication:** No application authentication layer is present. The internal vendor stats page is an unlinked/noindex static page gated by `public/data/feature_flags.json`, not by identity.

**Localization:** User-facing UI text is Spanish/Argentina. Dates and numbers use `es-AR` formatting in `src/lib/shared.js`.

**Assets:** Original product images live under `public/assets/grilon3/` and `public/assets/filamentos3d/`; generated thumbnails live under `public/assets/thumbs/`.

**Testing:** Python tests cover build, parsing, models, normalization, provider config, asset/frontend invariants, snapshots, and history under `tests/`.

---

*Architecture analysis: 2026-06-18*
