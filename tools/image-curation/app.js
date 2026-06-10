const lineRanks = {
  "PLA Standard": 10,
  "PLA+": 20,
  "PLA Flexible": 25,
  PETG: 30,
  ABS: 40,
  TPU: 50,
  Flex: 51,
  Simpliflex: 52,
  "PLA Astra": 60,
  "PLA Silk": 61,
  "PLA Boutique": 62,
  "PLA Wood": 63,
  "PLA 850": 70,
  "PLA 870": 71,
  "PLA Zeta": 72,
  "PETG Clear": 80,
  "E-PET": 81,
  "PP-T": 90,
  "Nylon 6": 100,
  "Nylon 12": 101,
  "Acetal-POM": 110,
  "PVA Soluble": 120,
  "Sampler / lapiz 3D": 130,
};

const state = {
  products: [],
  filtered: [],
  candidates: {},
  reviews: {},
  captureRunning: true,
  captureIndex: 0,
};

const elements = {
  search: document.querySelector("#search"),
  reviewFilter: document.querySelector("#review-filter"),
  products: document.querySelector("#products"),
  visibleCount: document.querySelector("#visible-count"),
  totalCount: document.querySelector("#total-count"),
  capturedCount: document.querySelector("#captured-count"),
  reviewedCount: document.querySelector("#reviewed-count"),
  captureStatus: document.querySelector("#capture-status"),
  captureToggle: document.querySelector("#capture-toggle"),
};

function normalizeText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function productLine(product) {
  if (!product.variant && product.material === "PLA") return "PLA Standard";
  return product.variant || product.material || "Sin clasificar";
}

function brandRank(brand) {
  if (brand === "Grilon3") return "0";
  if (brand === "3N3") return "1";
  return "9";
}

function productSortKey(product) {
  const line = productLine(product);
  return [
    String(lineRanks[line] ?? 999).padStart(3, "0"),
    brandRank(product.brand),
    product.brand || "",
    String(product.diameter_mm || "").padStart(5, "0"),
    line,
    product.material || "",
    product.variant || "",
    product.color || "",
    String(product.weight_g || "").padStart(8, "0"),
    product.display_name || "",
  ].join("|");
}

function productMeta(product) {
  return [
    product.brand,
    productLine(product),
    product.color,
    product.diameter_mm ? `${product.diameter_mm} mm` : "",
    product.weight_g ? `${Number(product.weight_g) / 1000} kg` : "",
  ].filter(Boolean).join(" · ");
}

function productSearchText(product) {
  return [
    product.id,
    product.display_name,
    product.material,
    product.variant,
    product.color,
    product.brand,
    product.pantone,
    product.sku,
    product.ean,
    product.manufacturer_product_url,
    product.provider_product_url,
    ...(product.offers || []).map((offer) => offer.original_name),
  ].join(" ");
}

function candidateSourceUrl(product) {
  return product.manufacturer_product_url || product.provider_product_url || "";
}

function localImageSrc(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return proxyImageSrc(path);
  return `/public/${path}`;
}

function proxyImageSrc(url) {
  return `/api/image?url=${encodeURIComponent(url)}`;
}

function filenameFromUrl(url) {
  try {
    const pathname = new URL(url).pathname;
    return decodeURIComponent(pathname.split("/").filter(Boolean).at(-1) || "imagen");
  } catch {
    return "imagen";
  }
}

function reviewLabel(review) {
  if (!review) return "Pendiente";
  if (review.action === "keep-current") return "Dejar igual";
  if (review.action === "use-candidate") return "Cambio elegido";
  return "Revisado";
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "content-type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
  return payload;
}

function applyFilters() {
  const query = normalizeText(elements.search.value).trim();
  const terms = query.split(/\s+/).filter(Boolean);
  const reviewFilter = elements.reviewFilter.value;

  state.filtered = state.products.filter((product) => {
    const haystack = normalizeText(productSearchText(product));
    if (!terms.every((term) => haystack.includes(term))) return false;
    const review = state.reviews[product.id];
    if (reviewFilter === "pending") return !review;
    if (reviewFilter === "selected") return review?.action === "use-candidate";
    if (reviewFilter === "kept") return review?.action === "keep-current";
    if (reviewFilter === "without-image") return !product.image_url;
    return true;
  });
  render();
}

function render() {
  elements.products.innerHTML = "";
  for (const product of state.filtered) {
    elements.products.append(renderProductCard(product));
  }
  renderStats();
}

function renderStats() {
  const captured = Object.values(state.candidates).filter((entry) => entry?.candidates?.length).length;
  const reviewed = Object.keys(state.reviews).length;
  elements.visibleCount.textContent = state.filtered.length;
  elements.totalCount.textContent = state.products.length;
  elements.capturedCount.textContent = captured;
  elements.reviewedCount.textContent = reviewed;
}

function renderProductCard(product) {
  const card = document.createElement("article");
  const cache = state.candidates[product.id] || {};
  const candidates = cache.candidates || [];
  const review = state.reviews[product.id];
  const sourceUrl = candidateSourceUrl(product);
  const statusClass = review?.action === "use-candidate" ? "selected" : review?.action === "keep-current" ? "kept" : "pending";
  card.className = `product-card ${statusClass}`;
  card.dataset.productId = product.id;

  card.innerHTML = `
    <div class="current-thumb">
      ${product.image_url ? `<img src="${localImageSrc(product.thumbnail_url || product.image_url)}" alt="Foto actual" loading="lazy">` : `<span>Sin foto</span>`}
    </div>
    <div class="product-main">
      <div class="product-head">
        <div>
          <p class="eyebrow">${escapeHtml(productLine(product))}</p>
          <h2>${escapeHtml(product.display_name || product.id)}</h2>
          <p class="muted">${escapeHtml(productMeta(product))}</p>
        </div>
        <span class="review-badge">${escapeHtml(reviewLabel(review))}</span>
      </div>

      <div class="candidate-strip">
        ${renderCandidateButtons(product, candidates)}
      </div>

      <div class="manual-row">
        <input class="manual-url" type="url" placeholder="URL manual de pagina o foto directa" value="${escapeHtml(sourceUrl)}">
        <button type="button" class="fetch-one secondary">Traer</button>
        <button type="button" class="keep-current">Dejar igual</button>
      </div>

      <p class="card-status">${escapeHtml(cache.error || captureMessage(product, cache))}</p>
    </div>
  `;

  card.querySelector(".fetch-one").addEventListener("click", () => captureProduct(product, card.querySelector(".manual-url").value.trim(), true));
  card.querySelector(".keep-current").addEventListener("click", () => saveReview(product, "keep-current"));
  card.querySelectorAll("[data-candidate-index]").forEach((button) => {
    button.addEventListener("click", () => saveReview(product, "use-candidate", candidates[Number(button.dataset.candidateIndex)]));
  });
  return card;
}

function renderCandidateButtons(product, candidates) {
  if (!candidateSourceUrl(product) && !candidates.length) {
    return `<div class="candidate-empty">Sin URL oficial. Pegá una URL manual.</div>`;
  }
  if (!candidates.length) {
    return `<div class="candidate-empty">Candidatas pendientes...</div>`;
  }
  return candidates.slice(0, 3).map((candidate, index) => `
    <button type="button" class="candidate-option" data-candidate-index="${index}">
      <img src="${proxyImageSrc(candidate.url)}" alt="Candidata ${index + 1}" loading="lazy">
      <span>Candidata ${index + 1}</span>
      <small>${escapeHtml(filenameFromUrl(candidate.url))}</small>
    </button>
  `).join("");
}

function captureMessage(product, cache) {
  if (cache.captured_at && cache.candidates?.length) return `Candidatas listas desde ${cache.input_url || "URL guardada"}`;
  if (cache.captured_at && !cache.candidates?.length) return "Sin candidatas detectadas. Podés pegar URL manual.";
  if (!candidateSourceUrl(product)) return "No hay URL oficial en el stock.";
  return "En cola para captura automatica.";
}

async function captureProduct(product, inputUrl = candidateSourceUrl(product), forceRender = false) {
  if (!inputUrl) return;
  const payload = await fetchJson("/api/candidates", {
    method: "POST",
    body: JSON.stringify({ product_id: product.id, url: inputUrl }),
  });
  state.candidates[product.id] = payload.cached || {
    captured_at: new Date().toISOString(),
    input_url: inputUrl,
    candidates: payload.candidates || [],
    error: payload.error || "",
  };
  if (forceRender) applyFilters();
  else renderStats();
}

async function saveReview(product, action, candidate = null) {
  const review = {
    action,
    product: productPayload(product),
    candidate,
    source_input_url: state.candidates[product.id]?.input_url || candidateSourceUrl(product),
  };
  const payload = await fetchJson(action === "use-candidate" ? "/api/select" : "/api/review", {
    method: "POST",
    body: JSON.stringify(review),
  });
  state.reviews[product.id] = payload.selection || payload.review;
  applyFilters();
}

function productPayload(product) {
  return {
    id: product.id,
    display_name: product.display_name,
    brand: product.brand,
    material: product.material,
    variant: product.variant,
    color: product.color,
    current_image_url: product.image_url || "",
    current_thumbnail_url: product.thumbnail_url || "",
    manufacturer_product_url: product.manufacturer_product_url || "",
    provider_product_url: product.provider_product_url || "",
  };
}

async function runCaptureQueue() {
  while (true) {
    if (!state.captureRunning) {
      await sleep(700);
      continue;
    }
    const pending = state.products.filter((product) => candidateSourceUrl(product) && !state.candidates[product.id]);
    if (!pending.length) {
      elements.captureStatus.textContent = "Captura automatica completa. Podés revisar o pegar URLs manuales donde falten candidatas.";
      await sleep(2500);
      continue;
    }
    const product = pending[0];
    state.captureIndex += 1;
    elements.captureStatus.textContent = `Capturando ${state.captureIndex}: ${product.display_name}`;
    try {
      await captureProduct(product);
    } catch (error) {
      state.candidates[product.id] = {
        captured_at: new Date().toISOString(),
        input_url: candidateSourceUrl(product),
        candidates: [],
        error: error.message,
      };
    }
    if (state.filtered.some((item) => item.id === product.id)) render();
    await sleep(850);
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function init() {
  const [{ products }, { cache }, { selections }] = await Promise.all([
    fetchJson("/api/products"),
    fetchJson("/api/candidate-cache"),
    fetchJson("/api/selections"),
  ]);
  state.products = (products || []).sort((left, right) => productSortKey(left).localeCompare(productSortKey(right), "es-AR"));
  state.filtered = state.products;
  state.candidates = cache || {};
  state.reviews = selections || {};
  render();
  runCaptureQueue();
}

elements.search.addEventListener("input", applyFilters);
elements.reviewFilter.addEventListener("change", applyFilters);
elements.captureToggle.addEventListener("click", () => {
  state.captureRunning = !state.captureRunning;
  elements.captureToggle.textContent = state.captureRunning ? "Pausar captura" : "Reanudar captura";
  elements.captureStatus.textContent = state.captureRunning ? "Captura automatica activa." : "Captura pausada.";
});

init().catch((error) => {
  elements.captureStatus.textContent = `Error inicializando: ${error.message}`;
});
