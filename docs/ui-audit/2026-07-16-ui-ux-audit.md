# Auditoría automatizada de UI/UX — 2026-07-16

## Veredicto

La UI funciona bien en el flujo principal de cotización y mantiene presupuestos locales de carga razonables, pero todavía no está lista para tratar la auditoría responsive y WCAG como una barrera de calidad obligatoria. Los defectos más importantes son el desbordamiento horizontal del Color Picker, dos pérdidas de foco por teclado y contrastes AA insuficientes.

Esta auditoría no modifica componentes de producción. Agrega infraestructura reproducible, pruebas y evidencia en la rama aislada `codex/ui-ux-automation-audit`.

## Alcance

Vistas verificadas:

- Resumen/catálogo: `/CentraldeFilamentos/`
- Color Picker: `/CentraldeFilamentos/color-picker.html`
- Estadísticas de proveedores: `/CentraldeFilamentos/estadisticas.html`

Viewports:

| Perfil | Tamaño |
|---|---:|
| 4K | 3840 × 2160 |
| 2K | 2560 × 1440 |
| 1080p | 1920 × 1080 |
| Laptop | 1366 × 768 |
| Móvil grande | 412 × 915 |
| Móvil | 390 × 844 |
| Móvil compacto | 360 × 800 |
| Móvil horizontal | 844 × 390 |

Se verificaron carga, errores de consola/red, imágenes rotas, overflow, controles recortados, jerarquía de encabezados, teclado/foco, flujo de cotización, estados dinámicos del Color Picker, axe WCAG 2 A/AA/2.1/2.2, peso de recursos y tiempos locales.

## Resultados automatizados

| Suite | Resultado | Lectura |
|---|---:|---|
| Runtime smoke | 8/8 pasan | Las cuatro familias de tamaño cargan en Chrome sin fallos fatales. |
| Responsive estructural | 3 pasan, 21 fallan | Las fallas se concentran en H1 ausente y overflow, no en 21 defectos distintos. |
| Cotización profunda | 2/2 pasan | Desktop 1080p y móvil 390: agregar, foco del drawer, caja x12, cobertura, mensaje y WhatsApp. |
| Color Picker profundo | 2 pasan, 4 fallan | Cambio de vistas pasa; foco post-selección y skip link fallan en desktop y móvil. |
| Axe dinámico | 8 fallan | Contraste AA insuficiente en las tres vistas y estados dinámicos. |
| Presupuestos locales | 3/3 pasan | Tres muestras por vista, sin exceder 3 s DCL, 5 s load, 2 MB total, 250 KB JS o 120 KB CSS. |
| Build Vite | Pasa | 287 módulos; CSS 70.49 KB y chunks JS individuales de 10.53–63.03 KB sin gzip. |
| Lighthouse CI | Bloqueado | Chrome produjo una muestra parcial, pero Windows negó limpiar el perfil temporal en tres intentos. No se usa como resultado concluyente. |

## Hallazgos prioritarios

### Alta prioridad

1. **Color Picker genera scroll horizontal.** Se midieron 101 px extra a 360 px, 85 px a 390 px, 90 px en 844 × 390 y 13 px en 1366 × 768. En móvil el scrollbar es visible. Los tooltips generados por CSS amplían el ancho aunque estén ocultos.
2. **El header se corta en móvil horizontal.** El layout mantiene tres columnas hasta 820 px, por lo que 844 × 390 cae justo fuera del breakpoint móvil y recorta marca/navegación.
3. **Pérdida de foco al elegir un color similar.** El botón activado desaparece al recalcular resultados y `document.activeElement` termina en `body`, en desktop y móvil. Riesgo WCAG 2.4.3.
4. **El skip link no transfiere foco.** Cambia el hash y desplaza, pero `#main-content` no recibe foco. Riesgo WCAG 2.4.1.
5. **Contraste AA insuficiente.** Axe confirmó, entre otros, navegación 4.27:1, texto secundario 4.37:1, controles azules alrededor de 4.25–4.28:1 y deltas de stock alrededor de 3.79–4.25:1, por debajo de 4.5:1 para texto normal.
6. **Resumen y Estadísticas no tienen H1.** Color Picker sí tiene uno; las otras dos vistas exponen cero `h1` en todas las resoluciones.
7. **Objetivos táctiles pequeños.** Hay swatches de 34 px, campanas de 34 px, botones `+1` de 40 × 36 px y puntos del mapa entre 12 y 24 px; varios no alcanzan WCAG 2.5.8.

### Prioridad media

8. El Resumen desborda 9 px en 844 × 390 y el breakpoint 820/821 crea un salto brusco entre tabla móvil y desktop.
9. Los totales móviles se ocultan por debajo de 1100 px porque `.summary-mobile-totals` permanece en `display: none`.
10. El modal de imagen cuadrado puede superar la altura útil en 844 × 390 y no define `max-height`/scroll interno.
11. Las tarjetas de estadísticas y la fila intradía quedan demasiado densas en móvil horizontal; el KPI grid mantiene tres columnas incluso a 360 px.
12. El mapa 2D depende de posición/tamaño para transmitir significado, pero el lector de pantalla recibe una secuencia plana de botones.
13. Resultados similares aparecen sin región live y el error HEX no está asociado al input mediante `aria-describedby`.
14. La navegación activa usa una clase visual pero no `aria-current="page"`.

### Operación y mantenimiento

15. Todas las vistas solicitan `/favicon.ico` y reciben 404.
16. `.github/workflows/pages.yml` no observa `color-picker.html`; un cambio exclusivo a ese HTML no dispara publicación.
17. `npm audit` informa 6 vulnerabilidades de desarrollo: 2 bajas, 2 moderadas y 2 altas. Las altas están en Vite 8.0.13 y `tmp` transitivo de LHCI. No se aplicó un `audit fix` automático.
18. En 4K/2K el contenido conserva un máximo cercano a 1180 px. No se rompe, pero desaprovecha mucho espacio horizontal y reduce la ventaja de esas pantallas.

## Fortalezas confirmadas

- El flujo completo de cotización pasa en 1920 × 1080 y 390 × 844.
- El drawer es modal, enfoca inicialmente el botón cerrar y devuelve el foco al disparador.
- La lista persiste localmente, permite caja x12, compara cobertura y arma mensajes individuales de consulta.
- Los tiles de color son botones nativos con nombre accesible, stock y `aria-pressed`.
- El HEX inválido usa `aria-invalid` y `role="alert"`.
- No se detectaron imágenes rotas visibles ni excepciones JavaScript fatales en la matriz.
- `prefers-reduced-motion` está contemplado en componentes clave.

## Evidencia visual aceptada

### Desktop

![Color Picker desktop](screenshots/color-picker-desktop.jpg)

### Móvil 390 px

El scrollbar inferior confirma el reflow defectuoso.

![Color Picker móvil con overflow](screenshots/color-picker-mobile-390.jpg)

### Móvil horizontal 844 × 390 en Chrome

![Header recortado y overflow horizontal](screenshots/chrome-color-picker-844x390.png)

## Cómo ejecutar

```text
npm ci
npm run build
npm run test:ui
npm run audit:lighthouse
```

`npm run test:ui` deja reporte HTML en `playwright-report/` y evidencia de fallos en `test-results/`. La automatización de GitHub está en `.github/workflows/ui-audit.yml` y conserva artefactos durante 14 días.

## Limitaciones de evidencia

- Axe detecta reglas automatizables; no sustituye NVDA/VoiceOver ni una revisión cognitiva con usuarios.
- Los presupuestos de rendimiento locales no tienen throttling de red/CPU. Lighthouse quedó configurado, pero su corrida multi-muestra fue bloqueada por permisos temporales de Chrome en esta máquina.
- Los datos del catálogo cambian con el pipeline. El smoke usa los datos actuales; para regresiones visuales estrictas conviene sumar un fixture estable en una segunda fase.
