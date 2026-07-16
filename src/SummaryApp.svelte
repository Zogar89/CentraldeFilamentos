<script>
  import { onDestroy, onMount } from "svelte";
  import QuickLines from "./components/QuickLines.svelte";
  import QuoteListDrawer from "./components/QuoteListDrawer.svelte";
  import SiteHeader from "./components/SiteHeader.svelte";
  import SiteFooter from "./components/SiteFooter.svelte";
  import {
    clampQuoteQuantity,
    combineQuoteListItems,
    initializeQuoteList,
    loadQuoteList,
    previewQuoteListImport,
    saveQuoteList,
    serializeQuoteListExport,
    snapshotQuoteItem,
  } from "./lib/quoteList.js";
  import {
    loadStockSubscriptions,
    saveStockSubscriptions,
    stockSignature,
    subscriptionKey,
  } from "./lib/stockSubscriptions.js";
  import {
    brandRank,
    colorSwatchLabel,
    colorSwatchStyle,
    comparePresentations,
    dataUrl,
    diameterLabel,
    fetchJson,
    formatDate,
    formatInteger,
    formatPresentation,
    formatWeightLabel,
    lineLabel,
    lineMeta,
    lineOptionLabel,
    lineRank,
    materialSwatchAlt,
    matchesSearchTerms,
    pantoneSwatchLabel,
    productBaseName,
    providerAnchorId,
    slugText,
  } from "./lib/shared.js";

  let filters = {
    query: "",
    material: "",
    variant: "",
    color: "",
    diameter: "",
    weight: "",
    brand: "",
    provider: "",
    stock: "all",
  };
  let showMoreFilters = false;

  let products = [];
  let sources = [];
  let generatedAt = "";
  let categoryOrder = "popular";
  let lineHelp = "";
  let preview = null;
  let stockSubscriptions = [];
  let stockAlerts = [];
  let stockWatchEnabled = false;
  let quoteItems = [];
  let quoteSettings = { showQuickControls: true };
  let quoteStorageWarning = "";
  let quoteReconcileNotice = "";
  let quoteDrawerOpen = false;
  let quoteListReadOnly = false;
  let preservedQuotePayload = null;
  let quoteImportInput;
  let quoteImportPreview = null;
  let quoteImportError = "";
  let quoteImportFileName = "";
  let quoteAddFeedback = {};
  let quoteFeedbackMessage = "";
  let quotePulseKey = 0;
  const quoteFeedbackTimers = new Map();
  let stockWatchFeedback = {};
  const stockWatchFeedbackTimers = new Map();
  const quoteStorageWarningCopy = "No pudimos guardar la lista en este navegador. La podes usar durante esta sesion, pero se puede perder al cerrar la pagina.";
  const quoteCatalogWarningCopy = "No pudimos actualizar el catalogo; conservamos tu lista guardada.";
  const quoteSchemaWarningCopy = "La lista guardada usa una version mas nueva. La conservamos sin cambios para no perder datos.";
  const quoteRemovedNoticeTemplate = "Quitamos {count} item(s) que ya no aparecen en el catalogo publicado.";

  onMount(async () => {
    const [payload, featureFlags] = await Promise.all([
      fetchJson("data/stock.json", null),
      fetchJson("data/feature_flags.json", {}),
    ]);
    const catalogResult = payload && Array.isArray(payload.products)
      ? { ok: true, products: payload.products }
      : { ok: false, products: [] };
    products = catalogResult.products;
    sources = Array.isArray(payload?.sources) ? payload.sources : [];
    generatedAt = payload?.generated_at || "";
    stockWatchEnabled = featureFlags.stockWatchEnabled === true;
    if (stockWatchEnabled) {
      stockSubscriptions = loadStockSubscriptions();
      reconcileStockSubscriptions();
    }
    const quoteList = loadQuoteList();
    quoteListReadOnly = quoteList.readOnly;
    preservedQuotePayload = quoteList.preservedPayload;
    quoteSettings = quoteList.settings;
    const reconciledQuoteList = initializeQuoteList(quoteList, catalogResult);
    quoteItems = reconciledQuoteList.items;
    quoteReconcileNotice = reconciledQuoteList.removedCount
      ? quoteRemovedNoticeTemplate.replace("{count}", reconciledQuoteList.removedCount)
      : "";
    quoteStorageWarning = catalogResult.ok
      ? (quoteList.storageAvailable ? "" : quoteStorageWarningCopy)
      : quoteCatalogWarningCopy;
    if (quoteListReadOnly) quoteStorageWarning = quoteSchemaWarningCopy;
    if (reconciledQuoteList.shouldSave) {
      saveQuoteListState(quoteItems, quoteSettings);
    }
  });

  onDestroy(() => {
    quoteFeedbackTimers.forEach((timer) => window.clearTimeout(timer));
    stockWatchFeedbackTimers.forEach((timer) => window.clearTimeout(timer));
  });

  $: subscribedKeys = new Set(stockSubscriptions.map((item) => item.key));
  $: filteredProducts = (filters, categoryOrder, products.filter(matchesFilters).sort(compareProducts));
  $: groups = (categoryOrder, groupProducts(filteredProducts));
  $: lineOptions = (products, lineValues());
  $: availableLines = (products, lineValues());
  $: materialOptions = (products, valuesFor("material"));
  $: colorOptions = (products, valuesFor("color"));
  $: diameterOptions = (products, valuesFor("diameter_mm"));
  $: weightOptions = (products, valuesFor("weight_g"));
  $: brandOptions = (products, valuesFor("brand"));
  $: providerOptions = (products, providerValues());
  $: secondaryFilterCount = [
    filters.variant,
    filters.diameter,
    filters.weight,
    filters.brand,
    filters.stock !== "all" ? filters.stock : "",
  ].filter(Boolean).length;
  $: activeFilterChips = [
    filters.query ? { key: "query", label: `Buscar: ${filters.query}` } : null,
    filters.material ? { key: "material", label: filters.material } : null,
    filters.color ? { key: "color", label: filters.color } : null,
    filters.provider ? { key: "provider", label: filters.provider } : null,
    filters.variant ? { key: "variant", label: lineOptionLabel(filters.variant) } : null,
    filters.diameter ? { key: "diameter", label: `${filters.diameter} mm` } : null,
    filters.weight ? { key: "weight", label: formatWeightLabel(filters.weight) } : null,
    filters.brand ? { key: "brand", label: filters.brand } : null,
    filters.stock !== "all" ? {
      key: "stock",
      label: {
        in_stock: "Con stock",
        out_of_stock: "Sin stock",
        unknown: "Sin cantidad",
      }[filters.stock],
    } : null,
  ].filter(Boolean);
  $: contactContext = [
    filters.query ? `"${filters.query}"` : "",
    filters.material,
    filters.variant,
    filters.color,
    filters.diameter ? `${filters.diameter} mm` : "",
    filters.weight ? formatWeightLabel(filters.weight) : "",
    filters.brand,
  ].filter(Boolean).join(", ");

  function matchesFilters(product) {
    const queryFields = [
      product.display_name,
      product.material,
      product.variant,
      product.color,
      product.pantone,
      product.sku,
      product.ean,
      product.brand,
      ...(product.offers || []).map((offer) => offer.original_name),
    ];

    if (filters.query && !matchesSearchTerms(filters.query.toLowerCase().trim(), queryFields)) return false;
    if (filters.material && product.material !== filters.material) return false;
    if (filters.variant && lineLabel(product) !== filters.variant) return false;
    if (filters.color && product.color !== filters.color) return false;
    if (filters.diameter && String(product.diameter_mm) !== filters.diameter) return false;
    if (filters.weight && String(product.weight_g) !== filters.weight) return false;
    if (filters.brand && product.brand !== filters.brand) return false;
    if (filters.provider && !(product.offers || []).some((offer) => offer.provider_name === filters.provider)) return false;
    if (filters.stock !== "all" && !(product.offers || []).some((offer) => offer.stock_status === filters.stock)) return false;
    return true;
  }

  function setFilter(name, value) {
    filters = { ...filters, [name]: value };
  }

  function setVariantFilter(value) {
    setFilter("variant", value);
    lineHelp = value ? (lineMeta[value]?.help || "") : "";
  }

  function clearFilter(name) {
    if (name === "variant") {
      setVariantFilter("");
      return;
    }
    setFilter(name, name === "stock" ? "all" : "");
  }

  function clearAllFilters() {
    filters = {
      query: "",
      material: "",
      variant: "",
      color: "",
      diameter: "",
      weight: "",
      brand: "",
      provider: "",
      stock: "all",
    };
    lineHelp = "";
    showMoreFilters = false;
  }

  function groupProducts(items) {
    const grouped = new Map();
    items.forEach((product) => {
      const key = [product.brand || "Sin marca", diameterLabel(product), lineLabel(product)].join("||");
      if (!grouped.has(key)) {
        grouped.set(key, {
          brand: product.brand || "Sin marca",
          diameter: diameterLabel(product),
          line: lineLabel(product),
          products: [],
        });
      }
      grouped.get(key).products.push(product);
    });
    return [...grouped.values()].sort(compareGroups);
  }

  function groupBaseProducts(items) {
    const cards = new Map();
    items.forEach((product) => {
      const key = [
        product.brand || "Sin marca",
        product.diameter_mm || "Sin diametro",
        lineLabel(product),
        product.material || "Sin material",
        product.variant || "",
        product.color || "Sin color",
      ].join("||");
      if (!cards.has(key)) cards.set(key, { products: [] });
      cards.get(key).products.push(product);
    });
    return [...cards.values()].map((card) => {
      card.products.sort(comparePresentations);
      return card;
    });
  }

  function compareGroups(left, right) {
    if (categoryOrder === "alpha") {
      return [left.line, left.brand, left.diameter].join(" ").localeCompare([right.line, right.brand, right.diameter].join(" "), "es-AR");
    }
    return (
      lineRank(left.line) - lineRank(right.line)
      || brandRank(left.brand).localeCompare(brandRank(right.brand), "es-AR")
      || left.diameter.localeCompare(right.diameter, "es-AR")
      || left.line.localeCompare(right.line, "es-AR")
    );
  }

  function compareProducts(left, right) {
    const groupComparison = compareProductGroups(left, right);
    if (groupComparison !== 0) return groupComparison;
    return [left.color || "", left.display_name].join(" ").localeCompare([right.color || "", right.display_name].join(" "), "es-AR");
  }

  function compareProductGroups(left, right) {
    const leftLine = lineLabel(left);
    const rightLine = lineLabel(right);
    if (categoryOrder === "alpha") {
      return [leftLine, left.brand || "", diameterLabel(left)].join(" ").localeCompare([rightLine, right.brand || "", diameterLabel(right)].join(" "), "es-AR");
    }
    return (
      lineRank(leftLine) - lineRank(rightLine)
      || brandRank(left.brand).localeCompare(brandRank(right.brand), "es-AR")
      || diameterLabel(left).localeCompare(diameterLabel(right), "es-AR")
      || leftLine.localeCompare(rightLine, "es-AR")
    );
  }

  function valuesFor(field) {
    return [...new Set(products.map((product) => product[field]).filter((value) => value !== "" && value !== null && value !== undefined))].sort();
  }

  function providerValues() {
    return [...new Set(products.flatMap((product) => (product.offers || []).map((offer) => offer.provider_name)))].sort();
  }

  function lineValues() {
    return [...new Set(products.map(lineLabel).filter(Boolean))].sort((left, right) => lineRank(left) - lineRank(right) || left.localeCompare(right, "es-AR"));
  }

  function groupTargetId(group) {
    return `linea-${slugText([group.line, group.brand, group.diameter].join(" "))}`;
  }

  function productVisual(product, cardProducts) {
    const imageProducts = cardProducts.filter((item) => item.image_url).sort(compareImagePresentations);
    return imageProducts.length ? imageProducts[0] : product;
  }

  function compareImagePresentations(left, right) {
    return imagePresentationRank(left) - imagePresentationRank(right) || comparePresentations(left, right);
  }

  function imagePresentationRank(product) {
    if (Number(product.weight_g) === 1000) return 0;
    if (Number(product.weight_g) === 2500) return 1;
    return 2;
  }

  function assetPath(path) {
    if (!path || /^https?:\/\//.test(path)) return path;
    return dataUrl(path);
  }

  function showPreview(event, product) {
    if (!product.image_url) return;
    preview = {
      src: assetPath(product.image_url),
      title: [product.color || "Sin color", product.pantone, formatPresentation(product)].filter(Boolean).join(" · "),
      x: event.clientX + 16,
      y: event.clientY + 16,
      modal: false,
    };
  }

  function movePreview(event) {
    if (!preview || preview.modal) return;
    preview = { ...preview, x: event.clientX + 16, y: event.clientY + 16 };
  }

  function hideHoverPreview() {
    if (!preview?.modal) preview = null;
  }

  function openImagePreview(product) {
    if (!product.image_url) return;
    preview = {
      src: assetPath(product.image_url),
      title: productBaseName(product),
      meta: [product.color || "Sin color", product.pantone, formatPresentation(product)].filter(Boolean).join(" · "),
      modal: true,
    };
  }

  function closePreviewBackdrop(event) {
    if (event.target === event.currentTarget) preview = null;
  }

  function handlePreviewKeydown(event) {
    if (event.key === "Escape" && preview?.modal) preview = null;
  }

  function providerTitle(offer) {
    return `${offer.provider_name} · ${offer.provider_zone}`;
  }

  function isSubscribed(product, offer) {
    return subscribedKeys.has(subscriptionKey(product, offer));
  }

  function toggleStockSubscription(product, offer) {
    const key = subscriptionKey(product, offer);
    const existing = stockSubscriptions.find((item) => item.key === key);
    if (existing) {
      stockSubscriptions = stockSubscriptions.filter((item) => item.key !== key);
      stockAlerts = stockAlerts.filter((item) => item.key !== key);
    } else {
      stockSubscriptions = [
        ...stockSubscriptions,
        {
          key,
          productId: product.id,
          sourceId: offer.source_id || offer.provider_name,
          productName: productBaseName(product),
          providerName: offer.provider_name,
          presentation: formatPresentation(product),
          subscribedAt: new Date().toISOString(),
          lastStockStatus: offer.stock_status || "unknown",
          lastStockQuantity: Number(offer.stock_quantity || 0),
          lastStockSignature: stockSignature(offer),
          acknowledgedAt: "",
        },
      ];
    }
    saveStockSubscriptions(stockSubscriptions);
    showStockWatchFeedback(key);
  }

  function showStockWatchFeedback(key) {
    window.clearTimeout(stockWatchFeedbackTimers.get(key));
    stockWatchFeedback = {
      ...stockWatchFeedback,
      [key]: Number(stockWatchFeedback[key] || 0) + 1,
    };
    stockWatchFeedbackTimers.set(key, window.setTimeout(() => {
      const nextFeedback = { ...stockWatchFeedback };
      delete nextFeedback[key];
      stockWatchFeedback = nextFeedback;
      stockWatchFeedbackTimers.delete(key);
    }, 520));
  }

  function addQuoteItem(product) {
    const existing = quoteItems.find((item) => item.productId === product.id);
    const nextQuantity = Number(existing?.quantity || 0) + 1;
    const nextItems = existing
      ? quoteItems.map((item) => item.productId === product.id ? snapshotQuoteItem(product, nextQuantity) : item)
      : [...quoteItems, snapshotQuoteItem(product, 1)];
    saveQuoteListState(nextItems);
    showQuoteAddFeedback(product, nextQuantity);
    quoteDrawerOpen = true;
  }

  function showQuoteAddFeedback(product, quantity) {
    const productId = product.id;
    window.clearTimeout(quoteFeedbackTimers.get(productId));
    quoteAddFeedback = { ...quoteAddFeedback, [productId]: quantity };
    quoteFeedbackMessage = `${productBaseName(product)} agregado. ${quantity} unidad(es) en la lista.`;
    quotePulseKey += 1;
    quoteFeedbackTimers.set(productId, window.setTimeout(() => {
      const nextFeedback = { ...quoteAddFeedback };
      delete nextFeedback[productId];
      quoteAddFeedback = nextFeedback;
      quoteFeedbackTimers.delete(productId);
    }, 850));
  }

  function pulseQuoteList(message) {
    quotePulseKey += 1;
    quoteFeedbackMessage = message;
  }

  function saveQuoteListState(nextItems, nextSettings = quoteSettings) {
    quoteItems = nextItems;
    quoteSettings = nextSettings;
    const result = saveQuoteList({
      items: quoteItems,
      settings: quoteSettings,
      readOnly: quoteListReadOnly,
      preservedPayload: preservedQuotePayload,
    });
    quoteStorageWarning = result.blocked
      ? quoteSchemaWarningCopy
      : (result.ok ? "" : quoteStorageWarningCopy);
    if (!quoteItems.length) closeQuoteDrawer();
  }

  function setQuoteItemQuantity(productId, quantity) {
    const product = products.find((item) => item.id === productId);
    const nextQuantity = clampQuoteQuantity(quantity);
    const nextItems = quoteItems.map((item) => {
      if (item.productId !== productId) return item;
      return product
        ? snapshotQuoteItem(product, nextQuantity)
        : { ...item, quantity: nextQuantity };
    });
    saveQuoteListState(nextItems);
    pulseQuoteList(`Cantidad actualizada a ${nextQuantity} unidad(es).`);
  }

  function removeQuoteItem(productId) {
    saveQuoteListState(quoteItems.filter((item) => item.productId !== productId));
    pulseQuoteList("Producto quitado de la lista.");
  }

  function clearQuoteList() {
    if (!window.confirm("¿Vaciar la lista de cotizacion? Se quitaran todos los filamentos guardados en este navegador.")) return;
    quoteReconcileNotice = "";
    saveQuoteListState([]);
  }

  function exportQuoteList() {
    if (!quoteItems.length || quoteListReadOnly) return;
    const blob = new Blob([
      serializeQuoteListExport({ items: quoteItems, settings: quoteSettings }),
    ], { type: "application/json" });
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
      quoteImportError = "El archivo es demasiado grande para una lista de cotizacion.";
      return;
    }
    const previewResult = previewQuoteListImport(await file.text(), products);
    if (!previewResult.ok) {
      quoteImportPreview = null;
      quoteImportError = previewResult.error;
      return;
    }
    quoteImportError = "";
    quoteImportPreview = previewResult;
  }

  function applyQuoteImport(mode) {
    if (!quoteImportPreview || quoteListReadOnly) {
      quoteImportError = quoteSchemaWarningCopy;
      return;
    }
    const importedItems = quoteImportPreview.items;
    const nextItems = mode === "combine"
      ? combineQuoteListItems(quoteItems, importedItems)
      : importedItems;
    const nextSettings = mode === "replace" ? quoteImportPreview.settings : quoteSettings;
    const skipped = quoteImportPreview.skippedCount;
    quoteReconcileNotice = `Importamos ${quoteImportPreview.validCount} item(s)${skipped ? ` y descartamos ${skipped}` : ""}.`;
    saveQuoteListState(nextItems, nextSettings);
    closeQuoteImport();
  }

  function closeQuoteImport() {
    quoteImportPreview = null;
    quoteImportError = "";
    quoteImportFileName = "";
  }

  function toggleQuoteControls() {
    saveQuoteListState(quoteItems, {
      ...quoteSettings,
      showQuickControls: !quoteSettings.showQuickControls,
    });
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

  function reconcileStockSubscriptions() {
    const alerts = [];
    const nextSubscriptions = stockSubscriptions.map((subscription) => {
      const match = findSubscribedOffer(subscription);
      if (!match) return subscription;

      const { product, offer } = match;
      const signature = stockSignature(offer);
      const currentQuantity = Number(offer.stock_quantity || 0);
      const previousQuantity = Number(subscription.lastStockQuantity || 0);
      const cameBack = offer.stock_status === "in_stock" && subscription.lastStockStatus !== "in_stock";
      const increasedStock = offer.stock_status === "in_stock" && currentQuantity > previousQuantity;
      if (cameBack || increasedStock) {
        alerts.push({
          key: subscription.key,
          productName: productBaseName(product),
          providerName: offer.provider_name,
          quantity: currentQuantity,
          previousQuantity,
          href: `#${stockWatchTargetId(product, offer)}`,
        });
        return subscription;
      }

      return {
        ...subscription,
        productName: productBaseName(product),
        providerName: offer.provider_name,
        presentation: formatPresentation(product),
        lastStockStatus: offer.stock_status || "unknown",
        lastStockQuantity: currentQuantity,
        lastStockSignature: signature,
      };
    });

    stockSubscriptions = nextSubscriptions;
    stockAlerts = alerts;
    saveStockSubscriptions(nextSubscriptions);
  }

  function findSubscribedOffer(subscription) {
    const product = products.find((item) => item.id === subscription.productId);
    if (!product) return null;

    const offer = (product.offers || []).find((item) => (item.source_id || item.provider_name) === subscription.sourceId);
    if (!offer) return null;
    return { product, offer };
  }

  function dismissStockAlerts() {
    if (!stockAlerts.length) return;
    const alertKeys = new Set(stockAlerts.map((item) => item.key));
    stockSubscriptions = stockSubscriptions.map((subscription) => {
      if (!alertKeys.has(subscription.key)) return subscription;
      const match = findSubscribedOffer(subscription);
      if (!match) return subscription;
      return {
        ...subscription,
        productName: productBaseName(match.product),
        providerName: match.offer.provider_name,
        presentation: formatPresentation(match.product),
        lastStockStatus: match.offer.stock_status || "unknown",
        lastStockQuantity: Number(match.offer.stock_quantity || 0),
        lastStockSignature: stockSignature(match.offer),
        acknowledgedAt: new Date().toISOString(),
      };
    });
    stockAlerts = [];
    saveStockSubscriptions(stockSubscriptions);
  }

  function stockWatchTargetId(product, offer) {
    return `stock-watch-${slugText([product.id, offer.source_id || offer.provider_name].join(" "))}`;
  }
  $: summaryRows = (filteredProducts, buildSummaryRows(filteredProducts));
  $: providerTotals = totalsForSummaryRows(summaryRows);
  $: grandTotal = Object.values(providerTotals).reduce((sum, value) => sum + value, 0);
  $: groupedRows = (categoryOrder, groupSummaryRows(summaryRows));

  function buildSummaryRows(items) {
    return items.map((product) => {
      const cells = Object.fromEntries(sources.map((source) => [source.id, { units: 0, unknown: false }]));
      (product.offers || []).forEach((offer) => {
        const cell = cells[offer.source_id];
        if (!cell) return;
        if (Number.isFinite(Number(offer.stock_quantity)) && Number(offer.stock_quantity) > 0) {
          cell.units += Number(offer.stock_quantity);
        } else if (offer.stock_status === "unknown") {
          cell.unknown = true;
        }
      });
      const total = Object.values(cells).reduce((sum, cell) => sum + cell.units, 0);
      return { product, cells, total };
    }).sort((a, b) => compareSummaryProducts(a.product, b.product));
  }

  function totalsForSummaryRows(items) {
    const totals = Object.fromEntries(sources.map((source) => [source.id, 0]));
    items.forEach((row) => {
      sources.forEach((source) => {
        totals[source.id] += row.cells[source.id]?.units || 0;
      });
    });
    return totals;
  }

  function groupSummaryRows(items) {
    const groups = new Map();
    items.forEach((row) => {
      const key = summaryGroupKey(row.product);
      if (!groups.has(key)) {
        groups.set(key, {
          title: summaryGroupTitle(row.product),
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
    return [...groups.values()].sort(compareSummaryGroups);
  }

  function groupPresentationRows(rows) {
    const presentationGroups = new Map();
    rows.forEach((row) => {
      const product = row.product;
      const key = [
        product.brand || "Sin marca",
        product.diameter_mm || "Sin diámetro",
        lineLabel(product),
        product.material || "Sin material",
        product.variant || "",
        product.color || "Sin color",
        product.pantone || "",
      ].join("||");
      if (!presentationGroups.has(key)) presentationGroups.set(key, []);
      presentationGroups.get(key).push(row);
    });
    return [...presentationGroups.values()];
  }

  function summaryGroupKey(product) {
    return [brandRank(product.brand), product.brand || "Sin marca", product.diameter_mm ? `${product.diameter_mm} mm` : "Sin diámetro", lineLabel(product)].join("||");
  }

  function summaryGroupTitle(product) {
    return [product.brand || "Sin marca", product.diameter_mm ? `${product.diameter_mm} mm` : "Sin diámetro", lineLabel(product)].filter(Boolean).join(" · ");
  }

  function compareSummaryGroups(left, right) {
    if (categoryOrder === "alpha") return left.title.localeCompare(right.title, "es-AR");
    return lineRank(left.line) - lineRank(right.line)
      || brandRank(left.brand).localeCompare(brandRank(right.brand), "es-AR")
      || left.diameter.localeCompare(right.diameter, "es-AR")
      || left.title.localeCompare(right.title, "es-AR");
  }

  function compareSummaryProducts(left, right) {
    return [
      brandRank(left.brand), left.brand || "", left.diameter_mm ? `${left.diameter_mm} mm` : "Sin diámetro", lineLabel(left), left.color || "", left.display_name,
    ].join(" ").localeCompare([
      brandRank(right.brand), right.brand || "", right.diameter_mm ? `${right.diameter_mm} mm` : "Sin diámetro", lineLabel(right), right.color || "", right.display_name,
    ].join(" "), "es-AR");
  }

  function productSummaryName(product) {
    if (product.color && product.color !== "Sin color") return product.color;
    const repeatedParts = [product.brand, product.diameter_mm ? `${product.diameter_mm} mm` : "", formatPresentation(product), lineLabel(product), product.material].filter(Boolean);
    return repeatedParts.reduce((name, part) => name.replace(part, "").replace(/\s+/g, " ").trim(), product.display_name) || product.display_name;
  }

  function summaryGroupTargetId(group) {
    return `resumen-linea-${slugText(group.title)}`;
  }

  function offerForSource(product, sourceId) {
    return (product.offers || []).find((offer) => offer.source_id === sourceId);
  }

  function showAssetPreview(event, src, title) {
    if (!src) return;
    preview = {
      src: assetPath(src),
      title,
      x: event.clientX + 16,
      y: event.clientY + 16,
      modal: false,
    };
  }

  function openAssetPreview(src, title, meta = "") {
    if (!src) return;
    preview = { src: assetPath(src), title, meta, modal: true };
  }
</script>

<main id="main-content" class="shell" tabindex="-1">
  <h1 class="sr-only">Resumen por proveedor</h1>
  <SiteHeader active="summary" updatedAt={generatedAt} subtitle="Resumen por proveedor" showCatalogHelp />
  <p class="sr-only" aria-live="polite">{quoteFeedbackMessage}</p>

  {#if quoteListReadOnly}
    <p class="line-help quote-list-warning" role="status">{quoteSchemaWarningCopy}</p>
  {/if}

  <section class="filters" class:show-more-filters={showMoreFilters} aria-label="Filtros">
    <label class="search-field">
      <span>Buscar</span>
      <input id="search-input" type="search" value={filters.query} on:input={(event) => setFilter("query", event.currentTarget.value)} placeholder="PLA negro, PETG, Grilon3...">
    </label>
    <select id="material-filter" aria-label="Filtrar por material" value={filters.material} on:change={(event) => setFilter("material", event.currentTarget.value)}><option value="">Material</option>{#each materialOptions as value}<option value={value}>{value}</option>{/each}</select>
    <select id="color-filter" aria-label="Filtrar por color" value={filters.color} on:change={(event) => setFilter("color", event.currentTarget.value)}><option value="">Color</option>{#each colorOptions as value}<option value={value}>{value}</option>{/each}</select>
    <select id="provider-filter" aria-label="Filtrar por proveedor" value={filters.provider} on:change={(event) => setFilter("provider", event.currentTarget.value)}><option value="">Proveedor</option>{#each providerOptions as value}<option value={value}>{value}</option>{/each}</select>
    <button class="more-filters-button" type="button" aria-expanded={showMoreFilters} on:click={() => showMoreFilters = !showMoreFilters}>
      {showMoreFilters ? "Menos filtros" : "Mas filtros"}{secondaryFilterCount ? ` · ${secondaryFilterCount}` : ""}
    </button>
    <select class="filter-secondary" id="variant-filter" aria-label="Filtrar por linea" value={filters.variant} on:change={(event) => setVariantFilter(event.currentTarget.value)}><option value="">Línea</option>{#each lineOptions as value}<option value={value}>{lineOptionLabel(value)}</option>{/each}</select>
    <select class="filter-secondary" id="diameter-filter" aria-label="Filtrar por diametro" value={filters.diameter} on:change={(event) => setFilter("diameter", event.currentTarget.value)}><option value="">Diámetro</option>{#each diameterOptions as value}<option value={String(value)}>{value} mm</option>{/each}</select>
    <select class="filter-secondary" id="weight-filter" aria-label="Filtrar por peso" value={filters.weight} on:change={(event) => setFilter("weight", event.currentTarget.value)}><option value="">Peso</option>{#each weightOptions as value}<option value={String(value)}>{Number(value) / 1000} kg</option>{/each}</select>
    <select class="filter-secondary" id="brand-filter" aria-label="Filtrar por marca" value={filters.brand} on:change={(event) => setFilter("brand", event.currentTarget.value)}><option value="">Marca</option>{#each brandOptions as value}<option value={value}>{value}</option>{/each}</select>
    <select class="filter-secondary" id="stock-filter" aria-label="Filtrar por disponibilidad" value={filters.stock} on:change={(event) => setFilter("stock", event.currentTarget.value)}>
      <option value="all">Todos</option>
      <option value="in_stock">Con stock</option>
      <option value="out_of_stock">Sin stock</option>
      <option value="unknown">Sin cantidad</option>
    </select>
  </section>

  {#if activeFilterChips.length}
    <div class="active-filters" aria-label="Filtros activos">
      {#each activeFilterChips as chip}
        <button type="button" on:click={() => clearFilter(chip.key)} aria-label={`Quitar filtro ${chip.label}`}>
          <span>{chip.label}</span><span aria-hidden="true">×</span>
        </button>
      {/each}
      {#if activeFilterChips.length > 1}
        <button type="button" class="clear-filter-chips" on:click={clearAllFilters}>Limpiar</button>
      {/if}
    </div>
  {/if}

  <section class="quick-lines-shell" aria-label="Líneas populares">
    <QuickLines id="quick-lines" available={availableLines} bind:help={lineHelp} targetSelector=".summary-group-row" />
    <p id="line-help" class="line-help">{lineHelp}</p>
  </section>

  <div class="result-meta">
    <strong id="result-count">{filteredProducts.length} filamentos</strong>
    <div class="quote-import-entry">
      <button class="soft-button" type="button" on:click={openQuoteImportPicker}>Importar lista</button>
      <button
        type="button"
        class="quote-import-help-tip"
        aria-label="Importa una lista exportada para recuperarla o llevarla desde otra PC o navegador."
        data-tooltip="Importa una lista exportada para recuperarla o llevarla desde otra PC o navegador."
      >?</button>
    </div>
    {#if quoteItems.length > 0}
      <button class="soft-button quote-list-trigger" type="button" aria-expanded={quoteDrawerOpen} on:click={openQuoteDrawer}>
        Lista de cotización <span>{quoteItems.length}</span>
      </button>
    {/if}
    <div class="category-sort" role="group" aria-label="Orden de categorías">
      <span>Orden</span>
      <button id="sort-popular" class:active={categoryOrder === "popular"} class="soft-button" type="button" data-category-order="popular" on:click={() => categoryOrder = "popular"}>Popularidad</button>
      <button id="sort-alpha" class:active={categoryOrder === "alpha"} class="soft-button" type="button" data-category-order="alpha" on:click={() => categoryOrder = "alpha"}>A-Z</button>
    </div>
  </div>

  <div class:quote-list-layout-active={quoteItems.length > 0}>
    <div class="table-shell">
      <table id="summary-table" class="summary-table">
        <thead>
          <tr>
            <th class="summary-photo-column">Foto</th>
            <th class="summary-color-column">Color</th>
            <th>Filamento</th>
            <th class="summary-presentation">Presentación</th>
            <th class="summary-add-column"><span class="sr-only">Agregar</span>+1</th>
            {#each sources as source}
              <th><a href={source.homepage_url} target="_blank" rel="noopener" title={`${formatInteger(source.stats?.total_stock_units ?? 0)} carretes`}>{source.name}</a></th>
            {/each}
            <th class="summary-total">Total</th>
          </tr>
        </thead>
        <tbody>
          {#if !groupedRows.length}
            <tr>
              <td class="summary-empty-state" colspan={sources.length + 6}>
                <strong>No encontramos filamentos con esos filtros</strong>
                <button type="button" on:click={clearAllFilters}>Limpiar filtros</button>
              </td>
            </tr>
          {/if}
          {#each groupedRows as group}
            <tr class="summary-group-row" id={summaryGroupTargetId(group)} data-line={group.line}>
              <th colspan="5">
                {group.title}
                <span class="summary-mobile-totals" aria-hidden="true">
                  {#each sources as source}<span><b>{source.name}</b> {formatInteger(group.totals[source.id])}</span>{/each}
                  <span class="summary-mobile-total"><b>Total</b> {formatInteger(group.total)}</span>
                </span>
              </th>
              {#each sources as source}<td data-label={source.name}>{formatInteger(group.totals[source.id])}</td>{/each}
              <td class="summary-total" data-label="Total">{formatInteger(group.total)}</td>
            </tr>
            {#each groupPresentationRows(group.rows) as presentationGroup}
              {#each presentationGroup as row, presentationIndex}
                {@const imagePath = row.product.thumbnail_url || row.product.image_url || ""}
                {@const fullImagePath = row.product.image_url || row.product.thumbnail_url || ""}
                {@const swatchPath = row.product.material_swatch_url || ""}
                {@const visualTitle = [productSummaryName(row.product), row.product.pantone, formatPresentation(row.product)].filter(Boolean).join(" · ")}
                {@const addFeedback = quoteAddFeedback[row.product.id]}
                <tr
                  data-product-id={row.product.id}
                  class:presentation-grouped={presentationGroup.length > 1}
                  class:presentation-group-start={presentationGroup.length > 1 && presentationIndex === 0}
                  class:presentation-group-end={presentationGroup.length > 1 && presentationIndex === presentationGroup.length - 1}
                >
                  <td class="summary-photo-cell" data-label="Foto">
                    {#if imagePath}
                      <button class="summary-media-button" type="button" aria-label={"Ampliar foto de " + productBaseName(row.product)} on:click={() => openAssetPreview(fullImagePath, productBaseName(row.product), visualTitle)} on:pointerenter={(event) => showAssetPreview(event, fullImagePath, "Foto · " + visualTitle)} on:pointermove={movePreview} on:pointerleave={hideHoverPreview}>
                        <img class="summary-product-photo" src={assetPath(imagePath)} alt={productBaseName(row.product)} loading="lazy" decoding="async">
                      </button>
                    {:else}
                      <span class="summary-media-button summary-product-photo-placeholder" aria-hidden="true"></span>
                    {/if}
                  </td>
                  <td class="summary-color-cell" data-label="Color">
                    {#if swatchPath}
                      <button class="summary-media-button" type="button" aria-label={"Ampliar color renderizado de " + productBaseName(row.product)} on:click={() => openAssetPreview(swatchPath, productBaseName(row.product), "Color renderizado · " + visualTitle)} on:pointerenter={(event) => showAssetPreview(event, swatchPath, "Color renderizado · " + visualTitle)} on:pointermove={movePreview} on:pointerleave={hideHoverPreview}>
                        <img class="summary-color-swatch summary-material-swatch" src={assetPath(swatchPath)} alt={materialSwatchAlt(row.product)} loading="lazy" decoding="async">
                      </button>
                    {:else}
                      <span class="summary-color-swatch" style={colorSwatchStyle(row.product)} title={[row.product.color || "Sin color", row.product.pantone].filter(Boolean).join(" · ")} aria-label={[row.product.color || "Sin color", row.product.pantone].filter(Boolean).join(" · ")}></span>
                    {/if}
                  </td>
                  <th class="summary-product-name-cell">
                    {#if presentationGroup.length > 1}
                      <span class="presentation-group-marker" title="Otra presentación del mismo filamento" aria-hidden="true"></span>
                    {/if}
                    <span class="summary-product-name">
                      {#if row.product.manufacturer_product_url}
                        <a href={row.product.manufacturer_product_url} target="_blank" rel="noopener">{productSummaryName(row.product)}</a>
                      {:else}
                        {productSummaryName(row.product)}
                      {/if}
                      {#if row.product.pantone}<small>{row.product.pantone}</small>{/if}
                    </span>
                  </th>
                  <td class="summary-presentation" data-label="Presentación">{formatPresentation(row.product)}</td>
                  <td class="summary-add-cell" data-label="Agregar">
                    <button class="quote-add-button summary-quote-add" class:confirmed={Boolean(addFeedback)} type="button" aria-label="Agregar 1 unidad a la lista de cotizacion" on:click={() => addQuoteItem(row.product)}>{addFeedback ? "✓ " + addFeedback : "+1"}</button>
                  </td>
                  {#each sources as source}
                    {@const cell = row.cells[source.id]}
                    {@const offer = offerForSource(row.product, source.id)}
                    <td class={cell?.units > 0 ? "stock-in" : "stock-out"} data-label={source.name}>
                      <span class="summary-stock-cell">
                        <span>{formatInteger(cell?.units || 0)}</span>
                        {#if stockWatchEnabled && offer}
                          {@const watchFeedbackKey = subscriptionKey(row.product, offer)}
                          <button id={stockWatchTargetId(row.product, offer)} class="stock-watch-button summary-stock-watch" class:active={isSubscribed(row.product, offer)} type="button" aria-pressed={isSubscribed(row.product, offer)} aria-label={(isSubscribed(row.product, offer) ? "Dejar de seguir cambios de stock" : "Seguir cambios de stock") + " de " + productBaseName(row.product) + " en " + offer.provider_name} title={isSubscribed(row.product, offer) ? "Dejar de seguir cambios de stock" : "Avisarme si sube o vuelve el stock"} on:click={() => toggleStockSubscription(row.product, offer)}>
                            {#key stockWatchFeedback[watchFeedbackKey] || 0}
                              <svg class:bell-ringing={Boolean(stockWatchFeedback[watchFeedbackKey])} viewBox="0 0 24 24" aria-hidden="true"><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"></path><path d="M10 21h4"></path></svg>
                            {/key}
                          </button>
                        {/if}
                      </span>
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
            <th colspan="5">Carretes por proveedor</th>
            {#each sources as source}<td class="summary-provider-total" data-label={source.name}>{formatInteger(providerTotals[source.id])}</td>{/each}
            <td class="summary-total" data-label="Total">{formatInteger(grandTotal)}</td>
          </tr>
        </tfoot>
      </table>
    </div>

  </div>
</main>

{#if quoteItems.length > 0}
  <button class="quote-floating-button" type="button" aria-label={`Abrir lista de cotizacion con ${quoteItems.length} item(s)`} on:click={openQuoteDrawer}>
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M8 6h11"></path>
      <path d="M8 12h11"></path>
      <path d="M8 18h11"></path>
      <path d="m3 6 1 1 2-2"></path>
      <path d="m3 12 1 1 2-2"></path>
      <path d="m3 18 1 1 2-2"></path>
    </svg>
    {#key quotePulseKey}
      <span class="quote-floating-count">{quoteItems.length}</span>
    {/key}
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
  onClose={closeQuoteDrawer}
  onToggleControls={toggleQuoteControls}
  onSetQuantity={setQuoteItemQuantity}
  onRemoveItem={removeQuoteItem}
  onClearList={clearQuoteList}
  onExportList={exportQuoteList}
  onImportList={openQuoteImportPicker}
  {handleQuoteDrawerKeydown}
/>

<input class="quote-import-input" type="file" accept=".json,application/json" bind:this={quoteImportInput} on:change={handleQuoteImportFile}>

{#if quoteImportPreview || quoteImportError}
  <div class="quote-import-backdrop" role="presentation" on:click={(event) => event.target === event.currentTarget && closeQuoteImport()}>
    <div class="quote-import-dialog" role="dialog" aria-modal="true" aria-labelledby="quote-import-title" tabindex="-1">
      <button class="quote-import-close" type="button" aria-label="Cerrar importacion" on:click={closeQuoteImport}>×</button>
      <h2 id="quote-import-title">Importar lista</h2>
      <small>{quoteImportFileName}</small>
      {#if quoteImportError}
        <p class="quote-import-error" aria-live="polite">{quoteImportError}</p>
        <button class="soft-button" type="button" on:click={openQuoteImportPicker}>Elegir otro archivo</button>
      {:else}
        <p><strong>{quoteImportPreview.validCount}</strong> item(s) listos para importar.</p>
        {#if quoteImportPreview.skippedCount}
          <p>{quoteImportPreview.skippedCount} item(s) se descartaran porque no son validos o ya no existen.</p>
        {/if}
        <p class="quote-import-help">Combinar conserva tus otros items; si un producto se repite, usa la cantidad importada.</p>
        <div class="quote-import-actions">
          <button class="primary-button" type="button" on:click={() => applyQuoteImport("combine")}>Combinar</button>
          <button class="soft-button" type="button" on:click={() => applyQuoteImport("replace")}>Reemplazar</button>
        </div>
      {/if}
    </div>
  </div>
{/if}

<SiteFooter {sources} {contactContext} />

<svelte:window on:keydown={handlePreviewKeydown} />

{#if preview && preview.modal}
  <div class="image-preview-backdrop" role="presentation" on:click={closePreviewBackdrop}>
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
