import { quoteItemCode, quoteQuantityLabel } from "./quoteList.js";

export const whatsappSafeLength = 1800;

export function buildProviderCoverage(items, products, sources) {
  const productsById = new Map((products || []).map((product) => [product.id, product]));
  return (sources || []).map((source) => {
    const evaluatedItems = (items || []).map((item) => {
      const product = productsById.get(item.productId);
      const offer = product?.offers?.find((candidate) => candidate.source_id === source.id) || null;
      const requestedQuantity = Number(item.quantity || 0);
      const stockQuantity = Number(offer?.stock_quantity || 0);
      const covered = Boolean(
        offer
        && offer.stock_status === "in_stock"
        && stockQuantity >= requestedQuantity,
      );
      return {
        item,
        offer,
        requestedQuantity,
        stockQuantity,
        covered,
      };
    });
    const coveredItems = evaluatedItems.filter((entry) => entry.covered);
    return {
      source,
      items: evaluatedItems,
      coveredItems,
      coveredCount: coveredItems.length,
      totalCount: evaluatedItems.length,
      complete: evaluatedItems.length > 0 && coveredItems.length === evaluatedItems.length,
    };
  });
}

export function quoteItemMessageLine(entry) {
  const item = entry.item || entry;
  const providerName = entry.offer?.original_name || item.productName || item.displayName || "Filamento";
  const code = quoteItemCode(item);
  return `- ${quoteQuantityLabel(item.quantity)} · ${providerName}${code ? ` · Cod. ${code}` : ""}`;
}

export function generalQuoteMessage(items) {
  const lines = (items || []).map((item) => quoteItemMessageLine(item));
  return [
    "Hola, quisiera consultar cotizacion y disponibilidad de los siguientes filamentos:",
    "",
    ...lines,
    "",
    "Muchas gracias.",
  ].join("\n");
}

export function providerQuoteMessage(coverage) {
  const lines = (coverage?.coveredItems || []).map(quoteItemMessageLine);
  return [
    `Hola ${coverage?.source?.name || ""}, quisiera consultar cotizacion y disponibilidad de:`,
    "",
    ...lines,
    "",
    "Muchas gracias.",
  ].join("\n");
}

export function canOpenWhatsapp(url) {
  return Boolean(url && url.length <= whatsappSafeLength);
}
