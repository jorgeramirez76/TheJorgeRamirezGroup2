import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { chromium } from "/Users/teddy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const ROOT = path.resolve(process.cwd());
const SITE = "https://thejorgeramirezgroup.com";
const WIDTHS = [320, 390, 1440];
const hardTimeout = setTimeout(() => {
  process.stderr.write("market-intent browser audit exceeded the 180-second hard timeout\n");
  process.exit(2);
}, 180_000);
const SCREENSHOT_DIR = "/private/tmp/jrg-market-intent-browser-audit";
const SCREENSHOT_ROUTES = new Set([
  "/blog/hudson-county-real-estate-market-q2-2026",
  "/es/blog/market-report-glen-ridge-nj-2026",
  "/es/blog/market-report-cranford-nj-2026",
]);
const MIME = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".ico": "image/x-icon",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".js": "text/javascript; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
};

async function json(relative) {
  return JSON.parse(await readFile(path.join(ROOT, relative), "utf8"));
}

const countyManifest = await json("data/county-market-report-sources-2026-08-26.json");
const townManifests = [
  await json("data/town-market-research-essex-middlesex-somerset.json"),
  await json("data/union-morris-town-market-sources-2026-08-26.json"),
];

const records = [];
for (const report of countyManifest.reports) {
  for (const language of ["en", "es"]) {
    records.push({
      family: "county",
      language,
      route: report.routes[language],
      pair: report.routes,
      legacyQ2: report.legacyRoutePeriod === "Q2 2026",
      modifiedOn: "2026-08-27",
      sourceReviewedOn: "2026-08-27",
      report,
    });
  }
}
for (const [manifestIndex, manifest] of townManifests.entries()) {
  for (const report of manifest.reports) {
    for (const language of ["en", "es"]) {
      records.push({
        family: manifestIndex === 0 ? "town-east" : "town-west",
        language,
        route: report.routes[language],
        pair: report.routes,
        legacyQ2: false,
        modifiedOn: "2026-08-27",
        sourceReviewedOn: "2026-08-26",
        report,
      });
    }
  }
}

if (records.length !== 54) throw new Error(`Expected 54 routes, found ${records.length}`);
if (new Set(records.map(({ route }) => route)).size !== records.length) {
  throw new Error("Market route manifests contain duplicate routes");
}

const failures = [];
const canonicalsByWidth = new Map(WIDTHS.map((width) => [width, []]));
let schemaBlocks = 0;
let keyboardMenuScenarios = 0;
let localAssetResponses = 0;

const browser = await chromium.launch({
  headless: true,
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});
await mkdir(SCREENSHOT_DIR, { recursive: true });

try {
  for (const width of WIDTHS) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    const page = await context.newPage();

    await context.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      if (url.hostname !== "local.test") {
        const contentType = url.hostname === "fonts.googleapis.com"
          ? "text/css; charset=utf-8"
          : "text/javascript; charset=utf-8";
        return route.fulfill({ status: 200, body: "", contentType });
      }

      let relative = decodeURIComponent(url.pathname).replace(/^\/+/, "");
      if (!relative) relative = "index.html";
      const absolute = path.resolve(ROOT, relative);
      if (absolute !== ROOT && !absolute.startsWith(`${ROOT}${path.sep}`)) {
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

    for (const record of records) {
      const label = `${record.route} @ ${width}px`;
      const runtimeErrors = [];
      const badLocalAssets = [];
      const failedRequests = [];
      const onPageError = (error) => runtimeErrors.push(`pageerror: ${String(error)}`);
      const onConsole = (message) => {
        if (["error", "warning"].includes(message.type())) {
          runtimeErrors.push(`${message.type()}: ${message.text()}`);
        }
      };
      const onResponse = (response) => {
        const url = new URL(response.url());
        if (url.hostname !== "local.test") return;
        localAssetResponses += 1;
        if (response.status() >= 400) badLocalAssets.push(`${response.status()} ${url.pathname}`);
      };
      const onRequestFailed = (request) => failedRequests.push(`${request.url()}: ${request.failure()?.errorText || "failed"}`);
      page.on("pageerror", onPageError);
      page.on("console", onConsole);
      page.on("response", onResponse);
      page.on("requestfailed", onRequestFailed);

      const response = await page.goto(`http://local.test${record.route}.html`, {
        waitUntil: "load",
        timeout: 20_000,
      });

      await page.evaluate(async () => {
        for (const image of document.images) {
          image.scrollIntoView({ block: "center", inline: "nearest" });
          if (!image.complete) {
            await new Promise((resolve) => {
              image.addEventListener("load", resolve, { once: true });
              image.addEventListener("error", resolve, { once: true });
              setTimeout(resolve, 3_000);
            });
          }
          if (image.complete && image.naturalWidth && typeof image.decode === "function") {
            try { await image.decode(); } catch { /* naturalWidth remains authoritative */ }
          }
        }
        window.scrollTo(0, 0);
      });

      const result = await page.evaluate(() => {
        const isVisible = (element) => {
          if (!element) return false;
          const style = getComputedStyle(element);
          const rect = element.getBoundingClientRect();
          return style.display !== "none" && style.visibility !== "hidden" && Number(style.opacity) > 0 && rect.width > 0 && rect.height > 0;
        };
        const accessibleName = (element) => (
          element.getAttribute("aria-label") ||
          element.getAttribute("title") ||
          element.innerText ||
          element.querySelector("img")?.getAttribute("alt") ||
          ""
        ).trim();
        const schemaErrors = [];
        const schemas = [...document.querySelectorAll('script[type="application/ld+json"]')];
        const parsedSchemas = [];
        for (const script of schemas) {
          try { parsedSchemas.push(JSON.parse(script.textContent)); }
          catch (error) { schemaErrors.push(String(error)); }
        }
        const canonicalNodes = [...document.querySelectorAll('link[rel="canonical"]')];
        const hreflangNodes = [...document.querySelectorAll('link[rel="alternate"][hreflang]')];
        const h1 = document.querySelector("h1");
        const direct = document.querySelector("[data-direct-answer]");
        const h1Rect = h1?.getBoundingClientRect();
        const directRect = direct?.getBoundingClientRect();
        const interactive = [...document.querySelectorAll('a[href], button, input, select, textarea')];
        const visibleInteractive = interactive.filter(isVisible);
        const meta = (selector) => document.querySelector(selector)?.getAttribute("content") || "";
        const bodyText = document.body.innerText.replace(/\s+/g, " ").trim();
        const schemaModifiedDates = [];
        const visitSchema = (value) => {
          if (!value || typeof value !== "object") return;
          if (typeof value.dateModified === "string") schemaModifiedDates.push(value.dateModified);
          for (const child of Array.isArray(value) ? value : Object.values(value)) visitSchema(child);
        };
        parsedSchemas.forEach(visitSchema);
        return {
          bodyText,
          brokenImages: [...document.images]
            .filter((image) => !image.complete || image.naturalWidth === 0)
            .map((image) => image.getAttribute("src") || "<missing src>"),
          canonicalCount: canonicalNodes.length,
          canonical: canonicalNodes[0]?.href || "",
          directAnswer: direct?.innerText.replace(/\s+/g, " ").trim() || "",
          directAnswerVisible: isVisible(direct),
          directAnswerWithinViewport: !!directRect && directRect.left >= -1 && directRect.right <= innerWidth + 1,
          duplicateHreflangs: hreflangNodes
            .map((node) => node.hreflang)
            .filter((value, index, all) => all.indexOf(value) !== index),
          h1Count: document.querySelectorAll("h1").length,
          h1Text: h1?.innerText.replace(/\s+/g, " ").trim() || "",
          h1Visible: isVisible(h1),
          h1WithinViewport: !!h1Rect && h1Rect.left >= -1 && h1Rect.right <= innerWidth + 1,
          hreflangs: Object.fromEntries(hreflangNodes.map((node) => [node.hreflang, node.href])),
          htmlLang: document.documentElement.lang,
          lastUpdated: meta('meta[name="last-updated"]'),
          articleModified: meta('meta[property="article:modified_time"]'),
          modifiedSchemaDates: schemaModifiedDates,
          navCount: document.querySelectorAll("nav").length,
          positiveTabindex: interactive.filter((element) => Number(element.getAttribute("tabindex")) > 0).length,
          unnamedInteractive: visibleInteractive.filter((element) => !accessibleName(element)).length,
          overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          overflowElements: [...document.querySelectorAll("body *")]
            .map((element) => {
              const rect = element.getBoundingClientRect();
              return {
                tag: element.tagName,
                className: String(element.className || "").slice(0, 80),
                left: Math.round(rect.left * 10) / 10,
                right: Math.round(rect.right * 10) / 10,
                scrollWidth: element.scrollWidth,
                clientWidth: element.clientWidth,
              };
            })
            .filter((item) => item.left < -1 || item.right > innerWidth + 1 || item.scrollWidth > item.clientWidth + 1)
            .slice(0, 12),
          schemaCount: schemas.length,
          schemaErrors,
          timeDates: [...document.querySelectorAll("time[datetime]")].map((time) => time.dateTime),
          title: document.title,
          viewportWidth: innerWidth,
        };
      });

      const expectedCanonical = `${SITE}${record.route}`;
      const expectedHreflangs = {
        "en-US": `${SITE}${record.pair.en}`,
        "es-US": `${SITE}${record.pair.es}`,
        "x-default": `${SITE}${record.pair.en}`,
      };
      const directWordCount = result.directAnswer.split(/\s+/).filter(Boolean).length;

      if (!response?.ok()) failures.push(`${label}: document HTTP ${response?.status()}`);
      if (runtimeErrors.length) failures.push(`${label}: runtime ${runtimeErrors.join(" | ")}`);
      if (badLocalAssets.length) failures.push(`${label}: local assets ${badLocalAssets.join(" | ")}`);
      if (failedRequests.length) failures.push(`${label}: failed requests ${failedRequests.join(" | ")}`);
      if (result.brokenImages.length) failures.push(`${label}: broken images ${result.brokenImages.join(", ")}`);
      if (result.overflow > 1) failures.push(`${label}: horizontal overflow ${result.overflow}px; ${JSON.stringify(result.overflowElements)}`);
      if (result.h1Count !== 1 || !result.h1Visible || !result.h1WithinViewport) {
        failures.push(`${label}: h1 count=${result.h1Count}, visible=${result.h1Visible}, withinViewport=${result.h1WithinViewport}`);
      }
      if (!result.directAnswerVisible || !result.directAnswerWithinViewport) {
        failures.push(`${label}: direct answer hidden or outside viewport`);
      }
      if (directWordCount < 40 || directWordCount > 60) {
        failures.push(`${label}: direct answer has ${directWordCount} words, expected 40-60`);
      }
      if (result.schemaCount < 1 || result.schemaErrors.length) {
        failures.push(`${label}: schema count=${result.schemaCount}; ${result.schemaErrors.join(" | ")}`);
      }
      if (result.canonicalCount !== 1 || result.canonical !== expectedCanonical) {
        failures.push(`${label}: canonical count=${result.canonicalCount}; value=${result.canonical}`);
      }
      for (const [hreflang, expected] of Object.entries(expectedHreflangs)) {
        if (result.hreflangs[hreflang] !== expected) {
          failures.push(`${label}: hreflang ${hreflang}=${result.hreflangs[hreflang] || "missing"}`);
        }
      }
      if (result.hreflangs.es && result.hreflangs.es !== expectedHreflangs["es-US"]) {
        failures.push(`${label}: hreflang es=${result.hreflangs.es}`);
      }
      if (result.duplicateHreflangs.length) failures.push(`${label}: duplicate hreflangs ${result.duplicateHreflangs.join(", ")}`);
      if (result.htmlLang !== record.language) failures.push(`${label}: html lang=${result.htmlLang}`);
      if (result.positiveTabindex) failures.push(`${label}: ${result.positiveTabindex} positive tabindex controls`);
      if (result.unnamedInteractive) failures.push(`${label}: ${result.unnamedInteractive} visible unnamed controls`);
      if (result.navCount !== 1) failures.push(`${label}: nav count=${result.navCount}`);
      if (result.lastUpdated !== record.modifiedOn || result.articleModified !== record.modifiedOn) {
        failures.push(`${label}: dates last-updated=${result.lastUpdated}; article:modified=${result.articleModified}`);
      }
      if (!result.modifiedSchemaDates.length || result.modifiedSchemaDates.some((value) => value !== record.modifiedOn)) {
        failures.push(`${label}: schema modified dates=${result.modifiedSchemaDates.join(",") || "missing"}`);
      }
      if (!result.timeDates.includes(record.sourceReviewedOn)) {
        failures.push(`${label}: no visible source-review time datetime=${record.sourceReviewedOn}`);
      }

      if (record.family === "county") {
        if (!/source guide|research guide|gu[ií]a de fuentes|gu[ií]a de investigaci[oó]n/i.test(result.h1Text)) {
          failures.push(`${label}: H1 does not identify a source guide: ${result.h1Text}`);
        }
        if (/Q2 2026 market report|informe (?:del )?mercado (?:de|para) Q2/i.test(result.title) || /Q2 2026 market report|informe (?:del )?mercado (?:de|para) Q2/i.test(result.h1Text)) {
          failures.push(`${label}: title/H1 promises a Q2 report`);
        }
        if (!/does not (?:publish|reproduce)|not a live|no publica|no reproduce|no (?:es )?una radiograf[ií]a vigente/i.test(result.directAnswer)) {
          failures.push(`${label}: county direct answer lacks no-snapshot wording`);
        }
        if (!/copyright|derechos de autor/i.test(result.bodyText) || !/do(?:es)? not grant express republication permission|no (?:otorgan|conceden) permiso expreso para (?:volver a publicar|republicarlos)/i.test(result.bodyText)) {
          failures.push(`${label}: publication-rights disclaimer missing`);
        }
        if (record.legacyQ2) {
          const q2Phrase = record.language === "en"
            ? "does not publish a Q2 2026 market snapshot"
            : "no publica una radiografía del mercado para el Q2 de 2026";
          if (!result.directAnswer.includes(q2Phrase)) failures.push(`${label}: exact Q2 direct-answer disclaimer missing`);
          const continuityPhrase = record.language === "en"
            ? "retained URL includes Q2 2026 for continuity"
            : "URL conservada incluye Q2 2026 por continuidad";
          if (!result.bodyText.includes(continuityPhrase)) failures.push(`${label}: Q2 route-continuity disclaimer missing`);
        }
      } else {
        if (!result.directAnswer.includes("2025")) failures.push(`${label}: town direct answer lacks 2025 source year`);
        if (!/historical|hist[oó]ricos/i.test(result.directAnswer)) failures.push(`${label}: town direct answer lacks historical qualifier`);
        if (!/not current listing data|no (?:datos vigentes de listados|listados vigentes)/i.test(result.directAnswer)) {
          failures.push(`${label}: town direct answer lacks current-listing disclaimer`);
        }
        if (/finalized 2026|finalizada de 2026/i.test(result.bodyText)) failures.push(`${label}: finalized 2026 value claim found`);
      }

      if (SCREENSHOT_ROUTES.has(record.route)) {
        const slug = record.route.replace(/^\//, "").replaceAll("/", "-");
        await page.screenshot({
          path: `${SCREENSHOT_DIR}/${slug}-${width}.png`,
          fullPage: false,
        });
      }

      // Test the skip link as the first keyboard stop and verify it becomes visible.
      await page.evaluate(() => { document.activeElement?.blur(); window.scrollTo(0, 0); });
      await page.keyboard.press("Tab");
      const skipResult = await page.evaluate(() => {
        const link = document.querySelector(".skip-link");
        const rect = link?.getBoundingClientRect();
        return {
          focused: document.activeElement === link,
          href: link?.getAttribute("href") || "",
          visibleTop: rect?.top ?? -999,
        };
      });
      if (!skipResult.focused || skipResult.href !== "#main" || skipResult.visibleTop < -1) {
        failures.push(`${label}: skip link keyboard behavior ${JSON.stringify(skipResult)}`);
      }

      const menu = page.locator(".menu-button, .market-menu-button");
      if (await menu.count() !== 1) {
        failures.push(`${label}: expected one menu button, found ${await menu.count()}`);
      } else if (width < 1440) {
        keyboardMenuScenarios += 1;
        if (!await menu.isVisible()) failures.push(`${label}: mobile menu button hidden`);
        const menuBox = await menu.boundingBox();
        if (!menuBox || menuBox.width < 43.5 || menuBox.height < 43.5) {
          failures.push(`${label}: mobile menu control below 44px (${menuBox?.width}x${menuBox?.height})`);
        }
        await menu.focus();
        await page.keyboard.press("Enter");
        const openResult = await page.evaluate(() => {
          const button = document.querySelector(".menu-button, .market-menu-button");
          const links = document.querySelector("#primary-links");
          const visibleLinks = [...(links?.querySelectorAll("a[href]") || [])].filter((link) => {
            const style = getComputedStyle(link);
            const rect = link.getBoundingClientRect();
            return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
          });
          return {
            expanded: button?.getAttribute("aria-expanded"),
            linkCount: visibleLinks.length,
            tooSmall: visibleLinks.filter((link) => link.getBoundingClientRect().height < 43.5).length,
            outsideViewport: visibleLinks.filter((link) => {
              const rect = link.getBoundingClientRect();
              return rect.left < -1 || rect.right > innerWidth + 1;
            }).length,
            overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          };
        });
        if (openResult.expanded !== "true" || openResult.linkCount < 5 || openResult.tooSmall || openResult.outsideViewport || openResult.overflow > 1) {
          failures.push(`${label}: opened mobile nav ${JSON.stringify(openResult)}`);
        }
        await page.keyboard.press("Tab");
        const tabEnteredMenu = await page.evaluate(() => document.querySelector("#primary-links")?.contains(document.activeElement) || false);
        if (!tabEnteredMenu) failures.push(`${label}: Tab did not enter opened mobile navigation`);
        await menu.focus();
        await page.keyboard.press("Enter");
        if (await menu.getAttribute("aria-expanded") !== "false") failures.push(`${label}: keyboard could not close mobile menu`);
      } else {
        if (await menu.isVisible()) failures.push(`${label}: desktop menu button should be hidden`);
        const desktopNav = await page.evaluate(() => {
          const links = [...document.querySelectorAll("#primary-links a[href]")];
          return {
            count: links.length,
            hidden: links.filter((link) => {
              const style = getComputedStyle(link);
              const rect = link.getBoundingClientRect();
              return style.display === "none" || style.visibility === "hidden" || rect.width <= 0 || rect.height <= 0;
            }).length,
            tooSmall: links.filter((link) => link.getBoundingClientRect().height < 43.5).length,
          };
        });
        if (desktopNav.count < 5 || desktopNav.hidden || desktopNav.tooSmall) {
          failures.push(`${label}: desktop nav ${JSON.stringify(desktopNav)}`);
        }
      }

      schemaBlocks += result.schemaCount;
      canonicalsByWidth.get(width).push(result.canonical);
      page.off("pageerror", onPageError);
      page.off("console", onConsole);
      page.off("response", onResponse);
      page.off("requestfailed", onRequestFailed);
    }
    await context.close();

    const canonicals = canonicalsByWidth.get(width);
    if (new Set(canonicals).size !== records.length) {
      failures.push(`All routes @ ${width}px: canonical values are not unique (${new Set(canonicals).size}/${records.length})`);
    }
  }
} finally {
  await browser.close();
}

if (failures.length) {
  process.stderr.write(`${failures.join("\n")}\n`);
  process.exit(1);
}

process.stdout.write(
  `Market-intent browser audit passed: ${records.length} pages × ${WIDTHS.length} widths = ${records.length * WIDTHS.length} scenarios; ` +
  `${keyboardMenuScenarios} keyboard mobile-menu scenarios; ${schemaBlocks} schema blocks parsed; ${localAssetResponses} local responses verified.\n`,
);
clearTimeout(hardTimeout);
