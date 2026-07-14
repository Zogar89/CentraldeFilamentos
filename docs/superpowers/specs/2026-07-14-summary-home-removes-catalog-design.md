# Resumen como portada y retiro del Catalogo - Diseno

## Objetivo

Convertir la pantalla de Resumen en la experiencia principal de Central de Filamentos, servida directamente desde `/CentraldeFilamentos/`, eliminar la pantalla de Catalogo y mostrar en cada fila del resumen la foto del carrete junto a la muestra material prerenderizada.

## Navegacion y rutas

- `index.html` carga `src/summary.js` y por lo tanto monta `SummaryApp`.
- `/resumen.html` se conserva como alias compatible y sigue montando el mismo `SummaryApp`.
- Se eliminan `src/CatalogApp.svelte` y `src/catalog.js`.
- El encabezado deja de ofrecer dos vistas equivalentes. Conserva:
  - `Resumen`, enlazado a `index.html`.
  - `Proveedores`, enlazado a `index.html#site-footer`.
- La marca del encabezado enlaza a `index.html` y su etiqueta accesible pasa a describir la portada, no el catalogo.
- El build de Vite mantiene `index.html`, `resumen.html` y `estadisticas.html`; el input raiz cambia de nombre interno de `catalogo` a `principal`.

## Composicion visual de cada producto

La primera celda de cada fila usa un grupo visual horizontal compacto:

1. Foto del filamento, usando `thumbnail_url` y luego `image_url` como fallback.
2. Muestra material prerenderizada, usando `material_swatch_url`.
3. Si no existe render material, se mantiene el swatch CSS actual en la segunda posicion.
4. Si no existe foto, la muestra material o su fallback ocupan solos el grupo sin reservar un hueco vacio.

Las dos imagenes usan 28 x 28 px, borde y radio coherentes con la tabla. La foto es decorativa porque el nombre del producto ya aparece al lado; la muestra material conserva su descripcion accesible. En pantallas angostas el grupo no se parte y la fila mantiene la densidad actual.

Al pasar el puntero sobre cualquiera de las dos imagenes se muestra el preview ampliado existente. La foto usa el original cuando esta disponible y el render usa su WebP. En dispositivos sin hover no se muestra el preview flotante.

## Filtros y ayuda

Resumen recibe el panel completo que hoy existe en Catalogo: busqueda, material, color, proveedor, linea, diametro, peso, marca y disponibilidad. Los filtros se aplican antes de calcular filas, grupos y totales, por lo que la tabla y el pie siempre representan el subconjunto visible.

La franja de ayuda existente se mantiene mediante `SiteHeader` y pasa a mostrarse desde `SummaryApp`. Su texto conserva la explicacion de `+1` y campanita porque ambas acciones tambien se migran.

## Cotizacion y seguimiento

- Cada fila de producto muestra `+1` junto al nombre/presentacion y agrega una unidad a la lista local existente.
- Cada celda de proveedor muestra la campanita asociada a la oferta de ese producto/proveedor.
- Se migran a `SummaryApp` la carga, reconciliacion, importacion/exportacion, panel lateral, drawer mobile y feedback de la lista de cotizacion.
- Se migran la carga, persistencia, reconciliacion y avisos de seguimiento de stock.
- Se reutilizan sin cambiar esquema `src/lib/quoteList.js`, `src/lib/stockSubscriptions.js` y los componentes `QuoteList*`.
- Las acciones no cambian la semantica: StockCentral arma consultas y alertas locales; no vende ni procesa pedidos.

## Alcance de eliminacion

Se elimina unicamente la pantalla y entrypoint del Catalogo despues de comprobar que filtros, cotizacion, alertas y preview funcionan desde Resumen. Los componentes de lista de cotizacion, persistencia y alertas no se borran. El CSS que quede sin consumidores directos puede conservarse hasta una limpieza especifica posterior; no se hara una poda masiva mezclada con este cambio.

## Pruebas y verificacion

- El contrato de assets debe exigir que `index.html` y `resumen.html` carguen `summary.js`.
- Debe exigir que `CatalogApp.svelte` y `catalog.js` no existan.
- Debe verificar que `SummaryApp` renderice `thumbnail_url || image_url` junto a `material_swatch_url` y conserve `colorSwatchStyle` como fallback.
- Debe verificar los nueve filtros, la franja de ayuda, `+1`, campanita, lista de cotizacion y preview ampliado desde `SummaryApp`.
- Debe verificar que el encabezado ya no contenga la opcion `Catalogo`.
- La suite Python completa y `npm run build` deben pasar.
- El build final debe producir `index.html`, `resumen.html` y `estadisticas.html`.
