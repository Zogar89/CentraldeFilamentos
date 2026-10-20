---
phase: quick
plan: 261020-k2s
status: complete
date: 2026-10-20
tasks_completed: [1, 2]
commits:
  - 0c5ac001f0a97adebc3529daaf5845f96862d951
published_commit: 3c0f3239c1402ded6eb3c87eeb24178112fbf87e
---

# Alarma exclusivamente por stock sin cambios

La aclaración del usuario «Me refiero a sin cambios» sustituye la interpretación anterior. La única condición de alarma es stock_unchanged_since con al menos 120 horas de antigüedad. Última lectura permanece informativa; su edad no activa el aviso ni determina su cantidad de días.

## Cambio y validación

- Se eliminó la rama unread del helper JavaScript y se ajustaron el copy del pie, las pruebas, la documentación y el canon de diseño. No se modificaron Python, firmas, fechas de observación, datos ni imágenes.
- Las siete pruebas Node pasan: lectura antigua con baseline reciente o ausente no alerta; baseline de ocho días y lectura de seis avisa ocho días sin cambios; lectura reciente con baseline de cinco sí alerta. Se mantienen límites exactos, husos horarios, fechas inválidas y aislamiento por fuente.
- Cuatro pruebas E2E aprobadas en desktop-1080 y mobile-360 en 12.2 s, incluidos avance del reloj y Axe sin violaciones serias o críticas. El build Vite pasó como parte del servidor de pruebas. Resultados aislados en .image-curation/source-alarm-no-changes/playwright.
- git diff --check pasó; el detector de Impeccable no encontró advertencias en SiteFooter.

## Publicación y preservación

- Implementación publicada en 0c5ac001f0a97adebc3529daaf5845f96862d951.
- [CI 39466735465](https://github.com/Zogar89/CentraldeFilamentos/actions/runs/39466735465) aprobó Python, cotización, pruebas de frescura y build.
- [Publish UI 39466735392](https://github.com/Zogar89/CentraldeFilamentos/actions/runs/39466735392) terminó correctamente y publicó 3c0f3239c1402ded6eb3c87eeb24178112fbf87e.
- Chrome móvil verificó en el sitio público el texto «Alarma desde los 5 días sin cambios de stock detectados», tres proveedores y cero seguimientos pendientes.
- El stock público es idéntico al snapshot tomado antes del ajuste. Las tres fechas stock_unchanged_since siguen en 2026-10-20T14:24:07-03:00. El diff publicado no cambia data ni los árboles de imágenes de producto. No se ejecutó ninguna captura nueva.

## Self-Check: PASSED

Plan y resumen presentes; commit, pruebas, UI pública y continuidad del seguimiento comprobados. No quedan pasos pendientes para esta corrección.
