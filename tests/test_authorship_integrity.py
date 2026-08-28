#!/usr/bin/env python3
"""Fail-closed authorship integrity contracts for indexable pages and renderers."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# These files are actively owned by other remediation tracks or explicitly queued.
# They remain visible to the coordinating full-site audit and must not be edited here.
OUT_OF_SCOPE = {
    "buy-a-home.html",
    "es/buy-a-home.html",
    "investment-property-nj.html",
    "es/investment-property-nj.html",
    "nj-home-seller-guide.html",
    "blog/why-new-yorkers-moving-to-nj-2026.html",
    "es/blog/moving-from-nyc-to-nj-guide.html",
    "net-proceeds-calculator.html",
    "es/net-proceeds-calculator.html",
    "luxury-homes-nj.html",
    "es/luxury-homes-nj.html",
    "55-plus-communities-nj.html",
    "es/55-plus-communities-nj.html",
    "downsizing-nj.html",
    "es/downsizing-nj.html",
    "blog/downsizing-your-nj-home.html",
    "es/blog/downsizing-your-nj-home.html",
    "blog/moving-from-jersey-city-hoboken-to-suburbs.html",
    "tools/blog-automation/template_source.html",
}

RENDERERS = (
    "tools/render_property_research_pages.py",
    "tools/render_moving_to_nj_checklist.py",
    "scripts/rebuild_commuter_suburbs_guide.py",
    "tools/generate_high_value_legal_fair_housing.py",
    "tools/generate_seller_editorial_rebuild.py",
    "tools/generate_town_market_research_essex_middlesex.py",
)

UNSUPPORTED = re.compile(
    r"(?:"
    r"\bhuman[- ]authored\b|\bhuman[- ]reviewed\b|"
    r"\breviewed\s+by\s+jorge(?:\s+ramirez)?\b|"
    r"\breviewed\b[^\"<\n]{0,100}\bby\s+jorge(?:\s+ramirez)?\b|"
    r"\bsource[- ]review(?:ed)?\s+by\s+jorge(?:\s+ramirez)?\b|"
    r"\bsource[- ]reviewed\b[^\"<\n]{0,160}\bby\s+jorge(?:\s+ramirez)?\b|"
    r"\brevisi[oó]n\s+por\s+jorge(?:\s+ramirez)?\b|"
    r"\brevisi[oó]n\s+de\s+fuentes\s+por\s+jorge(?:\s+ramirez)?\b|"
    r"\bp[aá]gina\s+educativa\b[^\"<\n]{0,160}\brevisada\b[^\"<\n]{0,80}\bpor\s+jorge(?:\s+ramirez)?\b|"
    r"\brevisad[oa]\s+por\s+jorge(?:\s+ramirez)?\b|"
    r"\brevisad[oa]\b[^\"<\n]{0,100}\bpor\s+jorge(?:\s+ramirez)?\b|"
    r"\bwritten\s+by\s+jorge(?:\s+ramirez)?\b|"
    r"\bauthored\s+by\s+jorge(?:\s+ramirez)?\b|"
    r"\bescrit[oa]\s+por\s+jorge(?:\s+ramirez)?\b|"
    r"\bredactad[oa]\s+por\s+jorge(?:\s+ramirez)?\b|"
    r"\brevisad[oa]\s+por\s+una\s+persona\b|"
    r"\bredactad[oa]\s+por\s+una\s+persona\b"
    r")",
    re.I,
)


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_indexable(source: str) -> bool:
    robots = re.search(
        r'<meta\s+[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']*)["\']',
        source,
        flags=re.I,
    )
    return not robots or "noindex" not in robots.group(1).casefold()


def schema_nodes(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from schema_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from schema_nodes(child)


class AuthorshipIntegrityTests(unittest.TestCase):
    maxDiff = None

    def test_indexable_html_does_not_claim_unsupported_human_authorship_or_review(self) -> None:
        offenders: list[str] = []
        for path in ROOT.rglob("*.html"):
            name = relative(path)
            if name.startswith((".git/", ".vercel/", "tmp/")) or name in OUT_OF_SCOPE:
                continue
            source = path.read_text(encoding="utf-8")
            if is_indexable(source) and UNSUPPORTED.search(source):
                offenders.append(name)
        self.assertEqual([], offenders)

    def test_deterministic_renderers_cannot_reintroduce_unsupported_claims(self) -> None:
        offenders = [name for name in RENDERERS if UNSUPPORTED.search((ROOT / name).read_text(encoding="utf-8"))]
        self.assertEqual([], offenders)

    def test_ai_authority_profiles_are_current_and_describe_services_factually(self) -> None:
        expected = {
            "ai-authority.html": (
                "https://thejorgeramirezgroup.com/ai-authority",
                "provides seller representation and buyer services",
            ),
            "es/ai-authority.html": (
                "https://thejorgeramirezgroup.com/es/ai-authority",
                "ofrece representación para vendedores y servicios para compradores",
            ),
        }
        for name, (url, phrase) in expected.items():
            source = (ROOT / name).read_text(encoding="utf-8")
            blocks = [json.loads(block) for block in re.findall(
                r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                source,
                flags=re.I | re.S,
            )]
            nodes = [node for block in blocks for node in schema_nodes(block)]
            profiles = [node for node in nodes if node.get("@type") == "ProfilePage"]
            agents = [node for node in nodes if node.get("@type") == "RealEstateAgent"]
            with self.subTest(path=name):
                self.assertEqual(1, len(profiles))
                self.assertEqual(url, profiles[0].get("url"))
                self.assertEqual("2026-08-27", profiles[0].get("dateModified"))
                self.assertEqual(1, len(agents))
                self.assertIn(phrase, str(agents[0].get("description", "")).casefold())
                self.assertNotIn("specializ", str(agents[0].get("description", "")).casefold())

    def test_ai_declarations_use_truthful_nonreviewer_language_on_key_surfaces(self) -> None:
        expected = {
            "index.html": "ai-assisted",
            "contact.html": "ai-assisted",
            "privacy-policy.html": "ai-assisted",
            "es/privacy-policy.html": "ai-assisted",
            "closing-costs-calculator.html": "ai-assisted, source-checked",
            "es/closing-costs-calculator.html": "ai-assisted, source-checked",
            "property-search.html": "ai-assisted, source-checked",
            "es/property-search.html": "ai-assisted, source-checked",
            "tools/market-comparison-widget.html": "ai-assisted, source-checked",
            "es/tools/market-comparison-widget.html": "ai-assisted, source-checked",
        }
        for name, declaration in expected.items():
            source = (ROOT / name).read_text(encoding="utf-8")
            with self.subTest(path=name):
                self.assertIn(
                    f'<meta name="ai-content-declaration" content="{declaration}">',
                    source,
                )


if __name__ == "__main__":
    unittest.main()
