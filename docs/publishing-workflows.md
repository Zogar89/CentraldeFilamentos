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
- Reutilizar las rutas de muestras de color existentes, sin renderizar imagenes durante la captura.
- Actualizar snapshots e historial de proveedores.
- Mantener el registro interno de colores provisionales detectados en titulos de proveedores.
- Escribir logs publicos de salud del build.
- Committear los datos generados en `master`.
- Copiar `public/data/*.json` a `gh-pages/data/`.

### Reglas de captura y recuperación

La captura decide por proveedor. Se publica una actualización parcial cuando al menos una fuente pasa los controles y el catálogo resultante es válido.

| Situación | Resultado y recuperación |
| --- | --- |
| Fallo de lectura o respuesta sin productos o cantidades interpretables | Se hacen dos intentos de lectura ante errores del conector. Si la fuente queda pendiente, se muestran sus últimas ofertas válidas con su fecha original. La siguiente captura puede volver a actualizarla. |
| Dos productos diferentes quedan con el mismo identificador y proveedor | Se conserva el último stock válido de esa fuente. El log técnico registra el identificador y los títulos en conflicto para corregir el conector o la normalización. |
| Caída sospechosa de una fuente | Se aplica el mismo resguardo cuando pierde más del 40% de las filas con una referencia de al menos 50, o más del 60% de las unidades con una referencia de al menos 100. Si persiste, contrastar la planilla o página original y la lectura del conector antes de ajustar una regla. |
| Fuente sin una lectura válida anterior | Queda marcada como pendiente y sus ofertas quedan vacías hasta la primera lectura aceptada. |
| Todas las fuentes fallan, el resultado es inválido o el catálogo cae por encima del control global | Se conserva `stock.json` y se publica el diagnóstico de la corrida. Si el archivo de referencia ya está dañado, Actions corta la publicación. Se puede recuperar la última versión válida desde el historial de Git o de Pages y volver a ejecutar la captura. |
| Falla una lectura auxiliar de imágenes, colores o historial | Se registra el aviso. Si el stock pasa los controles, puede actualizarse mientras se corrige el archivo o la fuente auxiliar. |

El catálogo indica qué proveedores muestran datos anteriores. Esas ofertas quedan fuera de la cobertura confirmada de cotizaciones. El historial y las variaciones incluyen únicamente lecturas aceptadas. Un cero medido sigue siendo un dato válido.

Los tres workflows de publicación comparten una cola. Cada uno empieza desde el `master` vigente al recibir su turno. La publicación a Pages reintenta hasta tres veces sobre el último estado de la rama, con avance rápido de Git. Si la captura ya guardó datos en `master` y falló la publicación, volver a ejecutar `Capture Stock Data` en `master`. Puede republicar los JSON vigentes aunque no haya un nuevo commit de stock.

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
- Publicar el HTML y los recursos compilados de `dist/` en `gh-pages`. Cuando ya existe una publicación, los datos y recursos de producto se conservan.

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
- Generar miniaturas.

### Publish Thumbnails

Archivo: `.github/workflows/thumbnails.yml`

Responsabilidad:

- Generar miniaturas WebP desde imagenes fuente.
- Committear cambios en `public/assets/thumbs`.
- Publicar los recursos de producto y el conjunto de JSON de captura de `master` en `gh-pages`.

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
3. Ejecutar `Run workflow` en `master`.
4. Revisar el estado en `data/build_business_log.json` y las fechas `last_success_at` por proveedor en `data/stock.json`. Una captura parcial puede mostrar fechas diferentes.

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

## Alarma de fuentes sin cambios

Cada proveedor conserva en `stock.json` una firma de sus filas de inventario (`stock_signature`) y la fecha desde la que se observa ese mismo contenido (`stock_unchanged_since`). El orden de las filas y las fechas de consulta no renuevan esa fecha. Un cambio de cantidades, productos o URL de la fuente inicia una nueva observación. El estado se guarda únicamente cuando la captura supera los controles de calidad.

El pie de proveedores distingue **Última lectura** de **Sin cambios observados desde**. La alarma se activa únicamente desde las 120 horas sin cambios de stock detectados y cuenta desde `stock_unchanged_since`. La fecha de lectura es informativa y no activa ni reinicia la alarma. El navegador evalúa el plazo al abrir la página, cada minuto y al volver a la pestaña. Fechas ausentes, inválidas o futuras no se presentan como una actualización confirmada.

El seguimiento comienza con la primera captura que contiene estos campos. La fecha describe una observación de Central de Filamentos: el mismo stock durante cinco días no demuestra que el proveedor haya dejado de editar su fuente. El aviso pide confirmar disponibilidad y no bloquea capturas ni cambia cantidades. Se muestra en la web; no envía mensajes, emails ni notificaciones fuera de ella.

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
