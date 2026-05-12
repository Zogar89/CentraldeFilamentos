# StockCentral

StockCentral centraliza stock online de proveedores de filamento 3D del AMBA para que usuarios de impresion 3D encuentren rapido quien tiene el material, color, marca y formato que necesitan.

## Estado actual

El proyecto esta en implementacion inicial del MVP.

Decisiones principales:

- Sitio estatico publico.
- Python para ingesta y normalizacion.
- GitHub Actions para actualizar stock 2 a 4 veces por dia en horario de oficina.
- GitHub Pages para publicar.
- Proveedores iniciales: Filamentos3D, Grupo Senz y MundoInsumos.
- UI en espanol argentino, compacta, mobile friendly y minimalista.

## Desarrollo local

```bash
python -m pip install -e ".[dev]"
pytest
python -m stockcentral.build_data --output public/data/stock.json
python -m http.server 8000 -d public
```

Abrir `http://localhost:8000`.
La vista compacta de resumen queda en `http://localhost:8000/resumen.html`.

## Datos

El frontend lee `public/data/stock.json`. En produccion, GitHub Actions genera ese archivo y publica `public/` en GitHub Pages.

## Documentacion

- Spec de producto: `docs/superpowers/specs/2026-05-12-stockcentral-design.md`
- Plan de implementacion: `docs/superpowers/plans/2026-05-12-stockcentral-mvp.md`
- Handoff de sesion y preguntas pendientes: `docs/superpowers/session-handoff-2026-05-12.md`

## Proximo paso

Implementar el MVP siguiendo el plan desde Task 1: scaffold Python, modelos y tests.
