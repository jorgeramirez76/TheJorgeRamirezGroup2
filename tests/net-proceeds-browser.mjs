import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { chromium, webkit } from "/Users/teddy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const ROOT = process.cwd();
const SCREENSHOTS = "/private/tmp/net-proceeds-browser-20260827";
const requestedEngine = (
  process.argv[2] || process.env.CALCULATOR_BROWSER_ENGINE || "chrome"
).toLowerCase();
if (!['chrome', 'webkit'].includes(requestedEngine)) {
  throw new Error(`Unsupported CALCULATOR_BROWSER_ENGINE: ${requestedEngine}`);
}
const hardTimeout = setTimeout(() => {
  process.stderr.write("net-proceeds browser checks exceeded the 120-second hard timeout\n");
  process.exit(2);
}, 120_000);
const routes = [
  {
    path: "/net-proceeds-calculator.html",
    canonical: "https://thejorgeramirezgroup.com/net-proceeds-calculator",
    language: "en",
    directionError: "Select whether the property-tax adjustment is due from or due to the seller.",
    possibleFee: "Possible NJ Graduated Percent Fee (not deducted; confirmation required)",
    confirmedFee: "Estimated NJ Graduated Percent Fee",
    notApplicableFee: "NJ Graduated Percent Fee (confirmed not deducted from seller proceeds)",
    unknownTotal: "Estimated Net (Excludes Unconfirmed Possible Fee)",
  },
  {
    path: "/es/net-proceeds-calculator.html",
    canonical: "https://thejorgeramirezgroup.com/es/net-proceeds-calculator",
    language: "es",
    directionError: "Selecciona si el ajuste de impuesto a la propiedad está a cargo o a favor del vendedor.",
    possibleFee: "Posible Graduated Percent Fee de NJ (no deducida; requiere confirmación)",
    confirmedFee: "Graduated Percent Fee de NJ estimada",
    notApplicableFee: "Graduated Percent Fee de NJ (confirmada sin deducción de los fondos del vendedor)",
    unknownTotal: "Neto Estimado (Excluye la Posible Tarifa No Confirmada)",
  },
];
const widths = [320, 390, 1440];
const MIME = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".jpg": "image/jpeg",
  ".js": "text/javascript; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
};

await mkdir(SCREENSHOTS, { recursive: true });
const browserType = requestedEngine === "webkit" ? webkit : chromium;
const launchOptions = requestedEngine === "chrome"
  ? { executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" }
  : {};
const browser = await browserType.launch({ headless: true, ...launchOptions });
const failures = [];
let screenshots = 0;
let interactions = 0;

function fail(label, message) {
  failures.push(`${label}: ${message}`);
}

function expectIncludes(label, text, expected) {
  if (!text.includes(expected)) fail(label, `missing ${JSON.stringify(expected)}`);
}

for (const width of widths) {
  const context = await browser.newContext({
    viewport: { width, height: 900 },
    reducedMotion: "reduce",
  });
  await context.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (url.hostname !== "local.test") {
      const contentType = url.hostname === "fonts.googleapis.com"
        ? "text/css; charset=utf-8"
        : "text/javascript; charset=utf-8";
      return route.fulfill({ status: 200, body: "", contentType });
    }
    let relative = decodeURIComponent(url.pathname).replace(/^\/+/, "");
    if (!path.extname(relative)) relative += ".html";
    const absolute = path.resolve(ROOT, relative);
    if (!absolute.startsWith(`${ROOT}${path.sep}`)) {
      return route.fulfill({ status: 403, body: "Forbidden" });
    }
    try {
      const body = await readFile(absolute);
      return route.fulfill({
        status: 200,
        body,
        contentType: MIME[path.extname(absolute).toLowerCase()] || "application/octet-stream",
      });
    } catch {
      return route.fulfill({ status: 404, body: "Not found" });
    }
  });

  for (const route of routes) {
    const page = await context.newPage();
    const runtimeErrors = [];
    page.on("pageerror", (error) => runtimeErrors.push(`pageerror: ${String(error)}`));
    page.on("console", (message) => {
      if (["error", "warning"].includes(message.type())) {
        runtimeErrors.push(`${message.type()}: ${message.text()}`);
      }
    });
    const label = `${route.language.toUpperCase()} @ ${width}px`;
    const response = await page.goto(`http://local.test${route.path}`, {
      waitUntil: "domcontentloaded",
      timeout: 20_000,
    });
    await page.waitForTimeout(100);
    if (!response?.ok()) fail(label, `HTTP ${response?.status()}`);

    await page.click(".calc-btn");
    interactions += 1;
    if (await page.locator("#results").isVisible()) fail(label, "blank form revealed results");
    const blankState = await page.evaluate(() => ({
      focused: document.activeElement?.id,
      message: document.querySelector("#salePrice").validationMessage,
    }));
    if (blankState.focused !== "salePrice" || !blankState.message) {
      fail(label, `blank validation focused=${blankState.focused}; message=${blankState.message}`);
    }

    await page.fill("#salePrice", "1000000.50");
    await page.fill("#brokerCompensation", "0");
    await page.fill("#propertyTaxAdjustment", "0.01");
    await page.click(".calc-btn");
    interactions += 1;
    if (await page.locator("#results").isVisible()) fail(label, "ambiguous tax direction revealed results");
    const directionState = await page.evaluate(() => ({
      focused: document.activeElement?.id,
      message: document.querySelector("#propertyTaxAdjustmentDirection").validationMessage,
    }));
    if (directionState.focused !== "propertyTaxAdjustmentDirection") {
      fail(label, `ambiguous direction focused ${directionState.focused}`);
    }
    if (directionState.message !== route.directionError) {
      fail(label, `direction error ${JSON.stringify(directionState.message)}`);
    }

    await page.selectOption("#propertyTaxAdjustmentDirection", "credit");
    await page.click(".calc-btn");
    interactions += 1;
    let resultText = await page.locator("#lineItems").innerText();
    expectIncludes(label, resultText, route.possibleFee);
    expectIncludes(label, resultText, route.unknownTotal);
    expectIncludes(label, resultText, "$10,000.01");
    expectIncludes(label, resultText, "$990,419.46");

    await page.selectOption("#graduatedPercentFeeApplicability", "applies");
    await page.click(".calc-btn");
    interactions += 1;
    resultText = await page.locator("#lineItems").innerText();
    expectIncludes(label, resultText, route.confirmedFee);
    expectIncludes(label, resultText, "-$10,000.01");
    expectIncludes(label, resultText, "$980,419.45");

    await page.selectOption("#graduatedPercentFeeApplicability", "not-applicable");
    await page.click(".calc-btn");
    interactions += 1;
    resultText = await page.locator("#lineItems").innerText();
    expectIncludes(label, resultText, route.notApplicableFee);
    expectIncludes(label, resultText, "$0.00");
    expectIncludes(label, resultText, "$990,419.46");

    await page.fill("#payoff", "-0.01");
    // The browser's native invalid-number bubble can keep the button moving
    // while actionability is checked. Force the click here so the calculator's
    // own fail-closed validation path is exercised deterministically.
    await page.click(".calc-btn", { force: true });
    interactions += 1;
    const negativeState = await page.evaluate(() => ({
      focused: document.activeElement?.id,
      message: document.querySelector("#payoff").validationMessage,
      visible: getComputedStyle(document.querySelector("#results")).display !== "none",
    }));
    if (negativeState.visible || negativeState.focused !== "payoff" || !negativeState.message) {
      fail(label, `negative input visible=${negativeState.visible}; focused=${negativeState.focused}; message=${negativeState.message}`);
    }
    await page.fill("#payoff", "");

    await page.selectOption("#brokerCompensationMethod", "flat");
    await page.fill("#brokerCompensation", "1234.56");
    await page.fill("#propertyTaxAdjustment", "");
    await page.selectOption("#graduatedPercentFeeApplicability", "applies");
    await page.click(".calc-btn");
    interactions += 1;
    resultText = await page.locator("#lineItems").innerText();
    expectIncludes(label, resultText, "-$1,234.56");
    expectIncludes(label, resultText, "-$9,581.05");
    expectIncludes(label, resultText, "-$10,000.01");
    expectIncludes(label, resultText, "$979,184.88");

    await page.fill("#salePrice", "99.99");
    await page.fill("#brokerCompensation", "0");
    await page.selectOption("#graduatedPercentFeeApplicability", "unknown");
    await page.click(".calc-btn");
    interactions += 1;
    resultText = await page.locator("#lineItems").innerText();
    expectIncludes(label, resultText, "$99.99");
    if (!/Transfer Fee[^\n]*\n\$0\.00|Transferencia Inmobiliaria[^\n]*\n\$0\.00/.test(resultText)) {
      fail(label, "below-$100 scenario did not show a $0.00 RTF");
    }

    if (width === 390) {
      const gpfCliffs = [
        ["1000000", null],
        ["1000000.01", "-$10,000.00"],
        ["2000000", "-$20,000.00"],
        ["2000000.01", "-$40,000.00"],
        ["2500000", "-$50,000.00"],
        ["2500000.01", "-$62,500.00"],
        ["3000000", "-$75,000.00"],
        ["3000000.01", "-$90,000.00"],
        ["3500000", "-$105,000.00"],
        ["3500000.01", "-$122,500.00"],
      ];
      await page.selectOption("#graduatedPercentFeeApplicability", "applies");
      for (const [price, expectedFee] of gpfCliffs) {
        await page.fill("#salePrice", price);
        await page.click(".calc-btn", { force: true });
        interactions += 1;
        const text = await page.locator("#lineItems").innerText();
        const hasConfirmedFee = text.includes(route.confirmedFee);
        if (!expectedFee && hasConfirmedFee) fail(label, `$${price} incorrectly showed a GPF`);
        if (expectedFee) {
          if (!hasConfirmedFee) fail(label, `$${price} omitted confirmed GPF`);
          expectIncludes(`${label} $${price}`, text, expectedFee);
        }
      }
    }

    await page.fill("#salePrice", "1000000.50");
    await page.fill("#brokerCompensation", "0");
    await page.fill("#propertyTaxAdjustment", "0.01");
    await page.selectOption("#propertyTaxAdjustmentDirection", "credit");
    await page.selectOption("#graduatedPercentFeeApplicability", "unknown");
    await page.click(".calc-btn");
    interactions += 1;

    const state = await page.evaluate(() => {
      const source = document.documentElement.innerHTML.toLowerCase();
      const describedByTargetsExist = [...document.querySelectorAll("[aria-describedby]")].every((element) =>
        element.getAttribute("aria-describedby").split(/\s+/).every((id) => document.getElementById(id)),
      );
      const controlsHaveLabels = [...document.querySelectorAll("input,select")].every(
        (element) => element.labels && element.labels.length > 0,
      );
      const checkedSelectors = [
        ".calc-wrapper", ".calc-card", ".results", ".line-item",
        ".input-group input", ".input-group select", ".calc-btn",
      ];
      const clipped = checkedSelectors.flatMap((selector) => [...document.querySelectorAll(selector)])
        .filter((element) => {
          const rect = element.getBoundingClientRect();
          return rect.width > 0 && (rect.left < -1 || rect.right > document.documentElement.clientWidth + 1);
        })
        .map((element) => `${element.tagName.toLowerCase()}.${element.className || ""}#${element.id || ""}`);
      const schemas = [...document.querySelectorAll('script[type="application/ld+json"]')];
      const schemaErrors = [];
      for (const script of schemas) {
        try { JSON.parse(script.textContent); } catch (error) { schemaErrors.push(String(error)); }
      }
      const h1 = document.querySelector("h1");
      return {
        bodyFont: getComputedStyle(document.body).fontFamily,
        brokenImages: [...document.images]
          .filter((image) => !image.complete || image.naturalWidth === 0)
          .map((image) => image.getAttribute("src")),
        canonical: document.querySelector('link[rel="canonical"]')?.href || "",
        clipped,
        controlsHaveLabels,
        describedByTargetsExist,
        duplicateIds: [...document.querySelectorAll("[id]")]
          .map((element) => element.id)
          .filter((id, index, ids) => ids.indexOf(id) !== index),
        h1Count: document.querySelectorAll("h1").length,
        h1Font: h1 ? getComputedStyle(h1).fontFamily : "",
        language: document.documentElement.lang,
        mainCount: document.querySelectorAll("main#main").length,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        resultsLive: document.querySelector("#results")?.getAttribute("aria-live"),
        schemaCount: schemas.length,
        schemaErrors,
        source,
      };
    });

    if (state.canonical !== route.canonical) fail(label, `canonical ${state.canonical}`);
    if (state.language !== route.language) fail(label, `language ${state.language}`);
    if (state.mainCount !== 1 || state.h1Count !== 1) fail(label, `main=${state.mainCount}; h1=${state.h1Count}`);
    if (state.overflow > 1 || state.clipped.length) {
      fail(label, `overflow=${state.overflow}px; clipped=${state.clipped.join(", ")}`);
    }
    if (!state.controlsHaveLabels || !state.describedByTargetsExist || state.resultsLive !== "polite") {
      fail(label, `a11y labels=${state.controlsHaveLabels}; descriptions=${state.describedByTargetsExist}; live=${state.resultsLive}`);
    }
    if (state.duplicateIds.length) fail(label, `duplicate IDs ${state.duplicateIds.join(", ")}`);
    if (state.brokenImages.length) fail(label, `broken images ${state.brokenImages.join(", ")}`);
    if (!state.schemaCount || state.schemaErrors.length) {
      fail(label, `schema count=${state.schemaCount}; ${state.schemaErrors.join(" | ")}`);
    }
    if (!/playfair/i.test(state.h1Font) || !/inter/i.test(state.bodyFont)) {
      fail(label, `fonts h1=${state.h1Font}; body=${state.bodyFont}`);
    }
    for (const color of ["#1a1a1a", "#c41230", "#8b0d22", "#b8962e", "#fafaf8"]) {
      if (!state.source.includes(color)) fail(label, `missing palette color ${color}`);
    }
    if (runtimeErrors.length) fail(label, runtimeErrors.join(" | "));

    const slug = route.language === "es" ? "es-net-proceeds" : "en-net-proceeds";
    await page.screenshot({ path: `${SCREENSHOTS}/${requestedEngine}-${slug}-${width}.png`, fullPage: true });
    screenshots += 1;
    await page.close();
  }
  await context.close();
}

await browser.close();
clearTimeout(hardTimeout);
if (failures.length) {
  process.stderr.write(`${failures.join("\n")}\n`);
  process.exit(1);
}
process.stdout.write(
  `net-proceeds browser checks passed (${requestedEngine}): ${routes.length} routes x ${widths.length} widths; ${interactions} interactions; ${screenshots} screenshots\n`,
);
