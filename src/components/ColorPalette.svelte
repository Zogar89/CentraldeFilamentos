<script>
  import { buildColorMap, groupColorFamilies, groupContinuousBands } from "../lib/colorPicker.js";

  export let groups = [];
  export let view = "continuous";
  export let selectedIds = [];
  export let onSelect = () => {};

  let activeTooltip = null;

  $: continuousBands = groupContinuousBands(groups);
  $: familyGroups = [...groupColorFamilies(groups)];
  $: mapGroups = buildColorMap(groups);

  function continuousBandLabel(band) {
    return {
      intense: "Rueda cromática intensa",
      muted: "Claros y apagados",
      earth: "Tierras y marrones",
      neutral: "Neutros",
    }[band] || band;
  }

  function tooltip(group) {
    return `${group.brand} · ${group.line} · ${group.name} · ${group.hex} · ${group.inStock ? "con stock" : "sin stock"}`;
  }

  function showTooltip(event, group) {
    const rect = event.currentTarget.getBoundingClientRect();
    const width = Math.min(240, window.innerWidth - 24);
    activeTooltip = {
      text: tooltip(group),
      left: Math.min(window.innerWidth - 12 - width / 2, Math.max(12 + width / 2, rect.left + rect.width / 2)),
      top: rect.top - 8,
    };
  }

  function hideTooltip() {
    activeTooltip = null;
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
    on:mouseenter={(event) => showTooltip(event, group)}
    on:mouseleave={hideTooltip}
    on:focus={(event) => showTooltip(event, group)}
    on:blur={hideTooltip}
    on:click={() => onSelect(group)}
  >
    <span class="sr-only">{group.name}</span>
    {#if !group.inStock}<span class="color-picker-stock-mark" aria-hidden="true">×</span>{/if}
  </button>
{/snippet}

{#if view === "continuous"}
  <div class="color-picker-palette color-picker-palette-continuous" aria-label="Paleta continua de colores PLA">
    {#each continuousBands as [band, items] (band)}
      <section class="color-picker-continuous-band" aria-labelledby={`continuous-band-${band}`}>
        <h2 id={`continuous-band-${band}`}>{continuousBandLabel(band)}</h2>
        <div class="color-picker-continuous-grid">
          {#each items as group (group.id)}{@render tile(group)}{/each}
        </div>
      </section>
    {/each}
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
    <div class="color-picker-map" aria-label="Mapa perceptual de colores PLA">
      <span class="color-picker-map-y">Luminosidad ↑</span>
      <span class="color-picker-map-x">Tono →</span>
      <span class="color-picker-map-note">Tamaño = intensidad</span>
      {#each mapGroups as group (group.id)}
        <div
          class="color-picker-map-point"
          style={`left: ${group.mapX}%; top: ${group.mapY}%; --map-size: ${group.mapSize}px`}
        >
          {@render tile(group)}
        </div>
      {/each}
    </div>
  </div>
{/if}

{#if activeTooltip}
  <div
    class="color-picker-tooltip"
    role="tooltip"
    style={`left: ${activeTooltip.left}px; top: ${activeTooltip.top}px`}
  >{activeTooltip.text}</div>
{/if}
