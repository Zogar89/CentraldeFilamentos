<script>
  import { onDestroy, onMount } from "svelte";

  import CatalogExplorerResults from "./components/CatalogExplorerResults.svelte";
  import ColorRibbon from "./components/ColorRibbon.svelte";
  import MaterialSelector from "./components/MaterialSelector.svelte";
  import QuoteListDrawer from "./components/QuoteListDrawer.svelte";
  import QuoteListPanel from "./components/QuoteListPanel.svelte";
  import SiteFooter from "./components/SiteFooter.svelte";
  import SiteHeader from "./components/SiteHeader.svelte";
  import {
    colorChoices,
    compareCatalogProducts,
    compareExplorerProducts,
    materialChoices,
    matchesColorSelection,
    matchesMaterialSelection,
  } from "./lib/catalogExplorer.js";
  import { createQuoteWorkspace } from "./lib/quoteWorkspace.js";
  import { buildSummaryRows } from "./lib/summaryRows.js";
  import {
    dataUrl,
    fetchJson,
    formatDate,
    formatWeightLabel,
    lineLabel,
    lineOptionLabel,
    matchesSearchTerms,
    productBaseName,
  } from "./lib/shared.js";

  const BRAND_LOGOS = {
    "3N3": "assets/brands/3n3.png",
    Grilon3: "assets/brands/grilon3.png",
  };

  let loading = true;
  let loadError = "";
  let products = [];
  let sources = [];
  let generatedAt = "";
  let selectedMaterial = "PLA";
  let selectedColor = "";
  let sortOrder = "popular";
  let showMoreFilters = false;
  let compactQuoteMode = false;
  let quoteDrawerOpen = false;
  let quoteWorkspace = null;
  let unsubscribeQuote = null;
  let quoteState = {
    items: [],
    settings: { showQuickControls: true },
    storageWarning: "",
    reconcileNotice: "",
    readOnly: false,
    preservedPayload: null,
  };
  let quoteImportInput;
  let quoteImportPreview = null;
  let quoteImportError = "";
  let quoteImportFileName = "";
  let quoteAddFeedback = {};
  let quoteFeedbackMessage = "";
  let preview = null;
  let mediaQuery = null;
  const quoteFeedbackTimers = new Map();

  let filters = {
    query: "",
    variant: "",
    diameter: "1.75",
    weight: "",
    brand: "",
    provider: "",
    stock: "all",
  };

  onMount(() => {
    loadCatalog();
    mediaQuery = window.matchMedia("(max-width: 1099px)");
    updateQuoteMode(mediaQuery);
    mediaQuery.addEventListener("change", updateQuoteMode);
  });

  onDestroy(() => {
    unsubscribeQuote?.();
    mediaQuery?.removeEventListener("change", updateQuoteMode);
    quoteFeedbackTimers.forEach((timer) => window.clearTimeout(timer));
  });

  $: materialChoiceOptions = materialChoices(products);
  $: availableColors = colorChoices(products, selectedMaterial);
  $: selectedColorChoice = availableColors.find((choice) => choice.name === selectedColor) || null;
  $: filteredProducts = (selectedMaterial, selectedColor, selectedColorChoice, filters, sortOrder, products.filter(matchesFilters).sort((left, right) => (
    sortOrder === "availability"
      ? compareExplorerProducts(left, right)
      : compareCatalogProducts(left, right)
  )));
  $: resultRows = buildSummaryRows(filteredProducts, sources);
  $: materialProducts = products.filter((product) => matchesMaterialSelection(product, selectedMaterial));
  $: selectedColorProductCount = selectedColorChoice
    ? materialProducts.filter((product) => matchesColorSelection(product, selectedColorChoice)).length
    : 0;
  $: variantOptions = valuesForMaterial(materialProducts, (product) => lineLabel(product));
  $: diameterOptions = valuesForMaterial(materialProducts, (product) => product.diameter_mm);
  $: weightOptions = valuesForMaterial(materialProducts, (product) => product.weight_g);
  $: brandOptions = valuesForMaterial(materialProducts, (product) => product.brand);
  $: providerOptions = [...new Set(materialProducts.flatMap((product) => (product.offers || []).map((offer) => offer.provider_name)).filter(Boolean))].sort((left, right) => left.localeCompare(right, "es-AR"));
  $: secondaryFilterCount = [filters.variant, filters.diameter, filters.weight, filters.brand, filters.provider, filters.stock !== "all" ? filters.stock : ""].filter(Boolean).length;
  $: contactContext = [filters.query, selectedMaterial, selectedColor, filters.variant, filters.diameter ? `${filters.diameter} mm` : "", filters.weight ? formatWeightLabel(filters.weight) : "", filters.brand].filter(Boolean).join(", ");

  async function loadCatalog() {
    loading = true;
    loadError = "";
    const payload = await fetchJson("data/stock.json", null);
    const catalogAvailable = Boolean(payload && Array.isArray(payload.products));
    products = catalogAvailable ? payload.products : [];
    sources = Array.isArray(payload?.sources) ? payload.sources : [];
    generatedAt = payload?.generated_at || "";
    if (!catalogAvailable) loadError = "No pudimos cargar el stock publicado.";
    if (!products.some((product) => product.material === selectedMaterial)) {
      selectedMaterial = materialChoices(products)[0]?.id || "PLA";
    }
    connectQuoteWorkspace(catalogAvailable);
    loading = false;
  }

  function connectQuoteWorkspace(catalogAvailable) {
    unsubscribeQuote?.();
    quoteWorkspace = createQuoteWorkspace({ products, catalogAvailable });
    unsubscribeQuote = quoteWorkspace.state.subscribe((state) => {
      quoteState = state;
      if (!state.items.length) quoteDrawerOpen = false;
    });
  }

  function updateQuoteMode(event) {
    compactQuoteMode = event.matches;
    if (!compactQuoteMode) quoteDrawerOpen = false;
  }

  function valuesForMaterial(materialItems, selector) {
    return [...new Set(materialItems.map(selector).filter((value) => value !== "" && value !== null && value !== undefined))]
      .sort((left, right) => String(left).localeCompare(String(right), "es-AR", { numeric: true }));
  }

  function matchesFilters(product) {
    if (!matchesMaterialSelection(product, selectedMaterial)) return false;
    if (selectedColorChoice && !matchesColorSelection(product, selectedColorChoice)) return false;
    const queryFields = [
      product.display_name,
      product.material,
      product.variant,
      product.subrange,
      product.color,
      product.pantone,
      product.sku,
      product.ean,
      product.brand,
      ...(product.offers || []).map((offer) => offer.original_name),
    ];
    if (filters.query && !matchesSearchTerms(filters.query.toLowerCase().trim(), queryFields)) return false;
    if (filters.variant && lineLabel(product) !== filters.variant) return false;
    if (filters.diameter && String(product.diameter_mm) !== filters.diameter) return false;
    if (filters.weight && String(product.weight_g) !== filters.weight) return false;
    if (filters.brand && product.brand !== filters.brand) return false;
    if (filters.provider && !(product.offers || []).some((offer) => offer.provider_name === filters.provider)) return false;
    if (filters.stock !== "all" && !(product.offers || []).some((offer) => offer.stock_status === filters.stock)) return false;
    return true;
  }

  function setMaterial(material) {
    selectedMaterial = material;
    selectedColor = "";
    filters = { ...filters, variant: "", brand: "", provider: "" };
  }

  function selectColor(color) {
    selectedColor = selectedColor === color ? "" : color;
  }

  function setFilter(name, value) {
    filters = { ...filters, [name]: value };
  }

  function clearSecondaryFilters() {
    selectedColor = "";
    filters = { ...filters, variant: "", diameter: "", weight: "", brand: "", provider: "", stock: "all" };
    showMoreFilters = false;
  }

  function openQuote() {
    if (compactQuoteMode) {
      if (quoteState.items.length) quoteDrawerOpen = true;
      return;
    }
    document.querySelector(".catalog-quote-rail")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function addQuoteItem(product) {
    if (!quoteWorkspace || quoteState.readOnly) return;
    quoteWorkspace.addProduct(product);
    const quantity = Number(quoteState.items.find((item) => item.productId === product.id)?.quantity || 0);
    showQuoteFeedback(product, quantity);
    if (compactQuoteMode) quoteDrawerOpen = true;
  }

  function showQuoteFeedback(product, quantity) {
    window.clearTimeout(quoteFeedbackTimers.get(product.id));
    quoteAddFeedback = { ...quoteAddFeedback, [product.id]: quantity };
    quoteFeedbackMessage = `${productBaseName(product)} agregado. ${quantity} unidad(es) en la lista.`;
    quoteFeedbackTimers.set(product.id, window.setTimeout(() => {
      const next = { ...quoteAddFeedback };
      delete next[product.id];
      quoteAddFeedback = next;
      quoteFeedbackTimers.delete(product.id);
    }, 1100));
  }

  function clearQuoteList() {
    if (!window.confirm("¿Vaciar la lista de cotización?")) return;
    quoteWorkspace?.clear();
  }

  function exportQuoteList() {
    if (!quoteState.items.length || quoteState.readOnly) return;
    const blob = new Blob([quoteWorkspace.exportJson()], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `stockcentral-lista-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }

  function openQuoteImportPicker() {
    quoteImportError = "";
    quoteImportInput?.click();
  }

  async function handleQuoteImportFile(event) {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = "";
    if (!file) return;
    quoteImportFileName = file.name;
    if (file.size > 2_000_000) {
      quoteImportPreview = null;
      quoteImportError = "El archivo es demasiado grande para una lista de cotización.";
      return;
    }
    const result = quoteWorkspace.previewImport(await file.text());
    if (!result.ok) {
      quoteImportPreview = null;
      quoteImportError = result.error;
      return;
    }
    quoteImportError = "";
    quoteImportPreview = result;
  }

  function applyQuoteImport(mode) {
    quoteWorkspace?.applyImport(quoteImportPreview, mode);
    closeQuoteImport();
  }

  function closeQuoteImport() {
    quoteImportPreview = null;
    quoteImportError = "";
    quoteImportFileName = "";
  }

  function showAssetPreview(event, src, title) {
    if (!src) return;
    preview = { src: dataUrl(src), title, x: event.clientX + 16, y: event.clientY + 16, modal: false };
  }

  function movePreview(event) {
    if (!preview || preview.modal) return;
    preview = { ...preview, x: event.clientX + 16, y: event.clientY + 16 };
  }

  function hideHoverPreview() {
    if (!preview?.modal) preview = null;
  }

  function openAssetPreview(src, title, meta = "") {
    if (!src) return;
    preview = { src: dataUrl(src), title, meta, modal: true };
  }

  function handleWindowKeydown(event) {
    if (event.key === "Escape" && (quoteImportPreview || quoteImportError)) closeQuoteImport();
    else if (event.key === "Escape" && preview?.modal) preview = null;
    else if (event.key === "Escape" && quoteDrawerOpen) quoteDrawerOpen = false;
  }
</script>

<SiteHeader
  active="summary"
  catalogMode
  query={filters.query}
  onQueryChange={(value) => setFilter("query", value)}
  quoteCount={quoteState.items.length}
  onOpenQuote={openQuote}
/>

<main id="main-content" class="catalog-explorer-shell" tabindex="-1">
  <p class="sr-only" aria-live="polite">{quoteFeedbackMessage}</p>

  {#if loading}
    <p class="catalog-explorer-state" role="status">Cargando materiales, colores y stock…</p>
  {:else if loadError}
    <section class="catalog-explorer-state" role="alert">
      <strong>{loadError}</strong>
      <button type="button" on:click={loadCatalog}>Reintentar</button>
    </section>
  {:else}
    <div class="catalog-explorer-layout">
      <div class="catalog-explorer-main">
        <MaterialSelector choices={materialChoiceOptions} selected={selectedMaterial} onSelect={setMaterial} />
        <ColorRibbon choices={availableColors} selected={selectedColor} material={selectedMaterial} selectionProductCount={selectedColorProductCount} onSelect={selectColor} onClear={() => selectedColor = ""} />

        <section class="catalog-explorer-filters" class:expanded={showMoreFilters} aria-label="Filtros de presentación y proveedor">
          <div class="catalog-explorer-filter-control">
            <span>Diámetro</span>
            <div class="catalog-explorer-filter-buttons" role="group" aria-label="Diámetro">
              {#each diameterOptions as value}
                <button
                  id={`diameter-filter-${value}`}
                  class="catalog-explorer-filter-option"
                  type="button"
                  aria-pressed={filters.diameter === String(value)}
                  on:click={() => setFilter("diameter", filters.diameter === String(value) ? "" : String(value))}
                >{value} mm</button>
              {/each}
            </div>
          </div>
          <label>
            <span>Presentación</span>
            <select id="variant-filter" value={filters.variant} on:change={(event) => setFilter("variant", event.currentTarget.value)}>
              <option value="">Todas</option>
              {#each variantOptions as value}<option value={value}>{lineOptionLabel(value)}</option>{/each}
            </select>
          </label>
          <label>
            <span>Peso</span>
            <select id="weight-filter" value={filters.weight} on:change={(event) => setFilter("weight", event.currentTarget.value)}>
              <option value="">Todos</option>
              {#each weightOptions as value}<option value={String(value)}>{formatWeightLabel(value)}</option>{/each}
            </select>
          </label>
          <div class="catalog-explorer-filter-control">
            <span>Marca</span>
            <div class="catalog-explorer-filter-buttons" role="group" aria-label="Marca">
              {#each brandOptions as value}
                <button
                  id={`brand-filter-${value}`}
                  class="catalog-explorer-filter-option"
                  type="button"
                  aria-label={value}
                  aria-pressed={filters.brand === value}
                  on:click={() => setFilter("brand", filters.brand === value ? "" : value)}
                >
                  <img class="catalog-explorer-filter-brand-logo" src={dataUrl(BRAND_LOGOS[value])} alt="" aria-hidden="true">
                </button>
              {/each}
            </div>
          </div>
          <button class="catalog-explorer-more-filters" type="button" aria-expanded={showMoreFilters} on:click={() => showMoreFilters = !showMoreFilters}>
            {showMoreFilters ? "Menos filtros" : "Más filtros"}{secondaryFilterCount ? ` · ${secondaryFilterCount}` : ""}
          </button>
          <label class="catalog-explorer-filter-extra">
            <span>Proveedor</span>
            <select id="provider-filter" value={filters.provider} on:change={(event) => setFilter("provider", event.currentTarget.value)}>
              <option value="">Todos</option>
              {#each providerOptions as value}<option value={value}>{value}</option>{/each}
            </select>
          </label>
          <label class="catalog-explorer-filter-extra">
            <span>Stock</span>
            <select id="stock-filter" value={filters.stock} on:change={(event) => setFilter("stock", event.currentTarget.value)}>
              <option value="all">Todos</option>
              <option value="in_stock">Con stock</option>
              <option value="out_of_stock">Sin stock</option>
              <option value="unknown">A consultar</option>
            </select>
          </label>
        </section>

        <header class="catalog-explorer-result-meta">
          <div>
            <strong>{filteredProducts.length} opciones en {selectedMaterial}</strong>
            <span>Actualizado {formatDate(generatedAt)}</span>
          </div>
          <div>
            {#if selectedColor || secondaryFilterCount}<button type="button" on:click={clearSecondaryFilters}>Limpiar filtros</button>{/if}
            <label>
              <span>Ordenar por</span>
              <select value={sortOrder} on:change={(event) => sortOrder = event.currentTarget.value}>
                <option value="popular">Popularidad</option>
                <option value="availability">Disponibilidad total</option>
              </select>
            </label>
          </div>
        </header>

        <CatalogExplorerResults
          rows={resultRows}
          {sources}
          addFeedback={quoteAddFeedback}
          onAdd={addQuoteItem}
          onOpenPreview={openAssetPreview}
          onShowPreview={showAssetPreview}
          onMovePreview={movePreview}
          onHidePreview={hideHoverPreview}
        />
      </div>

      <aside class="catalog-quote-rail" aria-label="Espacio de cotización">
        <QuoteListPanel
          items={quoteState.items}
          {products}
          {sources}
          showQuickControls={quoteState.settings.showQuickControls}
          storageWarning={quoteState.storageWarning}
          reconcileNotice={quoteState.reconcileNotice}
          onToggleControls={() => quoteWorkspace?.toggleQuickControls()}
          onSetQuantity={(productId, quantity) => quoteWorkspace?.setQuantity(productId, quantity)}
          onRemoveItem={(productId) => quoteWorkspace?.removeProduct(productId)}
          onClearList={clearQuoteList}
          onExportList={exportQuoteList}
          onImportList={openQuoteImportPicker}
        />
      </aside>
    </div>
  {/if}
</main>

{#if compactQuoteMode && quoteState.items.length}
  <button class="quote-floating-button catalog-quote-mobile-trigger" type="button" aria-label={`Abrir lista de cotización con ${quoteState.items.length} item(s)`} on:click={() => quoteDrawerOpen = true}>
    Lista de cotización <span>{quoteState.items.length}</span>
  </button>
{/if}

<QuoteListDrawer
  open={compactQuoteMode && quoteDrawerOpen && quoteState.items.length > 0}
  items={quoteState.items}
  {products}
  {sources}
  showQuickControls={quoteState.settings.showQuickControls}
  storageWarning={quoteState.storageWarning}
  reconcileNotice={quoteState.reconcileNotice}
  onClose={() => quoteDrawerOpen = false}
  onToggleControls={() => quoteWorkspace?.toggleQuickControls()}
  onSetQuantity={(productId, quantity) => quoteWorkspace?.setQuantity(productId, quantity)}
  onRemoveItem={(productId) => quoteWorkspace?.removeProduct(productId)}
  onClearList={clearQuoteList}
  onExportList={exportQuoteList}
  onImportList={openQuoteImportPicker}
  handleQuoteDrawerKeydown={handleWindowKeydown}
/>

<input class="quote-import-input" type="file" accept=".json,application/json" bind:this={quoteImportInput} on:change={handleQuoteImportFile}>

{#if quoteImportPreview || quoteImportError}
  <div class="quote-import-backdrop" role="presentation" on:click={(event) => event.target === event.currentTarget && closeQuoteImport()}>
    <div class="quote-import-dialog" role="dialog" aria-modal="true" aria-labelledby="quote-import-title" tabindex="-1">
      <button class="quote-import-close" type="button" aria-label="Cerrar importación" on:click={closeQuoteImport}>×</button>
      <h2 id="quote-import-title">Importar lista</h2>
      <small>{quoteImportFileName}</small>
      {#if quoteImportError}
        <p class="quote-import-error" aria-live="polite">{quoteImportError}</p>
        <button class="soft-button" type="button" on:click={openQuoteImportPicker}>Elegir otro archivo</button>
      {:else}
        <p><strong>{quoteImportPreview.validCount}</strong> item(s) listos para importar.</p>
        {#if quoteImportPreview.skippedCount}<p>{quoteImportPreview.skippedCount} item(s) se descartarán.</p>{/if}
        <div class="quote-import-actions">
          <button class="primary-button" type="button" on:click={() => applyQuoteImport("combine")}>Combinar</button>
          <button class="soft-button" type="button" on:click={() => applyQuoteImport("replace")}>Reemplazar</button>
        </div>
      {/if}
    </div>
  </div>
{/if}

<SiteFooter {sources} {contactContext} />

<svelte:window on:keydown={handleWindowKeydown} />

{#if preview && preview.modal}
  <div class="image-preview-backdrop" role="presentation" on:click={(event) => event.target === event.currentTarget && (preview = null)}>
    <div class="image-preview-modal" role="dialog" aria-modal="true" aria-label={preview.title}>
      <button class="image-preview-close" type="button" aria-label="Cerrar imagen ampliada" on:click={() => preview = null}>×</button>
      <img src={preview.src} alt={preview.title}>
      <strong>{preview.title}</strong>
      <span>{preview.meta}</span>
    </div>
  </div>
{:else if preview}
  <div class="image-preview visible" style={`left:${preview.x}px; top:${preview.y}px;`}>
    <img src={preview.src} alt={preview.title}>
    <span>{preview.title}</span>
  </div>
{/if}
