# Verificación de densidad UI — 2026-07-16

## Resultado

- Build: PASS — `npm run build` terminó con exit 0; Vite 8.0.16 transformó 289 módulos y finalizó en 1.20 s.
- Node tests: BASELINE KNOWN ISSUE — `node --test tests/*.test.js` terminó con 45 pass y 3 fail: las suites huérfanas `quoteWorkspace`, `stockWatchWorkspace` y `summaryRows` importan módulos que no existen. No pertenecen al cambio de densidad y no se modificaron.
- Pytest: PASS — ejecución elevada del controlador con `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos`: 252 passed en 34.58 s, exit 0. Hubo una única `PytestCacheWarning` no bloqueante porque la ACL de `.pytest_cache` en el worktree deniega acceso.
- Playwright (8 viewports, Chrome): PASS con rerun focalizado posterior al ajuste de contrato. La única matriz completa ejecutada enumeró sus 176 casos en los ocho proyectos y no se colgó; los dos fallos iniciales de `mobile-landscape` eran expectativas que confundían el nombre del proyecto con el breakpoint CSS. `f85148c` usa ancho de viewport (`<= 860` para quick lines; `<= 520` para acciones compactas) y el rerun de esos dos casos dio 2/2 pass, exit 0. No se repitió la matriz completa.
- Axe serious/critical: 0 — los checks de accesibilidad de la matriz completa no reportaron violaciones serious ni critical.

## Métricas observadas

- Contenedor 4K/2K: 1180 px máximo, centrado.
- Quick lines: 30 px desktop / 32 px móvil.
- Campanas: 24 x 24 px.
- `+1`: 42 x 28 px desktop / 40 x 36 px móvil.
- Celda de color móvil: 36 px.
- Color Picker: input 48 x 40 px; tiles con mínimo de 42 px desktop y 34 px móvil; hitbox del mapa 44 x 44 px.
- Overflow: 0 en todas las páginas inspeccionadas; en el mapa Color Picker móvil sólo desborda horizontalmente su scroller interno previsto.

## Revisión visual

- 4K: PASS — Resumen a 3840 x 2160 con shell de 1180 px, controles compactos y sin overflow.
- 1080p: PASS — Resumen a 1920 x 1080 con densidad restaurada y sin overflow.
- 390 x 844: PASS — Resumen sin solapamientos; medidas móviles esperadas y overflow 0.
- Color Picker desktop/móvil: PASS — 1920 x 1080 y 390 x 844 mantienen dimensiones esperadas, foco/hitbox de mapa y overflow de página 0.
- Evidencia visual: cinco vistas inspeccionadas en Chrome real por el controlador.

## Publicación

- Publicación: no realizada por instrucción explícita de esta tarea.
- Merge: no realizado.
- Push: no realizado.
- Rama verificada: `codex/restore-ui-density`.
- La documentación de esta evidencia se commitea localmente por separado; no se declara un hash futuro dentro de este archivo.
