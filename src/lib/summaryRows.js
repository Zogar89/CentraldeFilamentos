export function buildSummaryRows(products, sources) {
  return (products || []).map((product) => {
    const cells = Object.fromEntries((sources || []).map((source) => [source.id, {
      units: 0,
      unknown: false,
      offer: null,
    }]));
    for (const offer of product.offers || []) {
      const cell = cells[offer.source_id];
      if (!cell || cell.offer) continue;
      const quantity = Number(offer.stock_quantity);
      cell.offer = offer;
      cell.units = Number.isFinite(quantity) && quantity > 0 ? quantity : 0;
      cell.unknown = offer.stock_status === "unknown";
    }
    return {
      product,
      cells,
      total: Object.values(cells).reduce((sum, cell) => sum + cell.units, 0),
    };
  });
}

export function summaryProductImage(product) {
  if (!["manufacturer", "provider"].includes(product?.image_source)) return "";
  return product.thumbnail_url || product.image_url || "";
}
