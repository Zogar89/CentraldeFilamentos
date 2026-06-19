<script>
  import { quoteQuantityLabel } from "../lib/quoteList.js";

  export let items = [];
  export let storageWarning = "";

  $: itemCount = items.reduce((total, item) => total + Number(item.quantity || 0), 0);
</script>

<aside class="quote-list-panel" aria-label="Lista de cotizacion">
  <header class="quote-list-header" aria-live="polite">
    <div>
      <span class="quote-list-kicker">Herramienta local</span>
      <h2>Lista de cotizacion</h2>
    </div>
    <strong class="quote-list-count">{quoteQuantityLabel(itemCount)}</strong>
  </header>

  <div class="quote-list-notices">
    <p>Usa esta lista para planificar tu compra. Confirma stock y precio final con cada proveedor.</p>
    <p>Se guarda solo en este navegador/dispositivo. No se sincroniza con otra PC o navegador.</p>
    <p>StockCentral no vende productos ni procesa pedidos.</p>
    {#if storageWarning}
      <p class="quote-list-warning" aria-live="polite">{storageWarning}</p>
    {/if}
  </div>

  <div class="quote-list-items">
    {#each items as item}
      <article class="quote-list-item">
        <div>
          <strong>{item.productName}</strong>
          <span>{[item.brand, item.line, item.color].filter(Boolean).join(" · ")}</span>
          <small>{[item.diameterMm ? `${item.diameterMm} mm` : "sin diametro", item.presentation || "sin presentacion", item.sku || item.ean || item.articleCode || "sin codigo"].join(" · ")}</small>
          {#if !item.hasOnlineStock}
            <em>confirmar stock</em>
          {/if}
        </div>
        <strong>{quoteQuantityLabel(item.quantity)}</strong>
      </article>
    {/each}
  </div>
</aside>
