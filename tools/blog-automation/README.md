# Daily SEO Blog Draft Automation

Creates one New Jersey real-estate draft for editorial review at 7:00 AM.
Scheduled runs never alter the public site, sitemap, git history, or production
deployment. An AI score is a drafting aid, not a substitute for factual, legal,
fair-housing, brand, source, and search-intent review.

## What it does each morning

1. Picks the next unused topic from `topics.json`.
2. Creates an AI-assisted draft in Jorge's calm, no-pressure voice.
3. Runs a second AI draft screen. Drafts below the configured threshold are
   skipped, but passing the screen does not publish anything.
4. Renders the page structure, metadata, and schema for inspection.
5. Saves `logs/REVIEW-<slug>.html` and stops. It does not touch `blog/`, the
   blog index, `sitemap.xml`, git, or Vercel.

The same topic remains next in the queue until a reviewed version is explicitly
published. Every run is recorded in `logs/daily_blog.log`.

## Editorial publication gate

An editor should verify all primary sources, dates, property-specific caveats,
fair-housing neutrality, legal and financial language, local search intent,
internal links, and visual consistency. Save the approved content as JSON, then
preview it:

```bash
cd ~/TheJorgeRamirezGroup2/tools/blog-automation
python3 daily_blog.py --content-file reviewed.json --slug reviewed-slug
```

Only an explicit reviewed-publication command can change the site:

```bash
python3 daily_blog.py --content-file reviewed.json --slug reviewed-slug --publish-reviewed
```

Use `--no-push` with that command when a local commit should be inspected before
remote publication:

```bash
python3 daily_blog.py --content-file reviewed.json --slug reviewed-slug --publish-reviewed --no-push
```

`--publish-reviewed` is rejected unless `--content-file` is present. Generated
content cannot turn on the publication flag by itself.

## Other controls

```bash
python3 daily_blog.py --pick        # show the next topic only
python3 daily_blog.py               # scheduled-style review draft
python3 daily_blog.py --dry-run     # review draft; no public-site changes
```

## Writing engine

The `engine` value in `config.json` may be `auto`, `claude`, or `ollama`.
Credentials belong only in the git-ignored local configuration. Regardless of
the engine, unattended output remains a review artifact.

## Schedule and files

The launch agent `~/Library/LaunchAgents/com.jrg.dailyblog.plist` runs the script
at 7:00 AM. Its no-argument command is intentionally review-only.

| File | Purpose |
|---|---|
| `daily_blog.py` | Draft and explicit reviewed-publication workflow |
| `config.json` | Local engine settings and credentials; git-ignored |
| `topics.json` | Draft topic queue |
| `template_source.html` | Page skeleton used for rendered review copies |
| `state.json` | Tracks explicitly published pages |
| `logs/` | Review copies and run logs; git-ignored |

## Safety contract

- Scheduled runs cannot change indexable pages, sitemaps, git history, or
  production.
- Passing an AI draft score never authorizes publication.
- The assembled output is checked for the prohibited personal phone number.
- `ai-content-declaration` remains `ai-assisted`.
- Only a human-reviewed content file with `--publish-reviewed` may enter the
  public publication path.
