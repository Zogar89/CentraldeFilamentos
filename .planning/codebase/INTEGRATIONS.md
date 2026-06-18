# External Integrations

**Analysis Date:** 2026-06-18

## APIs & External Services

**Stock Sources:**
- Filamentos3D stock page - HTML source for Zona Sur stock in `centraldefilamentos/providers.py` and `centraldefilamentos/connectors/filamentos3d.py`.
  - SDK/Client: `httpx` from `pyproject.toml`; called with `httpx.get(..., follow_redirects=True)` in `centraldefilamentos/connectors/filamentos3d.py`.
  - Auth: Not required.
  - URL: `https://filamentos3d.com.ar/grilon3.php` configured in `centraldefilamentos/providers.py`.
- Grupo Senz Google Sheet - CSV export source for Zona Oeste stock in `centraldefilamentos/providers.py` and `centraldefilamentos/connectors/google_sheet.py`.
  - SDK/Client: `requests` from `pyproject.toml`; called with `requests.get(...)` in `centraldefilamentos/connectors/google_sheet.py`.
  - Auth: Not required; uses public Google Sheets CSV export.
  - Sheet: `sheet_id="14nblAeXZfx_TEeHj4xnK90hSmUp3hk6KSO4nUTrb9zM"`, `gid="614179668"` in `centraldefilamentos/providers.py`.
- MundoInsumos Google Sheet - CSV export source for Zona Norte stock in `centraldefilamentos/providers.py` and `centraldefilamentos/connectors/google_sheet.py`.
  - SDK/Client: `requests` from `pyproject.toml`; called with `requests.get(...)` in `centraldefilamentos/connectors/google_sheet.py`.
  - Auth: Not required; uses public Google Sheets CSV export.
  - Sheet: `sheet_id="1r-nKy4tRRtZ-5xwgxAcia8REDVW0Dv0h"`, `gid="1981641819"` in `centraldefilamentos/providers.py`.

**Product Metadata & Images:**
- Grilon3 product catalog - Official product metadata, product URLs, images, Pantone, SKU, and EAN in `centraldefilamentos/providers.py`, `centraldefilamentos/connectors/grilon3_catalog.py`, and `centraldefilamentos/cache_grilon3_metadata.py`.
  - SDK/Client: `requests` from `pyproject.toml`; catalog/detail fetches use `requests.get(...)` in `centraldefilamentos/connectors/grilon3_catalog.py`.
  - Auth: Not required.
  - URLs: `https://grilon3.com.ar/productos/` and `https://grilon3.com.ar/product-sitemap.xml` in `centraldefilamentos/connectors/grilon3_catalog.py`.
- Filamentos3D category/product pages - 3N3 product image and SKU enrichment in `centraldefilamentos/connectors/filamentos3d_catalog.py` and `centraldefilamentos/cache_filamentos3d_metadata.py`.
  - SDK/Client: `httpx` from `pyproject.toml`; category/detail fetches use `httpx.get(..., follow_redirects=True)` in `centraldefilamentos/connectors/filamentos3d_catalog.py`.
  - Auth: Not required.
  - Category URLs: `https://filamentos3d.com.ar/43-pla-3n3-175mm-1kg`, `https://filamentos3d.com.ar/49-3nmax-pla`, `https://filamentos3d.com.ar/66-3nflex-pla-175mm`, `https://filamentos3d.com.ar/48-3n3-petg-175mm`, and `https://filamentos3d.com.ar/40-3n3-epet-175mm` in `centraldefilamentos/connectors/filamentos3d_catalog.py`.

**Publishing & Hosting:**
- GitHub Pages - Static hosting for the site in `README.md`, `docs/publishing-workflows.md`, `.github/workflows/pages.yml`, `.github/workflows/data-capture.yml`, and `.github/workflows/thumbnails.yml`.
  - SDK/Client: Git CLI in GitHub Actions; no GitHub Pages API is used by the workflows.
  - Auth: `GH_TOKEN` assigned from `${{ github.token }}` in `.github/workflows/pages.yml`, `.github/workflows/data-capture.yml`, and `.github/workflows/thumbnails.yml`.
  - Published URL: `https://zogar89.github.io/CentraldeFilamentos/` in `README.md`.
- GitHub Issues - Public contact/feedback link in `src/lib/shared.js`.
  - SDK/Client: Browser link only.
  - Auth: Not required by the application.
  - URL: `https://github.com/Zogar89/CentraldeFilamentos/issues/new` in `src/lib/shared.js`.

**Local Tooling:**
- Image candidate collection - Local human-in-the-loop tool fetches product pages/images from arbitrary reviewed URLs in `tools/image-curation/server.mjs`.
  - SDK/Client: Node global `fetch` and built-in `node:http` in `tools/image-curation/server.mjs`.
  - Auth: Not required.
  - Runtime config: optional `PORT` and `HOST` in `tools/image-curation/server.mjs`.

## Data Storage

**Databases:**
- Not detected.
  - Connection: Not applicable.
  - Client: Not applicable.

**File Storage:**
- Local JSON files are the primary application data store. Generated public data lives in `public/data/stock.json`, `public/data/provider_stock_history.json`, `public/data/build_business_log.json`, and `public/data/build_technical_log.json`.
- Versioned pipeline caches live in `centraldefilamentos/data/grilon3_metadata.json`, `centraldefilamentos/data/filamentos3d_metadata.json`, `centraldefilamentos/data/daily_provider_stock_snapshot.json`, and `centraldefilamentos/data/provider_stock_history.json`.
- Local static image assets live in `public/assets/grilon3/`, `public/assets/filamentos3d/`, and generated thumbnails in `public/assets/thumbs/`.
- Local image-curation state lives in `.image-curation/selection.json`, `.image-curation/selections.json`, and `.image-curation/candidates.json`; `.image-curation/` is ignored by `.gitignore`.
- Published static storage is the `gh-pages` branch, with UI files at branch root, JSON under `data/`, and images under `assets/`, managed by `.github/workflows/pages.yml`, `.github/workflows/data-capture.yml`, and `.github/workflows/thumbnails.yml`.

**Caching:**
- Grilon3 metadata cache: `centraldefilamentos/data/grilon3_metadata.json`, read by `centraldefilamentos/build_data.py` and refreshed by `centraldefilamentos/cache_grilon3_metadata.py`.
- Filamentos3D metadata cache: `centraldefilamentos/data/filamentos3d_metadata.json`, read by `centraldefilamentos/build_data.py` and refreshed by `centraldefilamentos/cache_filamentos3d_metadata.py`.
- Provider daily snapshot: `centraldefilamentos/data/daily_provider_stock_snapshot.json`, maintained by `centraldefilamentos/build_data.py`.
- Provider stock history: `centraldefilamentos/data/provider_stock_history.json` and public mirror `public/data/provider_stock_history.json`, maintained by `centraldefilamentos/build_data.py`.
- Browser-side subscription state: `localStorage` key `centraldefilamentos.stockSubscriptions.v1` in `src/lib/stockSubscriptions.js`.

## Authentication & Identity

**Auth Provider:**
- Not detected for the application.
  - Implementation: Public static site with no login, sessions, OAuth, JWT, or backend auth in `src/`, `centraldefilamentos/`, or `tools/image-curation/`.

**Publishing Identity:**
- GitHub Actions uses the built-in `github-actions[bot]` identity for commits in `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, and `.github/workflows/thumbnails.yml`.
- GitHub Actions authenticates Git pushes with `${{ github.token }}` exposed as `GH_TOKEN` in `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, and `.github/workflows/thumbnails.yml`.

## Monitoring & Observability

**Error Tracking:**
- External error tracking is not detected.
- Build health logs are generated as JSON by `centraldefilamentos/build_data.py` and written to `public/data/build_business_log.json` and `public/data/build_technical_log.json`.
- The vendor stats page reads health logs with `fetchJson("data/build_business_log.json", ...)` in `src/VendorStatsApp.svelte`.

**Logs:**
- Data quality checks and events are created in `centraldefilamentos/build_data.py`.
- CLI scripts print concise status messages in `centraldefilamentos/cache_grilon3_metadata.py`, `centraldefilamentos/cache_filamentos3d_metadata.py`, and `centraldefilamentos/thumbnails.py`.
- The local image-curation server logs its URL and state behavior to stdout in `tools/image-curation/server.mjs`.
- GitHub Actions logs workflow command output in `.github/workflows/*.yml`.

## CI/CD & Deployment

**Hosting:**
- GitHub Pages from branch `gh-pages`, path `/`, documented in `README.md` and `docs/publishing-workflows.md`.
- Vite base path is `/CentraldeFilamentos/` in `vite.config.js`; frontend data URLs are built relative to that base in `src/lib/shared.js`.

**CI Pipeline:**
- `.github/workflows/ci.yml` runs on push and pull request, installs Python and Node dependencies, runs `python -m pytest -v`, and runs `npm run build`.
- `.github/workflows/data-capture.yml` runs manually and on a weekday cron, builds stock JSON with `python -m centraldefilamentos.build_data --output public/data/stock.json`, commits generated data to `master`, and publishes `public/data/*.json` to `gh-pages/data/`.
- `.github/workflows/pages.yml` runs manually and on UI/config changes to `master`, builds with `npm run build`, and publishes `dist/` to `gh-pages`.
- `.github/workflows/thumbnails.yml` runs manually and on source asset changes, runs `python -m centraldefilamentos.generate_thumbnails --stock-json public/data/stock.json`, commits thumbnails, and publishes `public/assets/` plus `public/data/stock.json` to `gh-pages`.

## Environment Configuration

**Required env vars:**
- No runtime environment variables are required for the public static frontend or Python data pipeline.
- `PORT` is optional for `tools/image-curation/server.mjs`; default is `4177`.
- `HOST` is optional for `tools/image-curation/server.mjs`; default is `127.0.0.1`.
- `GH_TOKEN` is required inside publishing workflow steps but is supplied from `${{ github.token }}` in `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, and `.github/workflows/thumbnails.yml`.

**Secrets location:**
- No `.env` files are present at repo root.
- No project-managed secret files are detected.
- GitHub Actions uses GitHub's built-in `github.token`; no repository secret names are referenced in `.github/workflows/*.yml`.

## Webhooks & Callbacks

**Incoming:**
- No production webhook endpoints are detected; the public application is static.
- Local-only HTTP API endpoints exist in `tools/image-curation/server.mjs`: `GET /api/products`, `GET /api/selection`, `GET /api/selections`, `GET /api/candidate-cache`, `GET /api/image`, `POST /api/candidates`, `POST /api/select`, and `POST /api/review`.

**Outgoing:**
- Python data capture fetches external stock, catalog, sitemap, product detail, and image URLs from Google Sheets, Filamentos3D, and Grilon3 in `centraldefilamentos/connectors/*.py`, `centraldefilamentos/cache_grilon3_metadata.py`, and `centraldefilamentos/cache_filamentos3d_metadata.py`.
- The frontend opens provider/contact URLs and WhatsApp links from source metadata in `centraldefilamentos/providers.py`, rendered through components that consume `public/data/stock.json`.
- GitHub Actions pushes commits to the repository and the `gh-pages` branch in `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, and `.github/workflows/thumbnails.yml`.

---

*Integration audit: 2026-06-18*
