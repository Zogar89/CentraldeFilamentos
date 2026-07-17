<script>
  import { summaryProductImage } from "../lib/summaryRows.js";
  import { colorFamilyForProduct } from "../lib/catalogExplorer.js";
  import {
    colorSwatchStyle,
    dataUrl,
    formatInteger,
    formatPresentation,
    lineLabel,
    materialSwatchAlt,
    productBaseName,
  } from "../lib/shared.js";

  export let rows = [];
  export let sources = [];
  export let addFeedback = {};
  export let onAdd = () => {};
  export let onOpenPreview = () => {};
  export let onShowPreview = () => {};
  export let onMovePreview = () => {};
  export let onHidePreview = () => {};

  function approvedImage(product) {
    return summaryProductImage(product);
  }

  function fullImage(product) {
    if (!["manufacturer", "provider"].includes(product?.image_source)) return "";
    return product.image_url || product.thumbnail_url || "";
  }

  function stockLabel(cell) {
    if (cell?.units > 0) return "en stock";
    if (cell?.unknown) return "consultar";
    return "sin stock";
  }
</script>

<section class="catalog-explorer-results" aria-label="Resultados del catálogo">
  {#if rows.length}
    <div class="catalog-explorer-result-list">
      {#each rows as row (row.product.id)}
        {@const product = row.product}
        {@const imagePath = approvedImage(product)}
        {@const fullImagePath = fullImage(product)}
        {@const feedback = addFeedback[product.id]}
        <article
          class="catalog-explorer-result-row"
          data-product-id={product.id}
          data-material={product.material}
          data-color={product.color}
          data-color-family={colorFamilyForProduct(product).label}
        >
          <div class="catalog-explorer-result-identity">
            {#if imagePath}
              <button
                type="button"
                class="catalog-explorer-result-image"
                aria-label={`Ampliar foto de ${productBaseName(product)}`}
                on:click={() => onOpenPreview(fullImagePath, productBaseName(product), formatPresentation(product))}
                on:pointerenter={(event) => onShowPreview(event, fullImagePath, productBaseName(product))}
                on:pointermove={onMovePreview}
                on:pointerleave={onHidePreview}
              >
                <img src={dataUrl(imagePath)} alt={productBaseName(product)} loading="lazy" decoding="async">
              </button>
            {/if}
            {#if product.material_swatch_url}
              <img class="catalog-explorer-result-swatch" src={dataUrl(product.material_swatch_url)} alt={materialSwatchAlt(product)} loading="lazy" decoding="async">
            {:else}
              <span class="catalog-explorer-result-swatch" style={colorSwatchStyle(product)} aria-label={product.color || "Color sin normalizar"}></span>
            {/if}
            <div>
              <strong>{product.color || productBaseName(product)}</strong>
              <span>{product.brand} · {lineLabel(product)}</span>
              <small>{formatPresentation(product)}</small>
            </div>
          </div>

          <div class="catalog-explorer-provider-stock" aria-label={`Disponibilidad de ${productBaseName(product)}`}>
            {#each sources as source}
              {@const cell = row.cells[source.id]}
              <div class:available={cell?.units > 0} class:unknown={cell?.unknown}>
                <span>{source.name}</span>
                <strong>{cell?.unknown && !cell?.units ? "—" : formatInteger(cell?.units || 0)}</strong>
                <small>{stockLabel(cell)}</small>
              </div>
            {/each}
          </div>

          <button
            type="button"
            class="catalog-explorer-add"
            class:confirmed={Boolean(feedback)}
            aria-label={`Agregar ${productBaseName(product)} a la lista de cotización`}
            on:click={() => onAdd(product)}
          >
            <strong>{feedback ? `${feedback} en lista` : "Agregar"}</strong>
            <span>{feedback ? "Cantidad actualizada" : "+1 unidad"}</span>
          </button>
        </article>
      {/each}
    </div>
  {:else}
    <div class="catalog-explorer-no-results">
      <strong>No encontramos opciones con estos filtros</strong>
      <p>El material elegido sigue activo. Probá limpiar color o filtros secundarios.</p>
    </div>
  {/if}
</section>
