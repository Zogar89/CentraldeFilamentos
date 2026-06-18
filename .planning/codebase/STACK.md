# Technology Stack

**Analysis Date:** 2026-06-18

## Languages

**Primary:**
- Python 3.12 - Data ingestion, normalization, metadata enrichment, JSON generation, thumbnail generation, and tests in `centraldefilamentos/`, `tests/`, `pyproject.toml`, and `.github/workflows/*.yml`.
- JavaScript ES modules - Svelte/Vite app entry points and local image-curation server in `src/catalog.js`, `src/summary.js`, `src/vendor-stats.js`, `src/lib/shared.js`, and `tools/image-curation/server.mjs`.
- Svelte 5.55.7 - Frontend UI components in `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, `src/VendorStatsApp.svelte`, and `src/components/*.svelte`.

**Secondary:**
- CSS - Shared frontend styling in `src/styles/global.css` and local image-curation styling in `tools/image-curation/styles.css`.
- HTML - Vite multi-page entry files in `index.html`, `resumen.html`, and `estadisticas.html`; local image-curation UI in `tools/image-curation/index.html`.
- YAML - GitHub Actions workflows in `.github/workflows/ci.yml`, `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, and `.github/workflows/thumbnails.yml`.
- JSON - Generated/static data and metadata caches in `public/data/*.json`, `centraldefilamentos/data/*.json`, `public/assets/**`, and `package-lock.json`.

## Runtime

**Environment:**
- Python >=3.12 - Declared in `pyproject.toml`; GitHub Actions pins `python-version: "3.12"` in `.github/workflows/ci.yml`, `.github/workflows/data-capture.yml`, and `.github/workflows/thumbnails.yml`.
- Node.js 24 - GitHub Actions pins `node-version: "24"` in `.github/workflows/ci.yml` and `.github/workflows/pages.yml`.
- Browser runtime - The built static site runs as plain HTML/CSS/JS from GitHub Pages and reads static JSON with `fetch` in `src/lib/shared.js`.

**Package Manager:**
- npm - Scripts and frontend dev dependencies live in `package.json`; CI and Pages use `npm ci` in `.github/workflows/ci.yml` and `.github/workflows/pages.yml`.
- pip/setuptools - Python packaging uses `setuptools.build_meta` in `pyproject.toml`; workflows install with `python -m pip install -e .` or `python -m pip install -e ".[dev]"`.
- Lockfile: present for frontend dependencies at `package-lock.json` with lockfileVersion 3. No Python lockfile is present.

## Frameworks

**Core:**
- Svelte 5.55.7 - Component framework for catalog, summary, vendor stats, header/footer, and quick-line filters in `src/*.svelte` and `src/components/*.svelte`.
- Vite 8.0.13 - Frontend dev server/build tool configured in `vite.config.js`; outputs to `dist/` and builds three HTML entry points.
- @sveltejs/vite-plugin-svelte 7.1.2 - Vite/Svelte integration configured in `vite.config.js`.
- Python package `centraldefilamentos` - Data pipeline package declared in `pyproject.toml` and implemented under `centraldefilamentos/`.

**Testing:**
- pytest >=8.2.0 - Python test runner declared in `pyproject.toml`; tests live in `tests/` and CI runs `python -m pytest -v` in `.github/workflows/ci.yml`.
- Frontend asset checks - Python tests inspect frontend source/build assumptions in `tests/test_frontend_assets.py`; there is no dedicated JS test runner configured in `package.json`.

**Build/Dev:**
- Vite - `npm run dev`, `npm run build`, and `npm run preview` are defined in `package.json`.
- setuptools >=69 - Python build backend configured in `pyproject.toml`.
- GitHub Actions - CI, data capture, UI publish, and thumbnail publish workflows live in `.github/workflows/`.
- Node built-in HTTP server - Local image-curation tool uses `node:http`, `node:fs`, and `fetch` in `tools/image-curation/server.mjs`.

## Key Dependencies

**Critical:**
- `svelte` 5.55.7 - Required for all frontend pages mounted from `src/catalog.js`, `src/summary.js`, and `src/vendor-stats.js`.
- `vite` 8.0.13 - Required for local frontend development and production build configured in `vite.config.js`.
- `@sveltejs/vite-plugin-svelte` 7.1.2 - Required to compile Svelte components through Vite in `vite.config.js`.
- `requests>=2.32.3` - Used for Google Sheet CSV export, Grilon3 catalog/product fetches, and image downloads in `centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/grilon3_catalog.py`, and `centraldefilamentos/cache_grilon3_metadata.py`.
- `httpx>=0.27.0` - Used for Filamentos3D stock/catalog fetches and image downloads in `centraldefilamentos/connectors/filamentos3d.py`, `centraldefilamentos/connectors/filamentos3d_catalog.py`, and `centraldefilamentos/cache_filamentos3d_metadata.py`.
- `beautifulsoup4>=4.12.3` - Used to parse Filamentos3D HTML pages in `centraldefilamentos/connectors/filamentos3d.py` and `centraldefilamentos/connectors/filamentos3d_catalog.py`.
- `lxml>=5.2.0` - Preferred BeautifulSoup parser for Filamentos3D HTML parsing in `centraldefilamentos/connectors/filamentos3d.py` and `centraldefilamentos/connectors/filamentos3d_catalog.py`.
- `Pillow>=10.4.0` - Used for thumbnail generation in `centraldefilamentos/thumbnails.py`.

**Infrastructure:**
- GitHub Actions `actions/checkout@v6` - Source checkout in all workflows under `.github/workflows/`.
- GitHub Actions `actions/setup-python@v6` - Python 3.12 setup in `.github/workflows/ci.yml`, `.github/workflows/data-capture.yml`, and `.github/workflows/thumbnails.yml`.
- GitHub Actions `actions/setup-node@v6` - Node 24 setup with npm cache in `.github/workflows/ci.yml` and `.github/workflows/pages.yml`.
- Git CLI - Workflows clone, commit, and push generated artifacts to `master` and `gh-pages` in `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, and `.github/workflows/thumbnails.yml`.

## Configuration

**Environment:**
- Vite base path is `/CentraldeFilamentos/` in `vite.config.js`; frontend data URLs are built with `import.meta.env.BASE_URL` in `src/lib/shared.js`.
- Local image-curation server reads optional `PORT` and `HOST` environment variables, defaulting to `4177` and `127.0.0.1`, in `tools/image-curation/server.mjs`.
- GitHub Actions uses the built-in `${{ github.token }}` as `GH_TOKEN` for publishing to `gh-pages` in `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, and `.github/workflows/thumbnails.yml`.
- No `.env` files are present at repo root. No application secrets are read by the Python data pipeline or frontend.

**Build:**
- `vite.config.js` configures Svelte, `base`, `dist/` output, and multi-page Rollup inputs: `index.html`, `resumen.html`, and `estadisticas.html`.
- `svelte.config.js` currently exports an empty Svelte config.
- `pyproject.toml` configures Python package metadata, dependencies, optional `dev` dependencies, setuptools package discovery, and pytest paths.
- `package.json` defines `dev`, `build`, `preview`, and `curate-images` scripts.
- `.gitignore` excludes generated/local directories: `.superpowers/`, `__pycache__/`, `.pytest_cache/`, `node_modules/`, `dist/`, and `.image-curation/`.

## Platform Requirements

**Development:**
- Install Python dependencies with `python -m pip install -e ".[dev]"` from `README.md`.
- Install frontend dependencies with `npm ci` from `README.md`.
- Run tests with `python -m pytest -v` on Linux/GitHub Actions or `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos` on Windows as documented in `README.md`.
- Generate data with `python -m centraldefilamentos.build_data --output public/data/stock.json` from `README.md`.
- Run local frontend with `npm run dev` and local image-curation UI with `npm run curate-images` from `package.json`.

**Production:**
- Deployment target is GitHub Pages at `https://zogar89.github.io/CentraldeFilamentos/`, documented in `README.md` and `docs/publishing-workflows.md`.
- GitHub Pages uses legacy publishing from branch `gh-pages`, path `/`, documented in `README.md` and `docs/publishing-workflows.md`.
- UI publication copies `dist/` to the root of `gh-pages` in `.github/workflows/pages.yml`.
- Data publication copies `public/data/*.json` to `gh-pages/data/` in `.github/workflows/data-capture.yml`.
- Asset publication copies `public/assets/` and `public/data/stock.json` to `gh-pages` in `.github/workflows/thumbnails.yml`.

---

*Stack analysis: 2026-06-18*
