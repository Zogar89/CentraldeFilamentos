# Publicacion y workflows

Central de Filamentos publica un sitio estatico en GitHub Pages desde la rama `gh-pages`.

La idea principal es separar responsabilidades: capturar stock no debe reconstruir la interfaz, generar miniaturas no debe correr en cada captura, y un cambio visual no debe disparar scraping de proveedores.

## Rama publicada

GitHub Pages esta configurado con:

- `build_type: legacy`
- branch: `gh-pages`
- path: `/`

La rama `master` contiene el codigo fuente, tests, datos fuente versionados y workflows. La rama `gh-pages` contiene solamente el sitio estatico que ve el usuario.

## Workflows

### Capture Stock Data

Archivo: `.github/workflows/data-capture.yml`

Responsabilidad:

- Correr el scraper.
- Generar `public/data/stock.json`.
- Actualizar snapshots e historial de proveedores.
- Mantener el registro interno de colores provisionales detectados en titulos de proveedores.
- Escribir logs publicos de salud del build.
- Committear los datos generados en `master`.
- Copiar `public/data/*.json` a `gh-pages/data/`.

No debe:

- Ejecutar `npm run build`.
- Generar miniaturas.
- Tocar assets de UI.
- Copiar `centraldefilamentos/data/color_registry.json` a GitHub Pages.

Schedule:

- Lunes a viernes a las 12, 15, 18 y 21 UTC.
- Equivale a 09, 12, 15 y 18 hs Argentina.

### Publish UI

Archivo: `.github/workflows/pages.yml`

Responsabilidad:

- Instalar dependencias frontend.
- Ejecutar `npm run build`.
- Copiar `dist/` a la raiz de `gh-pages`.

Corre cuando cambian archivos de interfaz o configuracion:

- `src/**`
- `index.html`
- `resumen.html`
- `estadisticas.html`
- `package.json`
- `package-lock.json`
- `vite.config.js`
- `svelte.config.js`
- el propio workflow

No debe:

- Scrappear proveedores.
- Regenerar stock.
- Instalar Python.
- Generar miniaturas.

### Publish Thumbnails

Archivo: `.github/workflows/thumbnails.yml`

Responsabilidad:

- Generar miniaturas WebP desde imagenes fuente.
- Committear cambios en `public/assets/thumbs`.
- Publicar `assets/` y `data/stock.json` en `gh-pages`.

Corre manualmente o cuando cambian imagenes fuente en `public/assets/**`, excluyendo `public/assets/thumbs/**`.

No debe:

- Correr con cada captura de datos.
- Reconstruir la UI.
- Scrappear proveedores.

## CI

Archivo: `.github/workflows/ci.yml`

Responsabilidad:

- Ejecutar tests Python.
- Ejecutar build frontend.

Ignora pushes que solo cambian datos o assets:

- `centraldefilamentos/data/**`
- `public/data/**`
- `public/assets/**`

Esto evita gastar CI en commits automaticos de stock o miniaturas.

## Mantenimiento manual

Para probar captura de stock sin esperar cron:

1. Ir a Actions.
2. Elegir `Capture Stock Data`.
3. Ejecutar `Run workflow`.
4. Verificar que el run publique solo cambios de `data/` en `gh-pages`.

Para publicar una nueva UI:

1. Cambiar archivos frontend.
2. Push a `master`.
3. `Publish UI` corre automaticamente por paths.

Para regenerar miniaturas:

1. Cambiar o agregar imagenes fuente en `public/assets/`.
2. Push a `master`, o ejecutar `Publish Thumbnails` manualmente.
3. Verificar que `public/assets/thumbs/` y `gh-pages/assets/` queden actualizados.

### Revision de colores provisionales

`centraldefilamentos/data/color_registry.json` es estado interno versionado. Cuando un titulo de proveedor tiene un color que aun no coincide con `COLOR_RULES`, la captura lo incorpora con una identidad estable y estado `provisional`; el catalogo indica que es una etiqueta del proveedor pendiente de normalizar.

Despues de una captura exitosa:

1. Revisar el diff del registry y el warning `provisional_colors` de `public/data/build_technical_log.json`.
2. Confirmar el titulo fuente del proveedor. No usar este registro para inferir Pantone, RGB, foto o equivalencia fisica.
3. Si se acepta la etiqueta tal como viene del proveedor, cambiar solo su `status` de `provisional` a `approved`. Se conserva la misma identidad y en la proxima captura desaparece el aviso del catalogo.
4. Si se quiere agregar una equivalencia canonica a `COLOR_RULES`, hacerlo en un cambio revisado aparte que considere la migracion de identidad; nunca se fusiona automaticamente desde el registry.

Una captura bloqueada por controles de calidad no actualiza el registry, los snapshots, el historial ni `stock.json`.

Para incorporar un color a la normalizacion global, agregar su etiqueta a `COLOR_RULES` con los nombres compuestos antes de los genericos (por ejemplo, `Malaquita Verde` antes de `Verde`, y `Gris Plata` antes de `Plata`). Las medidas del titulo, incluso `1,75MM` o `500GR`, no forman parte del nombre de un color provisional.

El selector de colores PLA necesita un Pantone resuelto o una entrada en `centraldefilamentos/data/color_estimates.json`. Si solo se conoce el nombre del proveedor, usar `source: name_only`, confianza `low` y un aviso explicito de que no hay foto ni Pantone verificados. Luego regenerar datos y muestras con `python -m centraldefilamentos.build_data --output public/data/stock.json` y `python -m centraldefilamentos.generate_material_swatches --stock-json public/data/stock.json --public-dir public`.

Las fotos 3N3 verificadas en otros proveedores se conservan, junto con su procedencia y estado de revision, en `centraldefilamentos/data/3n3_reviewed_metadata.json`. El build las combina con la cache de Filamentos3D por identidad exacta. Ver la [revision de 3N3 Silk del 16/10/2026](research/2026-10-16-3n3-silk.md) para el conjunto de fotos uniforme y los pendientes.

## Checks utiles

Ver configuracion de Pages:

```bash
gh api repos/Zogar89/CentraldeFilamentos/pages --jq '{build_type,source,html_url}'
```

Ver ultimos runs:

```bash
gh run list --limit 10
```

Ver datos publicados sin cache:

```bash
curl "https://zogar89.github.io/CentraldeFilamentos/data/provider_stock_history.json?v=$(date +%s)"
```
