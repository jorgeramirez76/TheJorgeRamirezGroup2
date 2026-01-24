#!/usr/bin/env python3
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

TOWNS_DIR = Path("towns")

# 1) URL fixes (global replace)
URL_REPLACEMENTS = [
    ("https://www.thejorgeramirezgroup.com", "https://thejorgeramirezgroup.com"),
    ("http://www.thejorgeramirezgroup.com", "https://thejorgeramirezgroup.com"),
]

# 2) sameAs array (EXACTLY as provided)
SAME_AS = [
    "https://www.zillow.com/profile/TheJorgeRamirezGroup",
    "https://www.linkedin.com/in/jorgeramirez1213",
    "https://www.facebook.com/thejorgeramirezgroup",
    "https://www.instagram.com/jorgesellsnjhomes",
    "https://www.google.com/maps/place/Jorge+Ramirez+Realtor+-+Keller+Williams+Premier+Properties/@40.7176144,-74.3613942,16z",
    "https://thejorgeramirezgroup.kw.com/agent/Jorge-Ramirez/520237",
]

AGGREGATE_RATING = {
    "@type": "AggregateRating",
    "ratingValue": "5.0",
    "reviewCount": "26",
    "bestRating": "5",
    "worstRating": "1",
}

HAS_CREDENTIAL = {
    "@type": "EducationalOccupationalCredential",
    "credentialCategory": "Real Estate License",
    "recognizedBy": {
        "@type": "Organization",
        "name": "New Jersey Real Estate Commission",
    },
    "identifier": "1754604",
}

LICENSE_NUM = "1754604"

# JSON-LD script regex
LD_JSON_SCRIPT_RE = re.compile(
    r'(<script[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
    re.IGNORECASE | re.DOTALL,
)

# Footer edits
COPYRIGHT_RE = re.compile(
    r"©\s*2026\s+Jorge\s+Ramirez\s*-\s*Keller\s+Williams\b",
    re.IGNORECASE,
)

FOOTER_SENTENCE = "Full-time Realtor with Keller Williams Premier Properties since 2017."
LICENSE_P_HTML = r'<p><strong>NJ License #1754604</strong></p>'

def filename_to_town_name(slug: str) -> str:
    name = slug.replace(".html", "").replace("-", " ")
    words = []
    for w in name.split():
        lw = w.lower()
        if lw in {"nj", "usa"}:
            words.append(w.upper())
        elif lw in {"city"}:
            words.append("City")
        elif lw in {"borough"}:
            words.append("Borough")
        elif lw in {"township"}:
            words.append("Township")
        else:
            words.append(w.capitalize())
    return " ".join(words)

def find_realestateagent_obj(data: Any) -> Optional[Dict[str, Any]]:
    def is_agent(obj: Any) -> bool:
        if not isinstance(obj, dict):
            return False
        t = obj.get("@type")
        if isinstance(t, str):
            return t.lower() == "realestateagent"
        if isinstance(t, list):
            return any(isinstance(x, str) and x.lower() == "realestateagent" for x in t)
        return False
    if isinstance(data, dict):
        if is_agent(data):
            return data
        g = data.get("@graph")
        if isinstance(g, list):
            for item in g:
                if is_agent(item):
                    return item
    elif isinstance(data, list):
        for item in data:
            found = find_realestateagent_obj(item)
            if found:
                return found
    return None

def find_webpage_obj_in_graph(data: Any) -> Optional[Dict[str, Any]]:
    def is_webpage(obj: Any) -> bool:
        if not isinstance(obj, dict):
            return False
        t = obj.get("@type")
        if isinstance(t, str):
            return t.lower() == "webpage"
        if isinstance(t, list):
            return any(isinstance(x, str) and x.lower() == "webpage" for x in t)
        return False
    if isinstance(data, dict):
        g = data.get("@graph")
        if isinstance(g, list):
            for item in g:
                if is_webpage(item):
                    return item
    return None

def infer_town_name_from_agent(agent: Dict[str, Any], fallback_slug: str) -> str:
    area = agent.get("areaServed")
    if isinstance(area, dict):
        nm = area.get("name")
        if isinstance(nm, str) and nm.strip():
            return nm.strip()
    addr = agent.get("address")
    if isinstance(addr, dict):
        loc = addr.get("addressLocality")
        if isinstance(loc, str) and loc.strip():
            return loc.strip()
    return filename_to_town_name(fallback_slug)

def ensure_agent_updates(agent: Dict[str, Any], town_name: str) -> bool:
    changed = False
    if agent.get("sameAs") != SAME_AS:
        agent["sameAs"] = SAME_AS
        changed = True
    if "aggregateRating" not in agent:
        agent["aggregateRating"] = AGGREGATE_RATING
        changed = True
    if "hasCredential" not in agent:
        agent["hasCredential"] = HAS_CREDENTIAL
        changed = True
    desired_desc = (
        f"Jorge Ramirez is a top-rated real estate agent serving {town_name}, NJ "
        f"(License #{LICENSE_NUM}). Specializing in luxury homes, first-time buyers, "
        f"and investment properties with an AI-powered marketing system."
    )
    if agent.get("description") != desired_desc:
        agent["description"] = desired_desc
        changed = True
    return changed

def ensure_webpage_speakable(webpage: Dict[str, Any]) -> bool:
    desired = {
        "@type": "SpeakableSpecification",
        "cssSelector": [".hero-content", ".town-seo"],
    }
    if "speakable" in webpage:
        if webpage.get("speakable") != desired:
            webpage["speakable"] = desired
            return True
        return False
    webpage["speakable"] = desired
    return True

def update_footer(html: str) -> Tuple[str, bool]:
    changed = False
    out = html
    new_line = "© 2026 Jorge Ramirez - Keller Williams Premier Properties | NJ License #1754604"
    out2 = COPYRIGHT_RE.sub(new_line, out)
    if out2 != out:
        out = out2
        changed = True
    if LICENSE_P_HTML not in out:
        pattern = re.escape(FOOTER_SENTENCE)
        out3 = re.sub(
            pattern,
            FOOTER_SENTENCE + "\n" + LICENSE_P_HTML,
            out,
            count=1,
        )
        if out3 != out:
            out = out3
            changed = True
    return out, changed

def update_jsonld_blocks(html: str, filename_slug: str) -> Tuple[str, bool]:
    changed_any = False
    def repl(match: re.Match) -> str:
        nonlocal changed_any
        open_tag, json_text, close_tag = match.group(1), match.group(2), match.group(3)
        raw = json_text.strip()
        try:
            data = json.loads(raw)
        except Exception:
            return match.group(0)
        changed = False
        agent = find_realestateagent_obj(data)
        if agent:
            town_name = infer_town_name_from_agent(agent, filename_slug)
            if ensure_agent_updates(agent, town_name):
                changed = True
        webpage = find_webpage_obj_in_graph(data)
        if webpage:
            if ensure_webpage_speakable(webpage):
                changed = True
        if not changed:
            return match.group(0)
        changed_any = True
        new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return f"{open_tag}\n{new_json}\n{close_tag}"
    new_html = LD_JSON_SCRIPT_RE.sub(repl, html)
    return new_html, changed_any

def main():
    if not TOWNS_DIR.exists():
        raise SystemExit("ERROR: /towns folder not found. Run from repo root.")
    files = sorted(TOWNS_DIR.glob("*.html"))
    if not files:
        raise SystemExit("ERROR: No .html files found in /towns.")
    total = len(files)
    changed_files = 0
    changed_url = 0
    changed_jsonld = 0
    changed_footer = 0
    for fp in files:
        original = fp.read_text(encoding="utf-8", errors="ignore")
        html = original
        file_changed = False
        before = html
        for a, b in URL_REPLACEMENTS:
            html = html.replace(a, b)
        if html != before:
            changed_url += 1
            file_changed = True
        html2, did_jsonld = update_jsonld_blocks(html, fp.name)
        if did_jsonld:
            changed_jsonld += 1
            file_changed = True
        html = html2
        html3, did_footer = update_footer(html)
        if did_footer:
            changed_footer += 1
            file_changed = True
        html = html3
        if file_changed and html != original:
            fp.write_text(html, encoding="utf-8")
            changed_files += 1
    print(f"Town pages found: {total}")
    print(f"Files changed: {changed_files}")
    print(f"Files with URL fixes: {changed_url}")
    print(f"Files with JSON-LD updates: {changed_jsonld}")
    print(f"Files with footer updates: {changed_footer}")

if __name__ == "__main__":
    main()
