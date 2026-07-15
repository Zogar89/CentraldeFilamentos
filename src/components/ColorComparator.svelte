<script>
  import { rgbFromHex } from "../lib/colorPicker.js";
  import { dataUrl } from "../lib/shared.js";

  export let groups = [];
  export let addDisabled = false;
  export let onRemove = () => {};
  export let onAddPresentation = () => {};
</script>

<section class="color-picker-comparator" aria-labelledby="comparator-title">
  <header>
    <div>
      <h2 id="comparator-title">Comparador</h2>
      <p>Máximo cuatro colores.</p>
    </div>
    <span>{groups.length} / 4</span>
  </header>

  {#if groups.length}
    <div class="color-picker-comparator-grid">
      {#each groups as group (group.id)}
        {@const rgb = rgbFromHex(group.hex)}
        <article class="color-picker-compare-card" style={`--picker-color: ${group.hex}`}>
          <header>
            <div><strong>{group.name}</strong><span>{group.brand} · {group.line}</span></div>
            <button type="button" aria-label={`Quitar ${group.name} del comparador`} on:click={() => onRemove(group)}>×</button>
          </header>
          <div class="color-picker-material-render">
            <span class="color-picker-render-fallback" aria-label={`Muestra plana ${group.hex}`}></span>
            {#if group.materialSwatchUrl}
              <img src={dataUrl(group.materialSwatchUrl)} alt={`Render de material para ${group.brand} ${group.name}`} on:error={(event) => event.currentTarget.hidden = true}>
            {/if}
          </div>
          <dl>
            <div><dt>HEX</dt><dd>{group.hex}</dd></div>
            <div><dt>RGB</dt><dd>{rgb.r}, {rgb.g}, {rgb.b}</dd></div>
            <div><dt>Pantone</dt><dd>{group.pantone || "Color estimado"}</dd></div>
            <div><dt>Stock</dt><dd>{group.inStock ? "Disponible" : "Sin stock"}</dd></div>
          </dl>
          {#if group.estimated && group.warning}<p class="color-picker-estimate-warning">{group.warning}</p>{/if}
          <div class="color-picker-presentations">
            <span>Presentaciones</span>
            {#each group.presentations as presentation (presentation.id)}
              <button type="button" disabled={addDisabled} on:click={() => onAddPresentation(presentation.product)}>
                <span>{presentation.label}{presentation.inStock ? "" : " · sin stock"}</span><strong>+1</strong>
              </button>
            {/each}
          </div>
        </article>
      {/each}
    </div>
  {:else}
    <p class="color-picker-empty-comparator">Seleccioná cuadrados de la paleta o resultados similares para comparar.</p>
  {/if}
</section>
