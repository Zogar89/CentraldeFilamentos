# Orden del catálogo por color, marca y presentación

## Objetivo

Cambiar el orden inicial de los resultados del catálogo para que las opciones se presenten por color, luego por marca y finalmente por presentación. El orden por disponibilidad total se conserva como alternativa seleccionable.

## Alcance

El cambio afecta únicamente la lista de resultados del catálogo renderizada por `src/SummaryApp.svelte`. No modifica la lista de cotización, el Color Picker, la cinta de colores ni el orden de los filtros.

## Comportamiento

El orden predeterminado compara cada producto con la siguiente prioridad:

1. `color`, en orden alfabético español.
2. `brand`, en orden alfabético español.
3. Presentación, con menor peso primero.
4. Diámetro, en orden numérico ascendente.
5. Nombre visible o identificador, como desempate estable.

Los samplers se ubican después de las presentaciones con peso conocido. Los productos sin peso ni formato reconocido quedan al final. Los campos ausentes se tratan como cadenas vacías o valores no definidos sin interrumpir el render.

El selector `Ordenar por` inicia en `Color · Marca · Presentación` y conserva `Disponibilidad total` como segunda opción. Cambiar la selección reordena los productos filtrados sin alterar los filtros activos.

## Arquitectura

La regla se implementa como un comparador puro y exportado desde `src/lib/catalogExplorer.js`. `src/SummaryApp.svelte` selecciona entre ese comparador y `compareExplorerProducts`, que conserva la lógica existente de disponibilidad.

El comparador reutiliza las reglas compartidas de presentación de `src/lib/shared.js` y agrega sólo los desempates necesarios para diámetro e identidad. `buildSummaryRows()` continúa respetando el orden de entrada y no incorpora reglas de ordenamiento.

## Pruebas

La prueba de comportamiento se agrega primero en `tests/catalogExplorer.test.js` y debe fallar antes de modificar producción. Debe demostrar que:

- el color tiene prioridad sobre marca y presentación;
- la marca tiene prioridad sobre presentación;
- dentro del mismo color y marca, el menor peso aparece primero;
- el diámetro y la identidad resuelven empates de forma estable;
- el comparador de disponibilidad existente mantiene su comportamiento.

La verificación final incluye la prueba Node del explorador, el build de Vite y la suite Python con un directorio temporal escribible en Windows.

## Criterios de aceptación

- Al abrir el catálogo, el selector muestra `Color · Marca · Presentación`.
- Los resultados visibles siguen exactamente esa jerarquía.
- `Disponibilidad total` sigue disponible y reproduce el orden anterior.
- La lista de cotización y el Color Picker no cambian de orden.
- Las pruebas y el build terminan correctamente.
