#!/usr/bin/env python3
"""Audit the owned English public-page inventory for fair-housing risk."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "data" / "english-fair-housing-inventory.json"
QUARANTINE_PATH = ROOT / "data" / "english-fair-housing-quarantine.json"
PROGRAMMATIC_DOORWAY_PATH = ROOT / "data" / "programmatic-doorway-retirement.json"
SKIP_PARTS = {".git", "crm", "es", "node_modules", "property-leads-system", "realtor", "towns"}
BUILD_OUTPUT_PARTS = {".vercel"}
MARKET_REPORT = re.compile(r"(?:market-report|real-estate-market|county-market)", re.I)
REDIRECT_STUB = re.compile(r'<meta\b[^>]*http-equiv=["\']refresh["\']', re.I)
ROBOTS_NOINDEX = re.compile(
    r'<meta\b[^>]*name=["\']robots["\'][^>]*content=["\'][^"\']*\bnoindex\b',
    re.I,
)

REBUILT_EXCLUSIONS = {
    "blog/best-nj-suburbs-nyc-commuters.html",
    "blog/best-nj-towns-for-families-2026.html",
    "blog/best-nj-towns-for-families.html",
    "blog/best-nj-towns-to-sell-home.html",
    "blog/best-time-to-sell-home-nj.html",
    "blog/first-time-home-buyer-nj-guide.html",
    "blog/midtown-direct-towns-nj.html",
    "blog/nj-property-tax-guide.html",
    "blog/top-nyc-commuter-towns-nj-2026.html",
    "nj-train-map.html",
    "tools/mortgage-calculator.html",
}

SOURCE_EMITTERS = {
    "api/lead.js",
    "build_communities_page.py",
    "fix_site_issues_v2.py",
    "generate_county_reports_and_comparisons.py",
    "generate_new_landing_pages.py",
    "index.html.backup",
    "js/communities-data.js",
    "js/main.js",
    "optimize_seo.py",
    "tools/blog-automation/daily_blog.py",
    "tools/blog-automation/template_source.html",
    "tools/blog-automation/topics.json",
}

GUARDED_EMITTERS = {
    "generate_blog.py": (
        "Legacy buying/selling functions contain excluded market-report data, but "
        "write_file refuses every fair-housing quarantine path."
    ),
}

RISK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "subjective school ranking",
        re.compile(
            r"(?:(?:top[- ](?:rated|ranked)|best|excellent|great|good|strong|weak|bad|"
            r"outstanding|award[- ]winning|highly[- ]rated|nationally[- ]ranked|"
            r"high[- ]performing|low[- ]performing|well[- ]regarded|acclaimed|elite|"
            r"premier|Blue Ribbon|A\+|\d+(?:\.\d+)?\s*/\s*10)"
            r"(?:\s+[A-Za-z-]+){0,2}\s+\b(?:schools?|school districts?|districts?)\b|"
            r"\b(?:schools?|school districts?|districts?)\b[^.<\n]{0,45}"
            r"(?:top[- ](?:rated|ranked)|rank(?:ed|s|ing)?\s+(?:in|among)|best|excellent|"
            r"great|good|strong|weak|bad|outstanding|highly[- ]rated|elite|premier|A\+|"
            r"\d+(?:\.\d+)?\s*/\s*10)|"
            r"\b(?:school quality|school[- ]focused buyers?|top[- ]school towns?)\b|"
            r"\b(?:schools?|school districts?|districts?)[^.<\n]{0,55}"
            r"\b\d+(?:\.\d+)?(?:\s*[-–]\s*\d+(?:\.\d+)?)?\s+out of\s+(?:5|10)\b|"
            r"\b\d+(?:\.\d+)?(?:\s*[-–]\s*\d+(?:\.\d+)?)?\s+out of\s+(?:5|10)"
            r"[^.<\n]{0,55}\b(?:schools?|school districts?|districts?)\b|"
            r"\b(?:school[- ]obsessed|school system[^.<\n]{0,25}(?:draw|attract))\b|"
            r"\b(?:\d+(?:\.\d+)?)(?:[- ]out[- ]of[- ](?:5|10)|\s+out\s+of\s+(?:5|10))"
            r"[^.<\n]{0,25}\b(?:schools?|school districts?|districts?)\b|"
            r"\b(?:schools?|school districts?|districts?)[^.<\n]{0,35}"
            r"\b(?:rating|ratings|rated|ranking|rankings|score|scores)\b|"
            r"\b(?:school[- ]rating|school[- ]district\s+(?:resource|information)\s+rating)\b|"
            r"\b(?:schools?|districts?)[^.<\n]{0,50}\bgraduates?\b[^.<\n]{0,35}"
            r"\b(?:Ivy League|top[- ]tier|top universities?)\b|"
            r"\b(?:GreatSchools|SchoolDigger|Niche\.com)\b)",
            re.I,
        ),
    ),
    (
        "categorical safety or crime",
        re.compile(
            r"\b(?:safest|safer\s+(?:town|community|neighbou?rhood|place|area|street)|"
            r"safe\s+(?:town|community|neighbou?rhood|place|area|street)|low[- ]crime|"
            r"crime[- ]free|very safe|unsafe\s+(?:town|community|neighbou?rhood)|"
            r"crime\s+rates?\s+(?:are|is)\s+(?:low|high)|Safety and Community|"
            r"schools?[^.<\n]{0,30}\bthe safety\b)\b",
            re.I,
        ),
    ),
    (
        "protected-class audience",
        re.compile(
            r"\b(?:family[- ](?:friendly|focused|oriented)|young\s+famil(?:y|ies)|"
            r"families\s+with\s+(?:young\s+)?(?:children|kids)|"
            r"families\s+with\s+\d+(?:\s*[-–]\s*\d+)?\s+kids|"
            r"buyers?\s+with\s+(?:children|kids)|school[- ]age\s+(?:children|kids)|"
            r"young\s+professionals?|retirees?|empty[- ]nesters?|dual[- ]income\s+families|"
            r"DINKs?|growing\s+families|starter\s+families|commuting\s+families|"
            r"school[- ]focused\s+buyers?|(?:NYC|finance|tech|creative|urban)\s+professionals?|"
            r"(?:buying|selling|commuting)\s+families|family\s+(?:demand|score|buyer|market)|"
            r"families\s+(?:I|we)\s+work\s+with|families\s+ask|"
            r"children\s+(?:reach|enter|approach)\s+school\s+age|"
            r"families\s+(?:moving|relocating|seeking|prioritizing|buying|who|with|"
            r"looking|ask|pick|choose|accept|pay|want|need|end\s+up)|"
            r"family[- ](?:feel|life|lifestyle|town|suburb|buyers?|demographic|demand|"
            r"traditional|heavy|score)|"
            r"(?:kids|children)[^.<\n]{0,35}\b(?:schools?|town|community|neighbou?rhood|"
            r"suburb|move|housing|commute|space|yard|downtown|buyers?)\b|"
            r"(?:buyers?|households?)[^.<\n]{0,45}\b(?:without\s+kids|families\s+with|"
            r"families\s+without|school[- ]age\s+children)\b|"
            r"families\s+(?:who|seeking|looking|prioritizing|buying|moving|leaving|want|need)"
            r"[^.<\n]{0,55}\b(?:schools?|district|town|community|neighbou?rhood|suburb|"
            r"commute|space|yard|downtown|housing)|"
            r"buyers?\s+(?:who|seeking|prioritizing|focused\s+on)[^.<\n]{0,45}\bschools?\b)\b",
            re.I,
        ),
    ),
    (
        "protected-class targeting",
        re.compile(
            r"\b(?:target(?:ing|ed)?|appeal(?:s|ing)?\s+to|attract(?:s|ing)?|ideal\s+for|"
            r"perfect\s+for|best\s+for|great\s+for|popular\s+with|designed\s+for|draws?)"
            r"[^.<\n]{0,35}\b(?:families|parents|professionals|executives|retirees|"
            r"empty[- ]nesters|seniors)\b|"
            r"\bexecutives?\s+(?:who|seeking|requiring|want|need|buying|moving)\b|"
            r"\bbuyers?\s+(?:are|skew|pool\s+skews?)[^.<\n]{0,50}"
            r"\b(?:executives|professionals|lawyers|families|retirees)\b",
            re.I,
        ),
    ),
    (
        "subjective community ranking",
        re.compile(
            r"\b(?:best|perfect|ideal|top[- ]rated|most desirable|exclusive|prestigious|"
            r"prestige|elite|affluent|wealthy|upscale|premier|premium|top[- ]tier|"
            r"up[- ]and[- ]coming|hidden gem|hot|"
            r"quiet(?:er)?|tight[- ]knit|diverse|inclusive)\s+"
            r"(?:(?:NJ|New Jersey)\s+)?(?:town|community|neighbou?rhood|suburb|place|area|street)s?\b|"
            r"\bone of (?:New Jersey|NJ|the (?:state|county))[^.<\n]{0,40}"
            r"\b(?:best|safest|most desirable)\b|"
            r"\b(?:town|community|neighbou?rhood|suburb|place|area|street)s?[^.<\n]{0,35}"
            r"\b(?:exclusive|prestigious|affluent|wealthy|upscale|quiet(?:er)?|tight[- ]knit|"
            r"diverse|inclusive)\b|"
            r"\b(?:town|community|neighbou?rhood|suburb)s?[^.<\n]{0,25}"
            r"\b(?:premium|premier|top[- ]tier)\b",
            re.I,
        ),
    ),
    (
        "school-value proxy",
        re.compile(
            r"\b(?:school|district)[^.<\n]{0,70}\b(?:premium|"
            r"drives?\s+(?:demand|home values?|property values?)|"
            r"protects?\s+(?:values?|resale)|boosts?\s+(?:values?|demand))\b",
            re.I,
        ),
    ),
    (
        "demographic preference",
        re.compile(
            r"\b(?:predominantly|primarily)\s+(?:white|black|asian|hispanic|latino|"
            r"christian|jewish|muslim|family|families)|\b(?:affluent|wealthy)\s+families\b|"
            r"\b(?:neighbor|buyer|community|town|suburb|resident)[A-Za-z-]*[^.<\n]{0,45}"
            r"\bdemographic(?:s|ally)?\b|\bdemographic\s+profile\b|"
            r"\bintegrated\s+suburbs?\b|\bacross\s+race[^.<\n]{0,35}\borientation\b",
            re.I,
        ),
    ),
)


@dataclass(frozen=True)
class Issue:
    path: str
    category: str
    match: str


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8", errors="replace")


def retired_files() -> set[str]:
    payload = json.loads(read("data/retired-legacy-daily-posts.json"))
    return {item["file"] for item in payload["pages"]}


def quarantined_files() -> set[str]:
    if not QUARANTINE_PATH.exists():
        return set()
    payload = json.loads(QUARANTINE_PATH.read_text(encoding="utf-8"))
    return {item["file"] for item in payload["pages"]}


def retired_programmatic_doorway_files() -> set[str]:
    if not PROGRAMMATIC_DOORWAY_PATH.exists():
        return set()
    payload = json.loads(PROGRAMMATIC_DOORWAY_PATH.read_text(encoding="utf-8"))
    return {item["file"] for item in payload["pages"]}


def discover_inventory() -> dict[str, list[str]]:
    excluded = {
        "rebuilt": [],
        "retired": [],
        "retired_programmatic_doorways": [],
        "market_reports": [],
        "redirects": [],
        "directories": [],
    }
    owned: list[str] = []
    retired = retired_files()
    retired_programmatic = retired_programmatic_doorway_files()
    quarantined = quarantined_files()
    for path in sorted(ROOT.rglob("*.html")):
        relative = path.relative_to(ROOT).as_posix()
        parts = path.relative_to(ROOT).parts
        if any(part in BUILD_OUTPUT_PARTS for part in parts):
            continue
        if any(part in SKIP_PARTS for part in parts):
            excluded["directories"].append(relative)
        elif relative in REBUILT_EXCLUSIONS:
            excluded["rebuilt"].append(relative)
        elif relative in retired:
            excluded["retired"].append(relative)
        elif relative in retired_programmatic:
            excluded["retired_programmatic_doorways"].append(relative)
        elif MARKET_REPORT.search(path.name):
            excluded["market_reports"].append(relative)
        elif relative in quarantined:
            owned.append(relative)
        elif REDIRECT_STUB.search(path.read_text(encoding="utf-8", errors="replace")):
            excluded["redirects"].append(relative)
        else:
            owned.append(relative)
    return {"owned": owned, **excluded}


def inventory_payload() -> dict[str, object]:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def scan_text(source: str) -> str:
    source = re.sub(r"<style\b[^>]*>.*?</style>", " ", source, flags=re.I | re.S)
    source = re.sub(
        r"<script\b(?![^>]*application/ld\+json)[^>]*>.*?</script>",
        " ",
        source,
        flags=re.I | re.S,
    )
    source = re.sub(r"<!--.*?-->", " ", source, flags=re.S)
    attributes: list[str] = []
    for tag in re.findall(r"<[^>]+>", source, flags=re.S):
        if re.match(r"<meta\b", tag, re.I):
            names = ("content",)
        else:
            names = ("alt", "aria-label", "title")
        for name in names:
            match = re.search(rf'\b{name}\s*=\s*(["\'])(.*?)\1', tag, re.I | re.S)
            if match:
                attributes.append(match.group(2))
    visible_and_jsonld = re.sub(
        r"</?(?:address|article|aside|blockquote|br|dd|div|dl|dt|fieldset|figcaption|"
        r"figure|footer|form|h[1-6]|header|hr|li|main|nav|ol|p|section|table|tbody|td|"
        r"tfoot|th|thead|tr|ul)\b[^>]*>",
        ". ",
        source,
        flags=re.I,
    )
    visible_and_jsonld = re.sub(r"<[^>]+>", " ", visible_and_jsonld)
    return html.unescape(". ".join([visible_and_jsonld, *attributes]))


def scan_file(relative: str) -> list[Issue]:
    source = read(relative)
    if relative == "generate_county_reports_and_comparisons.py":
        # The county-report generator is owned by a separate remediation batch.
        # This audit owns only its comparison definitions/template.
        source = source.split("# ============================ TOWN COMPARISONS", 1)[-1]
    candidate = scan_text(source)
    issues: list[Issue] = []
    for category, pattern in RISK_PATTERNS:
        for match in pattern.finditer(candidate):
            issues.append(Issue(relative, category, " ".join(match.group(0).split())))
    return issues


def blocking_issues() -> list[Issue]:
    payload = inventory_payload()
    reviewed = [str(item) for item in payload["reviewed"]]
    emitters = [str(item) for item in payload["emitters"]]
    return [issue for path in [*reviewed, *emitters] for issue in scan_file(path)]


def write_inventory() -> None:
    discovered = discover_inventory()
    emitters = sorted(SOURCE_EMITTERS | {p.relative_to(ROOT).as_posix() for p in (ROOT / "_posts").glob("*.md")})
    quarantined = sorted(quarantined_files())
    owned = set(discovered.pop("owned"))
    payload = {
        "base": "831c7918f9fcaad2496c4ea039ed1d8cc217038c",
        "reviewed": sorted(owned - set(quarantined)),
        "quarantined": quarantined,
        "emitters": emitters,
        "guarded_emitters": GUARDED_EMITTERS,
        "excluded": discovered,
    }
    INVENTORY_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-inventory", action="store_true")
    args = parser.parse_args()
    if args.write_inventory:
        write_inventory()
        print(f"wrote {INVENTORY_PATH.relative_to(ROOT)}")
        return 0
    issues = blocking_issues()
    for issue in issues:
        print(f"{issue.path}: {issue.category}: {issue.match}")
    print(f"English fair-housing audit: {len(issues)} issue(s)")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
