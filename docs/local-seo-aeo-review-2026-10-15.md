# Local SEO/AEO review — October 15, 2026

Local preparation only. Base: `a18a5a89` (PR #11 sitemap repair). No commit,
push, PR, deployment, publishing, external-account change, installation or form
submission was performed. Work is in a separate copy in task-9; the source
checkout at `../task/TheJorgeRamirezGroup2` was not edited.

## Prepared changes

- Added 4–6 month, 2–3 month and approximately 1 month **pre-listing** decision
  paths to `/sell-your-home`, with corresponding timeline and budget sections
  on the existing resources. These are preparation windows, not sale-duration
  promises. Linked the existing resources and three town guides; added no URLs.
- Added practical, answer-first seller preparation to Summit, Westfield and
  Chatham, using the official sources below. Chatham Borough and Township are
  explicitly separate, and the page does not transplant either process to the
  other municipality. No local statistics, transactions or case studies added.
- Rewrote the pets and living-room articles to remove universal buyer-behavior,
  exact-duration, price/return and cleaning-efficacy claims. The visible FAQs and
  FAQ schema agree. Existing routes, publication dates, authentic logos and
  brokerage identity remain. Updated the two blog index excerpts accordingly.
- Buyer-guide meta, Open Graph and Twitter descriptions now promise a path to
  verify current NJHMFA programs, matching the existing body. The maintained
  snippet manifest carries the same text. No assistance amounts were invented;
  this metadata clarification does not claim a newly reviewed program date.
- Nine significantly changed English pages have October 15 modification dates
  and sitemap lastmod values. Sitemap-index English child lastmod is October 15.
  The Spanish child is September 15, the recorded last change to sitemap-es.xml
  at `f630b01a`; Spanish pages and sitemap content were not changed. No blanket
  freshness update. The tax guide's September 30 revision and labeled 2025 data
  remain byte-identical to the source checkout.
- Existing renderers now apply `data/seller-planning-additions.json` through
  `tools/seller_planning_additions.py`. This retains the new sections and earlier
  maintained internal links when rendering the six affected pages. It fails on
  a missing/ambiguous insertion marker. Existing tests retain their assertions;
  only the expected modification dates for these changed pages were advanced.

## Official municipal sources checked October 15

- [Summit Zoning Certificates of Occupancy](https://www.cityofsummit.org/164/Zoning-Certificates-of-Occupancy): the published residential ZCO process; confirm property-specific application and timing with the City.
- [Summit Construction Office](https://www.cityofsummit.org/162/Code-Administration): the office to confirm permit/project documentation.
- [Westfield Building Department FAQ](https://www.westfieldnj.gov/faq.aspx?TID=44) and [Smoke Detector Application](https://www.westfieldnj.gov/2041/Smoke-Detector-Application): distinguish the stated lack of a home-sale CO/CCO requirement from fire-compliance inspection requirements. No fees or appointment times copied into the guide.
- [Chatham Borough residential CCO application](https://www.chathamborough.org/applications/156-continuing-certificate-of-occupancy-permit-residential-property-application-fillable-form/file): sale-specific permit and municipal-account checks. No precise processing promise reproduced.
- [Chatham Township Selling Your Home](https://chathamtownship.org/departments/public-safety/fire-prevention/selling-your-home/): Township fire-inspection application and scheduling source. Kept distinct from Borough requirements.

The new copy narrowly attributes local process information and directs the reader
to the responsible office. Original August regulatory/source-review dates are
retained, separately from the date of the new planning sections.

## Maplewood redirect review — proposal only

`/blog/neighborhoods-maplewood-nj` currently redirects to
`/counties/essex-county`. The quarantine manifest records it as a retired
`scaled-neighborhood-ranking` article. The risk-decision manifest deliberately
uses a stable non-town target independent of town quarantine, and existing
regression tests explicitly enforce that choice. The archive stub is noindex.

The now-maintained, self-canonical, indexable `/towns/maplewood` is a closer
geographic match and is the proposed replacement destination. It would remain an
official-record guide, not a restoration of neighborhood rankings or unsupported
claims. This patch leaves the redirect, archive and safeguards unchanged. A
follow-on redirect change must update the two manifests, Vercel redirect, archive
canonical/refresh/link and targeted regression contract together, verifying a
single-hop indexable destination. The mismatch is not proof of a cause of the
search decline.

## Entity review and owner facts

The homepage/town business ID is `/#agent` (The Jorge Ramirez Group). Jorge's
Person ID is `/#jorge-ramirez`; the existing identity tests pass. Some article
publishers use `/#organization` for the same team, while the blog index and some
legal articles use `/#brokerage` with `NOTUDES ENTERPRISES LLC` and alternate name
`Keller Williams Realty Premier Properties of Summit`. Person `worksFor`
references differ between the team and brokerage. Those entities can represent
different real-world roles; a blind merge would not establish correctness.

No legal name, logo, phone or entity relationship was changed. Before any broader
schema normalization, obtain a current brokerage/legal-entity source and confirm
which entity publishes the site; then consistently represent the team, person and
brokerage as distinct entities where appropriate.

Removed anecdotes are not verified client experience. Owner confirmation would
be needed before restoring the living-room claim about most Cranford/Scotch
Plains rooms Jorge walks through, the Westfield/Summit seller-regret narrative,
or the pets article's implied personal experience and precise showing duration.
The rewrites use conditional advice instead. Existing author attribution remains;
owner review of the revised advice is still needed before publication.

## Verification and limits

Passing checks:

- `tools/sync_sitemap.py --check`; `tools/check_technical_seo.py` (1,384 HTML
  files, 392 sitemap URLs); `tools/test_portfolio_sitemap.py` (2 tests).
- All 79 tests across 12 focused suites: sitemap synchronization, daily-review
  gate, sitemap-publication gate, lastmod updater/alignment, schema identity,
  indexable-town remediation, Search Console route recovery, first-time buyer
  guides, seller legal accuracy, high-value legal/timeline and the new planning
  contracts. The new contracts check marker failure behavior/idempotence,
  existing internal-link fragment targets and visible FAQ/schema agreement.
- Exact `vercel.json` build command in a disposable local copy passed. It removed
  the validator only from disposable output; the source validator remains.
- Nine edited content pages checked in Chrome at desktop and 390px mobile:
  readable main content, one H1, expected apex canonical and no horizontal
  overflow. Chatham desktop/mobile screenshots and browser-check JSON saved in
  the sibling `evidence/` directory. No GSC tab used and no forms submitted.
- Both sitemap URL sets are identical to the base: 265 English + 127 Spanish,
  392 total. Property-tax HTML is byte-identical. `git diff --check` passed.

Broader suites still fail on **confirmed pre-existing issues**. They have not
been weakened or hidden:

- Seller-service renderer check: `sell-rental-property-nj.html` drift. The base
  also had `sell-your-home.html` drift; that affected-page drift is now resolved.
- Seller-editorial renderer check: `blog/absentee-owner-nj-sell-rental-property.html`
  and `blog/downsizing-your-nj-home.html` drift. The
  base also had selling-costs drift, now resolved for the edited page.
- Authorship integrity: both authority profiles lack the date expected by the
  older test; 107 existing article files have wording rejected by that suite,
  including the standard author phrase mandated by CLAUDE.md. This is an
  existing editorial-policy conflict, not a reason to weaken the test or silently
  rewrite all articles.
- Priority-snippet suite: its old tax-title expectation differs from the genuine
  newer property-tax guide. Preserved the newer tax work as instructed.

Full logs, baseline-failure logs, browser checks and build evidence are outside
public source in `../evidence/`. No claim that the full test suite is green, that
these edits will reverse a search decline, or that production changed.

Publication remains blocked pending specific approval of the tested patch.

## Approved release review

Jorge explicitly approved pushing and deploying this batch and requested live
verification. This supersedes the local-only publication hold above.

Before release, the two revised articles were changed to identify The Jorge
Ramirez Group as publisher and explicitly label the guidance AI-assisted.
Unverified personal-authorship language and the BlogPosting personal-author
reference were removed; Jorge remains the named licensed professional contact.
No legal entity name, logo, brokerage relationship or verified credential changed.
This scoped correction follows the release instruction to exclude unsupported
claims; it intentionally does not repeat CLAUDE.md's standard personal-authorship
phrase. No other blog posts or the general blog template were changed.

The broader authorship test now flags 105 unchanged articles, down from 107 on
clean a18a5a89. There are zero introduced offenders and zero changed files still
flagged. Both authority-profile failures, the rental/absentee/downsizing renderer
drift and the old tax-snippet expectation reproduce on unchanged base files.
The full broader suite is not green, but none of its remaining failures affects
this batch's changed pages. No tests were weakened to hide those failures.

The 12 focused suites now pass 80 tests, including the new attribution regression
contract. The production/source inventory gate passes with 180 production blog
routes and zero pending source-only routes. The exact build, sitemap and technical
SEO checks pass after the final correction. This document records pre-release
acceptance; final commit, deployment and live checks are reported separately.
