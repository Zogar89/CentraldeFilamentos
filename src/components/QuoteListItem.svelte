<script>
  import { quoteQuantityLabel } from "../lib/quoteList.js";
  import QuoteQuantityControl from "./QuoteQuantityControl.svelte";

  export let item;
  export let showControls = false;
  export let onChange = () => {};
  export let onRemove = () => {};

  $: code = item?.articleCode || item?.sku || item?.ean || item?.originalName || "";
  $: metadata = [
    item?.brand || "sin marca",
    item?.line || item?.material || "confirmar dato",
    item?.color || "confirmar dato",
  ];
  $: missingBadges = [
    code ? "" : "sin codigo",
    item?.diameterMm ? "" : "sin diametro",
    item?.presentation ? "" : "sin presentacion",
    item?.line || item?.material ? "" : "confirmar dato",
    item?.hasOnlineStock ? "" : "confirmar stock",
  ].filter(Boolean);
</script>

<article class="quote-list-item">
  <div class="quote-list-item-main">
    <div class="quote-list-item-title">
      <strong>{item.productName || item.displayName || "Filamento"}</strong>
      <button type="button" class="quote-list-remove" aria-label={`Quitar ${item.productName || "filamento"} de la lista`} title="Quitar" on:click={onRemove}>×</button>
    </div>
    <span>{metadata.filter(Boolean).join(" · ")}</span>
    <small>{[item?.diameterMm ? `${item.diameterMm} mm` : "", item?.presentation, code].filter(Boolean).join(" · ")}</small>
    <div class="quote-list-badges" aria-label="Datos a confirmar">
      {#each missingBadges as badge}
        <em class="quote-list-badge">{badge}</em>
      {/each}
    </div>
  </div>

  <div class="quote-list-item-quantity">
    <strong>{quoteQuantityLabel(item.quantity)}</strong>
    {#if showControls}
      <QuoteQuantityControl quantity={item.quantity} {onChange} {onRemove} />
    {/if}
  </div>
</article>
