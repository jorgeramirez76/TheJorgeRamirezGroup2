#!/usr/bin/env python3
"""Apply the audited publisher and contact provenance to five priority town guides."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "other-priority-town-sources.json"
SITE = "https://thejorgeramirezgroup.com"
ORGANIZATION_ID = f"{SITE}/#organization"
PERSON_ID = f"{SITE}/#jorge-ramirez"
PAGE_MODIFIED_ON = "2026-08-27"
TARGETS = (
    "bloomfield",
    "east-brunswick",
    "guttenberg",
    "south-brunswick",
    "west-new-york",
)
DECLARATION_RE = re.compile(
    r'^\s*<meta\s+name="ai-content-declaration"\s+content="[^"]*">\s*$',
    re.MULTILINE,
)
LLM_CONTEXT_RE = re.compile(r'^\s*<meta\s+name="llm-context"[^>]*>\s*$', re.MULTILINE)
SCHEMA_RE = re.compile(
    r'(?P<open><script\s+type="application/ld\+json">)'
    r'(?P<payload>.*?)'
    r'(?P<close></script>)',
    re.DOTALL,
)
BYLINE_RE = re.compile(r'<p\s+class="byline"(?:\s+data-content-provenance="v1")?>.*?</p>', re.DOTALL)


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, object]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if set(manifest.get("municipalities", {})) != set(TARGETS):
        raise ValueError("priority town manifest inventory changed")
    expected = {
        "publisher": "The Jorge Ramirez Group",
        "declaration": "ai-assisted, source-checked",
        "sourceCheckedDate": "2026-08-25",
        "responsibleContact": "Jorge Ramirez",
        "njRealEstateLicense": "1754604",
        "structuredDataRule": (
            "The WebPage publisher is the Organization; Jorge Ramirez is a Person "
            "who works for that Organization and is not represented as the page author or reviewer."
        ),
    }
    if manifest.get("provenancePolicy") != expected:
        raise ValueError("priority town provenance policy changed")
    return manifest


def organization_node(policy: dict[str, str]) -> dict[str, object]:
    return {
        "@type": "Organization",
        "@id": ORGANIZATION_ID,
        "name": policy["publisher"],
        "url": f"{SITE}/",
        "telephone": "+1-908-230-7844",
        "email": "jorge.ramirez@kw.com",
    }


def person_node(policy: dict[str, str]) -> dict[str, object]:
    return {
        "@type": "Person",
        "@id": PERSON_ID,
        "name": policy["responsibleContact"],
        "url": f"{SITE}/ai-authority",
        "jobTitle": "New Jersey real estate salesperson",
        "identifier": {
            "@type": "PropertyValue",
            "propertyID": "New Jersey real estate salesperson license",
            "value": policy["njRealEstateLicense"],
        },
        "worksFor": {"@id": ORGANIZATION_ID},
    }


def normalize_schema(source: str, policy: dict[str, str], relative: str) -> str:
    matches = list(SCHEMA_RE.finditer(source))
    if not matches:
        raise ValueError(f"{relative}: missing JSON-LD")
    match = matches[0]
    payload = json.loads(match.group("payload"))
    if not isinstance(payload, dict) or not isinstance(payload.get("@graph"), list):
        raise ValueError(f"{relative}: expected a JSON-LD graph")
    graph = [
        node
        for node in payload["@graph"]
        if not (isinstance(node, dict) and node.get("@id") in {ORGANIZATION_ID, PERSON_ID})
    ]
    web_pages = [node for node in graph if isinstance(node, dict) and node.get("@type") == "WebPage"]
    if len(web_pages) != 1:
        raise ValueError(f"{relative}: expected one WebPage node")
    web_pages[0]["publisher"] = {"@id": ORGANIZATION_ID}
    web_pages[0]["dateModified"] = PAGE_MODIFIED_ON
    payload["@graph"] = [organization_node(policy), person_node(policy), *graph]
    replacement = (
        match.group("open")
        + "\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n  "
        + match.group("close")
    )
    return source[: match.start()] + replacement + source[match.end() :]


def normalize_page(source: str, policy: dict[str, str], relative: str) -> str:
    declaration = f'  <meta name="ai-content-declaration" content="{policy["declaration"]}">'
    if DECLARATION_RE.search(source):
        source = DECLARATION_RE.sub(declaration, source, count=1)
    else:
        llm = LLM_CONTEXT_RE.search(source)
        if llm is None:
            raise ValueError(f"{relative}: missing llm-context insertion point")
        source = source[: llm.end()] + "\n" + declaration + source[llm.end() :]

    source = normalize_schema(source, policy, relative)
    bylines = list(BYLINE_RE.finditer(source))
    if len(bylines) != 1:
        raise ValueError(f"{relative}: expected one visible byline")
    visible = (
        '<p class="byline" data-content-provenance="v1">'
        "<strong>Published by The Jorge Ramirez Group.</strong> "
        "AI-assisted, source-checked August 25, 2026. "
        "Jorge Ramirez is a New Jersey real estate salesperson (license #1754604). "
        '<a href="/contact">Contact Jorge or request a correction.</a></p>'
    )
    return BYLINE_RE.sub(visible, source, count=1)


def expected_pages() -> dict[Path, str]:
    manifest = load_manifest()
    policy = manifest["provenancePolicy"]
    assert isinstance(policy, dict)
    rendered: dict[Path, str] = {}
    for slug in TARGETS:
        path = ROOT / "towns" / f"{slug}.html"
        rendered[path] = normalize_page(
            path.read_text(encoding="utf-8"),
            policy,
            path.relative_to(ROOT).as_posix(),
        )
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if a priority page lacks current provenance")
    args = parser.parse_args()
    try:
        rendered = expected_pages()
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        print(f"priority town provenance error: {error}", file=sys.stderr)
        return 2

    stale = [path for path, expected in rendered.items() if path.read_text(encoding="utf-8") != expected]
    if args.check:
        for path in stale:
            print(f"stale provenance: {path.relative_to(ROOT).as_posix()}", file=sys.stderr)
        if stale:
            return 1
        print(f"priority town provenance check passed ({len(rendered)} pages)")
        return 0

    for path in stale:
        path.write_text(rendered[path], encoding="utf-8")
    print(f"priority town provenance updated {len(stale)} of {len(rendered)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
