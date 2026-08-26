# Sitemap `lastmod` maintenance

Use `tools/update_sitemap_lastmod.py` after meaningful HTML content changes.
The caller must provide both the changed HTML paths and the editorial date;
the utility never guesses a date from a filesystem timestamp.

## Preview and check

Replace `YYYY-MM-DD` with the verified content-change date and list only HTML
files changed in the work being shipped:

```sh
python3 tools/update_sitemap_lastmod.py --check --date YYYY-MM-DD index.html towns/example.html es/blog/index.html
```

`--dry-run` is an alias for `--check`. Neither mode writes. A check exits with
status 1 when an eligible sitemap entry would change, is missing, is
ambiguous, or lacks an existing `<lastmod>` element; status 0 means no action
is required. Invalid dates and unsafe paths exit with status 2.

## Apply

After reviewing the preview, repeat the same explicit path list in apply mode:

```sh
python3 tools/update_sitemap_lastmod.py --apply --date YYYY-MM-DD index.html towns/example.html es/blog/index.html
```

The utility validates every input and parses every affected sitemap before it
writes anything. It then changes only the text of an existing `<lastmod>` for
an exact canonical URL match. Missing URLs and entries without `<lastmod>` are
reported and left unchanged; the utility does not create sitemap records.

## Route and indexability rules

- `index.html` maps to `/`.
- A directory index such as `blog/index.html` maps to `/blog`.
- `es/index.html` maps to `/es`, and all `/es` routes use `sitemap-es.xml`.
- Other files such as `towns/example.html` map to the clean route
  `/towns/example`; `.html` canonical URLs are rejected.
- A page must have exactly one HTTPS apex canonical matching its deployed
  route. `noindex`, meta-refresh, non-self-canonical, and exact Vercel redirect
  sources are reported and skipped.
- Absolute or relative input paths are allowed only when their resolved file
  remains inside the repository. Missing paths, non-HTML files, and symlink
  escapes are rejected before any sitemap can be written.

The two sitemap XML files retain their declaration, indentation, comments,
URL ordering, and all non-target text. Apply mode stages changed documents
before atomically replacing the originals.
