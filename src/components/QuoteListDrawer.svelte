<script>
  import { onDestroy, tick } from "svelte";
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

  let dialogElement;
  let closeButton;
  let previouslyFocused;
  let inertedElements = [];
  let wasOpen = false;

  $: if (open && !wasOpen) {
    wasOpen = true;
    activateDrawer();
  } else if (!open && wasOpen) {
    wasOpen = false;
    deactivateDrawer();
  }

  onDestroy(deactivateDrawer);

  async function activateDrawer() {
    previouslyFocused = document.activeElement;
    await tick();
    const backdrop = dialogElement?.parentElement;
    const appRoot = backdrop?.parentElement;
    inertedElements = appRoot
      ? [...appRoot.children]
        .filter((element) => element !== backdrop)
        .map((element) => ({ element, wasInert: element.inert }))
      : [];
    inertedElements.forEach(({ element }) => element.inert = true);
    closeButton?.focus();
  }

  function deactivateDrawer() {
    inertedElements.forEach(({ element, wasInert }) => element.inert = wasInert);
    inertedElements = [];
    if (previouslyFocused?.isConnected) previouslyFocused.focus();
    previouslyFocused = null;
  }

  function focusableElements() {
    if (!dialogElement) return [];
    return [...dialogElement.querySelectorAll(
      'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
    )];
  }

  function handleKeydown(event) {
    handleQuoteDrawerKeydown(event);
    if (!open || event.defaultPrevented) return;
    if (event.key === "Escape") {
      event.preventDefault();
      onClose();
      return;
    }
    if (event.key !== "Tab") return;

    const focusable = focusableElements();
    if (!focusable.length) {
      event.preventDefault();
      dialogElement.focus();
      return;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  function closeBackdrop(event) {
    if (event.target === event.currentTarget) onClose();
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if open}
  <div class="quote-list-backdrop" role="presentation" on:click={closeBackdrop}>
    <div class="quote-list-drawer" role="dialog" aria-modal="true" aria-label="Lista de cotizacion" tabindex="-1" bind:this={dialogElement}>
      <button class="quote-list-drawer-close" type="button" aria-label="Cerrar lista de cotizacion" on:click={onClose} bind:this={closeButton}>×</button>
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
