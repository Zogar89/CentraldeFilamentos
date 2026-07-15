# Integrate Local UI With Current Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the currently approved local interface while retaining the current remote catalog, improved product photos, thumbnails, color estimates, finishes, and 320x320 material swatches.

**Architecture:** Treat `origin/master` as the authoritative data and asset layer. Replay only the tracked local UI delta onto a clean branch based on `origin/master`; never copy the stale local `public/data/stock.json` or local assets. Resolve integration conflicts in favor of the local interaction/layout contract and the remote static-data contract.

**Tech Stack:** Svelte 5, Vite 8, JavaScript ES modules, CSS, Python 3.12+, pytest, GitHub Actions, GitHub Pages.

## Global Constraints

- Preserve the 11 tracked local UI changes and exclude untracked planning, cache, attachment, and review artifacts.
- Keep `public/data/stock.json` and `public/assets/**` from current `origin/master`.
- Keep Pantone products free of estimated-color fields.
- Keep all referenced material swatches on renderer v2 at 320x320 pixels.
- Run Windows tests with a writable `C:\tmp` pytest base directory.
- Review the integrated interface in Chrome before publication.

---

### Task 1: Replay the tracked local UI delta

**Files:**
- Modify: `index.html`
- Delete: `src/CatalogApp.svelte`
- Delete: `src/catalog.js`
- Modify: `src/SummaryApp.svelte`
- Modify: `src/components/QuoteListItem.svelte`
- Modify: `src/components/SiteHeader.svelte`
- Modify: `src/lib/quoteList.js`
- Modify: `src/lib/shared.js`
- Modify: `src/styles/global.css`
- Modify: `tests/test_frontend_assets.py`
- Modify: `vite.config.js`

**Interfaces:**
- Consumes: tracked working-tree diff from the main checkout at `C:\Users\Gabriel\Documents\GitHub\StockCentral`.
- Produces: the same local UI behavior on top of current `origin/master` data and assets.

- [ ] **Step 1: Export only the tracked UI paths**

Run `git diff --binary -- index.html src/CatalogApp.svelte src/SummaryApp.svelte src/catalog.js src/components/QuoteListItem.svelte src/components/SiteHeader.svelte src/lib/quoteList.js src/lib/shared.js src/styles/global.css tests/test_frontend_assets.py vite.config.js` from the main checkout and capture it as a temporary patch outside the repository.

- [ ] **Step 2: Apply the patch in the isolated worktree**

Run `git apply --3way <patch-file>` from `.worktrees/integrate-local-ui`. If a conflict occurs, compare the local UI file with `origin/master` and keep the local layout/interaction plus the remote material-swatch support.

- [ ] **Step 3: Verify scope**

Run `git status --short` and confirm that only the eleven listed paths plus this plan are changed; `public/data/stock.json` and `public/assets/**` must remain clean.

### Task 2: Verify data and interface contracts

**Files:**
- Test: `tests/test_frontend_assets.py`
- Verify: `public/data/stock.json`
- Verify: `public/assets/material-swatches/*.webp`

**Interfaces:**
- Consumes: integrated Svelte UI and the remote catalog payload.
- Produces: a build that renders current photos and v2 material swatches through the local UI.

- [ ] **Step 1: Run frontend contract tests**

Run `python -m pytest -q tests/test_frontend_assets.py -p no:cacheprovider --basetemp C:\tmp\pytest-integrated-ui-frontend` and require zero failures.

- [ ] **Step 2: Run the full suite**

Run `python -m pytest -q -p no:cacheprovider --basetemp C:\tmp\pytest-integrated-ui-final` and require zero failures.

- [ ] **Step 3: Build production assets**

Run `npm.cmd run build` and require exit code 0 without Svelte accessibility warnings.

- [ ] **Step 4: Verify catalog invariants**

Load `public/data/stock.json` and assert: 370 products, 339 unique material-swatch URLs, only `-v2.webp` references, all referenced files exist, every referenced image is 320x320, and no Pantone product has estimated-color fields.

### Task 3: Review and publish

**Files:**
- No additional source files expected.

**Interfaces:**
- Consumes: successful automated verification and local production-equivalent UI.
- Produces: updated `master` and verified GitHub Pages deployment.

- [ ] **Step 1: Review in Chrome**

Run the integrated app locally, open the summary/home view in Chrome, verify current product photos, material swatches, filters, quote drawer, and zoom preview at desktop and mobile widths.

- [ ] **Step 2: Commit the isolated integration**

Stage only the eleven UI paths and this plan. Commit with `feat:publish-integrated-local-interface`.

- [ ] **Step 3: Fast-forward remote master**

Fetch `origin/master`, require it to be an ancestor of `HEAD`, then run `git push origin HEAD:master`.

- [ ] **Step 4: Verify deployment**

Require successful CI, Publish UI, and any triggered asset workflow. Confirm the public HTML references the new bundle, the public JSON reports 370 products and 339 v2 swatches, and a representative product image and material swatch return HTTP 200.
