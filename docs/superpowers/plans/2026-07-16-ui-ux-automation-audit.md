# UI/UX Automation Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and execute a production-grade Chrome UI/UX audit across 4K, 2K, 1080p, laptop, and mobile screens.

**Architecture:** Playwright Test runs a production Vite preview through named Chrome viewport projects. Shared fixtures collect browser/runtime failures, route specs cover responsive invariants, focused specs exercise product workflows, axe scans dynamic states, and Lighthouse CI records performance evidence.

**Tech Stack:** Svelte 5, Vite 8, Node 24, Playwright Test, Chrome, axe-core, Lighthouse CI, GitHub Actions.

## Global Constraints

- Do not change product behavior during the audit.
- Use Chrome for interactive UI inspection.
- Keep runtime static and GitHub Pages-compatible.
- Use deterministic local static data and clear browser persistence between independent tests.
- Stop after three evidence-driven attempts for the same failure.

---

### Task 1: Browser test runtime

**Files:**
- Modify: `package.json`
- Modify: `package-lock.json`
- Create: `playwright.config.js`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `npm run test:ui`, `npm run test:ui:update`, and `npm run audit:lighthouse`.

- [ ] **Step 1: Add a minimal smoke spec before configuration**

Create `tests/e2e/runtime.spec.js` importing `test` and `expect` from `@playwright/test`, navigating to `/CentraldeFilamentos/`, and asserting that `main` is visible.

- [ ] **Step 2: Run the spec and verify RED**

Run: `npm run test:ui -- tests/e2e/runtime.spec.js`

Expected: failure because the script or Playwright dependency does not exist.

- [ ] **Step 3: Install and configure the runtime**

Install `@playwright/test`, `@axe-core/playwright`, and `@lhci/cli` as development dependencies. Configure `webServer` to build and preview on port 4173, `channel: "chrome"`, trace/screenshot retention, and the eight exact viewport projects from the design.

- [ ] **Step 4: Verify GREEN**

Run: `npm run test:ui -- tests/e2e/runtime.spec.js`

Expected: eight passing project executions.

### Task 2: Cross-viewport quality gates

**Files:**
- Create: `tests/e2e/helpers/audit.js`
- Create: `tests/e2e/responsive.spec.js`

**Interfaces:**
- Produces: `installRuntimeGuards(page)`, `waitForStablePage(page)`, `visibleOverflow(page)`, and `brokenImages(page)`.

- [ ] **Step 1: Write route assertions for the three public surfaces**

Assert successful navigation, visible main and heading, no horizontal overflow, no clipped interactive controls, no broken images, no console/page errors, and no failed same-origin requests.

- [ ] **Step 2: Verify RED against the unimplemented helpers**

Run: `npm run test:ui -- tests/e2e/responsive.spec.js`

Expected: helper import or assertion failure.

- [ ] **Step 3: Implement the smallest shared helpers**

Collect errors per page, wait for document fonts and rendered images, and return structured geometry/image violations for clear failure messages.

- [ ] **Step 4: Run all eight viewport projects**

Run: `npm run test:ui -- tests/e2e/responsive.spec.js`

Expected: route-by-project results with every real defect named by route and viewport.

### Task 3: Critical product flows

**Files:**
- Create: `tests/e2e/summary-flow.spec.js`
- Create: `tests/e2e/color-picker-flow.spec.js`

**Interfaces:**
- Consumes: runtime guards and stable-page helper.
- Produces: verified summary/quote and Color Picker journeys.

- [ ] **Step 1: Write desktop and mobile summary flow tests**

Cover filters, filter removal, add-to-quote, quantity, box x12, persistence, provider coverage, send step, stock watch, image preview, keyboard close, and focus return.

- [ ] **Step 2: Run and record expected RED failures**

Run each spec against `desktop-1080` and `mobile-390`; confirm selectors or behavioral expectations fail for the intended missing test support rather than syntax errors.

- [ ] **Step 3: Complete selectors and deterministic setup**

Use accessible roles and labels. Clear the two application local-storage keys before each independent flow and avoid test-only production hooks.

- [ ] **Step 4: Write and run the Color Picker flow**

Cover view switching, stock/sampler toggles, color comparison, similar-color search, four-color constraint, quote addition, and cross-page quote persistence.

### Task 4: Accessibility and visual evidence

**Files:**
- Create: `tests/e2e/accessibility.spec.js`
- Create: `tests/e2e/visual.spec.js`
- Create: `tests/e2e/__screenshots__/win32/`

**Interfaces:**
- Produces: serious/critical axe gate and stable visual baselines.

- [ ] **Step 1: Add axe scans for static and dynamic states**

Scan WCAG 2 A/AA/2.1/2.2 tags after opening drawers, modals, provider tabs, and comparison states. Attach the complete JSON result to the Playwright report and fail on serious or critical violations.

- [ ] **Step 2: Verify accessibility results**

Run: `npm run test:ui -- tests/e2e/accessibility.spec.js --project=desktop-1080 --project=mobile-390`

- [ ] **Step 3: Add stable screenshot assertions**

Disable animations, wait for fonts/images, mask only generated timestamps, and capture the named states from the design.

- [ ] **Step 4: Generate and re-run baselines**

Run `npm run test:ui:update -- tests/e2e/visual.spec.js`, inspect every generated image, then rerun without update and require zero unexpected differences.

### Task 5: Lighthouse and continuous integration

**Files:**
- Create: `lighthouserc.json`
- Create: `.github/workflows/ui-audit.yml`

**Interfaces:**
- Produces: repeatable mobile Lighthouse reports and a Windows Chrome pull-request gate.

- [ ] **Step 1: Configure Lighthouse collection**

Collect two runs for summary and Color Picker against the production preview. Assert accessibility ≥ 0.90, best practices ≥ 0.90, SEO ≥ 0.90, CLS ≤ 0.10, and warn on performance below 0.70.

- [ ] **Step 2: Run Lighthouse locally**

Run: `npm run audit:lighthouse`

Expected: reports under `.lighthouseci/` and explicit assertion results.

- [ ] **Step 3: Add Windows Chrome CI**

Install dependencies with `npm ci`, run UI tests, upload Playwright/Lighthouse artifacts on failure, and keep the existing Python/Node CI unchanged.

### Task 6: Human-grade Chrome audit and report

**Files:**
- Create: `docs/ui-audit/2026-07-16/report.md`
- Create: `docs/ui-audit/2026-07-16/screenshots/*.png`

**Interfaces:**
- Produces: screenshot-backed UX/accessibility report and exact evidence limits.

- [ ] **Step 1: Inspect representative flows in Chrome**

Capture accepted screenshots for desktop summary, mobile summary, open quote workflow, Color Picker palette/comparison, and vendor statistics/disabled state.

- [ ] **Step 2: Inspect every saved screenshot**

Reject blank, loading, cropped, or wrong-state captures. Record hierarchy, spacing, readability, focus, target-size, and responsive findings tied to numbered screenshots.

- [ ] **Step 3: Run the complete verification set**

Run Python tests, configured Node tests, Vite build, all Playwright projects, visual comparison, axe, and Lighthouse. Record exact pass/fail counts without hiding pre-existing defects.

- [ ] **Step 4: Write the final report**

Include scope, step health, strengths, UX risks, accessibility risks, viewport table, performance measurements, failure attempts, evidence limits, and prioritized recommendations.
