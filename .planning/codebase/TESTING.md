# Testing Patterns

**Analysis Date:** 2026-06-18

## Test Framework

**Runner:**
- pytest `>=8.2.0`
- Config: `pyproject.toml`

**Assertion Library:**
- Native Python `assert` statements in pytest tests under `tests/`.
- `pytest.raises` is used for expected exceptions in `tests/test_build_data.py`.

**Run Commands:**
```bash
python -m pytest -v              # Run all tests, as used by .github/workflows/ci.yml
python -m pytest tests/test_normalize.py -v              # Run one test module
python -m pytest -k "build_payload" -v              # Run a focused subset
npm run build              # Build frontend, as used by .github/workflows/ci.yml
```

## Test File Organization

**Location:**
- Tests live in the top-level `tests/` directory, separate from implementation files in `centraldefilamentos/` and `src/`.
- Static parser fixtures live in `tests/fixtures/`, including `tests/fixtures/filamentos3d_stock.html`, `tests/fixtures/google_sheet_stock.csv`, and `tests/fixtures/grilon3_catalog.html`.
- Frontend contract tests are Python tests in `tests/test_frontend_assets.py`; no JavaScript test runner is configured in `package.json`.

**Naming:**
- Test files use `tests/test_*.py`, such as `tests/test_build_data.py`, `tests/test_filamentos3d.py`, `tests/test_grilon3_catalog.py`, and `tests/test_provider_stock_history.py`.
- Test functions use `test_<behavior>`, such as `test_build_payload_groups_products_and_keeps_unknown_stock_visible()` in `tests/test_build_data.py` and `test_parse_sheet_csv_detects_name_stock_and_brand()` in `tests/test_google_sheet.py`.
- Local test data helpers use short domain names, such as `raw()` in `tests/test_normalize.py` and `payload_with_sources()` in `tests/test_provider_stock_history.py`.

**Structure:**
```text
tests/
├── fixtures/
│   ├── filamentos3d_stock.html
│   ├── google_sheet_stock.csv
│   └── grilon3_catalog.html
├── test_build_data.py
├── test_daily_snapshot.py
├── test_filamentos3d.py
├── test_filamentos3d_catalog.py
├── test_frontend_assets.py
├── test_google_sheet.py
├── test_grilon3_catalog.py
├── test_models.py
├── test_normalize.py
├── test_provider_stock_history.py
└── test_providers.py
```

## Test Structure

**Suite Organization:**
```python
from centraldefilamentos.models import RawStockItem
from centraldefilamentos.normalize import build_product_id, normalize_record


def raw(name: str, source_id: str = "filamentos3d", brand_hint: str = "") -> RawStockItem:
    return RawStockItem(
        source_id=source_id,
        provider_name="Proveedor",
        provider_zone="Zona Sur",
        provider_url="https://example.com",
        original_name=name,
        stock_quantity=1,
        source_url="https://example.com/source",
        brand_hint=brand_hint,
        updated_at="2026-05-12T12:00:00-03:00",
    )


def test_product_id_includes_brand_and_format():
    fields = normalize_record(raw("PLA Silk Azul 1kg 1.75mm Grilon3"))

    assert build_product_id(fields) == "pla-pla-silk-azul-175-1000-grilon3"
```

**Patterns:**
- Arrange test inputs inline or through a small helper, then call one public function and assert the exact output, as in `tests/test_normalize.py`, `tests/test_models.py`, and `tests/test_google_sheet.py`.
- Use explicit timestamps, providers, and product names in test data to make payload behavior deterministic, as in `tests/test_build_data.py` and `tests/test_daily_snapshot.py`.
- Prefer exact dictionary/list equality for serialized payload contracts, as in `tests/test_provider_stock_history.py` and `tests/test_daily_snapshot.py`.
- Use fixture files for realistic parser inputs while keeping network access mocked, as in `tests/test_filamentos3d.py`, `tests/test_google_sheet.py`, and `tests/test_grilon3_catalog.py`.

## Mocking

**Framework:** pytest `monkeypatch`

**Patterns:**
```python
def test_fetch_filamentos3d_items_downloads_source_url(monkeypatch):
    calls = []

    class Response:
        text = fixture_html

        def raise_for_status(self):
            calls.append("raise_for_status")

    def fake_get(url, timeout, follow_redirects=True):
        calls.append((url, timeout))
        return Response()

    monkeypatch.setattr("centraldefilamentos.connectors.filamentos3d.httpx.get", fake_get)

    items = fetch_filamentos3d_items(source, updated_at, timeout_seconds=7)

    assert calls == [(source.source_url, 7), "raise_for_status"]
    assert len(items) == 5
```

**What to Mock:**
- Mock HTTP clients at the module path used by the code under test, such as `centraldefilamentos.connectors.filamentos3d.httpx.get`, `centraldefilamentos.connectors.grilon3_catalog.requests.get`, and `centraldefilamentos.cache_grilon3_metadata.requests.get`.
- Mock internal fetch/enrichment functions when testing orchestration and retry behavior, such as `centraldefilamentos.build_data._fetch_source_items`, `centraldefilamentos.connectors.grilon3_catalog.fetch_grilon3_catalog`, and `centraldefilamentos.cache_grilon3_metadata.fetch_grilon3_catalog`.
- Use `tmp_path` for filesystem outputs and cache files in `tests/test_build_data.py`, `tests/test_daily_snapshot.py`, `tests/test_provider_stock_history.py`, and `tests/test_filamentos3d_catalog.py`.

**What NOT to Mock:**
- Do not mock pure parser and normalizer logic; tests call `parse_sheet_csv()`, `parse_filamentos3d_html()`, `parse_filamentos3d_category()`, `parse_grilon3_catalog()`, and `normalize_record()` directly.
- Do not mock serialization on dataclasses in `centraldefilamentos/models.py`; `tests/test_models.py` asserts `to_dict()` contracts directly.
- Do not mock generated public data for asset-contract checks in `tests/test_frontend_assets.py`; it reads `public/data/stock.json` and local asset paths directly.

## Fixtures and Factories

**Test Data:**
```python
def payload_with_sources(generated_at, totals):
    return {
        "generated_at": generated_at,
        "sources": [
            {
                "id": source_id,
                "stats": {
                    "total_stock_units": total,
                    "product_count": 1,
                    "total_stock_kg": float(total),
                    "in_stock_product_count": 1,
                    "out_of_stock_product_count": 0,
                },
            }
            for source_id, total in totals.items()
        ],
    }
```

**Location:**
- Inline helper factories live near the tests that use them, such as `raw()` in `tests/test_build_data.py` and `tests/test_normalize.py`, and `payload_with_sources()` in `tests/test_daily_snapshot.py` and `tests/test_provider_stock_history.py`.
- File fixtures live under `tests/fixtures/`; use them for realistic HTML/CSV samples in parser tests.
- Generated/public fixture-like data lives under `public/data/` and is asserted by `tests/test_frontend_assets.py`.

## Coverage

**Requirements:** None enforced

**View Coverage:**
```bash
Not detected
```

- No `coverage.py`, pytest-cov, coverage threshold, or coverage command is configured in `pyproject.toml`, `package.json`, or `.github/workflows/ci.yml`.
- New risk-heavy backend behavior should get direct pytest coverage in `tests/test_*.py` because CI only enforces test pass/fail and frontend build success.

## Test Types

**Unit Tests:**
- Normalization and ID/display-name behavior in `tests/test_normalize.py` exercises `centraldefilamentos/normalize.py`.
- Dataclass serialization contracts in `tests/test_models.py` exercise `centraldefilamentos/models.py`.
- Provider configuration contracts in `tests/test_providers.py` exercise `centraldefilamentos/providers.py`.

**Integration Tests:**
- Build pipeline behavior in `tests/test_build_data.py` covers grouping, deduplication, source failures, enrichment selection, image metadata, thumbnails, and JSON output across `centraldefilamentos/build_data.py`, `centraldefilamentos/cache_grilon3_metadata.py`, `centraldefilamentos/update_filamentos3d_images.py`, and `centraldefilamentos/thumbnails.py`.
- Parser integration tests in `tests/test_filamentos3d.py`, `tests/test_filamentos3d_catalog.py`, `tests/test_google_sheet.py`, and `tests/test_grilon3_catalog.py` combine realistic fixture HTML/CSV with connector parsing code.
- Frontend/static integration tests in `tests/test_frontend_assets.py` assert that `index.html`, `resumen.html`, `estadisticas.html`, `src/*.svelte`, `src/lib/*.js`, `src/styles/global.css`, and `public/data/stock.json` remain aligned.

**E2E Tests:**
- Not used. No Playwright, Cypress, Selenium, Vitest, Jest, or browser automation config is detected in `package.json`, `vite.config.js`, or the repo root.

## Common Patterns

**Async Testing:**
```python
Not detected
```

- Backend code is synchronous; HTTP calls use `requests` or sync `httpx.get()` in `centraldefilamentos/connectors/google_sheet.py`, `centraldefilamentos/connectors/filamentos3d.py`, and `centraldefilamentos/connectors/grilon3_catalog.py`.
- Frontend async behavior in `src/CatalogApp.svelte`, `src/SummaryApp.svelte`, and `src/VendorStatsApp.svelte` is not tested with a JavaScript async test runner; `tests/test_frontend_assets.py` validates expected source strings instead.

**Error Testing:**
```python
def test_build_payload_rejects_repeated_provider_inside_product_card():
    with pytest.raises(ValueError, match="repeated provider offers"):
        build_payload([...])
```

- Use `pytest.raises(..., match=...)` for expected contract errors, as in `tests/test_build_data.py`.
- Use fake functions that raise `RuntimeError` to exercise partial failure and retry paths, as in `test_collect_raw_items_keeps_fetching_when_one_source_fails()` and `test_collect_raw_items_retries_transient_source_failures()` in `tests/test_build_data.py`.
- Use missing-file cases to assert defensive load behavior, such as `load_daily_provider_stock_snapshot(tmp_path / "missing.json") == {}` in `tests/test_daily_snapshot.py` and `load_provider_stock_history(tmp_path / "missing.json") == {"days": []}` in `tests/test_provider_stock_history.py`.

---

*Testing analysis: 2026-06-18*
