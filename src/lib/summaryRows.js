const APPROVED_IMAGE_SOURCES = new Set(["manufacturer", "provider"]);

export function buildSummaryRows(products = [], sources = []) {
  return products.map((product) => {
    const cells = Object.fromEntries(
      sources.map((source) => [source.id, { units: 0, unknown: false, offer: null }]),
    );

    (product.offers || []).forEach((offer) => {
      const cell = cells[offer?.source_id];
      if (!cell || cell.offer) return;

      // Published offer order is authoritative; duplicates never replace the first provider cell.
      cell.offer = offer;
      const quantity = Number(offer.stock_quantity);
      if (Number.isFinite(quantity) && quantity > 0) cell.units = quantity;
      else if (offer.stock_status === "unknown") cell.unknown = true;
    });

    const total = Object.values(cells).reduce((sum, cell) => sum + cell.units, 0);
    return { product, cells, total };
  });
}

export function summaryProductImage(product) {
  if (!APPROVED_IMAGE_SOURCES.has(product?.image_source)) return "";
  return product.thumbnail_url || product.image_url || "";
}
