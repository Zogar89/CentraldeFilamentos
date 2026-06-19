<script>
  import QuoteListPanel from "./QuoteListPanel.svelte";

  export let open = false;
  export let items = [];
  export let showQuickControls = false;
  export let storageWarning = "";
  export let reconcileNotice = "";
  export let onClose = () => {};
  export let onToggleControls = () => {};
  export let onSetQuantity = () => {};
  export let onRemoveItem = () => {};
  export let onClearList = () => {};
  export let handleQuoteDrawerKeydown = () => {};

  function closeBackdrop(event) {
    if (event.target === event.currentTarget) onClose();
  }
</script>

<svelte:window on:keydown={handleQuoteDrawerKeydown} />

{#if open}
  <div class="quote-list-backdrop" role="presentation" on:click={closeBackdrop}>
    <div class="quote-list-drawer" role="dialog" aria-label="Lista de cotizacion">
      <button class="quote-list-drawer-close" type="button" aria-label="Cerrar lista de cotizacion" on:click={onClose}>×</button>
      <QuoteListPanel
        {items}
        {showQuickControls}
        {storageWarning}
        {reconcileNotice}
        {onToggleControls}
        {onSetQuantity}
        {onRemoveItem}
        {onClearList}
      />
    </div>
  </div>
{/if}
