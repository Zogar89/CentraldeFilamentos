import test from "node:test";
import assert from "node:assert/strict";
import {
  buildColorMap,
  buildPlaColorCatalog,
  colorOrderBand,
  distanceLabel,
  findSimilarColors,
  groupContinuousBands,
  groupColorFamilies,
  isValidHex,
  normalizeHex,
  rgbFromHex,
  sortPerceptually,
  toggleComparedColor,
} from "../src/lib/colorPicker.js";

function product(overrides = {}) {
  return {
    id: "pla-rojo-175-1000-grilon3",
    display_name: "Grilon3 PLA Rojo 1 kg",
    material: "PLA",
    variant: "",
    color: "Rojo",
    brand: "Grilon3",
    diameter_mm: 1.75,
    weight_g: 1000,
    pantone: "Pantone 179 C",
    pantone_hex: "#D92920",
    estimated_color_hex: "",
    estimated_color_confidence_band: "",
    estimated_color_source: "",
    estimated_color_warning: "",
    material_swatch_url: "assets/material-swatches/pantone-179-c-satin-v2.webp",
    offers: [{ provider_name: "Proveedor", stock_status: "in_stock", stock_quantity: 2 }],
    ...overrides,
  };
}

test("normalizes and validates #RRGGBB values", () => {
  assert.equal(normalizeHex("009dce"), "#009DCE");
  assert.equal(isValidHex("#009DCE"), true);
  assert.equal(isValidHex("#09DCE"), false);
  assert.deepEqual(rgbFromHex("#009DCE"), { r: 0, g: 157, b: 206 });
});

test("groups PLA by brand line and color while ignoring weight and diameter", () => {
  const products = [
    product(),
    product({ id: "pla-rojo-285-2500-grilon3", diameter_mm: 2.85, weight_g: 2500 }),
    product({ id: "pla-rojo-175-1000-3n3", brand: "3N3", pantone: "", pantone_hex: "", estimated_color_hex: "#D82A22" }),
    product({ id: "petg-rojo", material: "PETG" }),
  ];
  const catalog = buildPlaColorCatalog(products);
  assert.equal(catalog.groups.length, 2);
  const grilon = catalog.groups.find((group) => group.brand === "Grilon3");
  assert.equal(grilon.presentations.length, 2);
  assert.deepEqual(grilon.presentations.map((item) => item.label), ["1 kg · 1.75 mm", "2.5 kg · 2.85 mm"]);
});

test("prefers Pantone, then estimate confidence, source, stock, and id", () => {
  const catalog = buildPlaColorCatalog([
    product({ id: "z-low", pantone: "", pantone_hex: "", estimated_color_hex: "#CC2222", estimated_color_confidence_band: "low", estimated_color_source: "name_only" }),
    product({ id: "b-high", pantone: "", pantone_hex: "", estimated_color_hex: "#DD2222", estimated_color_confidence_band: "high", estimated_color_source: "image_and_name" }),
    product({ id: "a-pantone", pantone_hex: "#D92920" }),
  ]);
  assert.equal(catalog.groups[0].representative.id, "a-pantone");
  assert.equal(catalog.groups[0].hex, "#D92920");
});

test("counts PLA products without usable color data", () => {
  const catalog = buildPlaColorCatalog([
    product(),
    product({ id: "missing", color: "Sin dato", pantone_hex: "", estimated_color_hex: "" }),
  ]);
  assert.equal(catalog.excludedCount, 1);
});

test("derives stock and de-duplicates identical presentations", () => {
  const catalog = buildPlaColorCatalog([
    product({ id: "out", offers: [{ stock_status: "out_of_stock" }] }),
    product({ id: "in", offers: [{ stock_status: "in_stock" }] }),
  ]);
  assert.equal(catalog.groups[0].inStock, true);
  assert.equal(catalog.groups[0].presentations.length, 1);
  assert.equal(catalog.groups[0].presentations[0].product.id, "in");
});

test("sorts, groups, and maps from current OKLCH values", () => {
  const groups = buildPlaColorCatalog([
    product({ id: "red", color: "Rojo", pantone_hex: "#FF0000" }),
    product({ id: "green", color: "Verde", pantone_hex: "#00AA44" }),
    product({ id: "white", color: "Blanco", pantone_hex: "#F7F7F7" }),
  ]).groups;
  assert.equal(sortPerceptually(groups).length, 3);
  assert.equal(groupColorFamilies(groups).get("Neutros").length, 1);
  assert.ok(buildColorMap(groups).every((item) => item.mapX >= 0 && item.mapX <= 100 && item.mapY >= 0 && item.mapY <= 100));
});

test("separates perceptual map points that share a tone and luminosity anchor", () => {
  const groups = buildPlaColorCatalog([
    product({ id: "red-a", color: "Rojo A", pantone_hex: "#CC3333" }),
    product({ id: "red-b", color: "Rojo B", pantone_hex: "#CC3333" }),
    product({ id: "white", color: "Blanco", pantone_hex: "#F7F7F7" }),
  ]).groups;
  const points = buildColorMap(groups);

  assert.equal(points.length, 3);
  assert.ok(points.every((point) => point.mapX >= 0 && point.mapX <= 100));
  assert.ok(points.every((point) => point.mapY >= 0 && point.mapY <= 100));
  assert.ok(points.every((point) => point.mapSize >= 12 && point.mapSize <= 24));
  assert.notDeepEqual(
    [points[0].mapX, points[0].mapY],
    [points[1].mapX, points[1].mapY],
  );
});

test("separates the continuous palette into intense, muted, earth, and neutral bands", () => {
  const groups = buildPlaColorCatalog([
    product({ id: "red", color: "Rojo", pantone_hex: "#E63424" }),
    product({ id: "pastel", color: "Pastel", pantone_hex: "#DFA0BA" }),
    product({ id: "earth", color: "Tierra", pantone_hex: "#7B432D" }),
    product({ id: "white", color: "Blanco", pantone_hex: "#FBFAF4" }),
    product({ id: "black", color: "Negro", pantone_hex: "#17191C" }),
  ]).groups;
  const bands = groupContinuousBands(groups);

  assert.deepEqual([...bands.keys()], ["intense", "muted", "earth", "neutral"]);
  assert.equal(colorOrderBand(groups.find((group) => group.id.includes("rojo"))), "intense");
  assert.equal(colorOrderBand(groups.find((group) => group.id.includes("pastel"))), "muted");
  assert.equal(colorOrderBand(groups.find((group) => group.id.includes("tierra"))), "earth");
  assert.deepEqual(bands.get("neutral").map((group) => group.id), ["grilon3-pla-standard-blanco", "grilon3-pla-standard-negro"]);
});

test("returns exactly three ordered CIEDE2000 neighbors and excludes the source group", () => {
  const groups = buildPlaColorCatalog([
    product({ id: "ref", color: "Referencia", pantone_hex: "#FF0000" }),
    product({ id: "one", color: "Uno", pantone_hex: "#F01010" }),
    product({ id: "two", color: "Dos", pantone_hex: "#D92920" }),
    product({ id: "three", color: "Tres", pantone_hex: "#B03020" }),
    product({ id: "four", color: "Cuatro", pantone_hex: "#0066CC" }),
  ]).groups;
  const source = groups.find((group) => group.name === "Referencia");
  const results = findSimilarColors(groups, source.hex, source.id);
  assert.equal(results.length, 3);
  assert.equal(results.some((item) => item.group.id === source.id), false);
  assert.ok(results[0].distance <= results[1].distance && results[1].distance <= results[2].distance);
});

test("returns the available neighbors when a stock filter leaves fewer than three", () => {
  const groups = buildPlaColorCatalog([
    product({ id: "ref", color: "Referencia", pantone_hex: "#FF0000" }),
    product({ id: "one", color: "Uno", pantone_hex: "#F01010" }),
    product({ id: "out", color: "Sin stock", pantone_hex: "#EE2020", offers: [{ stock_status: "out_of_stock" }] }),
  ]).groups;
  const source = groups.find((group) => group.name === "Referencia");
  const stockedGroups = groups.filter((group) => group.inStock);

  assert.equal(findSimilarColors(stockedGroups, source.hex, source.id, 3).length, 1);
});

test("labels distances and enforces four compared colors", () => {
  assert.equal(distanceLabel(2.9), "Muy cercano");
  assert.equal(distanceLabel(3), "Cercano");
  assert.equal(distanceLabel(8), "Alternativa");
  assert.deepEqual(toggleComparedColor(["a", "b", "c", "d"], "e"), {
    ids: ["a", "b", "c", "d"],
    message: "El comparador admite hasta cuatro colores. Quitá uno para sumar otro.",
  });
});
