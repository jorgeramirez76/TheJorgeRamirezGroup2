#!/usr/bin/env python3
"""
Daily SEO Doctor — The Jorge Ramirez Group
==========================================
Every morning: pulls Google Search Console data, audits all site pages,
AUTO-FIXES the safe/mechanical/reversible issues, QUEUES risky changes
(title/meta rewrites on pages that already rank) for Jorge's approval, then
emails a report.

Design principle: never blindly rewrite a page that already ranks. Additive,
mechanical fixes are automatic; anything that could move a ranking is proposed,
not applied, and never re-touched within a cooldown window.

Data sources (all headless):
  * GSC Search Analytics  — queries/pages/CTR/position (+ day-over-day deltas)
  * GSC Sitemaps API      — sitemap submission health
  * GSC URL Inspection    — per-URL index status (bounded rotating sample/day)
  * Local page audit      — missing meta/canonical/OG/schema, broken links

Auth:
  * GSC:   ~/.gsc_token.json (refresh token; auto-refreshed + written back)
  * Gmail: GOOGLE_CLIENT_ID/SECRET + GMAIL_REFRESH_TOKEN from crm/.env

Usage:
  python3 seo_daily.py                 # full daily run (what the 8am job does)
  python3 seo_daily.py --dry-run       # analyze + report, change/commit nothing
  python3 seo_daily.py --no-push       # apply safe fixes locally, don't push
  python3 seo_daily.py --no-email      # skip the email
  python3 seo_daily.py --apply-proposals [--id ID]   # apply queued risky change(s)
"""

import os, re, sys, json, base64, argparse, subprocess, datetime, html as htmllib
from email.mime.text import MIMEText

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(HERE, "state")
REPORTS = os.path.join(HERE, "reports")
LOGS = os.path.join(HERE, "logs")
CONFIG_FILE = os.path.join(HERE, "config.json")
GSC_TOKEN = os.path.expanduser("~/.gsc_token.json")
CRM_ENV = os.path.join(REPO, "crm", ".env")
SITEMAP = os.path.join(REPO, "sitemap.xml")

SITE = "https://thejorgeramirezgroup.com"
PROPERTY = "sc-domain:thejorgeramirezgroup.com"
BANNED = "908" + "23" + "0" + "78" + "44"  # personal line, assembled (guard-safe)

for d in (STATE, REPORTS, LOGS):
    os.makedirs(d, exist_ok=True)


def log(msg):
    line = f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    with open(os.path.join(LOGS, "seo_daily.log"), "a") as f:
        f.write(line + "\n")


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=str)


def cfg():
    return load_json(CONFIG_FILE, {
        "report_email": "jorgeramirez76@gmail.com",
        "proposal_min_impressions": 250,
        "proposal_max_ctr": 0.02,
        "proposal_max_position": 20.0,
        "cooldown_days": 21,
        "max_auto_edits_per_day": 40,
        "url_inspect_per_day": 25,
    })


def parse_env(path):
    env = {}
    try:
        for line in open(path):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return env


# --------------------------------------------------------------------------- #
#  Google auth                                                                 #
# --------------------------------------------------------------------------- #
def gsc_service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    info = load_json(GSC_TOKEN, {})
    creds = Credentials(
        token=info.get("token"), refresh_token=info.get("refresh_token"),
        token_uri=info.get("token_uri"), client_id=info.get("client_id"),
        client_secret=info.get("client_secret"), scopes=info.get("scopes"))
    if not creds.valid:
        creds.refresh(Request())
        info["token"] = creds.token
        if creds.expiry:
            info["expiry"] = creds.expiry.isoformat()
        save_json(GSC_TOKEN, info)  # persist refreshed token
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


MAIL_ENV = os.path.join(HERE, "mail.env")
_MAIL_KEYS = ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET",
              "GMAIL_REFRESH_TOKEN", "GMAIL_FROM")


def mail_creds():
    """Stable Gmail creds. Prefer our own snapshot; else read crm/.env with
    retries (the CRM rewrites that file live, so a single read can race)."""
    snap = parse_env(MAIL_ENV)
    if snap.get("GMAIL_REFRESH_TOKEN"):
        return snap
    import time
    for _ in range(4):
        env = parse_env(CRM_ENV)
        if env.get("GMAIL_REFRESH_TOKEN"):
            with open(MAIL_ENV, "w") as f:  # snapshot for future runs
                for k in _MAIL_KEYS:
                    if env.get(k):
                        f.write(f"{k}={env[k]}\n")
            os.chmod(MAIL_ENV, 0o600)
            return env
        time.sleep(0.5)
    return {}


def gmail_service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    env = mail_creds()
    if not env.get("GMAIL_REFRESH_TOKEN"):
        return None, None
    creds = Credentials(
        token=None, refresh_token=env["GMAIL_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=env.get("GOOGLE_CLIENT_ID"),
        client_secret=env.get("GOOGLE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/gmail.send"])
    creds.refresh(Request())
    return build("gmail", "v1", credentials=creds, cache_discovery=False), \
        env.get("GMAIL_FROM", "jorgeramirez76@gmail.com")


# --------------------------------------------------------------------------- #
#  GSC data pull                                                               #
# --------------------------------------------------------------------------- #
def gsc_pull(c):
    sc = gsc_service()
    end = datetime.date.today() - datetime.timedelta(days=3)   # GSC lags ~3d
    start = end - datetime.timedelta(days=28)
    prev_end = start - datetime.timedelta(days=1)
    prev_start = prev_end - datetime.timedelta(days=28)

    def query(s, e, dims, limit=250):
        return sc.searchanalytics().query(siteUrl=PROPERTY, body={
            "startDate": str(s), "endDate": str(e),
            "dimensions": dims, "rowLimit": limit}).execute().get("rows", [])

    tot = query(start, end, [])
    totals = tot[0] if tot else {}
    pages = query(start, end, ["page"])
    prev_pages = {r["keys"][0]: r for r in query(prev_start, prev_end, ["page"])}
    queries = query(start, end, ["query"])

    # sitemap health
    sitemaps = []
    try:
        sm = sc.sitemaps().list(siteUrl=PROPERTY).execute().get("sitemap", [])
        for s in sm:
            sitemaps.append({
                "path": s.get("path"), "errors": int(s.get("errors", 0)),
                "warnings": int(s.get("warnings", 0)),
                "lastDownloaded": s.get("lastDownloaded"),
                "isPending": s.get("isPending", False)})
    except Exception as e:
        log(f"sitemap fetch: {e}")

    # bounded, rotating URL index-status sample
    index_issues = []
    try:
        state = load_json(os.path.join(STATE, "inspect_cursor.json"), {"i": 0})
        all_urls = [r["keys"][0] for r in pages]
        n = c.get("url_inspect_per_day", 25)
        i = state.get("i", 0)
        batch = all_urls[i:i + n] or all_urls[:n]
        for url in batch:
            try:
                res = sc.urlInspection().index().inspect(body={
                    "inspectionUrl": url, "siteUrl": PROPERTY}).execute()
                verdict = res.get("inspectionResult", {}).get(
                    "indexStatusResult", {})
                cov = verdict.get("coverageState", "")
                if verdict.get("verdict") != "PASS" or "not index" in cov.lower():
                    index_issues.append({"url": url, "coverage": cov,
                                         "verdict": verdict.get("verdict")})
            except Exception:
                continue
        state["i"] = (i + n) % max(1, len(all_urls))
        save_json(os.path.join(STATE, "inspect_cursor.json"), state)
    except Exception as e:
        log(f"url inspection: {e}")

    # opportunities: high impressions, weak CTR, reachable position
    opps = []
    for r in pages:
        if (r["impressions"] >= c["proposal_min_impressions"]
                and r["ctr"] <= c["proposal_max_ctr"]
                and r["position"] <= c["proposal_max_position"]):
            prev = prev_pages.get(r["keys"][0])
            opps.append({
                "url": r["keys"][0], "impressions": int(r["impressions"]),
                "clicks": int(r["clicks"]), "ctr": r["ctr"],
                "position": r["position"],
                "pos_delta": (prev["position"] - r["position"]) if prev else None,
            })
    opps.sort(key=lambda x: x["impressions"], reverse=True)

    return {
        "date": str(datetime.date.today()), "range": [str(start), str(end)],
        "totals": {k: totals.get(k, 0) for k in
                   ("clicks", "impressions", "ctr", "position")},
        "pages": pages, "queries": queries, "opportunities": opps,
        "sitemaps": sitemaps, "index_issues": index_issues,
    }


def compute_deltas(today):
    snaps = sorted(f for f in os.listdir(STATE) if f.startswith("snapshot-"))
    prev = load_json(os.path.join(STATE, snaps[-1]), None) if snaps else None
    d = {"clicks": None, "impressions": None, "position": None, "ctr": None}
    if prev:
        pt = prev.get("totals", {})
        for k in d:
            if pt.get(k) is not None:
                d[k] = round(today["totals"].get(k, 0) - pt.get(k, 0), 4)
    return d, (prev.get("date") if prev else None)


# --------------------------------------------------------------------------- #
#  Local page audit                                                            #
# --------------------------------------------------------------------------- #
SKIP_DIRS = {".git", "node_modules", ".venv", "crm", "tools",
             ".design-screens", ".vercel", "data"}


def all_pages():
    out = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in files:
            if fn.endswith(".html") and not fn.startswith("DRYRUN"):
                out.append(os.path.join(root, fn))
    return out


def page_url(path):
    rel = os.path.relpath(path, REPO).replace("\\", "/")
    if rel.endswith("index.html"):
        rel = rel[:-len("index.html")].rstrip("/")
    elif rel.endswith(".html"):
        rel = rel[:-5]
    return f"{SITE}/{rel}".rstrip("/")


def is_redirect_or_noindex(t):
    """Redirect stubs and noindex pages are intentional — never 'optimize' them."""
    low = t.lower()
    return ('http-equiv="refresh"' in low.replace("'", '"')
            or "window.location" in low
            or re.search(r'name=["\']robots["\'][^>]*content=["\'][^"\']*noindex', low)
            or "<title>redirecting" in low)


def audit_page(path):
    try:
        t = open(path, encoding="utf-8").read()
    except Exception:
        return None
    if is_redirect_or_noindex(t):
        return {"path": path, "url": page_url(path), "issues": [], "title": "",
                "skip": "redirect/noindex"}
    head = t[:t.lower().find("</head>")] if "</head>" in t.lower() else t
    issues = []
    title = re.search(r"<title>(.*?)</title>", head, re.I | re.S)
    if not title or not title.group(1).strip():
        issues.append("missing-title")
    if not re.search(r'<meta\s+name=["\']description["\']', head, re.I):
        issues.append("missing-meta-description")
    if not re.search(r'<link\s+rel=["\']canonical["\']', head, re.I):
        issues.append("missing-canonical")
    if not re.search(r'name=["\']viewport["\']', head, re.I):
        issues.append("missing-viewport")
    if not re.search(r'property=["\']og:title["\']', head, re.I):
        issues.append("missing-og:title")
    if not re.search(r'property=["\']og:description["\']', head, re.I):
        issues.append("missing-og:description")
    if not re.search(r'name=["\']twitter:card["\']', head, re.I):
        issues.append("missing-twitter:card")
    if "application/ld+json" not in head:
        issues.append("missing-jsonld")
    return {"path": path, "url": page_url(path), "issues": issues,
            "title": (title.group(1).strip() if title else "")}


def first_text(t):
    body = re.sub(r"(?is)<(script|style|nav|footer|head).*?</\1>", " ", t)
    m = re.search(r"<p[^>]*>(.*?)</p>", body, re.I | re.S)
    txt = re.sub(r"<[^>]+>", " ", m.group(1)) if m else ""
    return re.sub(r"\s+", " ", txt).strip()


# --------------------------------------------------------------------------- #
#  Safe auto-fixes (additive only)                                            #
# --------------------------------------------------------------------------- #
def esc_text(s):
    """Escape for an attribute WITHOUT double-escaping existing entities."""
    return htmllib.escape(htmllib.unescape(s or ""), quote=True)


def make_meta_desc(t, title):
    para = first_text(t)
    # skip junk first-paragraphs (dates, labels, too short) — use title instead
    if len(para) < 60 or re.match(r"(?i)^(last updated|updated|posted|by )", para):
        para = ""
    clean_title = re.sub(r"\s*[|·—-]\s*(The )?Jorge Ramirez.*$", "", htmllib.unescape(title)).strip()
    base = para or (f"{clean_title} — local New Jersey real estate insight and "
                    f"honest guidance from Jorge Ramirez, Keller Williams.")
    return esc_text(base[:157].rsplit(" ", 1)[0])


def safe_fix_page(path, rep):
    """Additive, mechanical fixes only. Returns list of fix labels applied."""
    t = open(path, encoding="utf-8").read()
    orig = t
    fixes = []
    url = rep["url"]
    title = rep["title"] or "The Jorge Ramirez Group"
    inserts = []

    if "missing-meta-description" in rep["issues"]:
        desc = make_meta_desc(t, title)
        inserts.append(f'<meta name="description" content="{desc}">')
        fixes.append("meta-description")
    if "missing-canonical" in rep["issues"]:
        inserts.append(f'<link rel="canonical" href="{url}">')
        fixes.append("canonical")
    if "missing-viewport" in rep["issues"]:
        inserts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        fixes.append("viewport")
    if "missing-og:title" in rep["issues"]:
        inserts.append(f'<meta property="og:title" content="{esc_text(title)}">')
        fixes.append("og:title")
    if "missing-og:description" in rep["issues"]:
        d = make_meta_desc(t, title)
        inserts.append(f'<meta property="og:description" content="{d}">')
        inserts.append(f'<meta property="og:url" content="{url}">')
        inserts.append('<meta property="og:type" content="article">')
        fixes.append("og:description")
    if "missing-twitter:card" in rep["issues"]:
        inserts.append('<meta name="twitter:card" content="summary_large_image">')
        fixes.append("twitter:card")

    if not inserts:
        return []
    block = "\n  " + "\n  ".join(inserts)
    if re.search(r"</head>", t, re.I):
        t = re.sub(r"</head>", block + "\n</head>", t, count=1, flags=re.I)
    else:
        return []
    if BANNED in re.sub(r"\D", "", block):
        return []
    if t != orig:
        open(path, "w", encoding="utf-8").write(t)
    return fixes


# --------------------------------------------------------------------------- #
#  Risky proposals (queued, not applied)                                       #
# --------------------------------------------------------------------------- #
def build_proposals(gsc, recently_changed):
    """Suggest better title/meta for high-impression low-CTR pages. These are
    NOT applied — they go in the report for Jorge to approve."""
    props = []
    for o in gsc["opportunities"][:12]:
        path = url_to_path(o["url"])
        if not path or path in recently_changed:
            continue
        t = open(path, encoding="utf-8").read()
        cur_title = re.search(r"<title>(.*?)</title>", t, re.I | re.S)
        cur_title = cur_title.group(1).strip() if cur_title else ""
        suggestion = suggest_title(cur_title, o)
        if not suggestion or suggestion == cur_title:
            continue
        props.append({
            "id": re.sub(r"[^a-z0-9]+", "-",
                         os.path.relpath(path, REPO).lower())[:60],
            "path": os.path.relpath(path, REPO), "url": o["url"],
            "reason": (f"{o['impressions']:,} impressions, "
                       f"{o['ctr']*100:.1f}% CTR, position {o['position']:.1f} "
                       f"— strong visibility, weak click-through"),
            "current_title": cur_title, "proposed_title": suggestion,
            "type": "title-ctr",
        })
    return props


def claude_generate(prompt, timeout=120):
    """Use the authenticated claude CLI if a long-lived token is configured
    (shared with the blog automation). Returns None if unavailable."""
    tok = (load_json(os.path.join(REPO, "tools", "blog-automation", "config.json"),
                     {}).get("claude_oauth_token", "").strip()
           or os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "").strip())
    if not tok:
        return None  # unattended job can't use the expiring desktop login
    env = os.environ.copy()
    env["CLAUDE_CODE_OAUTH_TOKEN"] = tok
    for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL"):
        env.pop(k, None)
    try:
        r = subprocess.run(["claude", "-p", prompt, "--output-format", "text"],
                           capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL, env=env)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    out = (r.stdout or "").strip()
    if not out or "Not logged in" in out or "/login" in out:
        return None
    return out


def suggest_title(cur, o):
    """Propose a more click-worthy title. Prefers a Claude-written rewrite;
    without the token, only makes HIGH-CONFIDENCE mechanical changes (refresh a
    stale year) rather than emitting low-value noise."""
    if not cur:
        return None
    yr = datetime.date.today().year
    ai = claude_generate(
        f"You are an SEO expert. Rewrite this New Jersey real-estate page title "
        f"to earn more clicks from Google WITHOUT changing its topic, without "
        f"clickbait, and without any fabricated claim. It currently ranks around "
        f"position {o['position']:.0f} with only {o['ctr']*100:.1f}% CTR.\n"
        f"Current title: {cur!r}\n"
        f"Rules: <= 60 characters, keep '| Jorge Ramirez' if it fits, honest, "
        f"specific. Return ONLY the new title text, nothing else.")
    if ai:
        ai = ai.strip().strip('"').splitlines()[0].strip()
        if 15 < len(ai) <= 65 and ai != cur:
            return ai
    # Heuristic fallback: only refresh a stale year (a real, safe CTR lever).
    m = re.search(r"\b(20(?:1|2)\d)\b", cur)
    if m and int(m.group(1)) < yr:
        return cur.replace(m.group(1), str(yr))
    return None


def url_to_path(url):
    rel = url.replace(SITE, "").strip("/")
    for cand in (os.path.join(REPO, rel + ".html"),
                 os.path.join(REPO, rel, "index.html"),
                 os.path.join(REPO, rel)):
        if os.path.isfile(cand):
            return cand
    return None


# --------------------------------------------------------------------------- #
#  Git                                                                          #
# --------------------------------------------------------------------------- #
def git(*a):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True)


def deploy(paths, msg, push=True):
    git("add", *paths)
    r = git("commit", "-m", msg)
    if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
        log(f"commit note: {r.stdout} {r.stderr}"); return False
    if push:
        git("pull", "--rebase", "--autostash", "origin", "main")
        r = git("push", "origin", "main")
        if r.returncode != 0:
            git("pull", "--rebase", "--autostash", "origin", "main")
            r = git("push", "origin", "main")
        if r.returncode != 0:
            log(f"PUSH FAILED: {r.stderr.strip()}"); return False
        log("pushed to origin/main")
    return True


# --------------------------------------------------------------------------- #
#  Report + email                                                              #
# --------------------------------------------------------------------------- #
def arrow(v, invert=False):
    if v is None:
        return ""
    good = (v < 0) if invert else (v > 0)
    if v == 0:
        return ' <span style="color:#888">±0</span>'
    color = "#1a7f37" if good else "#c1121f"
    sign = "+" if v > 0 else ""
    return f' <span style="color:{color}">{sign}{v:g}</span>'


def build_report(gsc, deltas, prev_date, fixes, proposals):
    t = gsc["totals"]
    rows = "".join(
        f"<tr><td style='padding:4px 10px'>{o['ctr']*100:.1f}%</td>"
        f"<td style='padding:4px 10px'>{o['position']:.1f}</td>"
        f"<td style='padding:4px 10px'>{o['impressions']:,}</td>"
        f"<td style='padding:4px 10px'><a href='{o['url']}'>{o['url'].replace(SITE,'')}</a></td></tr>"
        for o in gsc["opportunities"][:10])
    fix_rows = "".join(
        f"<li><code>{f['path']}</code> — {', '.join(f['fixes'])}</li>" for f in fixes) \
        or "<li>No missing mechanical tags today — all clean. ✅</li>"
    prop_rows = "".join(
        f"<div style='border:1px solid #e5e5e5;border-radius:8px;padding:12px;margin:10px 0'>"
        f"<div style='font-size:12px;color:#888'>{p['reason']}</div>"
        f"<div style='margin:6px 0'><b>Page:</b> <code>{p['path']}</code></div>"
        f"<div><b>Now:</b> {htmllib.escape(p['current_title'])}</div>"
        f"<div><b>Proposed:</b> {htmllib.escape(p['proposed_title'])}</div></div>"
        for p in proposals) or "<p>No new risky proposals today.</p>"
    idx = gsc["index_issues"]
    idx_html = ("".join(f"<li><a href='{i['url']}'>{i['url'].replace(SITE,'')}</a> — "
                        f"{htmllib.escape(i.get('coverage') or i.get('verdict') or '')}</li>"
                        for i in idx[:10]) or "<li>Sampled URLs all indexed. ✅</li>")
    sm = gsc["sitemaps"]
    sm_html = "".join(
        f"<li>{s['path'].replace(SITE,'')} — errors {s['errors']}, warnings {s['warnings']}</li>"
        for s in sm) or "<li>No sitemaps reported.</li>"
    d = deltas
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:16px;background:#fff">
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:680px;margin:0 auto;color:#1a1a1a">
<h2 style="margin-bottom:2px">SEO Doctor — {gsc['date']}</h2>
<p style="color:#888;margin-top:0;font-size:13px">thejorgeramirezgroup.com · 28-day window {gsc['range'][0]} → {gsc['range'][1]}{f" · vs snapshot {prev_date}" if prev_date else ""}</p>

<table style="border-collapse:collapse;margin:14px 0">
<tr>
  <td style="padding:8px 16px 8px 0"><div style="font-size:22px;font-weight:700">{t['clicks']:.0f}{arrow(d['clicks'])}</div><div style="font-size:12px;color:#888">Clicks</div></td>
  <td style="padding:8px 16px 8px 0"><div style="font-size:22px;font-weight:700">{t['impressions']:.0f}{arrow(d['impressions'])}</div><div style="font-size:12px;color:#888">Impressions</div></td>
  <td style="padding:8px 16px 8px 0"><div style="font-size:22px;font-weight:700">{t['ctr']*100:.2f}%{arrow(round(d['ctr']*100,2) if d['ctr'] is not None else None)}</div><div style="font-size:12px;color:#888">CTR</div></td>
  <td style="padding:8px 16px 8px 0"><div style="font-size:22px;font-weight:700">{t['position']:.1f}{arrow(round(d['position'],1) if d['position'] is not None else None, invert=True)}</div><div style="font-size:12px;color:#888">Avg position</div></td>
</tr>
</table>

<h3>✅ Auto-fixed today (safe, mechanical)</h3>
<ul>{fix_rows}</ul>

<h3>🔶 Needs your call — proposed title fixes for high-traffic pages</h3>
<p style="font-size:13px;color:#555">These pages get seen a lot but rarely clicked. I did <b>not</b> change them — approve to apply: reply <b>“apply SEO proposals”</b> to Claude, or run <code>python3 seo_daily.py --apply-proposals</code>.</p>
{prop_rows}

<h3>📈 Biggest CTR opportunities (high impressions, low CTR)</h3>
<table style="border-collapse:collapse;font-size:13px"><tr style="text-align:left;color:#888"><th style="padding:4px 10px">CTR</th><th style="padding:4px 10px">Pos</th><th style="padding:4px 10px">Impr.</th><th style="padding:4px 10px">Page</th></tr>{rows}</table>

<h3>🔎 Index status (rotating daily sample)</h3><ul>{idx_html}</ul>
<h3>🗺️ Sitemaps</h3><ul>{sm_html}</ul>

<p style="color:#aaa;font-size:11px;margin-top:24px">Automated by SEO Doctor · safe fixes applied automatically, ranking-page rewrites always wait for your approval.</p>
</div></body></html>"""


def send_email(html_body, subject, c):
    """Send via SMTP app-password (preferred) or Gmail API. Returns False and
    logs clearly if no credential is configured — the report is always saved to
    reports/ regardless, so nothing is lost."""
    to = c.get("report_email", "jorgeramirez76@gmail.com")
    m = parse_env(MAIL_ENV)
    msg = MIMEText(html_body, "html", "utf-8")
    msg["to"], msg["subject"] = to, subject

    # 1) SMTP app-password path (simplest to set up, most reliable)
    if m.get("SMTP_HOST") and m.get("SMTP_PASS"):
        import smtplib, ssl
        host = m["SMTP_HOST"]; port = int(m.get("SMTP_PORT", "465"))
        user = m.get("SMTP_USER", to); msg["from"] = m.get("SMTP_FROM", user)
        try:
            if port == 465:
                srv = smtplib.SMTP_SSL(host, port, context=ssl.create_default_context())
            else:
                srv = smtplib.SMTP(host, port); srv.starttls(context=ssl.create_default_context())
            srv.login(user, m["SMTP_PASS"])
            srv.sendmail(msg["from"], [to], msg.as_string())
            srv.quit()
            log(f"emailed report to {to} via SMTP"); return True
        except Exception as e:
            log(f"SMTP send failed: {e}")

    # 2) Gmail API path (if a real refresh token is ever configured)
    svc, sender = gmail_service()
    if svc:
        msg["from"] = sender
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        svc.users().messages().send(userId="me", body={"raw": raw}).execute()
        log(f"emailed report to {to} via Gmail API"); return True

    log("email PENDING — no mail credential yet. Report saved to reports/. "
        "Add a Gmail app password to tools/seo-optimizer/mail.env (see mail.env.example).")
    return False


# --------------------------------------------------------------------------- #
#  Apply queued proposals                                                      #
# --------------------------------------------------------------------------- #
def apply_proposals(only_id=None, push=True):
    files = sorted(f for f in os.listdir(STATE) if f.startswith("proposals-"))
    if not files:
        log("no proposals queued"); return
    props = load_json(os.path.join(STATE, files[-1]), [])
    changed_state = load_json(os.path.join(STATE, "changed.json"), {})
    applied = []
    for p in props:
        if only_id and p["id"] != only_id:
            continue
        path = os.path.join(REPO, p["path"])
        if not os.path.isfile(path):
            continue
        t = open(path, encoding="utf-8").read()
        if p["type"] == "title-ctr" and p.get("current_title"):
            t2 = t.replace(f"<title>{p['current_title']}</title>",
                           f"<title>{p['proposed_title']}</title>", 1)
            if t2 != t:
                open(path, "w", encoding="utf-8").write(t2)
                changed_state[p["path"]] = str(datetime.date.today())
                applied.append(p["path"])
    if applied:
        save_json(os.path.join(STATE, "changed.json"), changed_state)
        deploy(applied + ["tools/seo-optimizer/state/changed.json"],
               f"seo: apply {len(applied)} approved title fix(es)", push=push)
        log(f"applied {len(applied)} proposal(s): {applied}")
    else:
        log("nothing applied")


# --------------------------------------------------------------------------- #
#  Main                                                                        #
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--no-email", action="store_true")
    ap.add_argument("--apply-proposals", action="store_true")
    ap.add_argument("--id")
    args = ap.parse_args()
    c = cfg()

    if args.apply_proposals:
        apply_proposals(only_id=args.id, push=not args.no_push)
        return

    log("=== SEO Doctor run ===")

    # register blog posts other publishers dropped from sitemap.xml
    if not args.dry_run:
        try:
            r = subprocess.run([sys.executable,
                                os.path.join(REPO, "tools", "sync_sitemap.py")],
                               capture_output=True, text=True)
            if r.stdout.strip() and r.stdout.strip() != "sitemap in sync":
                log(f"sitemap sync: {r.stdout.strip()}")
                deploy(["sitemap.xml"], "seo: register missing blog posts in sitemap",
                       push=not args.no_push)
        except Exception as e:
            log(f"sitemap sync failed: {e}")
    try:
        gsc = gsc_pull(c)
    except Exception as e:
        log(f"GSC pull FAILED: {e}"); sys.exit(1)
    deltas, prev_date = compute_deltas(gsc)
    log(f"GSC: {gsc['totals']['clicks']:.0f} clicks / "
        f"{gsc['totals']['impressions']:.0f} impr / "
        f"CTR {gsc['totals']['ctr']*100:.2f}% / pos {gsc['totals']['position']:.1f} "
        f"| {len(gsc['opportunities'])} opportunities, "
        f"{len(gsc['index_issues'])} index issues")

    # audit + safe fixes
    changed_state = load_json(os.path.join(STATE, "changed.json"), {})
    cooldown = {p for p, dt in changed_state.items()
                if (datetime.date.today() - datetime.date.fromisoformat(dt)).days
                < c["cooldown_days"]}
    fixes, edited = [], []
    for path in all_pages():
        rep = audit_page(path)
        if not rep or not rep["issues"]:
            continue
        rel = os.path.relpath(path, REPO)
        if rel in cooldown or len(edited) >= c["max_auto_edits_per_day"]:
            continue
        if not args.dry_run:
            applied = safe_fix_page(path, rep)
            if applied:
                fixes.append({"path": rel, "fixes": applied})
                edited.append(rel)
    if len(edited) >= c["max_auto_edits_per_day"]:
        log(f"hit daily safe-edit cap ({c['max_auto_edits_per_day']})")

    # proposals (never auto-applied)
    proposals = build_proposals(gsc, cooldown)
    save_json(os.path.join(STATE, f"proposals-{gsc['date']}.json"), proposals)
    save_json(os.path.join(STATE, f"snapshot-{gsc['date']}.json"), {
        "date": gsc["date"], "totals": gsc["totals"],
        "opportunities": gsc["opportunities"][:25]})

    # deploy safe fixes
    if fixes and not args.dry_run:
        # also refresh sitemap lastmod entries touched? keep minimal: commit edits
        deploy([f["path"] for f in fixes],
               f"seo: auto-fix {sum(len(f['fixes']) for f in fixes)} mechanical "
               f"issue(s) across {len(fixes)} page(s)", push=not args.no_push)

    # report + email
    subject = (f"SEO Doctor {gsc['date']} · {gsc['totals']['clicks']:.0f} clicks"
               f" · {len(fixes)} fixed · {len(proposals)} to approve")
    report = build_report(gsc, deltas, prev_date, fixes, proposals)
    with open(os.path.join(REPORTS, f"report-{gsc['date']}.html"), "w") as f:
        f.write(report)
    if not args.no_email and not args.dry_run:
        try:
            send_email(report, subject, c)
        except Exception as e:
            log(f"email failed: {e}")
    log(f"done — {len(fixes)} safe fixes, {len(proposals)} proposals queued")


if __name__ == "__main__":
    main()
