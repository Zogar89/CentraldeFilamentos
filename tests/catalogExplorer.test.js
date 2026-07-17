import assert from "node:assert/strict";
import test from "node:test";

import {
  colorFamilyForHex,
  colorChoices,
  compareExplorerProducts,
  materialChoices,
  matchesColorFamilySelection,
  matchesMaterialSelection,
  productStockTotal,
} from "../src/lib/catalogExplorer.js";

const products = [
  {
    id: "pla-yellow",
    material: "PLA",
    color: "Amarillo",
    pantone_hex: "#FFD21A",
    estimated_color_hex: "#F2D21B",
    thumbnail_url: "pla-yellow.webp",
    offers: [
      { source_id: "north", stock_quantity: 4, stock_status: "in_stock" },
      { source_id: "south", stock_quantity: 2, stock_status: "in_stock" },
    ],
  },
  {
    id: "pla-yellow-fluo",
    material: "PLA",
    color: "Amarillo Fluo",
    estimated_color_hex: "#EAF11D",
    image_url: "pla-fluo.jpg",
    offers: [{ source_id: "north", stock_quantity: 9, stock_status: "in_stock" }],
  },
  {
    id: "petg-yellow",
    material: "PETG",
    color: "Amarillo",
    estimated_color_hex: "#E0B20B",
    image_url: "petg-yellow.jpg",
    offers: [{ source_id: "south", stock_quantity: 30, stock_status: "in_stock" }],
  },
  {
    id: "abs-black",
    material: "ABS",
    color: "Negro",
    estimated_color_hex: "#111111",
    offers: [{ source_id: "north", stock_quantity: null, stock_status: "unknown" }],
  },
  {
    id: "pva-natural",
    material: "PVA",
    color: "Natural",
    estimated_color_hex: "#ECE4D5",
    offers: [{ source_id: "south", stock_quantity: 1, stock_status: "in_stock" }],
  },
];

test("material choices keep the maker-first order and group uncommon materials as Otros", () => {
  assert.deepEqual(
    materialChoices(products).map(({ id, count }) => [id, count]),
    [["PLA", 2], ["PETG", 1], ["ABS", 1], ["Otros", 1]],
  );
  assert.equal(materialChoices(products)[0].imageUrl, "pla-yellow.webp");
  assert.deepEqual(materialChoices(products).at(-1).materials, ["PVA"]);
});

test("material matching treats Otros as a hard set instead of clearing the material filter", () => {
  assert.equal(matchesMaterialSelection(products[0], "PLA"), true);
  assert.equal(matchesMaterialSelection(products[2], "PLA"), false);
  assert.equal(matchesMaterialSelection(products[4], "Otros"), true);
  assert.equal(matchesMaterialSelection(products[0], "Otros"), false);
});

test("color choices stay inside the selected material and prefer published Pantone HEX", () => {
  const plaColors = colorChoices(products, "PLA");

  assert.deepEqual(plaColors.map((choice) => choice.name), ["Amarillo", "Amarillo Fluo"]);
  assert.equal(plaColors[0].hex, "#FFD21A");
  assert.equal(plaColors[0].stockTotal, 6);
  assert.equal(plaColors.some((choice) => choice.hex === "#E0B20B"), false);
});

test("color choices for Otros include only uncommon materials", () => {
  assert.deepEqual(colorChoices(products, "Otros").map((choice) => choice.name), ["Natural"]);
});

test("color families keep nearby maker-facing tones together without crossing material", () => {
  const selected = colorChoices(products, "PLA").find((choice) => choice.name === "Amarillo");

  assert.equal(selected.familyLabel, "Amarillos");
  assert.equal(colorFamilyForHex("#EAF11D").label, "Amarillos");
  assert.equal(matchesColorFamilySelection(products[1], selected), true);
  assert.equal(matchesColorFamilySelection(products[2], selected), true);
  assert.equal(matchesMaterialSelection(products[2], "PLA"), false);
});

test("the color ribbon starts with light and dark neutrals before chromatic hues", () => {
  const ribbon = colorChoices([
    { material: "PLA", color: "Rojo", estimated_color_hex: "#D62929", offers: [] },
    { material: "PLA", color: "Negro", estimated_color_hex: "#151515", offers: [] },
    { material: "PLA", color: "Blanco", estimated_color_hex: "#F6F5F2", offers: [] },
  ], "PLA");

  assert.deepEqual(ribbon.map((choice) => choice.name), ["Blanco", "Negro", "Rojo"]);
});

test("stock totals ignore unknown or malformed quantities", () => {
  assert.equal(productStockTotal(products[0]), 6);
  assert.equal(productStockTotal(products[3]), 0);
  assert.equal(productStockTotal({ offers: [{ stock_quantity: "bad" }, { stock_quantity: -4 }] }), 0);
});

test("explorer products sort by total availability before their identity", () => {
  const sorted = [products[0], products[1], products[2]].sort(compareExplorerProducts);
  assert.deepEqual(sorted.map((product) => product.id), ["petg-yellow", "pla-yellow-fluo", "pla-yellow"]);
});
