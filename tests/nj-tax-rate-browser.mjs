import { chromium, webkit } from "/Users/teddy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const route = "/blog/nj-property-tax-rate-vs-what-you-actually-pay.html";
const widths = [320, 360, 390, 430, 1440];
const engines = [
  ["Chrome", chromium, { executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" }],
  ["WebKit", webkit, {}],
];
const failures = [];

for (const [name, engine, launchOptions] of engines) {
  const browser = await engine.launch({ headless: true, ...launchOptions });
  for (const width of widths) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(String(error)));
    const response = await page.goto(`http://127.0.0.1:8765${route}`, {
      waitUntil: "domcontentloaded",
    });
    await page.waitForTimeout(100);
    const result = await page.evaluate(() => {
      const main = document.querySelector("main#main");
      const tableRegion = document.querySelector('[role="region"][aria-label]');
      const hero = document.querySelector(".hero");
      const cta = document.querySelector(".cta");
      const headings = [...document.querySelectorAll("h1,h2,h3")].map((node) => Number(node.tagName[1]));
      const skipped = headings.some((level, index) => index > 0 && level > headings[index - 1] + 1);
      const navTargets = [...document.querySelectorAll(".nav-links a")].map((node) => {
        const rect = node.getBoundingClientRect();
        return { text: node.textContent.trim(), width: rect.width, height: rect.height };
      });
      return {
        canonical: document.querySelector('link[rel="canonical"]')?.href,
        robots: document.querySelector('meta[name="robots"]')?.content,
        mainCount: document.querySelectorAll("main#main").length,
        h1Count: document.querySelectorAll("h1").length,
        mainFocusable: main?.getAttribute("tabindex"),
        tableLabel: tableRegion?.getAttribute("aria-label"),
        tableFocusable: tableRegion?.getAttribute("tabindex"),
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        brokenImages: [...document.images]
          .filter((image) => !image.complete || image.naturalWidth === 0)
          .map((image) => image.currentSrc || image.src),
        skipped,
        bodyColor: getComputedStyle(document.body).backgroundColor,
        heroColor: hero ? getComputedStyle(hero).backgroundColor : "",
        ctaColor: cta ? getComputedStyle(cta).backgroundColor : "",
        navTargets,
      };
    });
    await page.focus(".skip-link");
    const skipState = await page.locator(".skip-link").evaluate((node) => {
      const rect = node.getBoundingClientRect();
      return {
        visible: rect.left >= 0 && rect.width > 0 && rect.height > 0,
        left: rect.left,
        top: rect.top,
        width: rect.width,
        height: rect.height,
        cssLeft: getComputedStyle(node).left,
        active: document.activeElement === node,
      };
    });

    const label = `${name} ${width}px`;
    if (!response || !response.ok()) failures.push(`${label}: HTTP ${response?.status()}`);
    if (result.canonical !== "https://thejorgeramirezgroup.com/blog/nj-property-tax-rate-vs-what-you-actually-pay") failures.push(`${label}: canonical mismatch`);
    if (!result.robots?.startsWith("index, follow")) failures.push(`${label}: robots mismatch`);
    if (result.mainCount !== 1 || result.h1Count !== 1 || result.mainFocusable !== "-1") failures.push(`${label}: landmark/H1 mismatch`);
    if (!result.tableLabel || result.tableFocusable !== "0") failures.push(`${label}: table-region accessibility mismatch`);
    if (result.overflow > 0.5) failures.push(`${label}: horizontal overflow ${result.overflow}px`);
    if (result.brokenImages.length) failures.push(`${label}: broken images ${result.brokenImages.join(", ")}`);
    if (result.skipped) failures.push(`${label}: skipped heading level`);
    if (!skipState.visible) failures.push(`${label}: skip link not visible on focus ${JSON.stringify(skipState)}`);
    if (result.bodyColor !== "rgb(250, 250, 248)") failures.push(`${label}: body palette ${result.bodyColor}`);
    if (result.heroColor !== "rgb(26, 26, 26)") failures.push(`${label}: hero palette ${result.heroColor}`);
    if (result.ctaColor !== "rgb(196, 18, 48)") failures.push(`${label}: CTA palette ${result.ctaColor}`);
    if (result.navTargets.some((target) => target.height < 43.5)) failures.push(`${label}: undersized nav target`);
    if (pageErrors.length) failures.push(`${label}: ${pageErrors.join(" | ")}`);
    await page.close();
  }
  await browser.close();
}

if (failures.length) {
  process.stderr.write(`${failures.join("\n")}\n`);
  process.exit(1);
}
process.stdout.write(`tax-rate browser checks passed: ${engines.length} engines x ${widths.length} widths\n`);
