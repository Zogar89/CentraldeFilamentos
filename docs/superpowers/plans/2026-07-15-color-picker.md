# PLA Color Picker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a new static `color-picker.html` page for PLA that dynamically organizes catalog colors, finds the three closest matches with CIEDE2000, compares up to four logical colors, and adds concrete presentations to the existing quote list.

**Architecture:** Keep all color derivation in a pure `src/lib/colorPicker.js` module backed by Culori, and keep the Svelte page as orchestration state over three focused components. The page reads the existing static `stock.json`, groups by brand + line + color, and reuses the current quote-list persistence contract without introducing backend state.

**Tech Stack:** Svelte 5.55.7, Vite 8.0.13, JavaScript ES modules, Culori 4.0.2, Node `node:test`, pytest frontend contract tests, GitHub Pages.

## Global Constraints

- Initial material scope is exactly `PLA`; other materials do not enter the palette.
- A logical color key is normalized brand + normalized line + normalized color name; weight, presentation, and diameter do not affect identity.
- Show all logical colors initially; `Ocultar sin stock` starts unchecked.
- `Continuo` is the initial view; `Familias` and `Mapa 2D` remain available.
- All positions, families, RGB values, and neighbor distances are recomputed from the current published HEX at runtime.
- Similar-color search returns at most exactly 3 results and uses CIEDE2000.
- The comparator starts empty and accepts at most 4 logical colors.
- Comparison uses `material_swatch_url` and falls back to the flat HEX; it never invents a Pantone.
- Every presentation `+1` targets a concrete existing `product.id` and persists through `centraldefilamentos.quoteList.v1`.
- Culori is bundled through npm as `^4.0.2`; no CDN or runtime server is allowed.
- The deployment remains a static Vite multi-page build under `/CentraldeFilamentos/`.
- Windows verification uses `npm.cmd` and `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos-color-picker`.

---

## File map

- Create `color-picker.html`: fourth public HTML entry.
- Create `src/color-picker.js`: thin Svelte mount entry.
- Create `src/ColorPickerApp.svelte`: data loading and interaction orchestration.
- Create `src/components/ColorPalette.svelte`: continuous, families, and 2D map rendering.
- Create `src/components/SimilarColorSearch.svelte`: controlled HEX form and three result cards.
- Create `src/components/ColorComparator.svelte`: comparison metadata, material render, and presentation actions.
- Create `src/lib/colorPicker.js`: pure grouping and color-science functions.
- Create `tests/colorPicker.test.js`: Node unit tests for the pure domain module.
- Modify `src/lib/quoteList.js` and `tests/quoteList.test.js`: share and test one-item increment behavior.
- Modify `src/components/SiteHeader.svelte`: expose the new public navigation item.
- Modify `src/styles/global.css`: scoped page layout, responsive behavior, focus, tooltips, and fallbacks.
- Modify `vite.config.js`, `package.json`, and `package-lock.json`: add the entry, test script, and Culori dependency.
- Modify `tests/test_frontend_assets.py`: enforce the new page and integration contracts.

---

### Task 1: Pure color catalog and Culori integration

**Files:**
- Create: `src/lib/colorPicker.js`
- Create: `tests/colorPicker.test.js`
- Modify: `package.json`
- Modify: `package-lock.json`

**Interfaces:**
- Consumes: `foldText(value)`, `lineLabel(product)`, `formatPresentation(product)`, and `comparePresentations(left, right)` from `src/lib/shared.js`; product records from `stock.json`.
- Produces: `buildPlaColorCatalog(products) -> { groups, excludedCount }`, `sortPerceptually(groups)`, `groupColorFamilies(groups)`, `buildColorMap(groups)`, `findSimilarColors(groups, referenceHex, excludedGroupId, limit = 3)`, `normalizeHex(value)`, `isValidHex(value)`, `rgbFromHex(hex)`, `distanceLabel(deltaE)`, and `toggleComparedColor(ids, id, max = 4)`.

- [ ] **Step 1: Install the pinned runtime dependency**

Run:

```powershell
npm.cmd install culori@^4.0.2
```

Expected: `package.json` contains `"culori": "^4.0.2"` under `dependencies`, `package-lock.json` resolves Culori, and npm exits 0.

- [ ] **Step 2: Write the failing unit tests**

Create `tests/colorPicker.test.js` with these concrete cases:

```js
import test from "node:test";
import assert from "node:assert/strict";
import {
  buildColorMap,
  buildPlaColorCatalog,
  distanceLabel,
  findSimilarColors,
  groupColorFamilies,
  isValidHex,
  normalizeHex,
  rgbFromHex,
  sortPerceptually,
  toggleComparedColor,
} from "../src/lib/colorPicker.js";

function product(overrides = {}) {
  return {
    id: "pla-rojo-175-1000-grilon3",
    display_name: "Grilon3 PLA Rojo 1 kg",
    material: "PLA",
    variant: "",
    color: "Rojo",
    brand: "Grilon3",
    diameter_mm: 1.75,
    weight_g: 1000,
    pantone: "Pantone 179 C",
    pantone_hex: "#D92920",
    estimated_color_hex: "",
    estimated_color_confidence_band: "",
    estimated_color_source: "",
    estimated_color_warning: "",
    material_swatch_url: "assets/material-swatches/pantone-179-c-satin-v2.webp",
    offers: [{ provider_name: "Proveedor", stock_status: "in_stock", stock_quantity: 2 }],
    ...overrides,
  };
}

test("normalizes and validates #RRGGBB values", () => {
  assert.equal(normalizeHex("009dce"), "#009DCE");
  assert.equal(isValidHex("#009DCE"), true);
  assert.equal(isValidHex("#09DCE"), false);
  assert.deepEqual(rgbFromHex("#009DCE"), { r: 0, g: 157, b: 206 });
});

test("groups PLA by brand line and color while ignoring weight and diameter", () => {
  const products = [
    product(),
    product({ id: "pla-rojo-285-2500-grilon3", diameter_mm: 2.85, weight_g: 2500 }),
    product({ id: "pla-rojo-175-1000-3n3", brand: "3N3", pantone: "", pantone_hex: "", estimated_color_hex: "#D82A22" }),
    product({ id: "petg-rojo", material: "PETG" }),
  ];
  const catalog = buildPlaColorCatalog(products);
  assert.equal(catalog.groups.length, 2);
  const grilon = catalog.groups.find((group) => group.brand === "Grilon3");
  assert.equal(grilon.presentations.length, 2);
  assert.deepEqual(grilon.presentations.map((item) => item.label), ["1 kg · 1.75 mm", "2.5 kg · 2.85 mm"]);
});

test("prefers Pantone, then estimate confidence, source, stock, and id", () => {
  const catalog = buildPlaColorCatalog([
    product({ id: "z-low", pantone: "", pantone_hex: "", estimated_color_hex: "#CC2222", estimated_color_confidence_band: "low", estimated_color_source: "name_only" }),
    product({ id: "b-high", pantone: "", pantone_hex: "", estimated_color_hex: "#DD2222", estimated_color_confidence_band: "high", estimated_color_source: "image_and_name" }),
    product({ id: "a-pantone", pantone_hex: "#D92920" }),
  ]);
  assert.equal(catalog.groups[0].representative.id, "a-pantone");
  assert.equal(catalog.groups[0].hex, "#D92920");
});

test("counts PLA products without usable color data", () => {
  const catalog = buildPlaColorCatalog([
    product(),
    product({ id: "missing", color: "Sin dato", pantone_hex: "", estimated_color_hex: "" }),
  ]);
  assert.equal(catalog.excludedCount, 1);
});

test("derives stock and de-duplicates identical presentations", () => {
  const catalog = buildPlaColorCatalog([
    product({ id: "out", offers: [{ stock_status: "out_of_stock" }] }),
    product({ id: "in", offers: [{ stock_status: "in_stock" }] }),
  ]);
  assert.equal(catalog.groups[0].inStock, true);
  assert.equal(catalog.groups[0].presentations.length, 1);
  assert.equal(catalog.groups[0].presentations[0].product.id, "in");
});

test("sorts, groups, and maps from current OKLCH values", () => {
  const groups = buildPlaColorCatalog([
    product({ id: "red", color: "Rojo", pantone_hex: "#FF0000" }),
    product({ id: "green", color: "Verde", pantone_hex: "#00AA44" }),
    product({ id: "white", color: "Blanco", pantone_hex: "#F7F7F7" }),
  ]).groups;
  assert.equal(sortPerceptually(groups).length, 3);
  assert.equal(groupColorFamilies(groups).get("Neutros").length, 1);
  assert.ok(buildColorMap(groups).every((item) => item.mapColumn >= 1 && item.mapColumn <= 12 && item.mapRow >= 1 && item.mapRow <= 6));
});

test("returns exactly three ordered CIEDE2000 neighbors and excludes the source group", () => {
  const groups = buildPlaColorCatalog([
    product({ id: "ref", color: "Referencia", pantone_hex: "#FF0000" }),
    product({ id: "one", color: "Uno", pantone_hex: "#F01010" }),
    product({ id: "two", color: "Dos", pantone_hex: "#D92920" }),
    product({ id: "three", color: "Tres", pantone_hex: "#B03020" }),
    product({ id: "four", color: "Cuatro", pantone_hex: "#0066CC" }),
  ]).groups;
  const source = groups.find((group) => group.name === "Referencia");
  const results = findSimilarColors(groups, source.hex, source.id);
  assert.equal(results.length, 3);
  assert.equal(results.some((item) => item.group.id === source.id), false);
  assert.ok(results[0].distance <= results[1].distance && results[1].distance <= results[2].distance);
});

test("labels distances and enforces four compared colors", () => {
  assert.equal(distanceLabel(2.9), "Muy cercano");
  assert.equal(distanceLabel(3), "Cercano");
  assert.equal(distanceLabel(8), "Alternativa");
  assert.deepEqual(toggleComparedColor(["a", "b", "c", "d"], "e"), {
    ids: ["a", "b", "c", "d"],
    message: "El comparador admite hasta cuatro colores. Quitá uno para sumar otro.",
  });
});
```

- [ ] **Step 3: Run the new test and verify it fails**

Run:

```powershell
node --test tests/colorPicker.test.js
```

Expected: FAIL with `ERR_MODULE_NOT_FOUND` for `src/lib/colorPicker.js`.

- [ ] **Step 4: Implement the pure module**

Create `src/lib/colorPicker.js` with this public contract and deterministic rules:

```js
import { converter, differenceCiede2000 } from "culori";
import {
  comparePresentations,
  foldText,
  formatPresentation,
  lineLabel,
  slugText,
} from "./shared.js";

const toOklch = converter("oklch");
const toRgb = converter("rgb");
const ciede2000 = differenceCiede2000();
const familyOrder = ["Rojos", "Naranjas", "Amarillos", "Verdes", "Turquesas", "Azules", "Violetas", "Rosas", "Neutros"];

export function normalizeHex(value) {
  const raw = String(value || "").trim().toUpperCase();
  return raw.startsWith("#") ? raw : `#${raw}`;
}

export function isValidHex(value) {
  return /^#[0-9A-F]{6}$/i.test(normalizeHex(value));
}

export function rgbFromHex(hex) {
  const rgb = toRgb(normalizeHex(hex));
  return {
    r: Math.round((rgb?.r || 0) * 255),
    g: Math.round((rgb?.g || 0) * 255),
    b: Math.round((rgb?.b || 0) * 255),
  };
}

export function productColorHex(product) {
  if (isValidHex(product?.pantone_hex)) return normalizeHex(product.pantone_hex);
  if (isValidHex(product?.estimated_color_hex)) return normalizeHex(product.estimated_color_hex);
  return "";
}

function productInStock(product) {
  return (product?.offers || []).some((offer) => offer.stock_status === "in_stock");
}

function confidenceRank(value) {
  return ({ high: 0, medium: 1, low: 2 })[String(value || "").toLowerCase()] ?? 3;
}

function sourceRank(value) {
  return ({ image_and_name: 0, name_only: 1 })[String(value || "").toLowerCase()] ?? 2;
}

function compareRepresentatives(left, right) {
  const leftPantone = isValidHex(left.pantone_hex) ? 0 : 1;
  const rightPantone = isValidHex(right.pantone_hex) ? 0 : 1;
  return leftPantone - rightPantone
    || confidenceRank(left.estimated_color_confidence_band) - confidenceRank(right.estimated_color_confidence_band)
    || sourceRank(left.estimated_color_source) - sourceRank(right.estimated_color_source)
    || Number(productInStock(right)) - Number(productInStock(left))
    || String(left.id).localeCompare(String(right.id), "es-AR");
}

function logicalColorKey(product) {
  return [product.brand || "Sin marca", lineLabel(product), product.color || "Sin color"].map(foldText).join("||");
}

function presentationKey(product) {
  return [formatPresentation(product), product.diameter_mm ?? ""].join("||");
}

function choosePresentation(current, candidate) {
  if (!current) return candidate;
  if (productInStock(candidate) !== productInStock(current)) return productInStock(candidate) ? candidate : current;
  return String(candidate.id).localeCompare(String(current.id), "es-AR") < 0 ? candidate : current;
}

function buildGroup(products) {
  const ordered = products.slice().sort(compareRepresentatives);
  const representative = ordered[0];
  const diameterCount = new Set(products.map((product) => product.diameter_mm).filter(Boolean)).size;
  const presentationByKey = new Map();
  for (const product of products) {
    const key = presentationKey(product);
    presentationByKey.set(key, choosePresentation(presentationByKey.get(key), product));
  }
  const presentations = [...presentationByKey.values()].sort(comparePresentations).map((product) => {
    const base = formatPresentation(product) || "Presentación a confirmar";
    return {
      id: product.id,
      label: diameterCount > 1 && product.diameter_mm ? `${base} · ${product.diameter_mm} mm` : base,
      inStock: productInStock(product),
      product,
    };
  });
  const line = lineLabel(representative);
  const name = representative.color || "Sin color";
  const brand = representative.brand || "Sin marca";
  return {
    id: slugText([brand, line, name].join("-")),
    name,
    brand,
    line,
    hex: productColorHex(representative),
    pantone: representative.pantone || "",
    estimated: !isValidHex(representative.pantone_hex),
    warning: representative.estimated_color_warning || "",
    materialSwatchUrl: representative.material_swatch_url || "",
    inStock: products.some(productInStock),
    representative,
    products: products.slice(),
    presentations,
  };
}

export function buildPlaColorCatalog(products) {
  const pla = (products || []).filter((product) => product.material === "PLA");
  const eligible = pla.filter((product) => productColorHex(product));
  const grouped = new Map();
  for (const product of eligible) {
    const key = logicalColorKey(product);
    grouped.set(key, [...(grouped.get(key) || []), product]);
  }
  return {
    groups: [...grouped.values()].map(buildGroup).sort((left, right) => left.id.localeCompare(right.id, "es-AR")),
    excludedCount: pla.length - eligible.length,
  };
}

function oklchFor(group) {
  const value = toOklch(group.hex) || {};
  return { l: Number(value.l || 0), c: Number(value.c || 0), h: Number.isFinite(value.h) ? value.h : 0 };
}

export function sortPerceptually(groups) {
  return (groups || []).slice().sort((left, right) => {
    const a = oklchFor(left);
    const b = oklchFor(right);
    const neutralA = a.c < 0.045;
    const neutralB = b.c < 0.045;
    if (neutralA !== neutralB) return neutralA ? 1 : -1;
    if (neutralA) return b.l - a.l || left.id.localeCompare(right.id, "es-AR");
    return a.h - b.h || b.l - a.l || b.c - a.c || left.id.localeCompare(right.id, "es-AR");
  });
}

export function colorFamily(group) {
  const value = oklchFor(group);
  if (value.c < 0.045) return "Neutros";
  if (value.h < 25 || value.h >= 350) return "Rojos";
  if (value.h < 65) return "Naranjas";
  if (value.h < 115) return "Amarillos";
  if (value.h < 170) return "Verdes";
  if (value.h < 225) return "Turquesas";
  if (value.h < 285) return "Azules";
  if (value.h < 330) return "Violetas";
  return "Rosas";
}

export function groupColorFamilies(groups) {
  const result = new Map(familyOrder.map((name) => [name, []]));
  for (const group of sortPerceptually(groups)) result.get(colorFamily(group)).push(group);
  for (const [name, items] of [...result]) if (!items.length) result.delete(name);
  return result;
}

export function buildColorMap(groups) {
  return (groups || []).map((group) => {
    const value = oklchFor(group);
    return {
      ...group,
      oklch: value,
      mapColumn: Math.min(12, Math.max(1, Math.floor(value.h / 30) + 1)),
      mapRow: Math.min(6, Math.max(1, 7 - Math.floor(value.l * 6))),
    };
  }).sort((left, right) => left.mapRow - right.mapRow || left.mapColumn - right.mapColumn || right.oklch.c - left.oklch.c || left.id.localeCompare(right.id, "es-AR"));
}

export function findSimilarColors(groups, referenceHex, excludedGroupId = "", limit = 3) {
  const hex = normalizeHex(referenceHex);
  if (!isValidHex(hex)) return [];
  return (groups || []).filter((group) => group.id !== excludedGroupId).map((group) => ({
    group,
    distance: ciede2000(hex, group.hex),
  })).sort((left, right) => left.distance - right.distance || left.group.id.localeCompare(right.group.id, "es-AR")).slice(0, limit);
}

export function distanceLabel(distance) {
  if (distance < 3) return "Muy cercano";
  if (distance < 8) return "Cercano";
  return "Alternativa";
}

export function toggleComparedColor(ids, id, max = 4) {
  if (ids.includes(id)) return { ids: ids.filter((value) => value !== id), message: "Color quitado del comparador." };
  if (ids.length >= max) return { ids: ids.slice(), message: "El comparador admite hasta cuatro colores. Quitá uno para sumar otro." };
  return { ids: [...ids, id], message: "Color agregado al comparador." };
}
```

- [ ] **Step 5: Run the domain test**

Run:

```powershell
node --test tests/colorPicker.test.js
```

Expected: 8 tests PASS and exit code 0.

- [ ] **Step 6: Commit the pure domain slice**

```powershell
git add package.json package-lock.json src/lib/colorPicker.js tests/colorPicker.test.js
git commit -m "feat: derive PLA color catalog with Culori"
```

---

### Task 2: Public page shell, data loading, and navigation

**Files:**
- Create: `color-picker.html`
- Create: `src/color-picker.js`
- Create: `src/ColorPickerApp.svelte`
- Modify: `src/components/SiteHeader.svelte`
- Modify: `vite.config.js`
- Modify: `package.json`
- Modify: `tests/test_frontend_assets.py`

**Interfaces:**
- Consumes: `fetchJson("data/stock.json", null)`, `buildPlaColorCatalog(products)`, `SiteHeader`, and `SiteFooter`.
- Produces: a buildable fourth Vite entry and the page-level states `loading`, `loadError`, `groups`, `excludedCount`, `sources`, and `generatedAt`.

- [ ] **Step 1: Add the failing frontend contract test**

Append this test to `tests/test_frontend_assets.py`:

```python
def test_color_picker_page_is_linked_and_built():
    html = (ROOT / "color-picker.html").read_text(encoding="utf-8")
    entry = (ROOT / "src" / "color-picker.js").read_text(encoding="utf-8")
    app = (ROOT / "src" / "ColorPickerApp.svelte").read_text(encoding="utf-8")
    header = (ROOT / "src" / "components" / "SiteHeader.svelte").read_text(encoding="utf-8")
    vite = (ROOT / "vite.config.js").read_text(encoding="utf-8")

    assert 'src="/src/color-picker.js"' in html
    assert 'mount(ColorPickerApp' in entry
    assert 'fetchJson("data/stock.json", null)' in app
    assert 'active="color-picker"' in app
    assert 'href: "color-picker.html"' in header
    assert 'colorPicker: resolve(__dirname, "color-picker.html")' in vite
```

- [ ] **Step 2: Run the contract test and verify it fails**

Run:

```powershell
python -m pytest tests/test_frontend_assets.py::test_color_picker_page_is_linked_and_built -v --basetemp C:\tmp\pytest-color-picker-shell
```

Expected: FAIL because `color-picker.html` does not exist.

- [ ] **Step 3: Create the HTML and mount entry**

Create `color-picker.html`:

```html
<!doctype html>
<html lang="es-AR">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Color Picker · Central de Filamentos</title>
    <meta name="description" content="Buscá, compará y elegí filamentos PLA por color.">
    <script type="module" src="/src/color-picker.js"></script>
  </head>
  <body>
    <div id="app"></div>
  </body>
</html>
```

Create `src/color-picker.js`:

```js
import "./styles/global.css";
import ColorPickerApp from "./ColorPickerApp.svelte";
import { mount } from "svelte";

mount(ColorPickerApp, {
  target: document.getElementById("app"),
});
```

- [ ] **Step 4: Create the load/error shell**

Create `src/ColorPickerApp.svelte`:

```svelte
<script>
  import { onMount } from "svelte";
  import SiteFooter from "./components/SiteFooter.svelte";
  import SiteHeader from "./components/SiteHeader.svelte";
  import { buildPlaColorCatalog } from "./lib/colorPicker.js";
  import { fetchJson } from "./lib/shared.js";

  let loading = true;
  let loadError = "";
  let groups = [];
  let excludedCount = 0;
  let sources = [];
  let generatedAt = "";

  onMount(loadCatalog);

  async function loadCatalog() {
    loading = true;
    loadError = "";
    const payload = await fetchJson("data/stock.json", null);
    if (!payload || !Array.isArray(payload.products)) {
      loading = false;
      loadError = "No pudimos cargar los colores publicados.";
      return;
    }
    const catalog = buildPlaColorCatalog(payload.products);
    groups = catalog.groups;
    excludedCount = catalog.excludedCount;
    sources = Array.isArray(payload.sources) ? payload.sources : [];
    generatedAt = payload.generated_at || "";
    loading = false;
  }
</script>

<SiteHeader active="color-picker" updatedAt={generatedAt} subtitle="PLA · búsqueda por color" />

<main id="main-content" class="color-picker-page">
  <header class="color-picker-hero">
    <div>
      <span class="eyebrow">PLA · COLOR PICKER</span>
      <h1>Encontrá el color que necesitás</h1>
      <p>Explorá el catálogo por apariencia, compará hasta cuatro opciones y sumá la presentación exacta a tu lista.</p>
    </div>
  </header>

  {#if loading}
    <p class="color-picker-state" role="status">Cargando colores…</p>
  {:else if loadError}
    <section class="color-picker-state" role="alert">
      <p>{loadError}</p>
      <button type="button" on:click={loadCatalog}>Reintentar</button>
    </section>
  {:else if !groups.length}
    <p class="color-picker-state">No hay filamentos PLA con datos HEX disponibles.</p>
  {:else}
    <p class="color-picker-state">{groups.length} colores PLA{excludedCount ? ` · ${excludedCount} sin datos cromáticos` : ""}</p>
  {/if}
</main>

<SiteFooter {sources} />
```

- [ ] **Step 5: Wire navigation, Vite, and the test script**

Add this item to `navItems` in `src/components/SiteHeader.svelte`, between Catálogo and Resumen:

```js
{ id: "color-picker", label: "Color Picker", href: "color-picker.html" },
```

Add this input to `vite.config.js`:

```js
colorPicker: resolve(__dirname, "color-picker.html"),
```

Add this script to `package.json`:

```json
"test:color-picker": "node --test tests/colorPicker.test.js"
```

- [ ] **Step 6: Verify the shell**

Run:

```powershell
python -m pytest tests/test_frontend_assets.py::test_color_picker_page_is_linked_and_built -v --basetemp C:\tmp\pytest-color-picker-shell
npm.cmd run test:color-picker
npm.cmd run build
```

Expected: contract test PASS, 8 Node tests PASS, and Vite output includes `dist/color-picker.html`.

- [ ] **Step 7: Commit the public shell**

```powershell
git add color-picker.html src/color-picker.js src/ColorPickerApp.svelte src/components/SiteHeader.svelte vite.config.js package.json tests/test_frontend_assets.py
git commit -m "feat: add Color Picker page shell"
```

---

### Task 3: Dynamic palette with three views and four-color selection

**Files:**
- Create: `src/components/ColorPalette.svelte`
- Modify: `src/ColorPickerApp.svelte`
- Modify: `src/styles/global.css`
- Modify: `tests/test_frontend_assets.py`

**Interfaces:**
- Consumes: logical groups from `buildPlaColorCatalog`, `sortPerceptually`, `groupColorFamilies`, `buildColorMap`, and `toggleComparedColor`.
- Produces: `ColorPalette` props `{ groups, view, selectedIds, onSelect }`; page state `{ activeView, hideOutOfStock, selectedIds, referenceHex, referenceGroupId, selectionMessage }`.

- [ ] **Step 1: Add a failing component contract**

Extend the existing color-picker test in `tests/test_frontend_assets.py` with:

```python
    palette = (ROOT / "src" / "components" / "ColorPalette.svelte").read_text(encoding="utf-8")
    assert 'aria-pressed={selectedIds.includes(group.id)}' in palette
    assert 'view === "continuous"' in palette
    assert 'view === "families"' in palette
    assert 'view === "map"' in palette
    assert 'Ocultar sin stock' in app
```

- [ ] **Step 2: Run the contract and verify it fails**

Run the same targeted pytest command from Task 2. Expected: FAIL because `ColorPalette.svelte` is absent.

- [ ] **Step 3: Implement `ColorPalette.svelte`**

Create the component with these exact branches and accessible tile contract:

```svelte
<script>
  import { buildColorMap, groupColorFamilies, sortPerceptually } from "../lib/colorPicker.js";

  export let groups = [];
  export let view = "continuous";
  export let selectedIds = [];
  export let onSelect = () => {};

  $: continuousGroups = sortPerceptually(groups);
  $: familyGroups = [...groupColorFamilies(groups)];
  $: mapGroups = buildColorMap(groups);

  function tooltip(group) {
    return `${group.brand} · ${group.line} · ${group.name} · ${group.hex} · ${group.inStock ? "con stock" : "sin stock"}`;
  }
</script>

{#snippet tile(group)}
  <button
    type="button"
    class:without-stock={!group.inStock}
    class="color-picker-tile"
    style={`--picker-color: ${group.hex}`}
    aria-label={tooltip(group)}
    aria-pressed={selectedIds.includes(group.id)}
    data-tooltip={tooltip(group)}
    on:click={() => onSelect(group)}
  >
    <span class="sr-only">{group.name}</span>
    {#if !group.inStock}<span class="color-picker-stock-mark" aria-hidden="true">×</span>{/if}
  </button>
{/snippet}

{#if view === "continuous"}
  <div class="color-picker-palette color-picker-palette-continuous" aria-label="Paleta continua de colores PLA">
    {#each continuousGroups as group (group.id)}{@render tile(group)}{/each}
  </div>
{:else if view === "families"}
  <div class="color-picker-palette color-picker-palette-families">
    {#each familyGroups as [family, items] (family)}
      <section class="color-picker-family" aria-labelledby={`family-${family}`}>
        <h2 id={`family-${family}`}>{family}</h2>
        <div class="color-picker-family-grid">
          {#each items as group (group.id)}{@render tile(group)}{/each}
        </div>
      </section>
    {/each}
  </div>
{:else if view === "map"}
  <div class="color-picker-map-scroll" tabindex="0" aria-label="Mapa de tono y luminosidad">
    <div class="color-picker-map">
      <span class="color-picker-map-y">Luminosidad ↑</span>
      <span class="color-picker-map-x">Tono →</span>
      {#each mapGroups as group (group.id)}
        <div class="color-picker-map-cell" style={`grid-column: ${group.mapColumn}; grid-row: ${group.mapRow}`}>
          {@render tile(group)}
        </div>
      {/each}
    </div>
  </div>
{/if}
```

- [ ] **Step 4: Wire the page controls and selection**

In `ColorPickerApp.svelte`, import `ColorPalette` and `toggleComparedColor`, then add:

```js
let activeView = "continuous";
let hideOutOfStock = false;
let selectedIds = [];
let referenceHex = "";
let referenceGroupId = "";
let selectionMessage = "";

$: visibleGroups = hideOutOfStock ? groups.filter((group) => group.inStock) : groups;

function selectGroup(group) {
  referenceHex = group.hex;
  referenceGroupId = group.id;
  const result = toggleComparedColor(selectedIds, group.id);
  selectedIds = result.ids;
  selectionMessage = result.message;
}
```

Replace the success-only state paragraph with these controls and palette:

```svelte
<section class="color-picker-controls" aria-label="Organización de la paleta">
  <div class="color-picker-view-tabs">
    {#each [["continuous", "Continuo"], ["families", "Familias"], ["map", "Mapa 2D"]] as [id, label]}
      <button type="button" class:active={activeView === id} aria-pressed={activeView === id} on:click={() => activeView = id}>{label}</button>
    {/each}
  </div>
  <label class="color-picker-stock-toggle">
    <input type="checkbox" bind:checked={hideOutOfStock}>
    <span>Ocultar sin stock</span>
  </label>
</section>

<div class="color-picker-summary">
  <span>{visibleGroups.length} colores</span>
  {#if excludedCount}<span>{excludedCount} productos PLA sin HEX</span>{/if}
</div>

<ColorPalette groups={visibleGroups} view={activeView} {selectedIds} onSelect={selectGroup} />
<p class="sr-only" aria-live="polite">{selectionMessage}</p>
```

- [ ] **Step 5: Add the first scoped layout rules**

Append this block to `src/styles/global.css`:

```css
.color-picker-page { width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 28px 0 56px; }
.color-picker-hero h1 { margin: 4px 0 8px; }
.color-picker-hero p { max-width: 720px; margin: 0; color: var(--muted); }
.color-picker-controls, .color-picker-summary { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 20px; }
.color-picker-view-tabs { display: flex; flex-wrap: wrap; gap: 8px; }
.color-picker-view-tabs button.active { color: var(--surface); background: var(--text); }
.color-picker-stock-toggle { display: inline-flex; align-items: center; gap: 8px; }
.color-picker-palette-continuous, .color-picker-family-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(42px, 1fr)); gap: 4px; margin-top: 12px; }
.color-picker-tile { position: relative; min-width: 0; aspect-ratio: 1; padding: 0; border: 1px solid color-mix(in srgb, var(--line) 72%, var(--picker-color)); background: var(--picker-color); }
.color-picker-tile.without-stock { border-style: dashed; filter: saturate(.58); }
.color-picker-tile[aria-pressed="true"] { outline: 3px solid var(--text); outline-offset: 2px; z-index: 1; }
.color-picker-stock-mark { position: absolute; top: 2px; right: 4px; color: var(--text); text-shadow: 0 1px 2px var(--surface); }
.color-picker-palette-families { display: grid; gap: 20px; margin-top: 16px; }
.color-picker-family h2 { margin: 0; font-size: 1rem; }
.color-picker-map-scroll { overflow-x: auto; margin-top: 12px; }
.color-picker-map { position: relative; display: grid; grid-template-columns: repeat(12, minmax(64px, 1fr)); grid-template-rows: repeat(6, minmax(64px, auto)); gap: 4px; min-width: 820px; padding: 22px 0 20px 30px; }
.color-picker-map-cell { display: flex; flex-wrap: wrap; gap: 3px; min-width: 0; }
.color-picker-map-cell .color-picker-tile { flex: 1 1 30px; }
.color-picker-map-y, .color-picker-map-x { position: absolute; color: var(--muted); font-size: .75rem; }
.color-picker-map-y { top: 0; left: 30px; }
.color-picker-map-x { right: 0; bottom: 0; }
```

- [ ] **Step 6: Verify and commit the palette**

Run the targeted pytest, `npm.cmd run test:color-picker`, and `npm.cmd run build`. Expected: all pass.

```powershell
git add src/components/ColorPalette.svelte src/ColorPickerApp.svelte src/styles/global.css tests/test_frontend_assets.py
git commit -m "feat: add dynamic Color Picker views"
```

---

### Task 4: Three-result similar-color search

**Files:**
- Create: `src/components/SimilarColorSearch.svelte`
- Modify: `src/ColorPickerApp.svelte`
- Modify: `src/styles/global.css`
- Modify: `tests/test_frontend_assets.py`

**Interfaces:**
- Consumes: `findSimilarColors(visibleGroups, hex, excludedGroupId, 3)`, `normalizeHex`, `isValidHex`, and `distanceLabel`.
- Produces: controlled component props `{ hex, results, error, onHexChange, onSearch, onCompare }`; invalid input keeps previous results intact.

- [ ] **Step 1: Add the failing three-results UI contract**

Append to the frontend contract test:

```python
    similar = (ROOT / "src" / "components" / "SimilarColorSearch.svelte").read_text(encoding="utf-8")
    assert 'Buscar colores similares' in similar
    assert 'result.distance.toFixed(1)' in similar
    assert 'onCompare(result.group)' in similar
    assert 'findSimilarColors(visibleGroups, normalized, referenceGroupId, 3)' in app
```

- [ ] **Step 2: Run the contract and verify it fails**

Expected: FAIL because `SimilarColorSearch.svelte` is absent.

- [ ] **Step 3: Create the controlled search component**

Create `src/components/SimilarColorSearch.svelte`:

```svelte
<script>
  import { distanceLabel, normalizeHex } from "../lib/colorPicker.js";

  export let hex = "";
  export let results = [];
  export let error = "";
  export let onHexChange = () => {};
  export let onSearch = () => {};
  export let onCompare = () => {};

  function colorValue() {
    const value = normalizeHex(hex);
    return /^#[0-9A-F]{6}$/.test(value) ? value : "#000000";
  }
</script>

<section class="color-picker-similar" aria-labelledby="similar-title">
  <header>
    <div>
      <span class="eyebrow">CIEDE2000 · CULORI</span>
      <h2 id="similar-title">Buscar colores similares</h2>
      <p>Elegí un cuadrado o ingresá cualquier HEX para ver los tres filamentos más cercanos.</p>
    </div>
    <form on:submit|preventDefault={onSearch}>
      <input type="color" aria-label="Elegir color de referencia" value={colorValue()} on:input={(event) => onHexChange(event.currentTarget.value)}>
      <label>
        <span>HEX de referencia</span>
        <input type="text" maxlength="7" spellcheck="false" value={hex} aria-invalid={error ? "true" : undefined} on:input={(event) => onHexChange(event.currentTarget.value)}>
      </label>
      <button type="submit">Buscar similares</button>
    </form>
  </header>

  {#if error}<p class="color-picker-error" role="alert">{error}</p>{/if}

  {#if results.length}
    <div class="color-picker-similar-results" aria-label={`${results.length} colores similares`}>
      {#each results as result (result.group.id)}
        <article class="color-picker-similar-card" style={`--picker-color: ${result.group.hex}`}>
          <button class="color-picker-similar-swatch" type="button" aria-label={`Comparar ${result.group.name}`} on:click={() => onCompare(result.group)}></button>
          <div>
            <strong>{result.group.name}</strong>
            <span>{result.group.brand} · {result.group.line}</span>
            <span>{result.group.hex} · ΔE {result.distance.toFixed(1)}</span>
          </div>
          <footer>
            <span>{distanceLabel(result.distance)}</span>
            <button type="button" on:click={() => onCompare(result.group)}>Comparar</button>
          </footer>
        </article>
      {/each}
    </div>
  {/if}

  <p class="color-picker-similar-warning">La distancia es orientativa: el acabado, la iluminación, el lote y la pantalla pueden cambiar la percepción del filamento real.</p>
</section>
```

- [ ] **Step 4: Wire controlled search state in the app**

Import `SimilarColorSearch`, `findSimilarColors`, `isValidHex`, and `normalizeHex`. Add:

```js
let similarHex = "";
let similarResults = [];
let similarError = "";
let searchActive = false;

function setSimilarHex(value) {
  similarHex = value;
  referenceGroupId = "";
  similarError = "";
}

function runSimilarSearch() {
  const normalized = normalizeHex(similarHex);
  if (!isValidHex(normalized)) {
    similarError = "Ingresá un HEX válido, por ejemplo #009DCE.";
    return;
  }
  similarHex = normalized;
  similarError = "";
  searchActive = true;
  similarResults = findSimilarColors(visibleGroups, normalized, referenceGroupId, 3);
}

function setHideOutOfStock(value) {
  hideOutOfStock = value;
  if (searchActive) {
    const nextGroups = value ? groups.filter((group) => group.inStock) : groups;
    similarResults = findSimilarColors(nextGroups, similarHex, referenceGroupId, 3);
  }
}
```

In `selectGroup(group)`, add before toggling:

```js
similarHex = group.hex;
similarError = "";
```

Replace `bind:checked` with a controlled stock checkbox:

```svelte
<input type="checkbox" checked={hideOutOfStock} on:change={(event) => setHideOutOfStock(event.currentTarget.checked)}>
```

Render the search immediately before `ColorPalette`:

```svelte
<SimilarColorSearch
  hex={similarHex}
  results={similarResults}
  error={similarError}
  onHexChange={setSimilarHex}
  onSearch={runSimilarSearch}
  onCompare={selectGroup}
/>
```

- [ ] **Step 5: Add exact three-card responsive styling**

Append:

```css
.color-picker-similar { display: grid; gap: 14px; margin-top: 18px; padding: 18px; border: 1px solid var(--line); background: var(--surface-soft); }
.color-picker-similar > header { display: grid; grid-template-columns: minmax(0, 1fr) minmax(360px, 1fr); gap: 20px; align-items: end; }
.color-picker-similar h2 { margin: 3px 0 5px; }
.color-picker-similar p { margin: 0; color: var(--muted); }
.color-picker-similar form { display: grid; grid-template-columns: 48px minmax(140px, 1fr) auto; gap: 8px; align-items: end; }
.color-picker-similar form label { display: grid; gap: 3px; }
.color-picker-similar form label span { font-size: .75rem; color: var(--muted); }
.color-picker-similar input[type="color"] { width: 48px; height: 40px; padding: 2px; }
.color-picker-similar-results { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.color-picker-similar-card { display: grid; grid-template-rows: 84px auto auto; min-width: 0; border: 1px solid var(--line); background: var(--surface); }
.color-picker-similar-swatch { border: 0; background: var(--picker-color); }
.color-picker-similar-card > div { display: grid; gap: 3px; padding: 10px; }
.color-picker-similar-card > div span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: .8rem; color: var(--muted); }
.color-picker-similar-card footer { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 0 10px 10px; }
.color-picker-similar-card footer span { font-size: .75rem; color: var(--muted); }
.color-picker-error { color: var(--warn); }
```

- [ ] **Step 6: Verify and commit the search slice**

Run the targeted pytest, Node test, and build; expect all PASS and exactly three cards for a four-plus-candidate fixture.

```powershell
git add src/components/SimilarColorSearch.svelte src/ColorPickerApp.svelte src/styles/global.css tests/test_frontend_assets.py
git commit -m "feat: find three similar PLA colors"
```

---

### Task 5: Comparator, material renders, and presentation `+1`

**Files:**
- Create: `src/components/ColorComparator.svelte`
- Modify: `src/ColorPickerApp.svelte`
- Modify: `src/lib/quoteList.js`
- Modify: `tests/quoteList.test.js`
- Modify: `src/styles/global.css`
- Modify: `tests/test_frontend_assets.py`

**Interfaces:**
- Consumes: selected logical groups, `rgbFromHex`, `dataUrl`, existing `loadQuoteList`, `initializeQuoteList`, `saveQuoteList`, and `snapshotQuoteItem`.
- Produces: `incrementQuoteListItem(items, product) -> normalizedItems`; `ColorComparator` props `{ groups, addDisabled, onRemove, onAddPresentation }`.

- [ ] **Step 1: Write the failing quote-list increment test**

Add this import and test to `tests/quoteList.test.js`:

```js
import { incrementQuoteListItem } from "../src/lib/quoteList.js";

test("increments one concrete product without changing other quote items", () => {
  const product = {
    id: "pla-rojo-175-1000-grilon3",
    display_name: "Grilon3 PLA Rojo 1 kg",
    material: "PLA",
    color: "Rojo",
    brand: "Grilon3",
    diameter_mm: 1.75,
    weight_g: 1000,
    offers: [{ stock_status: "in_stock", stock_quantity: 2 }],
  };
  const once = incrementQuoteListItem([], product);
  const twice = incrementQuoteListItem(once, product);
  assert.equal(twice.length, 1);
  assert.equal(twice[0].productId, product.id);
  assert.equal(twice[0].quantity, 2);
});
```

- [ ] **Step 2: Run and verify the quote test fails**

Run `npm.cmd run test:quote-list`. Expected: FAIL because `incrementQuoteListItem` is not exported.

- [ ] **Step 3: Add the shared increment helper**

Append to `src/lib/quoteList.js` after `snapshotQuoteItem`:

```js
export function incrementQuoteListItem(items, product) {
  const current = items || [];
  const existing = current.find((item) => item.productId === product.id);
  const quantity = Number(existing?.quantity || 0) + 1;
  return existing
    ? current.map((item) => item.productId === product.id ? snapshotQuoteItem(product, quantity) : item)
    : [...current, snapshotQuoteItem(product, 1)];
}
```

Run `npm.cmd run test:quote-list`. Expected: all quote-list tests PASS.

- [ ] **Step 4: Add the failing comparator contract**

Extend the Python contract with:

```python
    comparator = (ROOT / "src" / "components" / "ColorComparator.svelte").read_text(encoding="utf-8")
    assert 'group.materialSwatchUrl' in comparator
    assert 'rgbFromHex(group.hex)' in comparator
    assert 'onAddPresentation(presentation.product)' in comparator
    assert 'incrementQuoteListItem(quoteItems, product)' in app
    assert 'saveQuoteList({' in app
```

- [ ] **Step 5: Implement `ColorComparator.svelte`**

Create:

```svelte
<script>
  import { rgbFromHex } from "../lib/colorPicker.js";
  import { dataUrl } from "../lib/shared.js";

  export let groups = [];
  export let addDisabled = false;
  export let onRemove = () => {};
  export let onAddPresentation = () => {};
</script>

<section class="color-picker-comparator" aria-labelledby="comparator-title">
  <header>
    <div>
      <h2 id="comparator-title">Comparador</h2>
      <p>Máximo cuatro colores.</p>
    </div>
    <span>{groups.length} / 4</span>
  </header>

  {#if groups.length}
    <div class="color-picker-comparator-grid">
      {#each groups as group (group.id)}
        {@const rgb = rgbFromHex(group.hex)}
        <article class="color-picker-compare-card" style={`--picker-color: ${group.hex}`}>
          <header>
            <div><strong>{group.name}</strong><span>{group.brand} · {group.line}</span></div>
            <button type="button" aria-label={`Quitar ${group.name} del comparador`} on:click={() => onRemove(group)}>×</button>
          </header>
          <div class="color-picker-material-render">
            <span class="color-picker-render-fallback" aria-label={`Muestra plana ${group.hex}`}></span>
            {#if group.materialSwatchUrl}
              <img src={dataUrl(group.materialSwatchUrl)} alt={`Render de material para ${group.brand} ${group.name}`} on:error={(event) => event.currentTarget.hidden = true}>
            {/if}
          </div>
          <dl>
            <div><dt>HEX</dt><dd>{group.hex}</dd></div>
            <div><dt>RGB</dt><dd>{rgb.r}, {rgb.g}, {rgb.b}</dd></div>
            <div><dt>Pantone</dt><dd>{group.pantone || "Color estimado"}</dd></div>
            <div><dt>Stock</dt><dd>{group.inStock ? "Disponible" : "Sin stock"}</dd></div>
          </dl>
          {#if group.estimated && group.warning}<p class="color-picker-estimate-warning">{group.warning}</p>{/if}
          <div class="color-picker-presentations">
            <span>Presentaciones</span>
            {#each group.presentations as presentation (presentation.id)}
              <button type="button" disabled={addDisabled} on:click={() => onAddPresentation(presentation.product)}>
                <span>{presentation.label}{presentation.inStock ? "" : " · sin stock"}</span><strong>+1</strong>
              </button>
            {/each}
          </div>
        </article>
      {/each}
    </div>
  {:else}
    <p class="color-picker-empty-comparator">Seleccioná cuadrados de la paleta o resultados similares para comparar.</p>
  {/if}
</section>
```

- [ ] **Step 6: Initialize and persist quote state in `ColorPickerApp.svelte`**

Import `ColorComparator` and these quote helpers:

```js
import {
  incrementQuoteListItem,
  initializeQuoteList,
  loadQuoteList,
  saveQuoteList,
} from "./lib/quoteList.js";
```

Add state:

```js
let products = [];
let quoteItems = [];
let quoteSettings = { showQuickControls: false };
let quoteReadOnly = false;
let preservedQuotePayload = null;
let quoteMessage = "";
let quoteWarning = "";

$: selectedGroups = selectedIds.map((id) => groups.find((group) => group.id === id)).filter(Boolean);
```

Inside successful `loadCatalog()`, before setting `loading = false`, initialize from the same catalog result:

```js
products = payload.products;
const loadedQuote = loadQuoteList();
const reconciled = initializeQuoteList(loadedQuote, { ok: true, products });
quoteItems = reconciled.items;
quoteSettings = reconciled.settings;
quoteReadOnly = loadedQuote.readOnly;
preservedQuotePayload = loadedQuote.preservedPayload;
if (reconciled.shouldSave) {
  saveQuoteList({
    items: quoteItems,
    settings: quoteSettings,
    readOnly: quoteReadOnly,
    preservedPayload: preservedQuotePayload,
  });
}
quoteWarning = loadedQuote.readOnly
  ? "La lista guardada usa una versión más nueva. La conservamos sin cambios."
  : (loadedQuote.storageAvailable ? "" : "No pudimos guardar la lista; los cambios durarán sólo durante esta sesión.");
```

Add actions:

```js
function removeComparedGroup(group) {
  const result = toggleComparedColor(selectedIds, group.id);
  selectedIds = result.ids;
  selectionMessage = result.message;
}

function addPresentation(product) {
  if (quoteReadOnly) return;
  quoteItems = incrementQuoteListItem(quoteItems, product);
  const saveResult = saveQuoteList({
    items: quoteItems,
    settings: quoteSettings,
    readOnly: quoteReadOnly,
    preservedPayload: preservedQuotePayload,
  });
  const current = quoteItems.find((item) => item.productId === product.id);
  quoteMessage = `${current.productName} · ${current.presentation}: ${current.quantity} unidad(es) en la lista.`;
  if (!saveResult.ok && !saveResult.blocked) quoteWarning = "No pudimos guardar la lista; los cambios durarán sólo durante esta sesión.";
}
```

Render after the palette:

```svelte
<ColorComparator
  groups={selectedGroups}
  addDisabled={quoteReadOnly}
  onRemove={removeComparedGroup}
  onAddPresentation={addPresentation}
/>
{#if quoteWarning}<p class="color-picker-quote-warning" role="status">{quoteWarning}</p>{/if}
<p class="sr-only" aria-live="polite">{quoteMessage}</p>
```

- [ ] **Step 7: Add comparator styling**

Append:

```css
.color-picker-comparator { display: grid; gap: 14px; margin-top: 28px; padding-top: 20px; border-top: 1px solid var(--line); }
.color-picker-comparator > header, .color-picker-compare-card > header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
.color-picker-comparator h2, .color-picker-comparator p { margin: 0; }
.color-picker-comparator-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.color-picker-compare-card { display: grid; align-content: start; gap: 12px; min-width: 0; padding: 12px; border: 1px solid var(--line); background: var(--surface-soft); }
.color-picker-compare-card > header > div { display: grid; gap: 2px; }
.color-picker-compare-card > header span { color: var(--muted); font-size: .8rem; }
.color-picker-material-render { position: relative; display: grid; place-items: center; min-height: 160px; overflow: hidden; background: color-mix(in srgb, var(--picker-color) 18%, var(--surface)); }
.color-picker-material-render img, .color-picker-render-fallback { grid-area: 1 / 1; width: 100%; height: 160px; }
.color-picker-material-render img { position: relative; object-fit: contain; }
.color-picker-render-fallback { background: var(--picker-color); }
.color-picker-compare-card dl { display: grid; gap: 6px; margin: 0; }
.color-picker-compare-card dl div { display: flex; justify-content: space-between; gap: 8px; padding-bottom: 5px; border-bottom: 1px solid var(--line); }
.color-picker-compare-card dd { margin: 0; text-align: right; }
.color-picker-presentations { display: grid; gap: 6px; }
.color-picker-presentations > span { color: var(--muted); font-size: .8rem; }
.color-picker-presentations button { display: flex; justify-content: space-between; gap: 8px; width: 100%; }
.color-picker-estimate-warning, .color-picker-quote-warning { font-size: .8rem; color: var(--muted); }
```

- [ ] **Step 8: Verify and commit the comparator slice**

Run:

```powershell
npm.cmd run test:quote-list
npm.cmd run test:color-picker
python -m pytest tests/test_frontend_assets.py -v --basetemp C:\tmp\pytest-color-picker-comparator
npm.cmd run build
```

Expected: all commands exit 0 and the Vite build keeps four HTML entries.

```powershell
git add src/components/ColorComparator.svelte src/ColorPickerApp.svelte src/lib/quoteList.js tests/quoteList.test.js src/styles/global.css tests/test_frontend_assets.py
git commit -m "feat: compare colors and add presentations"
```

---

### Task 6: Responsive, accessibility, and end-to-end verification

**Files:**
- Modify: `src/styles/global.css`
- Modify: `tests/test_frontend_assets.py`

**Interfaces:**
- Consumes: the completed page and all component contracts.
- Produces: keyboard-visible tooltips/focus, mobile layouts, static asset assertions, and recorded verification evidence.

- [ ] **Step 1: Add the final failing static accessibility/style contract**

Extend `test_color_picker_page_is_linked_and_built`:

```python
    styles = (ROOT / "src" / "styles" / "global.css").read_text(encoding="utf-8")
    assert 'data-tooltip' in palette
    assert 'aria-live="polite"' in app
    assert '@media (max-width: 760px)' in styles
    assert '.color-picker-tile:focus-visible::after' in styles
    assert 'grid-template-columns: repeat(2, minmax(0, 1fr))' in styles
    assert 'grid-template-columns: minmax(0, 1fr)' in styles
```

- [ ] **Step 2: Run the targeted contract and verify it fails**

Expected: FAIL on the missing responsive/focus selectors.

- [ ] **Step 3: Add final focus and responsive rules**

Append exactly:

```css
.color-picker-tile::after { content: attr(data-tooltip); position: absolute; left: 50%; bottom: calc(100% + 7px); z-index: 20; width: max-content; max-width: 240px; padding: 6px 8px; color: var(--surface); background: var(--text); font-size: .75rem; line-height: 1.25; opacity: 0; pointer-events: none; transform: translate(-50%, 4px); transition: opacity .14s ease, transform .14s ease; }
.color-picker-tile:hover::after, .color-picker-tile:focus-visible::after { opacity: 1; transform: translate(-50%, 0); }
.color-picker-tile:focus-visible, .color-picker-similar button:focus-visible, .color-picker-comparator button:focus-visible { outline: 3px solid var(--text); outline-offset: 2px; }

@media (max-width: 900px) {
  .color-picker-comparator-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .color-picker-similar > header { grid-template-columns: minmax(0, 1fr); }
}

@media (max-width: 760px) {
  .color-picker-page { width: min(100% - 20px, 1180px); padding-top: 20px; }
  .color-picker-controls { align-items: flex-start; flex-direction: column; }
  .color-picker-palette-continuous, .color-picker-family-grid { grid-template-columns: repeat(auto-fill, minmax(34px, 1fr)); }
  .color-picker-similar-results { grid-template-columns: minmax(0, 1fr); }
}

@media (max-width: 460px) {
  .color-picker-similar form { grid-template-columns: 46px minmax(0, 1fr); }
  .color-picker-similar form button { grid-column: 1 / -1; }
  .color-picker-comparator-grid { grid-template-columns: minmax(0, 1fr); }
}

@media (prefers-reduced-motion: reduce) {
  .color-picker-tile::after { transition: none; }
}
```

- [ ] **Step 4: Run all automated verification**

Run in this order:

```powershell
npm.cmd run test:color-picker
npm.cmd run test:quote-list
npm.cmd run build
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos-color-picker
git diff --check
git status --short
```

Expected:

- Color Picker Node tests: all PASS.
- Existing quote-list Node tests: all PASS.
- Vite build: exit 0 with `dist/color-picker.html`, `dist/index.html`, `dist/resumen.html`, and `dist/estadisticas.html`.
- pytest: 133 or more tests PASS, 0 failures/errors.
- `git diff --check`: no output.
- `git status --short`: only the intended Task 6 files before commit.

- [ ] **Step 5: Review the real page in Chrome**

Start the local server:

```powershell
npm.cmd run dev
```

Use Chrome, not the integrated browser, and verify at desktop and mobile widths:

1. `color-picker.html` loads the published PLA dataset and starts in Continuo.
2. Familias and Mapa 2D remain interactive and contain the same visible logical colors.
3. `Ocultar sin stock` reduces both the palette and an active similarity result set.
4. Clicking a tile sets the HEX reference and toggles comparison.
5. A valid free HEX returns at most 3 CIEDE2000 results; invalid input preserves previous results and shows `aria-invalid`.
6. A fifth comparison is rejected with the accessible message.
7. Comparison cards show actual v2 material renders where available and flat fallback where absent.
8. Each presentation `+1` increments the exact `product.id`; reloading the catalog page shows the persisted quantity.
9. Keyboard Tab exposes the same tile description as mouse hover.
10. No horizontal page overflow occurs on mobile; only the 2D map owns horizontal scrolling.

- [ ] **Step 6: Commit the verified responsive finish**

```powershell
git add src/styles/global.css tests/test_frontend_assets.py
git commit -m "test: verify responsive Color Picker flow"
```

- [ ] **Step 7: Confirm the worktree is ready for review**

Run:

```powershell
git status --short --branch
git log --oneline --decorate -6
```

Expected: clean `codex/color-picker` worktree with the design/spec commits followed by six implementation commits.


