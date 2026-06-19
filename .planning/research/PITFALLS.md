# Pitfalls Research

**Domain:** Static stock catalog with local quote-list and WhatsApp consultation flow
**Researched:** 2026-06-18
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: The quote list reads like an e-commerce cart

**What goes wrong:**
Users interpret the feature as a cart, checkout, reservation, or order flow. They assume StockCentral is selling, holding stock, validating price, or committing the provider to fulfill the list. This breaks the project's strict non-commerce positioning and creates support/legal ambiguity when provider stock or prices differ from the static catalog.

**Why it happens:**
Shopping-list UX patterns naturally borrow cart vocabulary: "agregar al carrito", totals, checkout-style buttons, order summaries, and purchase confirmation language. A WhatsApp button with a full item list can feel like an order submission if the copy says "quiero comprar" instead of "consultar disponibilidad y cotizacion".

**How to avoid:**
Use quote/planning language everywhere: "lista de cotizacion", "consulta", "pedir cotizacion", "consultar disponibilidad". Never use "carrito", "checkout", "comprar ahora", "pedido confirmado", payment icons, order numbers, or totals that look payable. The WhatsApp text should explicitly ask the provider to confirm availability and price. Add a visible disclaimer near list actions: StockCentral no vende ni procesa pedidos; solo ayuda a armar consultas.

**Warning signs:**
Buttons say "comprar", "finalizar", "hacer pedido", or "enviar pedido". Users ask where to pay. The generated WhatsApp text says "quiero comprar estos productos" without asking for confirmation. UI tests only assert link creation and miss copy/framing.

**Phase to address:**
Phase 1: Quote-list framing and local list MVP. This phase should set naming, empty states, button labels, and message tone before provider coverage logic makes the feature feel transactional.

---

### Pitfall 2: Stale stock is presented as real-time availability

**What goes wrong:**
The list shows provider checks as if they mean the provider currently has stock. A maker sends a WhatsApp consultation expecting guaranteed availability, but the static `public/data/stock.json` may be hours or days old, a provider sheet/page may have changed, or the build may have been blocked by quality gates.

**Why it happens:**
The existing catalog is generated offline and published as static JSON. Provider offers include `updated_at` and source status, but list UX can hide that context behind green checks. Checks for "provider covers item" are derived from the last captured payload, not from a live provider API.

**How to avoid:**
Label checks as "figura disponible en la ultima captura" or equivalent. Show the capture timestamp near the list and inside the copied/WhatsApp text when space allows. Message copy must ask "me confirmas disponibilidad y precio?" rather than state "tenes stock". If build/source status is stale or errored, surface a warning in the list panel before generating messages.

**Warning signs:**
Coverage chips say only "disponible" with no timestamp. WhatsApp messages omit "segun Central de Filamentos" and omit confirmation language. Provider source errors exist in build logs but the list still shows all checks as confident. Users report that checks do not match provider replies.

**Phase to address:**
Phase 2: Provider coverage and stock-state semantics. The coverage model must define "covered from static data" before the UI turns it into checks.

---

### Pitfall 3: Partial provider coverage is flattened into a misleading yes/no

**What goes wrong:**
A provider with 3 of 5 requested items appears equivalent to a provider with all 5, or the WhatsApp message includes missing items. Users waste time contacting providers about products not listed there, and provider replies become noisy.

**Why it happens:**
The product requirement has two related concepts: provider-level coverage (`X/Y items`) and item-level checks. Implementations often compute only "has at least one offer" or only "all items covered", then lose the middle state. Another common mistake is generating WhatsApp text from the whole list instead of the provider-covered subset.

**How to avoid:**
Model coverage as a first-class derived object: `providerId`, `coveredItems`, `missingItems`, `coveredCount`, `totalCount`, `coversAll`. Generate provider WhatsApp messages exclusively from `coveredItems`. Show missing items in the UI for transparency, but do not include them in that provider's WhatsApp message in v1. Add tests for 0/Y, partial X/Y, and full Y/Y coverage.

**Warning signs:**
Coverage labels are boolean only. The same message text is reused for all providers. UI has a global "copiar lista" but no provider-scoped message preview. Tests cover only the happy path where one provider covers every item.

**Phase to address:**
Phase 2: Coverage engine and provider panels. This should be implemented before WhatsApp generation so message text cannot accidentally include uncovered items.

---

### Pitfall 4: localStorage loss is treated as data corruption or user error

**What goes wrong:**
Users lose a carefully assembled list after switching devices, using private browsing, clearing site data, changing protocol/origin, or opening a local file build. They assume StockCentral lost their data or silently broke.

**Why it happens:**
`localStorage` is origin-scoped browser storage, not an account. MDN documents that private browsing storage is usually deleted when private mode ends, persistence can be blocked by browser policy, and `file:` URL behavior is not guaranteed. The existing code already uses localStorage for stock watches, but the quote list has higher user effort and therefore higher loss sensitivity.

**How to avoid:**
Create a separate namespaced key such as `centraldefilamentos.quoteList.v1`. Wrap both read and write in `try/catch`, including `QuotaExceededError` and `SecurityError`. Show plain UX copy: "Se guarda solo en este navegador." Provide export/import in the MVP, not later. Consider an explicit "descargar respaldo" action after meaningful edits or before clearing the list.

**Warning signs:**
Only `load` has `try/catch`; `save` can throw. The UI promises "guardado" without saying where. Import/export is deferred past MVP. Bug reports mention "la lista desaparecio" after using another browser or incognito.

**Phase to address:**
Phase 1: Local persistence, resilience, and user copy. Import/export can be a small vertical slice in the same phase because it is the safety valve for no-backend persistence.

---

### Pitfall 5: Import/export accepts invalid, stale, or incompatible list files

**What goes wrong:**
An imported JSON file creates broken rows, negative quantities, duplicate items, old provider assumptions, missing fields, or products that no longer exist in the current `stock.json`. The list then generates incorrect coverage and confusing WhatsApp messages.

**Why it happens:**
Export feels like simple `JSON.stringify(list)`, and import feels like `JSON.parse(file)`. But MDN documents parse errors for invalid JSON, and this product also needs semantic validation against the current generated catalog. Product IDs can shift if normalization rules change, and provider offers can disappear between exports.

**How to avoid:**
Version the export schema: `{ version, exportedAt, items }`. Validate shape, item count, quantity bounds, known product id, provider-agnostic item fields, and optional source product metadata. On import, reconcile each item against current `stock.json` by product id first, then display an "items needing review" state for missing products instead of silently dropping or accepting them. Never import provider coverage as trusted data; always recompute coverage from current stock.

**Warning signs:**
Imported files can contain arbitrary fields that later render directly. Quantity accepts `NaN`, `0`, negative values, or huge values. Import success says "listo" even when some products were not found. Export has no version or timestamp.

**Phase to address:**
Phase 1: Export/import contract. Phase 2 should reuse the imported list but recompute coverage from current data.

---

### Pitfall 6: WhatsApp URLs become too long, malformed, or provider-incorrect

**What goes wrong:**
Clicking a provider WhatsApp button fails, opens without the text, truncates the message, or targets the wrong contact. Long quote lists are especially risky because URL length behavior varies by browser/app handoff, and WhatsApp's public click-to-chat docs describe the encoded `text` parameter but do not provide a dependable web URL length contract.

**Why it happens:**
The current helper appends `?text=${encodeURIComponent(message)}` to each provider's `contact_whatsapp_url`. That is correct for small messages, but quote lists add repeated product names, quantities, diameters, brands, and codes. Developers may also forget that provider numbers must come from `SourceConfig`/`stock.json`, not hardcoded UI constants.

**How to avoid:**
Generate one message per provider and include only covered items. Keep message lines compact: quantity, material/line, color, diameter, brand, code when available. Add a character/encoded-length guard and switch to "copiar mensaje" fallback when it exceeds a conservative threshold. Always show a preview or copy option beside the WhatsApp link. Keep provider contacts in `centraldefilamentos/providers.py` and assert generated public data includes valid `wa.me` links.

**Warning signs:**
No message preview. No length guard. Long lists produce a single global WhatsApp URL. Tests only check `sourceWhatsappUrl` exists, not encoded length, provider target, or fallback behavior. Contact numbers are duplicated inside Svelte.

**Phase to address:**
Phase 3: WhatsApp generation and copy fallback. This should come after provider coverage so message length is naturally reduced per provider.

---

### Pitfall 7: Quantity units drift from product presentation

**What goes wrong:**
The list lets users request 12 kg of sampler/lapiz 3D items, treats grams as kilograms incorrectly, or mixes "cantidad de bobinas" with "kg" without clarity. Provider coverage then looks precise while the request itself is semantically wrong.

**Why it happens:**
The requirement wants quantities in kg with quick actions `+1 kg` and `+12 kg`, while catalog products can include `weight_g`, sampler lengths, unknown presentation, diameters, and provider original names. A naive list stores just product id plus quantity and loses presentation nuance.

**How to avoid:**
Store quantity in kg as a numeric value with bounded increments, but keep item metadata from the selected product: material, color, brand, diameter, `weight_g`, display/presentation label, and article code when present. For sampler or unknown-weight products, disable kg quick-add or label the item as "revisar presentacion" before WhatsApp generation. Round and format quantities consistently in `es-AR`.

**Warning signs:**
The same quantity controls appear for bobinas and samplers. WhatsApp text says "12 kg" for a product whose presentation is meters or unknown. Tests do not cover sampler products or missing `weight_g`.

**Phase to address:**
Phase 1: Quote item model and quantity controls. This must be correct before provider coverage and export/import depend on item shape.

---

### Pitfall 8: The local list module becomes tangled with stock alerts

**What goes wrong:**
Quote-list persistence reuses `src/lib/stockSubscriptions.js` or shares storage normalization with stock alerts. A bug in quote-list import/export breaks alert subscriptions, or clearing the list clears stock watches.

**Why it happens:**
The existing localStorage utility is nearby and already solved load/save normalization, so it is tempting to extend it. But alerts and quote lists have different lifecycles, keys, data shapes, and user expectations.

**How to avoid:**
Create a separate frontend module, for example `src/lib/quoteList.js`, with its own key, schema version, normalizer, migration hook, and tests. Share tiny pure utilities only if they are truly generic, such as safe JSON parse or bounded number parsing.

**Warning signs:**
The quote-list key starts with `stockSubscriptions`. A function named `normalizeSubscriptions` handles quote items. Clearing a quote list calls `localStorage.clear()` or removes unrelated keys. Static source tests assert strings instead of behavior.

**Phase to address:**
Phase 1: Local quote-list state boundary.

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Store only product ids and quantities | Fast MVP persistence | Import files become unrecoverable when product ids shift or products disappear | Only for an internal spike, not roadmap implementation |
| Trust imported JSON after `JSON.parse` | Minimal code | Broken coverage, malformed UI rows, security review debt | Never for user-facing import |
| Hardcode provider WhatsApp numbers in Svelte | Faster button implementation | Contacts drift from `SourceConfig` and tests miss mismatches | Never; provider metadata already exists |
| Generate one global WhatsApp message | Simple copy/link UI | Long URLs, wrong provider targets, missing partial coverage semantics | Only for the general copy text, not provider WhatsApp |
| Add cart-style labels and icons "temporarily" | Users instantly understand the pattern | Product positioning shifts toward e-commerce | Never; naming is part of the product contract |
| Reuse stock subscription storage code | Avoids a new module | Coupled migrations and accidental data deletion | Only extract tiny generic safe-storage helpers |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| WhatsApp click-to-chat | Assuming every generated URL will survive browser/app handoff regardless of message length | Use provider-scoped compact messages, URL encoding, preview, copy fallback, and length guard |
| Provider contacts | Duplicating phone numbers or URLs in frontend components | Read `contact_whatsapp_url` from `public/data/stock.json`, produced from `SourceConfig` |
| Static stock JSON | Treating provider checks as live API availability | Display capture timestamp and ask provider to confirm stock and price |
| Browser storage | Assuming localStorage exists and writes always succeed | Catch read/write errors and expose export/import as backup |
| Import files | Importing old coverage results | Import desired items only; recompute coverage from current catalog data |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Recomputing coverage deeply on every keystroke | Mobile list panel lags when quantities change | Derive normalized quote items once and memoize provider coverage by list signature | Around dozens of list items times multiple providers |
| Serializing the full list to localStorage on every input event | Jank while holding quantity controls | Debounce saves or save on committed state changes; keep payload small | Frequent edits on low-end mobile browsers |
| Building full WhatsApp URLs for every provider on every render | UI churn and huge DOM attributes | Build messages lazily for visible provider panels or on click | Long lists with several providers |
| Rendering missing/covered matrices without constraints | Provider panels become unreadable on mobile | Use compact `X/Y` summary and expandable item details | More than 10 quote items or 3 providers |
| Storing full product/offer objects in localStorage | Payload bloats and imports become stale | Store stable item snapshot fields plus product id, not entire offers | Catalog growth or repeated exports |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Rendering imported item names as HTML | XSS through a malicious exported JSON file | Treat imported text as plain strings; let Svelte escape; never use `{@html}` for import content |
| Storing sensitive personal data in the list | Local device users or scripts can read it; OWASP advises against sensitive localStorage data | Store only product planning data, not addresses, payment notes, buyer identity, or auth-like data |
| Calling `localStorage.clear()` for quote-list reset | Deletes unrelated app/site state, including stock watches | Remove only the quote-list key |
| Opening arbitrary imported URLs | Malicious file can inject links into provider/message UI | Do not trust URLs from import; provider URLs come only from current stock/source metadata |
| Logging full user-generated WhatsApp text to analytics later | Leaks purchase intent or contact notes if analytics is added | Keep v1 client-only; if analytics appears, track events without item-level text |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Hiding local-only persistence caveat | User expects sync across PC/mobile and loses work | Show "guardado en este navegador" near the list and export action |
| Green checks without age/source context | User treats stale static stock as live guarantee | Pair checks with capture timestamp and confirmation copy |
| Provider partial coverage buried in details | User contacts providers inefficiently | Lead with `cubre X/Y` and a clear full-coverage marker |
| WhatsApp button with no preview | User cannot verify what will be sent | Show message preview/copy before opening WhatsApp |
| Quantity controls too fine-grained for makers | Repetitive editing for common purchase sizes | Provide `+1 kg`, `+12 kg`, editable numeric input, and reset/remove |
| Import failure as a generic error | User cannot recover old lists | Report invalid file, unsupported version, and per-item review states separately |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Local list persistence:** Saves and loads in normal browsing, but also handles blocked localStorage, private browsing loss, quota errors, and origin changes.
- [ ] **Export/import:** Exports JSON, but also includes `version`, `exportedAt`, validates quantities, rejects malformed files, and reconciles missing products.
- [ ] **Provider coverage:** Shows `X/Y`, but also tests 0 coverage, partial coverage, full coverage, missing providers, and stale source warnings.
- [ ] **WhatsApp generation:** Opens WhatsApp, but also URL-encodes text, uses provider contacts from source metadata, includes only covered items, and has a copy fallback for long messages.
- [ ] **Non-commerce framing:** Has no checkout, but also avoids cart labels, payment-like totals, and order-confirmation phrasing in empty states, buttons, and generated text.
- [ ] **Quantity controls:** Supports `+1 kg` and `+12 kg`, but also handles samplers, unknown presentations, decimal edits, bounds, and formatting.
- [ ] **Testing:** Source assertions pass, but runtime DOM behavior, localStorage failures, import files, and message-generation edge cases are verified.

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| E-commerce confusion shipped | MEDIUM | Rename labels/buttons, update generated WhatsApp copy, add disclaimer near list actions, add static tests for banned terms |
| Users lose local lists | MEDIUM | Add export/import immediately, add storage error banner, document local-only storage, avoid destructive migrations |
| Partial coverage messages include missing items | HIGH | Refactor message generation to consume `coveredItems`, add coverage fixtures, patch UI copy explaining old behavior |
| WhatsApp URLs fail for long lists | LOW | Add copy fallback and length guard, compact message format, split by provider or ask user to copy manually |
| Imported files break UI | MEDIUM | Add safe parse and schema validation, quarantine invalid items, provide export migration if versioned data exists |
| Stale stock complaints increase | MEDIUM | Surface capture timestamp, provider source status, and confirmation language more prominently |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| E-commerce confusion | Phase 1: Framing and local list MVP | Static text tests reject banned cart/checkout terms; WhatsApp copy asks for cotizacion/disponibilidad |
| Stale stock treated as live | Phase 2: Coverage semantics | UI shows capture timestamp and stale/source warning; tests cover old `generated_at` and source error states |
| Partial coverage flattened | Phase 2: Coverage engine | Unit tests cover 0/Y, X/Y, Y/Y; provider message contains only covered item ids |
| localStorage loss | Phase 1: Persistence and backup | Tests/mock browser storage throwing on get/set; UI explains local-only storage; export action present |
| Import/export incompatibility | Phase 1: Export/import contract | Fixture tests for valid v1, malformed JSON, unsupported version, missing product, invalid quantity |
| WhatsApp URL failure | Phase 3: Message generation | Tests for URL encoding, provider target, encoded-length fallback, and copy preview |
| Quantity/presentation drift | Phase 1: Item model | Tests cover 1 kg, 12 kg, decimal edit, sampler, unknown weight, and display formatting |
| State module coupling | Phase 1: Frontend state boundary | Separate `quoteList` storage key; reset removes only quote-list key |

## Sources

- Project context: `.planning/PROJECT.md`
- Known codebase risks: `.planning/codebase/CONCERNS.md`
- Existing test strategy: `.planning/codebase/TESTING.md`
- Current architecture: `.planning/codebase/ARCHITECTURE.md`
- Current localStorage implementation: `src/lib/stockSubscriptions.js`
- Current provider contact contract: `centraldefilamentos/providers.py`, `tests/test_providers.py`
- WhatsApp Help Center, click-to-chat / link from other app: https://faq.whatsapp.com/5913398998672934 and https://faq.whatsapp.com/425247423114725
- MDN, `window.localStorage`: https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage
- MDN, storage quotas and eviction criteria: https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria
- web.dev, Storage for the web: https://web.dev/articles/storage-for-the-web
- MDN, JSON.parse bad parsing: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Errors/JSON_bad_parse
- OWASP HTML5 Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html

---
*Pitfalls research for: local quote-list and WhatsApp flow in StockCentral*
*Researched: 2026-06-18*
