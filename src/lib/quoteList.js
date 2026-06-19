import {
  formatPresentation,
  lineLabel,
  productBaseName,
} from "./shared.js";

export const quoteListStorageKey = "centraldefilamentos.quoteList.v1";
export const quoteListSchemaVersion = 1;

const defaultSettings = {
  showQuickControls: false,
};

export function quoteQuantityLabel(quantity) {
  const value = clampQuoteQuantity(quantity);
  return `${value} ${value === 1 ? "carrete" : "carretes"}`;
}

export function clampQuoteQuantity(value) {
  const next = Math.floor(Number(value));
  if (!Number.isFinite(next) || next < 1) return 1;
  return next;
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
    hasOnlineStock: (product?.offers || []).some((offer) => offer.stock_status === "in_stock" && Number(offer.stock_quantity || 0) > 0),
    quantity: clampQuoteQuantity(quantity),
  };
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
