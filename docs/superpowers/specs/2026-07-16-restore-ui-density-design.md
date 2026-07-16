# Restauración de densidad visual de la UI

## Objetivo

Restaurar la densidad compacta que tenía Central de Filamentos antes de la auditoría UI del 16 de julio de 2026, sin perder las correcciones funcionales, responsive y de accesibilidad que no modifican la escala visual.

## Lectura de diseño

Interfaz de datos para makers que comparan muchas filas y proveedores. Debe priorizar escaneo rápido, alta densidad y estabilidad visual por encima de objetivos táctiles sobredimensionados o expansión especial para monitores grandes.

- Variación visual: 3/10.
- Movimiento: 2/10.
- Densidad visual: 8/10.
- Base: CSS y componentes existentes; no se introduce otro sistema de diseño.

## Enfoques considerados

1. **Restauración exacta de densidad, recomendada y aprobada.** Recuperar las métricas anteriores en ancho, chips, campanas, controles y Color Picker; conservar las mejoras no visuales.
2. **Compactación intermedia.** Mantener parte de los tamaños nuevos y reducirlos sólo parcialmente. Rechazado porque no recupera la densidad conocida por el usuario.
3. **Revertir toda la auditoría UI.** Rechazado porque también eliminaría correcciones válidas de foco, contraste, semántica, overflow y publicación.

## Métricas visuales a restaurar

### Contenedor y pantallas amplias

- El contenido vuelve a un ancho máximo de 1180 px.
- Se elimina la expansión a 1920 px aplicada desde 1800 px de viewport.
- En 2K y 4K se conserva espacio lateral; no se intenta llenar el monitor.

### Navegación rápida de materiales

- Los chips PLA, PLA+, Flex, PETG y equivalentes vuelven a 30 px en desktop y 32 px en la composición móvil.
- La banda rápida recupera 43 px en desktop y 48 px en móvil.
- No se fuerza una altura visual de 44 px en estos chips.

### Tabla de resumen

- Las campanas de stock vuelven a 24 × 24 px visibles.
- Los botones `+1` recuperan la escala compacta anterior: 42 × 28 px como base y 40 × 36 px en móvil.
- Las muestras de color y columnas móviles recuperan 36 px donde correspondía.
- Se eliminan alturas mínimas de 44 px que agrandan filas, enlaces y celdas.

### Color Picker

- Tiles de 42 px como base y 34 px en móvil.
- Los puntos del mapa conservan un hitbox absoluto de 44 px porque no cambia su tamaño visual ni la distribución.
- El input de color vuelve a 40 px y las pestañas recuperan su altura compacta anterior.
- El tooltip real y su ajuste al viewport se conservan.

### Drawers y modales

- Cerrar drawer vuelve a 32 px en desktop y 40 px en móvil.
- Quitar ítem vuelve a 28 px en desktop y 40 px en móvil.
- Cerrar imagen vuelve a 30 px.
- Se conserva el manejo de foco, Escape, devolución de foco y límites de altura en móvil horizontal.

## Correcciones que se conservan

- H1 y landmarks accesibles.
- Skip link con transferencia real de foco.
- Foco estable después de elegir colores similares.
- `aria-current`, estados live persistentes y asociación de errores.
- Contrastes AA corregidos.
- Breakpoint de 860 px que evita el header cortado en 844 × 390.
- Totales móviles, modal horizontal, prevención de overflow y tooltip acotado.
- Favicon, entradas Vite, redirección legacy y workflows de publicación/auditoría.
- Vite 8.0.16 y la infraestructura automatizada.

## Criterios de aceptación

1. En 3840 × 2160 y 2560 × 1440, el contenedor principal no supera 1180 px.
2. Los chips rápidos no superan 32 px de alto.
3. Las campanas de stock de la tabla miden 24 × 24 px visibles.
4. Las filas y controles recuperan una densidad visual comparable a `c26b868`.
5. No hay overflow horizontal en 4K, 2K, 1080p, 1366 px, 412 px, 390 px, 360 px ni 844 × 390.
6. Los flujos de cotización, Color Picker, teclado y foco continúan funcionando.
7. Axe no informa violaciones serias o críticas en los viewports representativos.
8. Build, pruebas Python, pruebas JavaScript y matriz Playwright terminan correctamente.

## Estrategia de pruebas

- Cambiar los tests de objetivos táctiles por contratos de densidad visibles y el mínimo WCAG 2.5.8 de 24 px para controles interactivos relevantes.
- Agregar aserciones explícitas para ancho máximo, altura de chips y campanas.
- Mantener pruebas de overflow, teclado, foco, axe, cotización y rendimiento.
- Comparar capturas de Resumen en 4K, 1080p y móvil contra la densidad anterior antes de publicar.

## Publicación

Implementar en una rama aislada, verificar, revisar el diff, fusionar por fast-forward a `master`, publicar y comprobar CI, Publish UI y los activos servidos por GitHub Pages.
