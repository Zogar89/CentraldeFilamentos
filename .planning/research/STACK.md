# Stack Research

**Domain:** lista local de compra/cotizacion y flujo de WhatsApp para catalogo estatico Svelte/Vite sin backend
**Researched:** 2026-06-18
**Confidence:** MEDIUM

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Svelte | 5.55.7 | UI reactiva de lista, cantidades, cobertura por proveedor y paneles de consulta | Ya es el framework del catalogo. Usar `$state` para el estado editable de la lista y `$derived` para totales/cobertura evita sumar un store global o una libreria de estado para una feature local. Confidence: MEDIUM. |
| Vite | 8.0.13 | Build estatico para GitHub Pages | Ya resuelve el base path `/CentraldeFilamentos/`. Mantener helpers existentes como `dataUrl`/`fetchJson` evita romper URLs bajo GitHub Pages. Confidence: MEDIUM. |
| Browser Web APIs | Baseline web platform | Persistencia local, import/export, copiar texto y apertura de WhatsApp | `localStorage`, `Blob`, `URL.createObjectURL`, `Blob.text()`/`FileReader`, `navigator.clipboard.writeText` y links `wa.me` cubren el flujo completo sin backend. Confidence: MEDIUM. |
| Static JSON from Python pipeline | Current project contract | Catalogo fuente para productos, ofertas, proveedores y contactos | La lista debe consumir `public/data/stock.json`; no debe editar datos generados ni introducir persistencia remota. Confidence: HIGH, basado en codebase local. |

### Supporting Libraries

| Library / API | Version | Purpose | When to Use |
|---------------|---------|---------|-------------|
| `localStorage` | Web Storage API | Guardar automaticamente la lista en el navegador | Usar para una lista chica, versionada y local al dispositivo. Envolver lectura/escritura en `try/catch` porque puede lanzar `SecurityError` o fallar por politicas del navegador. |
| `Blob` + `URL.createObjectURL` + anchor `download` | Web APIs | Exportar la lista como JSON descargable | Usar para `centraldefilamentos-lista-cotizacion.json`. Revocar el object URL despues de disparar la descarga. |
| `Blob.text()` con fallback a `FileReader.readAsText` | Web APIs | Importar JSON desde `<input type="file">` | Usar para listas chicas. Validar `schema`, `version` e items antes de guardar. |
| `navigator.clipboard.writeText` | Clipboard API | Copiar listado general o texto por proveedor | Usar desde un click/tap del usuario. Mostrar fallback visual si el navegador niega permisos o no hay contexto seguro. |
| `encodeURIComponent` + `sourceWhatsappUrl` | JavaScript + helper existente | Generar links de WhatsApp por proveedor | Reusar `src/lib/shared.js:sourceWhatsappUrl` cuando exista `contact_whatsapp_url`; si falta contacto, ofrecer copiar texto. |
| Node.js built-in test runner | Node 24 | Tests unitarios de helpers JS sin nueva dependencia | Usar si se extraen helpers puros para normalizacion de lista, cobertura e import/export. No instalar Vitest para esta fase salvo que el frontend crezca mucho. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `npm run build` | Verificar compilacion Vite/Svelte | Debe seguir funcionando sin backend ni variables privadas. |
| `python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos` | Suite existente en Windows | Agregar tests Python de invariantes si se inspeccionan fuentes frontend o contrato de `stock.json`. |
| `node --test` | Tests JS opcionales para helpers puros | Recomendado si se crea `src/lib/quoteList.js` o `src/lib/quoteMessages.js`; evita traer un runner adicional. |

## Installation

```bash
# Core
# No instalar dependencias nuevas para la primera version.
# Reusar Svelte/Vite ya presentes en package-lock.json.

# Verification
npm run build
python -m pytest -v --basetemp C:\tmp\pytest-centraldefilamentos

# Optional JS helper tests, if added
node --test tests/js/*.test.mjs
```

## Prescriptive Implementation Pattern

### Modules to Add

| Module | Responsibility | Confidence |
|--------|----------------|------------|
| `src/lib/quoteList.js` | Storage key, schema version, normalization, add/update/remove quantities, import/export payload validation | HIGH |
| `src/lib/quoteMessages.js` | Provider coverage, item matching, general copy text, provider-specific WhatsApp message body | HIGH |
| `src/components/QuoteListPanel.svelte` | Compact mobile-friendly panel/drawer or desktop side panel for list operations | MEDIUM |
| `src/CatalogApp.svelte` integration | Add buttons on product/offers, pass loaded products/sources into quote helpers, render panel | HIGH |

### Storage Contract

Use a versioned local payload, not raw component state:

```js
const quoteListStorageKey = "centraldefilamentos.quoteList.v1";

{
  schema: "centraldefilamentos.quoteList",
  version: 1,
  updatedAt: "2026-06-18T00:00:00.000Z",
  items: [
    {
      key: "product-id::diameter::brand::color",
      productId: "pla-standard-negro-175-1000g",
      quantityKg: 1,
      material: "PLA",
      color: "Negro",
      brand: "Grilon3",
      diameterMm: 1.75,
      weightG: 1000,
      articleCode: "optional provider/catalog code",
      displayName: "PLA Negro 1 kg"
    }
  ]
}
```

Rationale:
- `productId` lets the app rejoin with fresh `stock.json`.
- Snapshot fields keep exported/imported lists understandable even if catalog data later changes.
- `version` allows migration without breaking old local lists.
- `quantityKg` should be numeric, clamped to positive values, and rounded to practical filament quantities.

### Browser Persistence Pattern

Follow the existing `src/lib/stockSubscriptions.js` style:
- `loadQuoteList()` returns a normalized empty list on missing/invalid data.
- `saveQuoteList(items)` serializes only the versioned public schema.
- All `localStorage` access is guarded with `typeof localStorage !== "undefined"` and `try/catch`.
- UI copy must say the list is saved only in this browser/device.

Use `localStorage`, not cookies. Cookies would be sent with every static request and provide less ergonomic structured storage. Use IndexedDB only if future milestones store large multi-list history, images, or offline snapshots; this feature is tiny and synchronous `localStorage` is simpler.

### Import/Export Pattern

Export:
- Serialize the same versioned schema used for local persistence.
- Create a JSON `Blob` with `type: "application/json"`.
- Generate an object URL, click an anchor with `download`, then call `URL.revokeObjectURL`.

Import:
- Use `<input type="file" accept="application/json,.json">`.
- Read with `await file.text()` where available; fallback to `FileReader.readAsText`.
- Parse JSON, validate schema/version/items, normalize quantities, then offer replace/merge behavior.
- Never execute imported content or trust unknown fields.

### WhatsApp Pattern

Use provider-specific generated text and links:
- Compute provider coverage from current `stock.json`.
- Include only items that provider covers in that provider's message.
- Tone should request cotizacion/disponibilidad, not confirm a purchase.
- Use existing `sourceWhatsappUrl(source, message)` because it appends `text=` with `encodeURIComponent`.
- If `source.contact_whatsapp_url` is missing, disable WhatsApp and keep `Copiar texto`.

Message structure:

```text
Hola, te consulto por cotizacion y disponibilidad de estos filamentos:

- PLA Negro 1.75 mm, Grilon3, 2 kg
- PETG Blanco 1.75 mm, 1 kg

Lo arme desde StockCentral como referencia. Me confirmas precio y stock disponible?
```

Keep messages short. For long lists, provide copy/export and consider truncation warnings rather than forcing a huge WhatsApp URL.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Web APIs nativas | `dexie` / IndexedDB wrappers | Only if the app later needs multi-list history, large offline snapshots, or complex indexed search. |
| Component/local module state | Svelte store library or global app store | Only if the quote list becomes shared across multiple independent pages. Current scope is catalog-first. |
| JSON import/export with Blob/File | Backend account sync | Out of scope: violates static GitHub Pages/no backend constraint. |
| `wa.me` links | WhatsApp Business Cloud API | Only for a real business account sending server-side messages; it needs credentials/backend and is wrong for user-initiated provider consultations. |
| Node built-in tests | Vitest | Use Vitest only if Svelte component testing becomes necessary. For pure quote helpers, `node --test` is enough. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| SvelteKit/server routes | The project is static Vite and hosted on GitHub Pages; server routes would create deployment/runtime mismatch. | Plain Svelte components and browser APIs. |
| Backend persistence, auth, user accounts | Explicitly out of scope and unnecessary for a quote-planning tool. | `localStorage` plus import/export. |
| Cookies for the list | Worse fit for structured local data and can be blocked with persistence policies. | Versioned `localStorage` payload. |
| Direct edits to `public/data/stock.json` | Generated output will be overwritten by Python pipeline. | Derive quote behavior in frontend from the generated payload. |
| Cart/checkout/ecommerce SDKs | Creates marketplace expectations and conflicts with "StockCentral no vende". | "Lista de compra/cotizacion" wording and WhatsApp consultation flow. |
| WhatsApp Business API | Requires backend, tokens, templates and business account setup; overbuilt for click-to-chat. | `https://wa.me/<number>?text=<encoded message>`. |
| New heavy state/persistence libraries | More bundle and maintenance for a small local list. | Focused `src/lib/quoteList.js` + Svelte state. |
| Hardcoded `/data/stock.json` or GitHub Pages URLs | Breaks Vite base path/local dev assumptions. | Existing `fetchJson("data/stock.json")` and `dataUrl`. |

## Stack Patterns by Variant

**If implementing v1 in one catalog page:**
- Use local Svelte state in `CatalogApp.svelte` plus focused helper modules.
- Persist through `quoteList.js`.
- Because there is no cross-page synchronization requirement yet.

**If the list later appears on `resumen.html`:**
- Promote quote list state into a minimal Svelte store or shared module with subscription semantics.
- Keep the same storage schema.
- Because multiple app entries cannot share component-local state.

**If provider matching becomes fuzzy:**
- Keep matching logic in `quoteMessages.js` and test it as pure JS.
- Prefer catalog-normalized fields (`material`, `color`, `brand`, `diameter_mm`, `weight_g`, provider offer ids/codes) over display-name parsing.
- Because the Python pipeline already owns normalization.

**If localStorage is unavailable:**
- Keep an in-memory list for the current session.
- Show clear warning that persistence/import/export are still available but autosave failed.
- Because MDN documents browser policy and origin cases where persistence can be denied.

## Version Compatibility

| Package / API | Compatible With | Notes |
|---------------|-----------------|-------|
| `svelte@5.55.7` | `@sveltejs/vite-plugin-svelte@7.1.2` | Current lockfile versions. Use Svelte 5 runes in new components if the existing app style allows it; otherwise match local component style. |
| `vite@8.0.13` | GitHub Pages base `/CentraldeFilamentos/` | Dynamic URLs must use `import.meta.env.BASE_URL` through existing helpers. |
| `localStorage` | GitHub Pages HTTPS and localhost dev | Guard exceptions; data is same-origin and browser/device local. |
| Clipboard API | Secure contexts and user gesture | GitHub Pages is HTTPS. Still handle denial/failure gracefully. |
| Blob/File APIs | Modern browsers | Safe for small JSON import/export. Use `Blob.text()` where available, fallback to `FileReader`. |
| WhatsApp `wa.me` | Browser, WhatsApp Web/mobile | Phone must be international format without spaces or plus in the `wa.me` path; message must be URL-encoded. |

## Sources

- Local codebase: `.planning/PROJECT.md`, `.planning/codebase/STACK.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md` - current constraints and file placement. Confidence: HIGH.
- Local codebase: `package.json`, `package-lock.json`, `src/lib/shared.js`, `src/lib/stockSubscriptions.js`, `vite.config.js` - exact versions and existing persistence/URL patterns. Confidence: HIGH.
- [Svelte `$state` docs](https://svelte.dev/docs/svelte/%24state) - local reactive state and deep state behavior. Confidence: MEDIUM.
- [Svelte `$effect` docs](https://svelte.dev/docs/svelte/%24effect) - browser-side effect timing and guidance not to use effects for derived state. Confidence: MEDIUM.
- [Svelte stores docs](https://svelte.dev/docs/svelte/stores) - store alternative if state must later cross page/app boundaries. Confidence: MEDIUM.
- [Vite env docs](https://vite.dev/guide/env-and-mode) and [Vite build base docs](https://vite.dev/guide/build) - `import.meta.env.BASE_URL` and public base path behavior. Confidence: MEDIUM.
- [MDN `localStorage`](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage) - exceptions and local browser persistence caveats. Confidence: MEDIUM.
- [MDN `URL.createObjectURL`](https://developer.mozilla.org/en-US/docs/Web/API/URL/createObjectURL_static), [MDN `FileReader.readAsText`](https://developer.mozilla.org/en-US/docs/Web/API/FileReader/readAsText), [MDN Clipboard API](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard_API) - native import/export/copy APIs. Confidence: MEDIUM.
- [WhatsApp Help Center click-to-chat](https://faq.whatsapp.com/5913398998672934) - `wa.me` link and `text` parameter format. Confidence: MEDIUM.

---
*Stack research for: browser-local quote list and WhatsApp flow in StockCentral*
*Researched: 2026-06-18*
