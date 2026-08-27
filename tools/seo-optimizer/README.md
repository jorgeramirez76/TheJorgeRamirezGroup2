# SEO Doctor: local metadata verifier

SEO Doctor is **read-only by default**. It inventories local HTML metadata and
prints JSON to standard output. It does not contact Google Search Console or any
other service, save a report, refresh credentials, alter the repository, or
message anyone.

```bash
python3 tools/seo-optimizer/seo_daily.py
python3 tools/seo-optimizer/seo_daily.py --check
```

Both commands perform the same local inventory. The output reports HTML-file,
indexable-file, retired-file, and missing-metadata counts. Redirect and
intentional `noindex` pages are classified separately and are never candidates
for a metadata change.

## Explicit local apply mode

The only write path accepts an **explicit local metadata plan**. A plan must:

- use schema version `1`;
- name each repository-relative `.html` target;
- include the exact current SHA-256 for every target;
- contain only allowlisted missing metadata fields; and
- contain no more than ten files.

Example plan:

```json
{
  "version": 1,
  "changes": [
    {
      "path": "reviewed-page.html",
      "sha256": "replace-with-the-exact-64-character-lowercase-hash",
      "metadata": {
        "description": "A reviewed description for this exact page.",
        "twitter:card": "summary_large_image"
      }
    }
  ]
}
```

After an owner reviews that exact plan and current file hash, local application
requires both flags and the exact confirmation phrase:

```bash
python3 tools/seo-optimizer/seo_daily.py \
  --apply-plan /absolute/path/to/reviewed-plan.json \
  --owner-approval I_APPROVE_THIS_LOCAL_SEO_METADATA_PLAN
```

The apply mode rejects changed hashes, existing fields, markup in values,
non-HTML targets, paths outside the repository, fallback pages, redirects, and
intentional `noindex` pages. It only adds the reviewed fields before `</head>`.

## Safety boundary

This utility never commits, pulls, pushes, deploys, emails, or submits URLs or
sitemaps. It has no network, mail, credential-refresh, Git, deployment, or
scheduling code. Any resulting local diff must be reviewed and tested through
the repository's normal human-controlled workflow.
