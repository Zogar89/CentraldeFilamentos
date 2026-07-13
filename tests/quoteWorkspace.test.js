import assert from "node:assert/strict";
import { test } from "node:test";

import { get } from "svelte/store";

import {
  quoteListExportKind,
  quoteListSchemaVersion,
  quoteListStorageKey,
  serializeQuoteListExport,
} from "../src/lib/quoteList.js";
import { createQuoteWorkspace } from "../src/lib/quoteWorkspace.js";

const PRODUCT = {
  id: "pla-negro",
  display_name: "PLA Negro 1 kg",
  material: "PLA",
  variant: "PLA Standard",
  color: "Negro",
  brand: "Grilon3",
  diameter_mm: 1.75,
  weight_g: 1000,
  offers: [{ original_name: "PLA NEGRO", stock_status: "in_stock", stock_quantity: 4 }],
};

function quotePayload(items, settings) {
  return JSON.stringify({
    schemaVersion: quoteListSchemaVersion,
    items,
    ...(settings === undefined ? {} : { settings }),
  });
}

function memoryStorage(initialValue = null, { failRead = false, failWrite = false } = {}) {
  let value = initialValue;
  let writeCount = 0;
  return {
    getItem(key) {
      if (failRead) throw new Error("read unavailable");
      return key === quoteListStorageKey ? value : null;
    },
    setItem(key, nextValue) {
      if (failWrite) throw new Error("write unavailable");
      if (key === quoteListStorageKey) {
        value = nextValue;
        writeCount += 1;
      }
    },
    value: () => value,
    writes: () => writeCount,
  };
}

function installThrowingLocalStorage(t) {
  const descriptor = Object.getOwnPropertyDescriptor(globalThis, "localStorage");
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    get() {
      throw new DOMException("Access denied", "SecurityError");
    },
  });
  t.after(() => {
    if (descriptor) Object.defineProperty(globalThis, "localStorage", descriptor);
    else delete globalThis.localStorage;
  });
}

test("preserves an existing v1 item and addProduct writes one increment", () => {
  const storage = memoryStorage(quotePayload([{ productId: PRODUCT.id, quantity: 1 }]));
  const workspace = createQuoteWorkspace({ products: [PRODUCT], catalogAvailable: true, storage });

  workspace.addProduct(PRODUCT);

  assert.equal(get(workspace.state).items[0].quantity, 2);
  assert.equal(storage.writes(), 1);
  assert.equal(JSON.parse(storage.value()).schemaVersion, 1);
  assert.equal(JSON.parse(storage.value()).items[0].quantity, 2);
});

test("workspace instances keep storage and state isolated", () => {
  const firstStorage = memoryStorage();
  const secondStorage = memoryStorage();
  const first = createQuoteWorkspace({ products: [PRODUCT], catalogAvailable: true, storage: firstStorage });
  const second = createQuoteWorkspace({ products: [PRODUCT], catalogAvailable: true, storage: secondStorage });

  first.addProduct(PRODUCT);

  assert.equal(get(first.state).items.length, 1);
  assert.equal(get(second.state).items.length, 0);
  assert.equal(firstStorage.writes(), 1);
  assert.equal(secondStorage.writes(), 0);
});

test("failed catalog initialization preserves stored items and writes zero", () => {
  const original = quotePayload([{ productId: "stored-only", quantity: 3 }]);
  const storage = memoryStorage(original);

  const workspace = createQuoteWorkspace({ products: [], catalogAvailable: false, storage });

  assert.equal(get(workspace.state).items[0].productId, "stored-only");
  assert.equal(storage.writes(), 0);
  assert.equal(storage.value(), original);
});

test("future schema remains read-only and all mutating actions write zero", () => {
  const raw = JSON.stringify({
    schemaVersion: 9,
    items: [{ productId: "future", quantity: 7, futureField: true }],
    futureSettings: { grouped: true },
  });
  const storage = memoryStorage(raw);
  const workspace = createQuoteWorkspace({ products: [PRODUCT], catalogAvailable: true, storage });
  const preview = workspace.previewImport(serializeQuoteListExport({ items: [{ productId: PRODUCT.id }] }));

  workspace.addProduct(PRODUCT);
  workspace.setQuantity("future", 2);
  workspace.removeProduct("future");
  workspace.clear();
  workspace.toggleQuickControls();
  workspace.applyImport(preview, "replace");

  const state = get(workspace.state);
  assert.equal(state.readOnly, true);
  assert.deepEqual(state.preservedPayload, JSON.parse(raw));
  assert.deepEqual(state.items, []);
  assert.equal(storage.writes(), 0);
  assert.equal(storage.value(), raw);
});

test("quick controls default true for new and legacy payloads, then toggle once per write", () => {
  const newStorage = memoryStorage();
  const legacyStorage = memoryStorage(quotePayload([]));
  const fresh = createQuoteWorkspace({ products: [], catalogAvailable: true, storage: newStorage });
  const legacy = createQuoteWorkspace({ products: [], catalogAvailable: true, storage: legacyStorage });

  assert.equal(get(fresh.state).settings.showQuickControls, true);
  assert.equal(get(legacy.state).settings.showQuickControls, true);

  fresh.toggleQuickControls();
  assert.equal(get(fresh.state).settings.showQuickControls, false);
  assert.equal(JSON.parse(newStorage.value()).settings.showQuickControls, false);
  fresh.toggleQuickControls();
  assert.equal(get(fresh.state).settings.showQuickControls, true);
  assert.equal(newStorage.writes(), 2);
});

test("quantity, removal and clear normalize values and write once each", () => {
  const storage = memoryStorage(quotePayload([{ productId: PRODUCT.id, quantity: 2 }]));
  const workspace = createQuoteWorkspace({ products: [PRODUCT], catalogAvailable: true, storage });

  workspace.setQuantity(PRODUCT.id, 6.9);
  assert.equal(get(workspace.state).items[0].quantity, 6);
  workspace.setQuantity(PRODUCT.id, 0);
  assert.equal(get(workspace.state).items[0].quantity, 1);
  workspace.removeProduct(PRODUCT.id);
  assert.equal(get(workspace.state).items.length, 0);
  workspace.addProduct(PRODUCT);
  workspace.clear();

  assert.equal(get(workspace.state).items.length, 0);
  assert.equal(storage.writes(), 5);
});

test("import preview is pure and apply supports combine and replace", () => {
  const storage = memoryStorage(quotePayload([{ productId: PRODUCT.id, quantity: 2 }]));
  const secondProduct = { ...PRODUCT, id: "petg-azul", material: "PETG", variant: "PETG", color: "Azul" };
  const workspace = createQuoteWorkspace({ products: [PRODUCT, secondProduct], catalogAvailable: true, storage });
  const exported = serializeQuoteListExport({ items: [{ productId: secondProduct.id, quantity: 4 }] });

  const preview = workspace.previewImport(exported);
  assert.equal(preview.ok, true);
  assert.equal(storage.writes(), 0);
  workspace.applyImport(preview, "combine");
  assert.deepEqual(get(workspace.state).items.map((item) => item.productId), [PRODUCT.id, secondProduct.id]);
  assert.equal(storage.writes(), 1);

  const replacement = workspace.previewImport(serializeQuoteListExport({ items: [{ productId: PRODUCT.id, quantity: 8 }] }));
  workspace.applyImport(replacement, "replace");
  assert.deepEqual(get(workspace.state).items.map((item) => [item.productId, item.quantity]), [[PRODUCT.id, 8]]);
  assert.equal(storage.writes(), 2);
});

test("exportJson matches the established serializer contract", () => {
  const workspace = createQuoteWorkspace({ products: [PRODUCT], catalogAvailable: true, storage: memoryStorage() });
  workspace.addProduct(PRODUCT);

  const exported = JSON.parse(workspace.exportJson("2026-07-13T12:00:00.000Z"));
  const expected = JSON.parse(serializeQuoteListExport({
    items: get(workspace.state).items,
    settings: get(workspace.state).settings,
  }, "2026-07-13T12:00:00.000Z"));

  assert.deepEqual(exported, expected);
  assert.equal(exported.kind, quoteListExportKind);
});

test("write failures set a warning without losing usable in-memory state", () => {
  const storage = memoryStorage(null, { failWrite: true });
  const workspace = createQuoteWorkspace({ products: [PRODUCT], catalogAvailable: true, storage });

  assert.doesNotThrow(() => workspace.addProduct(PRODUCT));

  const state = get(workspace.state);
  assert.equal(state.items[0].quantity, 1);
  assert.notEqual(state.storageWarning, "");
  assert.equal(storage.writes(), 0);
});

test("read failures surface a warning and leave an empty usable workspace", () => {
  const workspace = createQuoteWorkspace({
    products: [PRODUCT],
    catalogAvailable: true,
    storage: memoryStorage(null, { failRead: true }),
  });

  const state = get(workspace.state);
  assert.equal(state.items.length, 0);
  assert.notEqual(state.storageWarning, "");
  assert.equal(state.readOnly, false);
});

test("a throwing global localStorage getter leaves the workspace usable", (t) => {
  installThrowingLocalStorage(t);

  let workspace;
  assert.doesNotThrow(() => {
    workspace = createQuoteWorkspace({ products: [PRODUCT], catalogAvailable: true });
  });
  assert.doesNotThrow(() => {
    workspace.addProduct(PRODUCT);
    workspace.toggleQuickControls();
    workspace.clear();
  });

  const state = get(workspace.state);
  assert.equal(state.items.length, 0);
  assert.equal(state.settings.showQuickControls, false);
  assert.notEqual(state.storageWarning, "");
  assert.equal(state.readOnly, false);
});

test("published reconciliation writes once and reports removed items", () => {
  const storage = memoryStorage(quotePayload([
    { productId: PRODUCT.id, quantity: 2 },
    { productId: "removed", quantity: 3 },
  ]));

  const workspace = createQuoteWorkspace({ products: [PRODUCT], catalogAvailable: true, storage });
  const state = get(workspace.state);

  assert.deepEqual(state.items.map((item) => item.productId), [PRODUCT.id]);
  assert.match(state.reconcileNotice, /1 item/);
  assert.equal(storage.writes(), 1);
});

test("public state contains only the documented fields", () => {
  const workspace = createQuoteWorkspace({ products: [], catalogAvailable: true, storage: memoryStorage() });
  assert.deepEqual(Object.keys(get(workspace.state)).sort(), [
    "items",
    "preservedPayload",
    "readOnly",
    "reconcileNotice",
    "settings",
    "storageWarning",
  ]);
});
