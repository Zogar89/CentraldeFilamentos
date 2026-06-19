<script>
  import { quoteQuantityLabel } from "../lib/quoteList.js";
  import QuoteListItem from "./QuoteListItem.svelte";
  import QuoteProviderCoverage from "./QuoteProviderCoverage.svelte";

  export let items = [];
  export let products = [];
  export let sources = [];
  export let showQuickControls = false;
  export let storageWarning = "";
  export let reconcileNotice = "";
  export let onToggleControls = () => {};
  export let onSetQuantity = () => {};
  export let onRemoveItem = () => {};
  export let onClearList = () => {};
  export let onExportList = () => {};
  export let onImportList = () => {};

  $: itemCount = items.reduce((total, item) => total + Number(item.quantity || 0), 0);
  $: dozenCount = itemCount >= 12
    ? new Intl.NumberFormat("es-AR", { maximumFractionDigits: 1 }).format(itemCount / 12)
    : "";
</script>

<aside class="quote-list-panel" aria-label="Lista de cotizacion">
  <header class="quote-list-header" aria-live="polite">
    <div>
      <h2>Lista de cotizacion</h2>
    </div>
    <div class="quote-list-total">
      <strong class="quote-list-count">{quoteQuantityLabel(itemCount)}</strong>
      {#if dozenCount}
        <small title="Los carretes suelen venir agrupados en cajas de 12 unidades.">{dozenCount} {dozenCount === "1" ? "docena" : "docenas"}</small>
      {/if}
    </div>
  </header>

  <div class="quote-list-notices">
    <details class="quote-list-info">
      <summary><span aria-hidden="true">i</span> Guardada en este dispositivo</summary>
      <p>Usala para planificar y confirma stock y precio con el proveedor. No se sincroniza con otra PC. StockCentral no vende ni procesa pedidos.</p>
      <div class="quote-portability-actions">
        <button type="button" on:click={onExportList}>Exportar JSON</button>
        <button type="button" on:click={onImportList}>Importar lista</button>
      </div>
    </details>
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

  <QuoteProviderCoverage {items} {products} {sources} />
</aside>
