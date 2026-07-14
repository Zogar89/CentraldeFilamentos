<script>
  import { onDestroy, onMount } from "svelte";
  import QuickLines from "./components/QuickLines.svelte";
  import QuoteListDrawer from "./components/QuoteListDrawer.svelte";
  import QuoteListPanel from "./components/QuoteListPanel.svelte";
  import SiteHeader from "./components/SiteHeader.svelte";
  import SiteFooter from "./components/SiteFooter.svelte";
  import { createQuoteWorkspace } from "./lib/quoteWorkspace.js";
  import { createStockWatchWorkspace } from "./lib/stockWatchWorkspace.js";
  import { buildSummaryRows, summaryProductImage } from "./lib/summaryRows.js";
  import {
    brandRank,
    colorSwatchStyle,
    dataUrl,
    fetchJson,
    formatDate,
    finishLabel,
    formatInteger,
    formatPresentation,
    lineLabel,
    lineRank,
    lineVariantDisambiguator,
    matchesSearchTerms,
    productBaseName,
    slugText,
    stockDelta,
    subrangeLabel,
    zoneOrder,
  } from "./lib/shared.js";

  let products = [];
  let sources = [];
  let rows = [];
  let generatedAt = "";
  let query = "";
  let categoryOrder = "popular";
  let lineHelp = "";
  let stockAlerts = [];
  let quoteItems = [];
  let quoteSettings = { showQuickControls: true };
  let quoteStorageWarning = "";
  let quoteReconcileNotice = "";
  let quoteDrawerOpen = false;
  let quoteListReadOnly = false;
  let quoteImportInput;
  let quoteImportPreview = null;
  let quoteImportError = "";
  let quoteImportFileName = "";
  let quoteImportRequestId = 0;
  let quoteAddFeedback = {};
  let quoteFeedbackMessage = "";
  let quotePulseKey = 0;
  let quoteWorkspace = null;
  let stockWatchWorkspace = null;
  let unsubscribeQuoteWorkspace = () => {};
  let unsubscribeStockWatchWorkspace = () => {};
  let componentActive = true;
  const quoteFeedbackTimers = new Map();
  const exportCleanupTimers = new Set();
  const exportObjectUrls = new Set();
  const quoteStorageWarningCopy = "No pudimos guardar la lista en este navegador. La podes usar durante esta sesion, pero se puede perder al cerrar la pagina.";
  const quoteCatalogWarningCopy = "No pudimos actualizar el catalogo; conservamos tu lista guardada.";
  const quoteSchemaWarningCopy = "La lista guardada usa una version mas nueva. La conservamos sin cambios para no perder datos.";

  onMount(async () => {
    const payload = await fetchJson("data/stock.json", null);
    if (!componentActive) return;
    const catalogResult = payload && Array.isArray(payload.products)
      ? { ok: true, products: payload.products }
      : { ok: false, products: [] };
    products = catalogResult.products;
    sources = [...(Array.isArray(payload?.sources) ? payload.sources : [])].sort((a, b) => (zoneOrder[a.zone] ?? 99) - (zoneOrder[b.zone] ?? 99) || a.name.localeCompare(b.name, "es-AR"));
    generatedAt = payload?.generated_at || "";
    rows = buildRows();

    quoteWorkspace = createQuoteWorkspace({ products, catalogAvailable: catalogResult.ok });
    unsubscribeQuoteWorkspace = quoteWorkspace.state.subscribe((state) => {
      quoteItems = state.items;
      quoteSettings = state.settings;
      quoteListReadOnly = state.readOnly;
      quoteReconcileNotice = state.reconcileNotice.replace("catálogo", "catalogo");
      quoteStorageWarning = state.readOnly
        ? quoteSchemaWarningCopy
        : (!catalogResult.ok ? quoteCatalogWarningCopy : (state.storageWarning ? quoteStorageWarningCopy : ""));
      if (!quoteItems.length) closeQuoteDrawer();
    });

    stockWatchWorkspace = createStockWatchWorkspace({ products });
    unsubscribeStockWatchWorkspace = stockWatchWorkspace.state.subscribe((state) => {
      stockAlerts = state.alerts;
    });
  });

  onDestroy(() => {
    componentActive = false;
    invalidateQuoteImportRequest();
    unsubscribeQuoteWorkspace();
    unsubscribeStockWatchWorkspace();
    quoteFeedbackTimers.forEach((timer) => window.clearTimeout(timer));
    exportCleanupTimers.forEach((timer) => window.clearTimeout(timer));
    exportObjectUrls.forEach((url) => URL.revokeObjectURL(url));
    exportCleanupTimers.clear();
    exportObjectUrls.clear();
  });

  $: visibleRows = (query, rows.filter(matchesQuery));
  $: providerTotals = totalsForRows(visibleRows);
  $: grandTotal = Object.values(providerTotals).reduce((sum, value) => sum + value, 0);
  $: groupedRows = (categoryOrder, groupRows(visibleRows));
  $: materialSections = groupMaterialSections(groupedRows);
  $: availableLines = (products, [...new Set(products.map(lineLabel).filter(Boolean))]);

  function buildRows() {
    return buildSummaryRows(products, sources).sort((a, b) => compareProducts(a.product, b.product));
  }

  function totalsForRows(items) {
    const totals = Object.fromEntries(sources.map((source) => [source.id, 0]));
    items.forEach((row) => {
      sources.forEach((source) => {
        totals[source.id] += row.cells[source.id]?.units || 0;
      });
    });
    return totals;
  }

  function groupRows(items) {
    const groups = new Map();
    items.forEach((row) => {
      const key = groupKey(row.product);
      if (!groups.has(key)) {
        groups.set(key, {
          key,
          title: groupTitle(row.product),
          material: row.product.material || "Sin clasificar",
          subrange: subrangeLabel(row.product),
          finish: finishLabel(row.product),
          brand: row.product.brand || "Sin marca",
          diameter: row.product.diameter_mm ? `${row.product.diameter_mm} mm` : "Sin diámetro",
          line: lineLabel(row.product),
          rows: [],
          totals: Object.fromEntries(sources.map((source) => [source.id, 0])),
          total: 0,
        });
      }
      const group = groups.get(key);
      group.rows.push(row);
      sources.forEach((source) => {
        group.totals[source.id] += row.cells[source.id]?.units || 0;
      });
      group.total += row.total;
    });
    return [...groups.values()].sort(compareGroups);
  }

  function groupKey(product) {
    return [
      product.material || "Sin clasificar",
      subrangeLabel(product),
      finishLabel(product),
      brandRank(product.brand),
      product.brand || "Sin marca",
      product.diameter_mm ? `${product.diameter_mm} mm` : "Sin diámetro",
      lineLabel(product),
      product.variant || "",
    ].join("||");
  }

  function groupTitle(product) {
    const compactLine = lineLabel(product);
    const variantDisambiguator = lineVariantDisambiguator(product);
    if (product.material === "PLA") {
      const presentationContext = variantDisambiguator ? compactLine : (compactLine === "Sampler / lápiz 3D" ? compactLine : "");
      return [variantDisambiguator || subrangeLabel(product), presentationContext, product.brand || "Sin marca", product.diameter_mm ? `${product.diameter_mm} mm` : "Sin diámetro"].filter(Boolean).join(" · ");
    }
    return [product.brand || "Sin marca", product.diameter_mm ? `${product.diameter_mm} mm` : "Sin diámetro", compactLine, variantDisambiguator].filter(Boolean).join(" · ");
  }

  function groupMaterialSections(groups) {
    const sections = new Map();
    groups.forEach((group) => {
      if (!sections.has(group.material)) {
        sections.set(group.material, { material: group.material, groups: [] });
      }
      sections.get(group.material).groups.push(group);
    });
    return [...sections.values()];
  }

  function compareGroups(left, right) {
    if (categoryOrder === "alpha") return left.title.localeCompare(right.title, "es-AR");
    return lineRank(left.line) - lineRank(right.line)
      || brandRank(left.brand).localeCompare(brandRank(right.brand), "es-AR")
      || left.diameter.localeCompare(right.diameter, "es-AR")
      || left.title.localeCompare(right.title, "es-AR");
  }

  function compareProducts(left, right) {
    return [
      brandRank(left.brand), left.brand || "", left.diameter_mm ? `${left.diameter_mm} mm` : "Sin diámetro", lineLabel(left), left.color || "", left.display_name,
    ].join(" ").localeCompare([
      brandRank(right.brand), right.brand || "", right.diameter_mm ? `${right.diameter_mm} mm` : "Sin diámetro", lineLabel(right), right.color || "", right.display_name,
    ].join(" "), "es-AR");
  }

  function matchesQuery(row) {
    if (!query) return true;
    return matchesSearchTerms(query.toLowerCase().trim(), [row.product.display_name, row.product.material, row.product.variant, row.product.subrange, row.product.finish, row.product.color, row.product.pantone, row.product.brand]);
  }

  function productSummaryName(product) {
    if (product.color && product.color !== "Sin color") return product.color;
    const repeatedParts = [product.brand, product.diameter_mm ? `${product.diameter_mm} mm` : "", formatPresentation(product), lineLabel(product), product.material].filter(Boolean);
    return repeatedParts.reduce((name, part) => name.replace(part, "").replace(/\s+/g, " ").trim(), product.display_name) || product.display_name;
  }

  function summaryGroupTargetId(group) {
    return `resumen-linea-${slugText(group.key)}`;
  }

  function assetPath(path) {
    if (!path || /^https?:\/\//.test(path)) return path;
    return dataUrl(path);
  }

  function isSubscribed(product, offer) {
    return stockWatchWorkspace?.isSubscribed(product, offer) || false;
  }

  function toggleStockSubscription(product, offer) {
    if (!stockWatchWorkspace) return;
    stockWatchWorkspace.toggle(product, offer);
  }

  function stockWatchTargetId(product, offer) {
    return `stock-watch-${slugText([product.id, offer.source_id || offer.provider_name].join(" "))}`;
  }

  function dismissStockAlerts() {
    stockWatchWorkspace?.dismissAlerts();
  }

  function addQuoteItem(product) {
    if (!quoteWorkspace || quoteListReadOnly) return;
    quoteWorkspace.addProduct(product);
    const quantity = quoteItems.find((item) => item.productId === product.id)?.quantity;
    if (!quantity) return;
    window.clearTimeout(quoteFeedbackTimers.get(product.id));
    quoteAddFeedback = { ...quoteAddFeedback, [product.id]: quantity };
    quoteFeedbackMessage = `${productBaseName(product)} agregado. ${quantity} unidad(es) en la lista.`;
    quotePulseKey += 1;
    quoteFeedbackTimers.set(product.id, window.setTimeout(() => {
      const nextFeedback = { ...quoteAddFeedback };
      delete nextFeedback[product.id];
      quoteAddFeedback = nextFeedback;
      quoteFeedbackTimers.delete(product.id);
    }, 850));
  }

  function pulseQuoteList(message) {
    quotePulseKey += 1;
    quoteFeedbackMessage = message;
  }

  function setQuoteItemQuantity(productId, quantity) {
    if (!quoteWorkspace || quoteListReadOnly) return;
    quoteWorkspace.setQuantity(productId, quantity);
    const nextQuantity = quoteItems.find((item) => item.productId === productId)?.quantity || 1;
    pulseQuoteList(`Cantidad actualizada a ${nextQuantity} unidad(es).`);
  }

  function removeQuoteItem(productId) {
    if (!quoteWorkspace || quoteListReadOnly) return;
    quoteWorkspace.removeProduct(productId);
    pulseQuoteList("Producto quitado de la lista.");
  }

  function clearQuoteList() {
    if (!quoteWorkspace || quoteListReadOnly) return;
    if (!window.confirm("¿Vaciar la lista de cotizacion? Se quitaran todos los filamentos guardados en este navegador.")) return;
    quoteWorkspace.clear();
  }

  function toggleQuoteControls() {
    if (!quoteWorkspace || quoteListReadOnly) return;
    quoteWorkspace.toggleQuickControls();
  }

  function exportQuoteList() {
    if (!quoteItems.length || quoteListReadOnly || !quoteWorkspace) return;
    const blob = new Blob([quoteWorkspace.exportJson()], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `stockcentral-lista-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.append(link);
    link.click();
    link.remove();
    exportObjectUrls.add(url);
    const cleanupTimer = window.setTimeout(() => {
      URL.revokeObjectURL(url);
      exportObjectUrls.delete(url);
      exportCleanupTimers.delete(cleanupTimer);
    }, 0);
    exportCleanupTimers.add(cleanupTimer);
  }

  function openQuoteImportPicker() {
    if (quoteListReadOnly || !quoteWorkspace) {
      quoteImportPreview = null;
      quoteImportFileName = "";
      quoteImportError = quoteListReadOnly
        ? quoteSchemaWarningCopy
        : "Todavia estamos cargando tu lista. Intenta nuevamente en unos segundos.";
      return;
    }
    quoteImportError = "";
    quoteImportInput?.click();
  }

  async function handleQuoteImportFile(event) {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = "";
    if (!file) return;
    const requestId = beginQuoteImportRequest();
    quoteImportPreview = null;
    quoteImportError = "";
    quoteImportFileName = file.name;
    if (quoteListReadOnly || !quoteWorkspace) {
      if (isCurrentQuoteImportRequest(requestId)) {
        quoteImportError = quoteListReadOnly
          ? quoteSchemaWarningCopy
          : "Todavia estamos cargando tu lista. Intenta nuevamente en unos segundos.";
      }
      return;
    }
    if (file.size > 2_000_000) {
      quoteImportError = "El archivo es demasiado grande para una lista de cotizacion.";
      return;
    }
    try {
      const fileText = await file.text();
      if (!isCurrentQuoteImportRequest(requestId)) return;
      const previewResult = quoteWorkspace.previewImport(fileText);
      if (!isCurrentQuoteImportRequest(requestId)) return;
      if (!previewResult.ok) {
        quoteImportError = previewResult.error;
        return;
      }
      quoteImportPreview = previewResult;
    } catch {
      if (!isCurrentQuoteImportRequest(requestId)) return;
      quoteImportError = "No pudimos leer ese archivo. Elegi nuevamente la lista exportada.";
    }
  }

  function applyQuoteImport(mode) {
    if (!quoteImportPreview || quoteListReadOnly || !quoteWorkspace) {
      quoteImportError = quoteSchemaWarningCopy;
      return;
    }
    quoteWorkspace.applyImport(quoteImportPreview, mode);
    closeQuoteImport();
  }

  function closeQuoteImport() {
    invalidateQuoteImportRequest();
    quoteImportPreview = null;
    quoteImportError = "";
    quoteImportFileName = "";
  }

  function beginQuoteImportRequest() {
    quoteImportRequestId += 1;
    return quoteImportRequestId;
  }

  function invalidateQuoteImportRequest() {
    quoteImportRequestId += 1;
  }

  function isCurrentQuoteImportRequest(requestId) {
    return componentActive && requestId === quoteImportRequestId;
  }

  function openQuoteDrawer() {
    if (quoteItems.length) quoteDrawerOpen = true;
  }

  function closeQuoteDrawer() {
    quoteDrawerOpen = false;
  }

  function handleQuoteDrawerKeydown(event) {
    if (event.key === "Escape" && (quoteImportPreview || quoteImportError)) {
      closeQuoteImport();
      return;
    }
    if (event.key === "Escape" && quoteDrawerOpen) closeQuoteDrawer();
  }

</script>

<main id="main-content" class="shell" tabindex="-1">
  <SiteHeader active="summary" updatedAt={generatedAt} subtitle="Resumen por proveedor" {stockAlerts} onDismissStockAlerts={dismissStockAlerts} />

  <section class="status-strip">
    <span id="summary-updated">Última actualización: {formatDate(generatedAt)}</span>
    <div class="category-sort" role="group" aria-label="Orden de categorías">
      <strong id="summary-count">{visibleRows.length} filamentos</strong>
      <span>Orden</span>
      <button id="summary-sort-popular" class="soft-button" class:active={categoryOrder === "popular"} type="button" data-category-order="popular" on:click={() => categoryOrder = "popular"}>Popularidad</button>
      <button id="summary-sort-alpha" class="soft-button" class:active={categoryOrder === "alpha"} type="button" data-category-order="alpha" on:click={() => categoryOrder = "alpha"}>A-Z</button>
    </div>
    <div class="quote-import-entry">
      <button class="soft-button" type="button" disabled={!quoteWorkspace || quoteListReadOnly} on:click={openQuoteImportPicker}>Importar lista</button>
      <button type="button" class="quote-import-help-tip" aria-label="Importa una lista exportada para recuperarla o llevarla desde otra PC o navegador." data-tooltip="Importa una lista exportada para recuperarla o llevarla desde otra PC o navegador.">?</button>
    </div>
  </section>

  {#if quoteListReadOnly}
    <p class="quote-list-warning summary-read-only-warning" aria-live="polite">{quoteSchemaWarningCopy}</p>
  {/if}

  <section class="filters" aria-label="Filtros">
    <label class="search-field">
      <span>Buscar</span>
      <input id="summary-search" type="search" bind:value={query} placeholder="Filamento, color, marca...">
    </label>
  </section>

  <section class="quick-lines-shell" aria-label="Líneas populares">
    <QuickLines id="summary-quick-lines" available={availableLines} bind:help={lineHelp} targetSelector=".summary-group-row" />
    <p id="summary-line-help" class="line-help">{lineHelp}</p>
  </section>

  <div class:quote-list-layout-active={quoteItems.length > 0} class="summary-action-layout">
    <div class="table-shell summary-table-region">
      <table id="summary-table" class="summary-table">
      <thead>
        <tr>
          <th>Filamento</th>
          <th class="summary-presentation">Presentación</th>
          {#each sources as source}
            <th><a href={source.homepage_url} target="_blank" rel="noopener" title={`${formatInteger(source.stats?.total_stock_units ?? 0)} carretes`}>{source.name}</a></th>
          {/each}
          <th class="summary-total">Total</th>
        </tr>
      </thead>
      <tbody>
        {#each materialSections as section}
          <tr class="summary-material-row">
            <th colspan={sources.length + 3}><h2>{section.material}</h2></th>
          </tr>
          {#each section.groups as group}
            <tr class="summary-group-row" id={summaryGroupTargetId(group)} data-line={group.line}>
              <th>
                <span class="summary-group-heading">
                  <h3>{group.title}</h3>
                  {#if group.finish}<small class="summary-group-finish">{group.finish}</small>{/if}
                </span>
                <span class="summary-mobile-totals" aria-hidden="true">
                  {#each sources as source}<span><b>{source.name}</b> {formatInteger(group.totals[source.id])}</span>{/each}
                  <span class="summary-mobile-total"><b>Total</b> {formatInteger(group.total)}</span>
                </span>
              </th>
              <td class="summary-presentation" data-label="Presentación"></td>
              {#each sources as source}<td data-label={source.name}>{formatInteger(group.totals[source.id])}</td>{/each}
              <td class="summary-total" data-label="Total">{formatInteger(group.total)}</td>
            </tr>
            {#each group.rows as row}
              <tr>
                <th>
                  <span class="summary-product">
                    {#if summaryProductImage(row.product)}
                      <img class="summary-product-thumbnail" src={assetPath(summaryProductImage(row.product))} alt={row.product.display_name || productSummaryName(row.product)} width="42" height="42" loading="lazy">
                    {/if}
                    <span class="summary-color-swatch" style={colorSwatchStyle(row.product)} title={[row.product.color || "Sin color", row.product.pantone].filter(Boolean).join(" · ")} aria-label={[row.product.color || "Sin color", row.product.pantone].filter(Boolean).join(" · ")}></span>
                    <span class="summary-product-name">
                      {#if row.product.manufacturer_product_url}
                        <a href={row.product.manufacturer_product_url} target="_blank" rel="noopener">{productSummaryName(row.product)}</a>
                      {:else}
                        {productSummaryName(row.product)}
                      {/if}
                      {#if row.product.sku || row.product.ean || row.product.pantone}
                        <small class="summary-official-metadata">
                          {#if row.product.sku}<span>SKU {row.product.sku}</span>{/if}
                          {#if row.product.ean}<span>EAN {row.product.ean}</span>{/if}
                          {#if row.product.pantone}<span>{row.product.pantone}</span>{/if}
                        </small>
                      {/if}
                    </span>
                    <button
                      class="quote-summary-add"
                      class:confirmed={quoteAddFeedback[row.product.id]}
                      type="button"
                      disabled={!quoteWorkspace || quoteListReadOnly}
                      aria-label={`Agregar ${row.product.display_name || productSummaryName(row.product)} a la lista de cotizacion`}
                      on:click={() => addQuoteItem(row.product)}
                    >{quoteAddFeedback[row.product.id] ? quoteAddFeedback[row.product.id] : "+1"}</button>
                  </span>
                </th>
                <td class="summary-presentation" data-label="Presentación">{formatPresentation(row.product)}</td>
                {#each sources as source}
                  {@const cell = row.cells[source.id]}
                  <td
                    id={cell?.offer ? stockWatchTargetId(row.product, cell.offer) : undefined}
                    class={cell?.units > 0 ? "stock-in" : (cell?.unknown ? "stock-unknown" : "stock-out")}
                    data-label={source.name}
                  >
                    <span class="summary-cell-value">{cell?.unknown && !cell?.units ? "—" : formatInteger(cell?.units || 0)}</span>
                    {#if cell?.offer}
                      <button
                        class="summary-stock-watch"
                        class:active={isSubscribed(row.product, cell.offer)}
                        type="button"
                        aria-pressed={isSubscribed(row.product, cell.offer)}
                        aria-label={`${isSubscribed(row.product, cell.offer) ? "Dejar de seguir" : "Avisarme por"} ${row.product.display_name || productSummaryName(row.product)} en ${cell.offer.provider_name || source.name}`}
                        on:click={() => toggleStockSubscription(row.product, cell.offer)}
                      >
                        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"></path><path d="M10 21h4"></path></svg>
                      </button>
                    {/if}
                  </td>
                {/each}
                <td class="summary-total" data-label="Total">{formatInteger(row.total)}</td>
              </tr>
            {/each}
          {/each}
        {/each}
      </tbody>
      <tfoot>
        <tr>
          <th>Carretes por proveedor</th>
          <td class="summary-presentation" data-label="Presentación"></td>
          {#each sources as source}<td class="summary-total" data-label={source.name}>{formatInteger(providerTotals[source.id])}</td>{/each}
          <td class="summary-total" data-label="Total">{formatInteger(grandTotal)}</td>
        </tr>
      </tfoot>
      </table>
    </div>

    {#if quoteItems.length > 0}
      <div class="quote-list-side-panel">
        <QuoteListPanel
          items={quoteItems}
          {products}
          {sources}
          showQuickControls={quoteSettings.showQuickControls}
          storageWarning={quoteStorageWarning}
          reconcileNotice={quoteReconcileNotice}
          readOnly={quoteListReadOnly}
          onToggleControls={toggleQuoteControls}
          onSetQuantity={setQuoteItemQuantity}
          onRemoveItem={removeQuoteItem}
          onClearList={clearQuoteList}
          onExportList={exportQuoteList}
          onImportList={openQuoteImportPicker}
        />
      </div>
    {/if}
  </div>

  <p class="visually-hidden" aria-live="polite">{quoteFeedbackMessage}</p>
</main>

{#if quoteItems.length > 0}
  <button class="quote-floating-button" type="button" aria-label={`Abrir lista de cotizacion con ${quoteItems.length} item(s)`} on:click={openQuoteDrawer}>
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 6h11"></path><path d="M8 12h11"></path><path d="M8 18h11"></path><path d="m3 6 1 1 2-2"></path><path d="m3 12 1 1 2-2"></path><path d="m3 18 1 1 2-2"></path></svg>
    {#key quotePulseKey}<span class="quote-floating-count">{quoteItems.length}</span>{/key}
  </button>
{/if}

<QuoteListDrawer
  open={quoteDrawerOpen && quoteItems.length > 0}
  items={quoteItems}
  {products}
  {sources}
  showQuickControls={quoteSettings.showQuickControls}
  storageWarning={quoteStorageWarning}
  reconcileNotice={quoteReconcileNotice}
  readOnly={quoteListReadOnly}
  onClose={closeQuoteDrawer}
  onToggleControls={toggleQuoteControls}
  onSetQuantity={setQuoteItemQuantity}
  onRemoveItem={removeQuoteItem}
  onClearList={clearQuoteList}
  onExportList={exportQuoteList}
  onImportList={openQuoteImportPicker}
  {handleQuoteDrawerKeydown}
/>

<input class="quote-import-input" type="file" disabled={quoteListReadOnly || !quoteWorkspace} accept=".json,application/json" bind:this={quoteImportInput} on:change={handleQuoteImportFile}>

{#if quoteImportPreview || quoteImportError}
  <div class="quote-import-backdrop" role="presentation" on:click={(event) => event.target === event.currentTarget && closeQuoteImport()}>
    <div class="quote-import-dialog" role="dialog" aria-modal="true" aria-labelledby="summary-quote-import-title" tabindex="-1">
      <button class="quote-import-close" type="button" aria-label="Cerrar importacion" on:click={closeQuoteImport}>×</button>
      <h2 id="summary-quote-import-title">Importar lista</h2>
      <small>{quoteImportFileName}</small>
      {#if quoteImportError}
        <p class="quote-import-error" aria-live="polite">{quoteImportError}</p>
        <button class="soft-button" type="button" disabled={quoteListReadOnly || !quoteWorkspace} on:click={openQuoteImportPicker}>Elegir otro archivo</button>
      {:else}
        <p><strong>{quoteImportPreview.validCount}</strong> item(s) listos para importar.</p>
        {#if quoteImportPreview.skippedCount}<p>{quoteImportPreview.skippedCount} item(s) se descartaran porque no son validos o ya no existen.</p>{/if}
        <p class="quote-import-help">Combinar conserva tus otros items; si un producto se repite, usa la cantidad importada.</p>
        <div class="quote-import-actions">
          <button class="primary-button" type="button" disabled={quoteListReadOnly} on:click={() => applyQuoteImport("combine")}>Combinar</button>
          <button class="soft-button" type="button" disabled={quoteListReadOnly} on:click={() => applyQuoteImport("replace")}>Reemplazar</button>
        </div>
      {/if}
    </div>
  </div>
{/if}

<SiteFooter sources={sources} contactContext={query ? `"${query}"` : ""} />
