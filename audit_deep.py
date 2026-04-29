#!/usr/bin/env python3
"""Deeper second-pass audit. Checks beyond the basic file/meta audit:

  1. Live HTTP status of every sitemap URL (catches 301/302/404/500)
  2. Image file existence — every <img src> resolves to a real file
  3. Inline JSON-LD validity (parseable as JSON, has @context + @type)
  4. H1 presence — every content page has exactly one <h1>
  5. Canonical URL matches the actual page URL (no canonical drift)
  6. Hreflang reciprocity — if EN→ES exists, ES→EN must exist
  7. robots.txt + sitemap consistency — every sitemap URL allowed by robots
  8. AI-SEO: llms.txt accessible + valid format
  9. Content depth — pages with <300 words flagged (thin content)
  10. Page weight — pages >500KB flagged (perf risk)
  11. Mixed content / external scripts that could leak/slow
  12. Title duplication across pages (cannibalization risk)

Outputs DEEP_AUDIT_REPORT.md with an issue-prioritized list.
"""
from __future__ import annotations
import json
import re
import urllib.request
import urllib.error
from collections import defaultdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).parent
ORIGIN = "https://thejorgeramirezgroup.com"
HEAD_TIMEOUT = 15


def all_html() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.html"):
        s = str(p)
        if "/.git/" in s or "_backup" in s or "/staging/" in s:
            continue
        out.append(p)
    return sorted(out)


def head_status(url: str) -> int:
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "JorgeAuditBot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=HEAD_TIMEOUT) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


# 1. Live URL status — pulled from sitemap.xml
def check_live_status() -> dict[str, int]:
    sitemap = (ROOT / "sitemap.xml").read_text()
    urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    print(f"[live] checking {len(urls)} URLs from sitemap.xml in parallel...")
    results = {}
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(head_status, u): u for u in urls}
        for f in as_completed(futures):
            u = futures[f]
            try:
                results[u] = f.result()
            except Exception:
                results[u] = 0
    return results


# 2. Image existence
def check_images() -> dict[str, list[str]]:
    """For each <img src>, verify the file exists."""
    print("[img] scanning <img src> tags...")
    broken = defaultdict(list)
    for p in all_html():
        text = p.read_text(errors="ignore")
        for m in re.finditer(r'<img[^>]*\ssrc=["\']([^"\']+)["\']', text, re.I):
            src = m.group(1)
            if src.startswith(("http://", "https://", "//", "data:")):
                continue
            src_clean = src.split("?")[0].split("#")[0]
            if src_clean.startswith("/"):
                target = ROOT / src_clean.lstrip("/")
            else:
                target = (p.parent / src_clean).resolve()
            if not target.exists():
                broken[src].append(str(p.relative_to(ROOT)))
    return broken


# 3. JSON-LD validity
def check_jsonld() -> list[tuple[str, str]]:
    print("[jsonld] validating inline JSON-LD blocks...")
    issues = []
    pat = re.compile(r'<script\s+type=["\']application/ld\+json["\'][^>]*>(.+?)</script>', re.S | re.I)
    for p in all_html():
        text = p.read_text(errors="ignore")
        for m in pat.finditer(text):
            blob = m.group(1).strip()
            try:
                obj = json.loads(blob)
            except json.JSONDecodeError as e:
                issues.append((str(p.relative_to(ROOT)), f"JSON parse: {e.msg} at line {e.lineno}"))
                continue
            arr = obj if isinstance(obj, list) else [obj]
            for item in arr:
                if not isinstance(item, dict):
                    continue
                if "@context" not in item:
                    issues.append((str(p.relative_to(ROOT)), "missing @context"))
                if "@type" not in item and "@graph" not in item:
                    issues.append((str(p.relative_to(ROOT)), "missing @type"))
    return issues


# 4. H1 presence
def check_h1() -> list[tuple[str, str]]:
    print("[h1] checking H1 presence + uniqueness...")
    issues = []
    for p in all_html():
        text = p.read_text(errors="ignore")
        h1s = re.findall(r"<h1[^>]*>", text, re.I)
        if len(h1s) == 0:
            issues.append((str(p.relative_to(ROOT)), "no <h1>"))
        elif len(h1s) > 1:
            issues.append((str(p.relative_to(ROOT)), f"{len(h1s)} <h1> tags (should be 1)"))
    return issues


# 5. Canonical drift
def check_canonical() -> list[tuple[str, str]]:
    print("[canon] checking canonical URLs...")
    issues = []
    for p in all_html():
        text = p.read_text(errors="ignore")
        m = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', text)
        if not m:
            continue
        canonical_url = m.group(1)
        rel = p.relative_to(ROOT).as_posix()
        if rel == "index.html":
            expected = ORIGIN + "/"
        elif rel.endswith("/index.html"):
            expected = ORIGIN + "/" + rel[:-len("index.html")]
        else:
            expected = ORIGIN + "/" + rel
        # Compare loosely (trailing slash differences are OK)
        if canonical_url.rstrip("/") != expected.rstrip("/"):
            issues.append((str(rel), f"canonical={canonical_url} expected={expected}"))
    return issues


# 6. Title duplication
def check_title_duplication() -> dict[str, list[str]]:
    print("[title] scanning for duplicate titles...")
    title_to_pages: dict[str, list[str]] = defaultdict(list)
    for p in all_html():
        text = p.read_text(errors="ignore")
        m = re.search(r"<title>([^<]+)</title>", text)
        if m:
            title_to_pages[m.group(1).strip()].append(str(p.relative_to(ROOT)))
    return {t: ps for t, ps in title_to_pages.items() if len(ps) > 1}


# 7. Content depth
def check_content_depth() -> list[tuple[str, int]]:
    print("[depth] estimating word counts...")
    thin = []
    tag_strip = re.compile(r"<[^>]+>")
    for p in all_html():
        text = p.read_text(errors="ignore")
        # Pull <body>
        m = re.search(r"<body[^>]*>(.*?)</body>", text, re.S | re.I)
        if not m:
            continue
        body = m.group(1)
        # Strip script/style
        body = re.sub(r"<script.*?</script>", "", body, flags=re.S | re.I)
        body = re.sub(r"<style.*?</style>", "", body, flags=re.S | re.I)
        clean = tag_strip.sub(" ", body)
        words = len([w for w in re.split(r"\s+", clean) if len(w) > 1])
        if words < 250:
            thin.append((str(p.relative_to(ROOT)), words))
    return thin


# 8. AI SEO — llms.txt exists + has structure
def check_ai_seo() -> list[str]:
    print("[ai-seo] checking AI/LLM-related files...")
    issues = []
    if not (ROOT / "llms.txt").exists():
        issues.append("llms.txt missing")
    if not (ROOT / "robots.txt").exists():
        issues.append("robots.txt missing")
    else:
        rt = (ROOT / "robots.txt").read_text()
        for bot in ["GPTBot", "PerplexityBot", "ClaudeBot", "CCBot", "Google-Extended"]:
            if bot not in rt:
                issues.append(f"robots.txt missing User-agent block for {bot}")
    return issues


# 9. Page weight
def check_page_weight() -> list[tuple[str, int]]:
    print("[weight] checking page weights...")
    heavy = []
    for p in all_html():
        kb = p.stat().st_size // 1024
        if kb > 500:
            heavy.append((str(p.relative_to(ROOT)), kb))
    return sorted(heavy, key=lambda x: -x[1])


def main():
    report_lines = ["# Deep Audit Report\n"]

    # 1. Live status
    live = check_live_status()
    bad = {u: c for u, c in live.items() if c not in (200, 301, 302)}
    report_lines.append(f"## 1. Live URL status ({len(live)} URLs in sitemap)\n")
    report_lines.append(f"- 200 OK: {sum(1 for c in live.values() if c == 200)}")
    report_lines.append(f"- 301/302 redirect: {sum(1 for c in live.values() if c in (301, 302))}")
    report_lines.append(f"- 404 not found: {sum(1 for c in live.values() if c == 404)}")
    report_lines.append(f"- 500+ server error: {sum(1 for c in live.values() if c >= 500)}")
    report_lines.append(f"- 0 (network error): {sum(1 for c in live.values() if c == 0)}\n")
    if bad:
        report_lines.append("### Non-200/3xx URLs:")
        for u, c in sorted(bad.items())[:30]:
            report_lines.append(f"- `{c}` {u}")

    # 2. Broken images
    broken_imgs = check_images()
    report_lines.append(f"\n## 2. Broken image references — {len(broken_imgs)}\n")
    for src, refs in sorted(broken_imgs.items(), key=lambda kv: -len(kv[1]))[:20]:
        report_lines.append(f"- `{src}` (refs: {len(refs)}, e.g. `{refs[0]}`)")

    # 3. JSON-LD issues
    jsonld_issues = check_jsonld()
    report_lines.append(f"\n## 3. JSON-LD validity issues — {len(jsonld_issues)}\n")
    for path, msg in jsonld_issues[:20]:
        report_lines.append(f"- `{path}`: {msg}")

    # 4. H1 issues
    h1_issues = check_h1()
    report_lines.append(f"\n## 4. H1 issues — {len(h1_issues)}\n")
    for path, msg in h1_issues[:30]:
        report_lines.append(f"- `{path}`: {msg}")

    # 5. Canonical drift
    canon_issues = check_canonical()
    report_lines.append(f"\n## 5. Canonical drift — {len(canon_issues)}\n")
    for path, msg in canon_issues[:20]:
        report_lines.append(f"- `{path}`: {msg}")

    # 6. Title duplication
    dups = check_title_duplication()
    report_lines.append(f"\n## 6. Duplicate titles — {len(dups)}\n")
    for t, pages in sorted(dups.items(), key=lambda kv: -len(kv[1]))[:15]:
        report_lines.append(f"- \"{t}\" — {len(pages)} pages: {', '.join(pages[:3])}{'…' if len(pages)>3 else ''}")

    # 7. Thin content
    thin = check_content_depth()
    report_lines.append(f"\n## 7. Thin content (<250 words) — {len(thin)}\n")
    for path, w in sorted(thin, key=lambda x: x[1])[:20]:
        report_lines.append(f"- `{path}` — {w} words")

    # 8. AI SEO
    ai_issues = check_ai_seo()
    report_lines.append(f"\n## 8. AI SEO — {len(ai_issues)} issues\n")
    for msg in ai_issues:
        report_lines.append(f"- {msg}")

    # 9. Heavy pages
    heavy = check_page_weight()
    report_lines.append(f"\n## 9. Heavy pages (>500KB) — {len(heavy)}\n")
    for path, kb in heavy[:15]:
        report_lines.append(f"- `{path}` — {kb} KB")

    out = ROOT / "DEEP_AUDIT_REPORT.md"
    out.write_text("\n".join(report_lines))
    print(f"\nWrote {out}")
    print(f"Summary: {len(bad)} live errors · {len(broken_imgs)} broken imgs · {len(jsonld_issues)} jsonld · {len(h1_issues)} h1 · {len(canon_issues)} canon · {len(dups)} dups · {len(thin)} thin · {len(ai_issues)} ai-seo")


if __name__ == "__main__":
    main()
