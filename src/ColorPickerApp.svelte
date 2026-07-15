<script>
  import { onMount } from "svelte";
  import ColorPalette from "./components/ColorPalette.svelte";
  import SimilarColorSearch from "./components/SimilarColorSearch.svelte";
  import SiteFooter from "./components/SiteFooter.svelte";
  import SiteHeader from "./components/SiteHeader.svelte";
  import {
    buildPlaColorCatalog,
    findSimilarColors,
    isValidHex,
    normalizeHex,
    toggleComparedColor,
  } from "./lib/colorPicker.js";
  import { fetchJson } from "./lib/shared.js";

  let loading = true;
  let loadError = "";
  let groups = [];
  let excludedCount = 0;
  let sources = [];
  let generatedAt = "";
  let activeView = "continuous";
  let hideOutOfStock = false;
  let selectedIds = [];
  let referenceHex = "";
  let referenceGroupId = "";
  let selectionMessage = "";
  let similarHex = "";
  let similarResults = [];
  let similarError = "";
  let searchActive = false;

  $: visibleGroups = hideOutOfStock ? groups.filter((group) => group.inStock) : groups;

  onMount(loadCatalog);

  async function loadCatalog() {
    loading = true;
    loadError = "";
    const payload = await fetchJson("data/stock.json", null);
    if (!payload || !Array.isArray(payload.products)) {
      loading = false;
      loadError = "No pudimos cargar los colores publicados.";
      return;
    }
    const catalog = buildPlaColorCatalog(payload.products);
    groups = catalog.groups;
    excludedCount = catalog.excludedCount;
    sources = Array.isArray(payload.sources) ? payload.sources : [];
    generatedAt = payload.generated_at || "";
    loading = false;
  }

  function selectGroup(group) {
    referenceHex = group.hex;
    referenceGroupId = group.id;
    similarHex = group.hex;
    similarError = "";
    const result = toggleComparedColor(selectedIds, group.id);
    selectedIds = result.ids;
    selectionMessage = result.message;
  }

  function setSimilarHex(value) {
    similarHex = value;
    referenceGroupId = "";
    similarError = "";
  }

  function runSimilarSearch() {
    const normalized = normalizeHex(similarHex);
    if (!isValidHex(normalized)) {
      similarError = "Ingresá un HEX válido, por ejemplo #009DCE.";
      return;
    }
    similarHex = normalized;
    similarError = "";
    searchActive = true;
    similarResults = findSimilarColors(visibleGroups, normalized, referenceGroupId, 3);
  }

  function setHideOutOfStock(value) {
    hideOutOfStock = value;
    if (searchActive) {
      const nextGroups = value ? groups.filter((group) => group.inStock) : groups;
      similarResults = findSimilarColors(nextGroups, similarHex, referenceGroupId, 3);
    }
  }
</script>

<SiteHeader active="color-picker" updatedAt={generatedAt} subtitle="PLA · búsqueda por color" />

<main id="main-content" class="color-picker-page">
  <header class="color-picker-hero">
    <div>
      <span class="eyebrow">PLA · COLOR PICKER</span>
      <h1>Encontrá el color que necesitás</h1>
      <p>Explorá el catálogo por apariencia, compará hasta cuatro opciones y sumá la presentación exacta a tu lista.</p>
    </div>
  </header>

  {#if loading}
    <p class="color-picker-state" role="status">Cargando colores…</p>
  {:else if loadError}
    <section class="color-picker-state" role="alert">
      <p>{loadError}</p>
      <button type="button" on:click={loadCatalog}>Reintentar</button>
    </section>
  {:else if !groups.length}
    <p class="color-picker-state">No hay filamentos PLA con datos HEX disponibles.</p>
  {:else}
    <section class="color-picker-controls" aria-label="Organización de la paleta">
      <div class="color-picker-view-tabs">
        {#each [["continuous", "Continuo"], ["families", "Familias"], ["map", "Mapa 2D"]] as [id, label]}
          <button type="button" class:active={activeView === id} aria-pressed={activeView === id} on:click={() => activeView = id}>{label}</button>
        {/each}
      </div>
      <label class="color-picker-stock-toggle">
        <input type="checkbox" checked={hideOutOfStock} on:change={(event) => setHideOutOfStock(event.currentTarget.checked)}>
        <span>Ocultar sin stock</span>
      </label>
    </section>

    <div class="color-picker-summary">
      <span>{visibleGroups.length} colores</span>
      {#if excludedCount}<span>{excludedCount} productos PLA sin HEX</span>{/if}
    </div>

    <SimilarColorSearch
      hex={similarHex}
      results={similarResults}
      error={similarError}
      onHexChange={setSimilarHex}
      onSearch={runSimilarSearch}
      onCompare={selectGroup}
    />

    <ColorPalette groups={visibleGroups} view={activeView} {selectedIds} onSelect={selectGroup} />
    <p class="sr-only" aria-live="polite">{selectionMessage}</p>
  {/if}
</main>

<SiteFooter {sources} />
