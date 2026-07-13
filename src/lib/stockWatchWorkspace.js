import { writable } from "svelte/store";

import {
  loadStockSubscriptions,
  saveStockSubscriptions,
  stockSignature,
  subscriptionKey,
} from "./stockSubscriptions.js";
import { slugText } from "./shared.js";

function offerSourceId(offer) {
  return offer?.source_id || offer?.provider_name || "";
}

function observedQuantity(offer) {
  const quantity = Number(offer?.stock_quantity);
  return Number.isFinite(quantity) ? quantity : 0;
}

function productName(product) {
  return product?.display_name || product?.product_name || product?.name || "Filamento esperado";
}

function presentation(product) {
  if (product?.presentation) return product.presentation;
  const weight = Number(product?.weight_g);
  if (!Number.isFinite(weight) || weight <= 0) return "";
  return weight % 1000 === 0 ? `${weight / 1000} kg` : `${weight} g`;
}

function stockWatchTargetId(product, offer) {
  return `stock-watch-${slugText([product.id, offerSourceId(offer)].join(" "))}`;
}

function observedSubscription(subscription, product, offer, acknowledgedAt = subscription.acknowledgedAt) {
  return {
    ...subscription,
    productName: productName(product),
    providerName: offer.provider_name || subscription.providerName,
    presentation: presentation(product),
    lastStockStatus: offer.stock_status || "unknown",
    lastStockQuantity: observedQuantity(offer),
    lastStockSignature: stockSignature(offer),
    acknowledgedAt,
  };
}

function observationChanged(previous, next) {
  return previous.productName !== next.productName
    || previous.providerName !== next.providerName
    || previous.presentation !== next.presentation
    || previous.lastStockStatus !== next.lastStockStatus
    || previous.lastStockQuantity !== next.lastStockQuantity
    || previous.lastStockSignature !== next.lastStockSignature;
}

function alertFor(subscription, product, offer) {
  const currentQuantity = observedQuantity(offer);
  const previousQuantity = Number(subscription.lastStockQuantity || 0);
  const currentIsPositive = offer.stock_status === "in_stock" && currentQuantity > 0;
  const returnedAfterConfirmedOut = currentIsPositive && subscription.lastStockStatus === "out_of_stock";
  const confirmedQuantityIncrease = currentIsPositive
    && subscription.lastStockStatus === "in_stock"
    && currentQuantity > previousQuantity;
  if (!returnedAfterConfirmedOut && !confirmedQuantityIncrease) return null;
  return {
    key: subscription.key,
    productId: product.id,
    sourceId: offerSourceId(offer),
    productName: productName(product),
    providerName: offer.provider_name || subscription.providerName,
    quantity: currentQuantity,
    previousQuantity,
    href: `#${stockWatchTargetId(product, offer)}`,
  };
}

export function createStockWatchWorkspace({ products = [], storage } = {}) {
  const productById = new Map(products.filter((product) => product?.id).map((product) => [product.id, product]));
  let subscriptions = loadStockSubscriptions(storage);
  const alerts = [];
  let changed = false;

  subscriptions = subscriptions.map((subscription) => {
    const product = productById.get(subscription.productId);
    if (!product) return subscription;
    const offer = (product.offers || []).find((candidate) => offerSourceId(candidate) === subscription.sourceId);
    if (!offer) return subscription;

    const alert = alertFor(subscription, product, offer);
    if (alert) {
      alerts.push(alert);
      return subscription;
    }

    const observed = observedSubscription(subscription, product, offer);
    if (observationChanged(subscription, observed)) changed = true;
    return observed;
  });

  let current = { subscriptions, alerts };
  const state = writable(current);
  if (changed) saveStockSubscriptions(subscriptions, storage);

  function publish(nextSubscriptions, nextAlerts) {
    current = { subscriptions: nextSubscriptions, alerts: nextAlerts };
    state.set(current);
  }

  function isSubscribed(product, offer) {
    if (!product?.id || !offerSourceId(offer)) return false;
    const key = subscriptionKey(product, offer);
    return current.subscriptions.some((subscription) => subscription.key === key);
  }

  function toggle(product, offer) {
    const sourceId = offerSourceId(offer);
    if (!product?.id || !sourceId) return false;
    const key = subscriptionKey(product, offer);
    const existing = current.subscriptions.some((subscription) => subscription.key === key);
    let nextSubscriptions;
    let nextAlerts = current.alerts;
    if (existing) {
      nextSubscriptions = current.subscriptions.filter((subscription) => subscription.key !== key);
      nextAlerts = current.alerts.filter((alert) => alert.key !== key);
    } else {
      nextSubscriptions = [
        ...current.subscriptions,
        {
          key,
          productId: product.id,
          sourceId,
          productName: productName(product),
          providerName: offer.provider_name || "Proveedor",
          presentation: presentation(product),
          subscribedAt: new Date().toISOString(),
          lastStockStatus: offer.stock_status || "unknown",
          lastStockQuantity: observedQuantity(offer),
          lastStockSignature: stockSignature(offer),
          acknowledgedAt: "",
        },
      ];
    }
    publish(nextSubscriptions, nextAlerts);
    saveStockSubscriptions(nextSubscriptions, storage);
    return !existing;
  }

  function dismissAlerts() {
    if (!current.alerts.length) return false;
    const alertKeys = new Set(current.alerts.map((alert) => alert.key));
    const acknowledgedAt = new Date().toISOString();
    const nextSubscriptions = current.subscriptions.map((subscription) => {
      if (!alertKeys.has(subscription.key)) return subscription;
      const product = productById.get(subscription.productId);
      if (!product) return subscription;
      const offer = (product.offers || []).find((candidate) => offerSourceId(candidate) === subscription.sourceId);
      if (!offer) return subscription;
      return observedSubscription(subscription, product, offer, acknowledgedAt);
    });
    publish(nextSubscriptions, []);
    saveStockSubscriptions(nextSubscriptions, storage);
    return true;
  }

  return { state, toggle, isSubscribed, dismissAlerts };
}
