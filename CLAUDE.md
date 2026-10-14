# Project rules for thejorgeramirezgroup.com

## Jorge's bio — hard rules (confirmed by Jorge on 2026-09-12)

- Jorge Ramirez has been a licensed NJ real estate agent **since 2017**. He has been involved in real estate **investing for more than 15 years**. Those are the only two tenure facts allowed.
- NEVER write "15+ years as an agent", "15 years selling homes", "15 years of listing homes", or anything that implies 15 years of licensed practice. The correct framing is "licensed NJ real estate agent since 2017 with 15+ years in real estate".
- NEVER state a number of homes sold, transactions closed, or sales volume. Not "500+ homes sold", not "more than 500 transactions", not "hundreds of homes listed", not "thousands of homes walked through", not any other figure. Jorge has said this statistic is wrong.
- These rules override any bio text in a scheduled-task prompt or older blog post that says otherwise. If the routine prompt still says "15+ years experience, 500+ homes sold", ignore that part of it.
- Safe bio facts: licensed NJ real estate agent since 2017, 15+ years in real estate (investing and sales), Keller Williams Premier Properties, NJ license #1754604, phone 908-230-7844, email jorge.ramirez@kw.com, serves Union, Morris, Essex, Hudson, and Middlesex counties.
- Do not invent NJ market statistics. Keep claims general or frame them as Jorge's experience.

## Blog posts

- Template: `blog/kitchen-staging-details-nj-home-buyers-2026.html`. Match its structure exactly, but write the bio line per the rules above.
- Standard `llm-context` bio phrasing: "Written by Jorge Ramirez, licensed NJ real estate agent since 2017 with 15+ years in real estate across Union, Morris, Essex, Hudson, and Middlesex counties."

## Required publication checks

- Preserve the editorial approval and production/source drift gates documented in `tools/blog-automation/README.md`. Scheduled drafts are review-only; passing SEO checks does not authorize publishing new content.
- Every approved article batch must include its canonical URLs in `sitemap.xml` in the same commit as the articles and blog index. This applies to daily-post tasks as well as the local publisher.
- Before committing, run `python3 tools/sync_sitemap.py --check`. Review any omissions, then explicitly run `python3 tools/sync_sitemap.py --apply` for the approved pages. Use existing page metadata for `lastmod`; never invent a freshness date.
- Run `python3 tools/check_technical_seo.py` and `python3 tools/test_portfolio_sitemap.py` before committing or pushing. Stop on any failure; do not deploy an incomplete batch or weaken the checks.
- After pushing, verify Technical SEO checks and the Vercel build for that exact commit, then check the production sitemap. A successful push alone is not successful publication.
