<script>
  export let choices = [];
  export let selected = "";
  export let material = "PLA";
  export let selectionProductCount = 0;
  export let onSelect = () => {};
  export let onClear = () => {};

  $: selectedChoice = choices.find((choice) => choice.name === selected) || null;
  $: familyMode = material === "PLA";

  function swatchStyle(choice) {
    const hexes = (choice.swatchHexes || [choice.hex]).filter(Boolean);
    if (!hexes.length) return "";
    const background = hexes.length === 1
      ? hexes[0]
      : `linear-gradient(135deg, ${hexes.join(", ")})`;
    return `--catalog-color: ${background}`;
  }
</script>

<section class="catalog-explorer-colors" aria-labelledby="catalog-color-title">
  <header>
    <h2 id="catalog-color-title">Explorá {familyMode ? "familias de color" : "colores"} en {material}</h2>
    <span>{choices.length} {familyMode ? "familias publicadas" : "colores publicados"}</span>
  </header>
  {#if choices.length}
    <div class="catalog-explorer-color-scroll" role="group" aria-label={`${familyMode ? "Familias de color" : "Colores"} disponibles en ${material}`}>
      {#each choices as choice (choice.id)}
        <button
          type="button"
          class="catalog-explorer-color"
          class:family={choice.selectionMode === "family"}
          class:selected={selected === choice.name}
          class:without-color={!choice.hex}
          style={swatchStyle(choice)}
          aria-label={choice.selectionMode === "family"
            ? `${choice.name}, ${choice.exactColorCount} colores, ${choice.productCount} opciones, ${choice.stockTotal} unidades publicadas`
            : `${choice.name}, ${choice.stockTotal} unidades publicadas`}
          aria-pressed={selected === choice.name}
          title={choice.name}
          on:click={() => onSelect(choice.name)}
        >
          <span aria-hidden="true"></span>
          {#if choice.selectionMode === "family"}<strong>{choice.name}</strong>{/if}
        </button>
      {/each}
    </div>
  {:else}
    <p class="catalog-explorer-color-empty">Todavía no hay colores normalizados para este material.</p>
  {/if}

  {#if selectedChoice}
    <div class="catalog-explorer-color-context" aria-live="polite">
      <span class="catalog-explorer-color-context-swatch" style={swatchStyle(selectedChoice)} aria-hidden="true"></span>
      <div>
        <strong>{selectedChoice.name}</strong>
        {#if selectedChoice.selectionMode === "family"}
          <span>{selectedChoice.exactColorCount} colores exactos, {selectionProductCount} opciones en {material}</span>
        {:else}
          <span>Color exacto, {selectionProductCount} opciones en {material}</span>
        {/if}
      </div>
      {#if material === "PLA"}<a href="color-picker.html">Comparar tonos</a>{/if}
      <button type="button" on:click={onClear}>Limpiar selección</button>
    </div>
  {/if}
</section>
