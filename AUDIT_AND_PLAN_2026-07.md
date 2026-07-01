# JRG.com — Audit, Execution Log & Remaining Plan (2026-07-01)

Durable handoff doc. Repo: `/Users/teddy/TheJorgeRamirezGroup2` (hosted on **Vercel**, git-integration = push to `main` auto-deploys). This file is `*.md` → excluded from the live site by `.vercelignore`.

A full 13-agent audit (visual / technical-SEO / content-SEO / AI-SEO / perf / a11y) was run and synthesized into a plan. Phases P1–P6 partially executed. **Everything below marked ✅ is committed + live-verified.**

---

## ✅ DONE this session (live on thejorgeramirezgroup.com)

**Migration + earlier fixes:** GitHub Pages → Vercel (DNS A-record swap at GoDaddy; Zoho MX/SPF + `value.` subdomain preserved); `vercel.json` (cleanUrls, security+cache headers, redirects); `.vercelignore` (hides `.py`/`.md`); contact.html mobile menu; Spanish site JS 404 fix; site-wide sticky Call/Text bar (`js/site-cta.js`); SMS links; CTR title rewrites (~7 pages); self-canonical why-jorge; **ES `moving-from-nyc-to-nj-guide` fully translated**; 301 `/nyc-to-nj-relocation` → EN guide; serverless `api/lead.js` deployed (NOT wired — see below).

**P1 — shared CSS polish:** dropped dead Cormorant font; `--gold-text #8A6D14` (AA) on light-bg gold text; `.mobile-menu-btn` 44px; `@media prefers-reduced-motion` guard. File: `css/styles.css`.

**P2 — homepage LCP:** hero paints via inline HTML bg (not JS), removed the hero.jpg double-paint bug, `defer` on communities-data.js + main.js, reduced-motion carousel guard. Files: `index.html`, `js/main.js`.

**S-1 — collapsed duplicate `/realtor/` town system (biggest SEO win):** 138 explicit per-town `301 /realtor/<town>-nj → /towns/<town>` in `vercel.json`; removed 139 `/realtor/` `<loc>` from `sitemap.xml`; repointed 138 in-body `/realtor/` links in `towns/*.html` → `/towns/`. **GOTCHA: Vercel path-to-regexp `:param-suffix` patterns (e.g. `/realtor/:town-nj`) DO NOT MATCH — must use explicit per-item redirects.**

**P4 — town pages (139), partial:** ✅ all CTAs unified to **red** (user chose red over gold): `.topnav-cta` gold→red + agent-box button gold→red; ✅ emoji snapshot icons (💰⏱️📚🚂) → inline SVG line icons (123 files); ✅ **AI "answer block"** (40–60 word extractable quick-answer w/ median/DOM/schools/commute + county) injected after hero on 138 files.

**P5 — partial:** ✅ fixed property-tax post date contradiction (March→June).

**P6 — Spanish, partial:** ✅ **19 high-value ES service/landing pages fully translated** Spanglish→natural Spanish (tú form): `es/index`, `cash-offer`, `buyer-agency-agreement`, `55-plus-communities`, `divorce-home-sale`, `downsizing`, `fsbo-help`, `how-we-sell-your-home`, `inherited-home`, `investment-property`, `luxury-homes`, `nj-anchor-benefit-guide`, `nj-home-buyer-guide`, `nj-real-estate-questions-answers`, `nyc-to-nj-relocation`, `relocating-from-nj`, `sell-rental-property`, `summit-nj-homes-for-sale`, `westfield-nj-homes-for-sale`. Fixed "Inicio"(=house)→casa (kept nav/breadcrumb "Inicio" label), English title tokens, code-switch. Also fixed a `BuscarAction`→`SearchAction` schema typo + a broken language toggle.

---

## 📋 REMAINING (prioritized) — how to execute

### 1. Bulk Spanish translation (biggest remaining quality gap) — ~330 pages still Spanglish
`es/blog` (181), `es/towns` (138), `es/features` (18), `es/counties` (6), `es/tools` (4).
- **How:** same approach as the 19 done — a **Workflow** batching ~4 files/agent with the strict translation rules (preserve HTML/links/data/JSON-LD; "Inicio"=house→casa but KEEP nav/breadcrumb "Inicio"; keep brand/proper nouns; no invented data), then a verify agent + independent grep before commit. Reusable script skeleton: `es-translate-highvalue` workflow (see prior run).
- Verify after each batch: `grep -hoE 'Inicios|NJ Inicio|a Inicio' <files>` = empty; titles have no `Market Report|Real Estate|Homes for Sale|Guide|Realtor`; JSON-LD parses.

### 2. Blog typography unification (EN `blog/*.html`, ~200)
Per-file `<style>` blocks use an em type scale, non-Playfair H2s, and off-brand blue `.info-box` (#f0f3ff) + `.tax-table th` red. **Fix:** add a shared `.blog-content` scope to `css/styles.css` (H2 `font-family:var(--font-display)`, rem/clamp sizes, `.info-box` → `var(--light-gray)` + `border-left 3px var(--gold)`, table th → `var(--ink)`) and strip the per-file `<style>` from `generate_blog.py` + regenerate/scrub existing files. Also add blog answer blocks + `BreadcrumbList` to the ~53 `buying-home-*` posts missing it.

### 3. Comparison pages (6 `*-vs-*.html`) + thin tools
Replicate the "Quick Verdict" block (cranford-vs-westfield has it) to the other 5. Tools: `commute-scorer` (205w), `market-comparison-widget` (231w), `home-value-estimator` — add 300–500w + FAQPage, or `noindex` + drop from sitemap. Replace `#1a1a2e`→`var(--ink)` in tools (~40 files).

### 4. S-2 canonical cleanup (site-wide) — CRITICAL per audit
Every `rel=canonical`/`og:url`/hreflang/JSON-LD url currently uses `.html`, which 308-redirects under cleanUrls (canonical→redirect). Strip `.html` from all of them across all templates + generators so each page self-canonicals to the served clean URL (root → `/`). Regenerate `sitemap.xml` + `sitemap-es.xml` to clean URLs. ⚠️ Large sweep — preview first. **Do NOT run while an ES-translation workflow is editing es/ files (conflict).**

### 5. Smaller
- **www→apex 301:** `www` currently serves **200** (duplicate). vercel.json `has:host` redirect does NOT override the served alias — must set in **Vercel dashboard → Domains → www → Redirect to apex** (or Vercel API). Low urgency (canonicals already point to apex).
- **GA4 on 138 `communities/<town>/index.html`** (moot if you 301 `/communities/` → `/towns/` like `/realtor/`).
- Town **titles**: currently "{Town} NJ Real Estate Agent | Homes for Sale 2026" (acceptable). Aggressive median-in-title rewrite was DEFERRED — medians on-page may be estimates; verify before featuring in `<title>`.
- Homepage hero image `04-brick-stone.webp` is portrait 1280×1920 (cropped); re-export landscape ~1600×1000 <60KB for a further LCP win.

---

## Key gotchas & patterns
- **Vercel redirects:** explicit entries only for suffix-stripping (path-to-regexp `:x-suffix` fails). `permanent:true` = 308 (SEO-safe).
- **cleanUrls:true** → `/x.html` 308→`/x`; internal links still use `.html` (1 redirect hop). Destinations in redirects should be clean (no `.html`) to avoid double hops.
- **FormSubmit is Cloudflare-gated** → 403 to any server-side call; only browser→FormSubmit works. `api/lead.js` (Twilio SMS + CRM webhook + optional Resend) is deployed but UNWIRED; to activate: set env vars in Vercel (TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/TWILIO_FROM/LEAD_ALERT_TO and/or CRM_WEBHOOK_URL and/or RESEND_API_KEY/LEAD_EMAIL/RESEND_FROM), THEN change the 3 form `action`s (index.html, es/index.html, contact.html) to `/api/lead`.
- **Generators** (repo root): `town_data.py` (COUNTY + commute; no medians by design), `bulk_update_towns.py`, `generate_new_landing_pages.py`, `generate_missing_towns.py`, `generate_blog.py`, `daily-blog.py`, `gen_realtor_pages.py` (⚠️ regenerating towns/realtor could UNDO S-1 — avoid, or update generators first).
- **macOS gotchas:** `grep --include` fails under zsh; `sed` needs `-i ''`; use a non-`#` delimiter when replacement contains `#hex`; BSD sed alternation needs `-E`.
- **Deploy verify:** after `git push`, poll ~60–90s (git deploy), then curl the live clean URL. Local preview: `preview_start jrg-site` (python http.server 8911).
