import { expect, test } from "@playwright/test";

import {
  assertRuntimeHealthy,
  inspectResponsiveLayout,
  installRuntimeGuards,
  waitForStablePage,
} from "./helpers/audit.js";

const routes = [
  ["summary", "./"],
  ["color picker", "./color-picker.html"],
  ["vendor statistics", "./estadisticas.html"],
];

test.beforeEach(async ({ page }) => {
  installRuntimeGuards(page);
});

for (const [name, path] of routes) {
  test(`${name} remains structurally healthy and inside the viewport`, async ({ page }) => {
    const response = await page.goto(path);
    expect(response?.ok(), `${name} should return a successful document response`).toBe(true);

    await waitForStablePage(page);
    await expect(page.locator("#main-content")).toBeVisible();

    if (["desktop-4k", "desktop-2k"].includes(test.info().project.name)) {
      const mainWidth = await page.locator("#main-content").evaluate((element) => element.getBoundingClientRect().width);
      expect.soft(mainWidth, `${name} main width`).toBeLessThanOrEqual(1180.5);
    }

    const layout = await inspectResponsiveLayout(page);
    await test.info().attach("responsive-layout.json", {
      body: Buffer.from(JSON.stringify(layout, null, 2)),
      contentType: "application/json",
    });
    expect.soft(layout.horizontalOverflow, `${name} document overflow`).toBeLessThanOrEqual(1);
    expect.soft(layout.brokenImages, `${name} broken images`).toEqual([]);
    expect.soft(layout.clippedControls, `${name} clipped controls`).toEqual([]);
    expect.soft(layout.h1Count, `${name} should expose one h1`).toBe(1);
    assertRuntimeHealthy(page);
  });
}
