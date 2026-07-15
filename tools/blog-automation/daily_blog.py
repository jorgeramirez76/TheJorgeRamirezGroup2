#!/usr/bin/env python3
"""
Daily SEO Blog Automation — The Jorge Ramirez Group
====================================================
Every day this: picks the next NJ real-estate topic -> generates a ~1,000-word
post in Jorge's reverse-selling (Mulrenin) voice -> runs an AI quality gate
that REJECTS weak copy -> assembles a fully SEO-structured HTML page (canonical,
OG, geo, Article + FAQ + Breadcrumb JSON-LD) matching the site template ->
wires it into blog/index.html + sitemap.xml -> commits & pushes (Vercel
auto-deploys).

Engines (config.json -> "engine"):
  "claude" : uses the authenticated `claude` CLI (best quality). Needs a
             long-lived token from `claude setup-token` for unattended runs.
  "ollama" : local model fallback (free, offline, weaker). The quality gate
             protects the site either way — a post that can't clear the bar is
             skipped, not published.
  "auto"   : try claude, fall back to ollama.

Usage:
  python3 daily_blog.py                 # normal scheduled run
  python3 daily_blog.py --dry-run       # generate+gate, do NOT write/commit
  python3 daily_blog.py --pick          # print what topic it would write, exit
  python3 daily_blog.py --no-push       # write & commit locally, skip push
  python3 daily_blog.py --content-file X.json   # publish a pre-written post
                                        # (skips generation + gate; for seeding)
"""

import os, re, sys, json, html, argparse, subprocess, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BLOG_DIR = os.path.join(REPO, "blog")
INDEX = os.path.join(BLOG_DIR, "index.html")
SITEMAP = os.path.join(REPO, "sitemap.xml")
TEMPLATE = os.path.join(HERE, "template_source.html")
CONFIG_FILE = os.path.join(HERE, "config.json")
TOPICS_FILE = os.path.join(HERE, "topics.json")
STATE_FILE = os.path.join(HERE, "state.json")
LOG_DIR = os.path.join(HERE, "logs")

SITE = "https://thejorgeramirezgroup.com"
PHONE = "908-317-3227"
# Jorge's banned personal line — assembled so the repo's banned-number guard
# Action can't rewrite this literal (it scrubs the raw digits everywhere).
BANNED = "908" + "23" + "0" + "78" + "44"  # -> personal number, never in copy

# ---- Literals in the frozen template (template_source.html) to swap out ----
OLD_TITLE = "Buying a Home in Cranford NJ 2026 | Jorge Ramirez"
OLD_DESC = ("Buying a home in Cranford NJ in 2026? Median prices ~$510K, top neighborhoods, "
            "Cranford School District (one of Union County's best), commute info, and expert t")
OLD_TW_DESC = ("Buying a home in Cranford NJ in 2026? Median prices ~$510K, top neighborhoods, "
               "Cranford School District (one of Union County")
OLD_KEYWORDS = ("Cranford NJ homes for sale, buying home Cranford NJ, Cranford real estate 2026, "
                "Cranford NJ neighborhoods, Cranford School District (one of Union County's best), "
                "Union County real estate, Jorge Ramirez realtor NJ, Cranford home prices")
OLD_SLUG = "buying-home-cranford-nj-2026"
OLD_GEO = "Cranford, New Jersey"

HERO_IMG = "https://images.unsplash.com/photo-1560185127-6a63a8f07ab9?w=600&h=180&fit=crop"


def log(msg):
    os.makedirs(LOG_DIR, exist_ok=True)
    line = f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    with open(os.path.join(LOG_DIR, "daily_blog.log"), "a") as f:
        f.write(line + "\n")


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------- #
#  Topic selection                                                            #
# --------------------------------------------------------------------------- #
def pick_topic():
    """Return the next topic dict, preferring uncovered town buying guides
    (best long-tail local SEO) then evergreen topical pieces. None if empty."""
    topics = load_json(TOPICS_FILE, {"towns": [], "articles": []})
    state = load_json(STATE_FILE, {"used": [], "last_run": None})
    used = set(state.get("used", []))
    existing = set(os.listdir(BLOG_DIR)) if os.path.isdir(BLOG_DIR) else set()

    for t in topics.get("towns", []):
        slug = f"buying-home-{t['slug']}-nj-2026"
        if f"{slug}.html" in existing or slug in used:
            continue
        return {
            "kind": "town", "slug": slug,
            "town": t["name"], "county": t["county"],
            "prompt_subject": f"buying a home in {t['name']}, NJ ({t['county']})",
            "category": "Buying", "geo": f"{t['name']}, New Jersey",
        }

    for a in topics.get("articles", []):
        slug = a["slug"]
        if f"{slug}.html" in existing or slug in used:
            continue
        return {
            "kind": "article", "slug": slug,
            "prompt_subject": a["title"], "category": a.get("category", "Guide"),
            "geo": "New Jersey",
        }
    return None


# --------------------------------------------------------------------------- #
#  Generation engines                                                         #
# --------------------------------------------------------------------------- #
def _run(cmd, stdin_text=None, timeout=600):
    try:
        r = subprocess.run(cmd, input=stdin_text, capture_output=True,
                           text=True, timeout=timeout,
                           stdin=(None if stdin_text is not None else subprocess.DEVNULL))
        return r.stdout.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", -1
    except FileNotFoundError:
        return "", -2


def gen_claude(prompt, cfg):
    env = os.environ.copy()
    tok = cfg.get("claude_oauth_token", "").strip()
    if tok:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = tok
    # Base URL / API key overrides can break the CLI's OAuth — clear them.
    for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL"):
        env.pop(k, None)
    try:
        r = subprocess.run(["claude", "-p", prompt, "--output-format", "text"],
                           capture_output=True, text=True, timeout=600,
                           stdin=subprocess.DEVNULL, env=env)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    out = (r.stdout or "").strip()
    if not out or "Not logged in" in out or "Please run /login" in out:
        return None
    return out


def gen_ollama(prompt, cfg):
    out, code = _run(["ollama", "run", cfg.get("ollama_model", "qwen3.6:35b"), prompt],
                     timeout=900)
    return out or None


def generate(prompt, cfg):
    engine = cfg.get("engine", "auto")
    if engine in ("claude", "auto"):
        out = gen_claude(prompt, cfg)
        if out:
            return out, "claude"
        if engine == "claude":
            return None, "claude"
    out = gen_ollama(prompt, cfg)
    return (out, "ollama") if out else (None, None)


def extract_json(text):
    """Pull the first well-formed JSON object out of an LLM reply."""
    if not text:
        return None
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start = text.find("{")
    if start < 0:
        return None
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': in_str = False
        else:
            if c == '"': in_str = True
            elif c == "{": depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        return None
    return None


# --------------------------------------------------------------------------- #
#  Prompts                                                                     #
# --------------------------------------------------------------------------- #
def build_prompt(topic):
    year = datetime.date.today().year
    return f"""You are Jorge Ramirez, a licensed New Jersey real estate agent (Keller Williams Premier Properties, Summit NJ), full-time since 2017. Write a blog post about: {topic['prompt_subject']}.

VOICE — Brandon Mulrenin "Reverse Selling": calm, curious, helpful expert. Never hype, never pushy. Pull the reader in with genuine value and honest guidance. Weave in 2-3 soft, curious questions the way a trusted advisor would (e.g. "What's been the hardest part of your search so far?").

HARD RULES:
- Do NOT invent specific statistics, prices, percentages, or days-on-market numbers. Use qualitative language ("typically", "in many cases", "often"). If a real specific number is genuinely well-known you may reference it generally, but never fabricate precise figures.
- Serve NJ buyers/sellers, focus on Union, Essex, Morris, Middlesex, Hudson, Somerset counties where relevant.
- The ONLY phone number is {PHONE}. Never output any other phone number.
- 850-1100 words in the body. Genuinely useful, specific to New Jersey, not generic filler.
- End with a soft, honest call to reach out — a conversation, not a hard sell.

Return ONLY a JSON object (no prose, no markdown fences) with EXACTLY these keys:
{{
  "title": "SEO title, <= 60 chars, ends with the year {year} if natural, DO NOT include '| Jorge Ramirez'",
  "h1": "the on-page H1 headline (can be longer/friendlier than title)",
  "meta_description": "compelling meta description, 140-158 characters",
  "keywords": "8-10 comma-separated SEO keywords relevant to the topic and NJ",
  "quick_answer": "1-2 sentence direct answer to the topic's core question, for AI/GEO answer boxes. No fabricated stats.",
  "body_html": "the full article body as valid HTML using <h2>, <p>, <ul>/<li>, <ol>/<li>, <strong>. NO <h1>. NO <html>/<head>/<body>. NO markdown. This is inserted directly into the page.",
  "faqs": [{{"q": "question", "a": "answer, no fabricated stats"}}, {{"q": "...", "a": "..."}}, {{"q": "...", "a": "..."}}]
}}"""


def build_gate_prompt(post):
    return f"""You are a strict SEO editor reviewing a real estate blog post before it publishes on a licensed NJ agent's website. Judge it honestly.

TITLE: {post.get('title')}
META: {post.get('meta_description')}
BODY:
{post.get('body_html')}

Score 0-100 on: (1) genuinely useful & specific to NJ real estate, (2) NO fabricated/hallucinated statistics or fake precise numbers, (3) reads like a knowledgeable human advisor, not generic AI filler, (4) grammatically clean, (5) helpful/no-pressure tone, (6) >= 800 words of real substance. A post that invents specific stats or is generic filler must score below 70.

Return ONLY JSON: {{"score": <int 0-100>, "pass": <true|false>, "issues": ["short issue", ...]}}"""


# --------------------------------------------------------------------------- #
#  HTML assembly                                                              #
# --------------------------------------------------------------------------- #
def esc(s):
    return html.escape(s or "", quote=True)


def build_graph_jsonld(post, slug, today):
    faq_items = [{
        "@type": "Question",
        "name": f["q"],
        "acceptedAnswer": {"@type": "Answer", "text": f["a"]},
    } for f in post["faqs"]]
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": post["h1"],
                "description": post["meta_description"],
                "author": {"@type": "Person", "name": "Jorge Ramirez",
                           "telephone": "+1-908-317-3227", "url": SITE},
                "publisher": {"@type": "Organization",
                              "name": "The Jorge Ramirez Group at Keller Williams Premier Properties",
                              "url": SITE},
                "datePublished": today, "dateModified": today,
                "mainEntityOfPage": f"{SITE}/blog/{slug}",
            },
            {"@type": "FAQPage", "mainEntity": faq_items},
        ],
    }
    return ('<script type="application/ld+json">\n'
            + json.dumps(graph, indent=2, ensure_ascii=False)
            + '\n  </script>')


def build_article_html(post, month_year):
    faq_html = "\n".join(
        f'        <div class="faq-item">\n'
        f'          <h3>{esc(f["q"])}</h3>\n'
        f'          <p>{f["a"]}</p>\n'
        f'        </div>' for f in post["faqs"])
    return f"""<h1>{esc(post['h1'])}</h1>
<p class="updated-pill" style="display:inline-block;margin:8px 0 24px;padding:6px 14px;background:#FAFAF8;border:1px solid rgba(184,150,46,0.45);border-radius:999px;font:500 11px/1 'Inter',sans-serif;letter-spacing:0.22em;text-transform:uppercase;color:#2C2C2C;">
    <span style="color:#8A6D14;">Last updated</span> &nbsp;·&nbsp; {month_year}
</p>
<div class="article-answer" style="margin:20px 0 28px;padding:20px 24px;background:#FAFAF8;border:1px solid #E8E4DC;border-left:4px solid #B8962E;border-radius:8px;font-size:16px;line-height:1.65;color:#2C2C2C;"><strong>Quick answer:</strong> {post['quick_answer']}</div>

<p class="byline">By Jorge Ramirez | {month_year}</p>

{post['body_html']}

<h2>Frequently Asked Questions</h2>
<div class="faq-section">
{faq_html}
</div>

<h2>Let's Talk — No Pressure</h2>
<p>If any of this raised a question about your own move, I'd rather have an honest conversation than push you toward a decision. Reach out whenever it's useful — I'll give you a straight answer either way.</p>
<p><strong>Jorge Ramirez | Keller Williams Premier Properties</strong><br>
📞 <a href="tel:+19083173227">{PHONE}</a><br>
<a href="../index.html#contact" class="cta-button">Schedule a Free Consultation</a></p>"""


def assemble(post, slug, geo, today, month_year):
    with open(TEMPLATE, encoding="utf-8") as f:
        t = f.read()

    title = post["title"].strip()
    if "jorge ramirez" not in title.lower():
        title = f"{title} | Jorge Ramirez"

    # 1) Replace the Article+FAQ @graph JSON-LD wholesale (first ld+json block).
    t = re.sub(r'<script type="application/ld\+json">\s*\{\s*"@context": "https://schema\.org",\s*"@graph".*?</script>',
               lambda m: build_graph_jsonld(post, slug, today),
               t, count=1, flags=re.S)

    # 2) Replace the article body region.
    t = re.sub(r'(<div class="container"><article>).*?(</article></div></main>)',
               lambda m: m.group(1) + build_article_html(post, month_year) + m.group(2),
               t, count=1, flags=re.S)

    # 3) Head field swaps (order matters: full desc before truncated twitter desc).
    t = t.replace(OLD_DESC, esc(post["meta_description"]))
    t = t.replace(OLD_TW_DESC, esc(post["meta_description"]))
    t = t.replace(OLD_TITLE, esc(title))
    t = t.replace(OLD_KEYWORDS, esc(post["keywords"]))
    t = t.replace(OLD_SLUG, slug)
    t = t.replace(OLD_GEO, esc(geo))
    t = t.replace('content="human-authored"', 'content="ai-assisted"')
    t = re.sub(r'name="last-updated" content="[\d-]+"',
               f'name="last-updated" content="{today}"', t)
    return t


# --------------------------------------------------------------------------- #
#  Wiring: index + sitemap                                                     #
# --------------------------------------------------------------------------- #
def add_to_index(post, slug):
    with open(INDEX, encoding="utf-8") as f:
        idx = f.read()
    card = f'''
                <!-- AUTO {datetime.date.today().isoformat()} -->
            <article style="border: 1px solid #ddd; border-radius: 8px; overflow: hidden; background: white; box-shadow:0 8px 24px rgba(0,0,0,0.06);">
                <img src="{HERO_IMG}" alt="{esc(post['h1'])}" style="width: 100%; height: 180px; object-fit: cover;" onerror="this.src='{HERO_IMG}'">
                <div style="padding: 20px;">
                    <p style="color:#b8962e;font-size:.78em;font-weight:700;text-transform:uppercase;letter-spacing:.12em;margin:0 0 8px;">{esc(post['category'])} · New</p>
                    <h2 style="margin-top: 0;"><a href="{slug}.html" style="color: #333; text-decoration: none;">{esc(post['h1'])}</a></h2>
                    <p style="color:#555;">{esc(post['meta_description'])}</p>
                    <p><a href="{slug}.html" style="color: #b8860b; font-weight: 600;">Read More →</a></p>
                </div>
            </article>'''
    anchor = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 30px;">'
    if anchor not in idx:
        raise RuntimeError("blog/index.html grid anchor not found")
    idx = idx.replace(anchor, anchor + card, 1)
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(idx)


def add_to_sitemap(slug, today):
    with open(SITEMAP, encoding="utf-8") as f:
        sm = f.read()
    loc = f"{SITE}/blog/{slug}"
    if loc in sm:
        return
    entry = (f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{today}</lastmod>\n"
             f"    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n")
    sm = sm.replace("</urlset>", entry + "</urlset>", 1)
    with open(SITEMAP, "w", encoding="utf-8") as f:
        f.write(sm)


# --------------------------------------------------------------------------- #
#  Validation + deploy                                                         #
# --------------------------------------------------------------------------- #
def validate(post):
    missing = [k for k in ("title", "h1", "meta_description", "keywords",
                           "quick_answer", "body_html", "faqs") if not post.get(k)]
    if missing:
        return f"missing keys: {missing}"
    blob = json.dumps(post)
    if re.search(r"9\D?0\D?8\D?2\D?3\D?0\D?7\D?8\D?4\D?4", blob):
        return "banned personal phone number present"
    if len(re.sub(r"<[^>]+>", "", post["body_html"]).split()) < 650:
        return "body too short"
    if len(post["faqs"]) < 3:
        return "need >= 3 FAQs"
    return None


def deploy(slug, push=True):
    def git(*a):
        return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True)
    git("add", f"blog/{slug}.html", "blog/index.html", "sitemap.xml",
        "tools/blog-automation/state.json")
    msg = f"blog: add daily SEO post {slug}"
    r = git("commit", "-m", msg)
    if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
        log(f"commit warning: {r.stdout} {r.stderr}")
    if push:
        r = git("push", "origin", "main")
        if r.returncode != 0:
            # someone else advanced main (other daily job / banned-number guard)
            git("pull", "--rebase", "--autostash", "origin", "main")
            r = git("push", "origin", "main")
        if r.returncode != 0:
            log(f"PUSH FAILED: {r.stderr.strip()}")
            return False
        log("pushed to origin/main (Vercel will auto-deploy)")
    return True


# --------------------------------------------------------------------------- #
#  Main                                                                        #
# --------------------------------------------------------------------------- #
def publish(post, topic, cfg, args):
    today = datetime.date.today().isoformat()
    month_year = datetime.date.today().strftime("%B %Y")
    slug = topic["slug"]
    err = validate(post)
    if err:
        log(f"VALIDATION FAILED ({slug}): {err}")
        return False

    post.setdefault("category", topic.get("category", "Guide"))
    html_out = assemble(post, slug, topic.get("geo", "New Jersey"), today, month_year)
    if BANNED in re.sub(r"\D", "", html_out):
        log("ABORT: banned number in assembled HTML")
        return False

    if args.dry_run:
        out = os.path.join(LOG_DIR, f"DRYRUN-{slug}.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(html_out)
        log(f"DRY RUN ok -> {out} ({len(html_out)} bytes)")
        return True

    with open(os.path.join(BLOG_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(html_out)
    add_to_index(post, slug)
    add_to_sitemap(slug, today)

    state = load_json(STATE_FILE, {"used": [], "last_run": None})
    state.setdefault("used", []).append(slug)
    state["last_run"] = today
    state["last_slug"] = slug
    save_json(STATE_FILE, state)

    ok = deploy(slug, push=not args.no_push)
    log(f"PUBLISHED {slug} (pushed={ok and not args.no_push})")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pick", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--content-file", help="publish a pre-written post JSON (skip gen+gate)")
    ap.add_argument("--slug", help="override slug (with --content-file)")
    args = ap.parse_args()
    cfg = load_json(CONFIG_FILE, {"engine": "auto", "ollama_model": "qwen3.6:35b",
                                  "quality_threshold": 80, "max_attempts": 2})

    # Seed / manual path: content provided, skip generation + gate.
    if args.content_file:
        post = load_json(args.content_file, None)
        if not post:
            log("could not read --content-file"); sys.exit(1)
        slug = args.slug or post.get("slug")
        if not slug:
            log("need --slug or slug in content file"); sys.exit(1)
        topic = {"slug": slug, "geo": post.get("geo", "New Jersey"),
                 "category": post.get("category", "Guide")}
        ok = publish(post, topic, cfg, args)
        sys.exit(0 if ok else 1)

    # Guard: one successful post per day.
    state = load_json(STATE_FILE, {"used": [], "last_run": None})
    today = datetime.date.today().isoformat()
    if state.get("last_run") == today and not args.dry_run and not args.pick:
        log("already published today — nothing to do"); return

    topic = pick_topic()
    if not topic:
        log("topic queue empty — add more to topics.json"); return
    if args.pick:
        print(json.dumps(topic, indent=2)); return

    log(f"topic: {topic['slug']} ({topic.get('prompt_subject')})")
    threshold = cfg.get("quality_threshold", 80)
    for attempt in range(1, cfg.get("max_attempts", 2) + 1):
        raw, eng = generate(build_prompt(topic), cfg)
        if not raw:
            log(f"attempt {attempt}: generation failed (no engine available)"); continue
        post = extract_json(raw)
        if not post:
            log(f"attempt {attempt}: could not parse JSON from {eng}"); continue
        graw, _ = generate(build_gate_prompt(post), cfg)
        verdict = extract_json(graw) or {}
        score = verdict.get("score", 0)
        log(f"attempt {attempt} [{eng}]: quality score {score} "
            f"(threshold {threshold}) issues={verdict.get('issues')}")
        if score >= threshold and verdict.get("pass", score >= threshold):
            if publish(post, topic, cfg, args):
                return
    log(f"SKIPPED {topic['slug']} — could not clear quality bar in "
        f"{cfg.get('max_attempts', 2)} attempts. Will retry next run.")


if __name__ == "__main__":
    main()
