# Central de Filamentos

## What This Is

Central de Filamentos es un sitio estatico para makers e usuarios de impresion 3D en Argentina que necesitan encontrar rapido que proveedor tiene el filamento que buscan. El producto centraliza stock online de proveedores, normaliza material, color, marca, diametro, formato y codigos cuando estan disponibles, y ayuda a comparar disponibilidad sin convertir la plataforma en una tienda.

El proximo foco del proyecto es una **lista de compra/cotizacion**: una herramienta local del navegador para que el maker arme un listado de filamentos, vea que proveedores cubren cada item y genere mensajes de WhatsApp individuales para consultar cotizacion y disponibilidad.

## Core Value

Ayudar al maker a convertir la informacion dispersa de stock de filamento en una consulta clara y accionable para comprar mejor, sin que StockCentral venda ni procese pedidos.

## Requirements

### Validated

- Validado: El sitio funciona como catalogo estatico publico consumiendo `public/data/stock.json`.
- Validado: La ingesta Python normaliza productos de proveedores distintos en un catalogo comun.
- Validado: La UI Svelte permite buscar, filtrar y comparar filamentos disponibles.
- Validado: El proyecto puede persistir estado local de usuario en `localStorage`, como ya ocurre con alertas de stock.
- Validado: La publicacion esta separada entre datos, UI y miniaturas mediante GitHub Actions.

### Active

- [ ] El usuario puede agregar filamentos a una lista de compra/cotizacion desde el catalogo.
- [ ] El usuario puede indicar cantidades en kg con accesos rapidos de `+1 kg` y `+12 kg`, y conservar una cantidad editable.
- [ ] Cada item de la lista conserva material, color, cantidad en kg, marca, diametro y codigo de articulo cuando el catalogo lo provee.
- [ ] La lista se guarda automaticamente en el navegador usando almacenamiento local.
- [ ] La UI informa que la lista se guarda solo en ese navegador/dispositivo y puede no estar disponible si se abre la web desde otro equipo o navegador.
- [ ] El usuario puede exportar e importar su lista para guardarla o moverla a otra PC.
- [ ] La plataforma muestra cobertura por proveedor, por ejemplo `cubre X/Y items`.
- [ ] La plataforma muestra checks por item para indicar si un proveedor cumple stock y caracteristicas del item.
- [ ] La plataforma muestra un check general del proveedor cuando cubre toda la lista.
- [ ] El usuario puede ver bloques o pestanas por proveedor con los items que ese proveedor cubre.
- [ ] El usuario puede copiar el listado completo general.
- [ ] El usuario puede generar un texto de WhatsApp por proveedor solo con los items que ese proveedor tiene disponibles.
- [ ] Cada proveedor tiene un boton o link individual de WhatsApp para enviar la consulta.
- [ ] Los mensajes usan tono de consulta, por ejemplo pedir cotizacion y disponibilidad, sin afirmar compra confirmada.
- [ ] La UI comunica explicitamente que StockCentral no vende productos ni procesa pedidos; solo ayuda a planificar y consultar.

### Out of Scope

- Checkout, pagos, ordenes de compra o procesamiento de pedidos - StockCentral no debe operar como marketplace ni e-commerce.
- Backend persistente, cuentas de usuario o sincronizacion cloud - el proyecto se mantiene como sitio estatico en GitHub Pages.
- Confirmacion real de stock o precio al momento de enviar WhatsApp - la disponibilidad publicada puede cambiar y el proveedor debe confirmarla.
- Mensajes de WhatsApp con items faltantes para un proveedor - en v1 el mensaje de cada proveedor incluye solo los items que ese proveedor cubre.
- Optimizacion automatica compleja de compra multi-proveedor - puede explorarse luego, pero v1 prioriza claridad y control del usuario.

## Context

- Proyecto brownfield basado en Python 3.12 para ingesta y normalizacion, Svelte 5 con Vite para UI estatica, y GitHub Pages como hosting.
- El frontend lee JSON estatico desde `public/data/stock.json` usando helpers de `src/lib/shared.js`; no hay backend de aplicacion.
- El estado persistente de usuario debe vivir en `localStorage` o cookies. La experiencia debe explicar con honestidad las limitaciones de ese almacenamiento.
- La feature debe evitar lenguaje de carrito, checkout o compra directa. El framing preferido es "lista de compra", "lista de cotizacion", "armar lista", "pedir cotizacion" y "enviar consulta".
- Los proveedores iniciales del producto son Filamentos3D, Grupo Senz y MundoInsumos. La UI debe poder generar consultas individuales para cada proveedor con datos de contacto disponibles en el catalogo.
- Si un proveedor no cubre todos los items, la UI debe mostrar cobertura y checks, pero el texto de WhatsApp de ese proveedor no debe incluir los faltantes.
- Importar/exportar lista compensa la falta de cuenta de usuario y permite mover una lista entre dispositivos.
- La UI actual esta en espanol argentino y debe seguir siendo compacta, mobile friendly y clara para uso frecuente.

## Constraints

- **Hosting**: sitio estatico en GitHub Pages - no asumir endpoints server-side ni sesiones.
- **Persistencia**: solo `localStorage` o cookies - datos locales, no sincronizados entre dispositivos.
- **Producto**: StockCentral no vende ni procesa pedidos - el copy y los iconos deben reforzar herramienta de planificacion/cotizacion.
- **Datos**: `public/data/stock.json` es generado - cambios durables de producto/ofertas vienen de normalizacion, fuentes, caches o build pipeline.
- **Proveedor**: disponibilidad y precio deben confirmarse con cada proveedor - los mensajes deben pedir cotizacion/disponibilidad, no prometer stock final.
- **UX**: mobile primero, pero con oportunidad de mostrar la lista a la derecha en desktop si el ancho lo permite.
- **Testing local Windows**: usar `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos` o un temp escribible.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Nombrar la feature como lista de compra/cotizacion, no carrito | Evita confusion con venta directa o checkout | - Pending |
| Generar mensajes de WhatsApp por proveedor individual | Refleja como compran los makers y permite consultar a cada proveedor sin backend | - Pending |
| Incluir solo items cubiertos en el mensaje de cada proveedor | Mantiene los mensajes limpios y evita pedir a un proveedor productos que no figuran disponibles | - Pending |
| Mostrar cobertura `X/Y`, checks por item y check general por proveedor | Hace visible cuando un proveedor cumple toda la lista o solo parte | - Pending |
| Persistir lista en almacenamiento local y agregar import/export | Mantiene el sitio estatico y da una salida para mover o guardar listas | - Pending |
| Usar cantidades rapidas `+1 kg` y `+12 kg` | Se ajusta a la compra habitual de filamento por kilo y packs/cajas grandes | - Pending |

---
*Last updated: 2026-06-18 after project initialization*
