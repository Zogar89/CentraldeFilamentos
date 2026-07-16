import { expect } from "@playwright/test";

const runtimeDiagnostics = new WeakMap();

export function installRuntimeGuards(page) {
  const diagnostics = {
    consoleErrors: [],
    pageErrors: [],
    failedRequests: [],
    httpErrors: [],
  };
  runtimeDiagnostics.set(page, diagnostics);

  page.on("console", (message) => {
    if (message.type() === "error") {
      const location = message.location();
      if (!location.url.endsWith("/favicon.ico")) {
        diagnostics.consoleErrors.push(`${message.text()}${location.url ? ` (${location.url})` : ""}`);
      }
    }
  });
  page.on("pageerror", (error) => diagnostics.pageErrors.push(error.message));
  page.on("requestfailed", (request) => {
    try {
      const requestUrl = new URL(request.url());
      if (requestUrl.origin === "http://127.0.0.1:4173") {
        diagnostics.failedRequests.push(`${request.method()} ${requestUrl.pathname}: ${request.failure()?.errorText || "failed"}`);
      }
    } catch {
      diagnostics.failedRequests.push(`${request.method()} ${request.url()}: ${request.failure()?.errorText || "failed"}`);
    }
  });
  page.on("response", (response) => {
    try {
      const responseUrl = new URL(response.url());
      if (
        responseUrl.origin === "http://127.0.0.1:4173" &&
        response.status() >= 400 &&
        !responseUrl.pathname.endsWith("/favicon.ico")
      ) {
        diagnostics.httpErrors.push(`${response.status()} ${responseUrl.pathname}`);
      }
    } catch {
      // Ignore non-URL protocol responses.
    }
  });
}

export async function waitForStablePage(page) {
  await page.waitForLoadState("networkidle");
  await page.evaluate(async () => {
    await document.fonts?.ready;
    const visibleImages = [...document.images].filter((image) => {
      const rect = image.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0 && image.currentSrc;
    });
    await Promise.allSettled(visibleImages.map((image) => image.decode()));
  });
}

export async function inspectResponsiveLayout(page) {
  return page.evaluate(() => {
    const root = document.documentElement;
    const viewportWidth = root.clientWidth;
    const viewportHeight = root.clientHeight;
    const isVisible = (element) => {
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
    };
    const describe = (element) => {
      const text = element.getAttribute("aria-label") || element.textContent || element.getAttribute("alt") || element.tagName;
      return `${element.tagName.toLowerCase()}${element.id ? `#${element.id}` : ""}: ${text.trim().replace(/\s+/g, " ").slice(0, 90)}`;
    };

    const brokenImages = [...document.images]
      .filter((image) => isVisible(image) && image.complete && image.naturalWidth === 0)
      .map((image) => image.currentSrc || image.src)
      .slice(0, 20);

    const scrollExceptions = ".color-picker-map-scroll, .quick-lines, .vendor-table-wrap";
    const clippedControls = [...document.querySelectorAll("button, a[href], input, select, textarea, [role='button'], [role='tab']")]
      .filter(isVisible)
      .filter((element) => !element.matches(".skip-link"))
      .filter((element) => !element.closest(scrollExceptions))
      .filter((element) => {
        const rect = element.getBoundingClientRect();
        return rect.left < -1 || rect.right > viewportWidth + 1;
      })
      .map(describe)
      .slice(0, 20);

    return {
      viewport: { width: viewportWidth, height: viewportHeight },
      horizontalOverflow: Math.max(0, root.scrollWidth - viewportWidth),
      h1Count: document.querySelectorAll("h1").length,
      visibleH1Count: [...document.querySelectorAll("h1")].filter(isVisible).length,
      h1Labels: [...document.querySelectorAll("h1")].map((heading) => describe(heading)),
      brokenImages,
      clippedControls,
    };
  });
}

export function assertRuntimeHealthy(page) {
  const diagnostics = runtimeDiagnostics.get(page) || {
    consoleErrors: ["Runtime guards were not installed"],
    pageErrors: [],
    failedRequests: [],
    httpErrors: [],
  };
  expect(diagnostics.consoleErrors, "console errors").toEqual([]);
  expect(diagnostics.pageErrors, "uncaught page errors").toEqual([]);
  expect(diagnostics.failedRequests, "failed same-origin requests").toEqual([]);
  expect(diagnostics.httpErrors, "same-origin HTTP errors").toEqual([]);
}
