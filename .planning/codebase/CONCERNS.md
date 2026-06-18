# Codebase Concerns

**Analysis Date:** 2026-06-18

## Tech Debt

**Monolithic data build pipeline:**
- Issue: `centraldefilamentos/build_data.py` combines payload assembly, quality gates, source retry logic, enrichment, metadata cache loading, stock history mutation, JSON writes, and the CLI in one 1,000+ line module.
- Files: `centraldefilamentos/build_data.py`
- Impact: Changes to unrelated behavior share the same module-level constants and helper functions, so a small enrichment or history change can regress publication, source status, or generated JSON shape.
- Fix approach: Split by responsibility before adding new behavior: keep orchestration in `centraldefilamentos/build_data.py`, move quality checks to `centraldefilamentos/build_quality.py`, history/snapshot writes to `centraldefilamentos/provider_history.py`, and metadata enrichment to `centraldefilamentos/enrichment.py`. Preserve public function names with thin wrappers until tests are migrated.

**Ordered heuristic normalization rules:**
- Issue: Product identity depends on ordered token lists and regexes in `centraldefilamentos/normalize.py`, plus connector-specific filters in `centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/filamentos3d.py`, `centraldefilamentos/connectors/filamentos3d_catalog.py`, and `centraldefilamentos/connectors/grilon3_catalog.py`.
- Files: `centraldefilamentos/normalize.py`, `centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/filamentos3d.py`, `centraldefilamentos/connectors/filamentos3d_catalog.py`, `centraldefilamentos/connectors/grilon3_catalog.py`
- Impact: New materials, colors, variants, provider wording, or category pages can be silently mis-grouped into existing product IDs. The blast radius is high because `build_product_id()` drives deduplication, image enrichment, provider cards, and generated static data.
- Fix approach: Add golden fixture tables for every provider and manufacturer line before changing rules. Keep the ordered rules, but require each new rule to include a positive fixture, a near-miss fixture, and a generated `product_id` assertion in `tests/test_normalize.py` or connector-specific tests.

**Silent enrichment degradation:**
- Issue: Several enrichment paths catch broad `Exception` and continue without recording per-product or per-fetch detail.
- Files: `centraldefilamentos/connectors/grilon3_catalog.py`, `centraldefilamentos/connectors/filamentos3d_catalog.py`, `centraldefilamentos/build_data.py`
- Impact: Missing Pantone, SKU, EAN, or product images can look like normal absence rather than a degraded fetch. The build publishes when enrichment errors are warnings, so metadata quality can drift without blocking publication.
- Fix approach: Return structured enrichment diagnostics from `enrich_grilon3_catalog_details()`, `enrich_grilon3_selected_details()`, and `enrich_filamentos3d_catalog_details()`. Include counts and failed URLs in `public/data/build_technical_log.json` while keeping business logs concise.

**Generated data and source code share publication commits:**
- Issue: Scheduled capture commits generated JSON from `centraldefilamentos/data/**` and `public/data/**` back to `master`, while CI ignores those paths on push.
- Files: `.github/workflows/data-capture.yml`, `.github/workflows/ci.yml`, `centraldefilamentos/data/provider_stock_history.json`, `centraldefilamentos/data/daily_provider_stock_snapshot.json`, `public/data/stock.json`
- Impact: Data-only commits can bypass the full CI workflow, even though tests include assertions against generated data in `tests/test_frontend_assets.py`.
- Fix approach: Add a lightweight data-validation workflow triggered by `centraldefilamentos/data/**` and `public/data/**`, or remove those paths from `paths-ignore` and keep expensive UI build steps conditional.

## Known Bugs

**Corrupt state JSON crashes the build:**
- Symptoms: `load_payload()` handles missing or invalid JSON defensively, but snapshot, history, and metadata loaders call `json.loads()` without `try/except`.
- Files: `centraldefilamentos/build_data.py`
- Trigger: A partial write, merge conflict artifact, manual edit, or truncated file in `centraldefilamentos/data/daily_provider_stock_snapshot.json`, `centraldefilamentos/data/provider_stock_history.json`, `centraldefilamentos/data/grilon3_metadata.json`, or `centraldefilamentos/data/filamentos3d_metadata.json`.
- Workaround: Fix or delete the corrupt JSON file before running `python -m centraldefilamentos.build_data`.

**Local pytest uses an unwritable default temp root on this Windows machine:**
- Symptoms: `python -m pytest -q` reports passing tests until fixtures needing `tmp_path` fail with `PermissionError: [WinError 5] Acceso denegado` under `C:\Users\Gabriel\AppData\Local\Temp\pytest-of-Gabriel`.
- Files: `pyproject.toml`, `tests/test_build_data.py`, `tests/test_daily_snapshot.py`, `tests/test_filamentos3d_catalog.py`, `tests/test_provider_stock_history.py`
- Trigger: Running the full Python test suite locally when pytest cannot create or reuse its default user temp directory.
- Workaround: Run pytest with an explicit writable base temp directory, for example `python -m pytest -q --basetemp .pytest_tmp`, and keep `.pytest_tmp/` uncommitted.

## Security Considerations

**Local image-curation server can become an SSRF and file-read surface if exposed:**
- Risk: `tools/image-curation/server.mjs` defaults to `HOST=127.0.0.1`, but honors `HOST` from the environment. Its `/api/candidates` and `/api/image` endpoints fetch arbitrary user-provided URLs without allowlisting protocols, domains, private IP ranges, redirects, timeouts, or response-size limits.
- Files: `tools/image-curation/server.mjs`, `tools/image-curation/app.js`, `.gitignore`
- Current mitigation: The server binds to localhost by default, `.image-curation/` is ignored by `.gitignore`, and it writes review state rather than public assets.
- Recommendations: Keep the server localhost-only for normal use. Add URL validation that permits only `http:` and `https:`, blocks private and link-local networks, applies `AbortSignal.timeout()`, follows limited redirects, and caps bytes read by `/api/image`.

**Static file path guard uses prefix matching:**
- Risk: `safeJoin()` checks `resolved.startsWith(path.resolve(baseDir))`, which can treat sibling paths with the same prefix as inside the base directory.
- Files: `tools/image-curation/server.mjs`
- Current mitigation: The guarded route is under the localhost-only curation tool and only serves files requested through `/public/`.
- Recommendations: Replace prefix matching with `path.relative(baseDir, resolved)` and reject paths that start with `..`, are absolute, or resolve outside `public/`.

**GitHub Actions use broad write permissions for publication:**
- Risk: Workflows that publish data, UI, and thumbnails all use `contents: write` and push to `master` or `gh-pages`.
- Files: `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, `.github/workflows/thumbnails.yml`
- Current mitigation: Workflows run on controlled triggers, use the repository token, and avoid external secrets in repo files.
- Recommendations: Keep write permissions only on publishing jobs. Add branch protection or workflow rules so generated commits cannot overwrite manual work without review.

## Performance Bottlenecks

**Provider fetches are serial at the source level:**
- Problem: `collect_raw_items()` fetches each configured source one after another, with retries inside each source.
- Files: `centraldefilamentos/build_data.py`, `centraldefilamentos/providers.py`
- Cause: `for source in sources.values()` calls `_fetch_source_items_with_retries()` synchronously for every provider.
- Improvement path: Fetch independent sources concurrently with a small worker pool. Preserve source-specific error capture so one failed provider still yields partial source status and quality logs.

**Filamentos3D catalog detail enrichment is sequential:**
- Problem: `enrich_filamentos3d_catalog_details()` fetches every product detail page one by one with a 12 second timeout.
- Files: `centraldefilamentos/connectors/filamentos3d_catalog.py`, `centraldefilamentos/cache_filamentos3d_metadata.py`
- Cause: Detail enrichment loops over `catalog.items()` and awaits each `httpx.get()` before moving to the next product.
- Improvement path: Add bounded concurrency, response caching, and summary diagnostics. Keep parser tests in `tests/test_filamentos3d_catalog.py` fixture-based to avoid network-dependent tests.

**Image proxy buffers whole remote images in memory:**
- Problem: `/api/image` reads the entire upstream response with `arrayBuffer()` before sending it to the browser.
- Files: `tools/image-curation/server.mjs`
- Cause: The proxy converts the full upstream body to `Buffer` and only then calls `response.end(bytes)`.
- Improvement path: Stream the upstream body to the response with a byte cap and timeout. Reject oversized content based on `content-length` when present and stop streaming after the configured maximum.

**Frontend fetches full JSON payloads on static pages:**
- Problem: Svelte entry points fetch generated JSON files directly from `public/data/stock.json` and `public/data/provider_stock_history.json`.
- Files: `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, `src/VendorStatsApp.svelte`, `public/data/stock.json`, `public/data/provider_stock_history.json`
- Cause: Static hosting has no server-side pagination, filtering, or incremental data endpoint.
- Improvement path: Keep this model while the catalog is small. If provider count or product count grows materially, generate smaller route-specific JSON files during `centraldefilamentos/build_data.py`.

## Fragile Areas

**External provider markup and spreadsheets are unversioned contracts:**
- Files: `centraldefilamentos/providers.py`, `centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/filamentos3d.py`, `centraldefilamentos/connectors/filamentos3d_catalog.py`, `centraldefilamentos/connectors/grilon3_catalog.py`
- Why fragile: Google Sheet headers, stock text, HTML table shape, category card classes, and WooCommerce gallery markup are parsed by heuristics. Provider changes can produce empty or malformed data without a code change.
- Safe modification: Add fixture snapshots for each new provider page or spreadsheet shape under `tests/fixtures/`, then update the connector parser and quality thresholds together.
- Test coverage: `tests/test_google_sheet.py`, `tests/test_filamentos3d.py`, `tests/test_filamentos3d_catalog.py`, and `tests/test_grilon3_catalog.py` cover representative fixtures; they do not protect against live upstream changes until fixtures are refreshed.

**Publication workflows can race on `gh-pages`:**
- Files: `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, `.github/workflows/thumbnails.yml`
- Why fragile: Data capture, UI publishing, and thumbnail publishing each clone and push `gh-pages` independently. Their concurrency groups are separate, so two workflows can publish overlapping branch content near the same time.
- Safe modification: Use one reusable publish job or one shared `gh-pages` concurrency group. Rebase or retry pushes when the remote branch changes during the job.
- Test coverage: Workflow behavior is not covered by `tests/`; validation is through GitHub Actions execution.

**Metadata cache keys depend on normalized product IDs and legacy fallbacks:**
- Files: `centraldefilamentos/build_data.py`, `centraldefilamentos/data/grilon3_metadata.json`, `centraldefilamentos/data/filamentos3d_metadata.json`, `centraldefilamentos/cache_grilon3_metadata.py`, `centraldefilamentos/cache_filamentos3d_metadata.py`
- Why fragile: A normalization change can orphan cached images, Pantone values, SKUs, or EANs. Legacy and unknown-diameter fallback logic can also attach metadata to nearby products if guard logic misses a case.
- Safe modification: Before changing `build_product_id()` or color/material rules, run generated-data tests and add targeted assertions in `tests/test_build_data.py` and `tests/test_frontend_assets.py`.
- Test coverage: Tests cover many cache edge cases, including presentation-specific images and color mismatches, but cache integrity still depends on fixture breadth.

**Frontend behavior is checked mostly through static source assertions:**
- Files: `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, `src/VendorStatsApp.svelte`, `src/lib/shared.js`, `tests/test_frontend_assets.py`
- Why fragile: Tests inspect source files and generated JSON but do not execute Svelte components in a browser-like runtime.
- Safe modification: For interactive filters, subscriptions, or responsive behavior, add Playwright or component tests before large UI changes.
- Test coverage: `tests/test_frontend_assets.py` validates required assets, source snippets, CSS constraints, and generated data invariants; it does not verify runtime DOM behavior.

## Scaling Limits

**Provider stock history is capped at 30 days:**
- Current capacity: `maybe_update_provider_stock_history()` and `write_public_provider_stock_history()` default to `max_days=30`.
- Limit: Longer trend windows, month-over-month reporting, and seasonal analysis are unavailable from `public/data/provider_stock_history.json`.
- Scaling path: Store long-term history in an internal file and publish a compact rolling window plus precomputed aggregates for the static frontend.

**Build quality thresholds are global constants:**
- Current capacity: Drop checks use `MIN_PRODUCTS_FOR_DROP_CHECK`, `MIN_PROVIDER_STOCK_FOR_DROP_CHECK`, `MAX_PRODUCT_DROP_RATIO`, and `MAX_PROVIDER_STOCK_DROP_RATIO`.
- Limit: Providers with different catalog sizes or volatility share the same thresholds.
- Scaling path: Move thresholds to per-source configuration in `centraldefilamentos/providers.py`, with defaults in `centraldefilamentos/build_data.py`.

**Static hosting limits server-side filtering:**
- Current capacity: The app serves built assets from `dist/` and JSON from `public/data/`.
- Limit: Large catalogs increase download size and client-side filtering work on every page load.
- Scaling path: Generate pre-sliced static JSON by page, material, provider, and summary view during the data build.

## Dependencies at Risk

**Live provider pages and Google Sheets:**
- Risk: External URLs in `centraldefilamentos/providers.py`, `centraldefilamentos/connectors/filamentos3d_catalog.py`, and `centraldefilamentos/connectors/grilon3_catalog.py` can change markup, access rules, or availability without versioning.
- Impact: Stock publication can be blocked by source errors, or enrichment can degrade to missing images/metadata.
- Migration plan: Keep raw fixture snapshots in `tests/fixtures/`, add live smoke checks as optional scheduled diagnostics, and record connector failure counts in technical logs.

**Generated image assets and thumbnails:**
- Risk: `public/assets/**` and `public/assets/thumbs/**` are committed generated assets tied to metadata cache entries and stock JSON URLs.
- Impact: Renaming, deleting, or regenerating assets without updating `public/data/stock.json` can break images on the static site.
- Migration plan: Treat asset regeneration as a pipeline step: run thumbnail generation, generated-data tests, and UI build together before publishing.

## Missing Critical Features

**No explicit alerting for blocked publication:**
- Problem: When quality checks block publication, `centraldefilamentos/build_data.py` writes logs and returns without failing the command.
- Blocks: Operators must inspect workflow output or generated logs to notice stale public stock data.
- Files: `centraldefilamentos/build_data.py`, `.github/workflows/data-capture.yml`, `public/data/build_business_log.json`, `public/data/build_technical_log.json`

**No automated validation for the image-curation tool:**
- Problem: The Node server and browser script have no dedicated tests.
- Blocks: Changes to candidate extraction, proxy behavior, saved selection shape, and path safety rely on manual verification.
- Files: `tools/image-curation/server.mjs`, `tools/image-curation/app.js`, `tools/image-curation/index.html`, `tools/image-curation/styles.css`

**No typed schema contract for generated public JSON:**
- Problem: `public/data/stock.json`, `public/data/provider_stock_history.json`, and build logs are validated by hand-written checks and tests, but there is no shared JSON Schema or TypeScript type emitted for frontend consumers.
- Blocks: Svelte components and Python builders can drift in expected field names and optionality.
- Files: `centraldefilamentos/models.py`, `centraldefilamentos/build_data.py`, `src/lib/shared.js`, `src/CatalogApp.svelte`, `public/data/stock.json`

## Test Coverage Gaps

**Image curation server and UI:**
- What's not tested: HTTP routes, request body validation, URL filtering, image proxy behavior, candidate extraction, saved selection JSON shape, and browser interactions.
- Files: `tools/image-curation/server.mjs`, `tools/image-curation/app.js`
- Risk: Security and data-review regressions can ship unnoticed because no `tests/` file imports or exercises the Node tool.
- Priority: High

**Corrupt JSON loader handling:**
- What's not tested: Invalid JSON in snapshot, history, and metadata cache files.
- Files: `centraldefilamentos/build_data.py`, `tests/test_build_data.py`, `tests/test_daily_snapshot.py`, `tests/test_provider_stock_history.py`
- Risk: A single corrupt generated file can stop scheduled capture before quality logs or fallback publication logic run.
- Priority: High

**Workflow publication behavior:**
- What's not tested: GitHub Actions push conflicts, `gh-pages` publication order, data-only CI validation, and blocked-publication signaling.
- Files: `.github/workflows/ci.yml`, `.github/workflows/data-capture.yml`, `.github/workflows/pages.yml`, `.github/workflows/thumbnails.yml`
- Risk: Publishing can fail or publish stale data even when code tests pass.
- Priority: Medium

**Runtime frontend interaction tests:**
- What's not tested: Real DOM rendering, filter interaction, localStorage subscription state, responsive behavior, and fetch error states.
- Files: `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, `src/VendorStatsApp.svelte`, `src/lib/stockSubscriptions.js`, `tests/test_frontend_assets.py`
- Risk: Static assertions can pass while users see broken interactions after bundling.
- Priority: Medium

---

*Concerns audit: 2026-06-18*
