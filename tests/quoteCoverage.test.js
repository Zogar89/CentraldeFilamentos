import assert from "node:assert/strict";
import { test } from "node:test";

import {
  buildProviderCoverage,
  canOpenWhatsapp,
  generalQuoteMessage,
  providerQuoteMessage,
} from "../src/lib/quoteCoverage.js";

const items = [
  { productId: "pla-negro", productName: "PLA Negro", quantity: 12, sku: "NEGRO-1" },
  { productId: "petg-rojo", productName: "PETG Rojo", quantity: 2 },
];
const products = [
  {
    id: "pla-negro",
    offers: [
      { source_id: "north", stock_status: "in_stock", stock_quantity: 12, original_name: "PLA NEGRO CAJA" },
      { source_id: "south", stock_status: "in_stock", stock_quantity: 3 },
    ],
  },
  {
    id: "petg-rojo",
    offers: [{ source_id: "south", stock_status: "in_stock", stock_quantity: 5, original_name: "PETG ROJO" }],
  },
];
const sources = [
  { id: "north", name: "Norte", contact_whatsapp_url: "https://wa.me/1" },
  { id: "south", name: "Sur", contact_whatsapp_url: "https://wa.me/2" },
];

test("coverage requires the exact product and enough stock", () => {
  const [north, south] = buildProviderCoverage(items, products, sources);

  assert.equal(north.coveredCount, 1);
  assert.equal(north.items[0].covered, true);
  assert.equal(north.items[1].covered, false);
  assert.equal(south.coveredCount, 1);
  assert.equal(south.items[0].covered, false);
  assert.equal(south.items[1].covered, true);
  assert.equal(north.complete, false);
});

test("provider message includes only covered items", () => {
  const [north] = buildProviderCoverage(items, products, sources);
  const message = providerQuoteMessage(north);

  assert.match(message, /PLA NEGRO CAJA/);
  assert.match(message, /12 unidades/);
  assert.doesNotMatch(message, /PETG Rojo/);
  assert.match(message, /cotizacion y disponibilidad/);
});

test("general message includes every requested item", () => {
  const message = generalQuoteMessage(items);
  assert.match(message, /PLA Negro/);
  assert.match(message, /PETG Rojo/);
});

test("whatsapp fallback rejects oversized links", () => {
  assert.equal(canOpenWhatsapp("https://wa.me/1?text=hola"), true);
  assert.equal(canOpenWhatsapp(`https://wa.me/1?text=${"x".repeat(1900)}`), false);
});
