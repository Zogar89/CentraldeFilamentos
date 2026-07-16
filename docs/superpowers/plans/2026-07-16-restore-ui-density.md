# Restore Compact UI Density Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restaurar la densidad compacta aprobada en Resumen y Color Picker sin perder las correcciones funcionales, responsive y de accesibilidad incorporadas por la auditoría UI.

**Architecture:** La restauración se limita a contratos Playwright de geometría visible y a reglas de `src/styles/global.css`; los componentes Svelte y la lógica de negocio permanecen sin cambios. Los contratos separan tamaño visual compacto de área táctil: controles visibles relevantes respetan un mínimo de 24 px y los puntos del mapa mantienen su hitbox invisible de 44 px.

**Tech Stack:** Svelte 5, CSS, Vite 8.0.16, Playwright 1.61 con Chrome, pytest.

## Global Constraints

- El contenido principal no puede superar 1180 px en viewports 2K o 4K.
- La banda de líneas rápidas mide 43 px en desktop y 48 px en móvil.
- Los chips de líneas rápidas miden como máximo 30 px en desktop y 32 px en móvil.
- Las campanas de stock visibles miden 24 x 24 px.
- Los botones `+1` miden 42 x 28 px en desktop y 40 x 36 px en móvil.
- Los tiles de Color Picker usan tracks mínimos de 42 px en desktop y 34 px en móvil.
- Los puntos del mapa perceptual conservan un hitbox de 44 x 44 px y su tamaño visual variable mediante `::before`.
- Se conservan foco, teclado, Escape, devolución de foco, contraste AA, tooltip acotado, breakpoint de 860 px, modal móvil horizontal, totales móviles y prevención de overflow.
- No se agregan dependencias ni se cambia la lógica Svelte.
- En Windows, pytest se ejecuta con `--basetemp C:\tmp\pytest-centraldefilamentos`.

---

## File Structure

- Modify: `tests/e2e/touch-targets.spec.js` — reemplaza el contrato universal de 44 px por contratos WCAG 2.5.8 y métricas de densidad visibles.
- Modify: `tests/e2e/responsive.spec.js` — comprueba el ancho máximo del contenido en 2K y 4K además de overflow y recortes.
- Modify: `tests/test_frontend_assets.py` — fija los tokens CSS críticos para detectar regresiones sin depender sólo del navegador.
- Modify: `src/styles/global.css` — restaura exclusivamente dimensiones anteriores y elimina la expansión ultrawide.
- Create: `docs/qa/2026-07-16-ui-density-verification.md` — registra comandos, viewports, capturas y estado de publicación.

### Task 1: Density and Responsive Contracts

**Files:**
- Modify: `tests/e2e/touch-targets.spec.js`
- Modify: `tests/e2e/responsive.spec.js`
- Modify: `tests/test_frontend_assets.py`

**Interfaces:**
- Consumes: selectores CSS existentes de Resumen, Color Picker, drawer y modal.
- Produces: contratos automatizados para `dimensions(locator)`, ancho máximo, mínimo interactivo de 24 px y tamaños compactos exactos.

- [ ] **Step 1: Replace the universal 44 px audit with the WCAG 2.5.8 minimum**

En `tests/e2e/touch-targets.spec.js`, conservar `dimensions()` y reemplazar `routeSelectors` y el primer bloque parametrizado por:

```js
const routeSelectors = [
  ["summary", "./", [
    ".view-switch .nav-link",
    ".filters input",
    ".filters select",
    ".more-filters-button",
    ".quick-line",
    ".summary-media-button",
    ".summary-stock-watch",
    ".summary-quote-add",
    ".quote-import-help-tip",
    ".provider-mark",
  ]],
  ["color picker", "./color-picker.html", [
    ".view-switch .nav-link",
    ".color-picker-view-tabs button",
    ".color-picker-similar form button",
    ".color-picker-similar form input",
    ".color-picker-tile",
  ]],
];

for (const [name, path, selectors] of routeSelectors) {
  test(`${name} primary controls are at least 24 by 24 CSS pixels`, async ({ page }) => {
    await page.goto(path);
    await waitForStablePage(page);

    const undersized = await page.evaluate((targetSelectors) => targetSelectors.flatMap((selector) =>
      [...document.querySelectorAll(selector)]
        .filter((element) => {
          const style = getComputedStyle(element);
          const rect = element.getBoundingClientRect();
          return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
        })
        .map((element) => {
          const rect = element.getBoundingClientRect();
          return { selector, label: element.getAttribute("aria-label") || element.textContent.trim(), width: rect.width, height: rect.height };
        })
        .filter(({ width, height }) => width < 23.5 || height < 23.5)
    ), selectors);

    expect(undersized).toEqual([]);
  });
}
```

- [ ] **Step 2: Add exact compact-density browser contracts**

Agregar al mismo archivo:

```js
test("summary restores compact visible controls", async ({ page }, testInfo) => {
  await page.goto("./");
  await waitForStablePage(page);

  const mobile = testInfo.project.name.startsWith("mobile-");
  const quickLine = await dimensions(page.locator(".quick-line").first());
  const stockWatch = await dimensions(page.locator(".summary-stock-watch").first());
  const quoteAdd = await dimensions(page.locator(".summary-quote-add").first());

  expect(quickLine.height).toBeLessThanOrEqual(mobile ? 32.5 : 30.5);
  expect(quickLine.height).toBeGreaterThanOrEqual(23.5);
  expect(stockWatch.width).toBeCloseTo(24, 0);
  expect(stockWatch.height).toBeCloseTo(24, 0);
  expect(quoteAdd.width).toBeCloseTo(mobile ? 40 : 42, 0);
  expect(quoteAdd.height).toBeCloseTo(mobile ? 36 : 28, 0);
});

test("compact overlay controls retain their intended size", async ({ page }, testInfo) => {
  await page.goto("./");
  await waitForStablePage(page);
  await page.locator(".summary-quote-add").first().click();

  const mobile = testInfo.project.name.startsWith("mobile-");
  const removeButton = page.getByRole("dialog", { name: "Lista de cotizacion" }).locator(".quote-list-remove").first();
  const drawerClose = page.getByRole("button", { name: "Cerrar lista de cotizacion" });
  await expect(removeButton).toBeVisible();
  expect(await dimensions(removeButton)).toEqual(expect.objectContaining({ width: mobile ? 40 : 28, height: mobile ? 40 : 28 }));
  expect(await dimensions(drawerClose)).toEqual(expect.objectContaining({ width: mobile ? 40 : 32, height: mobile ? 40 : 32 }));

  await drawerClose.click();
  await page.locator(".summary-media-button").first().click();
  const imageClose = page.getByRole("button", { name: "Cerrar imagen ampliada" });
  await expect(imageClose).toBeVisible();
  expect(await dimensions(imageClose)).toEqual(expect.objectContaining({ width: 30, height: 30 }));
});
```

Conservar sin cambios el test `color-map points expose 44px touch areas`.

- [ ] **Step 3: Add the ultrawide width assertion**

En `tests/e2e/responsive.spec.js`, después del bloque que verifica `#main-content`, agregar:

```js
if (["desktop-4k", "desktop-2k"].includes(test.info().project.name)) {
  const mainWidth = await page.locator("#main-content").evaluate((element) => element.getBoundingClientRect().width);
  expect.soft(mainWidth, `${name} main width`).toBeLessThanOrEqual(1180.5);
}
```

- [ ] **Step 4: Add source-level CSS regression checks**

Agregar a `tests/test_frontend_assets.py`:

```python
def test_ui_density_tokens_remain_compact():
    css = (SRC / "styles" / "global.css").read_text(encoding="utf-8")

    assert "--quick-lines-height: 43px" in css
    assert "--quick-lines-height: 48px" in css
    assert ".summary-stock-watch {" in css
    assert "minmax(42px, 1fr)" in css
    assert "minmax(34px, 1fr)" in css
    assert "@media (min-width: 1800px)" not in css
    assert "max-width: 1920px" not in css
```

- [ ] **Step 5: Run focused tests and verify they fail for the current oversized UI**

Run:

```powershell
python -m pytest tests/test_frontend_assets.py -v --basetemp C:\tmp\pytest-centraldefilamentos
npx playwright test tests/e2e/touch-targets.spec.js tests/e2e/responsive.spec.js --project=desktop-4k --project=desktop-1080 --project=mobile-390
```

Expected: pytest fails on the 43/48 px and 42/34 px tokens; Playwright fails on 1920 px ultrawide width, 44/56 px chips and 44 px bells/buttons.

- [ ] **Step 6: Commit the failing contracts**

```powershell
git add tests/e2e/touch-targets.spec.js tests/e2e/responsive.spec.js tests/test_frontend_assets.py
git commit -m "test: define compact UI density contracts"
```

### Task 2: Restore Compact CSS Metrics

**Files:**
- Modify: `src/styles/global.css`

**Interfaces:**
- Consumes: the selectors and exact metrics asserted by Task 1.
- Produces: compact geometry while preserving all semantics and behavior in Svelte.

- [ ] **Step 1: Restore root, Color Picker and navigation metrics**

Aplicar estos cambios exactos en `src/styles/global.css`:

```css
:root {
  --quick-lines-height: 43px;
}

.color-picker-family-grid,
.color-picker-continuous-grid {
  grid-template-columns: repeat(auto-fill, minmax(42px, 1fr));
}

.color-picker-tile {
  min-width: 0;
  min-height: 0;
}

.color-picker-similar input[type="color"] {
  width: 48px;
  min-height: 0;
  height: 40px;
}

.view-switch .nav-link {
  min-height: 0;
}
```

No modificar `.color-picker-map-point`, su botón de 44 px ni el `::before` que dibuja el punto visible.

- [ ] **Step 2: Restore quick-line and desktop overlay metrics**

Cambiar las declaraciones existentes a:

```css
.quick-line { min-height: 30px; }
.more-filters-button { min-height: 38px; }
.quote-list-drawer-close { width: 32px; height: 32px; }
.quote-list-item-title { grid-template-columns: minmax(0, 1fr) 28px; }
.quote-list-remove { width: 28px; height: 28px; }
.image-preview-close { width: 30px; height: 30px; }
.quote-add-button { min-width: 42px; min-height: 28px; }
.provider-mark { width: 42px; height: 42px; }
```

No modificar las reglas de foco, Escape, backdrop, modal horizontal o animación reducida.

- [ ] **Step 3: Restore summary-table density**

Cambiar las declaraciones existentes a:

```css
.summary-media-button {
  min-width: 0;
  min-height: 0;
}

.summary-quote-add {
  min-width: 42px;
  min-height: 28px;
}

.summary-stock-watch {
  width: 24px;
  height: 24px;
  min-width: 24px;
  min-height: 24px;
}
```

En la composición móvil de filas, restaurar `.summary-color-cell` a `width: 36px; min-width: 36px;` y eliminar `min-height: 44px` de `.summary-product-name a` sin cambiar su `display` ni alineación.

- [ ] **Step 4: Restore mobile-specific compact metrics**

En `@media (max-width: 860px)` y `@media (max-width: 760px)` aplicar:

```css
@media (max-width: 860px) {
  :root { --quick-lines-height: 48px; }
  .quick-line { min-height: 32px; }
  .color-picker-continuous-grid,
  .color-picker-family-grid { grid-template-columns: repeat(auto-fill, minmax(34px, 1fr)); }
}

@media (max-width: 520px) {
  .quote-list-drawer-close { width: 40px; height: 40px; }
  .quote-list-remove { width: 40px; height: 40px; }
  .quote-add-button,
  .summary-quote-add { min-width: 40px; min-height: 36px; }
}
```

Quitar del grupo móvil universal de `min-height: 44px` a `.color-picker-view-tabs button` y los inputs/botones de búsqueda similar cuando esa altura sólo provenga de la auditoría; conservar los controles de filtros que ya necesiten 44 px para su layout móvil.

- [ ] **Step 5: Remove the ultrawide expansion**

Eliminar completamente:

```css
@media (min-width: 1800px) {
  .shell {
    width: min(1920px, calc(100% - 48px));
  }

  .internal-shell {
    max-width: 1920px;
  }
}
```

La regla base `.shell { width: min(1180px, calc(100% - 32px)); }` y `.internal-shell { max-width: 1180px; }` quedan como autoridad única.

- [ ] **Step 6: Run focused contracts until green**

Run:

```powershell
python -m pytest tests/test_frontend_assets.py -v --basetemp C:\tmp\pytest-centraldefilamentos
npx playwright test tests/e2e/touch-targets.spec.js tests/e2e/responsive.spec.js --project=desktop-4k --project=desktop-1080 --project=mobile-390
```

Expected: both commands exit 0; Playwright reports no overflow, exact 24 px bells, compact chips and maximum 1180 px content.

- [ ] **Step 7: Commit the CSS restoration**

```powershell
git add src/styles/global.css
git commit -m "fix: restore compact UI density"
```

### Task 3: Full Verification, Visual Review and Publication

**Files:**
- Create: `docs/qa/2026-07-16-ui-density-verification.md`

**Interfaces:**
- Consumes: green focused contracts and compact CSS from Tasks 1–2.
- Produces: verification evidence, reviewed screenshots and a published `master`/GitHub Pages build.

- [ ] **Step 1: Run all non-browser quality gates**

Run:

```powershell
npm run build
node --test tests/*.test.js
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos
```

Expected: Vite build exits 0, all Node tests pass, all Python tests pass.

- [ ] **Step 2: Run the complete eight-project Chrome matrix**

Run:

```powershell
npm run test:ui
```

Expected: all Playwright tests pass for `desktop-4k`, `desktop-2k`, `desktop-1080`, `laptop-1366`, `mobile-412`, `mobile-390`, `mobile-360`, and `mobile-landscape`; axe has no serious or critical violations.

- [ ] **Step 3: Capture and inspect representative screenshots in Chrome**

Con Chrome, abrir Resumen y comprobar visualmente:

- `3840 x 2160`: contenido centrado, máximo 1180 px, espacio lateral amplio.
- `1920 x 1080`: chips compactos, filas densas, campanas discretas.
- `390 x 844`: chips de 32 px, `+1` de 40 x 36, filas sin solapamientos.

Guardar capturas en `test-results/ui-density-review/` como `summary-4k.png`, `summary-1080.png` y `summary-mobile-390.png`. Verificar también Color Picker en `1920 x 1080` y `390 x 844`, conservando tooltip, foco y mapa de 44 px.

- [ ] **Step 4: Review the final diff for unintended visual or behavioral changes**

Run:

```powershell
git diff c26b868..HEAD --stat
git diff HEAD~2..HEAD -- src/styles/global.css tests/e2e/touch-targets.spec.js tests/e2e/responsive.spec.js tests/test_frontend_assets.py
git diff --check
git status --short --branch
```

Expected: no Svelte/business-logic changes, no whitespace errors, only intended test/CSS/docs files.

- [ ] **Step 5: Record verification evidence**

Crear `docs/qa/2026-07-16-ui-density-verification.md` con esta estructura y valores reales de la ejecución:

```markdown
# Verificación de densidad UI — 2026-07-16

## Resultado

- Build: PASS
- Node tests: PASS
- Pytest: PASS
- Playwright (8 viewports, Chrome): PASS
- Axe serious/critical: 0

## Métricas observadas

- Contenedor 4K/2K: 1180 px máximo
- Quick lines: 30 px desktop / 32 px móvil
- Campanas: 24 x 24 px
- +1: 42 x 28 px desktop / 40 x 36 px móvil

## Revisión visual

- 4K: PASS
- 1080p: PASS
- 390 x 844: PASS
- Color Picker desktop/móvil: PASS

## Publicación

- Commit publicado: `<hash real>`
- CI: `<estado real>`
- Publish UI: `<estado real>`
- GitHub Pages: `<URL y verificación real>`
```

- [ ] **Step 6: Commit verification documentation**

```powershell
git add docs/qa/2026-07-16-ui-density-verification.md
git commit -m "docs: record compact UI verification"
```

- [ ] **Step 7: Publish and verify authoritative deployment state**

Actualizar `master` sólo si `git fetch origin` confirma que no hay cambios remotos incompatibles; rebasear o integrar de forma no destructiva si avanzó. Luego:

```powershell
git push origin master
gh run list --branch master --limit 10
gh api repos/Zogar89/CentraldeFilamentos/pages/builds/latest
```

Expected: CI and `Publish UI` finish successfully; latest Pages build reports `built`; the served CSS/HTML corresponds to the published commit. If `gh` authentication remains unavailable, use `git push` for publication and verify the workflow/Pages assets through the public GitHub endpoints without exposing credentials.

---

## Self-Review

- Spec coverage: all eight acceptance criteria map to Tasks 1–3.
- Placeholder scan: todas las acciones y bloques de código están definidos de forma concreta.
- Type/name consistency: all selectors match the current Svelte/CSS source; `dimensions()` is retained with the same return shape.
- Scope control: no component logic, data pipeline or dependency change is included.
