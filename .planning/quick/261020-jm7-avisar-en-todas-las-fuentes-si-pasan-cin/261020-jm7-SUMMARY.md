---
phase: quick
plan: 261020-jm7
status: complete
date: 2026-10-20
tasks_completed: [1, 2, 3]
commits:
  - 98a3dbc8745ddbb5a44fe1f48217b87f9e68452e
  - 883afbef0852a92d0650e5d6f75a3c38beb973b8
published_commit: 846794f2d25623926c39f8e4524c4f51f568022b
---

# Alarmas de fuentes después de cinco días

Los proveedores muestran por separado su última lectura válida y desde cuándo se observa el mismo inventario. A las 120 horas sin cambios de stock o sin lectura válida aparece un aviso textual con icono que pide confirmar disponibilidad. Una consulta exitosa con el mismo contenido conserva el plazo.

## Alcance y criterio

- Se consultaron criterio y canal mediante dos preguntas juntas. Al no recibir respuesta durante el trabajo independiente, se anunció el supuesto de alarmas en la web, junto a cada proveedor, por stock sin cambios, distinguiendo también falta de lectura válida. No se creó una automatización de chat, correo ni notificaciones externas.
- El seguimiento se inicia con la primera captura del nuevo esquema. No se infiere una fecha histórica de modificación real del proveedor. El texto dice «sin cambios observados»: no afirma que una fuente idéntica haya dejado de editarse.
- Se mantienen la arquitectura estática, las cantidades, los controles de calidad y la separación de captura e imágenes.

## Implementación

- SourceStatus incorpora stock_signature y stock_unchanged_since con defaults compatibles. El nuevo helper Python firma los pares nombre/cantidad ordenados por fuente, preserva duplicados y distingue cero de desconocido. Timestamps, orden y metadatos de imágenes no reinician el plazo; cambios de inventario o URL sí lo reinician.
- main carga una sola vez el payload previo aceptado y aplica continuidad antes de calidad. Los errores conservan la última lectura válida y el estado anterior. Un build bloqueado no persiste fechas ni firmas nuevas.
- El helper JavaScript usa un reloj inyectable y un umbral exacto de 120 horas. Distingue lectura vencida de stock sin cambios, trata fechas inválidas o futuras sin inventar antigüedad y funciona con payloads anteriores.
- El pie compartido usa el reloj del navegador al abrir, cada minuto y al volver a la pestaña; limpia temporizador y listener al desmontar. Cambió «Actualizado» por «Última lectura» sin usar el último intento como éxito.
- Se agregaron pruebas Node al script test:source-freshness y a CI. El canon de diseño y la documentación de publicación explican las fechas, el umbral y el alcance del aviso.

## Verificación

- Python: **313 passed in 37.55s** con temporal propio .image-curation/pytest-source-alarm-full.
- Node: **7 pruebas de frescura** y **18 pruebas de cotización** aprobadas.
- Build Vite aprobado. Suite UI en desktop-1080 y mobile-360: **53 aprobadas, 3 omitidas por condiciones de la suite, 59.5 s**, con Chrome y resultados aislados en .image-curation/source-alarm/playwright-full. Las cuatro pruebas focalizadas de alarmas también pasaron.
- Casos cubiertos: reordenación, metadatos, redistribución con total igual, altas/bajas, duplicados, cero/desconocido, cambio de URL, independencia por fuente, migración, errores, bloqueo, fechas inválidas/futuras, 119 h 59 min, 120 h y avance del reloj con la página abierta.
- Axe verificó los estados de alarma sin violaciones serias o críticas. QA visual a 1440 x 900 y 390 x 844: estados sin cambios, sin lectura y vigente; sin overflow. Evidencia local en .image-curation/source-alarm/after-desktop.png, after-mobile.png y visual-qa.json.
- Impeccable detect reportó cinco advertencias preexistentes de estilos fuera del diff; ninguna pertenece a los nuevos avisos.
- Captura real aislada: 376 productos, tres fuentes ok, should_publish=true y baseline inicial coherente. Las referencias visuales de los 376 productos permanecieron iguales. git diff --check aprobado.

## Publicación comprobada

- Código integrado y publicado en 98a3dbc8745ddbb5a44fe1f48217b87f9e68452e.
- [CI 39465407546](https://github.com/Zogar89/CentraldeFilamentos/actions/runs/39465407546) y [Publish UI 39465407547](https://github.com/Zogar89/CentraldeFilamentos/actions/runs/39465407547) terminaron correctamente. CI incluyó Python, cotización, nuevas pruebas de frescura y build.
- Después de finalizar la publicación de UI se ejecutó [Capture Stock Data 39465696945](https://github.com/Zogar89/CentraldeFilamentos/actions/runs/39465696945), también exitosa. Ese orden evita que un dist construido antes de la captura sobrescriba los nuevos campos.
- El commit automático 883afbef0852a92d0650e5d6f75a3c38beb973b8 solo cambia cinco JSON: historial interno/público, logs y stock. La publicación de datos quedó en 846794f2d25623926c39f8e4524c4f51f568022b.
- [stock.json público](https://zogar89.github.io/CentraldeFilamentos/data/stock.json), consultado sin caché, tiene generated_at **2026-10-20T14:24:07-03:00**, tres proveedores ok y, para cada uno, firma SHA-256 de 64 caracteres y stock_unchanged_since/last_success_at de esa primera observación.
- El log técnico público tiene la misma fecha y should_publish=true. El JSON servido coincide con master y gh-pages. Se preservaron las referencias de imágenes de los 376 productos y los seis árboles de assets de producto: brands, filamentos3d, grilon3, material-swatches, reviewed y thumbs.
- Comprobación del sitio público en Chrome, sin mocks: regla visible de cinco días, tres bloques con «Última lectura» y «Sin cambios observados desde 20/10/26, 14:24», cero seguimientos pendientes y cero alarmas iniciales, como corresponde a una observación recién iniciada.

## Self-Check: PASSED

Plan y resumen presentes, commits comprobados, suites y QA aprobadas, UI y datos públicos verificados. No quedan pasos pendientes para la alarma web solicitada.
