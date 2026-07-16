import { defineConfig } from "@playwright/test";

const viewportProjects = [
  ["desktop-4k", 3840, 2160],
  ["desktop-2k", 2560, 1440],
  ["desktop-1080", 1920, 1080],
  ["laptop-1366", 1366, 768],
  ["mobile-412", 412, 915],
  ["mobile-390", 390, 844],
  ["mobile-360", 360, 800],
  ["mobile-landscape", 844, 390],
];

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: !process.env.CI,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  timeout: 45_000,
  expect: {
    timeout: 8_000,
    toHaveScreenshot: {
      animations: "disabled",
      caret: "hide",
      maxDiffPixelRatio: 0.008,
    },
  },
  outputDir: "test-results",
  reporter: [
    ["line"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
  ],
  snapshotPathTemplate: "{testDir}/__screenshots__/{platform}/{projectName}/{arg}{ext}",
  use: {
    baseURL: "http://127.0.0.1:4173/CentraldeFilamentos/",
    channel: "chrome",
    headless: true,
    locale: "es-AR",
    timezoneId: "America/Argentina/Buenos_Aires",
    colorScheme: "light",
    reducedMotion: "reduce",
    trace: process.env.CI ? "on-first-retry" : "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
  },
  projects: viewportProjects.map(([name, width, height]) => ({
    name,
    use: {
      viewport: { width, height },
      deviceScaleFactor: 1,
      isMobile: name.startsWith("mobile-"),
      hasTouch: name.startsWith("mobile-"),
    },
  })),
  webServer: {
    command: "npm run build && npm run preview -- --host 127.0.0.1 --port 4173",
    url: "http://127.0.0.1:4173/CentraldeFilamentos/",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    stdout: "pipe",
    stderr: "pipe",
  },
});
