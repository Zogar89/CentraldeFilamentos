import { createServer } from "node:http";
import { createReadStream } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { draftProducts, reviewStatus, validateReview } from "./curation-state.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..", "..");
const publicDir = path.join(rootDir, "public");
const stateDir = path.join(rootDir, ".image-curation");
const scanPath = path.join(stateDir, "grilon3-scan.json");
const selectionsPath = path.join(stateDir, "selections.json");
const port = Number(process.env.PORT || 4177);
const host = process.env.HOST || "127.0.0.1";

const mimeTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".gif": "image/gif",
  ".jpeg": "image/jpeg",
  ".jpg": "image/jpeg",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
};

function sendJson(response, status, payload) {
  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  });
  response.end(JSON.stringify(payload, null, 2));
}

function sendText(response, status, value) {
  response.writeHead(status, {
    "content-type": "text/plain; charset=utf-8",
    "cache-control": "no-store",
  });
  response.end(value);
}

function serveFile(response, filePath) {
  response.writeHead(200, {
    "content-type": mimeTypes[path.extname(filePath)] || "application/octet-stream",
    "cache-control": "no-store",
  });
  createReadStream(filePath).pipe(response);
}

function safePublicPath(requestPath) {
  const relativePath = decodeURIComponent(requestPath).replace(/^\/+/, "");
  const resolved = path.resolve(publicDir, relativePath);
  const relative = path.relative(publicDir, resolved);
  if (relative.startsWith("..") || path.isAbsolute(relative)) return "";
  return resolved;
}

async function readJson(filePath, fallback) {
  try {
    return JSON.parse(await readFile(filePath, "utf-8"));
  } catch (error) {
    if (error?.code === "ENOENT") return fallback;
    throw error;
  }
}

async function readRequestJson(request) {
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  const raw = Buffer.concat(chunks).toString("utf-8");
  if (!raw.trim()) return {};
  try {
    return JSON.parse(raw);
  } catch {
    throw new Error("El cuerpo JSON no es válido.");
  }
}

async function loadProducts() {
  const scan = await readJson(scanPath, null);
  if (!scan) {
    throw new Error("Falta .image-curation/grilon3-scan.json. Ejecutá primero el scan oficial.");
  }
  return draftProducts(scan);
}

async function loadReviews() {
  const reviews = await readJson(selectionsPath, {});
  return reviews && typeof reviews === "object" && !Array.isArray(reviews) ? reviews : {};
}

async function saveReview(review) {
  const reviews = await loadReviews();
  reviews[review.product_url] = review;
  await mkdir(stateDir, { recursive: true });
  await writeFile(selectionsPath, `${JSON.stringify(reviews, null, 2)}\n`, "utf-8");
}

function normalizeRemoteUrl(value) {
  try {
    const url = new URL(String(value || ""));
    if (!["http:", "https:"].includes(url.protocol)) return "";
    return url.toString();
  } catch {
    return "";
  }
}

async function proxyImage(requestUrl, response) {
  const target = normalizeRemoteUrl(requestUrl.searchParams.get("url"));
  if (!target) {
    sendText(response, 400, "URL de imagen inválida");
    return;
  }
  const upstream = await fetch(target, {
    headers: {
      accept: "image/avif,image/webp,image/png,image/jpeg,image/gif,*/*",
      "user-agent": "CentralDeFilamentosImageCuration/2.0",
    },
  });
  if (!upstream.ok) {
    sendText(response, upstream.status, `No pude leer la imagen: HTTP ${upstream.status}`);
    return;
  }
  const contentType = upstream.headers.get("content-type") || "application/octet-stream";
  if (!contentType.startsWith("image/")) {
    sendText(response, 415, "La URL no devolvió una imagen");
    return;
  }
  response.writeHead(200, { "content-type": contentType, "cache-control": "no-store" });
  response.end(Buffer.from(await upstream.arrayBuffer()));
}

async function handleRequest(request, response) {
  const requestUrl = new URL(request.url || "/", `http://${request.headers.host || "localhost"}`);
  try {
    if (request.method === "GET" && requestUrl.pathname === "/") {
      serveFile(response, path.join(__dirname, "index.html"));
      return;
    }
    if (request.method === "GET" && ["/app.js", "/styles.css"].includes(requestUrl.pathname)) {
      serveFile(response, path.join(__dirname, requestUrl.pathname.slice(1)));
      return;
    }
    if (request.method === "GET" && requestUrl.pathname.startsWith("/public/")) {
      const filePath = safePublicPath(requestUrl.pathname.slice("/public/".length));
      if (!filePath) {
        sendText(response, 403, "Ruta no permitida");
        return;
      }
      serveFile(response, filePath);
      return;
    }
    if (request.method === "GET" && requestUrl.pathname === "/api/image") {
      await proxyImage(requestUrl, response);
      return;
    }
    if (request.method === "GET" && requestUrl.pathname === "/api/products") {
      const [products, reviews] = await Promise.all([loadProducts(), loadReviews()]);
      sendJson(response, 200, {
        products: products.map((product) => ({
          ...product,
          review_status: reviewStatus(product, reviews[product.product_url]),
        })),
      });
      return;
    }
    if (request.method === "GET" && requestUrl.pathname === "/api/selections") {
      sendJson(response, 200, { selections: await loadReviews() });
      return;
    }
    if (request.method === "POST" && requestUrl.pathname === "/api/review") {
      const body = await readRequestJson(request);
      const products = await loadProducts();
      const product = products.find((item) => item.product_url === body.product_url);
      if (!product) {
        sendJson(response, 400, { error: "El producto no pertenece al scan activo." });
        return;
      }
      const review = validateReview(product, {
        product_url: body.product_url,
        selected_image_remote_url: body.selected_image_remote_url,
        selection_reason: body.selection_reason,
        gallery_fingerprint: body.gallery_fingerprint,
        reviewed_at: new Date().toISOString(),
      });
      await saveReview(review);
      sendJson(response, 200, { review });
      return;
    }
    sendText(response, 404, "No encontrado");
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    const status = request.method === "POST" ? 400 : 500;
    sendJson(response, status, { error: message });
  }
}

createServer(handleRequest).listen(port, host, () => {
  console.log(`Curador local de galerías Grilon3: http://${host}:${port}`);
  console.log("Solo guarda revisiones en .image-curation/selections.json; no modifica producción.");
});
