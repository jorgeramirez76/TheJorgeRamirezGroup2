import { readFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { chromium } from "/Users/teddy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const ROOT = process.cwd();
const SCREENSHOTS = "/private/tmp/final-service-browser-20260827";
const hardTimeout = setTimeout(() => {
  process.stderr.write("final service browser checks exceeded the 120-second hard timeout\n");
  process.exit(2);
}, 120_000);
const routes = new Map([
  ["/luxury-homes-nj.html", "https://thejorgeramirezgroup.com/luxury-homes-nj"],
  ["/es/luxury-homes-nj.html", "https://thejorgeramirezgroup.com/es/luxury-homes-nj"],
  ["/55-plus-communities-nj.html", "https://thejorgeramirezgroup.com/55-plus-communities-nj"],
  ["/es/55-plus-communities-nj.html", "https://thejorgeramirezgroup.com/es/55-plus-communities-nj"],
  ["/downsizing-nj.html", "https://thejorgeramirezgroup.com/downsizing-nj"],
  ["/es/downsizing-nj.html", "https://thejorgeramirezgroup.com/es/downsizing-nj"],
  [
    "/blog/moving-from-jersey-city-hoboken-to-suburbs.html",
    "https://thejorgeramirezgroup.com/blog/moving-from-jersey-city-hoboken-to-suburbs",
  ],
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
let schemaBlocks = 0;

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

  for (const [route, expectedCanonical] of routes) {
    const page = await context.newPage();
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(String(error)));
    const response = await page.goto(`http://local.test${route}`, {
      waitUntil: "domcontentloaded",
      timeout: 20_000,
    });
    await page.evaluate(async () => {
      for (const image of document.images) {
        image.loading = "eager";
        image.scrollIntoView({ block: "center" });
        await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        try {
          await image.decode();
        } catch {
          // The broken-image assertion reports the exact source below.
        }
      }
      window.scrollTo(0, 0);
    });
    await page.waitForTimeout(80);
    await page.locator(".skip-link").focus();
    const skipLinkState = await page.evaluate(() => {
      const active = document.activeElement;
      const rect = active?.getBoundingClientRect();
      return {
        activeClass: active?.className || "",
        focused: Boolean(active?.classList.contains("skip-link")),
        rect: rect ? {
          bottom: rect.bottom,
          height: rect.height,
          left: rect.left,
          right: rect.right,
          top: rect.top,
          width: rect.width,
        } : null,
        visible: Boolean(
          rect && rect.width > 0 && rect.height > 0 && rect.left >= -1 &&
          rect.right <= document.documentElement.clientWidth + 1
        ),
      };
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
      const h1 = document.querySelector("h1");
      const h1Rect = h1?.getBoundingClientRect();
      const main = document.querySelector("main#main");
      const nav = document.querySelector("nav");
      const navRect = nav?.getBoundingClientRect();
      const description = document.querySelector('meta[name="description"]')?.content || "";
      const colors = document.documentElement.innerHTML.toLowerCase();
      const actionable = [...document.querySelectorAll("a, button")]
        .filter((element) => {
          const style = getComputedStyle(element);
          return !element.classList.contains("skip-link") &&
            style.display !== "none" && style.visibility !== "hidden";
        })
        .map((element) => {
          const rect = element.getBoundingClientRect();
          return { left: rect.left, right: rect.right, text: element.textContent.trim().slice(0, 50) };
        });
      return {
        brokenImages: [...document.images]
          .filter((image) => !image.complete || image.naturalWidth === 0)
          .map((image) => image.getAttribute("src")),
        canonical: document.querySelector('link[rel="canonical"]')?.href || "",
        colors,
        descriptionLength: description.length,
        h1Count: document.querySelectorAll("h1").length,
        h1Font: h1 ? getComputedStyle(h1).fontFamily : "",
        h1InMain: Boolean(main && h1 && main.contains(h1)),
        h1Visible: Boolean(h1Rect && h1Rect.width > 0 && h1Rect.height > 0),
        htmlLang: document.documentElement.lang,
        mainCount: document.querySelectorAll("main#main").length,
        navVisible: Boolean(navRect && navRect.width > 0 && navRect.height > 0),
        overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
        outOfViewportActions: actionable.filter(
          (item) => item.left < -1 || item.right > document.documentElement.clientWidth + 1,
        ),
        schemaCount: schemas.length,
        schemaErrors,
        bodyFont: getComputedStyle(document.body).fontFamily,
      };
    });

    if (!response?.ok()) failures.push(`${route} @ ${width}: HTTP ${response?.status()}`);
    if (result.canonical !== expectedCanonical) {
      failures.push(`${route} @ ${width}: canonical ${result.canonical}`);
    }
    if (result.mainCount !== 1 || result.h1Count !== 1 || !result.h1InMain || !result.h1Visible) {
      failures.push(
        `${route} @ ${width}: main=${result.mainCount}; h1=${result.h1Count}; inMain=${result.h1InMain}; visible=${result.h1Visible}`,
      );
    }
    if (!result.navVisible) failures.push(`${route} @ ${width}: nav hidden`);
    if (!skipLinkState.focused || !skipLinkState.visible) {
      failures.push(
        `${route} @ ${width}: skip link ${JSON.stringify(skipLinkState)}`,
      );
    }
    if (result.overflow) failures.push(`${route} @ ${width}: horizontal overflow`);
    if (result.outOfViewportActions.length) {
      failures.push(
        `${route} @ ${width}: actions outside viewport ${JSON.stringify(result.outOfViewportActions)}`,
      );
    }
    if (result.brokenImages.length) {
      failures.push(`${route} @ ${width}: broken images ${result.brokenImages.join(", ")}`);
    }
    if (!result.schemaCount || result.schemaErrors.length) {
      failures.push(
        `${route} @ ${width}: schema count=${result.schemaCount}; ${result.schemaErrors.join(" | ")}`,
      );
    }
    if (!/playfair/i.test(result.h1Font) || !/inter/i.test(result.bodyFont)) {
      failures.push(`${route} @ ${width}: fonts h1=${result.h1Font}; body=${result.bodyFont}`);
    }
    if (result.descriptionLength < 40 || result.descriptionLength > 165) {
      failures.push(`${route} @ ${width}: description length ${result.descriptionLength}`);
    }
    for (const color of ["#1a1a1a", "#c41230", "#b8962e", "#fafaf8"]) {
      if (!result.colors.includes(color)) failures.push(`${route} @ ${width}: missing ${color}`);
    }
    const expectedLang = route.startsWith("/es/") ? "es-US" : "en-US";
    if (result.htmlLang !== expectedLang) {
      failures.push(`${route} @ ${width}: lang=${result.htmlLang}; expected=${expectedLang}`);
    }
    if (pageErrors.length) failures.push(`${route} @ ${width}: ${pageErrors.join(" | ")}`);
    schemaBlocks += result.schemaCount;

    if (width === 390) {
      const slug = route.replace(/^\//, "").replaceAll("/", "-").replace(/\.html$/, "");
      await page.screenshot({ path: `${SCREENSHOTS}/${slug}-390.png`, fullPage: true });
    }
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
  `final service browser checks passed: ${routes.size} routes x ${widths.length} widths; ${schemaBlocks} schema blocks parsed; screenshots ${SCREENSHOTS}\n`,
);
