import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import test from "node:test";

import { buildSummaryRows, summaryProductImage } from "../src/lib/summaryRows.js";

test("summary row helpers live in a focused pure module", () => {
  assert.equal(existsSync(new URL("../src/lib/summaryRows.js", import.meta.url)), true);
});

const SOURCES = [{ id: "north" }, { id: "south" }];

test("each source cell keeps the exact first published offer", () => {
  const first = { source_id: "north", provider_name: "Primero", stock_quantity: 3, stock_status: "in_stock" };
  const laterDuplicate = { source_id: "north", provider_name: "Duplicado", stock_quantity: 9, stock_status: "in_stock" };
  const [row] = buildSummaryRows([{ id: "pla", offers: [first, laterDuplicate] }], SOURCES);

  assert.deepEqual(row.cells.north, { units: 3, unknown: false, offer: first });
  assert.equal(row.total, 3);
});

test("a duplicate cannot replace or add to the first source offer", () => {
  const firstUnknown = { source_id: "north", provider_name: "Primero", stock_quantity: null, stock_status: "unknown" };
  const laterPositive = { source_id: "north", provider_name: "Duplicado", stock_quantity: 7, stock_status: "in_stock" };
  const [row] = buildSummaryRows([{ id: "pla", offers: [firstUnknown, laterPositive] }], SOURCES);

  assert.equal(row.cells.north.offer, firstUnknown);
  assert.equal(row.cells.north.units, 0);
  assert.equal(row.cells.north.unknown, true);
  assert.equal(row.total, 0);
});

test("unknown, confirmed zero and independent sources stay distinct", () => {
  const unknown = { source_id: "north", stock_quantity: null, stock_status: "unknown" };
  const zero = { source_id: "south", stock_quantity: 0, stock_status: "out_of_stock" };
  const [row] = buildSummaryRows([{ id: "pla", offers: [unknown, zero] }], SOURCES);

  assert.deepEqual(row.cells.north, { units: 0, unknown: true, offer: unknown });
  assert.deepEqual(row.cells.south, { units: 0, unknown: false, offer: zero });
});

test("missing and unknown-source offers do not populate another source cell", () => {
  const [row] = buildSummaryRows([
    { id: "pla", offers: [{ source_id: "outside", stock_quantity: 5, stock_status: "in_stock" }] },
  ], SOURCES);

  assert.deepEqual(row.cells.north, { units: 0, unknown: false, offer: null });
  assert.deepEqual(row.cells.south, { units: 0, unknown: false, offer: null });
  assert.equal(row.total, 0);
});

test("summary images require a current approved image source", () => {
  assert.equal(summaryProductImage({ thumbnail_url: "thumb.webp", image_url: "image.jpg", image_source: "manufacturer" }), "thumb.webp");
  assert.equal(summaryProductImage({ image_url: "provider.jpg", image_source: "provider" }), "provider.jpg");
  assert.equal(summaryProductImage({ image_url: "arbitrary.jpg", image_source: "" }), "");
  assert.equal(summaryProductImage({ thumbnail_url: "arbitrary.webp", image_source: "external" }), "");
  assert.equal(summaryProductImage({ image_source: "manufacturer" }), "");
});
