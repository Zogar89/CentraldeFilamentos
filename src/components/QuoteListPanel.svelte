<script>
  import { quoteQuantityLabel } from "../lib/quoteList.js";
  import QuoteListItem from "./QuoteListItem.svelte";

  export let items = [];
  export let showQuickControls = false;
  export let storageWarning = "";
  export let reconcileNotice = "";
  export let onToggleControls = () => {};
  export let onSetQuantity = () => {};
  export let onRemoveItem = () => {};
  export let onClearList = () => {};

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
    {#if reconcileNotice}
      <p class="quote-list-warning" aria-live="polite">{reconcileNotice}</p>
    {/if}
  </div>

  <div class="quote-list-actions">
    <button type="button" class="quote-list-toggle" aria-pressed={showQuickControls} on:click={onToggleControls}>
      {showQuickControls ? "Ocultar controles rapidos" : "Controles rapidos"}
    </button>
    <button type="button" class="quote-list-clear" on:click={onClearList}>Limpiar lista</button>
  </div>

  <div class="quote-list-items">
    {#each items as item}
      <QuoteListItem
        {item}
        showControls={showQuickControls}
        onChange={(quantity) => onSetQuantity(item.productId, quantity)}
        onRemove={() => onRemoveItem(item.productId)}
      />
    {/each}
  </div>
</aside>
