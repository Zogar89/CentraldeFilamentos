import { readFile } from "node:fs/promises";
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const NOW = Date.parse("2026-10-20T16:00:00Z");
const DAY_MS = 86_400_000;
const isoAgo = (days) => new Date(NOW - days * DAY_MS).toISOString();

async function installStock(page, configure) {
  const stock = JSON.parse(await readFile(new URL("../../public/data/stock.json", import.meta.url), "utf8"));
  for (const source of stock.sources) {
    source.last_success_at = isoAgo(0);
    source.stock_unchanged_since = isoAgo(0);
  }
  configure(stock.sources);
  await page.clock.install({ time: new Date(NOW) });
  await page.route("**/data/stock.json*", (route) => route.fulfill({ json: stock }));
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
