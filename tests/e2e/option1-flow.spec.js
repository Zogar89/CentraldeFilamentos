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

  const color = page.getByRole("button", { name: /Amarillo Fluo, .* unidades publicadas/ });
  await expect(color).toBeVisible();
  await color.click();

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
