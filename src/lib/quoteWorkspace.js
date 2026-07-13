import { writable } from "svelte/store";

import {
  clampQuoteQuantity,
  combineQuoteListItems,
  initializeQuoteList,
  loadQuoteList,
  normalizeQuoteList,
  previewQuoteListImport,
  quoteListSchemaVersion,
  saveQuoteList,
  serializeQuoteListExport,
  snapshotQuoteItem,
} from "./quoteList.js";

const storageWarningCopy = "No pudimos guardar la lista en este navegador. La sesión actual sigue disponible.";
const schemaWarningCopy = "La lista guardada usa una versión más nueva y quedó en modo de solo lectura.";

function normalizedWorkspaceState(items, settings) {
  return normalizeQuoteList({
    schemaVersion: quoteListSchemaVersion,
    items,
    settings,
  });
}

export function createQuoteWorkspace({
  products = [],
  catalogAvailable = false,
  storage,
} = {}) {
  const productById = new Map(products.map((product) => [product.id, product]));
  const loaded = loadQuoteList(storage);
  const initialized = initializeQuoteList(loaded, {
    ok: catalogAvailable,
    products,
  });

  let current = {
    items: initialized.items,
    settings: initialized.settings,
    storageWarning: loaded.readOnly
      ? schemaWarningCopy
      : (loaded.storageAvailable ? "" : storageWarningCopy),
    reconcileNotice: initialized.removedCount
      ? `Quitamos ${initialized.removedCount} item(s) que ya no aparecen en el catálogo publicado.`
      : "",
    readOnly: Boolean(loaded.readOnly),
    preservedPayload: loaded.preservedPayload,
  };
  const state = writable(current);

  if (initialized.shouldSave) {
    const result = saveQuoteList({
      items: current.items,
      settings: current.settings,
    }, storage);
    if (!result.ok) {
      current = { ...current, storageWarning: storageWarningCopy };
      state.set(current);
    }
  }

  function commit(items, settings = current.settings, reconcileNotice = current.reconcileNotice) {
    if (current.readOnly) return false;

    const normalized = normalizedWorkspaceState(items, settings);
    const result = saveQuoteList({
      items: normalized.items,
      settings: normalized.settings,
    }, storage);
    current = {
      ...current,
      items: normalized.items,
      settings: normalized.settings,
      storageWarning: result.ok ? "" : storageWarningCopy,
      reconcileNotice,
    };
    state.set(current);
    return result.ok;
  }

  function addProduct(product) {
    if (current.readOnly || !product?.id) return false;
    const existing = current.items.find((item) => item.productId === product.id);
    const quantity = Number(existing?.quantity || 0) + 1;
    const item = snapshotQuoteItem(product, quantity);
    const items = existing
      ? current.items.map((candidate) => candidate.productId === product.id ? item : candidate)
      : [...current.items, item];
    return commit(items);
  }

  function setQuantity(productId, quantity) {
    if (current.readOnly) return false;
    const nextQuantity = clampQuoteQuantity(quantity);
    const items = current.items.map((item) => {
      if (item.productId !== productId) return item;
      const product = productById.get(productId);
      return product
        ? snapshotQuoteItem(product, nextQuantity)
        : { ...item, quantity: nextQuantity };
    });
    return commit(items);
  }

  function removeProduct(productId) {
    if (current.readOnly) return false;
    return commit(current.items.filter((item) => item.productId !== productId));
  }

  function clear() {
    if (current.readOnly) return false;
    return commit([], current.settings, "");
  }

  function toggleQuickControls() {
    if (current.readOnly) return false;
    return commit(current.items, {
      ...current.settings,
      showQuickControls: !current.settings.showQuickControls,
    });
  }

  function previewImport(text) {
    return previewQuoteListImport(text, products);
  }

  function applyImport(preview, mode = "replace") {
    if (current.readOnly || !preview?.ok) return false;
    const items = mode === "combine"
      ? combineQuoteListItems(current.items, preview.items)
      : preview.items;
    const settings = mode === "replace" ? preview.settings : current.settings;
    const skipped = preview.skippedCount || 0;
    const notice = `Importamos ${preview.validCount} item(s)${skipped ? ` y descartamos ${skipped}` : ""}.`;
    return commit(items, settings, notice);
  }

  function exportJson(exportedAt) {
    return serializeQuoteListExport({
      items: current.items,
      settings: current.settings,
    }, exportedAt);
  }

  return {
    state,
    addProduct,
    setQuantity,
    removeProduct,
    clear,
    toggleQuickControls,
    previewImport,
    applyImport,
    exportJson,
  };
}
