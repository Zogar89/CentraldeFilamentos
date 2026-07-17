<script context="module">
  let quotePanelInstance = 0;
</script>

<script>
  import { onMount } from "svelte";
  import { flip } from "svelte/animate";
  import { fly } from "svelte/transition";
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

  let activeView = "list";
  let selectedSourceId = "";
  let motionDuration = 180;
  const panelInstanceId = `quote-panel-${++quotePanelInstance}`;
  const workflowViews = ["list", "providers", "send"];
  const workflowLabels = { list: "Lista", providers: "Proveedores", send: "Enviar" };

  function handleWorkflowTabKeydown(event, index) {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    let nextIndex = index;
    if (event.key === "ArrowLeft") nextIndex = (index - 1 + workflowViews.length) % workflowViews.length;
    if (event.key === "ArrowRight") nextIndex = (index + 1) % workflowViews.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = workflowViews.length - 1;
    activeView = workflowViews[nextIndex];
    event.currentTarget.parentElement?.querySelectorAll('[role="tab"]')[nextIndex]?.focus();
  }

  onMount(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) motionDuration = 0;
  });

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
      <strong class="quote-list-count">{itemCount ? quoteQuantityLabel(itemCount) : "0 unidades"}</strong>
      {#if dozenCount}
        <small title="Los carretes suelen venir agrupados en cajas de 12 unidades.">{dozenCount} {dozenCount === "1" ? "docena" : "docenas"}</small>
      {/if}
    </div>
  </header>

  <div class="quote-workflow-tabs" role="tablist" aria-label="Etapas de la cotizacion">
    {#each workflowViews as view, index}
      <button
        type="button"
        role="tab"
        id={`${panelInstanceId}-tab-${view}`}
        aria-controls={`${panelInstanceId}-view-${view}`}
        aria-selected={activeView === view}
        tabindex={activeView === view ? 0 : -1}
        class:active={activeView === view}
        on:click={() => activeView = view}
        on:keydown={(event) => handleWorkflowTabKeydown(event, index)}
      >{workflowLabels[view]}</button>
    {/each}
  </div>

  <div class="quote-list-notices">
    <details class="quote-list-info">
      <summary><span aria-hidden="true">i</span> Guardada en este dispositivo</summary>
      <p>Usala para planificar y confirma stock y precio con el proveedor. No se sincroniza con otra PC. StockCentral no vende ni procesa pedidos.</p>
    </details>
    {#if storageWarning}
      <p class="quote-list-warning" aria-live="polite">{storageWarning}</p>
    {/if}
    {#if reconcileNotice}
      <p class="quote-list-warning" aria-live="polite">{reconcileNotice}</p>
    {/if}
  </div>

  {#if activeView === "list"}
    <div class="quote-workflow-view" role="tabpanel" id={`${panelInstanceId}-view-list`} aria-labelledby={`${panelInstanceId}-tab-list`}>
      <div class="quote-list-toolbar">
        <button
          type="button"
          class="quote-list-toggle"
          aria-pressed={showQuickControls}
          aria-label={showQuickControls ? "Ocultar controles rapidos" : "Controles rapidos"}
          on:click={onToggleControls}
        >
          {showQuickControls ? "Ocultar cantidades" : "Editar cantidades"}
        </button>
        <details class="quote-list-menu">
          <summary>Acciones</summary>
          <div>
            <button type="button" on:click={onExportList}>Exportar JSON</button>
            <button type="button" on:click={onImportList}>Importar lista</button>
            <button type="button" class="danger" on:click={onClearList}>Limpiar lista</button>
          </div>
        </details>
      </div>

      {#if items.length}
        <div class="quote-list-items">
          {#each items as item (item.productId)}
            <div class="quote-list-item-motion" animate:flip={{ duration: motionDuration }} in:fly={{ y: 6, duration: motionDuration }} out:fly={{ y: -4, duration: motionDuration ? 150 : 0 }}>
              <QuoteListItem
                {item}
                showControls={showQuickControls}
                onChange={(quantity) => onSetQuantity(item.productId, quantity)}
                onRemove={() => onRemoveItem(item.productId)}
              />
            </div>
          {/each}
        </div>
      {:else}
        <div class="quote-list-empty">
          <strong>Tu lista está vacía</strong>
          <p>Agregá filamentos desde los resultados para comparar qué proveedor cubre mejor tu consulta.</p>
        </div>
      {/if}

      <button type="button" class="quote-workflow-primary" disabled={!items.length} on:click={() => activeView = "providers"}>Comparar proveedores</button>
    </div>
  {:else if activeView === "providers"}
    <div class="quote-workflow-view" role="tabpanel" id={`${panelInstanceId}-view-providers`} aria-labelledby={`${panelInstanceId}-tab-providers`}>
      <QuoteProviderCoverage mode="coverage" {items} {products} {sources} bind:selectedSourceId />
      <div class="quote-workflow-footer">
        <button type="button" on:click={() => activeView = "list"}>Volver a la lista</button>
        <button type="button" class="quote-workflow-primary" on:click={() => activeView = "send"}>Preparar consulta</button>
      </div>
    </div>
  {:else}
    <div class="quote-workflow-view" role="tabpanel" id={`${panelInstanceId}-view-send`} aria-labelledby={`${panelInstanceId}-tab-send`}>
      <QuoteProviderCoverage mode="send" {items} {products} {sources} bind:selectedSourceId />
      <div class="quote-workflow-footer">
        <button type="button" on:click={() => activeView = "providers"}>Volver a proveedores</button>
      </div>
    </div>
  {/if}
</aside>
