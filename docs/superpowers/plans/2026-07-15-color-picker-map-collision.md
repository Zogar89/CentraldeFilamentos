# Mapa 2D sin superposición del Color Picker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mostrar todos los colores PLA del mapa 2D sin que los que comparten tono y luminosidad queden ocultos uno debajo de otro.

**Architecture:** `src/lib/colorPicker.js` seguirá siendo el único lugar que transforma HEX en datos perceptuales. `buildColorMap` devolverá puntos continuos con coordenada ancla, diámetro y posición final después de una separación determinista; `ColorPalette.svelte` los dibujará sobre un plano relativo sin celdas discretas.

**Tech Stack:** Svelte 5, JavaScript ES modules, Culori 4, CSS, Node test runner y Vite.

## Global Constraints

- La posición, tamaño y separación se derivan del HEX actual con Culori; no se guardan posiciones manuales.
- X representa tono, Y representa luminosidad y el tamaño representa croma con límites visuales legibles.
- Ningún punto puede quedar fuera del plano ni coincidir exactamente con otro punto que tenga la misma ancla.
- Se conservan tooltip, selección, estado sin stock y acceso al comparador.
- El sitio sigue siendo estático y debe compilar con `npm.cmd run build` en Windows.

---

### Task 1: Modelo de puntos perceptuales con separación determinista

**Files:**
- Modify: `src/lib/colorPicker.js:193-208`
- Modify: `tests/colorPicker.test.js:1-103`

**Interfaces:**
- Consumes: `groups: Array<{ id: string, hex: string }>` y la conversión privada `oklchFor(group)`.
- Produces: `buildColorMap(groups): Array<{ id: string, hex: string, oklch: { l: number, c: number, h: number }, mapX: number, mapY: number, mapSize: number }>` ordenada por `mapY`, `mapX` e `id`.

- [ ] **Step 1: Escribir el test que expone la colisión actual**

```js
test("separates perceptual map points that share a tone and luminosity anchor", () => {
  const groups = buildPlaColorCatalog([
    product({ id: "red-a", color: "Rojo A", pantone_hex: "#CC3333" }),
    product({ id: "red-b", color: "Rojo B", pantone_hex: "#CC3333" }),
    product({ id: "white", color: "Blanco", pantone_hex: "#F7F7F7" }),
  ]).groups;
  const points = buildColorMap(groups);

  assert.equal(points.length, 3);
  assert.ok(points.every((point) => point.mapX >= 0 && point.mapX <= 100));
  assert.ok(points.every((point) => point.mapY >= 0 && point.mapY <= 100));
  assert.ok(points.every((point) => point.mapSize >= 12 && point.mapSize <= 24));
  assert.notDeepEqual(
    [points[0].mapX, points[0].mapY],
    [points[1].mapX, points[1].mapY],
  );
});
```

- [ ] **Step 2: Ejecutar el test y confirmar que falla**

Run: `node --test tests/colorPicker.test.js`

Expected: FAIL porque `buildColorMap` todavía devuelve `mapColumn` y `mapRow`, no `mapX`, `mapY` ni `mapSize`.

- [ ] **Step 3: Implementar anclas continuas, tamaño y separación**

```js
function clamp(value, lower, upper) {
  return Math.min(upper, Math.max(lower, value));
}

function mapAnchor(value) {
  return {
    x: value.c < 0.035 ? 96 : value.h / 3.6,
    y: 100 - value.l * 100,
  };
}

function separateMapPoints(points) {
  const ordered = points.slice().sort((left, right) => (
    left.anchorY - right.anchorY || left.anchorX - right.anchorX || left.id.localeCompare(right.id, "es-AR")
  ));
  const placed = [];
  for (const point of ordered) {
    let candidate = { x: point.anchorX, y: point.anchorY };
    for (let attempt = 0; attempt < 48; attempt += 1) {
      const collides = placed.some((other) => Math.hypot(candidate.x - other.mapX, candidate.y - other.mapY) < 3.4);
      if (!collides) break;
      const angle = (attempt + 1) * 2.399963;
      const radius = 2 + Math.floor(attempt / 6) * 1.5;
      candidate = {
        x: clamp(point.anchorX + Math.cos(angle) * radius, 2, 98),
        y: clamp(point.anchorY + Math.sin(angle) * radius, 2, 98),
      };
    }
    placed.push({ ...point, mapX: candidate.x, mapY: candidate.y });
  }
  return placed;
}

export function buildColorMap(groups) {
  const points = (groups || []).map((group) => {
    const oklch = oklchFor(group);
    const anchor = mapAnchor(oklch);
    return { ...group, oklch, anchorX: anchor.x, anchorY: anchor.y, mapSize: clamp(12 + oklch.c * 55, 12, 24) };
  });
  return separateMapPoints(points).sort((left, right) => left.mapY - right.mapY || left.mapX - right.mapX || left.id.localeCompare(right.id, "es-AR"));
}
```

- [ ] **Step 4: Ejecutar los tests unitarios**

Run: `node --test tests/colorPicker.test.js`

Expected: PASS; todos los tests de `colorPicker` pasan y las muestras cercanas ya no comparten posición final.

- [ ] **Step 5: Commit**

```bash
git add src/lib/colorPicker.js tests/colorPicker.test.js
git commit -m "feat: separate perceptual color map points"
```

### Task 2: Plano 2D de puntos responsivo y verificable

**Files:**
- Modify: `src/components/ColorPalette.svelte:67-77`
- Modify: `src/styles/global.css:115-121`
- Modify: `tests/test_frontend_assets.py`

**Interfaces:**
- Consumes: `mapGroups` desde `buildColorMap(groups)`, con `mapX`, `mapY` y `mapSize` en porcentaje.
- Produces: botones individuales posicionados en el plano `.color-picker-map`, con las mismas acciones del fragmento `tile(group)`.

- [ ] **Step 1: Escribir la comprobación estática que falla**

```python
def test_color_picker_map_uses_dynamic_point_coordinates() -> None:
    source = Path("src/components/ColorPalette.svelte").read_text(encoding="utf-8")
    css = Path("src/styles/global.css").read_text(encoding="utf-8")

    assert "left: ${group.mapX}%" in source
    assert "top: ${group.mapY}%" in source
    assert "--map-size: ${group.mapSize}px" in source
    assert ".color-picker-map-point" in css
```

- [ ] **Step 2: Ejecutar la comprobación y confirmar que falla**

Run: `python -m pytest tests/test_frontend_assets.py -v --basetemp C:\\tmp\\pytest-centraldefilamentos`

Expected: FAIL porque el componente todavía usa `grid-column` y `grid-row`.

- [ ] **Step 3: Reemplazar celdas por botones posicionados**

```svelte
<div class="color-picker-map-scroll">
  <div class="color-picker-map" aria-label="Mapa perceptual de colores PLA">
    <span class="color-picker-map-y">Luminosidad ↑</span>
    <span class="color-picker-map-x">Tono →</span>
    <span class="color-picker-map-note">Tamaño = intensidad</span>
    {#each mapGroups as group (group.id)}
      <div
        class="color-picker-map-point"
        style={`left: ${group.mapX}%; top: ${group.mapY}%; --map-size: ${group.mapSize}px`}
      >
        {@render tile(group)}
      </div>
    {/each}
  </div>
</div>
```

```css
.color-picker-map { position: relative; min-width: 820px; min-height: 520px; margin-top: 12px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }
.color-picker-map-point { position: absolute; transform: translate(-50%, -50%); width: var(--map-size); height: var(--map-size); }
.color-picker-map-point .color-picker-tile { width: 100%; height: 100%; min-height: 0; border-radius: 999px; }
.color-picker-map-note { position: absolute; right: 0; top: 0; color: var(--muted); font-size: .75rem; }
```

- [ ] **Step 4: Ejecutar las pruebas y la compilación**

Run: `python -m pytest tests/test_frontend_assets.py -v --basetemp C:\\tmp\\pytest-centraldefilamentos && node --test tests/colorPicker.test.js && npm.cmd run build`

Expected: PASS; la prueba de recursos, los tests del selector y el build de Vite finalizan correctamente.

- [ ] **Step 5: Revisar en Chrome local**

Run: `npm.cmd run dev -- --host 127.0.0.1 --port 5174`

Expected: al abrir `http://127.0.0.1:5174/CentraldeFilamentos/color-picker.html`, la vista `Mapa 2D` muestra todos los puntos sin superposición y permite seleccionar un color.

- [ ] **Step 6: Commit**

```bash
git add src/components/ColorPalette.svelte src/styles/global.css tests/test_frontend_assets.py
git commit -m "feat: render collision-free color map"
```
