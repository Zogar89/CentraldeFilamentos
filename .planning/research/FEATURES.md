# Feature Research

**Domain:** non-commerce maker filament quote list and provider-specific WhatsApp inquiry flow
**Researched:** 2026-06-18
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Add filament to list from catalog product cards | The catalog is the source of truth; users should not retype material/color/provider data already visible. | MEDIUM | Add an explicit "Agregar a lista" or "Pedir cotizacion" action, not cart wording. Preserve product id, material, color, brand, diameter, line/display name, and article/SKU code when available. |
| Editable kg quantity per item | Filament buying decisions are quantity-driven, and the project already validates `+1 kg` and `+12 kg` shortcuts. | LOW | Store quantity as kg numeric value with quick buttons and manual edit. Avoid unit ambiguity in messages. |
| Local autosave in `localStorage` | A list that disappears on refresh feels broken, but the static site cannot use backend accounts. | LOW | Use a versioned key separate from existing stock subscriptions. Copy must say it is saved only in this browser/device. |
| Clear local-storage limitation notice | Users need to understand why the list is not available on another PC or browser. | LOW | Suggested copy: "StockCentral guarda esta lista solo en este navegador. Para llevarla a otra PC, exportala." |
| Export list | Import/export is the portability substitute for accounts or cloud sync. | MEDIUM | Prefer JSON download with schema version and created/exported timestamp. Include enough product fields to survive catalog drift. |
| Import list | Users need to restore or move local quote lists across devices. | MEDIUM | Validate schema version, merge or replace intentionally, and show an import summary before applying destructive replacement. |
| Remove item and clear list | Basic list control is expected; without it, mistakes accumulate. | LOW | Use confirmation only for clear-all, not for single item removal. |
| Copy complete general list | Some users will paste into their own notes, email, or manual WhatsApp thread. | LOW | General copy can include all requested items, regardless of provider coverage. Make it a neutral "lista para consultar", not an order. |
| Provider coverage summary (`X/Y items`) | The main value is knowing which provider can satisfy which requested filaments. | MEDIUM | Compute from current catalog offers; surface per provider and update reactively as quantities/items change. |
| Per-item provider checks | Users need to see why a provider covers or does not cover a list. | MEDIUM | Check exact product identity and required characteristics: material, color, brand when specified, diameter, article code when available. Quantity can be requested, but current stock quantity may not be reliable unless source data supports it. |
| Provider complete-list indicator | Users need a fast signal for "this provider covers everything". | LOW | Use a check label like "Cubre toda la lista" and avoid "comprar todo aca". |
| Provider-specific covered-items view | A maker comparing providers expects to see each provider's subset before messaging. | MEDIUM | Tabs, sections, or compact cards by provider. Include only covered items by default. |
| WhatsApp message per provider | WhatsApp is the natural handoff channel for Argentine provider inquiries. | MEDIUM | Generate `wa.me` links with URL-encoded text and provider phone metadata. Also provide copy fallback if phone/link is missing. |
| WhatsApp text includes only provider-covered items | The project explicitly wants clean provider-specific inquiries and no missing-item requests in v1. | MEDIUM | Message should not include uncovered items. The UI can still show coverage gaps outside the message. |
| Quote-oriented message tone | StockCentral must not imply purchase confirmation, final stock, price, or checkout. | LOW | Suggested opening: "Hola, queria consultar cotizacion y disponibilidad de estos filamentos que figuran en StockCentral..." Suggested closing: "Me confirmas precio, stock actual y forma de pago/envio?" |
| Explicit "StockCentral does not sell" copy | Prevents marketplace/e-commerce confusion and sets correct expectations. | LOW | Repeat in list panel and before WhatsApp action: "StockCentral no vende ni procesa pedidos; solo arma la consulta para que hables con el proveedor." |
| Mobile-friendly list access | Makers may use the catalog from a phone right before contacting providers. | MEDIUM | Use a sticky compact list button/drawer on mobile; optional right-side panel on desktop. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| One-tap provider comparison by coverage | Makes StockCentral more useful than a static catalog by turning stock data into an action plan. | MEDIUM | Good v1.x enhancement after base coverage logic is proven. |
| Highlight "best first provider" without auto-optimizing | Helps users decide whom to message first while keeping control in their hands. | MEDIUM | Rank complete coverage first, then highest `X/Y`; avoid claiming cheapest/best because price is not confirmed. |
| Missing-item gap report | Helps users identify exactly what prevents a provider from covering the whole list. | MEDIUM | Defer until the base covered-items flow is stable; useful in UI, but not in provider WhatsApp text for v1. |
| Duplicate/similar item detection | Prevents accidental duplicate requests for the same filament under nearby names. | MEDIUM | Needs careful product identity rules; risky if normalization changes. Defer until real usage reveals duplicate patterns. |
| Saved named lists | Makers may maintain project lists, restock lists, or client job lists. | MEDIUM | Requires local list management but still no backend. Add after single-list behavior is validated. |
| Provider message templates | Users may want formal, short, bulk, or pickup/shipping variants. | MEDIUM | Defer; v1 should ship one high-quality neutral template. |
| Share/import via encoded URL | Lightweight way to move a list without files. | HIGH | Could hit URL length limits and expose data in URLs. Prefer JSON import/export first. |
| Price response tracking | Lets user compare quoted prices after WhatsApp replies. | HIGH | Valuable but shifts toward procurement workflow. Only consider after confirming demand and keeping data local. |
| Multi-provider split suggestion | Could suggest which providers together cover the whole list. | HIGH | Useful for larger lists, but can become optimization-heavy and confusing without prices and reliable quantities. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Shopping cart / checkout language | Familiar pattern for product selection. | Makes StockCentral look like it sells products or processes orders. | Use "lista", "consulta", "cotizacion", "enviar consulta", and "copiar listado". |
| Payments, invoices, order placement, checkout | Users may expect end-to-end purchase convenience. | Violates project scope, requires backend/compliance, and changes product identity into marketplace/e-commerce. | Handoff to provider WhatsApp; provider confirms payment and delivery terms. |
| User accounts or cloud sync | Solves cross-device persistence elegantly. | Breaks static GitHub Pages/no-backend constraint. | `localStorage` plus import/export. |
| Real-time stock or price guarantees | Users want certainty before contacting providers. | Current data is static snapshot and provider inventory can change. | Copy must ask provider to confirm current stock and price. |
| Including unavailable/missing items in provider WhatsApp messages | Users may want one message per provider asking for everything. | Creates noisy messages and asks providers for products StockCentral does not show them covering. | In v1, include only covered items; show gaps separately in UI. |
| Marketplace-style provider bidding | Could make quote comparison powerful. | Requires backend, provider participation, identity, notifications, and moderation. | Manual WhatsApp inquiries per provider. |
| Automatic cheapest provider selection | Users want a recommendation. | StockCentral does not have reliable live prices in scope. | Rank by coverage only; leave price comparison to provider replies. |
| Reserving stock | Sounds useful when inventory is scarce. | StockCentral cannot mutate provider inventory or guarantee reservation. | Message asks provider to confirm availability and next steps. |
| Delivery/shipping calculation | Helpful for final buying decision. | Depends on user address, provider policy, live costs, and payment flow. | Ask provider for pickup/shipping options in the WhatsApp template. |
| Analytics or server-side quote tracking | Useful for product learning. | Requires backend and changes privacy expectations. | Keep the list local; rely on qualitative feedback for now. |

## UX Copy Implications

Use language that frames the feature as planning and inquiry:

| Context | Recommended Copy | Avoid |
|---------|------------------|-------|
| Add action | "Agregar a lista" / "Sumar a cotizacion" | "Agregar al carrito", "Comprar" |
| List title | "Lista de compra/cotizacion" | "Carrito", "Pedido" |
| Provider CTA | "Enviar consulta por WhatsApp" | "Finalizar compra", "Hacer pedido" |
| Provider coverage | "Cubre 3/5 items" / "Cubre toda la lista" | "Proveedor ganador", "Comprar todo aca" |
| Persistence note | "Se guarda solo en este navegador." | "Tu cuenta", "Sincronizado" |
| Trust disclaimer | "StockCentral no vende ni procesa pedidos; solo ayuda a armar la consulta." | "Compras en StockCentral" |
| Availability disclaimer | "Confirmar precio y stock actual con el proveedor." | "Stock garantizado", "Precio final" |

Suggested WhatsApp template:

```text
Hola, queria consultar cotizacion y disponibilidad de estos filamentos que figuran en StockCentral:

- PLA Negro, 1.75 mm, Marca X, Codigo ABC123, 2 kg
- PETG Transparente, 1.75 mm, 1 kg

Me confirmas precio, stock actual y opciones de pago/envio?
Gracias.
```

The message should be generated per provider and include only items that provider currently covers in the catalog data.

## Feature Dependencies

```text
Catalog add action
    └──requires──> list item schema
                       └──requires──> product identity fields from stock.json

Quantity controls
    └──requires──> list item schema

Autosave
    └──requires──> list item schema
                       └──enhanced-by──> import/export schema version

Provider coverage
    └──requires──> list item schema + current stock.json offers
                       └──enables──> provider sections
                                      └──enables──> provider-specific WhatsApp links

Provider-specific WhatsApp links
    └──requires──> provider contact metadata + covered-items filtering + encoded message builder

Clear non-commerce copy
    └──constrains──> all CTAs, empty states, message templates, and provider coverage labels

Backend accounts / checkout / payments
    └──conflicts──> static no-backend product strategy
```

### Dependency Notes

- **List item schema requires stock identity fields:** The list should snapshot enough display data for export/import, but keep product ids so coverage can be recalculated against current catalog data.
- **Coverage requires current offers:** Coverage should be computed from loaded `stock.json`, not stored permanently in the list, because provider stock changes between visits.
- **WhatsApp requires covered-items filtering:** The provider message builder must receive the filtered covered subset, not the full list.
- **Import/export should follow autosave:** The same schema can power local persistence and portable files, reducing drift.
- **Copy constraints apply from the first phase:** Retrofitting language after users see "cart/checkout" language risks confusion and trust damage.

## MVP Definition

### Launch With (v1)

Minimum viable product - what's needed to validate the concept.

- [ ] Add/remove catalog products to a single local list - essential for the core workflow.
- [ ] Editable kg quantity with `+1 kg` and `+12 kg` shortcuts - essential for maker purchasing.
- [ ] Persist the list in `localStorage` - essential so refresh/navigation does not destroy work.
- [ ] Local-only persistence notice - essential for honest UX under no-backend constraints.
- [ ] Export/import JSON - essential because there are no accounts or cloud sync.
- [ ] Copy full general list - essential fallback for users who do not want provider-specific flows.
- [ ] Provider coverage `X/Y` and complete-list check - essential to transform catalog data into quote planning.
- [ ] Per-item checks by provider - essential to explain coverage.
- [ ] Provider-specific sections/tabs with covered items - essential before WhatsApp handoff.
- [ ] WhatsApp message/link per provider, only covered items - essential value delivery.
- [ ] Non-commerce disclaimer and quote-oriented CTA/copy - essential to keep the product out of e-commerce expectations.

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] Rank providers by coverage - add once coverage calculations are trusted.
- [ ] Missing-item gap report - add once users ask "what am I missing?" during provider comparison.
- [ ] Copy individual provider list without WhatsApp - add if users use desktop WhatsApp or alternate channels often.
- [ ] Import conflict resolution modes - add if users frequently import over existing lists.
- [ ] Duplicate/similar item warning - add after observing real duplicate mistakes.
- [ ] Saved named lists - add if makers use the tool for multiple projects or recurring restocks.

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Multi-provider split suggestions - defer because it adds optimization complexity without prices.
- [ ] Manual quote/price response tracking - defer because it becomes procurement software.
- [ ] Shareable encoded list URL - defer until list sizes and privacy expectations are understood.
- [ ] Provider message template variants - defer until the single default template is proven.
- [ ] Optional notes per item - defer unless users need substitutions, finish requirements, or urgency notes.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Add to list from catalog | HIGH | MEDIUM | P1 |
| Editable kg quantity | HIGH | LOW | P1 |
| `localStorage` autosave | HIGH | LOW | P1 |
| Local-only persistence notice | HIGH | LOW | P1 |
| Export/import JSON | HIGH | MEDIUM | P1 |
| Copy full general list | MEDIUM | LOW | P1 |
| Provider coverage `X/Y` | HIGH | MEDIUM | P1 |
| Per-item provider checks | HIGH | MEDIUM | P1 |
| Provider-specific covered-items view | HIGH | MEDIUM | P1 |
| WhatsApp link/message per provider | HIGH | MEDIUM | P1 |
| Non-commerce disclaimer/copy | HIGH | LOW | P1 |
| Provider ranking by coverage | MEDIUM | MEDIUM | P2 |
| Missing-item gap report | MEDIUM | MEDIUM | P2 |
| Duplicate/similar warning | MEDIUM | MEDIUM | P2 |
| Saved named lists | MEDIUM | MEDIUM | P2 |
| Multi-provider split suggestion | MEDIUM | HIGH | P3 |
| Price response tracking | MEDIUM | HIGH | P3 |
| Shareable encoded URL | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | RFQ/commerce platforms | Filament catalogs | Our Approach |
|---------|------------------------|-------------------|--------------|
| Selecting products for a quote | RFQ systems commonly let users request pricing for one or more products, often from a cart or quote list. | Filament catalogs expose material/color/diameter/brand but usually remain product browsing experiences. | Use catalog product selection, but call it a local list/cotizacion rather than cart. |
| Quote submission | RFQ platforms submit requests into seller/admin workflows, sales reps, or quote dashboards. | Catalog sites typically route users to product pages or seller contact. | Generate provider-specific WhatsApp messages; no server-side quote records. |
| Checkout/payment | RFQ commerce tools often connect quote acceptance back into orders, checkout, invoices, or payment status. | Filament retailers sell directly. | Deliberately exclude checkout, payment, order placement, and stock reservation. |
| Contact channel | RFQ systems often use forms/email/internal dashboards. | Local providers often rely on direct contact channels. | WhatsApp-first handoff with copy fallback. |
| Product attributes | Commerce catalogs expose category/product attributes. | Filament catalogs emphasize material, color, diameter/thickness, brand, weight, and availability. | Preserve maker-relevant fields and requested kg quantity in list/messages. |
| Persistence | Commerce platforms use accounts or server-side sessions. | Static catalogs generally do not persist user planning. | Browser-local persistence plus import/export under static hosting constraints. |

## Roadmap Implications

Recommended phase shape for requirements:

1. **Local list foundation** - schema, add/remove, quantity controls, autosave, empty states, local-only copy.
2. **Portability and resilience** - export/import, validation, schema versioning, corrupt/unknown import handling.
3. **Provider coverage** - `X/Y`, per-item checks, complete-list indicator, provider sections.
4. **WhatsApp quote flow** - provider-specific message builder, `wa.me` link generation, copy fallback, quote/disclaimer copy.
5. **Post-v1 refinements** - coverage ranking, missing-item gap report, duplicate detection, saved named lists.

Do not start with WhatsApp before coverage logic exists; the hardest UX trust issue is making sure each provider receives only the items it actually covers.

## Sources

- Local project context: `.planning/PROJECT.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/CONCERNS.md` (HIGH confidence for project constraints).
- WhatsApp Help Center, "How to use click to chat" - official `wa.me` and prefilled text behavior (MEDIUM confidence via websearch fallback): https://faq.whatsapp.com/5913398998672934
- MDN Web Docs, `Window.localStorage` - persistence and private browsing behavior (MEDIUM confidence via websearch fallback): https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage
- Optimizely Support, "Get started with Request for Quote" - RFQ pattern and commerce/admin scope to avoid (MEDIUM confidence): https://support.optimizely.com/hc/en-us/articles/4413199875341-Get-started-with-Request-for-Quote
- Ecwid Help Center, "How to collect quote requests in your store" - catalog/RFQ wording, contact flow, and quote-list reference (MEDIUM confidence): https://support.ecwid.com/hc/en-us/articles/360019618680-How-to-collect-quote-requests-in-your-store
- nopCommerce Documentation, "Requests for quote (RFQ)" - standalone RFQ plugin pattern and quote/cart linkage to avoid for StockCentral (MEDIUM confidence): https://docs.nopcommerce.com/en/running-your-store/order-management/rfq.html
- 3DJake filament catalog - filament browsing commonly centers material, color, thickness/diameter, and project fit (MEDIUM confidence): https://www.3djake.com/3d-printer-filaments

---
*Feature research for: StockCentral maker filament quote list*
*Researched: 2026-06-18*
