import { chromium } from "/Users/teddy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const browser = await chromium.launch({
  headless: true,
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});

const routes = [
  "/rent-vs-buy-nj.html",
  "/es/rent-vs-buy-nj.html",
  "/blog/nj-commute-cost-nyc-2026.html",
  "/blog/how-much-money-to-buy-a-house-nj.html",
  "/blog/nj-first-time-home-buyer-programs-2026.html",
];
const widths = [320, 390, 1440];
const failures = [];

for (const width of widths) {
  const context = await browser.newContext({ viewport: { width, height: 900 } });
  for (const route of routes) {
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(String(error)));
    const response = await page.goto(`http://127.0.0.1:8765${route}`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(150);
    if (!response || !response.ok()) failures.push(`${route} ${width}: HTTP ${response?.status()}`);
    const result = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      main: document.querySelectorAll("main#main").length,
      h1: document.querySelectorAll("h1").length,
      brokenImages: [...document.images]
        .filter((item) => !item.complete || item.naturalWidth === 0)
        .map((item) => item.src),
    }));
    if (result.overflow) failures.push(`${route} ${width}: horizontal overflow`);
    if (result.main !== 1 || result.h1 !== 1) failures.push(`${route} ${width}: main=${result.main} h1=${result.h1}`);
    if (result.brokenImages.length) failures.push(`${route} ${width}: broken images ${result.brokenImages.join(",")}`);
    if (errors.length) failures.push(`${route} ${width}: ${errors.join(" | ")}`);
    await page.close();
  }
  await context.close();
}

const formPage = await browser.newPage({ viewport: { width: 390, height: 900 } });
const rentValues = {
  purchasePrice: "400000", downPayment: "80000", mortgageRate: "6",
  mortgageTerm: "30", plannedYears: "5", monthlyRent: "2500",
  annualRentChange: "0", annualPropertyTax: "10000", annualHomeInsurance: "1800",
  monthlyHoa: "0", annualMaintenance: "4000", monthlyMortgageInsurance: "0",
  buyerClosingCosts: "12000", annualAppreciation: "0", sellerExitCosts: "24000",
  monthlyRentersInsurance: "240", renterNonrefundableCosts: "0",
  alternativeInvestment: "80000", annualInvestmentReturn: "0",
};
for (const route of ["/rent-vs-buy-nj.html", "/es/rent-vs-buy-nj.html"]) {
  await formPage.goto(`http://127.0.0.1:8765${route}`, { waitUntil: "domcontentloaded" });
  await formPage.click("button[type=submit]");
  if (await formPage.locator("#results").isVisible()) failures.push(`${route}: blank form revealed results`);
  for (const [id, value] of Object.entries(rentValues)) await formPage.fill(`#${id}`, value);
  await formPage.click("button[type=submit]");
  if (!(await formPage.locator("#results").isVisible())) failures.push(`${route}: completed scenario did not reveal results`);
  if (!(await formPage.locator("#worksheetStatus").innerText())) failures.push(`${route}: status was not announced`);
}

await formPage.goto("http://127.0.0.1:8765/blog/nj-commute-cost-nyc-2026.html", { waitUntil: "domcontentloaded" });
for (const id of [
  "transitDays", "transitFarePerDay", "stationParkingPerDay", "destinationTransitPerDay",
  "otherTransitMonthly", "drivingDays", "tollsPerDay", "drivingParkingPerDay", "fuelPerDay",
  "otherDrivingMonthly", "annualFees", "transitRoundTripMinutes", "drivingRoundTripMinutes",
]) await formPage.fill(`#${id}`, "0");
await formPage.click("button[type=submit]");
if (!(await formPage.locator("#commuteResults").isVisible())) failures.push("commute form did not reveal results");
await formPage.close();

await browser.close();
if (failures.length) {
  process.stderr.write(`${failures.join("\n")}\n`);
  process.exit(1);
}
process.stdout.write(`decision-finance browser checks passed: ${routes.length} routes x ${widths.length} widths plus form interactions\n`);
