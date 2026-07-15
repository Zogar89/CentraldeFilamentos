# Color Picker para PLA — Especificación de diseño

## Objetivo

Agregar una página pública `color-picker.html` que permita encontrar filamentos PLA por apariencia cromática, comparar hasta cuatro colores y sumar una presentación concreta a la lista de cotización existente.

La pantalla consume `public/data/stock.json` directamente en el navegador. No agrega endpoints, sesiones ni persistencia remota y mantiene el modelo estático de GitHub Pages.

## Alcance inicial

- Mostrar únicamente productos cuyo `material` sea `PLA`; las variantes y líneas de PLA se conservan como líneas distintas.
- Mostrar todos los colores al entrar, incluidos los que no tienen stock.
- Ofrecer el control `Ocultar sin stock`, desactivado por defecto.
- Mantener tres vistas de la misma colección: `Continuo`, `Familias` y `Mapa 2D`.
- Usar `Continuo` como vista inicial.
- Permitir una comparación de hasta cuatro colores.
- Mostrar en cada comparación HEX, RGB, Pantone o procedencia estimada, disponibilidad, render de material y presentaciones concretas.
- Permitir buscar seis colores similares desde un filamento o desde cualquier HEX válido.
- Sumar una unidad de una presentación concreta a la lista de cotización existente mediante un botón `+1`.

Quedan fuera de esta primera versión otros materiales, la comparación de precios, la conversión automática desde Pantone hacia filamentos y la edición manual de datos desde el frontend.

## Identidad de un color

Un color lógico queda identificado por:

```text
marca normalizada + línea normalizada + nombre de color normalizado
```

El agrupamiento no incluye peso, formato ni diámetro. Por ejemplo, `Grilon3 + PLA Standard + Amarillo` y `3N3 + PLA Standard + Amarillo` son colores distintos; las presentaciones de 1 kg y 2,5 kg del primer caso aparecen bajo una sola entrada.

La normalización reutiliza `foldText()` y `lineLabel()` para evitar diferencias sólo por mayúsculas, acentos o la representación vacía de `PLA Standard`. El identificador de frontend se deriva de esos tres campos y no reemplaza los `product.id` concretos del catálogo.

## Derivación del color representativo

Cada grupo elige un producto representativo de forma determinista. Ese producto aporta HEX, Pantone, acabado y render al cuadrado y a la tarjeta comparativa.

El orden de preferencia es:

1. `pantone_hex` válido.
2. `estimated_color_hex` válido con confianza `high`, luego `medium`, luego `low` y finalmente sin confianza declarada.
3. Dentro de la misma confianza, fuente `image_and_name` antes de `name_only`.
4. Producto con al menos una oferta `in_stock` antes de uno sin stock.
5. `product.id` en orden ascendente como desempate estable.

Un HEX válido cumple `#[0-9A-F]{6}` sin depender de mayúsculas. Los productos sin `pantone_hex` ni `estimated_color_hex` válidos no entran en la paleta, porque no pueden ubicarse ni compararse cromáticamente. La página informa cuántos productos PLA quedaron fuera por ese motivo.

Si mañana cambia el RGB/HEX publicado en `stock.json`, el grupo vuelve a calcular su posición, familia y vecinos al cargar la página. No existen coordenadas cromáticas persistidas ni orden manual.

## Disponibilidad y presentaciones

Un color lógico tiene stock cuando cualquiera de sus productos concretos contiene al menos una oferta con `stock_status === "in_stock"`. El control `Ocultar sin stock` filtra grupos completos con esa regla y afecta la paleta y los resultados de similitud.

Las presentaciones se derivan de los productos concretos incluidos en el grupo y se ordenan con `comparePresentations()`. Cada fila conserva su `product.id`, por lo que el botón `+1` agrega exactamente ese producto a la lista de cotización.

La etiqueta usa `formatPresentation()`. Si un grupo contiene más de un diámetro, agrega el diámetro a cada opción para evitar ambigüedad, por ejemplo `1 kg · 1,75 mm` y `1 kg · 2,85 mm`. Presentaciones idénticas según peso, formato y diámetro se muestran una sola vez; se conserva primero la que tenga stock y luego el `product.id` menor como desempate estable.

## Organización visual

### Vista Continuo

Es la vista predeterminada. Culori convierte cada HEX a OKLCH en tiempo de ejecución. Los colores cromáticos se ordenan por tono, luego luminosidad y croma; los neutros se ubican juntos y se ordenan de claro a oscuro.

La interfaz usa cuadrados compactos y responsivos. El `title`, el nombre accesible y el tooltip muestran marca, línea, color, HEX y estado de stock. Los colores sin stock permanecen visibles con un tratamiento no cromático adicional, de modo que el estado no dependa sólo del color.

### Vista Familias

Agrupa por rangos derivados de tono y croma OKLCH: rojos, naranjas, amarillos, verdes, turquesas, azules, violetas, rosas y neutros. Dentro de cada familia se aplica el mismo orden perceptual.

Las familias se recalculan al cargar los datos; cambiar un HEX puede mover un filamento de sección sin modificar código.

### Vista Mapa 2D

Ubica tono en el eje horizontal y luminosidad en el eje vertical usando 12 bandas de tono y 6 de luminosidad. Cuando varias entradas caen en la misma celda, se muestran en un flujo interno ordenado por croma y luego por identificador; nunca se superponen controles interactivos.

La vista mantiene rótulos de ejes y se adapta a móvil mediante desplazamiento horizontal controlado si no hay ancho suficiente.

## Selección y comparador

Un clic sobre un cuadrado realiza dos acciones coherentes con el mock aprobado:

1. Define ese HEX como referencia para `Buscar colores similares`.
2. Agrega o quita el color del comparador.

El comparador empieza vacío y conserva como máximo cuatro identificadores lógicos durante la vida de la página. No se persiste en `localStorage`; la lista de cotización sí mantiene su persistencia existente.

Cada tarjeta comparativa muestra:

- nombre, marca y línea;
- render desde `material_swatch_url` del producto representativo;
- fallback plano con el HEX cuando el render no existe o no carga;
- HEX en mayúsculas;
- RGB decimal derivado con Culori;
- Pantone cuando existe;
- en colores estimados, la etiqueta `Color estimado` y su advertencia publicada;
- estado agregado de stock;
- todas las presentaciones concretas, cada una con su botón `+1`.

Al intentar agregar un quinto color, la selección no cambia y aparece un mensaje que pide quitar uno. Quitar una tarjeta vuelve a sincronizar el estado `aria-pressed` de las tres vistas.

## Buscar colores similares

La búsqueda acepta dos orígenes:

- el último cuadrado seleccionado;
- un `<input type="color">` sincronizado con un campo de texto HEX.

El botón `Buscar similares` valida y normaliza el HEX. Culori calcula la distancia CIEDE2000 entre la referencia y cada grupo visible. Los resultados se ordenan de menor a mayor distancia y luego por nombre estable, excluyen el mismo grupo cuando la referencia proviene de la paleta y muestran los seis primeros.

Cada resultado incluye muestra, nombre, marca, línea, HEX, valor `ΔE`, una etiqueta orientativa y la acción `Comparar`. Las bandas son `Muy cercano` para `ΔE < 3`, `Cercano` para `3 ≤ ΔE < 8` y `Alternativa` para `ΔE ≥ 8`. No se comunica la distancia como garantía física: se muestra una advertencia permanente sobre acabado, iluminación, lote y calibración de pantalla.

Cuando cambia `Ocultar sin stock`, una búsqueda activa se recalcula con la colección filtrada. Si quedan menos de seis candidatos se muestran todos y se informa la cantidad.

## Integración con la lista de cotización

La página reutiliza `loadQuoteList()`, `saveQuoteList()`, `snapshotQuoteItem()` y las reglas de cantidad existentes en `src/lib/quoteList.js`.

Cada `+1`:

1. busca el `product.id` concreto en la lista cargada;
2. incrementa su cantidad o crea un snapshot con cantidad 1;
3. persiste mediante el mismo esquema `centraldefilamentos.quoteList.v1`;
4. muestra feedback accesible con el producto, presentación y cantidad resultante.

Si el almacenamiento está bloqueado, la lista sigue funcionando durante la sesión y aparece la misma advertencia conceptual que en el catálogo. Si el navegador encuentra una versión de esquema más nueva, la página no sobrescribe la lista y deshabilita `+1`.

Esta primera versión no incorpora el drawer completo dentro del Color Picker. La navegación permite volver al catálogo para revisar y enviar la lista.

## Arquitectura frontend

La página sigue el patrón multipágina existente:

- `color-picker.html`: entrada HTML pública.
- `src/color-picker.js`: montaje Svelte, sin lógica de dominio.
- `src/ColorPickerApp.svelte`: carga de datos, estado de vista, filtro, selección, búsqueda y coordinación de la lista.
- `src/components/ColorPalette.svelte`: vistas Continuo, Familias y Mapa 2D.
- `src/components/SimilarColorSearch.svelte`: formulario y seis resultados.
- `src/components/ColorComparator.svelte`: tarjetas comparativas y presentaciones.
- `src/lib/colorPicker.js`: funciones puras de agrupamiento, color representativo, orden, familias, mapa y similitud.

`vite.config.js` agrega `colorPicker` como cuarta entrada. `SiteHeader.svelte` agrega `Color Picker` a la navegación y acepta `active="color-picker"`.

Culori se instala como dependencia de runtime con versión `^4.0.2`; no se carga desde CDN. El sitio sigue siendo autocontenido en el build de Vite y funcional en GitHub Pages bajo `/CentraldeFilamentos/`.

## Flujo de datos

```text
stock.json
  -> filtrar material PLA
  -> descartar grupos sin HEX válido
  -> agrupar por marca + línea + color
  -> elegir representante y agregar presentaciones/stock
  -> convertir HEX con Culori
  -> renderizar una de las tres vistas
       -> seleccionar referencia/comparador
       -> buscar seis similares por CIEDE2000
       -> sumar product.id concreto a quoteList.v1
```

Todas las transformaciones de catálogo son funciones puras. Svelte conserva sólo estado de interacción y delega en esas funciones para que el comportamiento pueda probarse con Node sin montar el DOM.

## Estados vacíos y errores

- Error al cargar `stock.json`: mensaje claro y acción para reintentar; no se presenta una paleta vacía como si fuese válida.
- Ningún PLA con HEX válido: estado vacío que explica que faltan datos cromáticos.
- HEX manual inválido: `aria-invalid="true"`, ejemplo `#009DCE` y resultados anteriores intactos.
- Sin resultados por filtro de stock: mensaje específico y sugerencia de desactivar `Ocultar sin stock`.
- `material_swatch_url` ausente o fallido: fallback plano con el HEX y texto alternativo.
- Pantone ausente: `Color estimado`; nunca inventar un código Pantone.
- Máximo de comparación alcanzado: mensaje accesible y selección sin cambios.
- Error de `localStorage`: lista operativa en memoria y advertencia visible.

## Accesibilidad y responsive

- Todos los cuadrados son botones con nombre accesible completo y estado `aria-pressed`.
- El tooltip de mouse no es la única fuente de información; foco de teclado muestra el mismo contenido.
- Las vistas se eligen con botones reales y estado anunciado.
- Mensajes de búsqueda, límite y `+1` usan regiones `aria-live` sin interrumpir la navegación.
- El comparador usa cuatro columnas en escritorio, dos en tablet y una en móvil.
- La lista de similares puede envolver filas; nunca reduce texto o controles hasta volverlos ilegibles.
- El diseño reutiliza variables, tipografía y componentes visuales existentes en `src/styles/global.css`.

## Pruebas y criterios de aceptación

Las funciones puras se cubren con `node:test` en `tests/colorPicker.test.js`:

- sólo entran productos PLA con HEX válido;
- el agrupamiento ignora peso y diámetro pero separa marca, línea y nombre;
- la prioridad de representante es estable;
- el stock agregado responde a cualquier oferta `in_stock`;
- las presentaciones conservan el producto concreto y no se duplican;
- cambiar el HEX cambia el orden OKLCH, la familia o el mapa según corresponda;
- CIEDE2000 devuelve exactamente seis vecinos ordenados y respeta el filtro;
- la referencia de catálogo se excluye de sus propios resultados;
- el quinto color no entra en el comparador.

Los contratos de assets en `tests/test_frontend_assets.py` comprueban la nueva entrada HTML, el montaje, la navegación, la entrada Vite, el uso de `material_swatch_url` y la integración con `snapshotQuoteItem()`.

La verificación final exige:

```powershell
npm.cmd run test:color-picker
npm.cmd run test:quote-list
npm.cmd run build
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos-color-picker
```

La revisión visual se realiza en Chrome en escritorio y móvil, comprobando las tres vistas, el filtro, HEX libre, seis similares, límite de cuatro y `+1` persistido.

## Decisiones aprobadas

- Alcance inicial: PLA.
- Color lógico: marca + línea + nombre.
- Mostrar todos por defecto; el control oculta los que no tienen stock.
- Conservar las tres vistas, con Continuo como predeterminada.
- Reordenamiento dinámico por HEX/RGB mediante Culori.
- Comparador de cuatro colores.
- Render de material de alta resolución en vez de fotografía genérica.
- Presentaciones concretas con `+1` dentro de cada tarjeta.
- Búsqueda de seis similares por CIEDE2000 desde selección o HEX libre.
