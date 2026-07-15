<script>
  import { buildColorMap, groupColorFamilies, sortPerceptually } from "../lib/colorPicker.js";

  export let groups = [];
  export let view = "continuous";
  export let selectedIds = [];
  export let onSelect = () => {};

  $: continuousGroups = sortPerceptually(groups);
  $: familyGroups = [...groupColorFamilies(groups)];
  $: mapGroups = buildColorMap(groups);

  function tooltip(group) {
    return `${group.brand} · ${group.line} · ${group.name} · ${group.hex} · ${group.inStock ? "con stock" : "sin stock"}`;
  }
</script>

{#snippet tile(group)}
  <button
    type="button"
    class:without-stock={!group.inStock}
    class="color-picker-tile"
    style={`--picker-color: ${group.hex}`}
    aria-label={tooltip(group)}
    aria-pressed={selectedIds.includes(group.id)}
    data-tooltip={tooltip(group)}
    on:click={() => onSelect(group)}
  >
    <span class="sr-only">{group.name}</span>
    {#if !group.inStock}<span class="color-picker-stock-mark" aria-hidden="true">×</span>{/if}
  </button>
{/snippet}

{#if view === "continuous"}
  <div class="color-picker-palette color-picker-palette-continuous" aria-label="Paleta continua de colores PLA">
    {#each continuousGroups as group (group.id)}{@render tile(group)}{/each}
  </div>
{:else if view === "families"}
  <div class="color-picker-palette color-picker-palette-families">
    {#each familyGroups as [family, items] (family)}
      <section class="color-picker-family" aria-labelledby={`family-${family}`}>
        <h2 id={`family-${family}`}>{family}</h2>
        <div class="color-picker-family-grid">
          {#each items as group (group.id)}{@render tile(group)}{/each}
        </div>
      </section>
    {/each}
  </div>
{:else if view === "map"}
  <div class="color-picker-map-scroll">
    <div class="color-picker-map">
      <span class="color-picker-map-y">Luminosidad ↑</span>
      <span class="color-picker-map-x">Tono →</span>
      {#each mapGroups as group (group.id)}
        <div class="color-picker-map-cell" style={`grid-column: ${group.mapColumn}; grid-row: ${group.mapRow}`}>
          {@render tile(group)}
        </div>
      {/each}
    </div>
  </div>
{/if}
