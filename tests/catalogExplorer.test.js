import assert from "node:assert/strict";
import test from "node:test";

import {
  colorFamilyForHex,
  colorChoices,
  compareCatalogProducts,
  compareExplorerProducts,
  materialChoices,
  matchesColorSelection,
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

test("PLA color choices collapse exact tones into explicit families", () => {
  const plaFamilies = colorChoices(products, "PLA");

  assert.deepEqual(plaFamilies.map((choice) => choice.name), ["Amarillos"]);
  assert.equal(plaFamilies[0].selectionMode, "family");
  assert.equal(plaFamilies[0].hex, "#FFD21A");
  assert.deepEqual(plaFamilies[0].swatchHexes, ["#FFD21A", "#EAF11D"]);
  assert.equal(plaFamilies[0].stockTotal, 15);
  assert.equal(plaFamilies[0].productCount, 2);
  assert.equal(plaFamilies[0].exactColorCount, 2);
  assert.equal(plaFamilies.some((choice) => choice.swatchHexes.includes("#E0B20B")), false);
});

test("color choices for Otros include only uncommon materials", () => {
  const choices = colorChoices(products, "Otros");

  assert.deepEqual(choices.map((choice) => choice.name), ["Natural"]);
  assert.equal(choices[0].selectionMode, "exact");
});

test("color families keep nearby maker-facing tones together without crossing material", () => {
  const selected = colorChoices(products, "PLA").find((choice) => choice.name === "Amarillos");

  assert.equal(selected.familyLabel, "Amarillos");
  assert.equal(colorFamilyForHex("#EAF11D").label, "Amarillos");
  assert.equal(matchesColorSelection(products[1], selected), true);
  assert.equal(matchesColorSelection(products[2], selected), true);
  assert.equal(matchesMaterialSelection(products[2], "PLA"), false);
});

test("the PLA family ribbon starts with light and dark neutrals before chromatic families", () => {
  const ribbon = colorChoices([
    { material: "PLA", color: "Rojo", estimated_color_hex: "#D62929", offers: [] },
    { material: "PLA", color: "Negro", estimated_color_hex: "#151515", offers: [] },
    { material: "PLA", color: "Blanco", estimated_color_hex: "#F6F5F2", offers: [] },
  ], "PLA");

  assert.deepEqual(ribbon.map((choice) => choice.name), ["Claros", "Negros", "Rojos"]);
});

test("non-PLA choices stay exact even when two colors share a visual family", () => {
  const petgProducts = [
    { material: "PETG", color: "Blanco", estimated_color_hex: "#F6F5F2", offers: [] },
    { material: "PETG", color: "Hueso", estimated_color_hex: "#F7F4ED", offers: [] },
  ];
  const choices = colorChoices(petgProducts, "PETG");
  const white = choices.find((choice) => choice.name === "Blanco");

  assert.deepEqual(choices.map((choice) => choice.name), ["Blanco", "Hueso"]);
  assert.equal(white.selectionMode, "exact");
  assert.equal(matchesColorSelection(petgProducts[0], white), true);
  assert.equal(matchesColorSelection(petgProducts[1], white), false);
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

test("catalog products sort by color, brand, presentation, and diameter", () => {
  const product = (id, color, brand, weight_g, diameter_mm) => ({
    id,
    color,
    brand,
    weight_g,
    diameter_mm,
    display_name: id,
    offers: [],
  });
  const sorted = [
    product("rojo-liviano", "Rojo", "3N3", 250, 1.75),
    product("azul-grilon-liviano", "Azul", "Grilon3", 250, 1.75),
    product("azul-3n3-pesado", "Azul", "3N3", 2500, 1.75),
    product("azul-3n3-medio-285", "Azul", "3N3", 1000, 2.85),
    product("azul-3n3-medio-175", "Azul", "3N3", 1000, 1.75),
  ].sort(compareCatalogProducts);

  assert.deepEqual(sorted.map((item) => item.id), [
    "azul-3n3-medio-175",
    "azul-3n3-medio-285",
    "azul-3n3-pesado",
    "azul-grilon-liviano",
    "rojo-liviano",
  ]);
});

test("catalog products place samplers before unknown presentations", () => {
  const base = {
    color: "Azul",
    brand: "3N3",
    diameter_mm: 1.75,
    offers: [],
  };
  const sorted = [
    { ...base, id: "unknown", display_name: "unknown", weight_g: null },
    {
      ...base,
      id: "sampler",
      display_name: "sampler",
      weight_g: null,
      offers: [{ original_name: "SAMPLER X 5 M" }],
    },
    { ...base, id: "weighted", display_name: "weighted", weight_g: 1000 },
  ].sort(compareCatalogProducts);

  assert.deepEqual(sorted.map((item) => item.id), ["weighted", "sampler", "unknown"]);
});
