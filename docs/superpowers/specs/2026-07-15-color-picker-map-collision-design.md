# Mapa 2D sin superposición del Color Picker

## Objetivo

Mostrar todos los colores PLA en el mapa perceptual sin ocultar colores que comparten una celda de tono y luminosidad.

## Diseño aprobado

El mapa deja de usar doce columnas y seis filas discretas. Cada color conserva una coordenada objetivo continua calculada desde su OKLCH actual:

- **X:** tono (`h`), de rojo a rojo en el recorrido circular.
- **Y:** luminosidad (`l`), de claro arriba a oscuro abajo.
- **Tamaño:** croma (`c`), con un diámetro acotado para que los colores intensos sean un poco más notorios que los apagados.

Cuando dos o más colores quedarían demasiado cerca, se aplica una separación determinista de puntos. Cada color se desplaza lo mínimo necesario alrededor de su coordenada objetivo. El orden estable por coordenada y `id` asegura que el mismo catálogo produce la misma disposición.

No hay posiciones manuales ni una lista estática: si cambia el HEX publicado, Culori vuelve a calcular OKLCH, el color se mueve de ancla y el algoritmo reorganiza el racimo cercano.

## Interfaz

- El mapa se renderiza como un plano relativo con botones circulares/compactos posicionados en porcentaje.
- Los colores de un mismo vecindario aparecen como un pequeño racimo visible, no como fichas superpuestas.
- Cada punto conserva el tooltip nativo, el estado de sin stock, la selección y la acción hacia el comparador.
- La leyenda mantiene `Luminosidad` en el eje vertical y `Tono` en el horizontal. Se agrega una nota breve que explica que el tamaño representa intensidad/croma.
- En pantallas angostas el plano mantiene un ancho mínimo desplazable para preservar el espaciado y la selección táctil.

## Límites y accesibilidad

- La separación se limita a los márgenes del plano; no puede sacar un punto fuera del mapa.
- Se reserva un diámetro mínimo táctil/visual y los puntos siguen siendo botones enfocables.
- El orden del DOM permanece estable por la posición visual calculada y `id`, por lo que teclado y lectores de pantalla recorren todos los colores.

## Pruebas y aceptación

Las pruebas unitarias comprueban que cada color recibe una posición y tamaño derivados, que las posiciones permanecen dentro de los límites y que muestras que comparten tono/luminosidad no terminan con el mismo centro. La revisión local en Chrome confirma que los 162 colores del catálogo se ven como puntos individuales y que seleccionar uno todavía lo agrega al comparador.
