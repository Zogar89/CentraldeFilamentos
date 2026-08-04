# Canon de diseño — Central de Filamentos

**Estado:** canónico

**Vigente desde:** 2026-08-04

**Alcance:** todas las interfaces públicas e internas del repositorio

## 1. Propósito y autoridad

Este documento define la base visual, de interacción y de contenido de Central de Filamentos. Es la referencia por defecto para diseñar, implementar y revisar cualquier interfaz nueva o existente del proyecto.

La autoridad se interpreta así:

1. `design.md` define las decisiones duraderas del producto.
2. Una especificación de feature aprobada puede introducir una excepción explícita y acotada.
3. Si esa excepción pasa a ser permanente, la misma entrega debe actualizar este documento.
4. El código, los tests y la evidencia visual demuestran la implementación; una divergencia accidental no se convierte en canon por existir.
5. Las specs históricas explican decisiones pasadas, pero no reemplazan este documento.

El canon abarca:

- catálogo y resumen de stock;
- Color Picker y comparadores de color;
- lista de cotización y contacto con proveedores;
- estadísticas internas y salud de las capturas;
- herramienta local de curación de imágenes;
- cualquier nueva superficie visual del repositorio.

El pipeline de datos queda alcanzado cuando sus estados, campos o fallos se representan en una interfaz. Los archivos generados, incluido `public/data/stock.json`, no son una fuente editable de decisiones de diseño.

## 2. Identidad del producto

Central de Filamentos es una herramienta argentina para makers que transforma stock disperso en una consulta de compra clara y accionable. Centraliza y normaliza información, pero no vende, no cobra, no procesa pedidos y no garantiza disponibilidad final.

### Promesa principal

Ayudar a encontrar filamentos, comparar qué proveedor cubre una necesidad y preparar una consulta de cotización sin presentar la plataforma como una tienda.

### Personalidad

La interfaz debe sentirse:

- precisa, porque representa datos de terceros;
- directa, porque la tarea suele empezar con una necesidad concreta;
- sobria, para que los colores de producto sean protagonistas;
- confiable, mediante procedencia, fechas y estados explícitos;
- cercana al mundo maker, sin caricaturas ni estética infantil;
- eficiente, sin convertir densidad de información en ruido.

No debe sentirse como un marketplace, un checkout, una landing promocional ni un dashboard corporativo genérico.

## 3. Principios de experiencia

### 3.1 Material primero

La navegación principal sigue esta jerarquía:

`material → color → producto y presentación exacta → proveedor → lista de cotización`

El material es una restricción fuerte. Elegir un color nunca amplía silenciosamente los resultados a otro material. Los filtros secundarios refinan el conjunto actual; no debilitan la selección principal.

### 3.2 Evidencia antes que inferencia

Toda afirmación visible debe distinguir entre:

- dato publicado por el proveedor;
- dato normalizado por Central de Filamentos;
- estimación o aproximación;
- estado pendiente de revisión;
- interpretación interna.

No se inventan RGB, Pantone, equivalencias físicas, precios ni disponibilidad. Una aproximación útil debe identificarse como tal y conservar su procedencia.

### 3.3 Acción sin checkout

La acción principal no es “comprar”, sino agregar a una lista, comparar cobertura y consultar. Cada mensaje o enlace de contacto debe recordar que precio y disponibilidad se confirman con el proveedor.

### 3.4 Complejidad progresiva

La primera vista muestra las decisiones de mayor impacto. Variantes, diámetro, peso, marca, proveedor y otros filtros aparecen después o mediante expansión. Las herramientas internas pueden ser más densas, pero deben mantener jerarquía y escaneo rápido.

### 3.5 Control local y reversible

La lista de cotización vive en el navegador. Sus acciones deben ser explícitas, reversibles cuando sea posible y resistentes a esquemas más nuevos. Ninguna interacción debe sugerir sincronización entre dispositivos o persistencia remota.

### 3.6 Un estado nunca queda implícito

Carga, vacío, error, deshabilitado, solo lectura, dato desactualizado, confirmación y éxito parcial necesitan representación visible. Una pantalla silenciosamente vacía no es un estado válido.

## 4. Arquitectura de información

### Producto público

1. Identidad y búsqueda global.
2. Selección de material.
3. Selección de familia o color exacto, según el tamaño de la paleta.
4. Filtros secundarios.
5. Resultados y disponibilidad por proveedor.
6. Lista de cotización.
7. Comparación de cobertura y preparación de mensajes por proveedor.
8. Contexto de actualización, procedencia y límites de la información.

### Herramientas internas

1. Propósito y alcance de la herramienta.
2. Estado global o guardrail operativo.
3. Controles de búsqueda y filtrado.
4. Resumen cuantitativo.
5. Elementos que requieren revisión o diagnóstico.
6. Acción explícita y feedback inmediato.
7. Evidencia y procedencia suficientes para auditar la decisión.

Las herramientas internas comparten el lenguaje y los principios del producto, aunque tengan navegación, densidad y tokens locales mientras no forman parte del bundle público.

## 5. Sistema visual

### 5.1 Paleta semántica

La base pública vigente es clara, neutral y de contraste alto:

| Token | Valor base | Uso |
|---|---:|---|
| `--bg` | `#f7f8f8` | Fondo general |
| `--surface` | `#ffffff` | Paneles, controles y tarjetas |
| `--surface-soft` | `#f1f4f3` | Agrupaciones y estados suaves |
| `--line` | `#d9dfde` | Bordes y separadores |
| `--text` | `#1c2426` | Texto principal |
| `--muted` | `#647073` | Texto secundario |
| `--accent` | `#006f77` | Acción, selección y foco |
| `--ok` | `#0f733f` | Disponible, correcto o confirmado |
| `--out` | `#5c6068` | Sin stock, inactivo o neutral |
| `--warn` | `#a15c00` | Dato incierto, provisional o atención |
| `--danger` | `#a32626` | Fallo o acción destructiva interna |

Reglas de uso:

- El teal identifica acciones y selección; no se usa como relleno decorativo dominante.
- Verde, ámbar y rojo son semánticos. Siempre se acompañan con texto, icono o forma.
- El color del filamento es contenido de producto, no color de interfaz.
- Los colores de marca de proveedores no reemplazan la jerarquía semántica del producto.
- Las herramientas con aliases locales, como `--soft`, deben mapearse a estos roles. Si un token pasa a ser compartido, se centraliza en `src/styles/global.css`.
- Un valor nuevo y repetido debe convertirse en token; no se multiplican hexadecimales equivalentes entre componentes.

### 5.2 Tipografía

La familia base es la pila del sistema:

`-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`

La tipografía debe priorizar rendimiento y legibilidad. La escala recomendada parte de los tamaños ya usados:

- 11–13 px: metadatos, etiquetas y ayudas;
- 15 px: cuerpo y controles;
- 18–19 px: títulos de sección y panel;
- 25–31 px: título principal de producto;
- hasta 36 px: herramientas internas con espacio suficiente.

Los pesos altos señalan jerarquía o acción, no compensan falta de estructura. Las mayúsculas se reservan para eyebrows o estados breves; el cuerpo no se escribe en mayúsculas.

### 5.3 Espaciado, bordes y forma

- La unidad de espaciado es 4 px; se prefieren pasos de 4, 8, 12, 16, 20, 24, 28, 32 y 48 px.
- Controles compactos usan radios cercanos a 8 px; tarjetas, 10 px; paneles, hasta 14 px.
- Las píldoras se reservan para estados, contadores o selecciones breves.
- Los bordes son de 1 px y suaves. La separación estructural no depende solo de sombras.
- Las sombras son discretas y comunican elevación real: header sticky, drawer, diálogo o preview.
- No se agregan gradientes, glassmorphism, brillos o volumen si no mejoran una jerarquía funcional.

### 5.4 Imágenes y muestras de color

- Se usan imágenes reales aprobadas y thumbnails locales cuando existen.
- `object-fit: contain` es la opción normal para bobinas y envases; no se recorta información de producto por estética.
- Un fallback debe ser neutral y honesto. No se reemplaza una foto faltante por una ilustración que parezca evidencia.
- Una muestra estimada debe diferenciarse de una referencia oficial.
- Un color provisional se muestra con la etiqueta `Color del proveedor · pendiente de normalizar`.
- Ninguna imagen se publica automáticamente desde la herramienta de curación sin una decisión humana explícita.

### 5.5 Movimiento

Los tiempos compartidos actuales son:

- rápido: `140ms`;
- base: `190ms`;
- panel: `260ms`;
- curva: `cubic-bezier(.2, .78, .22, 1)`.

El movimiento confirma causalidad, cambio de estado o entrada de un panel. No se usa para decorar listados extensos. Con `prefers-reduced-motion: reduce`, las transiciones dejan de ser necesarias para comprender el estado.

## 6. Layout y responsive

El diseño es mobile-first, aunque desktop aprovecha el ancho para comparar más información.

### Anchos de referencia

- Shell público general: hasta 1180 px.
- Explorador principal: hasta 1520 px.
- Herramientas internas o de curación: hasta 1440 px.
- El contenido mantiene margen lateral útil; nunca toca el borde salvo barras globales deliberadas.

### Catálogo y cotización

- Desde 1100 px, catálogo y cotización forman dos columnas. El rail ocupa aproximadamente 340–365 px y puede permanecer sticky.
- Por debajo de 1100 px, el rail desaparece del flujo y la lista se abre como drawer accesible.
- En torno a 820 px, el header se reorganiza, materiales y colores pueden usar scroll horizontal deliberado y los filtros pasan a menos columnas.
- En torno a 520 px, metadatos, resultados y acciones se compactan sin ocultar identidad, disponibilidad ni acción principal.

Los breakpoints expresan necesidades del contenido, no modelos de dispositivo. Si una nueva traducción, control o dato rompe antes, el componente debe responder antes.

### Reglas generales

- No hay scroll horizontal de página. Solo se permite en cintas, tablas o galerías con contención y señal visual.
- En puntero táctil, el objetivo mínimo es 44 × 44 px. En desktop pueden existir controles de 40–42 px si conservan separación y foco claro.
- Una grilla debe degradar a menos columnas antes de comprimir texto o controles por debajo de su tamaño útil.
- El orden visual y el orden del DOM deben coincidir.

## 7. Patrones de componentes

### Header y navegación

- La marca, búsqueda y acción principal tienen prioridad.
- El estado activo de navegación es visible y usa `aria-current`.
- El acceso a la lista muestra su cantidad sin convertirla en carrito de compra.
- Toda página pública incluye un enlace para saltar al contenido.

### Selectores de material y color

- Material es el primer selector y muestra un estado seleccionado inequívoco.
- PLA puede agrupar por familias cromáticas; paletas cortas conservan colores exactos.
- La selección informa qué cubre y cuántos resultados afecta.
- Las muestras tienen nombre accesible; el color nunca es el único identificador.

### Filtros

- Los filtros más frecuentes permanecen visibles.
- Los secundarios usan disclosure o expansión y muestran si hay filtros activos.
- “Limpiar” afecta solo el nivel anunciado. No borra contexto o lista sin advertencia.
- Los filtros deben producir resultados deterministas y conservar la restricción de material.

### Resultado de producto

Cada fila o tarjeta conserva, en este orden perceptual:

1. imagen o fallback;
2. color y nombre de producto;
3. material, variante, diámetro, peso y marca relevantes;
4. disponibilidad separada por proveedor;
5. estado provisional o de incertidumbre, si aplica;
6. acción para agregar a cotización.

Los datos no caben a fuerza de truncamiento. La identidad principal puede truncarse solo cuando sigue disponible mediante contexto accesible o expansión.

### Estados y badges

- Un badge usa una sola idea y texto breve.
- `ok` significa hecho o disponible; no significa “probablemente”.
- `warn` identifica incertidumbre o revisión pendiente, no un fallo fatal.
- `danger` se reserva para fallos y consecuencias destructivas.
- Los contadores muestran cantidad; no se presentan como estado semántico.

### Diálogos, drawers y previews

- Al abrir, el foco entra en la superficie; al cerrar, vuelve al disparador.
- `Escape` cierra cuando no provoca pérdida irreversible.
- El fondo queda inerte y el nombre accesible describe la tarea.
- Un preview visual no reemplaza el texto alternativo ni los datos del producto.

## 8. Reglas por superficie

### Catálogo y resumen

- El catálogo es la entrada primaria y trabaja de material a producto exacto.
- La búsqueda global complementa, no sustituye, la navegación por material.
- El resumen puede ser más denso, pero debe conservar imágenes, identidad y comparación por proveedor.
- Precio y disponibilidad se presentan como información a confirmar.

### Lista de cotización

- Se denomina “lista de cotización”, nunca carrito o pedido.
- Persiste localmente y debe declarar cualquier estado de solo lectura, reconciliación o incompatibilidad.
- Cantidades, cobertura y proveedor se pueden revisar antes de preparar mensajes.
- Los mensajes se generan individualmente por proveedor y piden cotización y disponibilidad.
- Enviar o abrir WhatsApp es una acción iniciada por el usuario; la aplicación no publica ni contacta por sí sola.

### Color Picker

- Es una ayuda de comparación, no un colorímetro ni prueba del aspecto físico final.
- Diferencia color oficial, valor estimado, muestra de proveedor y dato provisional.
- La representación debe seguir siendo útil sin distinguir color perfectamente.
- Cualquier similitud calculada declara el espacio o criterio usado cuando esa información sea relevante para decidir.

### Estadísticas internas

- La fecha, ventana temporal, estado del build y fuente forman parte del significado del dato.
- Los gráficos incluyen etiqueta accesible, mínimo, máximo y valor actual cuando corresponda.
- Aumentos y descensos no se comunican solo con verde y rojo.
- Un feature flag apagado o una fuente ausente se explica; no se simula información.

### Curación de imágenes

- La interfaz separa imágenes aprobadas, candidatas, desactualizadas y sin revisar.
- Cada decisión conserva producto, fuente y evidencia visual suficiente.
- Aprobar es una acción explícita con feedback. Las acciones repetidas o bloqueadas muestran su estado.
- La herramienta puede usar mayor densidad y un acento local, pero mantiene tipografía, jerarquía semántica, targets y contraste del canon.

## 9. Voz y contenido

La interfaz habla en español claro para Argentina, con tono directo y útil. Puede usar voseo cuando mejora naturalidad: “Encontrá”, “Armá”, “Consultá”.

### Preferir

- “Agregar a la lista”
- “Consultar cotización”
- “Disponible según el proveedor”
- “Actualizado…”
- “Pendiente de normalizar”
- “Confirmá precio y disponibilidad con el proveedor”

### Evitar

- “Comprar ahora”
- “Checkout”
- “Pedido confirmado”
- “Stock garantizado”
- “Color exacto” cuando el dato es estimado
- mensajes técnicos sin una explicación accionable

Las unidades, fechas y cantidades mantienen un formato consistente dentro de cada vista. Los nombres propios y códigos del proveedor no se corrigen de forma que pierdan trazabilidad.

## 10. Accesibilidad

El objetivo mínimo es WCAG 2.2 AA para las superficies públicas e internas.

- Un solo `h1` describe cada página; los encabezados mantienen orden lógico.
- Se usan landmarks, botones y enlaces semánticos antes que elementos genéricos con handlers.
- Todo control tiene nombre accesible y estado programático.
- El foco visible usa un contorno claro, actualmente 3 px de `--accent` con separación.
- Todo flujo principal funciona con teclado.
- Color, posición y animación nunca son el único canal de información.
- Los mensajes dinámicos importantes se anuncian sin mover el foco arbitrariamente.
- Imágenes informativas tienen texto alternativo; imágenes redundantes usan `alt=""`.
- Drawers y diálogos gestionan foco, cierre y fondo inerte.
- Se respeta reducción de movimiento y zoom del navegador.
- Tablas y gráficos conservan una lectura textual equivalente.

## 11. Integridad, privacidad y fallos

- La arquitectura pública sigue siendo estática y compatible con GitHub Pages.
- No se diseñan flujos que requieran endpoints, sesiones o cuentas sin una decisión de arquitectura aprobada.
- La persistencia de usuario se limita al navegador y no se presenta como sincronizada.
- La lista local no sale del dispositivo salvo por una acción explícita del usuario, como abrir un mensaje preparado.
- Toda vista de stock muestra o permite encontrar su fecha de actualización.
- Un fallo de una fuente no se disfraza como catálogo completo.
- Un dato faltante usa texto o fallback; nunca se rellena con una afirmación inventada.
- Los errores explican qué ocurrió, qué información sigue siendo válida y qué puede hacer la persona.

## 12. Validación de diseño

Una modificación visual o de interacción se considera lista cuando cumple lo aplicable de esta checklist.

### Producto y contenido

- [ ] Refuerza planificación y cotización, no compra ni checkout.
- [ ] Conserva la jerarquía material → color → producto → proveedor.
- [ ] Separa dato, estimación, estado provisional e interpretación.
- [ ] Mantiene fecha, procedencia y límites relevantes.

### Visual y responsive

- [ ] Reutiliza tokens y componentes antes de crear variantes.
- [ ] Funciona en desktop y mobile sin overflow accidental.
- [ ] Mantiene la acción principal y la identidad del producto visibles.
- [ ] Imágenes y muestras no están rotas ni presentan evidencia falsa.
- [ ] Estados vacío, carga, error, deshabilitado y confirmación están diseñados.

### Accesibilidad

- [ ] Navegación completa por teclado y foco visible.
- [ ] Contraste AA y objetivos táctiles adecuados.
- [ ] Nombres, roles, estados y mensajes dinámicos son accesibles.
- [ ] Movimiento reducido y lectura sin dependencia exclusiva del color.

### Verificación técnica

- [ ] `npm.cmd run build`.
- [ ] Tests unitarios del flujo afectado, como `npm.cmd run test:quote-list` o `npm.cmd run test:color-picker`.
- [ ] `npm.cmd run test:ui` para cambios de interfaz pública o flujos cubiertos.
- [ ] Axe/Playwright sin violaciones introducidas ni errores runtime atribuibles a la aplicación.
- [ ] Prueba visual en al menos 390 × 844 y un viewport desktop representativo.
- [ ] `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos` cuando cambia el contrato de datos o su representación.
- [ ] Lighthouse cuando el cambio afecta estructura, carga, SEO o rendimiento de una ruta pública.

La evidencia visual aprobada de Opción 1 en `docs/qa/evidence/option-1/` sigue siendo la referencia histórica de la interfaz material-first. `design-qa.md` registra su comparación y los desvíos aceptados.

## 13. Gobernanza y evolución

- Todo cambio duradero de lenguaje visual, navegación principal, accesibilidad o significado de estados actualiza este archivo en la misma entrega.
- Una excepción local debe explicar superficie, motivo y duración. No se replica hasta convertirse en decisión canónica.
- Antes de crear un componente nuevo se busca uno existente con la misma responsabilidad.
- Antes de agregar un token se verifica que no exista ya un equivalente semántico.
- Las specs de features viven en `docs/superpowers/specs/`; describen el cambio. Este archivo conserva solamente las reglas que deben sobrevivir a esa feature.
- La QA visual vive junto a evidencia reproducible; una captura aislada sin viewport, estado y fecha no constituye aprobación.
- Si código y canon divergen, la revisión debe decidir explícitamente entre corregir la implementación o actualizar este documento.

## 14. Referencias operativas

- Tokens y estilos compartidos: `src/styles/global.css`
- Componentes públicos: `src/components/`
- Catálogo material-first y cotización: `src/SummaryApp.svelte`
- Estadísticas internas: `src/VendorStatsApp.svelte`
- Curación local: `tools/image-curation/`
- Diseño aprobado de Opción 1: `docs/superpowers/specs/2026-07-17-option-1-catalog-redesign-design.md`
- QA visual de Opción 1: `design-qa.md`
- Restricciones de producto y arquitectura: `AGENTS.md`
