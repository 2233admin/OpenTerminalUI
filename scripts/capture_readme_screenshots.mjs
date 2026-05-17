// Captures README screenshots of every major feature against the running app.
// Logs in as a real account so portfolio/watchlist pages show real data.
//
// Run from the frontend/ directory (so "@playwright/test" resolves):
//   cd frontend && node ../scripts/capture_readme_screenshots.mjs
//
// Requires the app running at http://localhost:8000 (docker compose up).
import path from "node:path";
import fs from "node:fs/promises";
import { createRequire } from "node:module";

// Resolve @playwright/test from the current working directory (run from frontend/).
const require = createRequire(`${process.cwd()}/`);
const { chromium } = require("@playwright/test");

const BASE = process.env.SHOT_BASE_URL || "http://localhost:8000";
const EMAIL = process.env.SHOT_EMAIL || "karanth.hithesh@gmail.com";
const PASSWORD = process.env.SHOT_PASSWORD || "Flyvi12#";
const OUT_DIR = path.resolve(process.cwd(), "..", "assets", "screenshots");

// One ticker the account actually holds — keeps Security Hub relevant.
const TICKER = "ICICIBANK";

const PAGES = [
  { name: "home", url: "/", settle: 8000 },
  { name: "chart-workstation", url: "/equity/chart-workstation", settle: 11000 },
  { name: "stock-detail", url: `/equity/security?ticker=${TICKER}`, settle: 9000 },
  { name: "screener", url: "/equity/screener", settle: 9000 },
  { name: "factor-dashboard", url: "/equity/factors", settle: 9000 },
  { name: "portfolio", url: "/equity/portfolio", settle: 11000 },
  { name: "portfolio-lab", url: "/equity/portfolio/lab", settle: 9000 },
  { name: "backtesting", url: "/backtesting", settle: 9000 },
  { name: "model-lab", url: "/backtesting/model-lab", settle: 9000 },
  { name: "risk-dashboard", url: "/equity/risk", settle: 9000 },
  { name: "cockpit", url: "/equity/cockpit", settle: 9000 },
  { name: "news-sentiment", url: "/equity/news", settle: 9000 },
  { name: "intelligence-timeline", url: "/equity/intelligence-timeline", settle: 8000 },
  { name: "fno-option-chain", url: "/fno", settle: 10000 },
  { name: "watchlist", url: "/equity/watchlist", settle: 8000 },
  { name: "commodities", url: "/equity/commodities", settle: 8000 },
];

async function main() {
  await fs.mkdir(OUT_DIR, { recursive: true });

  // 1. Real login -> tokens.
  const resp = await fetch(`${BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: EMAIL, password: PASSWORD }),
  });
  if (!resp.ok) throw new Error(`Login failed: ${resp.status} ${await resp.text()}`);
  const { access_token, refresh_token } = await resp.json();
  if (!access_token) throw new Error("No access_token in login response");
  console.log("Logged in as", EMAIL);

  // 2. Browser — block the service worker so nothing is served stale.
  const browser = await chromium.launch({ args: ["--disable-gpu"] });
  const context = await browser.newContext({
    viewport: { width: 1600, height: 1000 },
    deviceScaleFactor: 2,
    serviceWorkers: "block",
  });
  await context.addInitScript(
    ([at, rt]) => {
      localStorage.setItem("ot-access-token", at);
      localStorage.setItem("ot-refresh-token", rt);
    },
    [access_token, refresh_token],
  );
  const page = await context.newPage();

  // 3. Capture each page.
  for (const target of PAGES) {
    try {
      await page.goto(`${BASE}${target.url}`, { waitUntil: "domcontentloaded", timeout: 45000 });
      await page.waitForTimeout(target.settle ?? 8000);
      const out = path.join(OUT_DIR, `${target.name}.png`);
      await page.screenshot({ path: out, fullPage: false });
      console.log("captured", target.name);
    } catch (err) {
      console.error("FAILED", target.name, "-", err.message);
    }
  }

  await context.close();
  await browser.close();
  console.log("Done. Screenshots in", OUT_DIR);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
