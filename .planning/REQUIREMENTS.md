# Requirements: Central de Filamentos

**Defined:** 2026-06-19
**Core Value:** Ayudar al maker a convertir la informacion dispersa de stock de filamento en una consulta clara y accionable para comprar mejor, sin que StockCentral venda ni procese pedidos.

## v1 Requirements

Requirements for the quote-list milestone. Each maps to roadmap phases.

### Lista Local

- [x] **LIST-01**: Usuario puede agregar un filamento a la lista desde el catalogo.
- [x] **LIST-02**: Usuario puede ver la lista como herramienta de compra/cotizacion, no como carrito.
- [x] **LIST-03**: Usuario puede editar la cantidad entera de carretes por item.
- [x] **LIST-04**: Usuario puede sumar rapido `+1`, `+6` y `+12` carretes.
- [x] **LIST-05**: Usuario puede quitar items y limpiar la lista.

### Datos Del Item

- [x] **ITEM-01**: Cada item conserva material, color, marca, diametro y cantidad.
- [x] **ITEM-02**: Cada item conserva codigo de articulo cuando el catalogo lo provee.
- [x] **ITEM-03**: La UI indica cuando algun dato clave no esta disponible o debe confirmarse.

### Persistencia

- [x] **PERS-01**: La lista se guarda automaticamente en este navegador/dispositivo.
- [x] **PERS-02**: La UI avisa que la lista local no se sincroniza y puede no estar disponible desde otra PC/navegador.
- [ ] **PERS-03**: Usuario puede exportar la lista como archivo.
- [ ] **PERS-04**: Usuario puede importar una lista exportada.
- [ ] **PERS-05**: La importacion valida formato/version y evita romper la lista actual.

### Cobertura Por Proveedor

- [ ] **COV-01**: Usuario puede ver cuantos items cubre cada proveedor (`X/Y`).
- [ ] **COV-02**: Usuario puede ver checks por item cuando un proveedor cumple stock/caracteristicas.
- [ ] **COV-03**: Usuario puede ver un check general cuando un proveedor cubre toda la lista.
- [ ] **COV-04**: Usuario puede abrir bloques o pestanas por proveedor con los items cubiertos.

### Mensajes Y WhatsApp

- [ ] **MSG-01**: Usuario puede copiar el listado completo general.
- [ ] **MSG-02**: Usuario puede previsualizar y copiar un mensaje por proveedor.
- [ ] **MSG-03**: El mensaje por proveedor incluye solo items que ese proveedor cubre.
- [ ] **MSG-04**: Usuario puede abrir WhatsApp individualmente para cada proveedor con mensaje prellenado.
- [ ] **MSG-05**: El mensaje pide cotizacion y disponibilidad, sin afirmar compra ni stock garantizado.
- [ ] **MSG-06**: La UI ofrece fallback de copiar texto si WhatsApp no esta disponible o el link es demasiado largo.

### Transparencia

- [x] **DISC-01**: La UI comunica que StockCentral no vende productos ni procesa pedidos.
- [ ] **DISC-02**: La UI comunica que el proveedor debe confirmar disponibilidad y precio final.

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Refinamientos

- **REF-01**: Usuario puede ver proveedores rankeados por cobertura y criterios adicionales despues de validar uso real.
- **REF-02**: Usuario puede detectar items duplicados o similares dentro de la lista.
- **REF-03**: Usuario puede crear listas nombradas para proyectos recurrentes.
- **REF-04**: Usuario puede ajustar plantillas de mensaje por proveedor.
- **REF-05**: Usuario puede registrar cotizaciones recibidas sin convertir StockCentral en sistema de pedidos.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Checkout, pagos o ordenes procesadas por StockCentral | La plataforma no vende ni debe operar como marketplace o e-commerce. |
| Backend persistente, cuentas, login o sincronizacion cloud | El producto se mantiene como sitio estatico en GitHub Pages. |
| Optimizacion automatica multi-proveedor | Requiere reglas de optimizacion, precios confiables y puede confundir antes de validar el flujo base. |
| Seguimiento de cotizaciones recibidas en v1 | Acerca el producto a procurement; primero hay que validar la lista y el envio de consultas. |
| Listas nombradas o historial de listas en v1 | Aumenta complejidad local; puede pasar a v2 si los makers usan la herramienta recurrentemente. |
| Compartir lista por URL publica | Riesgo de longitud, privacidad y compatibilidad; import/export cubre la portabilidad inicial. |
| Mensajes de WhatsApp con items que el proveedor no cubre | En v1 cada proveedor recibe solo los items cubiertos para mantener consultas limpias. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| LIST-01 | Phase 1 | Complete |
| LIST-02 | Phase 1 | Complete |
| LIST-03 | Phase 1 | Complete |
| LIST-04 | Phase 1 | Complete |
| LIST-05 | Phase 1 | Complete |
| ITEM-01 | Phase 1 | Complete |
| ITEM-02 | Phase 1 | Complete |
| ITEM-03 | Phase 1 | Complete |
| PERS-01 | Phase 1 | Complete |
| PERS-02 | Phase 1 | Complete |
| PERS-03 | Phase 2 | Pending |
| PERS-04 | Phase 2 | Pending |
| PERS-05 | Phase 2 | Pending |
| COV-01 | Phase 3 | Pending |
| COV-02 | Phase 3 | Pending |
| COV-03 | Phase 3 | Pending |
| COV-04 | Phase 3 | Pending |
| MSG-01 | Phase 4 | Pending |
| MSG-02 | Phase 4 | Pending |
| MSG-03 | Phase 4 | Pending |
| MSG-04 | Phase 4 | Pending |
| MSG-05 | Phase 4 | Pending |
| MSG-06 | Phase 4 | Pending |
| DISC-01 | Phase 1 | Complete |
| DISC-02 | Phase 4 | Pending |

**Coverage:**

- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0

---
*Requirements defined: 2026-06-19*
*Last updated: 2026-06-19 after roadmap creation*
