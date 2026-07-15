<script>
  import { distanceLabel, normalizeHex } from "../lib/colorPicker.js";

  export let hex = "";
  export let results = [];
  export let error = "";
  export let searchActive = false;
  export let hideOutOfStock = false;
  export let hasValidHex = false;
  export let onHexChange = () => {};
  export let onSearch = () => {};
  export let onCompare = () => {};

  function colorValue() {
    const value = normalizeHex(hex);
    return /^#[0-9A-F]{6}$/.test(value) ? value : "#000000";
  }
</script>

<section class="color-picker-similar" aria-labelledby="similar-title">
  <header>
    <div>
      <span class="eyebrow">CIEDE2000 · CULORI</span>
      <h2 id="similar-title">Buscar colores similares</h2>
      <p>Elegí un cuadrado o ingresá cualquier HEX para ver los tres filamentos más cercanos.</p>
    </div>
    <form on:submit|preventDefault={onSearch}>
      <input type="color" aria-label="Elegir color de referencia" value={colorValue()} on:input={(event) => onHexChange(event.currentTarget.value)}>
      <label>
        <span>HEX de referencia</span>
        <input type="text" maxlength="7" spellcheck="false" value={hex} aria-invalid={error ? "true" : undefined} on:input={(event) => onHexChange(event.currentTarget.value)}>
      </label>
      <button type="submit">Buscar similares</button>
    </form>
  </header>

  {#if error}<p class="color-picker-error" role="alert">{error}</p>{/if}

  {#if searchActive && hasValidHex && results.length < 3}
    <p class="color-picker-similar-warning" role="status">
      {#if results.length}
        Se encontraron {results.length} de los tres colores similares disponibles.
      {:else}
        No encontramos colores similares con esta referencia y los filtros actuales.
      {/if}
      {#if hideOutOfStock} Desmarcá “Ocultar sin stock” para ampliar la búsqueda.{/if}
    </p>
  {/if}

  {#if results.length}
    <div class="color-picker-similar-results" role="region" aria-label={`${results.length} colores similares`}>
      {#each results as result (result.group.id)}
        <article class="color-picker-similar-card" style={`--picker-color: ${result.group.hex}`}>
          <button class="color-picker-similar-swatch" type="button" aria-label={`Comparar ${result.group.name}`} on:click={() => onCompare(result.group)}></button>
          <div>
            <strong>{result.group.name}</strong>
            <span>{result.group.brand} · {result.group.line}</span>
            <span>{result.group.hex} · ΔE {result.distance.toFixed(1)}</span>
          </div>
          <footer>
            <span>{distanceLabel(result.distance)}</span>
            <button type="button" on:click={() => onCompare(result.group)}>Comparar</button>
          </footer>
        </article>
      {/each}
    </div>
  {/if}

  <p class="color-picker-similar-warning">La distancia es orientativa: el acabado, la iluminación, el lote y la pantalla pueden cambiar la percepción del filamento real.</p>
</section>
