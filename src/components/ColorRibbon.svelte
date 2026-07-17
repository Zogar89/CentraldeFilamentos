<script>
  export let choices = [];
  export let selected = "";
  export let material = "PLA";
  export let familyProductCount = 0;
  export let onSelect = () => {};
  export let onClear = () => {};

  $: selectedChoice = choices.find((choice) => choice.name === selected) || null;
</script>

<section class="catalog-explorer-colors" aria-labelledby="catalog-color-title">
  <header>
    <h2 id="catalog-color-title">Explorá colores en {material}</h2>
    <span>{choices.length} colores publicados</span>
  </header>
  {#if choices.length}
    <div class="catalog-explorer-color-scroll" role="group" aria-label={`Colores disponibles en ${material}`}>
      {#each choices as choice (choice.id)}
        <button
          type="button"
          class="catalog-explorer-color"
          class:selected={selected === choice.name}
          class:without-color={!choice.hex}
          style={choice.hex ? `--catalog-color: ${choice.hex}` : ""}
          aria-label={`${choice.name}, ${choice.stockTotal} unidades publicadas`}
          aria-pressed={selected === choice.name}
          title={choice.name}
          on:click={() => onSelect(choice.name)}
        >
          <span aria-hidden="true"></span>
        </button>
      {/each}
    </div>
  {:else}
    <p class="catalog-explorer-color-empty">Todavía no hay colores normalizados para este material.</p>
  {/if}

  {#if selectedChoice}
    <div class="catalog-explorer-color-context" aria-live="polite">
      <span class="catalog-explorer-color-context-swatch" style={selectedChoice.hex ? `--catalog-color: ${selectedChoice.hex}` : ""} aria-hidden="true"></span>
      <div>
        <strong>{selectedChoice.name}</strong>
        <span>Familia: {selectedChoice.familyLabel} · {familyProductCount} opciones en {material}</span>
      </div>
      {#if material === "PLA"}<a href="color-picker.html">Comparar tonos</a>{/if}
      <button type="button" on:click={onClear}>Limpiar color</button>
    </div>
  {/if}
</section>
