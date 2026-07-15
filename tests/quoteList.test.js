import assert from "node:assert/strict";
import { afterEach, test } from "node:test";

import {
  combineQuoteListItems,
  incrementQuoteListItem,
  initializeQuoteList,
  loadQuoteList,
  normalizeQuoteList,
  nextBoxQuantity,
  quoteItemCode,
  quoteItemMissingBadges,
  quoteListSchemaVersion,
  quoteListStorageKey,
  saveQuoteList,
  serializeQuoteListExport,
  previewQuoteListImport,
} from "../src/lib/quoteList.js";

function createStorage(initialValue = null, { failWrite = false } = {}) {
  let value = initialValue;
  let writes = 0;
  return {
    getItem(key) {
      return key === quoteListStorageKey ? value : null;
    },
    setItem(key, nextValue) {
      if (failWrite) throw new Error("storage unavailable");
      if (key === quoteListStorageKey) {
        value = nextValue;
        writes += 1;
      }
    },
    value: () => value,
    writes: () => writes,
  };
}

function storedState(items, settings = { showQuickControls: false }) {
  return JSON.stringify({
    schemaVersion: quoteListSchemaVersion,
    items,
    settings,
  });
}

afterEach(() => {
  delete globalThis.localStorage;
});

test("a failed catalog load preserves the local quote list without writing", () => {
  const storage = createStorage(storedState([{ productId: "pla-negro", quantity: 3 }]));
  globalThis.localStorage = storage;

  const loaded = loadQuoteList();
  const initialized = initializeQuoteList(loaded, { ok: false, products: [] });

  assert.deepEqual(initialized.items, loaded.items);
  assert.equal(initialized.shouldSave, false);
  assert.equal(storage.writes(), 0);
  assert.equal(JSON.parse(storage.value()).items[0].quantity, 3);
});

test("an unknown schema remains byte-for-byte intact and blocks writes", () => {
  const raw = JSON.stringify({
    schemaVersion: 9,
    items: [{ productId: "future-product", quantity: 7, futureField: true }],
    futureSettings: { grouped: true },
  });
  const storage = createStorage(raw);
  globalThis.localStorage = storage;

  const loaded = loadQuoteList();
  const initialized = initializeQuoteList(loaded, { ok: true, products: [] });
  const saved = saveQuoteList({ ...loaded, items: [] });

  assert.equal(loaded.readOnly, true);
  assert.equal(initialized.shouldSave, false);
  assert.equal(saved.blocked, true);
  assert.equal(storage.writes(), 0);
  assert.equal(storage.value(), raw);
});

test("a failed write returns the complete session payload", () => {
  globalThis.localStorage = createStorage(null, { failWrite: true });
  const sessionItems = [{ productId: "petg-azul", quantity: 5 }];

  const result = saveQuoteList({ items: sessionItems, settings: { showQuickControls: true } });

  assert.equal(result.ok, false);
  assert.equal(result.saveError, "write");
  assert.equal(result.payload.items[0].productId, "petg-azul");
  assert.equal(result.payload.items[0].quantity, 5);
  assert.equal(result.payload.settings.showQuickControls, true);
});

test("normalization removes duplicate products and keeps the first quantity", () => {
  const normalized = normalizeQuoteList({
    schemaVersion: quoteListSchemaVersion,
    items: [
      { productId: "pla-blanco", quantity: 2 },
      { productId: "pla-blanco", quantity: 12 },
    ],
  });

  assert.equal(normalized.items.length, 1);
  assert.equal(normalized.items[0].quantity, 2);
});

test("reconciliation removes missing products and refreshes catalog snapshots", () => {
  const loaded = normalizeQuoteList({
    schemaVersion: quoteListSchemaVersion,
    items: [
      { productId: "kept", productName: "Nombre anterior", quantity: 4 },
      { productId: "removed", quantity: 1 },
    ],
  });
  const products = [{
    id: "kept",
    display_name: "PLA Negro 1 kg",
    material: "PLA",
    variant: "PLA Standard",
    color: "Negro",
    brand: "Grilon3",
    diameter_mm: 1.75,
    weight_g: 1000,
    offers: [],
  }];

  const initialized = initializeQuoteList(loaded, { ok: true, products });

  assert.equal(initialized.removedCount, 1);
  assert.equal(initialized.shouldSave, true);
  assert.equal(initialized.items.length, 1);
  assert.equal(initialized.items[0].productId, "kept");
  assert.equal(initialized.items[0].quantity, 4);
  assert.equal(initialized.items[0].color, "Negro");
});

test("quantity changes persist as normalized whole-spool values", () => {
  const storage = createStorage();
  globalThis.localStorage = storage;

  const result = saveQuoteList({
    items: [{ productId: "tpu-rojo", quantity: 6.9 }],
    settings: { showQuickControls: false },
  });
  const persisted = JSON.parse(storage.value());

  assert.equal(result.ok, true);
  assert.equal(storage.writes(), 1);
  assert.equal(persisted.items[0].quantity, 6);
});

test("an original provider name does not hide a missing article code", () => {
  const item = {
    originalName: "GRILON3 PLA NEGRO 1.75 MM X 1 KG",
    diameterMm: 1.75,
    presentation: "1 kg",
    material: "PLA",
    hasOnlineStock: true,
  };

  assert.equal(quoteItemCode(item), "");
  assert.deepEqual(quoteItemMissingBadges(item), ["sin codigo"]);
});

test("box shortcut completes the next multiple of twelve", () => {
  assert.equal(nextBoxQuantity(1), 12);
  assert.equal(nextBoxQuantity(11), 12);
  assert.equal(nextBoxQuantity(12), 24);
  assert.equal(nextBoxQuantity(13), 24);
});

test("export and import preserve valid items through the catalog", () => {
  const exported = serializeQuoteListExport({
    items: [{ productId: "pla-negro", quantity: 12 }],
    settings: { showQuickControls: true },
  }, "2026-06-19T12:00:00Z");
  const preview = previewQuoteListImport(exported, [{
    id: "pla-negro",
    display_name: "PLA Negro 1 kg",
    material: "PLA",
    variant: "PLA Standard",
    color: "Negro",
    brand: "Grilon3",
    diameter_mm: 1.75,
    weight_g: 1000,
    offers: [],
  }]);

  assert.equal(preview.ok, true);
  assert.equal(preview.validCount, 1);
  assert.equal(preview.items[0].quantity, 12);
  assert.equal(preview.items[0].color, "Negro");
});

test("invalid imports do not produce replacement items", () => {
  assert.equal(previewQuoteListImport("not-json", []).ok, false);
  assert.equal(previewQuoteListImport(JSON.stringify({ items: [] }), []).ok, false);
});

test("combine keeps local-only items and imported duplicates win", () => {
  const combined = combineQuoteListItems(
    [{ productId: "local", quantity: 2 }, { productId: "shared", quantity: 1 }],
    [{ productId: "shared", quantity: 12 }, { productId: "new", quantity: 3 }],
  );

  assert.deepEqual(combined.map((item) => [item.productId, item.quantity]), [
    ["local", 2], ["shared", 12], ["new", 3],
  ]);
});

test("increments one concrete product without changing other quote items", () => {
  const product = {
    id: "pla-rojo-175-1000-grilon3",
    display_name: "Grilon3 PLA Rojo 1 kg",
    material: "PLA",
    color: "Rojo",
    brand: "Grilon3",
    diameter_mm: 1.75,
    weight_g: 1000,
    offers: [{ stock_status: "in_stock", stock_quantity: 2 }],
  };
  const once = incrementQuoteListItem([], product);
  const twice = incrementQuoteListItem(once, product);
  assert.equal(twice.length, 1);
  assert.equal(twice[0].productId, product.id);
  assert.equal(twice[0].quantity, 2);
});
