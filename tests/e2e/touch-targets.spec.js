import { expect, test } from "@playwright/test";

import { waitForStablePage } from "./helpers/audit.js";

const routeSelectors = [
  ["summary", "./", [
    ".view-switch .nav-link",
    ".filters input",
    ".filters select",
    ".more-filters-button",
    ".quick-line",
    ".summary-media-button",
    ".summary-stock-watch",
    ".summary-quote-add",
    ".quote-import-help-tip",
    ".provider-mark",
  ]],
  ["color picker", "./color-picker.html", [
    ".view-switch .nav-link",
    ".color-picker-view-tabs button",
    ".color-picker-similar form button",
    ".color-picker-similar form input",
    ".color-picker-tile",
  ]],
];

test.beforeEach(async ({}, testInfo) => {
  test.skip(testInfo.project.name !== "mobile-390", "Touch target audit runs at the representative mobile viewport.");
});

async function dimensions(locator) {
  return locator.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    return { width: rect.width, height: rect.height };
  });
}

for (const [name, path, selectors] of routeSelectors) {
  test(`${name} primary touch targets are at least 44 by 44 CSS pixels`, async ({ page }) => {
    await page.goto(path);
    await waitForStablePage(page);

    const undersized = await page.evaluate((targetSelectors) => targetSelectors.flatMap((selector) =>
      [...document.querySelectorAll(selector)]
        .filter((element) => {
          const style = getComputedStyle(element);
          const rect = element.getBoundingClientRect();
          return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
        })
        .map((element) => {
          const rect = element.getBoundingClientRect();
          return { selector, label: element.getAttribute("aria-label") || element.textContent.trim(), width: rect.width, height: rect.height };
        })
        .filter(({ width, height }) => width < 43.5 || height < 43.5)
    ), selectors);

    expect(undersized).toEqual([]);
  });
}

test("quote removal exposes a 44px touch area", async ({ page }) => {
  await page.goto("./");
  await waitForStablePage(page);
  await page.locator(".summary-quote-add").first().click();
  const removeButton = page.getByRole("dialog", { name: "Lista de cotizacion" }).locator(".quote-list-remove").first();
  await expect(removeButton).toBeVisible();
  expect(await dimensions(removeButton)).toEqual(expect.objectContaining({ width: 44, height: 44 }));
});

test("color-map points expose 44px touch areas", async ({ page }) => {
  await page.goto("./color-picker.html");
  await waitForStablePage(page);
  await page.getByRole("button", { name: "Mapa 2D", exact: true }).click();
  const mapPoint = page.locator(".color-picker-map-point .color-picker-tile").first();
  await expect(mapPoint).toBeVisible();
  const mapPointSize = await dimensions(mapPoint);
  expect(mapPointSize.width).toBeGreaterThanOrEqual(43.5);
  expect(mapPointSize.height).toBeGreaterThanOrEqual(43.5);
});
