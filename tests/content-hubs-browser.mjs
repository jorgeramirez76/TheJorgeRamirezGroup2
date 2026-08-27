import { readFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { chromium, webkit } from "/Users/teddy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const ROOT = process.cwd();
const SCREENSHOTS = "/private/tmp/content-hubs-browser-20260827";
const hardTimeout = setTimeout(() => {
  process.stderr.write("content-hub browser checks exceeded the 120-second hard timeout\n");
  process.exit(2);
}, 120_000);
const routes = [
  ["/blog/index.html", "https://thejorgeramirezgroup.com/blog", "en", false],
  ["/es/blog/index.html", "https://thejorgeramirezgroup.com/es/blog", "es", false],
  ["/counties/index.html", "https://thejorgeramirezgroup.com/counties", "en", false],
  ["/thank-you.html", "https://thejorgeramirezgroup.com/thank-you", "en", true],
  ["/es/thank-you.html", "https://thejorgeramirezgroup.com/es/thank-you", "es", true],
];
const widths = [320, 390, 1440];
const engines = [
  ["Chrome", chromium, { executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" }],
  ["WebKit", webkit, {}],
];
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
const failures = [];
let schemaBlocks = 0;

for (const [engineName, engine, launchOptions] of engines) {
  const browser = await engine.launch({ headless: true, ...launchOptions });
  for (const width of widths) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    await context.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      if (url.hostname !== "local.test") {
        const contentType = url.hostname === "fonts.googleapis.com"
          ? "text/css; charset=utf-8"
          : "text/javascript; charset=utf-8";
        return route.fulfill({ status: 200, body: "", contentType });
      }
      const relative = decodeURIComponent(url.pathname).replace(/^\/+/, "");
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

    for (const [route, canonical, language, noindex] of routes) {
      const page = await context.newPage();
      const runtimeErrors = [];
      page.on("pageerror", (error) => runtimeErrors.push(String(error)));
      page.on("console", (message) => {
        if (["error", "warning"].includes(message.type())) {
          runtimeErrors.push(`${message.type()}: ${message.text()}`);
        }
      });
      const response = await page.goto(`http://local.test${route}`, {
        waitUntil: "domcontentloaded",
        timeout: 20_000,
      });
      await page.waitForTimeout(150);
      await page.evaluate(async () => {
        const images = [...document.images];
        for (const image of images) {
          image.loading = "eager";
          image.scrollIntoView({ block: "center", inline: "nearest" });
        }
        await Promise.all(images.map(async (image) => {
          if (!image.complete) {
            await new Promise((resolve) => {
              const finish = () => resolve();
              image.addEventListener("load", finish, { once: true });
              image.addEventListener("error", finish, { once: true });
              setTimeout(finish, 5_000);
            });
          }
          if (image.complete && image.naturalWidth && typeof image.decode === "function") {
            try {
              await image.decode();
            } catch {
              // The naturalWidth assertion below remains the source of truth.
            }
          }
        }));
        window.scrollTo(0, 0);
      });
      const result = await page.evaluate(() => {
        const schemas = [...document.querySelectorAll('script[type="application/ld+json"]')];
        const schemaErrors = [];
        for (const script of schemas) {
          try {
            JSON.parse(script.textContent);
          } catch (error) {
            schemaErrors.push(String(error));
          }
        }
        const headings = [...document.querySelectorAll("h1,h2,h3")].map((node) => Number(node.tagName[1]));
        const skippedHeading = headings.some(
          (level, index) => index > 0 && level > headings[index - 1] + 1,
        );
        const h1 = document.querySelector("h1");
        const directoryLinks = [...document.querySelectorAll("#blog-directory a")];
        const countyLink = document.querySelector('.county-index-page main h2 a');
        const comparisonLink = directoryLinks[0] || countyLink;
        const source = document.documentElement.innerHTML.toLowerCase();
        return {
          bodyBackground: getComputedStyle(document.body).backgroundColor,
          bodyFont: getComputedStyle(document.body).fontFamily,
          brokenImages: [...document.images]
            .filter((image) => !image.complete || image.naturalWidth === 0)
            .map((image) => image.getAttribute("src")),
          canonical: document.querySelector('link[rel="canonical"]')?.href || "",
          comparisonLinkColor: comparisonLink ? getComputedStyle(comparisonLink).color : "",
          directoryLinkCount: directoryLinks.length,
          duplicateIds: [...document.querySelectorAll("[id]")]
            .map((node) => node.id)
            .filter((id, index, all) => all.indexOf(id) !== index),
          h1Count: document.querySelectorAll("h1").length,
          h1Font: h1 ? getComputedStyle(h1).fontFamily : "",
          language: document.documentElement.lang,
          mainCount: document.querySelectorAll("main#main").length,
          overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          robots: document.querySelector('meta[name="robots"]')?.content || "",
          schemaCount: schemas.length,
          schemaErrors,
          skippedHeading,
          source,
        };
      });

      const label = `${engineName} ${route} @ ${width}px`;
      if (!response?.ok()) failures.push(`${label}: HTTP ${response?.status()}`);
      if (result.canonical !== canonical) failures.push(`${label}: canonical ${result.canonical}`);
      if (result.language !== language) failures.push(`${label}: language ${result.language}`);
      if (noindex !== result.robots.toLowerCase().startsWith("noindex")) {
        failures.push(`${label}: robots ${result.robots}`);
      }
      if (result.mainCount !== 1 || result.h1Count !== 1) {
        failures.push(`${label}: main=${result.mainCount}; h1=${result.h1Count}`);
      }
      if (result.overflow > 1) failures.push(`${label}: horizontal overflow ${result.overflow}px`);
      if (result.brokenImages.length) {
        failures.push(`${label}: broken images ${result.brokenImages.join(", ")}`);
      }
      if (result.schemaErrors.length || !result.schemaCount) {
        failures.push(`${label}: schema count=${result.schemaCount}; ${result.schemaErrors.join(" | ")}`);
      }
      if (result.skippedHeading) failures.push(`${label}: skipped heading level`);
      if (result.duplicateIds.length) failures.push(`${label}: duplicate IDs ${result.duplicateIds.join(", ")}`);
      if (!/playfair/i.test(result.h1Font) || !/inter/i.test(result.bodyFont)) {
        failures.push(`${label}: fonts h1=${result.h1Font}; body=${result.bodyFont}`);
      }
      if (result.bodyBackground !== "rgb(250, 250, 248)") {
        failures.push(`${label}: body background ${result.bodyBackground}`);
      }
      for (const color of ["#1a1a1a", "#c41230", "#8b0d22", "#b8962e", "#fafaf8"]) {
        if (!result.source.includes(color)) failures.push(`${label}: missing palette color ${color}`);
      }
      if (result.comparisonLinkColor && result.comparisonLinkColor !== "rgb(139, 13, 34)") {
        failures.push(`${label}: directory/county link color ${result.comparisonLinkColor}`);
      }
      if (route.endsWith("blog/index.html") && result.directoryLinkCount < 40) {
        failures.push(`${label}: only ${result.directoryLinkCount} directory links`);
      }
      if (runtimeErrors.length) failures.push(`${label}: ${runtimeErrors.join(" | ")}`);
      schemaBlocks += result.schemaCount;

      if (engineName === "Chrome" && width === 390) {
        const slug = route.replace(/^\//, "").replaceAll("/", "-").replace(/\.html$/, "");
        await page.screenshot({ path: `${SCREENSHOTS}/${slug}-390.png`, fullPage: true });
      }
      await page.close();
    }
    await context.close();
  }
  await browser.close();
}

if (failures.length) {
  process.stderr.write(`${failures.join("\n")}\n`);
  process.exit(1);
}
process.stdout.write(
  `content-hub browser checks passed: ${engines.length} engines x ${routes.length} routes x ${widths.length} widths; ${schemaBlocks} schema blocks parsed\n`,
);
clearTimeout(hardTimeout);
