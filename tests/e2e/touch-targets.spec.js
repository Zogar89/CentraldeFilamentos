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

async function dimensions(locator) {
  return locator.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    return { width: rect.width, height: rect.height };
  });
}

for (const [name, path, selectors] of routeSelectors) {
  test(`${name} primary controls are at least 24 by 24 CSS pixels`, async ({ page }) => {
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
        .filter(({ width, height }) => width < 23.5 || height < 23.5)
    ), selectors);

    expect(undersized).toEqual([]);
  });
}

test("summary restores compact visible controls", async ({ page }, testInfo) => {
  await page.goto("./");
  await waitForStablePage(page);

  const mobile = testInfo.project.name.startsWith("mobile-");
  const quickLine = await dimensions(page.locator(".quick-line").first());
  const stockWatch = await dimensions(page.locator(".summary-stock-watch").first());
  const quoteAdd = await dimensions(page.locator(".summary-quote-add").first());

  expect(quickLine.height).toBeLessThanOrEqual(mobile ? 32.5 : 30.5);
  expect(quickLine.height).toBeGreaterThanOrEqual(23.5);
  expect(stockWatch.width).toBeCloseTo(24, 0);
  expect(stockWatch.height).toBeCloseTo(24, 0);
  expect(quoteAdd.width).toBeCloseTo(mobile ? 40 : 42, 0);
  expect(quoteAdd.height).toBeCloseTo(mobile ? 36 : 28, 0);
});

test("compact overlay controls retain their intended size", async ({ page }, testInfo) => {
  await page.goto("./");
  await waitForStablePage(page);
  await page.locator(".summary-quote-add").first().click();
  const mobile = testInfo.project.name.startsWith("mobile-");
  const removeButton = page.getByRole("dialog", { name: "Lista de cotizacion" }).locator(".quote-list-remove").first();
  const drawerClose = page.getByRole("button", { name: "Cerrar lista de cotizacion" });
  await expect(removeButton).toBeVisible();
  expect(await dimensions(removeButton)).toEqual(expect.objectContaining({ width: mobile ? 40 : 28, height: mobile ? 40 : 28 }));
  expect(await dimensions(drawerClose)).toEqual(expect.objectContaining({ width: mobile ? 40 : 32, height: mobile ? 40 : 32 }));

  await drawerClose.click();
  await page.locator(".summary-media-button").first().click();
  const imageClose = page.getByRole("button", { name: "Cerrar imagen ampliada" });
  await expect(imageClose).toBeVisible();
  expect(await dimensions(imageClose)).toEqual(expect.objectContaining({ width: 30, height: 30 }));
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
