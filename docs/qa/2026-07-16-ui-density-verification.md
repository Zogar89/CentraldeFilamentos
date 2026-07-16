# Verificación de densidad UI — 2026-07-16

## Resultado

- Build: PASS — `npm run build` terminó con exit 0; Vite 8.0.16 transformó 289 módulos y finalizó en 1.20 s.
- Node tests: BASELINE KNOWN ISSUE — `node --test tests/*.test.js` terminó con 45 pass y 3 fail: las suites huérfanas `quoteWorkspace`, `stockWatchWorkspace` y `summaryRows` importan módulos que no existen. No pertenecen al cambio de densidad y no se modificaron.
- Pytest: PASS — ejecución elevada del controlador con `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos`: 252 passed, 1 `PytestCacheWarning` no bloqueante, exit 0. La advertencia sigue siendo la ACL de `.pytest_cache` en el worktree.
- Playwright (8 proyectos, Chrome): PASS — `npm.cmd run test:ui` sobre el HEAD exacto `2d82ab1` salió con exit 0. La matriz final completa enumeró 176 casos, con 95 passed, 81 skipped y 49.7 s totales. No hubo fallos responsive ni de overflow, y no aparecieron violaciones axe serious/critical.
- Contrato exacto de quick lines: PASS — rerun focalizado en `desktop-1080`, `mobile-390` y `mobile-landscape`: 3 passed en 2.9 s, exit 0.

## Métricas observadas

- Contenedor 4K/2K: 1180 px máximo, centrado.
- Quick lines: 30 px desktop / 32 px móvil.
- Campanas: 24 x 24 px.
- `+1`: 42 x 28 px desktop / 40 x 36 px móvil.
- Celda de color móvil: 36 px.
- Color Picker: input 48 x 40 px; tiles con mínimo de 42 px desktop y 34 px móvil; hitbox del mapa 44 x 44 px.
- Overflow: 0 en todas las páginas inspeccionadas; en el mapa Color Picker móvil sólo desborda horizontalmente su scroller interno previsto.
- Las métricas visuales y los resultados PASS documentados previamente siguen siendo correctos; esta actualización solo corrige el estado de Playwright para reflejar el rerun completo real.

## Revisión visual

- 4K: PASS — Resumen a 3840 x 2160 con shell de 1180 px, controles compactos y sin overflow.
- 1080p: PASS — Resumen a 1920 x 1080 con densidad restaurada y sin overflow.
- 390 x 844: PASS — Resumen sin solapamientos; medidas móviles esperadas y overflow 0.
- Color Picker desktop/móvil: PASS — 1920 x 1080 y 390 x 844 mantienen dimensiones esperadas, foco/hitbox de mapa y overflow de página 0.
- Evidencia visual retenida:
  - `docs/qa/evidence/ui-density/summary-4k.png`
  - `docs/qa/evidence/ui-density/summary-1080.png`
  - `docs/qa/evidence/ui-density/summary-mobile-390.png`
  - `docs/qa/evidence/ui-density/color-picker-1080.png`
  - `docs/qa/evidence/ui-density/color-picker-mobile-390.png`

## Publicación

- Publicación: pendiente en el estado local actual; no se realizó merge, push ni publicación.
- Merge: no realizado.
- Push: no realizado.
- Rama verificada: `codex/restore-ui-density`.
- La documentación de esta evidencia se commitea localmente por separado; no se declara un hash futuro dentro de este archivo.
