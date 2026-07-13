const statuses = ["pending", "reviewed", "stale", "without-gallery"];
const reasonLabels = {
  preferred_angle: "45° sin caja",
  best_spool: "Mejor carrete",
  official_primary: "Foto principal",
};

const state = {
  products: [],
  reviews: {},
  query: "",
  filter: "all",
  savingUrl: "",
};

const elements = {
  search: document.querySelector("#search"),
  filter: document.querySelector("#review-filter"),
  products: document.querySelector("#products"),
  message: document.querySelector("#message"),
  visible: document.querySelector("#visible-count"),
  total: document.querySelector("#total-count"),
  counters: Object.fromEntries(statuses.map((status) => [
    status,
    document.querySelector(`[data-count="${status}"]`),
  ])),
};

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function proxyImage(url) {
  return `/api/image?url=${encodeURIComponent(url)}`;
}

function imageSource(url) {
  return /^https?:\/\//i.test(url) ? proxyImage(url) : `/public/${String(url).replace(/^\/+/, "")}`;
}

function statusLabel(status) {
  return {
    pending: "Pendiente",
    reviewed: "Revisado",
    stale: "Desactualizado",
    "without-gallery": "Sin galería",
  }[status] || status;
}

function searchText(product) {
  return [
    product.product_id,
    product.title,
    product.product_url,
    product.material,
    product.variant,
    product.color,
    product.sku,
    product.ean,
    product.pantone,
  ].join(" ").toLocaleLowerCase("es-AR");
}

function filteredProducts() {
  const terms = state.query.toLocaleLowerCase("es-AR").trim().split(/\s+/).filter(Boolean);
  return state.products.filter((product) => {
    if (state.filter !== "all" && product.review_status !== state.filter) return false;
    const haystack = searchText(product);
    return terms.every((term) => haystack.includes(term));
  });
}

function currentApprovedUrl(product) {
  return product.current_image_url || product.image_url || product.thumbnail_url || "";
}

function renderCurrent(product, review) {
  const current = currentApprovedUrl(product);
  const reviewed = review?.selected_image_remote_url || "";
  if (!current && !reviewed) return "";
  return `
    <aside class="approved-images" aria-label="Imágenes aprobadas">
      ${current ? `<figure><img src="${imageSource(current)}" alt="Imagen aprobada actual"><figcaption>Aprobada actual</figcaption></figure>` : ""}
      ${reviewed ? `<figure><img src="${proxyImage(reviewed)}" alt="Última selección"><figcaption>Última selección · ${escapeHtml(reasonLabels[review.selection_reason] || review.selection_reason)}</figcaption></figure>` : ""}
    </aside>
  `;
}

function renderGallery(product) {
  const gallery = product.gallery_image_urls || [];
  if (!gallery.length) {
    return '<p class="empty-gallery">La ficha activa no publicó una galería oficial. No requiere una elección fabricada.</p>';
  }
  return `<div class="gallery">${gallery.map((url, index) => `
    <article class="candidate">
      <div class="candidate-position">${index + 1} / ${gallery.length}</div>
      <img src="${proxyImage(url)}" alt="${escapeHtml(product.title)} · imagen ${index + 1}" loading="lazy">
      <a href="${escapeHtml(url)}" target="_blank" rel="noreferrer" title="${escapeHtml(url)}">Ver original</a>
      <div class="candidate-actions">
        ${Object.entries(reasonLabels).map(([reason, label]) => `
          <button type="button" data-review data-product-url="${escapeHtml(product.product_url)}" data-image-index="${index}" data-reason="${reason}" ${state.savingUrl === product.product_url ? "disabled" : ""}>${label}</button>
        `).join("")}
      </div>
    </article>
  `).join("")}</div>`;
}

function render() {
  const visible = filteredProducts();
  const counts = Object.fromEntries(statuses.map((status) => [
    status,
    state.products.filter((product) => product.review_status === status).length,
  ]));
  elements.visible.textContent = visible.length;
  elements.total.textContent = state.products.length;
  for (const status of statuses) elements.counters[status].textContent = counts[status];

  elements.products.innerHTML = visible.map((product) => {
    const review = state.reviews[product.product_url];
    return `
      <article class="product-card status-${product.review_status}" data-product-url="${escapeHtml(product.product_url)}">
        <header class="product-head">
          <div>
            <p class="product-kicker">${escapeHtml([product.material, product.variant, product.color].filter(Boolean).join(" · "))}</p>
            <h2>${escapeHtml(product.title)}</h2>
            <a href="${escapeHtml(product.product_url)}" target="_blank" rel="noreferrer">${escapeHtml(product.product_url)}</a>
          </div>
          <span class="status-badge">${statusLabel(product.review_status)}</span>
        </header>
        <div class="review-layout">
          ${renderCurrent(product, review)}
          ${renderGallery(product)}
        </div>
      </article>
    `;
  }).join("") || '<p class="empty-results">No hay productos para este filtro.</p>';

  for (const button of elements.products.querySelectorAll("[data-review]")) {
    button.addEventListener("click", () => saveReview(button));
  }
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

async function saveReview(button) {
  const product = state.products.find((item) => item.product_url === button.dataset.productUrl);
  const selectedImage = product?.gallery_image_urls?.[Number(button.dataset.imageIndex)];
  if (!product || !selectedImage) {
    elements.message.textContent = "No pude resolver esa imagen dentro de la galería actual.";
    elements.message.dataset.kind = "error";
    return;
  }

  state.savingUrl = product.product_url;
  elements.message.textContent = `Guardando ${product.title}…`;
  elements.message.dataset.kind = "info";
  render();
  try {
    const { review } = await fetchJson("/api/review", {
      method: "POST",
      body: JSON.stringify({
        product_url: product.product_url,
        selected_image_remote_url: selectedImage,
        selection_reason: button.dataset.reason,
        gallery_fingerprint: product.gallery_fingerprint,
      }),
    });
    state.reviews[product.product_url] = review;
    product.review_status = "reviewed";
    elements.message.textContent = `Revisión guardada: ${product.title}.`;
    elements.message.dataset.kind = "success";
  } catch (error) {
    elements.message.textContent = `No se guardó la revisión: ${error.message}`;
    elements.message.dataset.kind = "error";
  } finally {
    state.savingUrl = "";
    render();
  }
}

async function init() {
  const [{ products }, { selections }] = await Promise.all([
    fetchJson("/api/products"),
    fetchJson("/api/selections"),
  ]);
  state.products = (products || []).sort((left, right) =>
    String(left.title || "").localeCompare(String(right.title || ""), "es-AR"));
  state.reviews = selections || {};
  elements.message.textContent = "Scan cargado. Cada galería se muestra completa y en orden oficial.";
  elements.message.dataset.kind = "success";
  render();
}

elements.search.addEventListener("input", (event) => {
  state.query = event.target.value;
  render();
});
elements.filter.addEventListener("change", (event) => {
  state.filter = event.target.value;
  render();
});

init().catch((error) => {
  elements.message.textContent = `No se pudo iniciar el curador: ${error.message}`;
  elements.message.dataset.kind = "error";
});
