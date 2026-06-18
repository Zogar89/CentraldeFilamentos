# Coding Conventions

**Analysis Date:** 2026-06-18

## Naming Patterns

**Files:**
- Use lowercase Python module names with underscores under `centraldefilamentos/`, such as `centraldefilamentos/build_data.py`, `centraldefilamentos/cache_grilon3_metadata.py`, and `centraldefilamentos/connectors/google_sheet.py`.
- Use Svelte component names in PascalCase under `src/`, such as `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, `src/components/SiteHeader.svelte`, and `src/components/QuickLines.svelte`.
- Use lowercase JavaScript entry and utility files under `src/`, such as `src/catalog.js`, `src/summary.js`, `src/vendor-stats.js`, `src/lib/shared.js`, and `src/lib/stockSubscriptions.js`.
- Use pytest file names in `tests/test_*.py`, such as `tests/test_build_data.py`, `tests/test_normalize.py`, and `tests/test_frontend_assets.py`.

**Functions:**
- Use `snake_case` for Python functions and private helpers in `centraldefilamentos/build_data.py`, `centraldefilamentos/normalize.py`, and `centraldefilamentos/connectors/filamentos3d.py`.
- Prefix internal Python helpers with `_`, such as `_write_json`, `_detect_material`, `_parse_stock`, `_normalize_header`, and `_soup` in `centraldefilamentos/build_data.py`, `centraldefilamentos/normalize.py`, and `centraldefilamentos/connectors/google_sheet.py`.
- Use descriptive action-oriented public Python names, such as `build_payload`, `write_payload`, `load_payload`, `evaluate_build_quality`, `fetch_sheet_items`, and `parse_sheet_csv` in `centraldefilamentos/build_data.py` and `centraldefilamentos/connectors/google_sheet.py`.
- Use `camelCase` for JavaScript and Svelte functions, such as `matchesFilters`, `setFilter`, `groupProducts`, `fetchJson`, `formatDate`, and `colorSwatchStyle` in `src/CatalogApp.svelte` and `src/lib/shared.js`.

**Variables:**
- Use `snake_case` for Python locals and parameters, such as `raw_items`, `source_errors`, `generated_at`, `timeout_seconds`, and `stock_quantity` in `centraldefilamentos/build_data.py` and `centraldefilamentos/connectors/google_sheet.py`.
- Use `UPPER_SNAKE_CASE` for Python module constants, such as `GRILON3_METADATA_CACHE`, `DEFAULT_ENRICHMENT`, `MATERIAL_RULES`, `COLOR_RULES`, and `SOURCES` in `centraldefilamentos/build_data.py`, `centraldefilamentos/normalize.py`, and `centraldefilamentos/providers.py`.
- Use `camelCase` for JavaScript and Svelte locals, props, and reactive values, such as `generatedAt`, `categoryOrder`, `lineOptions`, `availableLines`, and `stockSubscriptions` in `src/CatalogApp.svelte`.
- Use short domain names only when the surrounding context is clear, such as `item`, `source`, `fields`, `payload`, and `product` in `centraldefilamentos/build_data.py`, `centraldefilamentos/normalize.py`, and `src/CatalogApp.svelte`.

**Types:**
- Use frozen Python dataclasses for public data models in `centraldefilamentos/models.py`; add new payload entities as `@dataclass(frozen=True)` with explicit type annotations and a `to_dict()` method when serialized.
- Use `typing.Literal` aliases for constrained strings in `centraldefilamentos/models.py`, such as `StockStatus`, `SourceRunStatus`, and `ImageSource`.
- Use modern Python built-in generics and unions, such as `dict[str, object]`, `list[RawStockItem]`, and `int | None` in `centraldefilamentos/models.py` and `centraldefilamentos/build_data.py`.
- JavaScript files under `src/` are plain JavaScript, not TypeScript; do not introduce TypeScript-only syntax in `src/lib/shared.js`, `src/catalog.js`, or `src/CatalogApp.svelte`.

## Code Style

**Formatting:**
- Python formatting is conventional 4-space indentation with blank lines between top-level functions, shown in `centraldefilamentos/models.py`, `centraldefilamentos/normalize.py`, and `centraldefilamentos/connectors/google_sheet.py`.
- JavaScript and Svelte formatting uses 2-space indentation, double quotes, semicolons, and object literals split across lines when helpful in `src/CatalogApp.svelte`, `src/lib/shared.js`, and `vite.config.js`.
- JSON output written by backend code uses `json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True) + "\n"` via `_write_json()` in `centraldefilamentos/build_data.py`.
- No Prettier, Black, Ruff, ESLint, Biome, or formatting config is detected in `.prettierrc*`, `.eslintrc*`, `eslint.config.*`, `biome.json`, or `pyproject.toml`.

**Linting:**
- No lint command is configured in `package.json`, `pyproject.toml`, or `.github/workflows/ci.yml`.
- CI quality gates are `python -m pytest -v` and `npm run build` in `.github/workflows/ci.yml`; keep new code compatible with those commands.
- Add any future linting config explicitly before relying on formatter-specific behavior; current source files such as `centraldefilamentos/build_data.py` and `src/CatalogApp.svelte` are the style source of truth.

## Import Organization

**Order:**
1. Python standard library imports first, as in `centraldefilamentos/build_data.py` (`argparse`, `json`, `re`, `unicodedata`, `collections`, `datetime`, `pathlib`, `typing`, `zoneinfo`).
2. Third-party imports next, as in `centraldefilamentos/connectors/filamentos3d.py` (`bs4`, `httpx`) and `centraldefilamentos/connectors/google_sheet.py` (`requests`).
3. Local `centraldefilamentos.*` imports last, as in `centraldefilamentos/build_data.py`, `tests/test_build_data.py`, and `tests/test_google_sheet.py`.
4. Svelte component imports and local utilities are grouped at the top of `<script>` blocks, as in `src/CatalogApp.svelte`; import Svelte APIs first, components next, then `src/lib/*` helpers.

**Path Aliases:**
- No JavaScript path aliases are detected; use relative imports such as `./components/SiteHeader.svelte`, `./lib/shared.js`, and `../lib/shared.js` in `src/CatalogApp.svelte` and `src/components/SiteHeader.svelte`.
- Python tests and modules use package imports from `centraldefilamentos.*`; `pyproject.toml` sets `pythonpath = ["."]` for pytest.

## Error Handling

**Patterns:**
- Network fetchers call `raise_for_status()` immediately after `requests.get()` or `httpx.get()`, then delegate parsing to pure functions in `centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/filamentos3d.py`, and `centraldefilamentos/connectors/grilon3_catalog.py`.
- Parser helpers return defensive defaults for malformed optional values, such as `None`, `""`, or `[]`, in `_parse_stock()` and `_cell()` in `centraldefilamentos/connectors/google_sheet.py` and `centraldefilamentos/connectors/filamentos3d.py`.
- Expected data-contract violations raise `ValueError` with actionable messages, such as missing product columns in `centraldefilamentos/connectors/google_sheet.py` and repeated provider offers in `centraldefilamentos/build_data.py`.
- Build orchestration keeps partial source failures isolated: `collect_raw_items()` in `centraldefilamentos/build_data.py` returns successful items plus an `errors` mapping instead of aborting all providers.
- Frontend fetch failures return caller-provided fallback data in `fetchJson()` in `src/lib/shared.js`; use this pattern for optional static JSON reads.

## Logging

**Framework:** console / JSON build logs

**Patterns:**
- Backend build status is modeled as public JSON logs, not Python logging calls; use `write_build_logs()` and quality event payloads in `centraldefilamentos/build_data.py`.
- Business-facing and technical events are split into `public/data/build_business_log.json` and `public/data/build_technical_log.json` by `write_build_logs()` in `centraldefilamentos/build_data.py`.
- The local image curation tool uses `console.log()` for startup messages in `tools/image-curation/server.mjs`; keep console logging localized to tooling.
- Frontend application files under `src/` do not use `console.log`; keep user-facing errors represented in UI state or JSON data rather than browser console output.

## Comments

**When to Comment:**
- Use comments sparingly. Existing implementation modules such as `centraldefilamentos/normalize.py`, `centraldefilamentos/connectors/google_sheet.py`, and `src/lib/shared.js` rely on descriptive names and constants rather than explanatory comments.
- Keep schedule/process comments in configuration files when they clarify external behavior, such as the Argentina business-hour cron note in `.github/workflows/data-capture.yml`.
- Avoid comments that restate code; prefer named helpers like `_repair_mojibake()`, `matchesSearchTerms()`, `thumbnail_url_for()`, and `maybe_update_provider_stock_history()`.

**JSDoc/TSDoc:**
- No JSDoc or TSDoc convention is detected in `src/lib/shared.js`, `src/CatalogApp.svelte`, or `src/components/SiteHeader.svelte`.
- No Python docstring convention is detected in `centraldefilamentos/build_data.py`, `centraldefilamentos/normalize.py`, or `centraldefilamentos/connectors/google_sheet.py`; add focused docstrings only for non-obvious public contracts.

## Function Design

**Size:** Prefer small parser/formatter helpers, but accept larger orchestration functions when they encode build quality policy. Examples: compact helpers in `centraldefilamentos/normalize.py` and `src/lib/shared.js`; larger policy functions in `centraldefilamentos/build_data.py`.

**Parameters:** Pass explicit domain objects and plain mappings instead of hidden globals where tests need control. Examples: `build_payload(..., sources=..., manufacturers=..., generated_at=..., enrichments=...)` in `centraldefilamentos/build_data.py` and `fetch_sheet_items(source, updated_at, timeout_seconds=30)` in `centraldefilamentos/connectors/google_sheet.py`.

**Return Values:** Return plain dataclasses, lists, dictionaries, booleans, or `(items, errors)` tuples. Examples: `normalize_record()` in `centraldefilamentos/normalize.py`, `parse_sheet_csv()` in `centraldefilamentos/connectors/google_sheet.py`, `load_payload()` in `centraldefilamentos/build_data.py`, and `maybe_update_provider_stock_history()` in `centraldefilamentos/build_data.py`.

## Module Design

**Exports:** 
- Python modules export public functions directly from their module files; use imports like `from centraldefilamentos.build_data import build_payload` in tests such as `tests/test_build_data.py`.
- JavaScript utility exports are named exports from `src/lib/shared.js` and `src/lib/stockSubscriptions.js`; import only the helpers a component uses in `src/CatalogApp.svelte` and `src/SummaryApp.svelte`.
- Svelte entry files `src/catalog.js`, `src/summary.js`, and `src/vendor-stats.js` should remain thin mount wrappers around their corresponding app components.

**Barrel Files:**
- No Python or JavaScript barrel file pattern is used. `centraldefilamentos/connectors/__init__.py` is present but direct module imports are used throughout tests such as `tests/test_google_sheet.py` and `tests/test_filamentos3d.py`.
- Add new shared frontend helpers to `src/lib/shared.js` only when they are used by multiple views; otherwise keep view-local logic in `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, or `src/VendorStatsApp.svelte`.

---

*Convention analysis: 2026-06-18*
