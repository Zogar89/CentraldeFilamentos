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
- Escribir logs publicos de salud del build.
- Committear los datos generados en `master`.
- Copiar `public/data/*.json` a `gh-pages/data/`.

No debe:

- Ejecutar `npm run build`.
- Generar miniaturas.
- Tocar assets de UI.

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
