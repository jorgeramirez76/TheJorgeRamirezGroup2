import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { chromium } from "/Users/teddy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";


const ROOT = process.cwd();
const SCREENSHOTS = "/private/tmp/chatham-township-hero-browser";
const CASES = [
  { width: 390, deviceScaleFactor: 1, expectedCandidate: "chatham-township-2-640.webp" },
  { width: 390, deviceScaleFactor: 2, expectedCandidate: "chatham-township-2-960.webp" },
  { width: 1440, deviceScaleFactor: 1, expectedCandidate: "chatham-township-2-640.webp" },
  { width: 1440, deviceScaleFactor: 2, expectedCandidate: "chatham-township-2-960.webp" },
];
const MIME = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".webp": "image/webp",
};

await mkdir(SCREENSHOTS, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
});
const failures = [];
const observations = [];

try {
  for (const testCase of CASES) {
    const context = await browser.newContext({
      deviceScaleFactor: testCase.deviceScaleFactor,
      viewport: { width: testCase.width, height: 900 },
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
    const runtimeErrors = [];
    page.on("pageerror", (error) => runtimeErrors.push(String(error)));
    const response = await page.goto("http://local.test/towns/chatham-township.html", {
      waitUntil: "load",
      timeout: 20_000,
    });
    const hero = page.locator(".hero-photo img");
    await hero.evaluate(async (image) => {
      try {
        await image.decode();
      } catch {
        // The natural-size assertion reports a broken image precisely.
      }
    });
    const result = await page.evaluate(() => {
      const image = document.querySelector(".hero-photo img");
      const figure = document.querySelector(".hero-photo");
      const caption = figure?.querySelector("figcaption");
      const rect = image?.getBoundingClientRect();
      const currentCandidate = image?.currentSrc.split("/").at(-1) || "";
      const candidateWidth = Number(currentCandidate.match(/-(640|960)\.webp$/)?.[1] || 1280);
      return {
        alt: image?.alt || "",
        candidateWidth,
        caption: caption?.textContent || "",
        complete: image?.complete || false,
        currentCandidate,
        decoding: image?.getAttribute("decoding") || "",
        deviceScaleFactor: window.devicePixelRatio,
        documentWidth: document.documentElement.scrollWidth,
        fetchpriority: image?.getAttribute("fetchpriority") || "",
        imageRight: rect?.right || 0,
        naturalHeight: image?.naturalHeight || 0,
        naturalWidth: image?.naturalWidth || 0,
        renderedHeight: rect?.height || 0,
        renderedWidth: rect?.width || 0,
        srcset: image?.getAttribute("srcset") || "",
        viewportWidth: document.documentElement.clientWidth,
      };
    });

    const label = `${testCase.width}px @ ${testCase.deviceScaleFactor}x`;
    if (!response?.ok()) failures.push(`${label}: document status ${response?.status()}`);
    if (runtimeErrors.length) failures.push(`${label}: ${runtimeErrors.join(" | ")}`);
    if (!result.complete || !result.naturalWidth || !result.naturalHeight) {
      failures.push(`${label}: hero image is broken`);
    }
    if (result.currentCandidate !== testCase.expectedCandidate) {
      failures.push(
        `${label}: selected ${result.currentCandidate}; expected ${testCase.expectedCandidate}`,
      );
    }
    if (result.candidateWidth + 1 < result.renderedWidth * result.deviceScaleFactor) {
      failures.push(
        `${label}: ${result.candidateWidth}px candidate underserves ` +
        `${result.renderedWidth.toFixed(1)} CSS px at ${result.deviceScaleFactor}x`,
      );
    }
    if (result.fetchpriority !== "high" || result.decoding !== "async") {
      failures.push(`${label}: priority/loading semantics drifted`);
    }
    if (!result.srcset.includes("640w") || !result.srcset.includes("960w") || !result.srcset.includes("1280w")) {
      failures.push(`${label}: responsive candidate set is incomplete`);
    }
    if (!result.alt.includes("Mount Vernon School") || !result.alt.includes("Chatham Township")) {
      failures.push(`${label}: locality-specific alt text drifted`);
    }
    if (!result.caption.includes("Zeete") || !result.caption.includes("CC BY-SA 4.0")) {
      failures.push(`${label}: source attribution drifted`);
    }
    if (result.documentWidth > result.viewportWidth + 1 || result.imageRight > result.viewportWidth + 1) {
      failures.push(`${label}: horizontal overflow`);
    }

    observations.push(
      `${label}: ${result.currentCandidate}, ` +
      `${result.renderedWidth.toFixed(1)}×${result.renderedHeight.toFixed(1)} CSS px`,
    );
    await page.screenshot({
      path: `${SCREENSHOTS}/chatham-township-${testCase.width}-${testCase.deviceScaleFactor}x.png`,
      fullPage: false,
    });
    await context.close();
  }
} finally {
  await browser.close();
}

if (failures.length) {
  process.stderr.write(`${failures.join("\n")}\n`);
  process.exit(1);
}

process.stdout.write(`Chatham Township responsive hero checks passed.\n${observations.join("\n")}\n`);
