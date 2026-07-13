import assert from "node:assert/strict";
import { test } from "node:test";

import {
  draftProducts,
  reviewStatus,
  validateReview,
} from "../tools/image-curation/curation-state.mjs";

const product = {
  product_id: "pla-negro-175-1000-grilon3",
  title: "PLA Negro Grilon3 1 kg",
  product_url: "https://grilon3.com.ar/producto/pla-negro/",
  gallery_image_urls: [
    "https://grilon3.com.ar/images/pla-negro-caja.jpg",
    "https://grilon3.com.ar/images/pla-negro-bobina.jpg",
    "https://grilon3.com.ar/images/pla-negro-principal.jpg",
    "https://grilon3.com.ar/images/pla-negro-detalle.jpg",
  ],
  gallery_fingerprint: "fingerprint-current",
  active: true,
};

function validReview(overrides = {}) {
  return {
    product_url: product.product_url,
    selected_image_remote_url: product.gallery_image_urls[1],
    selection_reason: "preferred_angle",
    gallery_fingerprint: product.gallery_fingerprint,
    reviewed_at: "2026-07-13T12:00:00.000Z",
    ...overrides,
  };
}

test("draftProducts returns every active scan product with its complete ordered gallery", () => {
  const inactive = { ...product, product_id: "inactive", active: false };
  const second = {
    ...product,
    product_id: "pla-rojo-175-1000-grilon3",
    product_url: "https://grilon3.com.ar/producto/pla-rojo/",
    gallery_image_urls: ["https://grilon3.com.ar/images/rojo-1.jpg"],
  };

  const result = draftProducts({ products: [product, inactive, second] });

  assert.equal(result.length, 2);
  assert.deepEqual(result[0].gallery_image_urls, product.gallery_image_urls);
  assert.equal(result[0].gallery_image_urls.length, 4);
  assert.equal("candidates" in result[0], false);
});

test("draftProducts treats scan products as active when the scan omits an active flag", () => {
  const result = draftProducts({ products: [{ ...product, active: undefined }] });
  assert.equal(result.length, 1);
});

test("validateReview rejects an image outside the exact official gallery", () => {
  assert.throws(
    () => validateReview(product, validReview({ selected_image_remote_url: "https://example.com/arbitrary.jpg" })),
    /galer.a oficial/i,
  );
});

test("validateReview rejects an unknown reason", () => {
  assert.throws(
    () => validateReview(product, validReview({ selection_reason: "looks_nice" })),
    /motivo/i,
  );
});

test("validateReview rejects mismatched canonical product URL and fingerprint", () => {
  assert.throws(
    () => validateReview(product, validReview({ product_url: "https://grilon3.com.ar/producto/otro/" })),
    /producto/i,
  );
  assert.throws(
    () => validateReview(product, validReview({ gallery_fingerprint: "old-fingerprint" })),
    /fingerprint/i,
  );
});

test("validateReview serializes only the durable review contract without dropping reason or fingerprint", () => {
  const normalized = validateReview(product, validReview({ extra: "drop-me" }));

  assert.deepEqual(normalized, {
    product_url: product.product_url,
    selected_image_remote_url: product.gallery_image_urls[1],
    selection_reason: "preferred_angle",
    gallery_fingerprint: product.gallery_fingerprint,
    reviewed_at: "2026-07-13T12:00:00.000Z",
  });
});

test("validateReview rejects an invalid reviewed timestamp", () => {
  assert.throws(
    () => validateReview(product, validReview({ reviewed_at: "today" })),
    /fecha/i,
  );
});

test("reviewStatus reports stale when the official gallery fingerprint changed", () => {
  assert.equal(reviewStatus(product, validReview({ gallery_fingerprint: "old-fingerprint" })), "stale");
});

test("reviewStatus reports pending, reviewed, and without-gallery", () => {
  assert.equal(reviewStatus(product, null), "pending");
  assert.equal(reviewStatus(product, validReview()), "reviewed");
  assert.equal(
    reviewStatus({ ...product, gallery_image_urls: [], gallery_fingerprint: "empty" }, null),
    "without-gallery",
  );
});

test("reviewStatus treats malformed current reviews as pending", () => {
  assert.equal(reviewStatus(product, validReview({ selection_reason: "unknown" })), "pending");
});
