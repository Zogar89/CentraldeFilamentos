export const stockSubscriptionsStorageKey = "centraldefilamentos.stockSubscriptions.v1";

export function subscriptionKey(product, offer) {
  return [product?.id || "", offer?.source_id || offer?.provider_name || ""].join("::");
}

export function stockSignature(offer) {
  const status = offer?.stock_status || "unknown";
  const rawQuantity = offer?.stock_quantity;
  const quantity = status === "unknown" && (rawQuantity === null || rawQuantity === undefined || rawQuantity === "")
    ? "unknown"
    : Number(rawQuantity || 0);
  return [
    status,
    quantity,
    offer?.updated_at || "",
  ].join(":");
}

function resolvedStorage(storage) {
  if (storage !== undefined) return storage;
  try {
    return globalThis.localStorage;
  } catch {
    return null;
  }
}

export function loadStockSubscriptions(storage) {
  const target = resolvedStorage(storage);
  if (!target) return [];
  try {
    return normalizeSubscriptions(JSON.parse(target.getItem(stockSubscriptionsStorageKey) || "[]"));
  } catch {
    return [];
  }
}

export function saveStockSubscriptions(items, storage) {
  const payload = normalizeSubscriptions(items);
  const target = resolvedStorage(storage);
  if (!target) return { ok: false, payload };
  try {
    target.setItem(stockSubscriptionsStorageKey, JSON.stringify(payload));
    return { ok: true, payload };
  } catch {
    return { ok: false, payload };
  }
}

export function normalizeSubscriptions(payload) {
  const rawItems = Array.isArray(payload) ? payload : payload?.items;
  if (!Array.isArray(rawItems)) return [];

  const seen = new Set();
  return rawItems
    .filter((item) => item && typeof item.key === "string" && item.key.includes("::"))
    .filter((item) => {
      if (seen.has(item.key)) return false;
      seen.add(item.key);
      return true;
    })
    .map((item) => ({
      key: item.key,
      productId: item.productId || item.product_id || item.key.split("::")[0],
      sourceId: item.sourceId || item.source_id || item.key.split("::")[1],
      productName: item.productName || item.product_name || "Filamento esperado",
      providerName: item.providerName || item.provider_name || "Proveedor",
      presentation: item.presentation || "",
      subscribedAt: item.subscribedAt || item.subscribed_at || new Date().toISOString(),
      lastStockStatus: item.lastStockStatus || item.last_stock_status || "unknown",
      lastStockQuantity: Number(item.lastStockQuantity ?? item.last_stock_quantity ?? 0),
      lastStockSignature: item.lastStockSignature || item.last_stock_signature || "",
      acknowledgedAt: item.acknowledgedAt || item.acknowledged_at || "",
    }));
}
