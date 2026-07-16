import { expect, test } from "@playwright/test";

import { waitForStablePage } from "./helpers/audit.js";

const auditedProjects = new Set(["desktop-1080", "mobile-390"]);

test.beforeEach(async ({ page }, testInfo) => {
  test.skip(!auditedProjects.has(testInfo.project.name), "Deep Color Picker flow runs on representative desktop and mobile viewports.");
  await page.goto("./color-picker.html");
  await waitForStablePage(page);
});

test("exposes the active page and associates dynamic search feedback", async ({ page }) => {
  await expect(page.getByRole("link", { name: "Color Picker" })).toHaveAttribute("aria-current", "page");

  const hexInput = page.getByLabel("HEX de referencia");
  await hexInput.fill("mal");
  await page.getByRole("button", { name: "Buscar similares" }).click();
  const error = page.getByRole("alert");
  await expect(error).toHaveAttribute("id", /.+/);
  await expect(hexInput).toHaveAttribute("aria-describedby", await error.getAttribute("id"));

  await hexInput.fill("#00AEEF");
  await page.getByRole("button", { name: "Buscar similares" }).click();
  await expect(page.locator(".color-picker-similar-results")).toHaveAttribute("aria-live", "polite");
});

test("switches every color view and preserves a single active state", async ({ page }) => {
  const viewNames = ["Continuo", "Familias", "Mapa 2D"];
  for (const name of viewNames) {
    const viewButton = page.getByRole("button", { name, exact: true });
    await viewButton.click();
    await expect(viewButton).toHaveAttribute("aria-pressed", "true");
    const pressedStates = await Promise.all(viewNames.map((label) =>
      page.getByRole("button", { name: label, exact: true }).getAttribute("aria-pressed")
    ));
    expect(pressedStates.filter((state) => state === "true")).toHaveLength(1);
  }
});

test("validates HEX, exposes similar colors, and retains focus after choosing one", async ({ page }) => {
  const hexInput = page.getByLabel("HEX de referencia");
  await hexInput.fill("mal");
  await page.getByRole("button", { name: "Buscar similares" }).click();
  await expect(hexInput).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByRole("alert")).toBeVisible();

  await hexInput.fill("#00AEEF");
  await page.getByRole("button", { name: "Buscar similares" }).click();
  const results = page.locator(".color-picker-similar-results");
  await expect(results).toBeVisible();
  await expect(results.locator(".color-picker-similar-card")).toHaveCount(3);

  const firstResult = results.locator(".color-picker-similar-swatch").first();
  await firstResult.focus();
  await firstResult.press("Enter");
  await expect(page.locator(".color-picker-compare-card")).toHaveCount(1);
  await expect(page.locator(".color-picker-compare-card").getByRole("button", { name: /Quitar .+ del comparador/ })).toBeFocused();
});

test("skip link transfers keyboard focus to the main content", async ({ page }) => {
  await page.keyboard.press("Home");
  await page.keyboard.press("Tab");
  const skipLink = page.locator("a.skip-link");
  await expect(skipLink).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();
});
