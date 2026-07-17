# Design QA · Opción 1

## Evidencia

- Verdad visual: `C:/Users/Gabriel/Documents/GitHub/StockCentral/docs/qa/evidence/option-1/reference-option-1.png`
- Implementación desktop: `C:/Users/Gabriel/Documents/GitHub/StockCentral/docs/qa/evidence/option-1/desktop-selected.png`
- Comparación conjunta a escala nativa: `C:/Users/Gabriel/Documents/GitHub/StockCentral/docs/qa/evidence/option-1/comparison-full.png`
- Implementación mobile: `C:/Users/Gabriel/Documents/GitHub/StockCentral/docs/qa/evidence/option-1/mobile-main.png`
- Drawer mobile: `C:/Users/Gabriel/Documents/GitHub/StockCentral/docs/qa/evidence/option-1/mobile-quote-drawer.png`
- Viewport desktop: 1536 × 1092 por artefacto; comparación conjunta 3072 × 1092.
- Viewport mobile: 390 × 844.
- Estado comparado: PLA seleccionado, familia Amarillos activa desde Amarillo Fluo y tres productos en la lista de cotización.

La comparación completa se hizo con referencia e implementación juntas, a resolución nativa 1:1. No fue necesario un recorte adicional: tipografía, filtros, primeras filas, imágenes y rail de cotización permanecen legibles en la evidencia conjunta. Los dos estados mobile se capturaron aparte porque no existen en el mock desktop.

## Findings

No quedan diferencias P0, P1 o P2 accionables.

- [Aceptada] El mock usa iconografía conceptual para materiales y la implementación usa imágenes reales aprobadas del catálogo. Esto mejora el reconocimiento del producto y respeta los assets existentes.
- [Aceptada] El rail real incorpora edición de cantidades y separa cobertura y envío en etapas. Es más funcional que los chips estáticos del mock y conserva la misma jerarquía: lista persistente, comparación de proveedores y consulta por WhatsApp.
- [P3] El favicon multicolor existente difiere de la marca teal monocroma del mock. Se preservó el asset de marca actual para no introducir un logo nuevo sin una decisión de identidad explícita.

## Superficies de fidelidad

- Tipografía: la pila nativa Segoe UI/system mantiene la escala, peso, legibilidad y jerarquía del mock; no hay wrapping roto ni truncamiento de controles primarios.
- Espaciado y layout: selector de material, ribbon cromático, filtros, filas y rail mantienen las proporciones y el ritmo del mock. Desktop no tiene overflow y mobile transforma el rail en drawer.
- Colores y tokens: fondo frío, superficies blancas, bordes suaves y teal de acción están alineados con la referencia. Los tokens `--accent` y `--ok` se oscurecieron para superar contraste AA.
- Calidad de imágenes: se usan fotos/thumbnails reales del stock y swatches publicados; no hay placeholders, CSS art ni imágenes rotas.
- Copy y contenido: material primero, familia cromática dentro del material, stock por proveedor y lenguaje de cotización/confirmación sostienen la tarea maker. No se presenta a StockCentral como tienda.
- Estados e interacción: material, color, filtros, agregar, cantidades, cobertura, preparación del mensaje, drawer mobile, vacío y disabled están implementados.
- Accesibilidad: foco visible, semántica de botones/tabs/dialog, targets táctiles y contraste verificados. Las pruebas runtime no registran errores de aplicación; Chrome mostró únicamente avisos externos del canal de una extensión, no reproducidos por los guardas del sitio.

## Historial de comparación

### Iteración 1

- [P1] La selección de color filtraba el nombre exacto y no la familia visual del mock.
  - Fix: clasificación semántica y perceptual por familias, siempre subordinada al material seleccionado.
- [P2] Dos verdes de estado quedaban apenas debajo de contraste AA.
  - Fix: `--accent` pasó a `#006f77` y `--ok` a `#0f733f`.
- [P2] El acceso flotante a cotización se partía en tres líneas en 390 px.
  - Fix: grilla específica `auto 24px`, gap y `white-space: nowrap`.

### Iteración 2

- Evidencia post-fix: `comparison-full.png`, `mobile-main.png` y `mobile-quote-drawer.png`.
- Resultado visual: sin overflow, superposiciones, imágenes rotas ni controles recortados.
- Recorrido probado en Chrome: selección PLA → Amarillo Fluo/Amarillos → agregar tres productos → comparar tres proveedores → preparar mensaje → enlace WhatsApp válido.
- Verificación automatizada: suite responsive, accesibilidad, targets táctiles, runtime y flujo principal en desktop/mobile.

## Checklist de implementación

- [x] Jerarquía material → familia de color → stock exacto.
- [x] Filtros secundarios y orden por disponibilidad.
- [x] Lista persistente en desktop y drawer en mobile.
- [x] Comparación por proveedor y mensaje de WhatsApp.
- [x] Estados vacío, selección, agregado, disabled y envío.
- [x] Contraste, responsive, touch targets y build verificados.

final result: passed
