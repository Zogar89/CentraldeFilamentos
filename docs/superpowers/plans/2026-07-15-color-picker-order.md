# Color Picker Order Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reordenar la vista Continua del Color Picker en franjas perceptuales dinámicas para que los cromáticos, apagados, tierras y neutros no se mezclen.

**Architecture:** `src/lib/colorPicker.js` conserva toda la clasificación OKLCH en funciones puras y entrega las cuatro franjas ordenadas. `ColorPalette.svelte` consume esas franjas para renderizar cuatro grillas semánticas sin tocar la selección, la disponibilidad ni la comparación.

**Tech Stack:** Svelte 5, JavaScript ES modules, Culori 4, Node `node:test`, pytest y Vite.

## Global Constraints

- El sitio es estático en GitHub Pages; no se agregan endpoints ni persistencia remota.
- El orden se deriva en runtime desde el HEX actual con Culori; no hay posiciones manuales o estáticas.
- La identidad del color sigue siendo marca + línea + nombre y no incluye presentación, peso ni diámetro.
- `Ocultar sin stock` se aplica antes de las franjas visuales.
- Mantener JavaScript con 2 espacios, dobles comillas y punto y coma.
- Verificar en Windows con `npm.cmd` y `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos`.

---

### Task 1: Clasificar y ordenar las franjas perceptuales

**Files:**
- Modify: `src/lib/colorPicker.js`
- Test: `tests/colorPicker.test.js`

**Interfaces:**
- Consumes: grupos lógicos con `{ id, hex }` válidos.
- Produces: `colorOrderBand(group)` que retorna `"intense" | "muted" | "earth" | "neutral"` y `groupContinuousBands(groups)` que retorna un `Map` ordenado con esas cuatro claves y los grupos ordenados.

- [ ] **Step 1: Write the failing test**

```js
test("separates the continuous palette into intense, muted, earth, and neutral bands", () => {
  const groups = buildPlaColorCatalog([
    product({ id: "red", color: "Rojo", pantone_hex: "#E63424" }),
    product({ id: "pastel", color: "Pastel", pantone_hex: "#DFA0BA" }),
    product({ id: "earth", color: "Tierra", pantone_hex: "#7B432D" }),
    product({ id: "white", color: "Blanco", pantone_hex: "#FBFAF4" }),
    product({ id: "black", color: "Negro", pantone_hex: "#17191C" }),
  ]).groups;
  const bands = groupContinuousBands(groups);

  assert.deepEqual([...bands.keys()], ["intense", "muted", "earth", "neutral"]);
  assert.equal(colorOrderBand(groups.find((group) => group.id.includes("red"))), "intense");
  assert.equal(colorOrderBand(groups.find((group) => group.id.includes("pastel"))), "muted");
  assert.equal(colorOrderBand(groups.find((group) => group.id.includes("earth"))), "earth");
  assert.deepEqual(bands.get("neutral").map((group) => group.id), ["grilon3-pla-blanco", "grilon3-pla-negro"]);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm.cmd run test:color-picker`

Expected: FAIL because `groupContinuousBands` and `colorOrderBand` are not exported.

- [ ] **Step 3: Write minimal implementation**

```js
const continuousBandOrder = ["intense", "muted", "earth", "neutral"];

export function colorOrderBand(group) {
  const { l, c, h } = oklchFor(group);
  if (c < 0.035) return "neutral";
  if (h >= 15 && h < 85 && l < 0.62 && c < 0.11) return "earth";
  return c >= 0.11 ? "intense" : "muted";
}

export function groupContinuousBands(groups) {
  const result = new Map(continuousBandOrder.map((band) => [band, []]));
  for (const group of groups || []) result.get(colorOrderBand(group)).push(group);
  for (const [band, items] of result) {
    items.sort((left, right) => {
      const a = oklchFor(left);
      const b = oklchFor(right);
      if (band === "neutral") return b.l - a.l || left.id.localeCompare(right.id, "es-AR");
      return a.h - b.h || b.l - a.l || b.c - a.c || left.id.localeCompare(right.id, "es-AR");
    });
    if (!items.length) result.delete(band);
  }
  return result;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm.cmd run test:color-picker`

Expected: all Color Picker tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/lib/colorPicker.js tests/colorPicker.test.js
git commit -m "feat: group color picker palette bands"
```

### Task 2: Renderizar las cuatro franjas en la vista Continua

**Files:**
- Modify: `src/components/ColorPalette.svelte`
- Modify: `src/styles/global.css`
- Test: `tests/test_frontend_assets.py`

**Interfaces:**
- Consumes: `groupContinuousBands(groups)` desde `src/lib/colorPicker.js`.
- Produces: secciones `color-picker-continuous-band` con título y la misma interacción de cada `color-picker-tile`.

- [ ] **Step 1: Write the failing test**

```python
assert "groupContinuousBands" in palette
assert "color-picker-continuous-band" in palette
assert "Rueda cromática intensa" in palette
assert "Claros y apagados" in palette
assert "Tierras y marrones" in palette
assert "Neutros" in palette
assert ".color-picker-continuous-band" in styles
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_frontend_assets.py::test_color_picker_page_is_linked_and_built -q --basetemp C:\tmp\pytest-centraldefilamentos-order`

Expected: FAIL because the continuous-band component and styles do not exist.

- [ ] **Step 3: Write minimal implementation**

```svelte
{:if view === "continuous"}
  <div class="color-picker-palette color-picker-palette-continuous">
    {#each continuousBands as [band, items] (band)}
      <section class="color-picker-continuous-band" aria-labelledby={`continuous-band-${band}`}>
        <h2 id={`continuous-band-${band}`}>{continuousBandLabel(band)}</h2>
        <div class="color-picker-continuous-grid">
          {#each items as group (group.id)}{@render tile(group)}{/each}
        </div>
      </section>
    {/each}
  </div>
{/if}
```

```css
.color-picker-palette-continuous { display: grid; gap: 20px; margin-top: 16px; }
.color-picker-continuous-band { display: grid; gap: 8px; }
.color-picker-continuous-band h2 { margin: 0; font-size: 1rem; }
.color-picker-continuous-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(42px, 1fr)); gap: 4px; }
```

- [ ] **Step 4: Run tests and build to verify it passes**

Run: `npm.cmd run test:color-picker && python -m pytest tests/test_frontend_assets.py -q --basetemp C:\tmp\pytest-centraldefilamentos-order && npm.cmd run build`

Expected: tests pass and Vite emits `dist/color-picker.html`.

- [ ] **Step 5: Commit**

```powershell
git add src/components/ColorPalette.svelte src/styles/global.css tests/test_frontend_assets.py
git commit -m "feat: render ordered color picker bands"
```

## Final Verification

- [ ] Run `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos-order-final` and confirm 133 tests pass or more if new tests are added.
- [ ] Run `npm.cmd run test:color-picker && npm.cmd run test:quote-list && npm.cmd run build`.
- [ ] Review `http://127.0.0.1:5174/CentraldeFilamentos/color-picker.html` in Chrome: four blocks in `Continuo`, all colors retained, `Ocultar sin stock` preserves order, and the other two views still render.
