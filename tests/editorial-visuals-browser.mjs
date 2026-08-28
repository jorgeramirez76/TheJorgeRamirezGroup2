import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { chromium } from "/Users/teddy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const ROOT = process.cwd();
const MARKER = "<!-- JRG editorial visual:start -->";
const WIDTHS = [320, 390, 1440];
const MIME = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".jpg": "image/jpeg",
  ".js": "text/javascript; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
};

async function findEditorialPages(directory, relative = "") {
  const pages = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (entry.name.startsWith(".") || ["node_modules", "tests"].includes(entry.name)) continue;
    const absolute = path.join(directory, entry.name);
    const childRelative = path.join(relative, entry.name);
    if (entry.isDirectory()) {
      pages.push(...await findEditorialPages(absolute, childRelative));
    } else if (entry.isFile() && entry.name.endsWith(".html")) {
      const source = await readFile(absolute, "utf8");
      if (source.includes(MARKER)) pages.push(childRelative);
    }
  }
  return pages;
}

const editorialPages = (await findEditorialPages(ROOT)).sort();
if (editorialPages.length !== 38) {
  throw new Error(`Expected 38 editorial pages, found ${editorialPages.length}`);
}

const browser = await chromium.launch({
  headless: true,
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});
const failures = [];

try {
  for (const width of WIDTHS) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
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

    const page = await context.newPage();
    for (const relative of editorialPages) {
      const runtimeErrors = [];
      page.removeAllListeners("pageerror");
      page.on("pageerror", (error) => runtimeErrors.push(String(error)));
      const response = await page.goto(`http://local.test/${relative}`, {
        // External stylesheets are not guaranteed to finish by DOMContentLoaded.
        // Waiting for load prevents a false 1280px intrinsic-image overflow race.
        waitUntil: "load",
        timeout: 20_000,
      });
      await page.locator(".jrg-editorial-figure img").evaluate(async (image) => {
        image.scrollIntoView({ block: "center" });
        try {
          await image.decode();
        } catch {
          // The natural-size assertion below reports a broken image precisely.
        }
      });
      const result = await page.evaluate(() => {
        const figure = document.querySelector(".jrg-editorial-figure");
        const image = figure?.querySelector("img");
        const rect = figure?.getBoundingClientRect();
        const style = figure ? getComputedStyle(figure) : null;
        return {
          markerCount: document.querySelectorAll(".jrg-editorial-figure").length,
          naturalWidth: image?.naturalWidth || 0,
          naturalHeight: image?.naturalHeight || 0,
          alt: image?.getAttribute("alt") || "",
          loading: image?.getAttribute("loading") || "",
          decoding: image?.getAttribute("decoding") || "",
          figureWidth: rect?.width || 0,
          figureLeft: rect?.left || 0,
          figureRight: rect?.right || 0,
          display: style?.display || "",
          borderTopColor: style?.borderTopColor || "",
          viewportWidth: window.innerWidth,
          documentWidth: document.documentElement.scrollWidth,
          h1Count: document.querySelectorAll("h1").length,
        };
      });

      const prefix = `${relative} @ ${width}px`;
      if (!response || response.status() !== 200) failures.push(`${prefix}: document did not load`);
      if (runtimeErrors.length) failures.push(`${prefix}: runtime errors: ${runtimeErrors.join(" | ")}`);
      if (result.markerCount !== 1) failures.push(`${prefix}: expected one editorial figure`);
      if (!result.naturalWidth || !result.naturalHeight) failures.push(`${prefix}: editorial image is broken`);
      if (result.alt.trim().length < 24) failures.push(`${prefix}: editorial image lacks descriptive alt text`);
      if (result.loading !== "lazy" || result.decoding !== "async") failures.push(`${prefix}: image loading attributes drifted`);
      if (result.figureWidth <= 0 || result.display === "none") failures.push(`${prefix}: editorial figure is not visible`);
      if (result.figureWidth > Math.min(962, width) + 1) failures.push(`${prefix}: editorial figure exceeds its responsive width`);
      if (result.figureLeft < -1 || result.figureRight > width + 1) failures.push(`${prefix}: editorial figure escapes viewport`);
      if (result.documentWidth > result.viewportWidth + 1) failures.push(`${prefix}: horizontal overflow`);
      if (result.h1Count !== 1) failures.push(`${prefix}: expected one h1`);
      if (result.borderTopColor === "rgba(0, 0, 0, 0)") failures.push(`${prefix}: branded figure border missing`);
    }
    await context.close();
  }
} finally {
  await browser.close();
}

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log(`Editorial visual browser checks passed: ${editorialPages.length} pages × ${WIDTHS.length} widths.`);
