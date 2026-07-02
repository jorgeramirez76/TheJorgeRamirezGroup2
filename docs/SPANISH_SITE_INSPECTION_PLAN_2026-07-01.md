# Spanish Site Inspection + Fix Plan — thejorgeramirezgroup.com

## Inspection summary

Live pages inspected:
- `/` — English homepage loads cleanly and links to `/es/`.
- `/es/` — Spanish homepage loads cleanly with no browser console errors.
- Source repo: `/Users/teddy/TheJorgeRamirezGroup2` on `main`.

Key findings:
1. **Spanish homepage has visible count inconsistencies.** The hero stats say `138 comunidades`, but the communities section says `103 Comunidades` and a card says `120 Pueblos`.
2. **Top-level Spanish pages still contain machine-translation fragments in titles/meta and visible copy**, including examples like `Your Listado Expired`, `First-Time Comprador`, `Free NJ Valoración de Casa`, `Sell Mi Casa Fast`, `Calculator`, and `Buyer Costs`.
3. **Many generated Spanish town pages still contain English tokens and mixed-language phrases**, especially in meta/schema and repeated modules: `Looking to`, `Expert guidance`, `buyer`, `seller`, `home`, `market`, `schools`, `commute`, `top-rated`, etc.
4. **Existing uncommitted work is present in 42 `es/towns/*.html` files.** Those changes appear to be Claude Code's current Spanish-translation cleanup. Do not overwrite them; only apply additive, targeted corrections.
5. **Runtime status:** Browser console on `/es/` is clean. No mojibake was found in Spanish HTML (`Ã`, `Â`, `�` patterns absent).

## Execution plan with triple verification gates

### Task 1 — Fix Spanish homepage consistency and obvious visible copy defects
Acceptance criteria:
- `/es/` consistently says `138` for community/town coverage.
- No homepage-visible `103 Comunidades` or `120 Pueblos` remain.
- JSON-LD remains valid.

Verification, 3x before moving on:
1. Static grep for the bad phrases returns zero.
2. JSON-LD blocks in `es/index.html` parse successfully.
3. Browser reload of `/es/` shows the corrected text and no console errors.

### Task 2 — Fix top-level Spanish page titles/meta with obvious broken mixed-language phrases
Acceptance criteria:
- Top-level Spanish titles no longer contain known bad fragments such as `Your Listado`, `First-Time Comprador`, `Free NJ`, `What Is Mi Casa`, `Sell Mi Casa Fast`, `Calculator`, `Buyer Costs`, `Why Choose Jorge`.
- Changes are targeted and do not touch URL paths, hrefs, canonical links, or schema keys.

Verification, 3x before moving on:
1. Static scan for known bad title/meta fragments returns zero or only allowed proper nouns.
2. HTML parse / JSON-LD parse passes for edited files.
3. Browser spot-check of priority pages (`/es/sell-your-home.html`, `/es/buy-a-home.html`, `/es/home-valuation.html`, `/es/expired-listing-help.html`) shows no console errors.

### Task 3 — Add a reusable Spanish quality audit/fix workflow for generated pages
Acceptance criteria:
- Add an audit script that ranks Spanish pages by remaining English/mixed-language tokens.
- Add a targeted idempotent cleanup script for known repeated machine-translation errors.
- Preserve Claude Code's current uncommitted changes; no broad regeneration.

Verification, 3x before moving on:
1. Run audit before/after and confirm the top repeated known-bad tokens decrease.
2. `git diff --check` passes.
3. Re-run the cleanup script and confirm it is idempotent or produces zero additional changes.

### Task 4 — Batch-fix generated Spanish town-page leftovers safely
Acceptance criteria:
- Remove the highest-frequency English leftovers from `es/towns/*.html` without changing links/URLs.
- Keep market-specific town names, `NJ`, `NYC`, Zillow, Keller Williams, and legal identifiers intact.

Verification, 3x before moving on:
1. Audit count for town-page known-bad patterns drops materially.
2. Sample diffs from already-modified town pages show only translation/copy improvements, not structure damage.
3. HTML/JSON-LD validation passes on a representative sample of town pages.

### Task 5 — Final whole-site verification package
Acceptance criteria:
- Produce a final Spanish audit summary for Claude Code/Jorge.
- Confirm browser runtime is clean on the Spanish homepage and priority pages.
- Confirm no syntax/HTML/JSON-LD regressions were introduced.

Verification, 3x:
1. Static audit summary generated.
2. Browser console checks clean for sampled pages.
3. `git diff --check` plus validation script pass.
