# Daily SEO Blog Automation

Publishes one new, SEO-optimized New Jersey real-estate blog post to the site
**every day at 7:00 AM**, fully automatically, with an AI quality gate so weak
copy never goes live.

## What it does each morning

1. **Picks the next topic** from `topics.json` — uncovered NJ *town buying
   guides* first (best long-tail local SEO), then evergreen topical articles.
   Anything already on the site is skipped automatically.
2. **Writes a ~1,000-word post** in Jorge's reverse-selling (Mulrenin) voice —
   honest, no-pressure, genuinely useful. No fabricated statistics. Only the
   public phone number `908-317-3227`.
3. **Runs an AI quality gate** — a second pass scores the draft 0–100. If it
   can't clear the bar (`quality_threshold`, default 80), the post is
   **skipped, not published**, and retried next run. This is what protects your
   rankings from Google's scaled-content-abuse / helpful-content penalties.
4. **Assembles a fully SEO-structured page** matching the site template:
   canonical + hreflang, Open Graph, geo tags, an AI "Quick answer" block, and
   **Article + FAQ + Breadcrumb JSON-LD** schema.
5. **Wires it in** — prepends a card to `blog/index.html` and adds a `<url>` to
   `sitemap.xml` (fresh `lastmod`).
6. **Commits & pushes** to `main` → **Vercel auto-deploys**. Live in ~1 minute.

Every run is logged to `logs/daily_blog.log`.

## Writing engine

Set in `config.json` → `engine`:

| value | behavior |
|-------|----------|
| `auto` (default) | Try Claude, fall back to local Ollama. |
| `claude` | Force Claude quality (best copy). |
| `ollama` | Local model only — free, offline, weaker copy. |

### One-time upgrade to Claude quality (recommended, 30 seconds)

The desktop Claude login token expires daily, so an unattended 7 AM job can't
rely on it. For Claude-quality writing on autopilot, mint a long-lived token
**once**:

```bash
claude setup-token          # opens browser, ~1-year token
```

Copy the token it prints (`sk-ant-oat...`) into `config.json`:

```json
"claude_oauth_token": "sk-ant-oat-...."
```

`config.json` is **git-ignored**, so the token never leaves your Mac. Until you
do this, the job runs on the local Ollama model (`qwen3.6:35b`) and the quality
gate simply skips any post that isn't good enough — the site is never at risk.

## Manual controls

```bash
cd ~/TheJorgeRamirezGroup2/tools/blog-automation

python3 daily_blog.py --pick        # show the next topic, don't write
python3 daily_blog.py --dry-run     # generate + gate, write nothing (preview in logs/)
python3 daily_blog.py --no-push     # write & commit locally, don't push
python3 daily_blog.py               # full run (what the 7 AM job does)
```

## The schedule (launchd)

Installed as `~/Library/LaunchAgents/com.jrg.dailyblog.plist` (runs 7 AM daily,
survives reboots — loads at login).

```bash
launchctl load  ~/Library/LaunchAgents/com.jrg.dailyblog.plist   # enable
launchctl unload ~/Library/LaunchAgents/com.jrg.dailyblog.plist  # disable
launchctl start com.jrg.dailyblog                                # run now (test)
```

## Files

| file | purpose |
|------|---------|
| `daily_blog.py` | the automation |
| `config.json` | engine + token + threshold (**git-ignored** — holds the token) |
| `config.example.json` | template for `config.json` |
| `topics.json` | town + article queue (add more anytime) |
| `template_source.html` | frozen SEO page skeleton (from a top existing post) |
| `state.json` | tracks what's been published (guards against double-posting) |
| `logs/` | run logs (git-ignored) |

## Adding topics

Edit `topics.json`. `towns[]` become "Buying a Home in {name}, NJ" guides;
`articles[]` are evergreen pieces. The queue can hold months of runway — the
picker just walks it and skips anything already published.

## Safety

- Never emits Jorge's banned personal number; the assembled page is re-checked
  for it before writing, and a repo GitHub Action scrubs it on push as a
  backstop.
- `ai-content-declaration` meta is set honestly to `ai-assisted`.
- The quality gate + "one successful post per day" guard prevent spammy output.
