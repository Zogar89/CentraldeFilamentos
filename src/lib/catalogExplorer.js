import { converter } from "culori";

import { productColorHex } from "./colorPicker.js";
import { presentationRank } from "./shared.js";

const materialOrder = ["PLA", "PETG", "ABS", "TPU", "Nylon", "ASA"];
const coreMaterials = new Set(materialOrder);
const colorFamilyOrder = [
  "lights",
  "blacks",
  "grays",
  "reds",
  "oranges",
  "yellows",
  "greens",
  "turquoises",
  "blues",
  "violets",
  "pinks",
  "unknown",
];
const toOklch = converter("oklch");

function productImage(product) {
  return product?.thumbnail_url || product?.image_url || "";
}

function materialProducts(products, selectedMaterial) {
  return products.filter((product) => matchesMaterialSelection(product, selectedMaterial));
}

function representativeProduct(products) {
  return products.slice().sort((left, right) => (
    Number(Boolean(productImage(right))) - Number(Boolean(productImage(left)))
  ))[0] || null;
}

function representativeColorProduct(products) {
  return products.slice().sort((left, right) => (
    Number(Boolean(productColorHex(right))) - Number(Boolean(productColorHex(left)))
    || Number(Boolean(right.pantone_hex)) - Number(Boolean(left.pantone_hex))
    || productStockTotal(right) - productStockTotal(left)
    || String(left.id || "").localeCompare(String(right.id || ""), "es-AR")
  ))[0] || null;
}

function familySwatchHexes(products) {
  const sorted = products.slice().sort((left, right) => (
    Number(Boolean(right.pantone_hex)) - Number(Boolean(left.pantone_hex))
    || productStockTotal(right) - productStockTotal(left)
    || String(left.id || "").localeCompare(String(right.id || ""), "es-AR")
  ));
  return [...new Set(sorted.map((product) => productColorHex(product)).filter(Boolean))].slice(0, 3);
}

function colorPosition(choice) {
  const color = choice.hex ? toOklch(choice.hex) : null;
  if (!color || color.h === undefined || Number(color.c || 0) < 0.025) {
    return [0, -Number(color?.l ?? 0), choice.name];
  }
  return [1, Number(color.h || 0), -Number(color.l || 0), choice.name];
}

function compareColorChoices(left, right) {
  const leftKey = colorPosition(left);
  const rightKey = colorPosition(right);
  for (let index = 0; index < Math.max(leftKey.length, rightKey.length); index += 1) {
    if (leftKey[index] === rightKey[index]) continue;
    if (typeof leftKey[index] === "number" && typeof rightKey[index] === "number") {
      return leftKey[index] - rightKey[index];
    }
    return String(leftKey[index] || "").localeCompare(String(rightKey[index] || ""), "es-AR");
  }
  return 0;
}

export function colorFamilyForHex(hex) {
  const color = hex ? toOklch(hex) : null;
  if (!color) return { id: "unknown", label: "Otros tonos" };

  const lightness = Number(color.l ?? 0);
  const chroma = Number(color.c ?? 0);
  const hue = Number(color.h ?? 0);
  if (chroma < 0.035) {
    if (lightness >= 0.86) return { id: "lights", label: "Claros" };
    if (lightness <= 0.30) return { id: "blacks", label: "Negros" };
    return { id: "grays", label: "Grises" };
  }
  if (hue >= 345 || hue < 18) return { id: "reds", label: "Rojos" };
  if (hue < 55) return { id: "oranges", label: "Naranjas" };
  if (hue < 120) return { id: "yellows", label: "Amarillos" };
  if (hue < 165) return { id: "greens", label: "Verdes" };
  if (hue < 215) return { id: "turquoises", label: "Turquesas" };
  if (hue < 270) return { id: "blues", label: "Azules" };
  if (hue < 320) return { id: "violets", label: "Violetas" };
  return { id: "pinks", label: "Rosas" };
}

function colorFamilyForName(name) {
  const value = String(name || "").toLocaleLowerCase("es-AR");
  const families = [
    [/amarill|dorado|\boro\b|mostaza|arena|beige|crema|vainilla|marfil|caramelo|dulce de leche|bronce/, { id: "yellows", label: "Amarillos" }],
    [/verde|lima|oliva|pino|menta/, { id: "greens", label: "Verdes" }],
    [/turquesa|cian|aqua|aguamarina/, { id: "turquoises", label: "Turquesas" }],
    [/azul|celeste|navy/, { id: "blues", label: "Azules" }],
    [/violeta|lila|morado|purpura|lavanda/, { id: "violets", label: "Violetas" }],
    [/rosa|pink|magenta|fucsia/, { id: "pinks", label: "Rosas" }],
    [/rojo|bordo|cerezo|rubi|frutilla|carmesi/, { id: "reds", label: "Rojos" }],
    [/naranja|cobre|terracota|salmon/, { id: "oranges", label: "Naranjas" }],
    [/blanco|natural|cristal|transparente|perla/, { id: "lights", label: "Claros" }],
    [/negro|azabache|carbon|dark/, { id: "blacks", label: "Negros" }],
    [/gris|plata|platino|acero/, { id: "grays", label: "Grises" }],
  ];
  return families.find(([pattern]) => pattern.test(value))?.[1] || null;
}

export function colorFamilyForProduct(product) {
  return colorFamilyForName(product?.color) || colorFamilyForHex(productColorHex(product));
}

export function matchesColorSelection(product, selectedChoice) {
  if (!selectedChoice) return true;
  if (selectedChoice.selectionMode === "exact") return product?.color === selectedChoice.name;
  return colorFamilyForProduct(product).id === selectedChoice.familyId;
}

export function productStockTotal(product) {
  return (product?.offers || []).reduce((total, offer) => {
    const quantity = Number(offer?.stock_quantity);
    return total + (Number.isFinite(quantity) && quantity > 0 ? quantity : 0);
  }, 0);
}

export function matchesMaterialSelection(product, selectedMaterial) {
  const material = String(product?.material || "");
  if (selectedMaterial === "Otros") return Boolean(material) && !coreMaterials.has(material);
  return material === selectedMaterial;
}

export function materialChoices(products) {
  const choices = materialOrder.flatMap((material) => {
    const matches = products.filter((product) => product.material === material);
    if (!matches.length) return [];
    const representative = representativeProduct(matches);
    return [{
      id: material,
      label: material,
      materials: [material],
      count: matches.length,
      stockTotal: matches.reduce((total, product) => total + productStockTotal(product), 0),
      imageUrl: productImage(representative),
    }];
  });
  const otherProducts = products.filter((product) => product.material && !coreMaterials.has(product.material));
  if (otherProducts.length) {
    const representative = representativeProduct(otherProducts);
    choices.push({
      id: "Otros",
      label: "Otros",
      materials: [...new Set(otherProducts.map((product) => product.material))].sort((left, right) => left.localeCompare(right, "es-AR")),
      count: otherProducts.length,
      stockTotal: otherProducts.reduce((total, product) => total + productStockTotal(product), 0),
      imageUrl: productImage(representative),
    });
  }
  return choices;
}

function exactColorChoices(products) {
  const grouped = new Map();
  for (const product of products) {
    const name = String(product.color || "").trim();
    if (!name || name === "Sin color") continue;
    if (!grouped.has(name)) grouped.set(name, []);
    grouped.get(name).push(product);
  }
  return [...grouped.entries()].map(([name, items]) => {
    const representative = representativeColorProduct(items);
    const family = colorFamilyForProduct(representative);
    const hex = productColorHex(representative);
    return {
      id: `exact:${name}`,
      name,
      hex,
      swatchHexes: hex ? [hex] : [],
      selectionMode: "exact",
      familyId: family.id,
      familyLabel: family.label,
      stockTotal: items.reduce((total, product) => total + productStockTotal(product), 0),
      productCount: items.length,
      exactColorCount: 1,
      imageUrl: productImage(representative),
      representative,
    };
  }).sort(compareColorChoices);
}

function familyColorChoices(products) {
  const grouped = new Map();
  for (const product of products) {
    const name = String(product.color || "").trim();
    if (!name || name === "Sin color") continue;
    const family = colorFamilyForProduct(product);
    if (!grouped.has(family.id)) grouped.set(family.id, { family, items: [] });
    grouped.get(family.id).items.push(product);
  }
  return [...grouped.values()].map(({ family, items }) => {
    const representative = representativeColorProduct(items);
    const swatchHexes = familySwatchHexes(items);
    return {
      id: `family:${family.id}`,
      name: family.label,
      hex: swatchHexes[0] || productColorHex(representative),
      swatchHexes,
      selectionMode: "family",
      familyId: family.id,
      familyLabel: family.label,
      stockTotal: items.reduce((total, product) => total + productStockTotal(product), 0),
      productCount: items.length,
      exactColorCount: new Set(items.map((product) => product.color).filter(Boolean)).size,
      imageUrl: productImage(representative),
      representative,
    };
  }).sort((left, right) => (
    colorFamilyOrder.indexOf(left.familyId) - colorFamilyOrder.indexOf(right.familyId)
    || left.name.localeCompare(right.name, "es-AR")
  ));
}

export function colorChoices(products, selectedMaterial) {
  const scopedProducts = materialProducts(products, selectedMaterial);
  return selectedMaterial === "PLA"
    ? familyColorChoices(scopedProducts)
    : exactColorChoices(scopedProducts);
}

function compareCatalogText(left, right) {
  return String(left || "").localeCompare(String(right || ""), "es-AR", {
    numeric: true,
    sensitivity: "base",
  });
}

function compareOptionalNumber(left, right) {
  const leftNumber = Number(left);
  const rightNumber = Number(right);
  const leftRank = Number.isFinite(leftNumber) && leftNumber > 0 ? leftNumber : Number.POSITIVE_INFINITY;
  const rightRank = Number.isFinite(rightNumber) && rightNumber > 0 ? rightNumber : Number.POSITIVE_INFINITY;
  if (leftRank === rightRank) return 0;
  return leftRank - rightRank;
}

export function compareCatalogProducts(left, right) {
  return compareCatalogText(left?.color, right?.color)
    || compareCatalogText(left?.brand, right?.brand)
    || presentationRank(left || {}) - presentationRank(right || {})
    || compareOptionalNumber(left?.diameter_mm, right?.diameter_mm)
    || compareCatalogText(left?.display_name || left?.id, right?.display_name || right?.id);
}

export function compareExplorerProducts(left, right) {
  return productStockTotal(right) - productStockTotal(left)
    || [left.color || "", left.brand || "", left.display_name || left.id || ""].join(" ").localeCompare(
      [right.color || "", right.brand || "", right.display_name || right.id || ""].join(" "),
      "es-AR",
    );
}
