---
phase: quick
plan: 261020-i0y
status: complete
date: 2026-10-20
files_modified:
  - centraldefilamentos/providers.py
  - centraldefilamentos/normalize.py
  - tests/test_providers.py
  - tests/test_normalize.py
  - tests/test_build_data.py
  - centraldefilamentos/data/provider_stock_history.json
  - public/data/stock.json
  - public/data/provider_stock_history.json
  - public/data/build_business_log.json
  - public/data/build_technical_log.json
tasks_completed:
  - 1
  - 2
  - 3
commits:
  - cf4c244bafad66af66f177cc1e73c511644fcd11
  - 3834b297ea6983d49ae2262c04cbed98d476d19f
published_commit: 64b6401b4efd99d77080ddbbb348cf037da28921
---

# Nueva fuente de MundoInsumos

MundoInsumos usa la pestaña **Resumen**, `gid=472098222`, de la [planilla indicada](https://docs.google.com/spreadsheets/d/103_Y1W5b6rYRD1MaVQSJ-2GZQiWYXEb03eEkDjRHaBY/edit?gid=472098222#gid=472098222). El CSV se lee sin autenticación, conserva los encabezados Código/Descripción/Código/STOCK REAL y agrega PEDIDO, que no participa del stock. No fue necesario modificar el conector.

## Compatibilidad e identidades

- La fuente anterior devolvía 239 productos y 10296 unidades. La nueva devolvió 241 productos, 8994 unidades y ningún stock desconocido en las comprobaciones de esta tarea.
- Las dos filas nuevas de PLA+ `CARBOARD EDITION` se confundían con PLA+ común y causaban `ValueError: repeated provider offers`. Se incorporó la variante `PLA+ Cardboard Edition`, reconociendo la escritura del proveedor y `CARDBOARD EDITION` antes de la regla genérica PLA+. La abreviatura CE sola no infiere la edición.
- La edición blanca conserva 183 unidades y la negra 59. Las filas comunes siguen separadas con sus cantidades de cero. Los 239 IDs que ya tenía MundoInsumos permanecen iguales.
- Los títulos de edición indican 1 KG aunque el encabezado de sección dice 750 GR. Se conserva el peso explícito de 1000 g de cada título; no se modifica la planilla ni se inventa otro peso a partir de la sección.

## Validación local

- 104 pruebas focalizadas de proveedores, CSV, normalización y payload: aprobadas. La regresión integrada reproduce los espacios NBSP reales y el encabezado de sección de 750 g.
- `python -m pytest -v --basetemp .image-curation/pytest-mundoinsumos-full`: **294 passed in 36.43s**.
- `npm run test:quote-list`: **18 pruebas aprobadas**.
- `npm run build`: aprobado, Vite 8.0.16.
- Captura completa con salidas aisladas en `.image-curation/mundoinsumos-source-update/`: tres proveedores `ok`, `should_publish=true`, 376 productos y ningún error de enriquecimiento ni color provisional nuevo.
- Se comparó cada nombre y cantidad de MundoInsumos con el CSV contemporáneo: las 241 ofertas coinciden exactamente. Permanecen los 374 IDs anteriores del catálogo y sus referencias `image_url`, `thumbnail_url` y `material_swatch_url`.
- Los hashes SHA-256 de los 1037 archivos de `public/assets` no cambiaron. `git diff --check` pasó.

## Publicación verificada

- Código publicado en `cf4c244bafad66af66f177cc1e73c511644fcd11`, después de incorporar por avance rápido las capturas anteriores del remoto.
- [CI 39454297020](https://github.com/Zogar89/CentraldeFilamentos/actions/runs/39454297020): completado con éxito sobre ese SHA, incluidas las pruebas y el build.
- [Capture Stock Data 39454305889](https://github.com/Zogar89/CentraldeFilamentos/actions/runs/39454305889): completado con éxito sobre ese SHA. El job corrió del 16:05:15 al 16:05:45 UTC, con build, commit y publicación de datos exitosos, sin paso de generación de imágenes.
- El commit automático `3834b297ea6983d49ae2262c04cbed98d476d19f` cambia únicamente cinco JSON: historial interno, historial público, ambos logs y stock. La publicación `64b6401b4efd99d77080ddbbb348cf037da28921` cambia únicamente cuatro JSON en `data/`.
- [stock.json público](https://zogar89.github.io/CentraldeFilamentos/data/stock.json) comprobado sin caché: `generated_at=2026-10-20T13:05:36-03:00`, 376 productos y los tres proveedores `ok`. MundoInsumos usa la nueva URL y tiene 241 productos, 148 con stock, 93 sin stock y 8994 unidades. Ambas ediciones nuevas figuran separadas con 183 y 59 unidades.
- El log técnico público tiene la misma fecha, `status=ok` y `should_publish=true`. El JSON público coincide íntegramente con los archivos de stock de master y gh-pages; las ofertas de MundoInsumos coinciden nuevamente fila por fila con el CSV real.
- Se conservaron las referencias visuales de los 374 productos existentes. El árbol `public/assets` sigue siendo `9f4e45acd54d9d52f4ed213478234c219d7dddad`; el árbol publicado `assets` sigue siendo `d561553c3cfa986e40a8ad4b6c1127a12b3d2f6c`.
- La captura automática queda configurada con la fuente nueva. No quedan dependencias externas pendientes para esta actualización.

## Self-Check: PASSED

Plan, resumen y registro de estado presentes. Commits de implementación y datos comprobados en Git. Pruebas, captura, CI, archivos publicados, correspondencia con el CSV y preservación de imágenes verificados.
