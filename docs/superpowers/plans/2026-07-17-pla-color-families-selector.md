# PLA Color Families Selector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the catalog show explicit color families for PLA while preserving exact-color selection for every other material.

**Architecture:** Keep material-first filtering in `catalogExplorer.js`. Make each returned choice declare whether it represents a `family` or an `exact` color, then let the shared matcher honor that mode. `ColorRibbon.svelte` renders visible family labels and multi-tone swatches without changing the separate Color Picker page.

**Tech Stack:** Svelte 5, JavaScript ES modules, Node test runner, Vite, native CSS.

## Global Constraints

- Material remains a hard constraint and never broadens across PLA, PETG, ABS, TPU, Nylon, ASA, or Otros.
- PLA uses family-level choices; all other materials use exact-color choices.
- No new dependency, route, data field, server endpoint, or persistence key.
- Preserve the current teal, neutral, compact visual system and horizontal mobile scrolling.

---

### Task 1: Make selector semantics match what the maker sees

**Files:**
- Modify: `tests/catalogExplorer.test.js`
- Modify: `tests/e2e/option1-flow.spec.js`
- Modify: `src/lib/catalogExplorer.js`
- Modify: `src/components/ColorRibbon.svelte`
- Modify: `src/SummaryApp.svelte`
- Modify: `src/styles/global.css`

**Interfaces:**
- Consumes: `colorFamilyForProduct(product)`, `productColorHex(product)`, and the current material-first product list.
- Produces: `colorChoices(products, material)` choices with `selectionMode: "family" | "exact"`, plus `matchesColorSelection(product, choice)`.

- [ ] **Step 1: Write failing unit tests for PLA families and non-PLA exact colors**

Add assertions equivalent to:

```js
const plaChoices = colorChoices([
  { material: "PLA", color: "Blanco", estimated_color_hex: "#F6F5F2", offers: [] },
  { material: "PLA", color: "Hueso", estimated_color_hex: "#F7F4ED", offers: [] },
], "PLA");
assert.deepEqual(plaChoices.map((choice) => choice.name), ["Claros"]);
assert.equal(plaChoices[0].selectionMode, "family");

const petgProducts = [
  { material: "PETG", color: "Blanco", estimated_color_hex: "#F6F5F2", offers: [] },
  { material: "PETG", color: "Hueso", estimated_color_hex: "#F7F4ED", offers: [] },
];
const petgChoices = colorChoices(petgProducts, "PETG");
const white = petgChoices.find((choice) => choice.name === "Blanco");
assert.equal(white.selectionMode, "exact");
assert.equal(matchesColorSelection(petgProducts[1], white), false);
```

- [ ] **Step 2: Run the unit test and verify RED**

Run: `node --test tests/catalogExplorer.test.js`

Expected: FAIL because PLA still returns exact colors and `matchesColorSelection` does not exist.

- [ ] **Step 3: Implement family and exact choice builders**

In `src/lib/catalogExplorer.js`, group PLA products by `colorFamilyForProduct(product).id`, retain the family label, aggregate stock and product counts, expose up to three real family HEX values for the swatch, and order families as neutrals followed by chromatic families. Keep the existing exact-name grouping for non-PLA materials. Implement:

```js
export function matchesColorSelection(product, selectedChoice) {
  if (!selectedChoice) return true;
  if (selectedChoice.selectionMode === "exact") return product?.color === selectedChoice.name;
  return colorFamilyForProduct(product).id === selectedChoice.familyId;
}
```

- [ ] **Step 4: Render explicit family controls**

In `ColorRibbon.svelte`, use PLA copy such as `Explorá familias de color en PLA`, display each family name beside its multi-tone swatch, and describe the selected family by exact-color and option counts. For non-PLA materials, preserve the compact exact-color swatches and exact selection copy.

- [ ] **Step 5: Wire the semantic matcher into the catalog**

Replace `matchesColorFamilySelection` with `matchesColorSelection` in `SummaryApp.svelte`, keeping the active material check first. Update the Option 1 browser test to select `Amarillos` and verify every result remains PLA and belongs to that family.

- [ ] **Step 6: Run focused tests and verify GREEN**

Run: `node --test tests/catalogExplorer.test.js`

Expected: PASS.

Run: `npx playwright test tests/e2e/option1-flow.spec.js --project=desktop-1080 --project=mobile-390`

Expected: PASS on both representative viewports.

- [ ] **Step 7: Verify the production build and full relevant suite**

Run: `npm run build`

Expected: Vite build succeeds without Svelte compile errors.

Run: `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos`

Expected: all Python tests pass.

