import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { chromium, webkit } from "/Users/teddy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const ROOT = path.resolve(process.cwd());
const SCREENSHOTS = "/private/tmp/jrg-remaining-english-towns-20260829";
const WIDTHS = [390, 1440];
const ROUTES = [
  {
    route: "/towns/helmetta",
    phrase: "Separate the Borough file from construction-code guidance",
  },
  {
    route: "/towns/middlesex",
    phrase: "Middlesex Borough is not Middlesex County",
  },
  {
    route: "/towns/orange",
    phrase: "Verify the approved unit count before relying on a multifamily label",
  },
];
const ENGINES = [
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

const hardTimeout = setTimeout(() => {
  process.stderr.write("remaining-town browser checks exceeded the 120-second hard timeout\n");
  process.exit(2);
}, 120_000);
const failures = [];
let schemaBlocks = 0;

await mkdir(SCREENSHOTS, { recursive: true });

for (const [engineName, engine, launchOptions] of ENGINES) {
  const browser = await engine.launch({ headless: true, ...launchOptions });
  try {
    for (const width of WIDTHS) {
      const context = await browser.newContext({ viewport: { width, height: 900 } });
      await context.route("**/*", async (requestRoute) => {
        const url = new URL(requestRoute.request().url());
        if (url.hostname !== "local.test") {
          const contentType = url.hostname === "fonts.googleapis.com"
            ? "text/css; charset=utf-8"
            : "text/javascript; charset=utf-8";
          return requestRoute.fulfill({ status: 200, body: "", contentType });
        }
        let relative = decodeURIComponent(url.pathname).replace(/^\/+/, "");
        if (!relative) relative = "index.html";
        if (!path.extname(relative)) relative += ".html";
        const absolute = path.resolve(ROOT, relative);
        if (absolute !== ROOT && !absolute.startsWith(`${ROOT}${path.sep}`)) {
          return requestRoute.fulfill({ status: 403, body: "Forbidden" });
        }
        try {
          const body = await readFile(absolute);
          return requestRoute.fulfill({
            status: 200,
            body,
            contentType: MIME[path.extname(absolute).toLowerCase()] || "application/octet-stream",
          });
        } catch {
          return requestRoute.fulfill({ status: 404, body: "Not found" });
        }
      });

      for (const record of ROUTES) {
        const page = await context.newPage();
        const runtimeErrors = [];
        page.on("pageerror", (error) => runtimeErrors.push(`pageerror: ${String(error)}`));
        page.on("console", (message) => {
          if (["error", "warning"].includes(message.type())) {
            runtimeErrors.push(`${message.type()}: ${message.text()}`);
          }
        });

        const response = await page.goto(`http://local.test${record.route}`, {
          waitUntil: "load",
          timeout: 20_000,
        });
        await page.evaluate(async () => {
          for (const image of document.images) {
            image.loading = "eager";
            if (!image.complete) {
              await new Promise((resolve) => {
                image.addEventListener("load", resolve, { once: true });
                image.addEventListener("error", resolve, { once: true });
                setTimeout(resolve, 3_000);
              });
            }
            if (image.complete && image.naturalWidth && typeof image.decode === "function") {
              try { await image.decode(); } catch { /* naturalWidth is authoritative. */ }
            }
          }
        });

        const result = await page.evaluate(() => {
          const schemas = [...document.querySelectorAll('script[type="application/ld+json"]')];
          const schemaErrors = [];
          for (const script of schemas) {
            try { JSON.parse(script.textContent); }
            catch (error) { schemaErrors.push(String(error)); }
          }
          const ids = [...document.querySelectorAll("[id]")].map((node) => node.id);
          return {
            text: document.body.innerText.replace(/\s+/g, " ").trim(),
            canonical: document.querySelector('link[rel="canonical"]')?.href || "",
            robots: document.querySelector('meta[name="robots"]')?.content || "",
            h1Count: document.querySelectorAll("h1").length,
            mainCount: document.querySelectorAll("main#main").length,
            trustCount: document.querySelectorAll('[data-local-agent-trust="v1"]').length,
            provenanceCount: document.querySelectorAll('[data-content-provenance="v1"]').length,
            sourceCount: document.querySelectorAll('.town-guide__source-card a[href^="https://"]').length,
            actionCount: document.querySelectorAll(".town-guide__actions a").length,
            overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
            brokenImages: [...document.images]
              .filter((image) => !image.complete || image.naturalWidth === 0)
              .map((image) => image.getAttribute("src") || "<missing>"),
            duplicateIds: ids.filter((id, index) => ids.indexOf(id) !== index),
            schemaCount: schemas.length,
            schemaErrors,
            hasRemoteRuntimeImage: [...document.images]
              .some((image) => /^https?:\/\//i.test(image.getAttribute("src") || "")),
          };
        });

        const label = `${engineName} ${record.route} @ ${width}px`;
        if (!response?.ok()) failures.push(`${label}: HTTP ${response?.status()}`);
        if (result.canonical !== `https://thejorgeramirezgroup.com${record.route}`) {
          failures.push(`${label}: canonical ${result.canonical}`);
        }
        if (!result.robots.toLowerCase().startsWith("index")) failures.push(`${label}: robots ${result.robots}`);
        if (result.h1Count !== 1 || result.mainCount !== 1) failures.push(`${label}: h1=${result.h1Count}; main=${result.mainCount}`);
        if (result.trustCount !== 1 || result.provenanceCount !== 1) {
          failures.push(`${label}: trust=${result.trustCount}; provenance=${result.provenanceCount}`);
        }
        if (result.sourceCount < 5) failures.push(`${label}: only ${result.sourceCount} official source links`);
        if (result.actionCount < 4) failures.push(`${label}: only ${result.actionCount} primary actions`);
        if (!result.text.includes(record.phrase)) failures.push(`${label}: missing town-specific phrase`);
        if (result.overflow > 1) failures.push(`${label}: horizontal overflow ${result.overflow}px`);
        if (result.brokenImages.length) failures.push(`${label}: broken images ${result.brokenImages.join(", ")}`);
        if (result.duplicateIds.length) failures.push(`${label}: duplicate IDs ${result.duplicateIds.join(", ")}`);
        if (!result.schemaCount || result.schemaErrors.length) {
          failures.push(`${label}: schema=${result.schemaCount}; ${result.schemaErrors.join(" | ")}`);
        }
        if (result.hasRemoteRuntimeImage) failures.push(`${label}: remote runtime image`);
        if (runtimeErrors.length) failures.push(`${label}: ${runtimeErrors.join(" | ")}`);
        schemaBlocks += result.schemaCount;

        if (engineName === "Chrome" && width === 390) {
          await page.screenshot({
            path: `${SCREENSHOTS}/${record.route.split("/").at(-1)}-390.png`,
            fullPage: true,
          });
        }
        await page.close();
      }
      await context.close();
    }
  } finally {
    await browser.close();
  }
}

if (failures.length) {
  process.stderr.write(`${failures.join("\n")}\n`);
  process.exit(1);
}
process.stdout.write(
  `remaining-town browser checks passed: ${ENGINES.length} engines x ${ROUTES.length} routes x ${WIDTHS.length} widths; ${schemaBlocks} schema blocks parsed\n`,
);
clearTimeout(hardTimeout);
