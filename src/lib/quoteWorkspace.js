import { writable } from "svelte/store";

import {
  clampQuoteQuantity,
  combineQuoteListItems,
  initializeQuoteList,
  loadQuoteList,
  previewQuoteListImport,
  saveQuoteList,
  serializeQuoteListExport,
  snapshotQuoteItem,
} from "./quoteList.js";

const storageWarningCopy = "No pudimos guardar la lista en este navegador. La podés usar durante esta sesión.";
const schemaWarningCopy = "La lista guardada usa una versión más nueva. La conservamos sin cambios.";

export function createQuoteWorkspace({ products = [], catalogAvailable = true, storage } = {}) {
  const loaded = loadQuoteList(storage);
  const initialized = initializeQuoteList(loaded, { ok: catalogAvailable, products });
  const initialState = {
    items: initialized.items,
    settings: initialized.settings,
    storageWarning: loaded.readOnly ? schemaWarningCopy : (loaded.storageAvailable ? "" : storageWarningCopy),
    reconcileNotice: initialized.removedCount ? `Quitamos ${initialized.removedCount} item(s) que ya no aparecen en el catálogo publicado.` : "",
    readOnly: Boolean(loaded.readOnly),
    preservedPayload: loaded.preservedPayload || null,
  };
  const state = writable(initialState);
  let current = initialState;
  state.subscribe((value) => {
    current = value;
  });

  if (initialized.shouldSave) persist(initialized.items, initialized.settings);

  function commit(nextItems, nextSettings = current.settings) {
    if (current.readOnly) return;
    current = { ...current, items: nextItems, settings: nextSettings };
    state.set(current);
    persist(nextItems, nextSettings);
  }

  function persist(items, settings) {
    const result = saveQuoteList({
      items,
      settings,
      readOnly: current.readOnly,
      preservedPayload: current.preservedPayload,
    }, storage);
    const storageWarning = result.blocked ? schemaWarningCopy : (result.ok ? "" : storageWarningCopy);
    if (storageWarning !== current.storageWarning) {
      current = { ...current, storageWarning };
      state.set(current);
    }
    return result;
  }

  return {
    state,
    addProduct(product) {
      if (!product || current.readOnly) return;
      const existing = current.items.find((item) => item.productId === product.id);
      const quantity = Number(existing?.quantity || 0) + 1;
      commit(existing
        ? current.items.map((item) => item.productId === product.id ? snapshotQuoteItem(product, quantity) : item)
        : [...current.items, snapshotQuoteItem(product, 1)]);
    },
    setQuantity(productId, quantity) {
      if (current.readOnly) return;
      const product = products.find((item) => item.id === productId);
      const nextQuantity = clampQuoteQuantity(quantity);
      commit(current.items.map((item) => item.productId === productId
        ? (product ? snapshotQuoteItem(product, nextQuantity) : { ...item, quantity: nextQuantity })
        : item));
    },
    removeProduct(productId) {
      if (current.readOnly) return;
      commit(current.items.filter((item) => item.productId !== productId));
    },
    clear() {
      if (current.readOnly) return;
      commit([]);
    },
    toggleQuickControls() {
      if (current.readOnly) return;
      commit(current.items, {
        ...current.settings,
        showQuickControls: !current.settings.showQuickControls,
      });
    },
    previewImport(raw) {
      return previewQuoteListImport(raw, products);
    },
    applyImport(preview, mode) {
      if (current.readOnly || !preview?.ok) return;
      const nextItems = mode === "combine"
        ? combineQuoteListItems(current.items, preview.items)
        : preview.items;
      const nextSettings = mode === "replace" ? preview.settings : current.settings;
      commit(nextItems, nextSettings);
    },
    exportJson(exportedAt) {
      return serializeQuoteListExport({ items: current.items, settings: current.settings }, exportedAt);
    },
  };
}
