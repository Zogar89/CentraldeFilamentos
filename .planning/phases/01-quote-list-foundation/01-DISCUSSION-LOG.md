# Phase 1: Quote List Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-19
**Phase:** 1-Quote List Foundation
**Areas discussed:** Donde aparece la lista, Como se agrega un filamento, Que guarda cada item, Cantidad y controles, Framing y avisos, Autosave y limpiar lista

---

## Donde aparece la lista

| Option | Description | Selected |
|--------|-------------|----------|
| Panel lateral en desktop + boton flotante en mobile | En desktop se ve a la derecha si hay ancho suficiente; en mobile se abre desde un boton/lista. | yes |
| Seccion fija debajo de filtros | Siempre visible arriba del catalogo. | |
| Solo boton en header | Mas limpio, menos visible mientras se arma la lista. | |
| Otro | Freeform. | |

**User's choice:** Panel lateral en desktop + boton flotante en mobile.
**Notes:** En desktop el panel aparece solo cuando hay items. En mobile el boton flotante muestra icono de lista/checklist + contador y abre drawer inferior.

---

## Como se agrega un filamento

| Option | Description | Selected |
|--------|-------------|----------|
| En cada presentacion | Agrega una presentacion sin elegir proveedor. | yes |
| En cada oferta de proveedor | Agrega desde proveedor especifico. | |
| En el producto base/color | Agrega desde el producto agrupado. | |
| Otro | Freeform. | |

**User's choice:** En cada presentacion.
**Notes:** El usuario corrigio la unidad de negocio: no kg, sino `carrete`. Al tocar agregar suma `+1 carrete`; si ya existe, incrementa. La accion cambia a controles compactos. Presentaciones sin stock online se pueden agregar, marcadas como a confirmar.

---

## Que guarda cada item

| Option | Description | Selected |
|--------|-------------|----------|
| product.id + datos visibles | Usar clave interna para reconciliar y SKU/EAN/codigo como snapshot visible. | yes |
| SKU si existe + fallback | Usar SKU como principal si existe. | |
| Solo snapshot visible | No guardar clave estable. | |
| Otro | Freeform. | |

**User's choice:** Guardar los dos: `product.id` y datos/codigos visibles.
**Notes:** Se verifico `public/data/stock.json`: `id` esta presente y es unico en 370/370 productos; `sku` existe solo en 147/370 y algunos se repiten. El usuario pidio metodo para resetear o avisar si cambia la DB/catalogo y se rompe la coordinacion. Se decidio versionar schema, remover items puntuales no reconciliables y avisar cantidad removida.

---

## Cantidad y controles

| Option | Description | Selected |
|--------|-------------|----------|
| - / numero editable / + / +12 | Control completo inicial propuesto. | yes |
| Solo - / numero / + | Control simple. | |
| +1 y +12 sin input editable | Rapido pero menos flexible. | |
| Otro | Freeform. | yes |

**User's choice:** Controles extendidos `- / numero editable / + / +6 / +12`.
**Notes:** Cantidades enteras, minimo 1; si baja de 1 se elimina. Presentaciones raras o sin peso se permiten como unidades/carreteles con confirmacion. El usuario agrego un toggle para mantener la UI limpia: por defecto se muestra accion minima `+1`; el toggle muestra/oculta controles extendidos sin borrar ni apagar la lista.

---

## Framing y avisos

| Option | Description | Selected |
|--------|-------------|----------|
| Lista de compra | Cotidiano, pero puede sonar a compra real. | |
| Lista de cotizacion | Preciso y evita e-commerce. | yes |
| Lista maker | Mas de marca/comunidad. | |
| Otro | Freeform. | |

**User's choice:** Lista de cotizacion.
**Notes:** Aviso principal elegido: `Usa esta lista para planificar tu compra. Confirma stock y precio final con cada proveedor.` Aviso local-only dentro del panel/drawer, debajo del titulo. Icono/metafora: lista/checklist.

---

## Autosave y limpiar lista

| Option | Description | Selected |
|--------|-------------|----------|
| Automaticamente en cada cambio | Agregar, quitar, editar o limpiar guarda. | yes |
| Boton Guardar lista | Guardado explicito. | |
| Autosave con indicador guardado | Autosave mas estado visual. | |
| Otro | Freeform. | |

**User's choice:** Autosave automatico en cada cambio.
**Notes:** Limpiar lista requiere confirmacion simple. Si `localStorage` falla, la lista sigue en memoria y avisa que no se guardara al cerrar. Si se remueven items no reconciliables por cambios del catalogo, el aviso es no bloqueante dentro del panel.

---

## the agent's Discretion

- Definir el split exacto de componentes y helpers respetando patrones existentes.
- Elegir breakpoint exacto para panel desktop vs drawer mobile.
- Elegir implementacion concreta del icono checklist/list, evitando carrito.

## Deferred Ideas

- Import/export queda para Phase 2.
- Cobertura por proveedor queda para Phase 3.
- WhatsApp y mensajes por proveedor quedan para Phase 4.
