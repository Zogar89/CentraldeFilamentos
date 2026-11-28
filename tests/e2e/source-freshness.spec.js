import { readFile } from "node:fs/promises";
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const NOW = Date.parse("2026-10-20T16:00:00Z");
const DAY_MS = 86_400_000;
const isoAgo = (days) => new Date(NOW - days * DAY_MS).toISOString();

async function installStock(page, configure, health = { status: "ok" }) {
  const stock = JSON.parse(await readFile(new URL("../../public/data/stock.json", import.meta.url), "utf8"));
  stock.generated_at = isoAgo(0);
  for (const source of stock.sources) {
    source.last_success_at = isoAgo(0);
    source.stock_unchanged_since = isoAgo(0);
  }
  configure(stock.sources, stock);
  await page.clock.install({ time: new Date(NOW) });
  await page.route("**/data/stock.json*", (route) => route.fulfill({ json: stock }));
  await page.route("**/data/build_business_log.json*", (route) => route.fulfill({ json: health }));
  await page.goto("./");
  await expect(page.locator(".footer-provider")).toHaveCount(stock.sources.length);
}

test("each provider warns only about unchanged stock as time advances", async ({ page }) => {
  await installStock(page, (sources) => {
    sources[0].stock_unchanged_since = isoAgo(6);
    sources[1].last_success_at = isoAgo(6);
    sources[1].last_attempt_at = isoAgo(0);
    sources[1].stock_unchanged_since = isoAgo(7);
  });
  const providers = page.locator(".footer-provider");
  await expect(providers.nth(0).getByRole("status")).toContainText("Stock sin cambios detectados desde hace 6 días.");
  await expect(providers.nth(1).getByRole("status")).toContainText("Stock sin cambios detectados desde hace 7 días.");
  await expect(providers.nth(2).getByRole("status")).toHaveCount(0);
  await expect(providers.nth(0)).toContainText("Última lectura:");
  await expect(providers.nth(0)).toContainText("Sin cambios observados desde");

  const accessibility = await new AxeBuilder({ page }).include("#site-footer")
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
  expect(accessibility.violations.filter((violation) => ["critical", "serious"].includes(violation.impact))).toEqual([]);

  await page.clock.setSystemTime(new Date(NOW + 5 * DAY_MS));
  await page.clock.fastForward(60_000);
  await expect(providers.nth(2).getByRole("status")).toContainText("Stock sin cambios detectados desde hace 5 días.");
});

test("legacy or invalid timestamps do not invent dates or raise a five-day alarm", async ({ page }) => {
  await installStock(page, (sources) => {
    sources.forEach((source) => delete source.stock_unchanged_since);
    sources[0].last_success_at = "invalid";
    sources[0].last_attempt_at = isoAgo(0);
    sources[1].last_success_at = isoAgo(7);
  });
  await expect(page.locator(".source-freshness-alert")).toHaveCount(0);
  await expect(page.locator(".source-freshness-pending")).toHaveCount(3);
  await expect(page.locator(".footer-provider").first()).toContainText("Última lectura: Sin datos");
});

test("partial stock distinguishes earlier data from a reading that is still pending", async ({ page }) => {
  await installStock(page, (sources, stock) => {
    sources[0].status = "error";
    sources[0].last_success_at = isoAgo(2);
    sources[0].stock_unchanged_since = isoAgo(2);
    sources[1].status = "error";
    sources[1].last_success_at = "";
    sources[1].stock_unchanged_since = "";
    for (const product of stock.products) {
      product.offers = product.offers.filter((offer) => offer.source_id !== sources[1].id);
    }
  }, { status: "degraded", generated_at: isoAgo(0) });

  const notice = page.locator(".catalog-explorer-capture-status");
  await expect(notice).toContainText("Actualización parcial.");
  await expect(notice).toContainText("Se conservan los datos anteriores de");
  await expect(notice).toContainText("Lectura válida pendiente para");
  await expect(page.locator(".footer-provider").nth(0)).toContainText("Stock de una lectura anterior.");
  await expect(page.locator(".footer-provider").nth(1).locator(".footer-provider-stock strong")).toHaveText("—");
  await expect(page.locator(".catalog-explorer-provider-stock").getByText("dato anterior").first()).toBeVisible();
  await expect(page.locator(".source-freshness-alert")).toHaveCount(0);
});

test("a blocked attempt marks the published catalog as earlier data", async ({ page }) => {
  await installStock(page, (sources, stock) => {
    stock.generated_at = isoAgo(1);
    for (const source of sources) source.last_success_at = isoAgo(1);
  }, { status: "blocked", generated_at: isoAgo(0) });

  await expect(page.locator(".catalog-explorer-capture-status")).toContainText("Captura bloqueada.");
  await expect(page.locator(".source-read-status").filter({ hasText: "Stock de una lectura anterior." })).toHaveCount(3);
  await expect(page.locator(".catalog-explorer-provider-stock").getByText("dato anterior").first()).toBeVisible();
});

test("a blocked log from before the published catalog does not mark stock as earlier data", async ({ page }) => {
  await installStock(page, () => {}, { status: "blocked", generated_at: isoAgo(1) });

  await expect(page.locator(".catalog-explorer-capture-status")).toHaveCount(0);
  await expect(page.locator(".source-read-status")).toHaveCount(0);
});

test("vendor history shows a gap for an absent provider and retains a measured zero", async ({ page }) => {
  const days = [
    { date: "2026-10-18", captured_at: isoAgo(2), providers: { north: 60 } },
    { date: "2026-10-19", captured_at: isoAgo(1), providers: {}, checks: [{ captured_at: isoAgo(1), providers: {} }] },
    { date: "2026-10-20", captured_at: isoAgo(0), providers: { north: 0 } },
  ];
  await page.route("**/data/feature_flags.json*", (route) => route.fulfill({ json: { vendorStatsEnabled: true } }));
  await page.route("**/data/provider_stock_history.json*", (route) => route.fulfill({
    json: { generated_at: isoAgo(0), providers: [{ id: "north", name: "Norte" }], days },
  }));
  await page.route("**/data/build_business_log.json*", (route) => route.fulfill({
    json: { status: "degraded", summary: "Captura parcial", generated_at: isoAgo(0) },
  }));
  await page.goto("./estadisticas.html");

  await expect(page.locator(".build-health-degraded")).toBeVisible();
  const card = page.locator(".vendor-stat-card");
  const daysTable = card.locator(".daily-row");
  await expect(daysTable.nth(0).locator("td").nth(1)).toHaveText("0");
  await expect(daysTable.nth(0).locator("td").nth(2)).toHaveText("Sin base");
  await expect(daysTable.nth(1).locator("td").nth(1)).toHaveText("Sin medición");
  await expect(card.locator(".chart-point")).toHaveCount(2);
  await expect(card.locator(".chart-line")).toHaveCount(0);
  const checks = card.locator(".intraday-checks").nth(1);
  await checks.locator("summary").click();
  await expect(checks.locator(".intraday-quantity")).toHaveText("Sin medición");
  await expect(checks.getByText("Sin base")).toHaveCount(2);
});
