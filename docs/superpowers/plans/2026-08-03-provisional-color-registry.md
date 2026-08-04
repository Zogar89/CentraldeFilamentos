# Provisional Color Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Keep the existing worktree and draft PR #3; do not create a stacked branch.

**Goal:** Let an unseen supplier color publish safely with a durable provisional state, a stable product identity, and an explicit catalog badge, so it cannot collapse into `Sin color` and trigger the repeated-provider-offer failure again.

**Architecture:** Keep `COLOR_RULES` as the canonical path for reviewed colors. Add a versioned, internal `color_registry.json` plus a small Python domain module that validates it, derives a safe candidate from an unrecognized source title, and records provenance. `build_data` resolves that candidate before `build_product_id()` and grouping; it only persists registry changes after the existing quality gate permits publication. The public payload gets an optional `color_review_status` and the catalog renders a compact, non-visual badge from it.

**Tech Stack:** Python 3.12 dataclasses/pytest, Svelte 5, plain JavaScript, Vite 8, GitHub Actions.

## Global Constraints

- Do not replace, reorder, or weaken the explicit `COLOR_RULES` mapping.
- Keep `_validate_unique_provider_offers()` as the final integrity guard; prevent its false collision rather than suppressing it.
- Do not infer Pantone, RGB, image metadata, visual similarity, or an alias to an established color.
- Treat the provider title as an auditable supplier label, not proof of a physical color.
- PVA is explicitly color-optional. It remains `Sin color`, never opens a candidate, and preserves its current behavior.
- Registry state stays under `centraldefilamentos/data/`, is committed by Capture Stock Data, and is never copied to `gh-pages`.
- Public readers remain backward-compatible: only provisional products emit `color_review_status`; established products keep the current JSON shape.
- Do not change quote-list semantics, filtering behavior, supplier URLs, stock language, product swatches, or localStorage keys.
- Run Python tests on Windows with `--basetemp C:\tmp\pytest-centraldefilamentos`.
- Do not stage, commit, push, or merge implementation changes without fresh authorization.

---

### Task 1: Add validated durable color-registry state

**Files:**

- Create: `centraldefilamentos/color_registry.py`
- Create: `centraldefilamentos/data/color_registry.json`
- Create: `tests/test_color_registry.py`
- Modify: `centraldefilamentos/connectors/grilon3_catalog.py`

**Interfaces:**

- Produces `ColorRegistry`, `ColorCandidate`, and `ColorResolution` value objects.
- Produces `load_color_registry(path: str | Path) -> ColorRegistry` and `write_color_registry(registry: ColorRegistry, path: str | Path) -> None`.
- Produces `resolve_provisional_color(item: RawStockItem, fields: NormalizedFields, registry: ColorRegistry, observed_at: str) -> ColorResolution | None`.
- Exposes one shared `COLOR_OPTIONAL_MATERIALS = frozenset({"PVA"})` rule so catalog enrichment and stock capture cannot disagree.
- Initializes the tracked file to `{ "version": 1, "candidates": {} }` with stable JSON formatting.

`PAPAYA` and `ALUMINIO` are already canonical rules in this PR's first fix. Use synthetic labels absent from `COLOR_RULES` (`CASCADA` and `ZIRCONIA`) for the new provisional-path tests; retain Papaya/Aluminio only as known-color regression inputs.

- [ ] **Step 1: Write registry validation and deterministic-resolution tests**

Cover these contracts before implementing the module:

```python
def test_registry_round_trip_is_sorted_and_keeps_provenance(tmp_path):
    registry = ColorRegistry.empty()
    item = raw("grupo_senz", "3N3 SILK CASCADA 1.75 MM X 1 KG")
    result = resolve_provisional_color(
        item,
        normalize_record(item),
        registry,
        "2026-08-03T14:11:26-03:00",
    )

    write_color_registry(registry, tmp_path / "colors.json")
    loaded = load_color_registry(tmp_path / "colors.json")

    assert result.display_color == "Cascada"
    assert result.key == "grupo_senz|3n3|pla-silk|cascada"
    assert loaded.candidates[result.key].examples == ["3N3 SILK CASCADA 1.75 MM X 1 KG"]
```

Add focused failures for malformed JSON, duplicate object keys, bad version, blank candidate key/display label, invalid/missing provenance, malformed timestamps, non-list or duplicate examples, and unknown `status`. Confirm a missing registry file yields an empty in-memory registry so the first production capture can create it.

- [ ] **Step 2: Run the focused registry test and confirm it fails**

Run:

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_color_registry.py
```

Expected: FAIL because the color-registry module does not yet exist.

- [ ] **Step 3: Implement the typed registry, safe candidate extractor, and stable writer**

Implement these rules in `color_registry.py`:

1. Parse JSON with an `object_pairs_hook` that rejects duplicate keys, validate version `1`, validate every candidate fully, and raise an actionable `ValueError` naming the candidate key.
2. Keep candidate keys immutable and shaped as `source_id|brand_slug|variant_slug|candidate_slug`. Fold accents/case and normalize separators deterministically.
3. Derive `candidate_slug`/`display_color` by removing recognizable brand, material/variant, diameter, weight, and presentation tokens from the supplier title. `3N3 SILK CASCADA 1.75 MM X 1 KG` yields `Cascada`; a paired `ZIRCONIA` title yields `Zirconia`.
4. If the phrase is empty or unsafe, generate a deterministic source-title fallback key and a readable source-title display label. Never return `Sin color` for a non-optional raw item just because extraction was imperfect.
5. On repeat observation, preserve first display label/key, refresh only `last_seen_at`, and keep a de-duplicated bounded list of original-title examples.
6. `approved` retains key/display label but resolves without a pending state; `provisional` resolves with the pending state.
7. Use the supplied `observed_at` rather than the clock, so tests and generated state are deterministic.
8. Move `COLOR_OPTIONAL_MATERIALS` from `connectors/grilon3_catalog.py` to this shared module (or equally neutral shared module), import it back there, and do not broaden PVA in this change.

Write JSON as UTF-8 with `ensure_ascii=False`, `indent=2`, sorted keys, and a trailing newline.

- [ ] **Step 4: Verify all registry paths**

Run:

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_color_registry.py tests/test_grilon3_catalog.py
```

Expected: PASS. Inspect the serialized state to confirm no hex, Pantone, image, or alias field was introduced.

### Task 2: Resolve provisional color identity before grouping and serialize it additively

**Files:**

- Modify: `centraldefilamentos/models.py:54-92`
- Modify: `centraldefilamentos/build_data.py:62-138,962-1021`
- Modify: `tests/test_models.py`
- Modify: `tests/test_build_data.py`

**Interfaces:**

- `ProductGroup` gains `color_review_status: Literal["", "provisional"] = ""` after `offers`, retaining compatibility for existing constructors.
- `ProductGroup.to_dict()` omits `color_review_status` unless it is `"provisional"`.
- `build_payload` gains an optional `color_registry: ColorRegistry | None = None` parameter and observes new candidates before `build_product_id()`.
- Group state preserves the resolution status and passes it to `_product_from_group()`; catalog-only official products retain empty status.

- [ ] **Step 1: Add failing product-payload regressions for the original failure class**

Add tests beside the existing duplicate-provider regression:

```python
def test_build_payload_keeps_two_unseen_supplier_colors_as_distinct_provisional_products():
    registry = ColorRegistry.empty()
    payload = build_payload(
        [
            raw("grupo_senz", "Grupo Senz", "Zona Oeste", "3N3 SILK CASCADA 1.75 MM X 1 KG", 2, "3N3"),
            raw("grupo_senz", "Grupo Senz", "Zona Oeste", "3N3 SILK ZIRCONIA 1.75 MM X 1 KG", 3, "3N3"),
        ],
        generated_at="2026-08-03T14:11:26-03:00",
        color_registry=registry,
    )

    assert {(product["color"], product["color_review_status"]) for product in payload["products"]} == {
        ("Cascada", "provisional"),
        ("Zirconia", "provisional"),
    }
    assert all(len(product["offers"]) == 1 for product in payload["products"])
```

Also prove that a known `COLOR_RULES` match preserves its ID/no candidate, PVA stays `Sin color`/no candidate, repeated observation preserves key/examples, an approved candidate omits the public pending field, and the existing genuine-duplicate test still raises.

In `tests/test_models.py`, assert blank status is absent from JSON and `"provisional"` is present only when set.

- [ ] **Step 2: Run the focused payload/model suite and confirm it fails**

Run:

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_models.py tests/test_build_data.py -k "provisional or repeated_provider or colorless"
```

Expected: FAIL because `build_payload()` has no registry parameter and product serialization has no optional review state.

- [ ] **Step 3: Apply registry resolution before product identity is built**

In the raw-item loop in `build_payload()`:

1. Normalize through the existing `normalize_record()` path.
2. Leave known colors unchanged.
3. Leave colorless PVA unchanged and do not observe it.
4. Otherwise call `resolve_provisional_color()` with raw item, normalized fields, mutable registry, and the build's `generated_at`.
5. Use `dataclasses.replace(fields, color=resolution.display_color)` only for grouping, display name, and `build_product_id()`. Preserve `Offer.original_name` untouched as provider evidence.
6. Store `resolution.review_status` with the group; identical resolution must not downgrade an approved group to provisional.

Thread status into `_product_from_group()`. Preserve enrichment lookup, sort order, `color_estimates`, material appearance, and `_validate_unique_provider_offers()` exactly. Do not give a provisional item a visual estimate merely because it has a supplier label.

- [ ] **Step 4: Run the backend regression suite**

Run:

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_models.py tests/test_build_data.py tests/test_frontend_assets.py -k "provisional or repeated_provider or without_color or generated_stock_data"
```

Expected: PASS, including the original repeated-provider guard and generated-data invariant for stocked `Sin color` products.

### Task 3: Persist only a publishable registry update and surface non-blocking observability

**Files:**

- Modify: `centraldefilamentos/build_data.py:164-320,874-925`
- Modify: `tests/test_build_data.py`

**Interfaces:**

- Add CLI argument `--color-registry`, default `centraldefilamentos/data/color_registry.json`.
- Load/validate state before public-payload construction.
- Add a small `persist_publishable_build` helper that receives the payload, all output paths, current registry, and quality report, so tests prove registry output is only written after `quality_report["should_publish"]` is true.
- Extend `evaluate_build_quality` with optional `provisional_color_keys: Iterable[str] = ()`, emitting a non-blocking warning only when provisional keys were observed.

- [ ] **Step 1: Add failing transaction/observability tests**

Cover outcome rather than implementation detail:

```python
def test_provisional_color_warning_is_visible_but_does_not_block_publication():
    report = evaluate_build_quality(
        build_payload([], generated_at="2026-08-03T14:11:26-03:00"),
        provisional_color_keys=["grupo_senz|3n3|pla-silk|cascada"],
    )

    assert report["should_publish"] is True
    assert any(event["code"] == "provisional_colors" for event in report["technical_events"])
    assert any(event["level"] == "warning" for event in report["business_events"])


```

Add a second test that invokes the actual `persist_publishable_build` helper with temporary stock, registry, snapshot, and history paths plus a valid payload/report. Assert that the `should_publish=False` branch creates no registry path, while the successful branch writes the Cascada candidate. Also verify that `write_build_logs()` preserves warnings in the correct business/technical outputs.

- [ ] **Step 2: Run focused quality/output tests and confirm failure**

Run:

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_build_data.py -k "provisional or write_build_logs or quality"
```

Expected: FAIL on the new registry transaction and warning assertions.

- [ ] **Step 3: Wire registry into the trusted build lifecycle**

Implement this strict order in `main()`:

1. Parse `--color-registry` and load/validate state.
2. Collect sources/enrichments as today and call `build_payload` with the loaded registry.
3. Pass sorted provisional candidate keys observed in this build to `evaluate_build_quality()`.
4. Write business/technical logs regardless of publication outcome, as today.
5. If quality blocks publication, return without writing registry, snapshots, history, or `stock.json`.
6. If it succeeds, write registry in the same post-gate phase as snapshots/history/public JSON.

Add `provisional_colors` warning events. The technical one includes sorted candidate keys/count; the business one says only that supplier-labeled colors were incorporated pending normalization. It must not claim visual verification or confirmed stock.

- [ ] **Step 4: Verify lifecycle and logging behavior**

Run:

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_build_data.py
```

Expected: PASS. Confirm a blocked temporary build writes no registry and a successful one writes it after quality evaluation.

### Task 4: Render the provisional supplier-color badge in the actual catalog explorer

**Files:**

- Modify: `src/components/CatalogExplorerResults.svelte:52-56`
- Modify: `src/styles/global.css:4613-4636` and responsive rules if needed
- Modify: `tests/test_frontend_assets.py:207-270,358-366`

**Interfaces:**

- `CatalogExplorerResults.svelte` renders `Color del proveedor · pendiente de normalizar` only when `product.color_review_status === "provisional"`.
- The badge is a compact identity detail, uses the existing responsive grid column, truncates safely, and does not invent a visual value.

- [ ] **Step 1: Add a failing frontend source-contract test**

Assert all of:

```python
assert 'product.color_review_status === "provisional"' in results
assert "Color del proveedor · pendiente de normalizar" in results
assert "catalog-explorer-provisional-color" in results
assert ".catalog-explorer-provisional-color" in css
```

Also preserve the existing image-missing grid contract; the badge must not rearrange image/swatch columns.

- [ ] **Step 2: Run focused frontend test and confirm failure**

Run:

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_frontend_assets.py -k "catalog_result_identity or provisional"
```

Expected: FAIL because neither component nor CSS recognizes the optional field.

- [ ] **Step 3: Add conditional badge and restrained styling**

Render it below the normalized color and before the existing brand/line metadata. Add a dedicated CSS class using muted compact type with a clear warning accent that remains legible at 520px. Preserve overflow ellipsis and the three-column identity layout. Do not add a tooltip that overstates certainty, or a badge to quote items/provider stock cells.

- [ ] **Step 4: Verify UI contract and production build**

Run:

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos tests/test_frontend_assets.py
npm.cmd run build
```

Expected: both PASS. If a local provisional fixture is available, inspect desktop/mobile explorer output; otherwise retain a source-contract assertion rather than fabricating public data.

### Task 5: Commit generated state to Capture, document review, and verify end-to-end

**Files:**

- Modify: `.github/workflows/data-capture.yml:44-86`
- Modify: `docs/publishing-workflows.md:19-45,108-114`
- Modify: `README.md:123-131` if its quality-gate section is clearer
- Generated/created: `centraldefilamentos/data/color_registry.json`
- Modify: workflow-contract test in `tests/test_frontend_assets.py` or a dedicated test
- Modify: `docs/superpowers/specs/2026-08-03-provisional-color-registry-design.md` only to correct stale component naming/literal badge text if needed

**Interfaces:**

- Capture stages `centraldefilamentos/data/color_registry.json` with other internal durable state.
- The existing `cp public/data/*.json "$pages_dir/data/"` remains the only data publication step; registry never copies to `gh-pages`.
- Operators may change only a reviewed candidate's `status` from `provisional` to `approved`; keys and identities are immutable.

- [ ] **Step 1: Add failing workflow/documentation contract test**

Assert Capture includes registry in `DATA_FILES`, while the gh-pages copy source remains `public/data/*.json` and not `centraldefilamentos/data/`. Add documentation assertions only where they protect a real operational contract.

- [ ] **Step 2: Update workflow and operator guidance**

Add registry JSON to `DATA_FILES`, not the public copy step. Document this review flow:

1. Open the internal registry diff and technical log after a successful capture.
2. Confirm actual provider title and decide whether it is a supplier label or merits a separately reviewed canonical rule.
3. If the label itself is accepted but no canonical merge is authorized, change only `status` to `approved`; its stable ID remains and the pending badge disappears on the next capture.
4. Add a `COLOR_RULES` alias only in a separately reviewed normalization change that explicitly handles identity migration; never auto-merge here.

Confirm the design document continues to name `CatalogExplorerResults.svelte` and uses the UTF-8 `·` label; those documentation corrections were made during plan review.

- [ ] **Step 3: Regenerate through normal pipeline and inspect output scope**

Run:

```powershell
python -m centraldefilamentos.build_data --output public/data/stock.json
```

Expected: successful quality gate. Inspect `git status` and logs before staging. The initial empty registry remains empty until an unknown color is actually seen. Do not stage unrelated timestamp, history, source-data, image, or user-worktree drift from live inputs.

- [ ] **Step 4: Run complete verification matrix**

Run:

```powershell
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos
npm.cmd run test:quote-list
npm.cmd run build
```

Expected: all PASS. Recheck PVA genuinely colorless, known Papaya/Aluminio create no candidates, unknown Cascada/Zirconia stay separate, and the unchanged duplicate-offer validator catches a real duplicate.

- [ ] **Step 5: Prepare a reviewable same-PR change set**

Before any user-authorized Git operation, inspect the exact diff against `origin/master` and separate only intended registry/module/tests, build/model/UI/workflow/docs, and legitimate generated outputs. Keep `7d17d58 fix: normalize Grupo Senz silk colors` intact. Once explicitly authorized, stage/commit/push to `codex/fix-grupo-senz-silk-colors` so it updates draft PR #3; do not merge.
