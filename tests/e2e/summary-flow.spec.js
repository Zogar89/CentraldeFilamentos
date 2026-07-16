import { expect, test } from "@playwright/test";

import { waitForStablePage } from "./helpers/audit.js";

const auditedProjects = new Set(["desktop-1080", "mobile-390"]);
const productIds = [
  "pla-amarillo-175-1000-grilon3",
  "pla-plaplus-amarillo-175-750-3n3",
];

test.beforeEach(async ({ page }, testInfo) => {
  test.skip(!auditedProjects.has(testInfo.project.name), "Deep interaction flow runs on representative desktop and mobile viewports.");
  await page.goto("./");
  await waitForStablePage(page);
  await page.evaluate(() => localStorage.removeItem("centraldefilamentos.quoteList.v1"));
  await page.reload();
  await waitForStablePage(page);
});

test("builds a quote, compares coverage, and prepares a provider message", async ({ page }) => {
  const firstAddButton = page
    .locator(`tr[data-product-id="${productIds[0]}"]`)
    .getByRole("button", { name: "Agregar 1 unidad a la lista de cotizacion" });
  const secondAddButton = page
    .locator(`tr[data-product-id="${productIds[1]}"]`)
    .getByRole("button", { name: "Agregar 1 unidad a la lista de cotizacion" });

  await expect(firstAddButton).toBeVisible();
  await expect(secondAddButton).toBeVisible();
  await firstAddButton.click();
  const drawer = page.getByRole("dialog", { name: "Lista de cotizacion" });
  await expect(drawer).toBeVisible();
  await expect(drawer.getByRole("button", { name: "Cerrar lista de cotizacion" })).toBeFocused();
  await drawer.getByRole("button", { name: "Cerrar lista de cotizacion" }).click();
  await expect(firstAddButton).toBeFocused();

  await secondAddButton.click();
  await expect(drawer).toBeVisible();
  await expect(drawer.getByRole("button", { name: "Cerrar lista de cotizacion" })).toBeFocused();
  await expect(drawer.locator(".quote-list-item")).toHaveCount(2);

  const quantityInputs = drawer.getByRole("spinbutton", { name: "Cantidad de unidades" });
  if ((await quantityInputs.count()) === 0) {
    await drawer.getByRole("button", { name: "Controles rapidos", exact: true }).click();
  }
  await expect(quantityInputs).toHaveCount(2);
  await quantityInputs.first().fill("11");
  await drawer.getByRole("button", { name: "Completar siguiente caja de 12 unidades" }).first().click();
  await expect(quantityInputs.first()).toHaveValue("12");

  await drawer.getByRole("button", { name: "Comparar proveedores" }).click();
  await expect(drawer.getByRole("group", { name: "Cobertura de proveedores" })).toBeVisible();
  await expect(drawer.getByText("Cubre toda la lista", { exact: true })).toBeVisible();

  await drawer.getByRole("button", { name: "Preparar consulta" }).click();
  await expect(drawer.getByRole("tabpanel", { name: "Enviar" })).toBeVisible();
  await expect(drawer.getByRole("textbox", { name: "Mensaje de consulta" })).not.toHaveValue("");
  await expect(drawer.getByRole("link", { name: "Abrir WhatsApp" })).toHaveAttribute("href", /^https:\/\/wa\.me\//);

  await drawer.getByRole("button", { name: "Cerrar lista de cotizacion" }).click();
  await expect(drawer).toBeHidden();
  await expect(secondAddButton).toBeFocused();
});
