import {
  formatPresentation,
  lineLabel,
  productBaseName,
} from "./shared.js";

export const quoteListStorageKey = "centraldefilamentos.quoteList.v1";
export const quoteListSchemaVersion = 1;
export const quoteListExportKind = "centraldefilamentos.quote-list";
export const quoteListExportVersion = 1;

const defaultSettings = {
  showQuickControls: false,
};

export function quoteQuantityLabel(quantity) {
  const value = clampQuoteQuantity(quantity);
  return `${value} ${value === 1 ? "unidad" : "unidades"}`;
}

export function clampQuoteQuantity(value) {
  const next = Math.floor(Number(value));
  if (!Number.isFinite(next) || next < 1) return 1;
  return next;
}

export function nextBoxQuantity(value, boxSize = 12) {
  const quantity = clampQuoteQuantity(value);
  const size = Math.max(1, Math.floor(Number(boxSize)) || 12);
  return (Math.floor(quantity / size) + 1) * size;
}

export function quoteItemCode(item) {
  return item?.articleCode || item?.sku || item?.ean || "";
}

export function quoteItemMissingBadges(item) {
  return [
    quoteItemCode(item) ? "" : "sin codigo",
    item?.diameterMm ? "" : "sin diametro",
    item?.presentation ? "" : "sin presentacion",
    item?.line || item?.material ? "" : "confirmar dato",
    item?.hasOnlineStock ? "" : "confirmar stock",
  ].filter(Boolean);
}

export function normalizeQuoteList(payload) {
  if (payload && payload.schemaVersion !== quoteListSchemaVersion) {
    return {
      schemaVersion: payload.schemaVersion,
      items: [],
      settings: { ...defaultSettings },
      storageAvailable: true,
      resetReason: "schema",
      saveError: "",
      readOnly: true,
      preservedPayload: payload,
    };
  }

  if (!payload || !Array.isArray(payload.items)) {
    return {
      schemaVersion: quoteListSchemaVersion,
      items: [],
      settings: { ...defaultSettings },
      storageAvailable: true,
      resetReason: payload ? "schema" : "",
      saveError: "",
      readOnly: false,
      preservedPayload: null,
    };
  }

  const seen = new Set();
  const items = payload.items
    .filter((item) => item && typeof item.productId === "string" && item.productId)
    .filter((item) => {
      if (seen.has(item.productId)) return false;
      seen.add(item.productId);
      return true;
    })
    .map((item) => ({
      productId: item.productId,
      productName: item.productName || item.displayName || "Filamento",
      displayName: item.displayName || item.productName || "Filamento",
      material: item.material || "",
      line: item.line || item.material || "",
      color: item.color || "",
      brand: item.brand || "",
      diameterMm: item.diameterMm ?? null,
      presentation: item.presentation || "",
      sku: item.sku || "",
      ean: item.ean || "",
      articleCode: item.articleCode || item.article_code || "",
      originalName: item.originalName || item.original_name || "",
      thumbnailUrl: item.thumbnailUrl || item.thumbnail_url || "",
      imageUrl: item.imageUrl || item.image_url || "",
      hasOnlineStock: Boolean(item.hasOnlineStock),
      quantity: clampQuoteQuantity(item.quantity),
    }));

  return {
    schemaVersion: quoteListSchemaVersion,
    items,
    settings: {
      ...defaultSettings,
      ...(payload.settings && typeof payload.settings === "object" ? payload.settings : {}),
      showQuickControls: Boolean(payload.settings?.showQuickControls),
    },
    storageAvailable: true,
    resetReason: "",
    saveError: "",
    readOnly: false,
    preservedPayload: null,
  };
}

export function loadQuoteList() {
  if (typeof localStorage === "undefined") {
    return { ...normalizeQuoteList(null), storageAvailable: false, resetReason: "storage", saveError: "unavailable" };
  }

  try {
    const raw = localStorage.getItem(quoteListStorageKey);
    return { ...normalizeQuoteList(raw ? JSON.parse(raw) : null), storageAvailable: true, saveError: "" };
  } catch {
    return { ...normalizeQuoteList(null), storageAvailable: false, resetReason: "storage", saveError: "read" };
  }
}

export function saveQuoteList(state) {
  if (state?.readOnly) {
    return {
      ok: false,
      blocked: true,
      storageAvailable: true,
      saveError: "schema",
      payload: state.preservedPayload,
    };
  }

  const payload = normalizeQuoteList({
    schemaVersion: quoteListSchemaVersion,
    items: state?.items || [],
    settings: state?.settings || defaultSettings,
  });

  if (typeof localStorage === "undefined") {
    return { ok: false, storageAvailable: false, saveError: "unavailable", payload };
  }

  try {
    localStorage.setItem(quoteListStorageKey, JSON.stringify(payload));
    return { ok: true, storageAvailable: true, saveError: "", payload };
  } catch {
    return { ok: false, storageAvailable: false, saveError: "write", payload };
  }
}

export function serializeQuoteListExport(state, exportedAt = new Date().toISOString()) {
  const normalized = normalizeQuoteList({
    schemaVersion: quoteListSchemaVersion,
    items: state?.items || [],
    settings: state?.settings || defaultSettings,
  });
  return JSON.stringify({
    kind: quoteListExportKind,
    exportVersion: quoteListExportVersion,
    exportedAt,
    schemaVersion: quoteListSchemaVersion,
    items: normalized.items,
    settings: normalized.settings,
  }, null, 2);
}

export function previewQuoteListImport(raw, products) {
  let payload;
  try {
    payload = typeof raw === "string" ? JSON.parse(raw) : raw;
  } catch {
    return { ok: false, error: "El archivo no contiene JSON valido." };
  }

  if (!payload || payload.kind !== quoteListExportKind) {
    return { ok: false, error: "El archivo no es una lista exportada por StockCentral." };
  }
  if (payload.exportVersion !== quoteListExportVersion || payload.schemaVersion !== quoteListSchemaVersion) {
    return { ok: false, error: "La version del archivo no es compatible con esta aplicacion." };
  }
  if (!Array.isArray(payload.items)) {
    return { ok: false, error: "El archivo no contiene un listado de items valido." };
  }

  const normalized = normalizeQuoteList(payload);
  const reconciled = reconcileQuoteList(normalized.items, products || []);
  const malformedCount = Math.max(0, payload.items.length - normalized.items.length);
  const skippedCount = malformedCount + reconciled.removedCount;
  if (!reconciled.items.length) {
    return {
      ok: false,
      error: "No encontramos items vigentes para importar.",
      sourceCount: payload.items.length,
      skippedCount,
    };
  }
  return {
    ok: true,
    items: reconciled.items,
    settings: normalized.settings,
    sourceCount: payload.items.length,
    validCount: reconciled.items.length,
    skippedCount,
    exportedAt: payload.exportedAt || "",
  };
}

export function combineQuoteListItems(currentItems, importedItems) {
  const combined = new Map((currentItems || []).map((item) => [item.productId, item]));
  for (const item of importedItems || []) combined.set(item.productId, item);
  return [...combined.values()];
}

export function snapshotQuoteItem(product, quantity = 1) {
  const firstOffer = (product?.offers || []).find((offer) => offer.original_name) || {};
  return {
    productId: product?.id || "",
    productName: productBaseName(product || {}),
    displayName: product?.display_name || productBaseName(product || {}),
    material: product?.material || "",
    line: lineLabel(product || {}),
    color: product?.color || "",
    brand: product?.brand || "",
    diameterMm: product?.diameter_mm ?? null,
    presentation: formatPresentation(product || {}),
    sku: product?.sku || "",
    ean: product?.ean || "",
    articleCode: product?.article_code || product?.article || "",
    originalName: firstOffer.original_name || "",
    thumbnailUrl: product?.thumbnail_url || "",
    imageUrl: product?.image_url || "",
    hasOnlineStock: (product?.offers || []).some((offer) => offer.stock_status === "in_stock" && Number(offer.stock_quantity || 0) > 0),
    quantity: clampQuoteQuantity(quantity),
  };
}

export function incrementQuoteListItem(items, product) {
  const current = items || [];
  const existing = current.find((item) => item.productId === product.id);
  const quantity = Number(existing?.quantity || 0) + 1;
  return existing
    ? current.map((item) => item.productId === product.id ? snapshotQuoteItem(product, quantity) : item)
    : [...current, snapshotQuoteItem(product, 1)];
}

export function reconcileQuoteList(items, products) {
  const productById = new Map((products || []).map((product) => [product.id, product]));
  const nextItems = [];
  let removedCount = 0;

  for (const item of normalizeQuoteList({
    schemaVersion: quoteListSchemaVersion,
    items,
    settings: defaultSettings,
  }).items) {
    const product = productById.get(item.productId);
    if (!product) {
      removedCount += 1;
      continue;
    }
    nextItems.push(snapshotQuoteItem(product, item.quantity));
  }

  return {
    items: nextItems,
    settings: { ...defaultSettings },
    storageAvailable: true,
    resetReason: "",
    saveError: "",
    removedCount,
  };
}

export function initializeQuoteList(quoteList, catalogResult) {
  const current = quoteList || normalizeQuoteList(null);
  if (current.readOnly) {
    return {
      items: current.items,
      settings: current.settings,
      removedCount: 0,
      shouldSave: false,
      catalogAvailable: Boolean(catalogResult?.ok),
      readOnly: true,
      preservedPayload: current.preservedPayload,
    };
  }

  if (!catalogResult?.ok) {
    return {
      items: current.items,
      settings: current.settings,
      removedCount: 0,
      shouldSave: false,
      catalogAvailable: false,
    };
  }

  const reconciled = reconcileQuoteList(current.items, catalogResult.products);
  return {
    ...reconciled,
    settings: current.settings,
    shouldSave: reconciled.removedCount > 0,
    catalogAvailable: true,
  };
}
