<script>
  import { dataUrl, formatDate } from "../lib/shared.js";

  export let active = "summary";
  export let updatedAt = "";
  export let subtitle = "";
  export let showCatalogHelp = false;
  export let catalogMode = false;
  export let query = "";
  export let onQueryChange = () => {};
  export let quoteCount = 0;
  export let onOpenQuote = () => {};

  $: updatedLabel = updatedAt ? `Actualizado: ${formatDate(updatedAt)}` : subtitle;

  const navItems = [
    { id: "summary", label: "Resumen", href: "index.html" },
    { id: "color-picker", label: "Color Picker", href: "color-picker.html" },
    { id: "providers", label: "Proveedores", href: "index.html#site-footer" },
  ];

</script>

<a class="skip-link" href="#main-content">Saltar al contenido</a>

{#if catalogMode}
  <header class="site-header site-header-catalog">
    <a class="brand-lockup catalog-brand-lockup" href="index.html" aria-label="Ir al inicio">
      <img class="catalog-brand-mark" src={dataUrl("favicon.svg")} alt="">
      <span class="brand-title">Central de Filamentos</span>
    </a>
    <label class="catalog-header-search" for="search-input">
      <span class="sr-only">Buscar en el catálogo</span>
      <input
        id="search-input"
        type="search"
        value={query}
        placeholder="Buscar filamentos, colores, marcas..."
        on:input={(event) => onQueryChange(event.currentTarget.value)}
      >
    </label>
    <nav class="catalog-header-actions" aria-label="Acciones del catálogo">
      <a href="color-picker.html">Comparar colores</a>
      <button type="button" class="catalog-header-quote" on:click={onOpenQuote}>
        Lista de cotización <span>{quoteCount}</span>
      </button>
      <span class="catalog-header-locale" aria-label="Región Argentina">AR</span>
    </nav>
  </header>
{:else}
  <header class="site-header">
    <a class="brand-lockup" href="index.html" aria-label="Ir al resumen">
      <span class="brand-mark" aria-hidden="true">CF</span>
      <span class="brand-copy">
        <span class="brand-title">Central de Filamentos</span>
        {#if updatedLabel}
          <span class="brand-subtitle">{updatedLabel}</span>
        {/if}
      </span>
    </a>

    <nav class="view-switch" aria-label="Cambiar vista">
      {#each navItems as item}
        <a class="nav-link" class:active={active === item.id} aria-current={active === item.id ? "page" : undefined} href={item.href}>{item.label}</a>
      {/each}
    </nav>
  </header>
{/if}

{#if showCatalogHelp}
  <section class="catalog-guide" aria-label="Cómo usar el catálogo">
    <p class="catalog-guide-purpose">Encontrá filamentos disponibles, armá tu lista y consultá cotización directamente a cada proveedor.</p>
    <div class="catalog-guide-item">
      <span class="catalog-guide-control catalog-guide-add" aria-hidden="true">+1</span>
      <span>Agrega una unidad a tu lista de cotización.</span>
    </div>
  </section>
{/if}
