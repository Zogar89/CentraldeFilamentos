<script>
  import { dataUrl } from "../lib/shared.js";

  export let choices = [];
  export let selected = "PLA";
  export let onSelect = () => {};
</script>

<section class="catalog-explorer-materials" aria-labelledby="catalog-material-title">
  <header>
    <h1 id="catalog-material-title">¿Qué material vas a usar?</h1>
    <p>Elegí el material que vas a imprimir. Después exploramos colores y stock.</p>
  </header>
  <div class="catalog-explorer-material-grid" role="group" aria-label="Elegir material">
    {#each choices as choice (choice.id)}
      <button
        type="button"
        class="catalog-explorer-material"
        class:selected={selected === choice.id}
        aria-label={`${choice.label}, ${choice.count} opciones`}
        aria-pressed={selected === choice.id}
        on:click={() => onSelect(choice.id)}
      >
        <span class="catalog-explorer-material-visual" aria-hidden="true">
          {#if choice.imageUrl}
            <img src={dataUrl(choice.imageUrl)} alt="" loading="lazy" decoding="async" on:error={(event) => event.currentTarget.hidden = true}>
          {/if}
        </span>
        <strong>{choice.label}</strong>
        <small>{choice.count} opciones</small>
        {#if selected === choice.id}<span class="catalog-explorer-material-selected">Elegido</span>{/if}
      </button>
    {/each}
  </div>
</section>
