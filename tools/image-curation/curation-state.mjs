const selectionReasons = new Set([
  "preferred_angle",
  "best_spool",
  "official_primary",
]);
const reviewProvenance = new Set(["human", "vision_llm"]);

export function draftProducts(payload) {
  if (!payload || !Array.isArray(payload.products)) return [];
  return payload.products.filter((product) => product && product.active !== false);
}

export function validateReview(product, review) {
  if (!product || !review || typeof review !== "object") {
    throw new Error("Falta el producto o la revisión.");
  }
  if (review.product_url !== product.product_url) {
    throw new Error("La URL del producto no coincide con el scan.");
  }
  if (review.gallery_fingerprint !== product.gallery_fingerprint) {
    throw new Error("El fingerprint de la galería no coincide con el scan actual.");
  }
  if (!Array.isArray(product.gallery_image_urls)
      || !product.gallery_image_urls.includes(review.selected_image_remote_url)) {
    throw new Error("La imagen elegida no pertenece a la galería oficial exacta.");
  }
  if (!selectionReasons.has(review.selection_reason)) {
    throw new Error("El motivo de selección no es válido.");
  }
  if (typeof review.reviewed_at !== "string"
      || !review.reviewed_at.trim()
      || !Number.isFinite(Date.parse(review.reviewed_at))) {
    throw new Error("La fecha de revisión no es válida.");
  }
  const normalized = {
    product_url: product.product_url,
    selected_image_remote_url: review.selected_image_remote_url,
    selection_reason: review.selection_reason,
    gallery_fingerprint: product.gallery_fingerprint,
    reviewed_at: review.reviewed_at,
  };
  if (review.provenance !== undefined) {
    if (typeof review.provenance !== "string" || !reviewProvenance.has(review.provenance)) {
      throw new Error("La procedencia de la revisión no es válida.");
    }
    normalized.provenance = review.provenance;
  }
  return normalized;
}

export function reviewStatus(product, review) {
  if (!Array.isArray(product?.gallery_image_urls) || product.gallery_image_urls.length === 0) {
    return "without-gallery";
  }
  if (!review || typeof review !== "object") return "pending";
  if (typeof product.gallery_fingerprint !== "string"
      || !product.gallery_fingerprint.trim()
      || typeof review.gallery_fingerprint !== "string"
      || !review.gallery_fingerprint.trim()) {
    return "pending";
  }
  if (review.gallery_fingerprint !== product.gallery_fingerprint) return "stale";
  try {
    validateReview(product, review);
    return "reviewed";
  } catch {
    return "pending";
  }
}
