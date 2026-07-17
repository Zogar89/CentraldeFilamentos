import { expect, test } from "@playwright/test";

import { waitForStablePage } from "./helpers/audit.js";

const routeSelectors = [
  ["summary", "./", [
    ".catalog-header-search input",
    ".catalog-header-comparator",
    ".catalog-header-quote",
    ".catalog-explorer-material",
    ".catalog-explorer-color",
    ".catalog-explorer-filters select",
    ".catalog-explorer-result-meta button",
    ".catalog-explorer-result-meta select",
    ".catalog-explorer-result-image",
    ".catalog-explorer-add",
    ".quote-workflow-tabs button",
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

test("summary keeps exploration controls comfortably tappable", async ({ page }) => {
  await page.goto("./");
  await waitForStablePage(page);

  const material = await dimensions(page.locator(".catalog-explorer-material").first());
  const color = await dimensions(page.locator(".catalog-explorer-color").first());
  const quoteAdd = await dimensions(page.locator(".catalog-explorer-add").first());

  expect(material.width).toBeGreaterThanOrEqual(90);
  expect(material.height).toBeGreaterThanOrEqual(115);
  expect(color.width).toBeGreaterThanOrEqual(33.5);
  expect(color.height).toBeGreaterThanOrEqual(33.5);
  expect(quoteAdd.width).toBeGreaterThanOrEqual(75);
  expect(quoteAdd.height).toBeGreaterThanOrEqual(51);
});

test("compact overlay controls retain their intended size", async ({ page }, testInfo) => {
  await page.goto("./");
  await waitForStablePage(page);
  await page.locator(".catalog-explorer-add").first().click();
  const compactActionsMobile = testInfo.project.use.viewport.width <= 520;
  const removeButton = page.locator(".quote-list-panel:visible .quote-list-remove").first();
  const drawerClose = page.getByRole("button", { name: "Cerrar lista de cotizacion" });
  await expect(removeButton).toBeVisible();
  expect(await dimensions(removeButton)).toEqual(expect.objectContaining({ width: compactActionsMobile ? 40 : 28, height: compactActionsMobile ? 40 : 28 }));
  if (compactActionsMobile) {
    expect(await dimensions(drawerClose)).toEqual(expect.objectContaining({ width: 40, height: 40 }));
    await drawerClose.click();
  }

  await page.locator(".catalog-explorer-result-image").first().click();
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
