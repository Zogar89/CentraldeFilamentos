import { expect, test } from "@playwright/test";

import { waitForStablePage } from "./helpers/audit.js";

const routes = [
  ["summary", "./"],
  ["color-picker", "./color-picker.html"],
  ["vendor-statistics", "./estadisticas.html"],
];

test.beforeEach(async ({}, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-1080", "Local performance sampling runs once on the representative desktop viewport.");
});

for (const [name, path] of routes) {
  test(`${name} stays within local navigation and asset budgets`, async ({ page }) => {
    const samples = [];
    for (let run = 0; run < 3; run += 1) {
      await page.goto(path);
      await waitForStablePage(page);
      samples.push(await page.evaluate(() => {
        const navigation = performance.getEntriesByType("navigation")[0];
        const resources = performance.getEntriesByType("resource");
        const sizeFor = (entry) => entry.transferSize || entry.encodedBodySize || 0;
        const sumByType = (type) => resources
          .filter((entry) => entry.initiatorType === type)
          .reduce((total, entry) => total + sizeFor(entry), 0);
        return {
          domContentLoadedMs: navigation.domContentLoadedEventEnd - navigation.startTime,
          loadMs: navigation.loadEventEnd - navigation.startTime,
          resourceBytes: resources.reduce((total, entry) => total + sizeFor(entry), 0),
          scriptBytes: sumByType("script"),
          cssBytes: sumByType("css") || sumByType("link"),
          resourceCount: resources.length,
        };
      }));
    }

    await test.info().attach(`${name}-performance.json`, {
      body: Buffer.from(JSON.stringify(samples, null, 2)),
      contentType: "application/json",
    });
    const worst = (key) => Math.max(...samples.map((sample) => sample[key]));
    expect.soft(worst("domContentLoadedMs"), `${name} DOMContentLoaded`).toBeLessThanOrEqual(3000);
    expect.soft(worst("loadMs"), `${name} window load`).toBeLessThanOrEqual(5000);
    expect.soft(worst("resourceBytes"), `${name} resource payload`).toBeLessThanOrEqual(2_000_000);
    expect.soft(worst("scriptBytes"), `${name} JavaScript payload`).toBeLessThanOrEqual(250_000);
    expect.soft(worst("cssBytes"), `${name} CSS payload`).toBeLessThanOrEqual(120_000);
  });
}
