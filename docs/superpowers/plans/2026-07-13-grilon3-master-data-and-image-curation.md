# Grilon3 Master Data and Image Curation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete, auditable Grilon3 master-data scan and a review-gated process for applying official metadata and images.

**Architecture:** Python discovers the active paginated catalog, parses every detail page and writes an ignored draft scan. The existing Node curation UI reviews every official gallery in source order. A separate Python apply command validates scratch reviews, writes a durable selection manifest and updates only approved metadata/assets.

**Tech Stack:** Python 3.12, requests, dataclasses, pytest, Node.js 24 built-ins, plain browser JavaScript, Pillow thumbnails.

## Global Constraints

- Do not crawl Grilon3 detail pages during daily stock capture.
- Do not replace approved metadata or images when a scan is incomplete.
- Use only values published by Grilon3; missing SKU, EAN and Pantone stay empty.
- Use only official gallery images and require an explicit review decision per active product with a gallery.
- Selection priority is `preferred_angle`, then `best_spool`, then `official_primary`.
- Keep scratch scans/reviews under ignored `.image-curation/`; keep approved selections under version control.
- Preserve sampler/3D-pen no-spool-image behavior unless an exact official page is reviewed.
- Run pytest on Windows with `--basetemp C:\tmp\pytest-centraldefilamentos`.

---

### Task 1: Discover the complete active paginated catalog

**Files:**
- Modify: `centraldefilamentos/connectors/grilon3_catalog.py:20-216`
- Modify: `tests/test_grilon3_catalog.py:36-70`

**Interfaces:**
- Produces: `CatalogPage(products: tuple[CatalogProduct, ...], pagination_urls: tuple[str, ...], reported_total: int | None)`.
- Produces: `parse_grilon3_catalog_page(html_text: str, base_url: str) -> CatalogPage`.
- Produces: `fetch_grilon3_active_catalog(products_url: str = BASE_URL, timeout_seconds: int = 30) -> tuple[dict[str, CatalogProduct], int | None]`.

- [ ] **Step 1: Write failing pagination and deduplication tests**

```python
def test_parse_grilon3_catalog_page_returns_pagination_and_reported_total():
    page = parse_grilon3_catalog_page(
        '<p class="woocommerce-result-count">Mostrando 1–12 de 167 resultados</p>'
        '<a class="page-numbers" href="https://grilon3.com.ar/productos/page/2/">2</a>'
        '<a href="https://grilon3.com.ar/producto/pla-negro/"><img alt="PLA Negro" src="negro.jpg"></a>',
        "https://grilon3.com.ar/productos/",
    )
    assert page.reported_total == 167
    assert page.pagination_urls == ("https://grilon3.com.ar/productos/page/2/",)
    assert [product.product_url for product in page.products] == ["https://grilon3.com.ar/producto/pla-negro/"]


def test_fetch_grilon3_active_catalog_deduplicates_canonical_urls(monkeypatch):
    responses = {
        BASE_URL: FIRST_PAGE_WITH_PAGE_2,
        f"{BASE_URL}page/2/": SECOND_PAGE_REPEATING_PLA_NEGRO,
    }
    monkeypatch.setattr(requests, "get", lambda url, timeout: FakeResponse(responses[url]))
    catalog, total = fetch_grilon3_active_catalog()
    assert total == 2
    assert len({product.product_url for product in catalog.values()}) == 2
```

- [ ] **Step 2: Run the focused tests and confirm failure**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_grilon3_catalog.py -k "pagination or active_catalog"`

Expected: FAIL because `CatalogPage`, `parse_grilon3_catalog_page` and `fetch_grilon3_active_catalog` do not exist.

- [ ] **Step 3: Add the page model and complete traversal**

```python
@dataclass(frozen=True)
class CatalogPage:
    products: tuple[CatalogProduct, ...]
    pagination_urls: tuple[str, ...]
    reported_total: int | None


def fetch_grilon3_active_catalog(products_url: str = BASE_URL, timeout_seconds: int = 30):
    first_response = requests.get(products_url, timeout=timeout_seconds)
    first_response.raise_for_status()
    first_page = parse_grilon3_catalog_page(first_response.text, products_url)
    pages = [first_page]
    for page_url in first_page.pagination_urls:
        response = requests.get(page_url, timeout=timeout_seconds)
        response.raise_for_status()
        pages.append(parse_grilon3_catalog_page(response.text, page_url))
    by_url = {}
    for page in pages:
        for product in page.products:
            by_url.setdefault(product.product_url.rstrip("/") + "/", product)
    catalog = {}
    for product in by_url.values():
        catalog[_unique_catalog_key(catalog, product.product_id, product.product_url)] = product
    return catalog, first_page.reported_total
```

Implement `parse_grilon3_catalog_page()` by reusing `_ProductLinkParser`, extracting every `a.page-numbers` URL and parsing `de N resultados`. Keep `parse_grilon3_catalog()` as a compatibility wrapper returning the page products keyed by normalized ID.

- [ ] **Step 4: Run all connector tests**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_grilon3_catalog.py`

Expected: PASS.

- [ ] **Step 5: Commit the catalog discovery slice**

```powershell
git add centraldefilamentos/connectors/grilon3_catalog.py tests/test_grilon3_catalog.py
git commit -m "feat: crawl complete Grilon3 catalog"
```

### Task 2: Preserve ordered galleries and robust official fields

**Files:**
- Modify: `centraldefilamentos/connectors/grilon3_catalog.py:20-145,292-443`
- Modify: `tests/test_grilon3_catalog.py:90-215`
- Modify: `tests/fixtures/grilon3_catalog.html`

**Interfaces:**
- Produces: `CatalogProductDetail(product_url, category_path, gallery_image_urls, pantone, sku, ean)`.
- Changes: `fetch_grilon3_product_detail(...) -> CatalogProductDetail`.
- Changes: `parse_grilon3_product_detail(...) -> CatalogProductDetail`.

- [ ] **Step 1: Write failing ordered-gallery and fallback tests**

```python
def test_product_detail_keeps_original_gallery_order_and_structured_gtin():
    detail = parse_grilon3_product_detail(PRODUCT_WITH_FOUR_IMAGES_AND_JSON_LD, "https://grilon3.com.ar/producto/abs-amarillo/")
    assert detail.gallery_image_urls == (
        "https://grilon3.com.ar/uploads/boxed.jpg",
        "https://grilon3.com.ar/uploads/spool-angle.jpg",
        "https://grilon3.com.ar/uploads/spool-front.jpg",
        "https://grilon3.com.ar/uploads/range.jpg",
    )
    assert detail.sku == "M09IAM175CJ"
    assert detail.ean == "7798049653051"
    assert detail.pantone == "Pantone Yellow"
    assert detail.category_path == ("Básicos", "ABS")


def test_product_detail_leaves_unpublished_fields_empty():
    detail = parse_grilon3_product_detail(PRODUCT_WITHOUT_CODES_OR_PANTONE)
    assert (detail.sku, detail.ean, detail.pantone) == ("", "", "")
```

- [ ] **Step 2: Run the focused detail tests**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_grilon3_catalog.py -k "detail"`

Expected: FAIL because details currently return a string dictionary and score a single image.

- [ ] **Step 3: Introduce the immutable detail contract**

```python
@dataclass(frozen=True)
class CatalogProductDetail:
    product_url: str
    category_path: tuple[str, ...]
    gallery_image_urls: tuple[str, ...]
    pantone: str = ""
    sku: str = ""
    ean: str = ""

    @property
    def primary_image_url(self) -> str:
        return self.gallery_image_urls[0] if self.gallery_image_urls else ""
```

Update `_ProductDetailParser` to append original `data-large_image` URLs only while inside `.woocommerce-product-gallery`, deduplicate without sorting, and collect breadcrumb labels. Parse `.sku`, `.ean`, JSON-LD `sku`/`gtin13` and visible text in that precedence order. Remove `_preferred_product_image()` from the detail selection path; callers use `primary_image_url` only as a non-reviewed compatibility fallback.

- [ ] **Step 4: Update enrichment callers and run connector/build tests**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_grilon3_catalog.py tests/test_build_data.py -k "grilon3"`

Expected: PASS.

- [ ] **Step 5: Commit ordered detail extraction**

```powershell
git add centraldefilamentos/connectors/grilon3_catalog.py tests/test_grilon3_catalog.py tests/fixtures/grilon3_catalog.html
git commit -m "feat: preserve Grilon3 official galleries and codes"
```

### Task 3: Produce an auditable draft scan without touching production

**Files:**
- Create: `centraldefilamentos/grilon3_scan.py`
- Create: `tests/test_grilon3_scan.py`
- Modify: `centraldefilamentos/cache_grilon3_metadata.py:26-73,182-210`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `scan_grilon3_catalog(...) -> dict[str, object]`.
- Produces: `write_grilon3_scan(payload, output_path=".image-curation/grilon3-scan.json") -> None`.
- CLI: `python -m centraldefilamentos.grilon3_scan --output .image-curation/grilon3-scan.json`.

- [ ] **Step 1: Write failing scan audit tests**

```python
def test_scan_reports_count_errors_and_sitemap_only_urls(monkeypatch):
    monkeypatch.setattr(scan, "fetch_grilon3_active_catalog", lambda *args, **kwargs: (ACTIVE, 2))
    monkeypatch.setattr(scan, "fetch_grilon3_sitemap_catalog", lambda *args, **kwargs: SITEMAP_WITH_LEGACY)
    monkeypatch.setattr(scan, "enrich_grilon3_catalog_details", lambda products, **kwargs: ENRICHED)
    payload = scan_grilon3_catalog()
    assert payload["summary"]["active_count"] == 2
    assert payload["summary"]["reported_total"] == 2
    assert payload["sitemap_only"] == [{"url": LEGACY_URL, "classification": "unclassified"}]
    assert payload["complete"] is False


def test_write_scan_only_writes_requested_draft(tmp_path):
    output = tmp_path / "scan.json"
    write_grilon3_scan(COMPLETE_SCAN, output)
    assert json.loads(output.read_text(encoding="utf-8"))["complete"] is True
```

- [ ] **Step 2: Run the new test module**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_grilon3_scan.py`

Expected: FAIL because the scan module is absent.

- [ ] **Step 3: Implement the JSON draft and audit summary**

Each product JSON object must contain `product_id`, `title`, `product_url`, `category_path`, ordered `gallery_image_urls`, `gallery_fingerprint`, normalized fields, `sku`, `ean`, `pantone` and `warnings`. Compute the fingerprint from newline-joined gallery URLs with SHA-256. Set `complete` only when reported and discovered counts match, all detail requests succeeded and every sitemap-only URL has a non-`unclassified` classification.

Make `cache_grilon3_metadata.py` print a deprecation message directing full refreshes to the scan/curate/apply workflow; retain `--images-only` compatibility without making it the new path.

- [ ] **Step 4: Verify scan tests and gitignore behavior**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_grilon3_scan.py tests/test_build_data.py -k "grilon3"`

Expected: PASS, and `git check-ignore .image-curation/grilon3-scan.json` prints that path.

- [ ] **Step 5: Commit the safe scan**

```powershell
git add .gitignore centraldefilamentos/grilon3_scan.py centraldefilamentos/cache_grilon3_metadata.py tests/test_grilon3_scan.py
git commit -m "feat: add auditable Grilon3 draft scan"
```

### Task 4: Review every official gallery in the local curator

**Files:**
- Modify: `tools/image-curation/server.mjs:7-142,337-431`
- Modify: `tools/image-curation/app.js:27-360`
- Modify: `tools/image-curation/index.html`
- Modify: `tools/image-curation/styles.css`
- Create: `tests/imageCuration.test.js`
- Modify: `package.json`

**Interfaces:**
- GET `/api/products` reads `.image-curation/grilon3-scan.json` and returns all active draft products.
- POST `/api/review` stores `{product_url, selected_image_remote_url, selection_reason, gallery_fingerprint, reviewed_at}` in scratch `selections.json`.
- Produces exported pure functions `draftProducts(payload)`, `validateReview(product, review)` and `reviewStatus(product, review)` for Node tests.

- [ ] **Step 1: Add failing Node tests for draft loading and stale reviews**

```javascript
test("review must select an image from the official ordered gallery", () => {
  assert.throws(() => validateReview(PRODUCT, {
    selected_image_remote_url: "https://example.com/not-official.jpg",
    selection_reason: "preferred_angle",
  }), /official gallery/);
});

test("changed gallery fingerprints mark reviews stale", () => {
  assert.equal(reviewStatus({ gallery_fingerprint: "sha256:new" }, { gallery_fingerprint: "sha256:old" }), "stale");
});
```

- [ ] **Step 2: Add the test script and verify failure**

Add `tests/imageCuration.test.js` to `test:quote-list` or rename the script to `test:frontend` and keep `test:quote-list` as an alias. Run: `npm run test:quote-list`.

Expected: FAIL because the pure exports and draft contract do not exist.

- [ ] **Step 3: Replace ranked top-three candidates with the ordered draft gallery**

Render every `gallery_image_urls` item. Add three explicit selection buttons per candidate: `45° sin caja`, `Mejor carrete`, `Foto principal`. Store the corresponding reason enum. Keep the current image beside the candidates and show filters for `pending`, `reviewed`, `stale` and `without-gallery`.

- [ ] **Step 4: Run Node tests and a local smoke check**

Run: `npm run test:quote-list`.

Expected: PASS.

Run: `npm run curate-images`, open `http://127.0.0.1:4177`, and verify an Astra, Silk and ABS page preserve official gallery order and save the chosen reason.

- [ ] **Step 5: Commit the review UI**

```powershell
git add package.json tools/image-curation tests/imageCuration.test.js
git commit -m "feat: review complete Grilon3 galleries"
```

### Task 5: Apply only reviewed metadata and images

**Files:**
- Create: `centraldefilamentos/apply_grilon3_curation.py`
- Create: `centraldefilamentos/data/grilon3_image_selections.json`
- Create: `tests/test_grilon3_curation.py`
- Modify: `centraldefilamentos/build_data.py:624-643`
- Modify: `centraldefilamentos/cache_grilon3_metadata.py:96-150`

**Interfaces:**
- Produces: `build_apply_plan(scan, reviews, existing_selections, existing_metadata) -> dict[str, object]`.
- Produces: `apply_grilon3_plan(plan, *, apply: bool, metadata_path, selections_path, assets_dir) -> dict[str, object]`.
- CLI defaults to dry run; `--apply` performs writes.

- [ ] **Step 1: Write failing validation and dry-run tests**

```python
def test_apply_plan_refuses_incomplete_scan():
    with pytest.raises(ValueError, match="scan is incomplete"):
        build_apply_plan({**SCAN, "complete": False}, REVIEWS, {}, {})


def test_apply_plan_requires_review_for_every_gallery_product():
    with pytest.raises(ValueError, match="pending image reviews"):
        build_apply_plan(SCAN_WITH_TWO_GALLERIES, {FIRST_URL: REVIEW}, {}, {})


def test_dry_run_does_not_write_files(tmp_path):
    report = apply_grilon3_plan(PLAN, apply=False, metadata_path=tmp_path / "metadata.json", selections_path=tmp_path / "selections.json", assets_dir=tmp_path / "assets")
    assert report["mode"] == "dry-run"
    assert list(tmp_path.iterdir()) == []
```

- [ ] **Step 2: Run curation tests and verify failure**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_grilon3_curation.py`

Expected: FAIL because the apply module does not exist.

- [ ] **Step 3: Implement plan validation and selective writes**

Use canonical product URL keys. Reject incomplete scans, missing/stale reviews, selections outside the gallery and unknown reason enums. Merge SKU/EAN/Pantone even when empty only from the current official draft, but retain the previous approved image until its replacement download and thumbnail succeed. Write JSON through a temporary sibling and `Path.replace()` only after all downloads succeed.

- [ ] **Step 4: Run curation, build-data and thumbnail tests**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_grilon3_curation.py tests/test_build_data.py -k "grilon3 or thumbnail"`

Expected: PASS.

- [ ] **Step 5: Commit the apply workflow**

```powershell
git add centraldefilamentos/apply_grilon3_curation.py centraldefilamentos/cache_grilon3_metadata.py centraldefilamentos/build_data.py centraldefilamentos/data/grilon3_image_selections.json tests/test_grilon3_curation.py
git commit -m "feat: apply reviewed Grilon3 metadata"
```

### Task 6: Complete the initial live audit and document operations

**Files:**
- Modify: `README.md:67-100,129-133`
- Modify: `docs/image-curation.md`
- Generated after approved review: `centraldefilamentos/data/grilon3_metadata.json`
- Generated after approved review: `public/assets/grilon3/**`
- Generated after approved review: `public/assets/thumbs/**`

**Interfaces:**
- Consumes the scan and apply CLIs from Tasks 3 and 5.
- Produces a complete local draft and a reviewed, versioned metadata/image refresh.

- [ ] **Step 1: Run the live draft scan**

Run: `python -m centraldefilamentos.grilon3_scan --output .image-curation/grilon3-scan.json --timeout-seconds 12 --max-workers 16`.

Expected: exit 0 only when active count matches the reported listing count, all details were attempted, and sitemap-only URLs are classified.

- [ ] **Step 2: Review every gallery and inspect missing-field reports**

Run `npm run curate-images`. Review all `pending` and `stale` records. Confirm the final UI counters show zero pending/stale products with galleries. Inspect missing SKU/EAN/Pantone URLs; confirm they are truly absent from the official page rather than parser failures.

- [ ] **Step 3: Dry-run and apply the approved refresh**

Run: `python -m centraldefilamentos.apply_grilon3_curation --scan .image-curation/grilon3-scan.json --reviews .image-curation/selections.json`.

Expected: dry-run report lists exact metadata/image changes and zero validation errors.

Run the same command with `--apply` only after reviewing the report.

- [ ] **Step 4: Run the complete backend suite**

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos`.

Expected: PASS.

- [ ] **Step 5: Document and commit the reviewed refresh separately**

```powershell
git add README.md docs/image-curation.md centraldefilamentos/data/grilon3_metadata.json centraldefilamentos/data/grilon3_image_selections.json public/assets/grilon3 public/assets/thumbs
git commit -m "data: refresh reviewed Grilon3 master catalog"
```

Verify `git status --short` still shows only pre-existing unrelated user changes.
