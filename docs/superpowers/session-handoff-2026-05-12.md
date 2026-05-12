# StockCentral - Handoff de sesion

Fecha: 2026-05-12

## Estado al cerrar

- El repo local esta inicializado en git y con working tree limpio antes de publicar.
- Se definio el MVP como sitio estatico publico en GitHub Pages.
- Python va a correr en GitHub Actions para leer fuentes, normalizar stock y generar `public/data/stock.json`.
- El frontend va a ser HTML/CSS/JS estatico, en espanol argentino, pensado para AMBA.
- No hay codigo de aplicacion implementado todavia; por ahora quedaron spec y plan de ejecucion.
- Ultimo commit local antes de este handoff: `376d226 docs: add pivot summary view requirements`.

## Decisiones tomadas

- Proveedores iniciales:
  - Filamentos3D, Zona Sur, fuente HTML: `https://filamentos3d.com.ar/grilon3.php`.
  - Grupo Senz, Zona Oeste, fuente Google Sheet: `https://docs.google.com/spreadsheets/d/14nblAeXZfx_TEeHj4xnK90hSmUp3hk6KSO4nUTrb9zM`.
  - MundoInsumos, Zona Norte, fuente Google Sheet gid `1981641819`: `https://docs.google.com/spreadsheets/d/1r-nKy4tRRtZ-5xwgxAcia8REDVW0Dv0h/edit?gid=1981641819#gid=1981641819`.
- Sitio publico, actualizacion 2 a 4 veces por dia en horario de oficina.
- Sin precios en el MVP.
- Sin filtro por zona por ahora.
- Productos sin stock siempre visibles.
- Filtros del catalogo: material, variante, color, diametro, peso/kg, marca, proveedor y estado de stock.
- PLA queda destacado porque es el caso principal de busqueda.
- Producto agrupado por `material + variant + color + diameter_mm + weight_g + brand`.
- Productos Grilon3 deben linkear a pagina oficial cuando exista y traer imagen disponible desde `https://grilon3.com.ar/productos/`.
- 3N3 queda sin sitio oficial por ahora; no inventar links.
- Diseno minimalista estilo Apple como inspiracion: claro, compacto, rapido, sin copiar marca ni assets.
- Footer con fuentes, contactos disponibles, ultima actualizacion y estadisticas por proveedor.
- Valores negativos o raros de stock se publican como `unknown`, no como stock positivo y no suman unidades ni kg.
- Se agrego segunda pagina `resumen.html`: tabla tipo dinamica con filamentos por fila, proveedores por columna, total por producto a la derecha y kg por proveedor abajo.

## Archivos importantes

- `docs/superpowers/specs/2026-05-12-stockcentral-design.md`: especificacion de producto.
- `docs/superpowers/plans/2026-05-12-stockcentral-mvp.md`: plan ejecutable task-by-task para implementar el MVP.
- `docs/superpowers/session-handoff-2026-05-12.md`: este handoff.

## Preguntas para cuando vuelvas

1. Contactos de proveedores:
   - Filamentos3D: WhatsApp, mail, direccion exacta o zona publica, pagina de contacto.
   - Grupo Senz: sitio oficial si existe, WhatsApp, mail, direccion o zona publica.
   - MundoInsumos: WhatsApp, mail, direccion o zona publica.

2. Fuentes:
   - Confirmar que las planillas de Grupo Senz y MundoInsumos quedan publicas o al menos exportables como CSV sin login.
   - Confirmar si cada planilla tiene una sola hoja relevante o si hay que leer varios `gid`.
   - Confirmar cuales son las columnas reales de producto, stock, marca, diametro y peso si no son obvias.

3. Stock:
   - Confirmar que `stock` significa unidades/bobinas disponibles.
   - Confirmar que una unidad de 1 kg debe sumar 1 kg, 500 g suma 0,5 kg, etc.
   - Confirmar si los valores negativos deben mostrarse como `Stock a revisar` o directamente como `Sin dato`.

4. Super resumen:
   - Confirmar si las celdas por proveedor deben mostrar solo unidades, o unidades + kg.
   - Confirmar si el total derecho debe ser unidades totales, kg totales, o ambos.
   - Confirmar el orden preferido de proveedores: Zona Sur/Oeste/Norte, alfabetico, o manual.
   - Confirmar si una celda sin stock debe verse como `0`, `Sin stock`, o quedar visualmente tenue.

5. Normalizacion:
   - Confirmar sinonimos y variantes que conviene reconocer desde el inicio: PLA+, Silk, Mate, Pro, Flex, Wood, Galaxy, Boutique, Astra.
   - Confirmar si colores especiales deben agruparse o mantenerse separados: natural/transparente/cristal, gris/plata, multicolor/rainbow.
   - Confirmar si productos de distinta marca pero mismo material/color/peso deben quedar separados como ahora, o si alguna vista debe agruparlos juntos.

6. Imagenes y links:
   - Confirmar si esta bien usar imagenes remotas oficiales del fabricante, o si preferis cachearlas/copiar URLs al build.
   - Confirmar si cuando no hay link oficial del fabricante el titulo del producto debe linkear a la fuente/proveedor, o quedar sin link.

7. Flujo del usuario impresor 3D:
   - Si alguien necesita 4 kg del mismo color, conviene agregar un filtro rapido de cantidad minima?
   - Si no hay stock exacto, conviene sugerir variantes cercanas del mismo color/material?
   - Conviene mostrar un boton de WhatsApp por proveedor con mensaje prearmado tipo "Hola, vi en StockCentral que tenes PLA Negro..."?

8. Publicacion:
   - Confirmar si el repositorio `StockCentral` queda como nombre definitivo.
   - Cuando haya app implementada, confirmar si activamos GitHub Pages desde GitHub Actions en la configuracion del repo.

## Proximo paso sugerido

Implementar desde `docs/superpowers/plans/2026-05-12-stockcentral-mvp.md`, empezando por Task 1: scaffold Python, modelos y tests. Despues avanzar en orden hasta llegar al frontend y recien ahi validar visualmente en browser.
