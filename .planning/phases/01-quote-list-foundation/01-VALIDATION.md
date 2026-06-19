---
phase: 01
slug: quote-list-foundation
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-06-19
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 local; project declares pytest >=8.2.0 |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest -v tests/test_frontend_assets.py -x --basetemp C:\tmp\pytest-centraldefilamentos` |
| **Full suite command** | `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos` and `npm run build` |
| **Estimated runtime** | focused task checks <30 seconds; full wave/phase gates may take ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run the focused pytest command named in that task's `<verify>` block. Expected feedback latency is <30 seconds.
- **After every plan wave:** Run `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos` and `npm run build`
- **Before `$gsd-verify-work`:** Full suite and Vite build must be green
- **Max feedback latency:** 30 seconds for focused source-invariant task checks; slower `npm run build` and full-suite commands are wave/phase gates, not per-task latency targets

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | LIST-01, LIST-02, ITEM-01, ITEM-02, PERS-01, DISC-01 | T-01-01-01, T-01-01-02 | Source contract rejects cart framing and requires versioned local quote-list persistence | source invariant | `python -m pytest -v tests/test_frontend_assets.py::test_quote_list_source_contract_covers_foundation -x --basetemp C:\tmp\pytest-centraldefilamentos` | ✅ extend existing | ⬜ pending |
| 01-01-02 | 01 | 1 | LIST-01, LIST-02, ITEM-01, ITEM-02, PERS-01, DISC-01 | T-01-01-01, T-01-01-02, T-01-01-04 | Add +1 path uses `product.id`, schema v1 and no-commerce copy | source invariant; build at wave gate | `python -m pytest -v tests/test_frontend_assets.py::test_quote_list_source_contract_covers_foundation -x --basetemp C:\tmp\pytest-centraldefilamentos` | ✅ extend existing | ⬜ pending |
| 01-02-01 | 02 | 2 | LIST-03, LIST-04, LIST-05, ITEM-01, ITEM-02, ITEM-03 | T-01-02-01, T-01-02-02, T-01-02-03 | Quantity, remove, clear and badges are captured before implementation | source invariant | `python -m pytest -v tests/test_frontend_assets.py::test_quote_list_source_contract_covers_foundation -x --basetemp C:\tmp\pytest-centraldefilamentos` | ✅ extend existing | ⬜ pending |
| 01-02-02 | 02 | 2 | LIST-03, LIST-04, LIST-05, ITEM-01, ITEM-02, ITEM-03 | T-01-02-01, T-01-02-02, T-01-02-03, T-01-02-04 | Whole-carrete controls clamp invalid input and destructive clear is confirmed | source invariant; build at wave gate | `python -m pytest -v tests/test_frontend_assets.py::test_quote_list_source_contract_covers_foundation -x --basetemp C:\tmp\pytest-centraldefilamentos` | ✅ extend existing | ⬜ pending |
| 01-03-01 | 03 | 3 | LIST-02, ITEM-03, PERS-01, PERS-02, DISC-01 | T-01-03-01, T-01-03-02, T-01-03-03, T-01-03-04, T-01-03-05 | Responsive surfaces and resilience notices are captured before implementation | source invariant | `python -m pytest -v tests/test_frontend_assets.py::test_quote_list_styles_contract_covers_panel_and_controls -x --basetemp C:\tmp\pytest-centraldefilamentos` | ✅ extend existing | ⬜ pending |
| 01-03-02 | 03 | 3 | LIST-02, ITEM-03, PERS-01, PERS-02, DISC-01 | T-01-03-01, T-01-03-02, T-01-03-03, T-01-03-04, T-01-03-05 | Reconciliation, storage fallback, local-only/no-commerce notices, desktop panel and mobile drawer are verified | focused source invariant; build at phase gate | `python -m pytest -v tests/test_frontend_assets.py -x --basetemp C:\tmp\pytest-centraldefilamentos` | ✅ extend existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test runner, fixtures, backend, browser automation, or generated data edits are required before execution.

---

## Manual-Only Verifications

All phase behaviors have automated source-invariant and build verification. Optional human QA after execution may click through desktop and mobile layouts, but it is not the primary gate for this phase.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s for focused checks
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-19
