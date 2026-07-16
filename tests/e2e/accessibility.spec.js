import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { waitForStablePage } from "./helpers/audit.js";

const auditedProjects = new Set(["desktop-1080", "mobile-390"]);
const routes = [
  ["summary", "./"],
  ["color picker", "./color-picker.html"],
  ["vendor statistics", "./estadisticas.html"],
];

async function scanAndAttach(page, label) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  await test.info().attach(`${label}-axe.json`, {
    body: Buffer.from(JSON.stringify(results, null, 2)),
    contentType: "application/json",
  });
  const blocking = results.violations.filter((violation) => ["critical", "serious"].includes(violation.impact));
  expect(blocking, `${label}: critical or serious axe violations`).toEqual([]);
}

test.beforeEach(async ({}, testInfo) => {
  test.skip(!auditedProjects.has(testInfo.project.name), "Axe runs on representative desktop and mobile viewports.");
});

for (const [name, path] of routes) {
  test(`${name} has no serious or critical axe violations`, async ({ page }) => {
    await page.goto(path);
    await waitForStablePage(page);
    await scanAndAttach(page, name.replaceAll(" ", "-"));
  });
}

test("color picker dynamic validation and result states remain accessible", async ({ page }) => {
  await page.goto("./color-picker.html");
  await waitForStablePage(page);

  const hexInput = page.getByLabel("HEX de referencia");
  await hexInput.fill("no-es-un-hex");
  await page.getByRole("button", { name: "Buscar similares" }).click();
  await expect(hexInput).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByRole("alert")).toBeVisible();
  await scanAndAttach(page, "color-picker-invalid-hex");

  await hexInput.fill("#00AEEF");
  await page.getByRole("button", { name: "Buscar similares" }).click();
  await expect(page.locator(".color-picker-similar-results")).toBeVisible();
  await scanAndAttach(page, "color-picker-similar-results");
});
