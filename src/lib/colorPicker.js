import { converter, differenceCiede2000 } from "culori";
import {
  comparePresentations,
  foldText,
  formatPresentation,
  lineLabel,
  slugText,
} from "./shared.js";

const toOklch = converter("oklch");
const toRgb = converter("rgb");
const ciede2000 = differenceCiede2000();
const familyOrder = ["Rojos", "Naranjas", "Amarillos", "Verdes", "Turquesas", "Azules", "Violetas", "Rosas", "Neutros"];
const continuousBandOrder = ["intense", "muted", "earth", "neutral"];

export function normalizeHex(value) {
  const raw = String(value || "").trim().toUpperCase();
  return raw.startsWith("#") ? raw : `#${raw}`;
}

export function isValidHex(value) {
  return /^#[0-9A-F]{6}$/i.test(normalizeHex(value));
}

export function rgbFromHex(hex) {
  const rgb = toRgb(normalizeHex(hex));
  return {
    r: Math.round((rgb?.r || 0) * 255),
    g: Math.round((rgb?.g || 0) * 255),
    b: Math.round((rgb?.b || 0) * 255),
  };
}

export function productColorHex(product) {
  if (isValidHex(product?.pantone_hex)) return normalizeHex(product.pantone_hex);
  if (isValidHex(product?.estimated_color_hex)) return normalizeHex(product.estimated_color_hex);
  return "";
}

function productInStock(product) {
  return (product?.offers || []).some((offer) => offer.stock_status === "in_stock");
}

function confidenceRank(value) {
  return ({ high: 0, medium: 1, low: 2 })[String(value || "").toLowerCase()] ?? 3;
}

function sourceRank(value) {
  return ({ image_and_name: 0, name_only: 1 })[String(value || "").toLowerCase()] ?? 2;
}

function compareRepresentatives(left, right) {
  const leftPantone = isValidHex(left.pantone_hex) ? 0 : 1;
  const rightPantone = isValidHex(right.pantone_hex) ? 0 : 1;
  return leftPantone - rightPantone
    || confidenceRank(left.estimated_color_confidence_band) - confidenceRank(right.estimated_color_confidence_band)
    || sourceRank(left.estimated_color_source) - sourceRank(right.estimated_color_source)
    || Number(productInStock(right)) - Number(productInStock(left))
    || String(left.id).localeCompare(String(right.id), "es-AR");
}

function logicalColorKey(product) {
  return [product.brand || "Sin marca", lineLabel(product), product.color || "Sin color"].map(foldText).join("||");
}

function presentationKey(product) {
  return [formatPresentation(product), product.diameter_mm ?? ""].join("||");
}

function choosePresentation(current, candidate) {
  if (!current) return candidate;
  if (productInStock(candidate) !== productInStock(current)) return productInStock(candidate) ? candidate : current;
  return String(candidate.id).localeCompare(String(current.id), "es-AR") < 0 ? candidate : current;
}

function buildGroup(products) {
  const ordered = products.slice().sort(compareRepresentatives);
  const representative = ordered[0];
  const diameterCount = new Set(products.map((product) => product.diameter_mm).filter(Boolean)).size;
  const presentationByKey = new Map();
  for (const product of products) {
    const key = presentationKey(product);
    presentationByKey.set(key, choosePresentation(presentationByKey.get(key), product));
  }
  const presentations = [...presentationByKey.values()].sort(comparePresentations).map((product) => {
    const base = formatPresentation(product) || "Presentación a confirmar";
    return {
      id: product.id,
      label: diameterCount > 1 && product.diameter_mm ? `${base} · ${product.diameter_mm} mm` : base,
      inStock: productInStock(product),
      product,
    };
  });
  const line = lineLabel(representative);
  const name = representative.color || "Sin color";
  const brand = representative.brand || "Sin marca";
  return {
    id: slugText([brand, line, name].join("-")),
    name,
    brand,
    line,
    hex: productColorHex(representative),
    pantone: representative.pantone || "",
    estimated: !isValidHex(representative.pantone_hex),
    warning: representative.estimated_color_warning || "",
    materialSwatchUrl: representative.material_swatch_url || "",
    inStock: products.some(productInStock),
    representative,
    products: products.slice(),
    presentations,
  };
}

export function buildPlaColorCatalog(products) {
  const pla = (products || []).filter((product) => product.material === "PLA");
  const eligible = pla.filter((product) => productColorHex(product));
  const grouped = new Map();
  for (const product of eligible) {
    const key = logicalColorKey(product);
    grouped.set(key, [...(grouped.get(key) || []), product]);
  }
  return {
    groups: [...grouped.values()].map(buildGroup).sort((left, right) => left.id.localeCompare(right.id, "es-AR")),
    excludedCount: pla.length - eligible.length,
  };
}

function oklchFor(group) {
  const value = toOklch(group.hex) || {};
  return {
    l: Number(value.l || 0),
    c: Number(value.c || 0),
    h: Number.isFinite(value.h) ? value.h : 0,
  };
}

export function colorOrderBand(group) {
  const { l, c, h } = oklchFor(group);
  if (c < 0.035) return "neutral";
  if (h >= 15 && h < 85 && l < 0.62 && c < 0.11) return "earth";
  return c >= 0.11 ? "intense" : "muted";
}

export function groupContinuousBands(groups) {
  const result = new Map(continuousBandOrder.map((band) => [band, []]));
  for (const group of groups || []) result.get(colorOrderBand(group)).push(group);
  for (const [band, items] of result) {
    items.sort((left, right) => {
      const a = oklchFor(left);
      const b = oklchFor(right);
      if (band === "neutral") return b.l - a.l || left.id.localeCompare(right.id, "es-AR");
      return a.h - b.h || b.l - a.l || b.c - a.c || left.id.localeCompare(right.id, "es-AR");
    });
    if (!items.length) result.delete(band);
  }
  return result;
}

export function sortPerceptually(groups) {
  return (groups || []).slice().sort((left, right) => {
    const a = oklchFor(left);
    const b = oklchFor(right);
    const neutralA = a.c < 0.045;
    const neutralB = b.c < 0.045;
    if (neutralA !== neutralB) return neutralA ? 1 : -1;
    if (neutralA) return b.l - a.l || left.id.localeCompare(right.id, "es-AR");
    return a.h - b.h || b.l - a.l || b.c - a.c || left.id.localeCompare(right.id, "es-AR");
  });
}

export function colorFamily(group) {
  const value = oklchFor(group);
  if (value.c < 0.045) return "Neutros";
  if (value.h < 25 || value.h >= 350) return "Rojos";
  if (value.h < 65) return "Naranjas";
  if (value.h < 115) return "Amarillos";
  if (value.h < 170) return "Verdes";
  if (value.h < 225) return "Turquesas";
  if (value.h < 285) return "Azules";
  if (value.h < 330) return "Violetas";
  return "Rosas";
}

export function groupColorFamilies(groups) {
  const result = new Map(familyOrder.map((name) => [name, []]));
  for (const group of sortPerceptually(groups)) result.get(colorFamily(group)).push(group);
  for (const [name, items] of [...result]) {
    if (!items.length) result.delete(name);
  }
  return result;
}

function clamp(value, lower, upper) {
  return Math.min(upper, Math.max(lower, value));
}

function mapAnchor(value) {
  return {
    x: value.c < 0.035 ? 96 : value.h / 3.6,
    y: 100 - value.l * 100,
  };
}

function separateMapPoints(points) {
  const ordered = points.slice().sort((left, right) => (
    left.anchorY - right.anchorY || left.anchorX - right.anchorX || left.id.localeCompare(right.id, "es-AR")
  ));
  const placed = [];
  for (const point of ordered) {
    let candidate = { x: point.anchorX, y: point.anchorY };
    for (let attempt = 0; attempt < 48; attempt += 1) {
      const collides = placed.some((other) => Math.hypot(candidate.x - other.mapX, candidate.y - other.mapY) < 3.4);
      if (!collides) break;
      const angle = (attempt + 1) * 2.399963;
      const radius = 2 + Math.floor(attempt / 6) * 1.5;
      candidate = {
        x: clamp(point.anchorX + Math.cos(angle) * radius, 2, 98),
        y: clamp(point.anchorY + Math.sin(angle) * radius, 2, 98),
      };
    }
    placed.push({ ...point, mapX: candidate.x, mapY: candidate.y });
  }
  return placed;
}

export function buildColorMap(groups) {
  const points = (groups || []).map((group) => {
    const oklch = oklchFor(group);
    const anchor = mapAnchor(oklch);
    return { ...group, oklch, anchorX: anchor.x, anchorY: anchor.y, mapSize: clamp(12 + oklch.c * 55, 12, 24) };
  });
  return separateMapPoints(points).sort((left, right) => left.mapY - right.mapY || left.mapX - right.mapX || left.id.localeCompare(right.id, "es-AR"));
}

export function findSimilarColors(groups, referenceHex, excludedGroupId = "", limit = 3) {
  const hex = normalizeHex(referenceHex);
  if (!isValidHex(hex)) return [];
  return (groups || []).filter((group) => group.id !== excludedGroupId).map((group) => ({
    group,
    distance: ciede2000(hex, group.hex),
  })).sort((left, right) => (
    left.distance - right.distance || left.group.id.localeCompare(right.group.id, "es-AR")
  )).slice(0, limit);
}

export function distanceLabel(distance) {
  if (distance < 3) return "Muy cercano";
  if (distance < 8) return "Cercano";
  return "Alternativa";
}

export function toggleComparedColor(ids, id, max = 4) {
  if (ids.includes(id)) {
    return { ids: ids.filter((value) => value !== id), message: "Color quitado del comparador." };
  }
  if (ids.length >= max) {
    return { ids: ids.slice(), message: "El comparador admite hasta cuatro colores. Quitá uno para sumar otro." };
  }
  return { ids: [...ids, id], message: "Color agregado al comparador." };
}
