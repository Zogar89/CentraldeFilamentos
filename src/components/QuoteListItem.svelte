<script>
  import {
    quoteItemCode,
    quoteItemMissingBadges,
    quoteQuantityLabel,
  } from "../lib/quoteList.js";
  import { colorSwatchLabel, colorSwatchStyle, dataUrl } from "../lib/shared.js";
  import QuoteQuantityControl from "./QuoteQuantityControl.svelte";

  export let item;
  export let showControls = false;
  export let onChange = () => {};
  export let onRemove = () => {};

  $: code = quoteItemCode(item);
  $: metadata = [
    item?.brand || "sin marca",
    item?.line || item?.material || "confirmar dato",
    item?.color || "confirmar dato",
  ];
  $: missingBadges = quoteItemMissingBadges(item);
  $: dozenCount = Number(item?.quantity || 0) >= 12
    ? new Intl.NumberFormat("es-AR", { maximumFractionDigits: 1 }).format(Number(item.quantity) / 12)
    : "";
</script>

<article class="quote-list-item">
  <div class="quote-list-item-visual">
    {#if item?.thumbnailUrl || item?.imageUrl}
      <img src={dataUrl(item.thumbnailUrl || item.imageUrl)} alt="" loading="lazy" decoding="async">
    {:else}
      <span class="quote-list-color" style={colorSwatchStyle(item)} aria-label={item?.color || "Color a confirmar"}>
        {colorSwatchLabel(item?.color) || "?"}
      </span>
    {/if}
  </div>
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
    {#if dozenCount}
      <small class="quote-list-item-dozens">{dozenCount} {dozenCount === "1" ? "docena" : "docenas"}</small>
    {/if}
    {#if showControls}
      <QuoteQuantityControl quantity={item.quantity} {onChange} {onRemove} />
    {/if}
  </div>
</article>
