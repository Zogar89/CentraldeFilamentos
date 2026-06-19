---
phase: 01-quote-list-foundation
reviewed: 2026-06-19T15:24:43Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - src/CatalogApp.svelte
  - src/components/QuoteListDrawer.svelte
  - src/components/QuoteListItem.svelte
  - src/components/QuoteListPanel.svelte
  - src/components/QuoteQuantityControl.svelte
  - src/lib/quoteList.js
  - src/styles/global.css
  - tests/test_frontend_assets.py
findings:
  critical: 2
  warning: 2
  info: 0
  total: 4
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-06-19T15:24:43Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

La base de la lista de cotización compila y los tests actuales pasan, pero hay dos caminos que pueden borrar permanentemente la lista guardada. Además, el drawer no implementa el comportamiento modal necesario para teclado y las pruebas agregadas verifican texto fuente en lugar de los comportamientos críticos de persistencia.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01 [BLOCKER]: Un fallo transitorio del catálogo vacía la lista persistida

**File:** `src/CatalogApp.svelte:71-89`
**Issue:** `fetchJson` usa un catálogo vacío como fallback. El montaje no distingue ese fallo de una carga válida, reconcilia todos los ítems contra `products = []` y luego, como `removedCount` es mayor que cero, llama a `saveQuoteListState`. Esto sobrescribe `localStorage` con una lista vacía ante una caída de red, un JSON inválido o una publicación temporalmente inconsistente. Es pérdida de datos locales del usuario.
**Fix:** No reconciliar ni guardar hasta confirmar que el catálogo se cargó correctamente. Hacer que la carga exponga éxito/error (o validar una marca contractual del payload) y conservar los snapshots guardados cuando falla. Por ejemplo:

```js
const result = await fetchStockPayload();
if (!result.ok) {
  quoteItems = quoteList.items;
  quoteStorageWarning = "No pudimos actualizar el catalogo; conservamos tu lista guardada.";
  return;
}

products = result.payload.products;
const reconciled = reconcileQuoteList(quoteList.items, products);
```

### CR-02 [BLOCKER]: Una versión de esquema desconocida se sobrescribe con una lista vacía

**File:** `src/lib/quoteList.js:25-34`, `src/CatalogApp.svelte:78-89`
**Issue:** `normalizeQuoteList` convierte cualquier `schemaVersion` distinta de `1` en una lista vacía. Luego el montaje detecta `resetReason` y guarda inmediatamente ese estado vacío. Una pestaña con código antiguo puede así destruir datos escritos por una versión futura; incluso una migración pendiente se transforma en borrado irreversible. El aviso de incompatibilidad tampoco llega a mostrarse porque `saveQuoteListState` limpia la advertencia cuando la escritura vacía tiene éxito.
**Fix:** Tratar un esquema desconocido como no escribible: conservar el valor original, mostrar el aviso y no llamar a `saveQuoteList` hasta contar con una migración explícita o una confirmación del usuario. Las versiones conocidas deben migrarse mediante funciones versionadas, nunca mediante reinicio y guardado automático.

## Warnings

### WR-01 [WARNING]: El drawer con `role="dialog"` no funciona como modal para teclado

**File:** `src/components/QuoteListDrawer.svelte:21-26`
**Issue:** Al abrirse, el drawer no mueve el foco, no declara `aria-modal="true"`, no contiene el foco y no lo devuelve al botón disparador al cerrar. Un usuario de teclado o lector de pantalla puede seguir navegando por controles ocultos detrás del backdrop y perder su posición al cerrar.
**Fix:** Enfocar el botón de cierre o el encabezado al montar, agregar `aria-modal="true"`, contener `Tab`/`Shift+Tab` dentro del diálogo, marcar el contenido de fondo como inerte mientras esté abierto y restaurar el foco al disparador al cerrar.

### WR-02 [WARNING]: Los tests de la fase no ejercitan persistencia ni reconciliación

**File:** `tests/test_frontend_assets.py:177-318`
**Issue:** Las pruebas nuevas se limitan a buscar identificadores y fragmentos de copy/CSS en archivos fuente. Pasan aunque la carga del catálogo borre `localStorage`, aunque un esquema futuro sea destruido o aunque los controles de cantidad no actualicen el estado. Esto da una señal verde sin verificar los contratos funcionales más riesgosos de la fase.
**Fix:** Extraer la inicialización/reconciliación a funciones testeables y agregar tests de comportamiento con un almacenamiento simulado: catálogo fallido conserva ítems, esquema desconocido no escribe, escritura fallida mantiene estado de sesión, duplicados se normalizan y cambios de cantidad persisten. Mantener sólo unas pocas aserciones fuente para enlaces estáticos que realmente no puedan probarse de otra forma.

---

_Reviewed: 2026-06-19T15:24:43Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
