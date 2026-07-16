# UI/UX Audit Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir todos los defectos reproducibles de la auditoría UI/UX y dejar la matriz automatizada verde en Chrome.

**Architecture:** Conservar la arquitectura Svelte existente. Las correcciones semánticas viven en los componentes responsables; responsive, contraste y targets se resuelven en `src/styles/global.css`; publicación y tooling se corrigen en sus archivos de configuración. Cada bloque sigue RED → GREEN y se revisa antes del siguiente.

**Tech Stack:** Svelte 5, JavaScript ES modules, CSS, Vite 8, Playwright, axe-core, pytest, GitHub Actions.

## Global Constraints

- El sitio sigue siendo estático y compatible con GitHub Pages bajo `/CentraldeFilamentos/`.
- No agregar backend, sesiones ni dependencias de UI nuevas.
- Mantener el lenguaje visual existente; priorizar legibilidad, reflow y accesibilidad.
- Ningún control táctil principal menor de 44 × 44 CSS px salvo excepción WCAG por separación equivalente.
- Cero overflow horizontal del documento en los ocho viewports auditados.
- Una sola `h1` por vista y skip link con transferencia real de foco.
- Los fixes deben preservar el flujo de cotización y el contrato de datos actual.
- Máximo tres intentos por hipótesis; después, reanalizar arquitectura.

---

### Task 1: Semántica y foco

**Files:**
- Modify: `src/components/SiteHeader.svelte`
- Modify: `src/ColorPickerApp.svelte`
- Modify: `src/SummaryApp.svelte`
- Modify: `src/VendorStatsApp.svelte`
- Modify: `src/components/SimilarColorSearch.svelte`
- Test: `tests/e2e/color-picker-flow.spec.js`
- Test: `tests/e2e/responsive.spec.js`

**Interfaces:**
- Consumes: `#main-content`, `.skip-link`, resultado similar activado.
- Produces: `aria-current="page"`, una `h1` por vista, foco conservado o dirigido a un control existente.

- [ ] Confirmar que los tests de foco y H1 fallan por las causas auditadas.
- [ ] Hacer `#main-content` enfocable programáticamente y transferirle foco desde el skip link.
- [ ] Incorporar una `h1` visible o visualmente oculta en Resumen y Estadísticas sin duplicar títulos.
- [ ] Conservar foco al seleccionar un resultado similar, dirigiéndolo al card agregado o a su botón de quitar.
- [ ] Asociar error HEX con el input y anunciar resultados dinámicos.
- [ ] Ejecutar los specs de foco, responsive y axe; verificar GREEN.

### Task 2: Reflow y overflow

**Files:**
- Modify: `src/styles/global.css`
- Test: `tests/e2e/responsive.spec.js`

**Interfaces:**
- Consumes: ocho viewports Playwright y excepciones scroll autorizadas.
- Produces: `document.documentElement.scrollWidth <= clientWidth` en las tres vistas.

- [ ] Ejecutar el spec responsive y registrar overflow exacto por ruta/viewport.
- [ ] Corregir pseudo-elementos/tooltips del Color Picker para que no amplíen el documento.
- [ ] Mover el breakpoint del header y de la tabla para cubrir 844 × 390 sin cliff 820/821.
- [ ] Hacer visibles los totales equivalentes en móvil.
- [ ] Limitar modales al `visualViewport` con scroll interno y cierre visible.
- [ ] Corregir grids de KPIs e intradía para 360–844 px.
- [ ] Ejecutar el spec responsive completo; verificar GREEN.

### Task 3: Contraste y targets táctiles

**Files:**
- Modify: `src/styles/global.css`
- Test: `tests/e2e/accessibility.spec.js`
- Test: `tests/e2e/responsive.spec.js`

**Interfaces:**
- Consumes: reporte axe WCAG 2 A/AA/2.1/2.2.
- Produces: cero violaciones axe serias/críticas y objetivos táctiles conformes.

- [ ] Ejecutar axe y agrupar nodos por token/regla compartida.
- [ ] Ajustar tokens `muted`, `warn`, azul de acción y deltas sin cambiar la identidad.
- [ ] Garantizar foco visible de al menos 3:1.
- [ ] Aumentar swatches, campanas, `+1`, cierres, tabs y puntos del mapa o su hit area a 44 px.
- [ ] Ejecutar axe inicial/dinámico y los flujos de cotización; verificar GREEN.

### Task 4: Pantallas anchas y densidad

**Files:**
- Modify: `src/styles/global.css`
- Test: `tests/e2e/responsive.spec.js`
- Test: `tests/e2e/performance.spec.js`

**Interfaces:**
- Consumes: 2560 × 1440 y 3840 × 2160.
- Produces: ancho útil mayor sin degradar 1366/1080 ni superar presupuestos.

- [ ] Definir un max-width fluido apropiado para tablas y dashboards en 2K/4K.
- [ ] Mantener ancho de lectura controlado en Color Picker y textos.
- [ ] Verificar columnas, sticky layers y densidad visual en 1080p, 2K y 4K.
- [ ] Ejecutar responsive y performance; verificar GREEN.

### Task 5: Operación y supply chain

**Files:**
- Modify: `index.html`
- Modify: `resumen.html`
- Modify: `color-picker.html`
- Modify: `estadisticas.html`
- Create: `public/favicon.svg`
- Modify: `.github/workflows/pages.yml`
- Modify: `package.json`
- Modify: `package-lock.json`
- Modify: `lighthouserc.json`

**Interfaces:**
- Consumes: Vite base `/CentraldeFilamentos/`, Chrome/LHCI en Windows.
- Produces: favicon 200, trigger de publicación correcto, dependencias sin altas conocidas cuando exista versión segura compatible, LHCI sin depender de temp bloqueado.

- [ ] Agregar test de favicon y trigger de publicación; confirmar RED.
- [ ] Declarar favicon en todas las entradas y agregar el asset.
- [ ] Incluir `color-picker.html` en paths de Publish UI.
- [ ] Actualizar Vite a una versión segura compatible y revisar el riesgo transitivo de LHCI sin aplicar downgrades inseguros.
- [ ] Configurar perfil temporal de Lighthouse dentro del workspace o documentar el bloqueo si chrome-launcher no lo permite.
- [ ] Ejecutar build, npm audit y Lighthouse hasta tres intentos; verificar o registrar limitación real.

### Task 6: Revisión e integración

**Files:**
- Modify: `docs/ui-audit/2026-07-16-ui-ux-audit.md`

**Interfaces:**
- Consumes: diff completo desde `c26b868` y resultados frescos.
- Produces: rama revisada, reporte actualizado, merge a `master` y publicación verificada.

- [ ] Ejecutar revisión de especificación y calidad con agentes independientes.
- [ ] Corregir hallazgos importantes y repetir revisión.
- [ ] Ejecutar `npm run build`, Node tests, pytest y `npm run test:ui` completos.
- [ ] Ejecutar `npm audit` y registrar riesgos residuales.
- [ ] Actualizar el reporte con resultados post-fix.
- [ ] Integrar a `master`, push y verificar GitHub Actions/GitHub Pages.
