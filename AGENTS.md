<!-- GSD:project-start source:PROJECT.md -->

## Project

**Central de Filamentos**

Central de Filamentos es un sitio estatico para makers e usuarios de impresion 3D en Argentina que necesitan encontrar rapido que proveedor tiene el filamento que buscan. El producto centraliza stock online de proveedores, normaliza material, color, marca, diametro, formato y codigos cuando estan disponibles, y ayuda a comparar disponibilidad sin convertir la plataforma en una tienda.

El proximo foco del proyecto es una **lista de compra/cotizacion**: una herramienta local del navegador para que el maker arme un listado de filamentos, vea que proveedores cubren cada item y genere mensajes de WhatsApp individuales para consultar cotizacion y disponibilidad.

**Core Value:** Ayudar al maker a convertir la informacion dispersa de stock de filamento en una consulta clara y accionable para comprar mejor, sin que StockCentral venda ni procese pedidos.

### Constraints

- **Hosting**: sitio estatico en GitHub Pages - no asumir endpoints server-side ni sesiones.
- **Persistencia**: solo `localStorage` o cookies - datos locales, no sincronizados entre dispositivos.
- **Producto**: StockCentral no vende ni procesa pedidos - el copy y los iconos deben reforzar herramienta de planificacion/cotizacion.
- **Datos**: `public/data/stock.json` es generado - cambios durables de producto/ofertas vienen de normalizacion, fuentes, caches o build pipeline.
- **Proveedor**: disponibilidad y precio deben confirmarse con cada proveedor - los mensajes deben pedir cotizacion/disponibilidad, no prometer stock final.
- **UX**: mobile primero, pero con oportunidad de mostrar la lista a la derecha en desktop si el ancho lo permite.
- **Testing local Windows**: usar `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos` o un temp escribible.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python 3.12 - Data ingestion, normalization, metadata enrichment, JSON generation, thumbnail generation, and tests in `centraldefilamentos/`, `tests/`, `pyproject.toml`, and `.github/workflows/*.yml`.
- JavaScript ES modules - Svelte/Vite app entry points and local image-curation server in `src/catalog.js`, `src/summary.js`, `src/vendor-stats.js`, `src/lib/shared.js`, and `tools/image-curation/server.mjs`.
- Svelte 5.55.7 - Frontend UI components in `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, `src/VendorStatsApp.svelte`, and `src/components/*.svelte`.
- CSS - Shared frontend styling in `src/styles/global.css` and local image-curation styling in `tools/image-curation/styles.css`.
- HTML - Vite multi-page entry files in `index.html`, `resumen.html`, and `estadisticas.html`; local image-curation UI in `tools/image-curation/index.html`.
- YAML - GitHub Actions workflows in `.github/workflows/ci.yml`, `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, and `.github/workflows/thumbnails.yml`.
- JSON - Generated/static data and metadata caches in `public/data/*.json`, `centraldefilamentos/data/*.json`, `public/assets/**`, and `package-lock.json`.

## Runtime

- Python >=3.12 - Declared in `pyproject.toml`; GitHub Actions pins `python-version: "3.12"` in `.github/workflows/ci.yml`, `.github/workflows/data-capture.yml`, and `.github/workflows/thumbnails.yml`.
- Node.js 24 - GitHub Actions pins `node-version: "24"` in `.github/workflows/ci.yml` and `.github/workflows/pages.yml`.
- Browser runtime - The built static site runs as plain HTML/CSS/JS from GitHub Pages and reads static JSON with `fetch` in `src/lib/shared.js`.
- npm - Scripts and frontend dev dependencies live in `package.json`; CI and Pages use `npm ci` in `.github/workflows/ci.yml` and `.github/workflows/pages.yml`.
- pip/setuptools - Python packaging uses `setuptools.build_meta` in `pyproject.toml`; workflows install with `python -m pip install -e .` or `python -m pip install -e ".[dev]"`.
- Lockfile: present for frontend dependencies at `package-lock.json` with lockfileVersion 3. No Python lockfile is present.

## Frameworks

- Svelte 5.55.7 - Component framework for catalog, summary, vendor stats, header/footer, and quick-line filters in `src/*.svelte` and `src/components/*.svelte`.
- Vite 8.0.13 - Frontend dev server/build tool configured in `vite.config.js`; outputs to `dist/` and builds three HTML entry points.
- @sveltejs/vite-plugin-svelte 7.1.2 - Vite/Svelte integration configured in `vite.config.js`.
- Python package `centraldefilamentos` - Data pipeline package declared in `pyproject.toml` and implemented under `centraldefilamentos/`.
- pytest >=8.2.0 - Python test runner declared in `pyproject.toml`; tests live in `tests/` and CI runs `python -m pytest -v` in `.github/workflows/ci.yml`.
- Frontend asset checks - Python tests inspect frontend source/build assumptions in `tests/test_frontend_assets.py`; there is no dedicated JS test runner configured in `package.json`.
- Vite - `npm run dev`, `npm run build`, and `npm run preview` are defined in `package.json`.
- setuptools >=69 - Python build backend configured in `pyproject.toml`.
- GitHub Actions - CI, data capture, UI publish, and thumbnail publish workflows live in `.github/workflows/`.
- Node built-in HTTP server - Local image-curation tool uses `node:http`, `node:fs`, and `fetch` in `tools/image-curation/server.mjs`.

## Key Dependencies

- `svelte` 5.55.7 - Required for all frontend pages mounted from `src/catalog.js`, `src/summary.js`, and `src/vendor-stats.js`.
- `vite` 8.0.13 - Required for local frontend development and production build configured in `vite.config.js`.
- `@sveltejs/vite-plugin-svelte` 7.1.2 - Required to compile Svelte components through Vite in `vite.config.js`.
- `requests>=2.32.3` - Used for Google Sheet CSV export, Grilon3 catalog/product fetches, and image downloads in `centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/grilon3_catalog.py`, and `centraldefilamentos/cache_grilon3_metadata.py`.
- `httpx>=0.27.0` - Used for Filamentos3D stock/catalog fetches and image downloads in `centraldefilamentos/connectors/filamentos3d.py`, `centraldefilamentos/connectors/filamentos3d_catalog.py`, and `centraldefilamentos/cache_filamentos3d_metadata.py`.
- `beautifulsoup4>=4.12.3` - Used to parse Filamentos3D HTML pages in `centraldefilamentos/connectors/filamentos3d.py` and `centraldefilamentos/connectors/filamentos3d_catalog.py`.
- `lxml>=5.2.0` - Preferred BeautifulSoup parser for Filamentos3D HTML parsing in `centraldefilamentos/connectors/filamentos3d.py` and `centraldefilamentos/connectors/filamentos3d_catalog.py`.
- `Pillow>=10.4.0` - Used for thumbnail generation in `centraldefilamentos/thumbnails.py`.
- GitHub Actions `actions/checkout@v6` - Source checkout in all workflows under `.github/workflows/`.
- GitHub Actions `actions/setup-python@v6` - Python 3.12 setup in `.github/workflows/ci.yml`, `.github/workflows/data-capture.yml`, and `.github/workflows/thumbnails.yml`.
- GitHub Actions `actions/setup-node@v6` - Node 24 setup with npm cache in `.github/workflows/ci.yml` and `.github/workflows/pages.yml`.
- Git CLI - Workflows clone, commit, and push generated artifacts to `master` and `gh-pages` in `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, and `.github/workflows/thumbnails.yml`.

## Configuration

- Vite base path is `/CentraldeFilamentos/` in `vite.config.js`; frontend data URLs are built with `import.meta.env.BASE_URL` in `src/lib/shared.js`.
- Local image-curation server reads optional `PORT` and `HOST` environment variables, defaulting to `4177` and `127.0.0.1`, in `tools/image-curation/server.mjs`.
- GitHub Actions uses the built-in `${{ github.token }}` as `GH_TOKEN` for publishing to `gh-pages` in `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, and `.github/workflows/thumbnails.yml`.
- No `.env` files are present at repo root. No application secrets are read by the Python data pipeline or frontend.
- `vite.config.js` configures Svelte, `base`, `dist/` output, and multi-page Rollup inputs: `index.html`, `resumen.html`, and `estadisticas.html`.
- `svelte.config.js` currently exports an empty Svelte config.
- `pyproject.toml` configures Python package metadata, dependencies, optional `dev` dependencies, setuptools package discovery, and pytest paths.
- `package.json` defines `dev`, `build`, `preview`, and `curate-images` scripts.
- `.gitignore` excludes generated/local directories: `.superpowers/`, `__pycache__/`, `.pytest_cache/`, `node_modules/`, `dist/`, and `.image-curation/`.

## Platform Requirements

- Install Python dependencies with `python -m pip install -e ".[dev]"` from `README.md`.
- Install frontend dependencies with `npm ci` from `README.md`.
- Run tests with `python -m pytest -v` on Linux/GitHub Actions or `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos` on Windows as documented in `README.md`.
- Generate data with `python -m centraldefilamentos.build_data --output public/data/stock.json` from `README.md`.
- Run local frontend with `npm run dev` and local image-curation UI with `npm run curate-images` from `package.json`.
- Deployment target is GitHub Pages at `https://zogar89.github.io/CentraldeFilamentos/`, documented in `README.md` and `docs/publishing-workflows.md`.
- GitHub Pages uses legacy publishing from branch `gh-pages`, path `/`, documented in `README.md` and `docs/publishing-workflows.md`.
- UI publication copies `dist/` to the root of `gh-pages` in `.github/workflows/pages.yml`.
- Data publication copies `public/data/*.json` to `gh-pages/data/` in `.github/workflows/data-capture.yml`.
- Asset publication copies `public/assets/` and `public/data/stock.json` to `gh-pages` in `.github/workflows/thumbnails.yml`.

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- Use lowercase Python module names with underscores under `centraldefilamentos/`, such as `centraldefilamentos/build_data.py`, `centraldefilamentos/cache_grilon3_metadata.py`, and `centraldefilamentos/connectors/google_sheet.py`.
- Use Svelte component names in PascalCase under `src/`, such as `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, `src/components/SiteHeader.svelte`, and `src/components/QuickLines.svelte`.
- Use lowercase JavaScript entry and utility files under `src/`, such as `src/catalog.js`, `src/summary.js`, `src/vendor-stats.js`, `src/lib/shared.js`, and `src/lib/stockSubscriptions.js`.
- Use pytest file names in `tests/test_*.py`, such as `tests/test_build_data.py`, `tests/test_normalize.py`, and `tests/test_frontend_assets.py`.
- Use `snake_case` for Python functions and private helpers in `centraldefilamentos/build_data.py`, `centraldefilamentos/normalize.py`, and `centraldefilamentos/connectors/filamentos3d.py`.
- Prefix internal Python helpers with `_`, such as `_write_json`, `_detect_material`, `_parse_stock`, `_normalize_header`, and `_soup` in `centraldefilamentos/build_data.py`, `centraldefilamentos/normalize.py`, and `centraldefilamentos/connectors/google_sheet.py`.
- Use descriptive action-oriented public Python names, such as `build_payload`, `write_payload`, `load_payload`, `evaluate_build_quality`, `fetch_sheet_items`, and `parse_sheet_csv` in `centraldefilamentos/build_data.py` and `centraldefilamentos/connectors/google_sheet.py`.
- Use `camelCase` for JavaScript and Svelte functions, such as `matchesFilters`, `setFilter`, `groupProducts`, `fetchJson`, `formatDate`, and `colorSwatchStyle` in `src/CatalogApp.svelte` and `src/lib/shared.js`.
- Use `snake_case` for Python locals and parameters, such as `raw_items`, `source_errors`, `generated_at`, `timeout_seconds`, and `stock_quantity` in `centraldefilamentos/build_data.py` and `centraldefilamentos/connectors/google_sheet.py`.
- Use `UPPER_SNAKE_CASE` for Python module constants, such as `GRILON3_METADATA_CACHE`, `DEFAULT_ENRICHMENT`, `MATERIAL_RULES`, `COLOR_RULES`, and `SOURCES` in `centraldefilamentos/build_data.py`, `centraldefilamentos/normalize.py`, and `centraldefilamentos/providers.py`.
- Use `camelCase` for JavaScript and Svelte locals, props, and reactive values, such as `generatedAt`, `categoryOrder`, `lineOptions`, `availableLines`, and `stockSubscriptions` in `src/CatalogApp.svelte`.
- Use short domain names only when the surrounding context is clear, such as `item`, `source`, `fields`, `payload`, and `product` in `centraldefilamentos/build_data.py`, `centraldefilamentos/normalize.py`, and `src/CatalogApp.svelte`.
- Use frozen Python dataclasses for public data models in `centraldefilamentos/models.py`; add new payload entities as `@dataclass(frozen=True)` with explicit type annotations and a `to_dict()` method when serialized.
- Use `typing.Literal` aliases for constrained strings in `centraldefilamentos/models.py`, such as `StockStatus`, `SourceRunStatus`, and `ImageSource`.
- Use modern Python built-in generics and unions, such as `dict[str, object]`, `list[RawStockItem]`, and `int | None` in `centraldefilamentos/models.py` and `centraldefilamentos/build_data.py`.
- JavaScript files under `src/` are plain JavaScript, not TypeScript; do not introduce TypeScript-only syntax in `src/lib/shared.js`, `src/catalog.js`, or `src/CatalogApp.svelte`.

## Code Style

- Python formatting is conventional 4-space indentation with blank lines between top-level functions, shown in `centraldefilamentos/models.py`, `centraldefilamentos/normalize.py`, and `centraldefilamentos/connectors/google_sheet.py`.
- JavaScript and Svelte formatting uses 2-space indentation, double quotes, semicolons, and object literals split across lines when helpful in `src/CatalogApp.svelte`, `src/lib/shared.js`, and `vite.config.js`.
- JSON output written by backend code uses `json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True) + "\n"` via `_write_json()` in `centraldefilamentos/build_data.py`.
- No Prettier, Black, Ruff, ESLint, Biome, or formatting config is detected in `.prettierrc*`, `.eslintrc*`, `eslint.config.*`, `biome.json`, or `pyproject.toml`.
- No lint command is configured in `package.json`, `pyproject.toml`, or `.github/workflows/ci.yml`.
- CI quality gates are `python -m pytest -v` and `npm run build` in `.github/workflows/ci.yml`; keep new code compatible with those commands.
- Add any future linting config explicitly before relying on formatter-specific behavior; current source files such as `centraldefilamentos/build_data.py` and `src/CatalogApp.svelte` are the style source of truth.

## Import Organization

- No JavaScript path aliases are detected; use relative imports such as `./components/SiteHeader.svelte`, `./lib/shared.js`, and `../lib/shared.js` in `src/CatalogApp.svelte` and `src/components/SiteHeader.svelte`.
- Python tests and modules use package imports from `centraldefilamentos.*`; `pyproject.toml` sets `pythonpath = ["."]` for pytest.

## Error Handling

- Network fetchers call `raise_for_status()` immediately after `requests.get()` or `httpx.get()`, then delegate parsing to pure functions in `centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/filamentos3d.py`, and `centraldefilamentos/connectors/grilon3_catalog.py`.
- Parser helpers return defensive defaults for malformed optional values, such as `None`, `""`, or `[]`, in `_parse_stock()` and `_cell()` in `centraldefilamentos/connectors/google_sheet.py` and `centraldefilamentos/connectors/filamentos3d.py`.
- Expected data-contract violations raise `ValueError` with actionable messages, such as missing product columns in `centraldefilamentos/connectors/google_sheet.py` and repeated provider offers in `centraldefilamentos/build_data.py`.
- Build orchestration keeps partial source failures isolated: `collect_raw_items()` in `centraldefilamentos/build_data.py` returns successful items plus an `errors` mapping instead of aborting all providers.
- Frontend fetch failures return caller-provided fallback data in `fetchJson()` in `src/lib/shared.js`; use this pattern for optional static JSON reads.

## Logging

- Backend build status is modeled as public JSON logs, not Python logging calls; use `write_build_logs()` and quality event payloads in `centraldefilamentos/build_data.py`.
- Business-facing and technical events are split into `public/data/build_business_log.json` and `public/data/build_technical_log.json` by `write_build_logs()` in `centraldefilamentos/build_data.py`.
- The local image curation tool uses `console.log()` for startup messages in `tools/image-curation/server.mjs`; keep console logging localized to tooling.
- Frontend application files under `src/` do not use `console.log`; keep user-facing errors represented in UI state or JSON data rather than browser console output.

## Comments

- Use comments sparingly. Existing implementation modules such as `centraldefilamentos/normalize.py`, `centraldefilamentos/connectors/google_sheet.py`, and `src/lib/shared.js` rely on descriptive names and constants rather than explanatory comments.
- Keep schedule/process comments in configuration files when they clarify external behavior, such as the Argentina business-hour cron note in `.github/workflows/data-capture.yml`.
- Avoid comments that restate code; prefer named helpers like `_repair_mojibake()`, `matchesSearchTerms()`, `thumbnail_url_for()`, and `maybe_update_provider_stock_history()`.
- No JSDoc or TSDoc convention is detected in `src/lib/shared.js`, `src/CatalogApp.svelte`, or `src/components/SiteHeader.svelte`.
- No Python docstring convention is detected in `centraldefilamentos/build_data.py`, `centraldefilamentos/normalize.py`, or `centraldefilamentos/connectors/google_sheet.py`; add focused docstrings only for non-obvious public contracts.

## Function Design

## Module Design

- Python modules export public functions directly from their module files; use imports like `from centraldefilamentos.build_data import build_payload` in tests such as `tests/test_build_data.py`.
- JavaScript utility exports are named exports from `src/lib/shared.js` and `src/lib/stockSubscriptions.js`; import only the helpers a component uses in `src/CatalogApp.svelte` and `src/SummaryApp.svelte`.
- Svelte entry files `src/catalog.js`, `src/summary.js`, and `src/vendor-stats.js` should remain thin mount wrappers around their corresponding app components.
- No Python or JavaScript barrel file pattern is used. `centraldefilamentos/connectors/__init__.py` is present but direct module imports are used throughout tests such as `tests/test_google_sheet.py` and `tests/test_filamentos3d.py`.
- Add new shared frontend helpers to `src/lib/shared.js` only when they are used by multiple views; otherwise keep view-local logic in `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, or `src/VendorStatsApp.svelte`.

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

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

- Use Python as the trusted data producer. `centraldefilamentos/build_data.py` owns the public JSON contract written to `public/data/stock.json`.
- Use Svelte as a read-only static client. `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, and `src/VendorStatsApp.svelte` fetch static JSON through `src/lib/shared.js`.
- Keep provider-specific parsing behind connector modules. Add source-specific HTML/CSV logic under `centraldefilamentos/connectors/` and dispatch through `centraldefilamentos/build_data.py`.
- Keep durable product identity in normalized fields. `centraldefilamentos/normalize.py` and `centraldefilamentos/models.py` define how different provider rows collapse into one product.
- Publish UI, data, and thumbnails through separate workflows. `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, and `.github/workflows/thumbnails.yml` each own one deployment surface.

## Layers

- Purpose: Store provider and manufacturer facts used by scraping, public source status, contact UI, and tests.
- Location: `centraldefilamentos/providers.py`
- Contains: `SourceConfig`, `SOURCES`, and `MANUFACTURERS`.
- Depends on: `centraldefilamentos/models.py`.
- Used by: `centraldefilamentos/build_data.py`, `centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/filamentos3d.py`, tests in `tests/test_providers.py`.
- Purpose: Convert external provider formats into `RawStockItem` objects or catalog metadata objects.
- Location: `centraldefilamentos/connectors/`
- Contains: Stock fetchers (`fetch_filamentos3d_items`, `fetch_sheet_items`) and catalog metadata fetchers (`fetch_grilon3_catalog`, `fetch_filamentos3d_catalog`).
- Depends on: `centraldefilamentos/models.py`, `centraldefilamentos/providers.py`, `centraldefilamentos/normalize.py`, `requests`, `httpx`, and BeautifulSoup.
- Used by: Lazy dispatch in `centraldefilamentos/build_data.py` and cache scripts in `centraldefilamentos/cache_grilon3_metadata.py`, `centraldefilamentos/cache_filamentos3d_metadata.py`.
- Purpose: Canonicalize raw names into stable product fields and ids.
- Location: `centraldefilamentos/normalize.py`
- Contains: `MATERIAL_RULES`, `VARIANT_RULES`, `COLOR_RULES`, `BRAND_RULES`, `normalize_record`, `build_product_id`, and `build_display_name`.
- Depends on: `centraldefilamentos/models.py`.
- Used by: `centraldefilamentos/build_data.py`, `centraldefilamentos/connectors/grilon3_catalog.py`, `centraldefilamentos/connectors/filamentos3d_catalog.py`, tests in `tests/test_normalize.py`.
- Purpose: Coordinate data collection, enrichment, grouping, quality checks, snapshot/history updates, and file writes.
- Location: `centraldefilamentos/build_data.py`
- Contains: `collect_raw_items`, `_fetch_source_items`, `build_payload`, `evaluate_build_quality`, `maybe_update_daily_provider_stock_snapshot`, `maybe_update_provider_stock_history`, `write_public_provider_stock_history`, and `main`.
- Depends on: `centraldefilamentos/models.py`, `centraldefilamentos/normalize.py`, `centraldefilamentos/providers.py`, `centraldefilamentos/thumbnails.py`.
- Used by: CLI command `python -m centraldefilamentos.build_data --output public/data/stock.json`, `.github/workflows/data-capture.yml`, and tests in `tests/test_build_data.py`.
- Purpose: Persist enriched metadata and local images between stock captures.
- Location: `centraldefilamentos/data/`, `public/assets/`, `public/assets/thumbs/`
- Contains: `centraldefilamentos/data/grilon3_metadata.json`, `centraldefilamentos/data/filamentos3d_metadata.json`, `centraldefilamentos/data/daily_provider_stock_snapshot.json`, `centraldefilamentos/data/provider_stock_history.json`, original images, and generated thumbnails.
- Depends on: Cache scripts and thumbnail utilities in `centraldefilamentos/cache_grilon3_metadata.py`, `centraldefilamentos/cache_filamentos3d_metadata.py`, `centraldefilamentos/thumbnails.py`.
- Used by: `centraldefilamentos/build_data.py`, `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, `src/VendorStatsApp.svelte`, `.github/workflows/thumbnails.yml`.
- Purpose: Render static data into public catalog, compact summary, and internal stats pages.
- Location: `src/`, root HTML entry files.
- Contains: Svelte app components, mount scripts, shared utilities, shared components, and global CSS.
- Depends on: Static JSON under `public/data/` and assets under `public/assets/`.
- Used by: Vite multi-page build in `vite.config.js` and publish workflow `.github/workflows/pages.yml`.
- Purpose: Run CI, capture data, build UI, generate thumbnails, and publish to `gh-pages`.
- Location: `.github/workflows/`
- Contains: `.github/workflows/ci.yml`, `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, `.github/workflows/thumbnails.yml`.
- Depends on: Python package config in `pyproject.toml`, Node package config in `package.json`, Vite config in `vite.config.js`.
- Used by: GitHub Actions and GitHub Pages.

## Data Flow

### Primary Stock Capture Path

### Frontend Catalog Path

### Frontend Summary Path

### Vendor Stats Path

### UI Publish Path

### Thumbnail Publish Path

- Backend durable state lives in versioned JSON files under `centraldefilamentos/data/` and public JSON under `public/data/`.
- Frontend runtime state is component-local Svelte state in `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, and `src/VendorStatsApp.svelte`.
- Frontend persistent user state is limited to `localStorage` key `centraldefilamentos.stockSubscriptions.v1` in `src/lib/stockSubscriptions.js`.
- Image curation scratch state lives in ignored `.image-curation/*.json` via `tools/image-curation/server.mjs`.

## Key Abstractions

- Purpose: Declarative provider registry entry containing ids, URLs, connector type, sheet metadata, contact info, and brand hints.
- Examples: `centraldefilamentos/providers.py`
- Pattern: Frozen dataclass plus `SOURCES` map. Add providers by adding a `SourceConfig` and tests in `tests/test_providers.py`.
- Purpose: Declarative manufacturer registry for official metadata sources.
- Examples: `centraldefilamentos/models.py`, `centraldefilamentos/providers.py`
- Pattern: Frozen dataclass plus `MANUFACTURERS` map.
- Purpose: Connector-neutral row emitted by stock sources before normalization.
- Examples: `centraldefilamentos/models.py`, `centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/filamentos3d.py`
- Pattern: Frozen dataclass; connectors return `list[RawStockItem]`.
- Purpose: Canonical product identity fields derived from raw names and brand hints.
- Examples: `centraldefilamentos/models.py`, `centraldefilamentos/normalize.py`
- Pattern: Rules table plus detector functions, then `build_product_id` for durable ids.
- Purpose: Public catalog product plus provider offers serialized into `public/data/stock.json`.
- Examples: `centraldefilamentos/models.py`, `centraldefilamentos/build_data.py`
- Pattern: Frozen dataclasses with `to_dict` methods; `ProductGroup.offers` is sorted and de-duplicated before serialization.
- Purpose: Public provider health/contact/stats payload used by frontend provider summaries and build health.
- Examples: `centraldefilamentos/models.py`, `centraldefilamentos/build_data.py`
- Pattern: Derived from raw items and source errors in `_source_status`.
- Purpose: Metadata-only product records for manufacturer/provider catalog enrichment.
- Examples: `centraldefilamentos/connectors/grilon3_catalog.py`, `centraldefilamentos/connectors/filamentos3d_catalog.py`
- Pattern: Frozen dataclasses keyed by normalized product id.
- Purpose: Keep URL building, line labels, ranks, formatting, color swatches, search, and sort helpers consistent across Svelte apps.
- Examples: `src/lib/shared.js`
- Pattern: Named ES module exports consumed directly by Svelte components.
- Purpose: Shared navigation widget for popular material/line jumps.
- Examples: `src/components/QuickLines.svelte`, `src/CatalogApp.svelte`, `src/SummaryApp.svelte`
- Pattern: Component receives available line names and a target selector; it queries visible target nodes by `data-line`.

## Entry Points

- Location: `index.html`, `src/catalog.js`, `src/CatalogApp.svelte`
- Triggers: Browser navigation to `/CentraldeFilamentos/` or local Vite `index.html`.
- Responsibilities: Load stock data, filter/search, group product rows, show images and provider offers, manage local stock alerts.
- Location: `resumen.html`, `src/summary.js`, `src/SummaryApp.svelte`
- Triggers: Browser navigation to `/resumen.html`.
- Responsibilities: Render compact provider stock totals and product presentation rows.
- Location: `estadisticas.html`, `src/vendor-stats.js`, `src/VendorStatsApp.svelte`
- Triggers: Browser navigation to `/estadisticas.html`; page is `noindex,nofollow`.
- Responsibilities: Show provider history, movement charts, and build health when feature flag allows it.
- Location: `centraldefilamentos/build_data.py`
- Triggers: `python -m centraldefilamentos.build_data --output public/data/stock.json`.
- Responsibilities: Produce `public/data/stock.json`, logs, snapshots, and public provider history.
- Location: `centraldefilamentos/generate_thumbnails.py`, `centraldefilamentos/thumbnails.py`
- Triggers: `python -m centraldefilamentos.generate_thumbnails --stock-json public/data/stock.json`.
- Responsibilities: Generate thumbnails and update `thumbnail_url` fields for local product images.
- Location: `centraldefilamentos/cache_grilon3_metadata.py`, `centraldefilamentos/cache_filamentos3d_metadata.py`
- Triggers: Manual Python module commands documented in `README.md`.
- Responsibilities: Refresh metadata caches and local image assets for Grilon3 and Filamentos3D/3N3.
- Location: `centraldefilamentos/update_grilon3_images.py`, `centraldefilamentos/update_filamentos3d_images.py`
- Triggers: Manual scripts for applying existing refreshed cache data.
- Responsibilities: Apply image metadata to caches and stock payloads when explicitly used.
- Location: `tools/image-curation/server.mjs`, `tools/image-curation/index.html`, `tools/image-curation/app.js`
- Triggers: `npm run curate-images`.
- Responsibilities: Serve local product image review and persist ignored review state in `.image-curation/`.
- Location: `.github/workflows/ci.yml`
- Triggers: Pushes except data/assets-only paths, and pull requests.
- Responsibilities: Install Python/Node dependencies, run pytest, and build frontend.
- Location: `.github/workflows/data-capture.yml`
- Triggers: Manual dispatch and weekday cron.
- Responsibilities: Run stock build, commit generated data, and publish data files to `gh-pages`.
- Location: `.github/workflows/pages.yml`
- Triggers: Manual dispatch and pushes affecting UI/config files.
- Responsibilities: Build frontend and publish `dist/` to `gh-pages`.
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

### Bypassing SourceConfig Connector Dispatch

### Duplicating Frontend Line/Search Logic

### Running Bulk Image Refresh for One Product

### Fetching Static JSON Without dataUrl

## Error Handling

- Connector collection retries each source and records source-specific failures in `source_errors` (`centraldefilamentos/build_data.py:514`, `centraldefilamentos/build_data.py:532`).
- Build quality blocks publishing on source errors, schema errors, empty catalogs, suspicious total product drops, and suspicious provider stock drops (`centraldefilamentos/build_data.py:156`).
- Enrichment errors are warnings that allow stock publication with available data (`centraldefilamentos/build_data.py:545`, `centraldefilamentos/build_data.py:577`, `centraldefilamentos/build_data.py:610`).
- Frontend `fetchJson` catches network/parse errors and returns caller-provided fallbacks (`src/lib/shared.js:60`).
- Parser modules use defensive parsing for unknown stock values and non-product rows (`centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/filamentos3d.py`).

## Cross-Cutting Concerns

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
