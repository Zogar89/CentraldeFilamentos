export const stockSubscriptionsStorageKey = "centraldefilamentos.stockSubscriptions.v1";

export function subscriptionKey(product, offer) {
  return [product?.id || "", offer?.source_id || offer?.provider_name || ""].join("::");
}

export function stockSignature(offer) {
  return [
    offer?.stock_status || "unknown",
    Number(offer?.stock_quantity || 0),
    offer?.updated_at || "",
  ].join(":");
}

export function loadStockSubscriptions() {
  if (typeof localStorage === "undefined") return [];
  try {
    return normalizeSubscriptions(JSON.parse(localStorage.getItem(stockSubscriptionsStorageKey) || "[]"));
  } catch {
    return [];
  }
}

export function saveStockSubscriptions(items) {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(stockSubscriptionsStorageKey, JSON.stringify(normalizeSubscriptions(items)));
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
