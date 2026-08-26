# Daily SEO Doctor

Reads **Google Search Console** every morning, **auto-fixes the safe stuff**,
**queues risky changes for your approval**, and **emails you a report** — for
thejorgeramirezgroup.com.

## Core principle

Never blindly rewrite a page that already ranks. Additive, mechanical fixes are
automatic. Anything that could *move* a ranking (title/meta/content on a page
that ranks) is **proposed, not applied**, and a page we change is never touched
again for `cooldown_days` so the change can be measured first.

## What it does each morning (8:00 AM)

1. **Pulls GSC** (auto-refreshes + writes back the token): 28-day clicks /
   impressions / CTR / position, per-page + per-query, and day-over-day deltas.
2. **Checks index health**: a rotating daily sample of URLs via the URL
   Inspection API, plus sitemap submission status.
3. **Audits every page** for missing meta description / canonical / viewport /
   Open Graph / Twitter card / JSON-LD. **Redirect stubs and `noindex` pages
   are skipped** (they're intentional — 1,000+ on this site).
4. **Queues new blog pages for sitemap review** — self-canonical pages are not
   automatically submitted because canonical markup alone does not establish
   editorial quality, topical fit, or factual accuracy. After review, run
   `python3 tools/sync_sitemap.py --apply` from the repository root.
5. **Auto-fixes the safe class** (additive only), capped at
   `max_auto_edits_per_day`, each committed with a clear diff, then pushed →
   Vercel deploys.
6. **Queues risky proposals** — high-impression / low-CTR pages get a suggested
   better title (Claude-written when the token is set; otherwise only
   high-confidence changes like refreshing a stale year). These are **never
   auto-applied**.
7. **Emails the report**: what Google shows, what was fixed, what needs your
   call, and the biggest CTR opportunities.

## What it can and can't see

The public GSC API exposes **search performance, per-URL index status, and
sitemaps** — all used here. It does **not** expose the web-UI "Page Indexing /
Coverage", "Core Web Vitals", or "Enhancements" dashboards (Google offers no
API for those). URL Inspection reproduces most coverage insight per-URL.

## Approving risky changes

The daily email lists each proposal. To apply:

```bash
python3 seo_daily.py --apply-proposals          # apply all queued
python3 seo_daily.py --apply-proposals --id ID  # apply one
```

…or just tell Claude "apply today's SEO proposals".

## Two one-time setup steps (both optional, both improve quality)

1. **Email delivery** — needed for the morning report. Copy `mail.env.example`
   to `mail.env` and add a Gmail **App Password**
   (https://myaccount.google.com/apppasswords, 60 seconds). Until then the
   report is saved to `reports/` each day but not emailed.
2. **Claude-written titles** — set `claude_oauth_token` in
   `../blog-automation/config.json` (via `claude setup-token`). Then proposed
   title rewrites are AI-written instead of heuristic. Shared with the blog
   automation — set it once.

## Schedule

`~/Library/LaunchAgents/com.jrg.seo-optimizer.plist` — 8:00 AM daily
(staggered after the 7 AM blog job), reboot-proof.

```bash
launchctl load  ~/Library/LaunchAgents/com.jrg.seo-optimizer.plist
launchctl start com.jrg.seo-optimizer          # run now
```

## Manual controls

```bash
python3 seo_daily.py            # full run (what the 8am job does)
python3 seo_daily.py --dry-run  # analyze + report, change/commit nothing
python3 seo_daily.py --no-push  # apply safe fixes locally, don't push
python3 seo_daily.py --no-email # skip the email
```

## Files

| file | purpose |
|------|---------|
| `seo_daily.py` | the automation |
| `config.json` | thresholds, cooldown, caps, report email |
| `mail.env` | SMTP app password (git-ignored; from `mail.env.example`) |
| `state/` | daily snapshots, proposals, change cooldown (git-ignored) |
| `reports/` | daily HTML reports (git-ignored) |

## Safety

- Only skips or **adds** tags — never rewrites an existing title/content
  automatically.
- Redirect/`noindex` pages are never modified.
- `cooldown_days` prevents thrashing a page we already changed.
- Every change goes through git (diff-reviewable, revertible); pushes use
  `pull --rebase` so the two daily jobs never collide.
- Banned personal number is stripped from any inserted tag; a repo GitHub
  Action scrubs it on push as a backstop.
