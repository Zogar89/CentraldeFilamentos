# Phase 01: quote-list-foundation - Pattern Map

**Mapped:** 2026-06-19
**Files analyzed:** 8
**Analogs found:** 8 / 8

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/CatalogApp.svelte` | component | event-driven + localStorage + request-response | `src/CatalogApp.svelte` | exact |
| `src/lib/quoteList.js` | utility | localStorage + transform | `src/lib/stockSubscriptions.js` | exact |
| `src/components/QuoteListPanel.svelte` | component | event-driven | `src/components/SiteHeader.svelte` | role-match |
| `src/components/QuoteListDrawer.svelte` | component | event-driven | `src/CatalogApp.svelte` image preview modal | role-match |
| `src/components/QuoteListItem.svelte` | component | event-driven + transform display | `src/components/SiteFooter.svelte` | role-match |
| `src/components/QuoteQuantityControl.svelte` | component | event-driven | `src/components/QuickLines.svelte` | role-match |
| `src/styles/global.css` | config | responsive layout | `src/styles/global.css` | exact |
| `tests/test_frontend_assets.py` | test | source invariant checks | `tests/test_frontend_assets.py` | exact |

## Pattern Assignments

### `src/CatalogApp.svelte` (component, event-driven + localStorage + request-response)

**Analog:** `src/CatalogApp.svelte`

**Imports and state pattern** (lines 1-32, 46-53):
```svelte
import { onMount } from "svelte";
import QuickLines from "./components/QuickLines.svelte";
import SiteHeader from "./components/SiteHeader.svelte";
import SiteFooter from "./components/SiteFooter.svelte";
import {
  loadStockSubscriptions,
  saveStockSubscriptions,
  stockSignature,
  subscriptionKey,
} from "./lib/stockSubscriptions.js";
import {
  brandRank,
  colorSwatchLabel,
  colorSwatchStyle,
  comparePresentations,
  dataUrl,
  diameterLabel,
  fetchJson,
  formatDate,
  formatPresentation,
  formatWeightLabel,
  lineLabel,
  lineMeta,
  lineOptionLabel,
  lineRank,
  matchesSearchTerms,
  pantoneSwatchLabel,
  productBaseName,
  providerAnchorId,
  slugText,
} from "./lib/shared.js";

let products = [];
let sources = [];
let generatedAt = "";
let categoryOrder = "popular";
let lineHelp = "";
let preview = null;
let stockSubscriptions = [];
let stockAlerts = [];
```

**Static data load + local browser state pattern** (lines 55-62):
```svelte
onMount(async () => {
  const payload = await fetchJson("data/stock.json", { products: [], sources: [] });
  products = payload.products || [];
  sources = payload.sources || [];
  generatedAt = payload.generated_at || "";
  stockSubscriptions = loadStockSubscriptions();
  reconcileStockSubscriptions();
});
```

**Presentation grouping pattern** (lines 136-154):
```svelte
function groupBaseProducts(items) {
  const cards = new Map();
  items.forEach((product) => {
    const key = [
      product.brand || "Sin marca",
      product.diameter_mm || "Sin diametro",
      lineLabel(product),
      product.material || "Sin material",
      product.variant || "",
      product.color || "Sin color",
    ].join("||");
    if (!cards.has(key)) cards.set(key, { products: [] });
    cards.get(key).products.push(product);
  });
  return [...cards.values()].map((card) => {
    card.products.sort(comparePresentations);
    return card;
  });
}
```

**State mutation + autosave pattern** (lines 270-295):
```svelte
function toggleStockSubscription(product, offer) {
  const key = subscriptionKey(product, offer);
  const existing = stockSubscriptions.find((item) => item.key === key);
  if (existing) {
    stockSubscriptions = stockSubscriptions.filter((item) => item.key !== key);
    stockAlerts = stockAlerts.filter((item) => item.key !== key);
  } else {
    stockSubscriptions = [
      ...stockSubscriptions,
      {
        key,
        productId: product.id,
        sourceId: offer.source_id || offer.provider_name,
        productName: productBaseName(product),
        providerName: offer.provider_name,
        presentation: formatPresentation(product),
        subscribedAt: new Date().toISOString(),
        lastStockStatus: offer.stock_status || "unknown",
        lastStockQuantity: Number(offer.stock_quantity || 0),
        lastStockSignature: stockSignature(offer),
        acknowledgedAt: "",
      },
    ];
  }
  saveStockSubscriptions(stockSubscriptions);
}
```

**Reconciliation pattern** (lines 297-335):
```svelte
function reconcileStockSubscriptions() {
  const alerts = [];
  const nextSubscriptions = stockSubscriptions.map((subscription) => {
    const match = findSubscribedOffer(subscription);
    if (!match) return subscription;

    const { product, offer } = match;
    const signature = stockSignature(offer);
    const currentQuantity = Number(offer.stock_quantity || 0);
    const previousQuantity = Number(subscription.lastStockQuantity || 0);
    const cameBack = offer.stock_status === "in_stock" && subscription.lastStockStatus !== "in_stock";
    const increasedStock = offer.stock_status === "in_stock" && currentQuantity > previousQuantity;
    if (cameBack || increasedStock) {
      alerts.push({
        key: subscription.key,
        productName: productBaseName(product),
        providerName: offer.provider_name,
        quantity: currentQuantity,
        previousQuantity,
        href: `#${stockWatchTargetId(product, offer)}`,
      });
      return subscription;
    }

    return {
      ...subscription,
      productName: productBaseName(product),
      providerName: offer.provider_name,
      presentation: formatPresentation(product),
      lastStockStatus: offer.stock_status || "unknown",
      lastStockQuantity: currentQuantity,
      lastStockSignature: signature,
    };
  });

  stockSubscriptions = nextSubscriptions;
  stockAlerts = alerts;
  saveStockSubscriptions(nextSubscriptions);
}
```

**Presentation-row integration pattern** (lines 451-484):
```svelte
<div class="presentation-list">
  {#each card.products as presentation}
    <section class="presentation-row">
      <header><strong>{formatPresentation(presentation) || "Presentación sin dato"}</strong></header>
      <div class="offers">
        {#if (presentation.offers || []).length}
          {#each presentation.offers as offer}
            <div class="offer" id={stockWatchTargetId(presentation, offer)} title={providerTitle(offer)}>
              <div class="offer-main">
                <a href={`#${providerAnchorId(offer.source_id)}`} title={providerTitle(offer)}>{offer.provider_name}</a>
                <strong class={offer.stock_status === "in_stock" ? "stock-in" : "stock-out"}>{offer.stock_status === "in_stock" ? `${offer.stock_quantity} carretes` : "0"}</strong>
                <button
                  class="stock-watch-button"
                  class:active={isSubscribed(presentation, offer)}
                  type="button"
                  aria-pressed={isSubscribed(presentation, offer)}
                  aria-label={`${isSubscribed(presentation, offer) ? "Dejar de seguir cambios de stock" : "Seguir cambios de stock"} de ${productBaseName(presentation)} en ${offer.provider_name}`}
                  title={isSubscribed(presentation, offer) ? "Dejar de seguir cambios de stock" : "Avisarme si sube o vuelve el stock"}
                  on:click={() => toggleStockSubscription(presentation, offer)}
                >
```

Planner application:
- Add quote-list imports beside stock subscription imports.
- Load quote list only after `stock.json` is loaded so reconciliation can use current `products`.
- Put the add control inside each `.presentation-row`, not inside each `.offer`.
- Keep stock-watch provider-specific code intact; quote-list state is presentation-specific and provider-neutral.

---

### `src/lib/quoteList.js` (utility, localStorage + transform)

**Analog:** `src/lib/stockSubscriptions.js`

**Storage key + key builder pattern** (lines 1-12):
```javascript
export const stockSubscriptionsStorageKey = "centraldefilamentos.stockSubscriptions.v1";

export function subscriptionKey(product, offer) {
  return [product?.id || "", offer?.source_id || offer?.provider_name || ""].join("::");
}

export function stockSignature(offer) {
  return [
    offer?.stock_status || "unknown",
    Number(offer?.stock_quantity || 0),
    offer?.updated_at || "",
  ].join(":");
}
```

**Safe load/save pattern** (lines 15-27):
```javascript
export function loadStockSubscriptions() {
  if (typeof localStorage === "undefined") return [];
  try {
    return normalizeSubscriptions(JSON.parse(localStorage.getItem(stockSubscriptionsStorageKey) || "[]"));
  } catch {
    return [];
  }
}

export function saveStockSubscriptions(items) {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(stockSubscriptionsStorageKey, JSON.stringify(normalizeSubscriptions(items)));
}
```

**Normalization/dedupe pattern** (lines 29-54):
```javascript
export function normalizeSubscriptions(payload) {
  const rawItems = Array.isArray(payload) ? payload : payload?.items;
  if (!Array.isArray(rawItems)) return [];

  const seen = new Set();
  return rawItems
    .filter((item) => item && typeof item.key === "string" && item.key.includes("::"))
    .filter((item) => {
      if (seen.has(item.key)) return false;
      seen.add(item.key);
      return true;
    })
    .map((item) => ({
      key: item.key,
      productId: item.productId || item.product_id || item.key.split("::")[0],
      sourceId: item.sourceId || item.source_id || item.key.split("::")[1],
      productName: item.productName || item.product_name || "Filamento esperado",
      providerName: item.providerName || item.provider_name || "Proveedor",
      presentation: item.presentation || "",
      subscribedAt: item.subscribedAt || item.subscribed_at || new Date().toISOString(),
      lastStockStatus: item.lastStockStatus || item.last_stock_status || "unknown",
      lastStockQuantity: Number(item.lastStockQuantity ?? item.last_stock_quantity ?? 0),
      lastStockSignature: item.lastStockSignature || item.last_stock_signature || "",
      acknowledgedAt: item.acknowledgedAt || item.acknowledged_at || "",
    }));
}
```

Planner application:
- Use a focused key such as `centraldefilamentos.quoteList.v1`.
- Unlike the analog, expose storage write failures because the UI contract requires a warning.
- Store a schema/version field and reject incompatible payloads.
- Use `product.id` as the reconciliation key; SKU/EAN/article code are snapshot fields only.
- Export named helpers: `loadQuoteList`, `saveQuoteList`, `normalizeQuoteList`, `snapshotQuoteItem`, `reconcileQuoteList`, `clampQuoteQuantity`, and `quoteQuantityLabel`.

---

### `src/components/QuoteListPanel.svelte` (component, event-driven)

**Analog:** `src/components/SiteHeader.svelte`

**Props, derived copy, callback pattern** (lines 4-30):
```svelte
export let active = "catalog";
export let updatedAt = "";
export let subtitle = "";
export let stockAlerts = [];
export let onDismissStockAlerts = () => {};

$: updatedLabel = updatedAt ? `Actualizado: ${formatDate(updatedAt)}` : subtitle;
$: firstStockAlert = stockAlerts[0];
$: stockAlertDetail = stockAlerts.length === 1
  ? stockAlertLabel(firstStockAlert)
  : firstStockAlert
    ? `${stockAlertLabel(firstStockAlert)} y ${stockAlerts.length - 1} más`
    : "";

function stockAlertLabel(alert) {
  if (!alert) return "";
  const stockChange = Number(alert.previousQuantity) < Number(alert.quantity)
    ? ` (${Number(alert.previousQuantity)} -> ${Number(alert.quantity)} carretes)`
    : "";
  return `${alert.productName} en ${alert.providerName}${stockChange}`;
}
```

**Live notice/callback pattern** (lines 50-58):
```svelte
{#if stockAlerts.length}
  <section class="stock-alert-banner" aria-live="polite">
    <div>
      <strong>Tus filamentos esperados volvieron</strong>
      <span>{stockAlertDetail}</span>
    </div>
    <a href={firstStockAlert.href}>Ver</a>
    <button type="button" on:click={onDismissStockAlerts}>Visto</button>
  </section>
{/if}
```

Planner application:
- Quote panel should receive items, settings, notices, and callbacks as props.
- Use `aria-live="polite"` for storage/reconciliation notices and count changes.
- Put locked copy below the title: `Usa esta lista...`, local-only notice, and non-commerce notice.

---

### `src/components/QuoteListDrawer.svelte` (component, event-driven)

**Analog:** `src/CatalogApp.svelte` image preview modal

**Window keydown + dialog shell pattern** (lines 498-507):
```svelte
<svelte:window on:keydown={handlePreviewKeydown} />

{#if preview && preview.modal}
  <div class="image-preview-backdrop" role="presentation" on:click={closePreviewBackdrop}>
    <div class="image-preview-modal" role="dialog" aria-modal="true" aria-label={preview.title}>
      <button class="image-preview-close" type="button" aria-label="Cerrar imagen ampliada" on:click={() => preview = null}>×</button>
      <img src={preview.src} alt={preview.title}>
      <strong>{preview.title}</strong>
      <span>{preview.meta}</span>
    </div>
  </div>
```

Planner application:
- Reuse the conditional render + backdrop click + close button + Escape key style.
- If using `aria-modal="true"`, add actual focus return/trap behavior; do not rely on ARIA alone.
- Drawer should be bottom sheet on mobile, not full-screen modal or side drawer.

---

### `src/components/QuoteListItem.svelte` (component, event-driven + transform display)

**Analog:** `src/components/SiteFooter.svelte`

**Imports, props, derived message pattern** (lines 1-7):
```svelte
import { formatDate, formatInteger, providerAnchorId, siteContactUrl, siteRepoUrl, sourceWhatsappUrl, stockDelta } from "../lib/shared.js";

export let sources = [];
export let contactContext = "";

$: message = `Hola, vi su stock publicado en Central de Filamentos.${contactContext ? ` Estoy buscando ${contactContext}.` : " Quería consultar disponibilidad y precio."}`;
```

**Compact action icons with accessible labels** (lines 80-101):
```svelte
<a href={sourceWhatsappUrl(source, message)} target="_blank" rel="noopener" aria-label={`Enviar WhatsApp a ${source.name}`} title="WhatsApp">
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19.2 6.2 16A8 8 0 1 1 9 18.6L5 19.2Z"/><path d="M9.2 8.8c.2-.5.4-.5.7-.5h.5c.2 0 .4.1.5.4l.8 1.7c.1.3.1.5-.1.7l-.4.5c.7 1.2 1.7 2.1 3 2.8l.6-.5c.2-.2.4-.2.7-.1l1.6.8c.3.1.4.3.4.6v.4c0 .4-.2.7-.6.9-.6.3-1.4.4-2.4.1-2.9-.8-5.3-3.2-6-6-.2-.8-.1-1.4.2-1.8Z"/></svg>
  <span>WhatsApp</span>
</a>
```

Planner application:
- Keep item copy compact and Spanish/Argentina.
- Use existing shared display helpers from `src/lib/shared.js` for `productBaseName`, `formatPresentation`, `diameterLabel`, `lineLabel`, and swatch helpers.
- Use a non-cart remove icon/button with a clear `aria-label`.

---

### `src/components/QuoteQuantityControl.svelte` (component, event-driven)

**Analog:** `src/components/QuickLines.svelte`

**Props + local DOM state + reactive update pattern** (lines 1-24):
```svelte
import { onMount, tick } from "svelte";
import { lineMeta, quickLineHint, quickLineLabel, quickLineValues } from "../lib/shared.js";

export let available = [];
export let targetSelector = ".group-section";
export let help = "";
export let id = "";

let scrollNode;
let showScrollCue = false;

$: availableSet = new Set(available);
$: visibleLines = quickLineValues.filter((line) => availableSet.has(line));
$: {
  visibleLines;
  tick().then(updateScrollCue);
}

onMount(() => {
  updateScrollCue();
  window.addEventListener("resize", updateScrollCue);
  return () => window.removeEventListener("resize", updateScrollCue);
});
```

**Button event pattern** (lines 46-55):
```svelte
<div bind:this={scrollNode} id={id || undefined} class="quick-lines" on:scroll={updateScrollCue}>
  {#each visibleLines as line}
    {@const tone = lineMeta[line]?.quickTone || "default"}
    <button class={`quick-line quick-line-${tone}`} type="button" data-line={line} title={quickLineHint(line)} aria-label={`${quickLineLabel(line)}. ${quickLineHint(line)}`} on:click={() => scrollToLine(line)}>
      <span>{quickLineLabel(line)}</span>
    </button>
  {/each}
</div>
{#if showScrollCue}
  <span class="quick-lines-cue" aria-hidden="true"></span>
{/if}
```

Planner application:
- Quantity controls should be stable-width buttons/number input with callbacks passed from parent.
- Use Svelte `on:click`/`on:input` style to match current project convention.
- Clamp whole integers in helper code, then emit/update parent state.

---

### `src/styles/global.css` (config, responsive layout)

**Analog:** `src/styles/global.css`

**Base shell/grid pattern** (lines 44-58):
```css
.shell {
  width: min(1180px, calc(100% - 24px));
  margin: 0 auto;
  padding: 18px 0 28px;
}

.site-header {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) auto minmax(190px, auto);
  align-items: center;
  gap: 18px;
  margin-bottom: 18px;
  padding: 12px 14px;
  border: 1px solid color-mix(in srgb, var(--line) 84%, transparent);
  border-radius: 22px;
```

**Button/control token pattern** (lines 141-173):
```css
.soft-button,
select,
input {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text);
}

.nav-link,
.soft-button {
  padding: 9px 12px;
  font: inherit;
  cursor: pointer;
}

.nav-link.active,
.soft-button.active,
.soft-button:hover {
  background: var(--text);
  color: white;
}
```

**Product/presentation layout pattern** (lines 517-532, 794-817):
```css
.group-products {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  align-items: start;
  gap: 10px;
}

.product-row {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr);
  gap: 10px;
  padding: 10px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 8px;
  min-width: 0;
}

.presentation-row {
  display: grid;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px solid var(--line);
}

.presentation-row header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--muted);
  font-size: 12px;
}
```

**Icon button pattern** (lines 862-899):
```css
.stock-watch-button {
  display: inline-grid;
  place-items: center;
  align-self: center;
  width: 16px;
  height: 16px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: color-mix(in srgb, var(--muted) 78%, var(--surface));
  cursor: pointer;
  transition: transform 140ms ease, background 140ms ease, color 140ms ease, border-color 140ms ease;
}

.stock-watch-button svg {
  width: 12px;
  height: 12px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
```

**Responsive breakpoint pattern** (lines 1728-1779, 2011-2065):
```css
@media (max-width: 820px) {
  :root {
    --quick-lines-height: 48px;
  }

  .site-header {
    grid-template-columns: 1fr;
    gap: 10px;
    padding: 12px;
    border-radius: 18px;
  }

  .filters {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 520px) {
  .shell {
    width: min(100% - 16px, 1180px);
  }

  .filters {
    grid-template-columns: 1fr;
    position: static;
  }

  .product-row {
    grid-template-columns: 56px minmax(0, 1fr);
  }

  .group-products {
    grid-template-columns: 1fr;
  }
}
```

Planner application:
- Add quote list layout classes in this file, not component-scoped CSS.
- Desktop side panel should appear only when the quote list has items; use a parent layout class from `CatalogApp`.
- Mobile drawer/floating button should key off `max-width: 820px`; compact quantity controls should wrap at `max-width: 520px`.
- Keep border radius at 8px for cards/controls unless matching an existing special surface.

---

### `tests/test_frontend_assets.py` (test, source invariant checks)

**Analog:** `tests/test_frontend_assets.py`

**Source aggregation pattern** (lines 42-49):
```python
def test_catalog_svelte_fetches_json_and_supports_required_filters():
    view = (SRC / "CatalogApp.svelte").read_text(encoding="utf-8")
    shared = (SRC / "lib" / "shared.js").read_text(encoding="utf-8")
    footer = (SRC / "components" / "SiteFooter.svelte").read_text(encoding="utf-8")
    site_header = (SRC / "components" / "SiteHeader.svelte").read_text(encoding="utf-8")
    quick_lines = (SRC / "components" / "QuickLines.svelte").read_text(encoding="utf-8")
    subscriptions = (SRC / "lib" / "stockSubscriptions.js").read_text(encoding="utf-8")
    js = view + shared + footer + site_header + quick_lines + subscriptions
```

**Positive/negative invariant pattern** (lines 130-151):
```python
assert "sin stock online registrado" in js
assert "offer-main" in js
assert "providerTitle" in js
assert "Sin cantidad" in js
assert "stockSubscriptionsStorageKey" in js
assert "centraldefilamentos.stockSubscriptions.v1" in js
assert "loadStockSubscriptions" in js
assert "saveStockSubscriptions" in js
assert "subscriptionKey" in js
assert "stockSignature" in js
assert "stockAlerts" in js
assert "increasedStock" in js
assert "currentQuantity > previousQuantity" in js
assert "previousQuantity" in js
assert "stockAlertLabel" in js
assert "Tus filamentos esperados volvieron" in site_header
assert "stock-alert-banner" in site_header
assert "stock-watch-button" in js
assert "Avisarme si sube o vuelve el stock" in js
assert "Seguir cambios de stock" in js
assert "Dejar de seguir cambios de stock" in js
assert "reconcileStockSubscriptions" in js
```

**CSS invariant pattern** (lines 278-308):
```python
def test_styles_are_compact_and_responsive():
    css = (SRC / "styles" / "global.css").read_text(encoding="utf-8")

    assert "@media" in css
    assert "position: sticky" in css
    assert "grid-template-columns" in css
    assert "border-radius: 8px" in css
    assert ".group-section" in css
    assert ".group-section.quick-target" in css
    assert ".group-heading" in css
    assert ".quick-line::before" in css
    assert ".quick-lines-shell" in css
    assert ".quick-lines-cue" in css
    assert "quick-lines-cue-nudge" in css
    assert ".quick-line-abs" in css
    assert ".quick-line-boutique" in css
    assert ".quick-line-wood" in css
    assert ".quick-line-nylon" in css
    assert "flex-wrap: nowrap" in css
    assert "scroll-snap-type: x proximity" in css
    assert "-webkit-overflow-scrolling: touch" in css
    assert "scrollbar-width: none" in css
    assert "top: var(--quick-lines-height)" in css
    assert "scroll-margin-top" in css
    assert "repeat(auto-fit, minmax(320px, 1fr))" in css
    assert ".offer-main" in css
    assert ".stock-alert-banner" in css
    assert ".stock-watch-button" in css
    assert ".offer:target" in css
    assert ".presentation-list" in css
    assert ".presentation-row" in css
```

Planner application:
- Extend source-invariant tests for `quoteListStorageKey`, schema/version handling, local-only/no-commerce copy, `+1`, `+6`, `+12`, `carrete`, missing badges, panel/drawer/floating classes, and absence of cart/checkout language.
- Keep tests as Python source inspections unless the planner introduces a JS test runner.
- Windows command: `python -m pytest -v tests/test_frontend_assets.py --basetemp C:\tmp\pytest-centraldefilamentos`.

## Shared Patterns

### Static JSON Fetching

**Source:** `src/lib/shared.js` lines 60-70
**Apply to:** `src/CatalogApp.svelte`
```javascript
export async function fetchJson(path, fallback = {}, options = {}) {
  try {
    const url = new URL(dataUrl(path), window.location.origin);
    if (options.noCache) url.searchParams.set("v", String(Date.now()));
    const response = await fetch(url, { cache: options.noCache ? "no-store" : "default" });
    if (!response.ok) return fallback;
    return await response.json();
  } catch {
    return fallback;
  }
}
```

### Product Display Helpers

**Source:** `src/lib/shared.js` lines 91-145, 191-202
**Apply to:** `src/lib/quoteList.js`, `src/CatalogApp.svelte`, `src/components/QuoteListItem.svelte`
```javascript
export function formatWeightLabel(weightG) {
  if (!weightG) return "";
  return `${Number(weightG) / 1000} kg`;
}

export function lineLabel(product) {
  if (isSamplerProduct(product)) return "Sampler / lápiz 3D";
  if (!product.variant && product.material === "PLA") return "PLA Standard";
  return product.variant || product.material || "Sin clasificar";
}

export function diameterLabel(product) {
  return product.diameter_mm ? `${product.diameter_mm} mm` : "Sin diametro";
}

export function formatPresentation(product) {
  const weight = formatWeightLabel(product.weight_g);
  if (weight) return weight;
  const samplerLength = samplerLengthLabel(product);
  if (samplerLength) return `Sampler ${samplerLength}`;
  return "";
}

export function productBaseName(product) {
  const presentation = formatWeightLabel(product.weight_g);
  if (!presentation) return product.display_name;
  return product.display_name.replace(` ${presentation}`, "").replace(/\s+/g, " ").trim();
}

export function comparePresentations(left, right) {
  return presentationRank(left) - presentationRank(right) || left.display_name.localeCompare(right.display_name, "es-AR");
}
```

### Color and Badge Display

**Source:** `src/lib/shared.js` lines 207-232
**Apply to:** `src/components/QuoteListItem.svelte`
```javascript
export function colorSwatchStyle(product) {
  const color = product.color || "";
  const folded = foldText(color);
  const variant = foldText(product.variant || "");
  if (folded.includes("KIT") || folded.includes("TUTTI") || folded.includes("SERIE LIMITADA")) {
    return "background: linear-gradient(135deg, #e53935, #fdd835 28%, #43a047 52%, #1e88e5 76%, #8e24aa);";
  }
  if (folded.includes("CLEAR") || folded.includes("CRISTAL") || folded.includes("TRANSPARENTE") || folded.includes("NATURAL")) {
    return `background: ${transparentSwatch(folded)};`;
  }
  if (folded.includes("FLUO") || folded.includes("UV GLOW")) {
    return `background: ${fluorescentSwatch(folded)};`;
  }
  if (variant.includes("ASTRA") || folded.includes("ASTRA") || ["DARK", "JADE", "NEBULA", "NOCHE", "NOVA", "ROBY"].includes(folded)) {
    return `background: ${glitterSwatch(baseColorFor(folded))};`;
  }
  return `background: ${baseColorFor(folded)};`;
}

export function colorSwatchLabel(color) {
  if (!color) return "";
  return color.split(/\s+/).slice(0, 2).map((word) => word[0]).join("").toUpperCase();
}
```

### No-Commerce Copy Boundary

**Source:** `01-CONTEXT.md` decisions D-26 through D-29 and `01-UI-SPEC.md` Copywriting Contract
**Apply to:** all quote-list components and tests
```text
Feature title: Lista de cotizacion
Main notice: Usa esta lista para planificar tu compra. Confirma stock y precio final con cada proveedor.
Local-only notice: Se guarda solo en este navegador/dispositivo. No se sincroniza con otra PC o navegador.
Non-commerce notice: StockCentral no vende productos ni procesa pedidos.
```

### Quantity Rules

**Source:** `01-CONTEXT.md` decisions D-18 through D-21
**Apply to:** `src/lib/quoteList.js`, `QuoteQuantityControl.svelte`, `QuoteListItem.svelte`, tests
```text
Use carrete/carretes for quote-list quantity.
Whole integers only.
Minimum is 1.
Decrement below 1 removes the item.
Extended controls: - / editable number / + / +6 / +12.
```

## No Analog Found

No files are without a usable codebase analog. The drawer needs accessibility care beyond the existing image preview modal, but `CatalogApp.svelte` still provides the closest local shell pattern.

## Metadata

**Analog search scope:** `src/CatalogApp.svelte`, `src/lib/*.js`, `src/components/*.svelte`, `src/styles/global.css`, `tests/test_frontend_assets.py`, phase artifacts in `.planning/phases/01-quote-list-foundation/`
**Files scanned:** 12
**Pattern extraction date:** 2026-06-19
