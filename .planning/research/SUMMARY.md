# Project Research Summary

**Project:** Central de Filamentos
**Domain:** catalogo estatico Svelte/Vite para lista local de compra/cotizacion de filamentos con consultas por WhatsApp
**Researched:** 2026-06-18
**Confidence:** MEDIUM

## Executive Summary

Central de Filamentos debe seguir siendo un catalogo estatico de stock de filamentos, no un marketplace. La nueva feature es una herramienta de planificacion y cotizacion: el maker arma una lista local en el navegador, compara que proveedores cubren cada item y genera mensajes de WhatsApp individuales para pedir precio y disponibilidad. Expertos construirian este flujo como una capa de dominio browser-only sobre el JSON estatico existente, con persistencia local versionada y sin backend, cuentas, checkout ni promesas de stock en tiempo real.

La recomendacion es implementar helpers puros para lista, cobertura y mensajes, integrados en la pagina Svelte actual mediante componentes compactos. La lista debe persistir solo la intencion del usuario y snapshots legibles de los productos; la cobertura por proveedor se deriva siempre desde el `stock.json` vigente. Import/export JSON es parte del MVP porque compensa la falta de sincronizacion cloud y reduce el riesgo de perdida por `localStorage`.

Los riesgos principales son de confianza y framing: que la lista parezca carrito, que los checks parezcan disponibilidad garantizada, que un proveedor reciba items que no cubre o que el usuario pierda su lista local. Mitigarlos desde la primera fase exige copy de cotizacion, avisos de persistencia local, cobertura `X/Y` con checks por item, mensajes WhatsApp solo con items cubiertos y tests para import/export, cantidad, cobertura parcial y texto generado.

## Key Findings

### Recommended Stack

La pila recomendada es conservar Svelte 5 + Vite como frontend estatico, usar Web APIs nativas para persistencia/import/export/copy/WhatsApp y mantener `public/data/stock.json` como contrato de lectura. No hace falta agregar backend, SvelteKit, librerias de estado, IndexedDB ni SDKs de e-commerce para la v1.

**Core technologies:**
- Svelte 5.55.7: UI reactiva para lista, cantidades y paneles de cobertura; encaja con el catalogo existente.
- Vite 8.0.13: build estatico compatible con GitHub Pages y el base path actual.
- Browser Web APIs: `localStorage`, `Blob`, file input, Clipboard API y links `wa.me` cubren el flujo sin servidor.
- JSON estatico generado por Python: fuente de verdad para productos, ofertas, proveedores y contactos.
- Node built-in test runner: opcion liviana para tests puros de helpers JS si se agregan.

### Expected Features

**Must have (table stakes):**
- Agregar filamentos a la lista desde el catalogo, preservando material, color, marca, diametro, presentacion y codigo cuando exista.
- Cantidad editable en kg con accesos `+1 kg` y `+12 kg`.
- Autosave en `localStorage` con aviso claro de que vive solo en ese navegador/dispositivo.
- Exportar/importar JSON con schema/version y validacion.
- Remover items, limpiar lista y copiar listado general.
- Cobertura por proveedor `X/Y`, checks por item y marcador de "cubre toda la lista".
- Vista por proveedor con items cubiertos y mensaje/link de WhatsApp individual.
- Mensajes en tono de consulta que pidan cotizacion, precio y stock actual.
- Copy explicito de que StockCentral/Central de Filamentos no vende ni procesa pedidos.

**Should have (competitive):**
- Ranking simple por cobertura, priorizando proveedores que cubren toda la lista.
- Reporte de faltantes por proveedor.
- Copiar mensaje individual por proveedor como fallback o canal alternativo.
- Deteccion de duplicados/similares cuando haya datos reales de uso.
- Listas guardadas con nombre si los makers usan la herramienta para proyectos recurrentes.

**Defer (v2+):**
- Sugerencias automaticas multi-proveedor: requiere optimizacion y puede confundir sin precios confiables.
- Seguimiento de precios/cotizaciones recibidas: acerca el producto a procurement.
- URLs compartibles con lista codificada: riesgos de longitud y privacidad.
- Variantes de plantillas WhatsApp: primero validar una plantilla neutral.
- Cuentas, sync cloud, pagos, checkout, reservas o marketplace: fuera del producto estatico.

### Architecture Approach

La arquitectura debe separar intencion persistida de estado derivado. `CatalogApp.svelte` carga productos y proveedores, mantiene estado local de la lista y pasa datos a componentes. `quoteList.js` normaliza, persiste, importa y exporta. `quoteCoverage.js` calcula cobertura desde `items + products + sources`. `quoteMessages.js` arma texto general y mensajes por proveedor, reutilizando `sourceWhatsappUrl()` de `shared.js`. Ningun modulo de la feature debe escribir `stock.json` ni duplicar contactos de proveedores.

**Major components:**
1. `src/lib/quoteList.js` — storage key versionada, normalizacion, cantidades, import/export y resiliencia ante storage bloqueado.
2. `src/lib/quoteCoverage.js` — cobertura derivada, checks por item, `coveredItems`, `missingItems`, `coveredCount` y `coversAll`.
3. `src/lib/quoteMessages.js` — listado general, mensajes por proveedor solo con items cubiertos, formato compacto y tono de consulta.
4. `QuoteAddControls.svelte` — acciones por producto/presentacion para sumar y ajustar kg.
5. `QuoteListPanel.svelte` — lista local, cantidades, avisos, import/export, copiar, limpiar y resumen.
6. `ProviderCoverageTabs.svelte` o seccion equivalente — bloques por proveedor, checks, preview/copy y WhatsApp.

### Critical Pitfalls

1. **La lista parece carrito de e-commerce** — evitar "carrito", "checkout", "comprar ahora", totales pagables y confirmaciones; usar lista/cotizacion/consulta y disclaimer visible.
2. **Stock estatico tratado como disponibilidad en vivo** — mostrar timestamp/contexto de captura cuando sea posible y pedir confirmacion de stock/precio en cada mensaje.
3. **Cobertura parcial reducida a si/no** — modelar `coveredItems` y `missingItems`; mensajes de WhatsApp deben consumir solo los cubiertos.
4. **Perdida o falla de `localStorage`** — envolver lectura/escritura en `try/catch`, avisar que es local y entregar export/import en MVP.
5. **Import/export inseguro o incompatible** — versionar schema, validar cantidades, limitar tamano/items, reconciliar contra catalogo actual y nunca confiar cobertura importada.
6. **URLs WhatsApp largas o mal dirigidas** — usar contactos del `stock.json`, mensajes compactos por proveedor, preview/copy fallback y guard de longitud.
7. **Deriva de unidades kg/presentacion** — guardar `weightG`, diametro, marca y codigos; tratar samplers o peso desconocido como "revisar presentacion".

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Quote List Foundation
**Rationale:** La lista, el schema y el framing son dependencias de todo lo demas; si se modela mal, cobertura, import/export y WhatsApp heredan errores.
**Delivers:** `quoteList.js`, storage versionado, add/remove/update, `+1 kg`, `+12 kg`, cantidades editables, empty states, aviso local-only y copy no-commerce.
**Addresses:** add from catalog, quantity controls, autosave, remove/clear, local persistence notice.
**Avoids:** e-commerce framing, quantity drift, coupling with stock subscriptions, localStorage loss.

### Phase 2: Portability And Import/Export Resilience
**Rationale:** Import/export es el reemplazo practico de cuentas/sync y debe compartir el mismo contrato que autosave antes de crecer el flujo.
**Delivers:** export JSON, import file, schema/version, merge/replace deliberado, validacion, resumen de importacion y estado para items no reconciliados.
**Addresses:** export list, import list, portability across devices.
**Avoids:** invalid stale imports, silent data loss, trusting imported provider coverage.

### Phase 3: Provider Coverage Semantics
**Rationale:** La cobertura es el nucleo de valor y debe existir antes del WhatsApp para garantizar que cada proveedor reciba solo lo que cubre.
**Delivers:** `quoteCoverage.js`, `X/Y`, checks por item, `coversAll`, providers sorted by coverage, stale/source context where available and provider sections.
**Addresses:** provider coverage summary, per-item checks, complete-list indicator, provider-specific covered-items view.
**Avoids:** stale stock as real-time guarantee, partial coverage flattened, misleading checks.

### Phase 4: WhatsApp Quote Flow
**Rationale:** WhatsApp es el handoff final; depende de cobertura correcta, provider contacts and consultative copy.
**Delivers:** `quoteMessages.js`, general copy, provider message preview, copy fallback, `wa.me` links from source metadata, length guard and quote/disclaimer text.
**Addresses:** provider-specific WhatsApp messages, individual provider buttons, copy full/provider text.
**Avoids:** missing items in provider messages, malformed/too-long WhatsApp URLs, provider-incorrect contacts and purchase-confirmation language.

### Phase 5: Post-v1 Refinements
**Rationale:** Enhancements should follow real usage once the core workflow is trusted.
**Delivers:** coverage ranking polish, missing-item gap report, duplicate/similar warnings, named local lists and optional provider message copy improvements.
**Addresses:** differentiators without changing product identity.
**Avoids:** premature optimization, procurement/workflow creep and overbuilt v2 features.

### Phase Ordering Rationale

- Model and copy come first because they define the product boundary: quote-planning, not commerce.
- Import/export follows early because local-only persistence is a known user-risk, not a later nicety.
- Coverage must precede WhatsApp because provider messages should be built from `coveredItems`, never the full list.
- WhatsApp is intentionally late in v1 so URL length, provider contacts and message tone can be tested against real coverage objects.
- Refinements are separated because ranking, duplicate detection and named lists add complexity without being required to validate the core quote-list workflow.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3:** Validate exact `stock.json` fields for source freshness, stock quantities, `weight_g`, sampler/unknown presentations and provider offer identity before final coverage rules.
- **Phase 4:** Validate WhatsApp URL behavior on target mobile/desktop browsers and choose a conservative encoded-length fallback threshold.
- **Phase 5:** Research only when user demand exists; duplicate detection and named lists depend on observed usage patterns.

Phases with standard patterns (skip research-phase):
- **Phase 1:** Well-documented Svelte local state and browser storage patterns already match existing code.
- **Phase 2:** JSON import/export with schema validation and `Blob` download is standard and covered by current research.
- **Phase 4 message text:** Implementation pattern is standard once provider contact format and length threshold are confirmed.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Strong local-codebase evidence and official docs for Web APIs/Svelte/Vite; exact package versions come from current lockfile but implementation should verify local scripts. |
| Features | MEDIUM | Requirements are well defined in `.planning/PROJECT.md` and aligned with RFQ/catalog patterns; actual maker behavior still needs validation after launch. |
| Architecture | HIGH | Based heavily on current codebase boundaries, existing `stockSubscriptions.js`, `shared.js`, generated data contract and static hosting constraints. |
| Pitfalls | MEDIUM | Risks are well grounded in project constraints and web platform docs; severity should be rechecked with real user feedback. |

**Overall confidence:** MEDIUM

### Gaps to Address

- **Exact stock freshness fields:** During Phase 3, inspect current `stock.json` payload for global/source timestamps and error states; do not invent UI promises the data cannot support.
- **Quantity confidence:** Confirm how samplers, unknown `weight_g` and non-kg products appear in the generated catalog before enabling kg shortcuts universally.
- **Provider contact completeness:** Verify all initial providers expose usable `contact_whatsapp_url`; where missing, show copy fallback instead of hardcoding.
- **WhatsApp length threshold:** Choose and test a conservative fallback on Windows desktop, mobile browser and WhatsApp Web/app handoff.
- **Import conflict UX:** Decide in Phase 2 whether v1 supports replace only, merge only, or both; keep destructive actions explicit.

## Sources

### Primary (HIGH confidence)
- `.planning/PROJECT.md` — product scope, active requirements, constraints and copy boundaries.
- `.planning/research/STACK.md` — recommended stack, browser APIs, testing approach and version notes.
- `.planning/research/FEATURES.md` — table-stakes features, differentiators, anti-features and prioritization.
- `.planning/research/ARCHITECTURE.md` — component boundaries, data model, data flow and testing implications.
- `.planning/research/PITFALLS.md` — critical risks, prevention strategies and phase mapping.
- Local codebase references cited by research: `src/CatalogApp.svelte`, `src/lib/shared.js`, `src/lib/stockSubscriptions.js`, `centraldefilamentos/providers.py`, generated `stock.json` contract and existing tests.

### Secondary (MEDIUM confidence)
- Svelte docs — `$state`, `$effect` and stores guidance for local reactivity.
- Vite docs — base path and static build behavior.
- MDN Web Docs — `localStorage`, Clipboard API, `Blob`, `URL.createObjectURL`, `FileReader`, JSON parse errors and storage quota behavior.
- WhatsApp Help Center — click-to-chat `wa.me` links and prefilled text parameter.
- OWASP HTML5 Security Cheat Sheet — avoid sensitive data in localStorage and treat imported content safely.

### Tertiary (LOW confidence)
- RFQ/e-commerce platform documentation from Optimizely, Ecwid and nopCommerce — useful for identifying patterns to avoid, but not directly defining this static catalog product.
- Filament catalog examples — useful for expected attributes, but provider-specific behavior must come from Central de Filamentos data.

---
*Research completed: 2026-06-18*
*Ready for roadmap: yes*
