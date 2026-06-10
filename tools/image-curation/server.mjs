import { createServer } from "node:http";
import { createReadStream } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..", "..");
const publicDir = path.join(rootDir, "public");
const stateDir = path.join(rootDir, ".image-curation");
const selectionPath = path.join(stateDir, "selection.json");
const selectionsPath = path.join(stateDir, "selections.json");
const candidatesPath = path.join(stateDir, "candidates.json");
const toolDir = __dirname;
const port = Number(process.env.PORT || 4177);
const host = process.env.HOST || "127.0.0.1";

const mimeTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".png": "image/png",
  ".webp": "image/webp",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
};

function sendJson(response, status, payload) {
  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  });
  response.end(JSON.stringify(payload, null, 2));
}

function sendText(response, status, text) {
  response.writeHead(status, {
    "content-type": "text/plain; charset=utf-8",
    "cache-control": "no-store",
  });
  response.end(text);
}

function safeJoin(baseDir, requestPath) {
  const cleanPath = decodeURIComponent(requestPath).replace(/^\/+/, "");
  const resolved = path.resolve(baseDir, cleanPath);
  if (!resolved.startsWith(path.resolve(baseDir))) {
    return "";
  }
  return resolved;
}

async function serveFile(response, filePath) {
  const extension = path.extname(filePath).toLowerCase();
  response.writeHead(200, {
    "content-type": mimeTypes[extension] || "application/octet-stream",
    "cache-control": "no-store",
  });
  createReadStream(filePath).pipe(response);
}

async function readRequestJson(request) {
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  const body = Buffer.concat(chunks).toString("utf-8");
  if (!body.trim()) return {};
  return JSON.parse(body);
}

async function loadStockProducts() {
  const payload = JSON.parse(await readFile(path.join(publicDir, "data", "stock.json"), "utf-8"));
  return (payload.products || []).map((product) => ({
    id: product.id,
    display_name: product.display_name,
    material: product.material,
    variant: product.variant,
    color: product.color,
    brand: product.brand,
    diameter_mm: product.diameter_mm,
    weight_g: product.weight_g,
    pantone: product.pantone,
    sku: product.sku,
    ean: product.ean,
    image_url: product.image_url,
    thumbnail_url: product.thumbnail_url,
    image_source: product.image_source,
    manufacturer_product_url: product.manufacturer_product_url,
    provider_product_url: product.provider_product_url,
    offers: product.offers || [],
  }));
}

async function loadJsonFile(filePath, fallback) {
  try {
    return JSON.parse(await readFile(filePath, "utf-8"));
  } catch {
    return fallback;
  }
}

async function writeJsonFile(filePath, payload) {
  await mkdir(stateDir, { recursive: true });
  await writeFile(filePath, JSON.stringify(payload, null, 2) + "\n", "utf-8");
}

async function loadSelection() {
  return loadJsonFile(selectionPath, null);
}

async function loadSelections() {
  return loadJsonFile(selectionsPath, {});
}

async function loadCandidateCache() {
  return loadJsonFile(candidatesPath, {});
}

async function saveSelection(payload) {
  const selections = await loadSelections();
  selections[payload.product.id] = payload;
  await writeJsonFile(selectionPath, payload);
  await writeJsonFile(selectionsPath, selections);
}

async function saveReview(payload) {
  const selections = await loadSelections();
  selections[payload.product.id] = payload;
  await writeJsonFile(selectionsPath, selections);
}

async function saveCandidateCache(productId, inputUrl, candidates, error = "") {
  const cache = await loadCandidateCache();
  cache[productId] = {
    captured_at: new Date().toISOString(),
    input_url: inputUrl,
    candidates,
    error,
  };
  await writeJsonFile(candidatesPath, cache);
  return cache[productId];
}

function isProbablyImageUrl(value) {
  try {
    const pathname = new URL(value).pathname.toLowerCase();
    return /\.(avif|gif|jpe?g|png|webp)(?:$|\?)/i.test(pathname);
  } catch {
    return false;
  }
}

function normalizeUrl(value, baseUrl) {
  const trimmed = String(value || "").trim();
  if (!trimmed || trimmed.startsWith("data:") || trimmed.startsWith("blob:")) return "";
  try {
    return new URL(trimmed, baseUrl).toString();
  } catch {
    return "";
  }
}

function parseAttributes(tag) {
  const attributes = {};
  const pattern = /([a-zA-Z_:.-]+)\s*=\s*("([^"]*)"|'([^']*)'|([^\s"'=<>`]+))/g;
  for (const match of tag.matchAll(pattern)) {
    attributes[match[1].toLowerCase()] = match[3] ?? match[4] ?? match[5] ?? "";
  }
  return attributes;
}

function largestSrcsetImage(srcset, baseUrl) {
  let best = { width: -1, url: "" };
  for (const rawPart of String(srcset || "").split(",")) {
    const parts = rawPart.trim().split(/\s+/);
    if (!parts[0]) continue;
    const width = parts[1]?.endsWith("w") ? Number(parts[1].slice(0, -1)) || 0 : 0;
    const url = normalizeUrl(parts[0], baseUrl);
    if (url && width >= best.width) best = { width, url };
  }
  return best.url;
}

function pageMatchTokens(pageUrl) {
  try {
    const slug = new URL(pageUrl).pathname.split("/").filter(Boolean).at(-1) || "";
    const generic = new Set([
      "producto",
      "filamento",
      "filamentos",
      "3d",
      "pla",
      "petg",
      "abs",
      "tpu",
      "hips",
      "nylon",
      "grilon3",
      "175",
      "285",
      "mm",
      "kg",
      "x1kg",
    ]);
    return slug
      .toLowerCase()
      .split(/[^a-z0-9]+/)
      .filter((token) => token.length >= 3 && !generic.has(token));
  } catch {
    return [];
  }
}

function candidateMatchesPage(candidate, tokens) {
  if (!tokens.length || candidate.source === "meta") return true;
  const text = `${candidate.url} ${candidate.alt || ""}`.toLowerCase();
  return tokens.some((token) => text.includes(token));
}

function imageScore(candidate) {
  const text = `${candidate.url} ${candidate.alt || ""}`.toLowerCase();
  const blocked = ["favicon", "logo", "icon", "tabla", "perfil", "placeholder", "no-image", "whatsapp", "/modules/"];
  if (blocked.some((token) => text.includes(token))) return -1000;

  let score = candidate.source === "meta" ? 55 : 0;
  if (candidate.source === "gallery") score += 40;
  if (candidate.source === "image") score += 20;
  if (text.includes("data-large_image")) score += 20;
  if (text.includes("600x600")) score += 35;
  if (text.includes("350x350")) score += 22;
  if (text.includes("product_main_2x")) score += 35;
  if (text.includes("product_main")) score += 28;
  if (text.includes("default_xl")) score += 18;
  if (/(^|[-_])web([-_.]|$)/.test(text)) score += 22;
  if (text.includes("woocommerce-product-gallery")) score += 18;
  if (text.includes("wp-post-image")) score -= 15;
  if (/(leon|dragon|pieza|textura)/.test(text)) score -= 45;
  if (/\.(svg)(?:$|\?)/.test(text)) score -= 80;
  return score;
}

function extractImageCandidates(html, pageUrl) {
  const candidates = [];
  const matchTokens = pageMatchTokens(pageUrl);

  for (const match of html.matchAll(/<meta\b[^>]+>/gi)) {
    const attrs = parseAttributes(match[0]);
    const key = String(attrs.property || attrs.name || "").toLowerCase();
    if (!["og:image", "og:image:secure_url", "twitter:image"].includes(key)) continue;
    const url = normalizeUrl(attrs.content, pageUrl);
    if (url) candidates.push({ url, source: "meta", alt: key });
  }

  for (const match of html.matchAll(/<img\b[^>]*>/gi)) {
    const tag = match[0];
    const attrs = parseAttributes(tag);
    const url = (
      normalizeUrl(attrs["data-large_image"], pageUrl)
      || largestSrcsetImage(attrs.srcset || attrs["data-srcset"], pageUrl)
      || normalizeUrl(attrs["data-src"], pageUrl)
      || normalizeUrl(attrs.src, pageUrl)
    );
    if (!url) continue;
    const classText = attrs.class || "";
    const source = /gallery|woocommerce-product-gallery|js-qv-product-cover|product-cover/.test(classText) ? "gallery" : "image";
    candidates.push({ url, source, alt: attrs.alt || classText });
  }

  const unique = new Map();
  for (const candidate of candidates) {
    if (!candidate.url || unique.has(candidate.url)) continue;
    if (!candidateMatchesPage(candidate, matchTokens)) continue;
    const score = imageScore(candidate);
    if (score <= -100) continue;
    unique.set(candidate.url, { ...candidate, score });
  }

  return [...unique.values()]
    .sort((left, right) => right.score - left.score || left.url.localeCompare(right.url))
    .slice(0, 3);
}

async function collectCandidates(inputUrl) {
  const url = normalizeUrl(inputUrl);
  if (!url) {
    throw new Error("URL invalida.");
  }
  if (isProbablyImageUrl(url)) {
    return [{ url, source: "direct", alt: "URL directa", score: 100 }];
  }

  const response = await fetch(url, {
    headers: {
      "user-agent": "CentralDeFilamentosImageCuration/1.0",
      accept: "text/html,application/xhtml+xml",
    },
  });
  if (!response.ok) {
    throw new Error(`No pude leer la pagina: HTTP ${response.status}.`);
  }
  const contentType = response.headers.get("content-type") || "";
  if (contentType.startsWith("image/")) {
    return [{ url, source: "direct", alt: contentType, score: 100 }];
  }
  const html = await response.text();
  return extractImageCandidates(html, url);
}

async function proxyImage(requestUrl, response) {
  const target = requestUrl.searchParams.get("url") || "";
  const url = normalizeUrl(target);
  if (!url) {
    sendText(response, 400, "URL invalida");
    return;
  }
  const upstream = await fetch(url, {
    headers: {
      "user-agent": "CentralDeFilamentosImageCuration/1.0",
      accept: "image/avif,image/webp,image/png,image/jpeg,image/gif,*/*",
    },
  });
  if (!upstream.ok) {
    sendText(response, upstream.status, `No pude leer la imagen: HTTP ${upstream.status}`);
    return;
  }
  const contentType = upstream.headers.get("content-type") || "application/octet-stream";
  const bytes = Buffer.from(await upstream.arrayBuffer());
  response.writeHead(200, {
    "content-type": contentType,
    "cache-control": "no-store",
  });
  response.end(bytes);
}

async function handleRequest(request, response) {
  const requestUrl = new URL(request.url || "/", `http://${request.headers.host || "localhost"}`);

  try {
    if (request.method === "GET" && requestUrl.pathname === "/") {
      await serveFile(response, path.join(toolDir, "index.html"));
      return;
    }
    if (request.method === "GET" && ["/app.js", "/styles.css"].includes(requestUrl.pathname)) {
      await serveFile(response, path.join(toolDir, requestUrl.pathname.slice(1)));
      return;
    }
    if (request.method === "GET" && requestUrl.pathname.startsWith("/public/")) {
      const filePath = safeJoin(publicDir, requestUrl.pathname.replace(/^\/public\//, ""));
      if (!filePath) {
        sendText(response, 403, "Ruta no permitida");
        return;
      }
      await serveFile(response, filePath);
      return;
    }
    if (request.method === "GET" && requestUrl.pathname === "/api/products") {
      sendJson(response, 200, { products: await loadStockProducts() });
      return;
    }
    if (request.method === "GET" && requestUrl.pathname === "/api/selection") {
      sendJson(response, 200, { selection: await loadSelection() });
      return;
    }
    if (request.method === "GET" && requestUrl.pathname === "/api/selections") {
      sendJson(response, 200, { selections: await loadSelections() });
      return;
    }
    if (request.method === "GET" && requestUrl.pathname === "/api/candidate-cache") {
      sendJson(response, 200, { cache: await loadCandidateCache() });
      return;
    }
    if (request.method === "GET" && requestUrl.pathname === "/api/image") {
      await proxyImage(requestUrl, response);
      return;
    }
    if (request.method === "POST" && requestUrl.pathname === "/api/candidates") {
      const body = await readRequestJson(request);
      try {
        const candidates = (await collectCandidates(body.url)).slice(0, 3);
        if (body.product_id) {
          const cached = await saveCandidateCache(String(body.product_id), body.url, candidates);
          sendJson(response, 200, { candidates, cached });
        } else {
          sendJson(response, 200, { candidates });
        }
      } catch (error) {
        if (body.product_id) {
          const cached = await saveCandidateCache(String(body.product_id), body.url, [], error instanceof Error ? error.message : String(error));
          sendJson(response, 200, { candidates: [], cached, error: cached.error });
        } else {
          throw error;
        }
      }
      return;
    }
    if (request.method === "POST" && requestUrl.pathname === "/api/select") {
      const body = await readRequestJson(request);
      if (!body.product?.id || !body.candidate?.url) {
        sendJson(response, 400, { error: "Falta producto o candidato." });
        return;
      }
      const payload = {
        selected_at: new Date().toISOString(),
        action: "use-candidate",
        product: body.product,
        candidate: body.candidate,
        source_input_url: body.source_input_url || "",
        note: body.note || "",
      };
      await saveSelection(payload);
      sendJson(response, 200, { selection: payload, path: selectionPath });
      return;
    }
    if (request.method === "POST" && requestUrl.pathname === "/api/review") {
      const body = await readRequestJson(request);
      if (!body.product?.id || !body.action) {
        sendJson(response, 400, { error: "Falta producto o accion." });
        return;
      }
      const payload = {
        reviewed_at: new Date().toISOString(),
        action: body.action,
        product: body.product,
        candidate: body.candidate || null,
        source_input_url: body.source_input_url || "",
        note: body.note || "",
      };
      await saveReview(payload);
      sendJson(response, 200, { review: payload, path: selectionsPath });
      return;
    }

    sendText(response, 404, "No encontrado");
  } catch (error) {
    sendJson(response, 500, { error: error instanceof Error ? error.message : String(error) });
  }
}

createServer(handleRequest).listen(port, host, () => {
  console.log(`Curador local de imagenes: http://${host}:${port}`);
  console.log("No escribe assets ni stock. Guarda candidatas y decisiones en .image-curation/");
});
