# Roadmap: Central de Filamentos Quote List

## Overview

Este milestone convierte el catalogo estatico en una herramienta local de compra/cotizacion: el usuario arma una lista en su navegador, puede moverla entre dispositivos mediante import/export, entiende que proveedores cubren cada item y termina con consultas de WhatsApp individuales que piden cotizacion y disponibilidad sin convertir a StockCentral en tienda, checkout ni procesador de pedidos.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Quote List Foundation** - Usuarios pueden armar y mantener una lista local de cotizacion desde el catalogo. (completed 2026-06-19)
- [ ] **Phase 2: Portability And Import/Export Resilience** - Usuarios pueden guardar o mover su lista sin cuentas ni sincronizacion cloud.
- [ ] **Phase 3: Provider Coverage Semantics** - Usuarios pueden ver que proveedor cubre cada item y cuando cubre toda la lista.
- [ ] **Phase 4: WhatsApp Quote Flow** - Usuarios pueden copiar listados y enviar consultas por proveedor solo con items cubiertos.

## Phase Details

### Phase 1: Quote List Foundation

**Goal:** As a maker, I want to build a local quote list from the catalog, so that I can plan filament purchases.
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: LIST-01, LIST-02, LIST-03, LIST-04, LIST-05, ITEM-01, ITEM-02, ITEM-03, PERS-01, PERS-02, DISC-01
**Success Criteria** (what must be TRUE):

  1. Usuario puede agregar un filamento desde el catalogo y verlo en una lista presentada como herramienta de compra/cotizacion, no como carrito.
  2. Usuario puede editar la cantidad entera de unidades, sumar +1 o completar una caja de 12, quitar items y limpiar la lista.
  3. Cada item visible conserva material, color, marca, diametro, cantidad y codigo de articulo cuando el catalogo lo provee.
  4. Usuario ve cuando un dato clave falta o debe confirmarse con el proveedor.
  5. Usuario ve que la lista se guarda automaticamente solo en este navegador/dispositivo y que StockCentral no vende ni procesa pedidos.

**Plans**: 3/3 plans complete
Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Crear el slice inicial de agregar presentaciones a Lista de cotizacion con autosave local.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Completar cantidades en carretes, controles rapidos, quitar/limpiar y badges de item.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md — Cerrar responsive desktop/mobile, reconciliacion, storage fallback y notices local-only/no-commerce.

**UI hint**: yes

### Phase 2: Portability And Import/Export Resilience

**Goal**: Usuarios pueden exportar e importar la lista local con validacion suficiente para moverla o resguardarla sin romper su lista actual.
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: PERS-03, PERS-04, PERS-05
**Success Criteria** (what must be TRUE):

  1. Usuario puede exportar su lista actual como archivo reutilizable.
  2. Usuario puede importar una lista exportada y entender el resultado antes de perder cambios existentes.
  3. Una importacion con formato o version invalida se rechaza con un mensaje claro y conserva la lista actual.
  4. Una lista importada se muestra como lista local editable y vuelve a guardarse en este navegador/dispositivo.

**Plans**: TBD
**UI hint**: yes

### Phase 3: Provider Coverage Semantics

**Goal**: Usuarios pueden comparar proveedores por cobertura real de la lista y entender que items cubre cada uno segun el catalogo estatico vigente.
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: COV-01, COV-02, COV-03, COV-04
**Success Criteria** (what must be TRUE):

  1. Usuario puede ver para cada proveedor cuantos items cubre sobre el total de la lista.
  2. Usuario puede ver checks por item cuando un proveedor cumple stock y caracteristicas del item.
  3. Usuario puede identificar rapidamente cuando un proveedor cubre toda la lista.
  4. Usuario puede abrir bloques o pestanas por proveedor y ver solo los items que ese proveedor cubre.
  5. Usuario entiende que la cobertura se basa en el catalogo publicado y que disponibilidad/precio final deben confirmarse.

**Plans**: TBD
**UI hint**: yes

### Phase 4: WhatsApp Quote Flow

**Goal**: Usuarios pueden transformar la lista y la cobertura por proveedor en textos de consulta y enlaces individuales de WhatsApp sin incluir items faltantes.
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: MSG-01, MSG-02, MSG-03, MSG-04, MSG-05, MSG-06, DISC-02
**Success Criteria** (what must be TRUE):

  1. Usuario puede copiar un listado completo general de su lista de cotizacion.
  2. Usuario puede previsualizar y copiar un mensaje por proveedor en tono de consulta.
  3. Cada mensaje por proveedor incluye solo los items que ese proveedor cubre.
  4. Usuario puede abrir WhatsApp individualmente para cada proveedor con el mensaje prellenado cuando hay contacto disponible.
  5. Usuario ve un fallback de copiar texto cuando WhatsApp no esta disponible, el contacto falta o el link es demasiado largo.

**Plans**: TBD
**UI hint**: yes

## Future v2 Refinements

Los refinamientos como ranking avanzado, deteccion de duplicados, listas nombradas, plantillas editables y registro de cotizaciones quedan fuera del v1 salvo que se promuevan explicitamente desde REQUIREMENTS.md.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Quote List Foundation | 3/3 | Complete    | 2026-06-19 |
| 2. Portability And Import/Export Resilience | 0/TBD | Not started | - |
| 3. Provider Coverage Semantics | 0/TBD | Not started | - |
| 4. WhatsApp Quote Flow | 0/TBD | Not started | - |
