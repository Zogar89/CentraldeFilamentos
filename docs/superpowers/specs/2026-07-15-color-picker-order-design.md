# Orden visual del Color Picker

## Objetivo

Hacer que la vista `Continuo` se lea de izquierda a derecha como una paleta física ordenada, sin mezclar colores intensos, apagados, tierras y neutros en la misma corrida visual.

## Criterio aprobado

La paleta se divide dinámicamente en cuatro franjas, en este orden:

1. **Rueda cromática intensa:** rojo, naranja, amarillo, verde, turquesa, azul, violeta y rosa.
2. **Claros y apagados:** el mismo recorrido de tono.
3. **Tierras y marrones:** arena, ocre, cobre, marrón rojizo, marrón, topo y caqui.
4. **Neutros:** blanco, gris claro, gris medio, grafito y negro.

Cada franja muestra una grilla propia y un rótulo breve. Esto evita que el corte de fila responsivo mezcle accidentalmente el final de una familia con el inicio de otra.

## Clasificación dinámica

La clasificación usa OKLCH calculado con Culori desde el HEX actual de cada grupo lógico. No se guardan coordenadas ni posiciones manuales.

- **Neutros:** croma muy bajo, incluidos blanco, gris y negro.
- **Tierras:** tonos cálidos con luminosidad y croma moderados o bajos.
- **Intensos:** resto de colores con croma alto.
- **Claros y apagados:** resto de colores con croma inferior al de los intensos.

Los umbrales viven en funciones puras de `src/lib/colorPicker.js`. Si el RGB/HEX publicado cambia, el color vuelve a clasificarse y puede moverse de franja sin cambios manuales.

Dentro de las franjas cromáticas el desempate es: tono, luminosidad de claro a oscuro, croma y `id`. En tierras se prioriza tono cálido y luminosidad; en neutros, luminosidad de claro a oscuro. El `id` conserva estabilidad cuando los atributos perceptuales empatan.

## Cambios de interfaz

- `ColorPalette.svelte` reemplaza la única grilla de `Continuo` por cuatro secciones derivadas, sin cambiar el comportamiento de los cuadrados, tooltip, stock, selección o comparador.
- `Familias` incorpora `Tierras` como familia cuando corresponda; conserva las demás familias y su orden actual.
- `Mapa 2D`, comparador, búsqueda CIEDE2000 y filtro `Ocultar sin stock` no cambian. El filtro se aplica antes de agrupar las franjas.
- Los rótulos de franja son encabezados semánticos para que la estructura también sea navegable con lector de pantalla.

## Pruebas y aceptación

Las pruebas de `colorPicker` cubren que una muestra sintética ubica rojo/azul en la franja intensa, un pastel en claros y apagados, un marrón en tierras y blanco/gris/negro en neutros; también verifican el orden de franjas y el orden claro a oscuro de los neutros.

La revisión visual en Chrome confirma que la primera vista ya no intercala marrones y grises entre los cromáticos, y que al activar `Ocultar sin stock` se conservan los cuatro bloques con los colores restantes.
