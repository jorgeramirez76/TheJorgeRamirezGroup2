import { readFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { chromium } from "/Users/teddy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const ROOT = process.cwd();
const SCREENSHOTS = "/private/tmp/verified-service-browser-20260827";
const routes = [
  "/buy-a-home.html",
  "/es/buy-a-home.html",
  "/investment-property-nj.html",
  "/es/investment-property-nj.html",
  "/nj-home-seller-guide.html",
  "/blog/why-new-yorkers-moving-to-nj-2026.html",
  "/es/blog/moving-from-nyc-to-nj-guide.html",
];
const isolatedServiceHeroRoutes = new Set([
  "/buy-a-home.html",
  "/es/buy-a-home.html",
  "/investment-property-nj.html",
  "/es/investment-property-nj.html",
]);
const widths = [320, 390, 768, 1440];
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
const browser = await chromium.launch({
  headless: true,
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});
const failures = [];
let parsedSchemas = 0;

for (const width of widths) {
  const context = await browser.newContext({ viewport: { width, height: 900 } });
  await context.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (url.hostname !== "local.test") return route.abort();
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
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(String(error)));
    const response = await page.goto(`http://local.test${route}`, {
      waitUntil: "domcontentloaded",
      timeout: 20_000,
    });
    await page.evaluate(async () => {
      const images = [...document.images];
      for (const image of images) {
        image.loading = "eager";
        image.scrollIntoView({ block: "center" });
        await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        try {
          await image.decode();
        } catch {
          // The broken-image assertion below reports the exact source.
        }
      }
      window.scrollTo(0, 0);
    });
    await page.waitForTimeout(100);
    const result = await page.evaluate(() => {
      const scripts = [...document.querySelectorAll('script[type="application/ld+json"]')];
      const schemaErrors = [];
      for (const script of scripts) {
        try {
          JSON.parse(script.textContent);
        } catch (error) {
          schemaErrors.push(String(error));
        }
      }
      const h1 = document.querySelector("h1");
      const navBrand = document.querySelector(".service-nav .brand");
      const navBrandRect = navBrand?.getBoundingClientRect();
      const navBrandStyle = navBrand ? getComputedStyle(navBrand) : null;
      const serviceHero = document.querySelector(".service-hero");
      const serviceHeroRect = serviceHero?.getBoundingClientRect();
      const serviceHeroStyle = serviceHero ? getComputedStyle(serviceHero) : null;
      return {
        brokenImages: [...document.images]
          .filter((image) => !image.complete || image.naturalWidth === 0)
          .map((image) => image.getAttribute("src")),
        canonical: document.querySelector('link[rel="canonical"]')?.href || "",
        h1Count: document.querySelectorAll("h1").length,
        h1Font: h1 ? getComputedStyle(h1).fontFamily : "",
        bodyFont: getComputedStyle(document.body).fontFamily,
        mainCount: document.querySelectorAll("main#main").length,
        navBrand: navBrandRect
          ? {
              bottom: navBrandRect.bottom,
              display: navBrandStyle.display,
              height: navBrandRect.height,
              opacity: navBrandStyle.opacity,
              top: navBrandRect.top,
              visibility: navBrandStyle.visibility,
              width: navBrandRect.width,
            }
          : null,
        overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
        paletteSource: document.documentElement.innerHTML.toLowerCase(),
        schemaCount: scripts.length,
        schemaErrors,
        legacyServiceHeroCount: document.querySelectorAll(".service-shell > .hero").length,
        serviceHero: serviceHeroRect
          ? {
              childOverflow: [...serviceHero.children].some((child) => {
                const rect = child.getBoundingClientRect();
                return (
                  rect.left < serviceHeroRect.left - 1 ||
                  rect.right > serviceHeroRect.right + 1 ||
                  rect.top < serviceHeroRect.top - 1 ||
                  rect.bottom > serviceHeroRect.bottom + 1
                );
              }),
              display: serviceHeroStyle.display,
              height: serviceHeroRect.height,
              h1FontSize: h1 ? Number.parseFloat(getComputedStyle(h1).fontSize) : 0,
              minHeight: serviceHeroStyle.minHeight,
            }
          : null,
      };
    });

    if (!response?.ok()) failures.push(`${route} @ ${width}: HTTP ${response?.status()}`);
    if (result.overflow) failures.push(`${route} @ ${width}: horizontal overflow`);
    if (result.mainCount !== 1 || result.h1Count !== 1) {
      failures.push(`${route} @ ${width}: main=${result.mainCount}; h1=${result.h1Count}`);
    }
    if (!result.canonical.startsWith("https://thejorgeramirezgroup.com/")) {
      failures.push(`${route} @ ${width}: invalid canonical ${result.canonical}`);
    }
    if (isolatedServiceHeroRoutes.has(route)) {
      if (
        !result.navBrand ||
        result.navBrand.width <= 0 ||
        result.navBrand.height <= 0 ||
        result.navBrand.top < 0 ||
        result.navBrand.display === "none" ||
        result.navBrand.visibility !== "visible" ||
        result.navBrand.opacity === "0"
      ) {
        failures.push(`${route} @ ${width}: hidden/cropped nav brand ${JSON.stringify(result.navBrand)}`);
      }
    }
    if (result.brokenImages.length) {
      failures.push(`${route} @ ${width}: broken images ${result.brokenImages.join(", ")}`);
    }
    if (!result.schemaCount || result.schemaErrors.length) {
      failures.push(`${route} @ ${width}: schema count=${result.schemaCount}; ${result.schemaErrors.join(" | ")}`);
    }
    if (!/playfair/i.test(result.h1Font) || !/inter/i.test(result.bodyFont)) {
      failures.push(`${route} @ ${width}: fonts h1=${result.h1Font}; body=${result.bodyFont}`);
    }
    if (isolatedServiceHeroRoutes.has(route)) {
      if (!result.serviceHero || result.legacyServiceHeroCount) {
        failures.push(
          `${route} @ ${width}: isolated service hero missing or legacy .hero remains`,
        );
      } else if (
        result.serviceHero.display !== "block" ||
        result.serviceHero.minHeight !== "0px" ||
        result.serviceHero.h1FontSize > 64 ||
        result.serviceHero.childOverflow
      ) {
        failures.push(`${route} @ ${width}: invalid service hero ${JSON.stringify(result.serviceHero)}`);
      }
    }
    for (const color of ["#1a1a1a", "#c41230", "#b8962e", "#fafaf8"]) {
      if (!result.paletteSource.includes(color)) failures.push(`${route} @ ${width}: missing ${color}`);
    }
    if (pageErrors.length) failures.push(`${route} @ ${width}: ${pageErrors.join(" | ")}`);
    parsedSchemas += result.schemaCount;

    if (width === 390) {
      const slug = route.replace(/^\//, "").replaceAll("/", "-").replace(/\.html$/, "");
      await page.screenshot({ path: `${SCREENSHOTS}/${slug}-390.png`, fullPage: true });
    }
    await page.close();
  }
  await context.close();
}

await browser.close();
if (failures.length) {
  process.stderr.write(`${failures.join("\n")}\n`);
  process.exit(1);
}
process.stdout.write(
  `verified service browser checks passed: ${routes.length} routes x ${widths.length} widths; ${parsedSchemas} schema blocks parsed\n`,
);
