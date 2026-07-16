import { expect, test } from "@playwright/test";

test("production preview renders the primary application region", async ({ page }) => {
  const response = await page.goto("./");

  expect(response?.ok()).toBe(true);
  await expect(page.locator("main")).toBeVisible();
});
