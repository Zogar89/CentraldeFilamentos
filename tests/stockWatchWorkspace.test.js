import assert from "node:assert/strict";
import { test } from "node:test";

import { get } from "svelte/store";

import { stockSubscriptionsStorageKey } from "../src/lib/stockSubscriptions.js";
import { createStockWatchWorkspace } from "../src/lib/stockWatchWorkspace.js";

const NORTE = {
  source_id: "norte",
  provider_name: "Filamentos Norte",
  stock_status: "in_stock",
  stock_quantity: 4,
};
const OESTE = {
  source_id: "oeste",
  provider_name: "Filamentos Oeste",
  stock_status: "in_stock",
  stock_quantity: 7,
};
const PRODUCT = {
  id: "pla-negro-1kg",
  display_name: "PLA Negro 1 kg",
  material: "PLA",
  color: "Negro",
  weight_g: 1000,
  offers: [NORTE, OESTE],
};

function memoryStorage(initialValue = null, { failRead = false, failWrite = false } = {}) {
  let value = initialValue;
  let writes = 0;
  return {
    getItem(key) {
      if (failRead) throw new Error("read unavailable");
      return key === stockSubscriptionsStorageKey ? value : null;
    },
    setItem(key, nextValue) {
      if (failWrite) throw new Error("write unavailable");
      if (key === stockSubscriptionsStorageKey) {
        value = nextValue;
        writes += 1;
      }
    },
    value: () => value,
    writes: () => writes,
  };
}

function storedSubscription({
  offer = NORTE,
  status = "unknown",
  quantity = 0,
  signature = `${status}:${quantity}:`,
} = {}) {
  return {
    key: `${PRODUCT.id}::${offer.source_id}`,
    productId: PRODUCT.id,
    sourceId: offer.source_id,
    productName: PRODUCT.display_name,
    providerName: offer.provider_name,
    presentation: "1 kg",
    subscribedAt: "2026-07-13T12:00:00.000Z",
    lastStockStatus: status,
    lastStockQuantity: quantity,
    lastStockSignature: signature,
    acknowledgedAt: "",
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

test("subscription identity is provider-specific and survives reload", () => {
  const storage = memoryStorage();
  const first = createStockWatchWorkspace({ products: [PRODUCT], storage });

  first.toggle(PRODUCT, NORTE);

  assert.equal(first.isSubscribed(PRODUCT, NORTE), true);
  assert.equal(first.isSubscribed(PRODUCT, OESTE), false);
  assert.equal(storage.writes(), 1);

  const reloaded = createStockWatchWorkspace({ products: [PRODUCT], storage });
  assert.equal(reloaded.isSubscribed(PRODUCT, NORTE), true);
  assert.equal(reloaded.isSubscribed(PRODUCT, OESTE), false);
  assert.equal(get(reloaded.state).subscriptions.length, 1);
  assert.equal(storage.writes(), 1);
});

test("toggle off removes only the exact provider pair", () => {
  const storage = memoryStorage();
  const workspace = createStockWatchWorkspace({ products: [PRODUCT], storage });
  workspace.toggle(PRODUCT, NORTE);
  workspace.toggle(PRODUCT, OESTE);

  workspace.toggle(PRODUCT, NORTE);

  assert.equal(workspace.isSubscribed(PRODUCT, NORTE), false);
  assert.equal(workspace.isSubscribed(PRODUCT, OESTE), true);
  assert.deepEqual(get(workspace.state).subscriptions.map((item) => item.sourceId), [OESTE.source_id]);
  assert.equal(storage.writes(), 3);
});

test("missing offers cannot create a subscription", () => {
  const storage = memoryStorage();
  const workspace = createStockWatchWorkspace({ products: [PRODUCT], storage });

  assert.doesNotThrow(() => workspace.toggle(PRODUCT, null));
  assert.equal(workspace.isSubscribed(PRODUCT, null), false);
  assert.deepEqual(get(workspace.state).subscriptions, []);
  assert.equal(storage.writes(), 0);
});

test("confirmed out of stock returning to four creates one exact alert", () => {
  const storage = memoryStorage(JSON.stringify([
    storedSubscription({ status: "out_of_stock", quantity: 0 }),
  ]));

  const workspace = createStockWatchWorkspace({ products: [PRODUCT], storage });
  const state = get(workspace.state);

  assert.equal(state.alerts.length, 1);
  assert.deepEqual(state.alerts[0], {
    key: `${PRODUCT.id}::${NORTE.source_id}`,
    productId: PRODUCT.id,
    sourceId: NORTE.source_id,
    productName: PRODUCT.display_name,
    providerName: NORTE.provider_name,
    quantity: 4,
    previousQuantity: 0,
  });
  assert.equal(storage.writes(), 0);
});

test("known positive increase alerts but a decrease only updates observation", () => {
  const increaseStorage = memoryStorage(JSON.stringify([
    storedSubscription({ status: "in_stock", quantity: 2 }),
  ]));
  const increased = createStockWatchWorkspace({ products: [PRODUCT], storage: increaseStorage });
  assert.equal(get(increased.state).alerts.length, 1);
  assert.equal(get(increased.state).alerts[0].previousQuantity, 2);
  assert.equal(increaseStorage.writes(), 0);

  const decreaseProduct = {
    ...PRODUCT,
    offers: [{ ...NORTE, stock_quantity: 2 }, OESTE],
  };
  const decreaseStorage = memoryStorage(JSON.stringify([
    storedSubscription({ status: "in_stock", quantity: 4 }),
  ]));
  const decreased = createStockWatchWorkspace({ products: [decreaseProduct], storage: decreaseStorage });
  assert.deepEqual(get(decreased.state).alerts, []);
  assert.equal(get(decreased.state).subscriptions[0].lastStockQuantity, 2);
  assert.equal(decreaseStorage.writes(), 1);
});

test("unknown and confirmed zero remain distinct transitions", () => {
  const unknownStorage = memoryStorage(JSON.stringify([
    storedSubscription({ status: "unknown", quantity: 0, signature: "unknown:unknown:" }),
  ]));
  const fromUnknown = createStockWatchWorkspace({ products: [PRODUCT], storage: unknownStorage });
  assert.deepEqual(get(fromUnknown.state).alerts, []);
  assert.equal(get(fromUnknown.state).subscriptions[0].lastStockStatus, "in_stock");
  assert.equal(get(fromUnknown.state).subscriptions[0].lastStockQuantity, 4);
  assert.equal(unknownStorage.writes(), 1);

  const unknownOffer = { ...NORTE, stock_status: "unknown", stock_quantity: null };
  const unknownProduct = { ...PRODUCT, offers: [unknownOffer, OESTE] };
  const zeroStorage = memoryStorage(JSON.stringify([
    storedSubscription({ status: "out_of_stock", quantity: 0 }),
  ]));
  const toUnknown = createStockWatchWorkspace({ products: [unknownProduct], storage: zeroStorage });
  assert.deepEqual(get(toUnknown.state).alerts, []);
  assert.equal(get(toUnknown.state).subscriptions[0].lastStockStatus, "unknown");
  assert.equal(get(toUnknown.state).subscriptions[0].lastStockQuantity, 0);
  assert.match(get(toUnknown.state).subscriptions[0].lastStockSignature, /^unknown:unknown:/);
  assert.equal(zeroStorage.writes(), 1);
});

test("dismiss persists the current observation and prevents duplicate alerts on reload", () => {
  const storage = memoryStorage(JSON.stringify([
    storedSubscription({ status: "out_of_stock", quantity: 0 }),
  ]));
  const workspace = createStockWatchWorkspace({ products: [PRODUCT], storage });
  assert.equal(get(workspace.state).alerts.length, 1);

  workspace.dismissAlerts();

  assert.deepEqual(get(workspace.state).alerts, []);
  assert.equal(get(workspace.state).subscriptions[0].lastStockQuantity, 4);
  assert.notEqual(get(workspace.state).subscriptions[0].acknowledgedAt, "");
  assert.equal(storage.writes(), 1);
  const reloaded = createStockWatchWorkspace({ products: [PRODUCT], storage });
  assert.deepEqual(get(reloaded.state).alerts, []);
  assert.equal(storage.writes(), 1);
});

test("workspace instances do not share subscriptions or alerts", () => {
  const first = createStockWatchWorkspace({ products: [PRODUCT], storage: memoryStorage() });
  const second = createStockWatchWorkspace({ products: [PRODUCT], storage: memoryStorage() });

  first.toggle(PRODUCT, NORTE);

  assert.equal(get(first.state).subscriptions.length, 1);
  assert.equal(get(second.state).subscriptions.length, 0);
  assert.deepEqual(get(second.state).alerts, []);
});

test("corrupt JSON and a blocked global storage getter remain safe", (t) => {
  const corrupt = createStockWatchWorkspace({ products: [PRODUCT], storage: memoryStorage("not-json") });
  assert.deepEqual(get(corrupt.state), { subscriptions: [], alerts: [] });
  assert.doesNotThrow(() => corrupt.toggle(PRODUCT, NORTE));

  installThrowingLocalStorage(t);
  let blocked;
  assert.doesNotThrow(() => {
    blocked = createStockWatchWorkspace({ products: [PRODUCT] });
    blocked.toggle(PRODUCT, NORTE);
    blocked.dismissAlerts();
  });
  assert.equal(blocked.isSubscribed(PRODUCT, NORTE), true);
});

test("write failures retain usable in-memory toggle and acknowledgement behavior", () => {
  const toggleWorkspace = createStockWatchWorkspace({
    products: [PRODUCT],
    storage: memoryStorage(null, { failWrite: true }),
  });
  assert.doesNotThrow(() => toggleWorkspace.toggle(PRODUCT, NORTE));
  assert.equal(toggleWorkspace.isSubscribed(PRODUCT, NORTE), true);

  const alertStorage = memoryStorage(JSON.stringify([
    storedSubscription({ status: "out_of_stock", quantity: 0 }),
  ]), { failWrite: true });
  const alertWorkspace = createStockWatchWorkspace({ products: [PRODUCT], storage: alertStorage });
  assert.equal(get(alertWorkspace.state).alerts.length, 1);
  assert.doesNotThrow(() => alertWorkspace.dismissAlerts());
  assert.deepEqual(get(alertWorkspace.state).alerts, []);
  assert.equal(get(alertWorkspace.state).subscriptions[0].lastStockQuantity, 4);
});

test("missing catalog products preserve unrelated stored subscriptions without writes", () => {
  const missing = storedSubscription();
  missing.productId = "missing-product";
  missing.key = `missing-product::${NORTE.source_id}`;
  const original = JSON.stringify([missing]);
  const storage = memoryStorage(original);

  const workspace = createStockWatchWorkspace({ products: [PRODUCT], storage });

  assert.deepEqual(get(workspace.state).subscriptions, [missing]);
  assert.equal(storage.value(), original);
  assert.equal(storage.writes(), 0);
});
