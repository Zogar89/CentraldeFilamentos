import { expect, test } from "@playwright/test";

import { waitForStablePage } from "./helpers/audit.js";

const auditedProjects = new Set(["desktop-1080", "mobile-390"]);

test.beforeEach(async ({ page }, testInfo) => {
  test.skip(!auditedProjects.has(testInfo.project.name), "Option 1 runs on representative desktop and mobile viewports.");
  await page.goto("./");
  await waitForStablePage(page);
  await page.evaluate(() => localStorage.removeItem("centraldefilamentos.quoteList.v1"));
  await page.reload();
  await waitForStablePage(page);
});

test("keeps material as a hard constraint and builds the quote in the responsive workspace", async ({ page }, testInfo) => {
  await expect(page.getByRole("heading", { name: "¿Qué material vas a usar?" })).toBeVisible();
  await expect(page.getByRole("button", { name: /PLA, .* opciones/ })).toHaveAttribute("aria-pressed", "true");

  const family = page.getByRole("button", { name: /Amarillos, .* opciones, .* unidades publicadas/ });
  await expect(family).toBeVisible();
  await expect(family).toHaveAttribute("title", "Amarillos");
  await family.click();

  const rows = page.locator(".catalog-explorer-result-row");
  await expect(rows.first()).toBeVisible();
  expect(await rows.evaluateAll((items) => items.every((item) => item.dataset.material === "PLA"))).toBe(true);
  expect(await rows.evaluateAll((items) => items.every((item) => item.dataset.colorFamily === "Amarillos"))).toBe(true);
  expect(new Set(await rows.evaluateAll((items) => items.map((item) => item.dataset.color))).size).toBeGreaterThan(1);

  await rows.first().getByRole("button", { name: /Agregar .* a la lista de cotización/ }).click();

  if (testInfo.project.name === "desktop-1080") {
    const rail = page.locator(".catalog-quote-rail");
    await expect(rail).toBeVisible();
    await expect(rail.locator(".quote-list-item")).toHaveCount(1);
    await expect(page.getByRole("dialog", { name: "Lista de cotizacion" })).toBeHidden();
  } else {
    const drawer = page.getByRole("dialog", { name: "Lista de cotizacion" });
    await expect(drawer).toBeVisible();
    await expect(drawer.locator(".quote-list-item")).toHaveCount(1);
  }
});

test("packs unlabeled PLA families with the same spacing as exact colors", async ({ page }, testInfo) => {
  const familyGrid = page.locator(".catalog-explorer-color-scroll");
  const familyButtons = familyGrid.getByRole("button");
  const layout = (element) => {
    const buttons = [...element.querySelectorAll("button")];
    const first = buttons[0].getBoundingClientRect();
    const second = buttons[1].getBoundingClientRect();
    return {
      display: getComputedStyle(element).display,
      gap: Math.round(second.left - first.right),
    };
  };

  await expect(familyButtons).toHaveCount(11);
  expect(await familyButtons.allTextContents()).toEqual(Array(11).fill(""));
  const familyLayout = await familyGrid.evaluate(layout);
  if (testInfo.project.name === "desktop-1080") {
    expect(await familyGrid.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
  }

  await page.getByRole("button", { name: /PETG, .* opciones/ }).click();
  expect(await page.locator(".catalog-explorer-color-scroll").evaluate(layout)).toEqual(familyLayout);
});

test("uses the same button design for PLA families and exact colors", async ({ page }) => {
  const buttonStyle = (element) => {
    const style = getComputedStyle(element);
    return {
      height: style.height,
      padding: style.padding,
      borderRadius: style.borderRadius,
      backgroundColor: style.backgroundColor,
    };
  };

  const plaButtons = page.locator(".catalog-explorer-color");
  await expect(plaButtons).toHaveCount(11);
  const plaStyle = await plaButtons.first().evaluate(buttonStyle);

  await page.getByRole("button", { name: /PETG, .* opciones/ }).click();
  const exactButtons = page.locator(".catalog-explorer-color");
  await expect(exactButtons.first()).toBeVisible();

  expect(await exactButtons.first().evaluate(buttonStyle)).toEqual(plaStyle);
});
