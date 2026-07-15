<script>
  import { onMount } from "svelte";
  import ColorPalette from "./components/ColorPalette.svelte";
  import ColorComparator from "./components/ColorComparator.svelte";
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
  import {
    incrementQuoteListItem,
    initializeQuoteList,
    loadQuoteList,
    saveQuoteList,
  } from "./lib/quoteList.js";

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
  let products = [];
  let quoteItems = [];
  let quoteSettings = { showQuickControls: false };
  let quoteReadOnly = false;
  let preservedQuotePayload = null;
  let quoteMessage = "";
  let quoteWarning = "";

  $: visibleGroups = hideOutOfStock ? groups.filter((group) => group.inStock) : groups;
  $: selectedGroups = selectedIds.map((id) => groups.find((group) => group.id === id)).filter(Boolean);
  $: normalizedSimilarHex = normalizeHex(similarHex);
  $: if (searchActive && isValidHex(normalizedSimilarHex)) {
    similarResults = findSimilarColors(visibleGroups, normalizedSimilarHex, referenceGroupId, 3);
  } else if (searchActive) {
    similarResults = [];
  }

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
    products = payload.products;
    const catalog = buildPlaColorCatalog(products);
    groups = catalog.groups;
    excludedCount = catalog.excludedCount;
    sources = Array.isArray(payload.sources) ? payload.sources : [];
    generatedAt = payload.generated_at || "";
    const loadedQuote = loadQuoteList();
    const reconciled = initializeQuoteList(loadedQuote, { ok: true, products });
    quoteItems = reconciled.items;
    quoteSettings = reconciled.settings;
    quoteReadOnly = loadedQuote.readOnly;
    preservedQuotePayload = loadedQuote.preservedPayload;
    if (reconciled.shouldSave) {
      saveQuoteList({
        items: quoteItems,
        settings: quoteSettings,
        readOnly: quoteReadOnly,
        preservedPayload: preservedQuotePayload,
      });
    }
    quoteWarning = loadedQuote.readOnly
      ? "La lista guardada usa una versión más nueva. La conservamos sin cambios."
      : (loadedQuote.storageAvailable ? "" : "No pudimos guardar la lista; los cambios durarán sólo durante esta sesión.");
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
    if (!isValidHex(normalizedSimilarHex)) {
      similarError = "Ingresá un HEX válido, por ejemplo #009DCE.";
      return;
    }
    similarHex = normalizedSimilarHex;
    similarError = "";
    searchActive = true;
  }

  function setHideOutOfStock(value) {
    hideOutOfStock = value;
  }

  function removeComparedGroup(group) {
    const result = toggleComparedColor(selectedIds, group.id);
    selectedIds = result.ids;
    selectionMessage = result.message;
  }

  function addPresentation(product) {
    if (quoteReadOnly) return;
    quoteItems = incrementQuoteListItem(quoteItems, product);
    const saveResult = saveQuoteList({
      items: quoteItems,
      settings: quoteSettings,
      readOnly: quoteReadOnly,
      preservedPayload: preservedQuotePayload,
    });
    const current = quoteItems.find((item) => item.productId === product.id);
    quoteMessage = `${current.productName} · ${current.presentation}: ${current.quantity} unidad(es) en la lista.`;
    if (!saveResult.ok && !saveResult.blocked) {
      quoteWarning = "No pudimos guardar la lista; los cambios durarán sólo durante esta sesión.";
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
      searchActive={searchActive}
      hideOutOfStock={hideOutOfStock}
      hasValidHex={isValidHex(normalizedSimilarHex)}
      onHexChange={setSimilarHex}
      onSearch={runSimilarSearch}
      onCompare={selectGroup}
    />

    <ColorPalette groups={visibleGroups} view={activeView} {selectedIds} onSelect={selectGroup} />
    <ColorComparator
      groups={selectedGroups}
      addDisabled={quoteReadOnly}
      onRemove={removeComparedGroup}
      onAddPresentation={addPresentation}
    />
    {#if quoteWarning}<p class="color-picker-quote-warning" role="status">{quoteWarning}</p>{/if}
    <p class="sr-only" aria-live="polite">{quoteMessage}</p>
    <p class="sr-only" aria-live="polite">{selectionMessage}</p>
  {/if}
</main>

<SiteFooter {sources} />
