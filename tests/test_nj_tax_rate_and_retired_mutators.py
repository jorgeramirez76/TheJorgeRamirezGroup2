#!/usr/bin/env python3
"""Contracts for the source-led NJ tax-rate guide and retired mutators."""

from __future__ import annotations

import hashlib
import html
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
PAGE = ROOT / "blog" / "nj-property-tax-rate-vs-what-you-actually-pay.html"
ROUTE = "/blog/nj-property-tax-rate-vs-what-you-actually-pay"
REVIEWED_ON = "2026-08-27"

LEGACY_MUTATORS = (
    ROOT / "optimize_seo.py",
    ROOT / "fix_site_issues_v2.py",
    ROOT / "comprehensive_audit_and_fix.py",
    ROOT / "bulk_update_towns.py",
    ROOT / "finish_remaining_optimizations.py",
    ROOT / "fix_site_issues.py",
    ROOT / "fix_site_issues_v3.py",
    ROOT / "tools" / "seo-optimizer" / "internal_links.py",
)
SEO_DOCTOR = ROOT / "tools" / "seo-optimizer" / "seo_daily.py"
SEO_DOCTOR_README = ROOT / "tools" / "seo-optimizer" / "README.md"
SEO_DOCTOR_CONFIG = ROOT / "tools" / "seo-optimizer" / "config.json"
SEO_DOCTOR_MAIL_EXAMPLE = ROOT / "tools" / "seo-optimizer" / "mail.env.example"
OWNER_APPROVAL = "I_APPROVE_THIS_LOCAL_SEO_METADATA_PLAN"

STATS = "https://www.nj.gov/treasury/taxation/lpt/statdata.shtml"
RATES_2025 = "https://www.nj.gov/treasury/taxation/pdf/lpt/gtr/2025taxrates.pdf"
AVERAGES_2025 = (
    "https://www.nj.gov/treasury/taxation/pdf/lpt/class4/2025AvgResStat.pdf"
)
GENERAL_INFO = "https://www.nj.gov/treasury/taxation/lpt/genlpt.shtml"
APPEALS = "https://www.nj.gov/treasury/taxation/lpt/lpt-appeal.shtml"
TAXPAYER_RIGHTS = "https://www.nj.gov/treasury/taxation/lpt/lpt-tpbors.shtml"

EXPECTED_ROWS = {
    "Clark": ("2.269", "1.899", "$11,951", "$684,576.07"),
    "Cranford": ("7.248", "2.106", "$13,729", "$809,972.65"),
    "Rahway": ("7.584", "2.542", "$10,435", "$497,987.50"),
    "Roselle Park": ("4.506", "2.521", "$11,417", "$516,054.47"),
    "Scotch Plains": ("12.350", "2.137", "$15,818", "$878,329.03"),
    "Summit": ("4.471", "1.475", "$19,701", "$1,606,165.10"),
    "Westfield": ("2.292", "1.810", "$18,948", "$1,305,037.09"),
}

STALE_TAX_CLAIMS = re.compile(
    r"(?:"
    r"2024 general tax rates?|"
    r"\b(?:2\.214|2\.252|4\.287|4\.356|6\.779|11\.768)\b|"
    r"rates? (?:lie|lies)|wildly different rates?|five times|"
    r"summit is (?:the )?cheapest|lowest property taxes?|"
    r"only figure that compares|only version that compares|"
    r"actual (?:tax )?burdens? (?:are|is) far closer|"
    r"tells? you (?:almost )?nothing|"
    r"garden state mls|\bmls closed sales|roughly 30% low|"
    r"only if your assessment rises faster|moves? most bills? very little|"
    r"buying (?:at|above)[^.]{0,100}(?:does not|doesn't) automatically trigger|"
    r"median bill|median tax bill"
    r")",
    re.I,
)

UNSAFE_SCRIPT_LITERALS = re.compile(
    r"(?:"
    r"AggregateRating|ratingValue|reviewCount|"
    r"luxury homes|investment properties|AI-powered marketing|"
    r"A/8-9|Best value|Culture \+ diversity|"
    r"\$1\.3M-\$1\.5M|\$700K-\$750K|"
    r"38 min \(Midtown Direct\)|"
    r"500\+ buyers|\+90-180 clicks|130-260% increase|"
    r"3-7 days|4-8 weeks|traffic increases visible|"
    r"Somerset County Market Report \(coming soon\)|"
    r"Union \(21 towns\)|Morris \(33 towns\)|"
    r"school-district resources, transit times, median prices"
    r")",
    re.I,
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def visible_text(source: str) -> str:
    source = re.sub(
        r"<(?:script|style|template|noscript)\b[^>]*>.*?"
        r"</(?:script|style|template|noscript)>",
        " ",
        source,
        flags=re.I | re.S,
    )
    source = re.sub(r"<!--.*?-->", " ", source, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", source)).split())


def schema_nodes(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from schema_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from schema_nodes(child)


class IntegrityParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.external_rel_errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.casefold(): value or "" for key, value in attrs}
        if tag.casefold() == "a" and values.get("target") == "_blank":
            rel = set(values.get("rel", "").casefold().split())
            if not {"noopener", "noreferrer"} <= rel:
                self.external_rel_errors.append(values.get("href", ""))
        if values.get("id"):
            self.ids.append(values["id"])


class NjTaxRateAndRetiredMutatorsTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.source = read(PAGE)
        cls.text = visible_text(cls.source)

    def test_tax_page_preserves_canonical_intent_schema_and_lead_paths(self) -> None:
        source = self.source
        self.assertIn(f'<link rel="canonical" href="{SITE}{ROUTE}">', source)
        self.assertRegex(source, r'<meta\s+name="robots"\s+content="index, follow,')
        self.assertIn(f'<meta name="last-updated" content="{REVIEWED_ON}">', source)
        self.assertIn(
            '<meta name="ai-content-declaration" content="ai-assisted, source-checked">',
            source,
        )
        self.assertNotIn("human-reviewed", source.casefold())
        self.assertIn("G-KMS6H85LB0", source)
        self.assertIn('href="/css/styles.css?v=20260701b"', source)
        self.assertIn(
            "<title>NJ Property Tax Rate vs. Actual Bill: 2025 Source Guide</title>",
            source,
        )
        self.assertIn(
            '<meta name="description" content="Compare New Jersey general and effective tax rates with official 2025 municipal averages, then verify the current assessment and bill for a specific property.">',
            source,
        )
        for href in (
            "/home-valuation",
            "/buy-a-home",
            "/communities",
            "/blog/nj-property-tax-guide",
            "/blog/nj-property-taxes-lowest-commuter-towns-2026",
            "/tools/mortgage-calculator",
            "/closing-costs-calculator",
            "/blog/moving-from-nyc-to-nj-guide",
            "tel:+19082307844",
        ):
            self.assertIn(f'href="{href}"', source)

        blocks = [
            json.loads(block)
            for block in re.findall(
                r'<script\b[^>]*type="application/ld\+json"[^>]*>'
                r"(.*?)</script>",
                source,
                flags=re.I | re.S,
            )
        ]
        nodes = [node for block in blocks for node in schema_nodes(block)]
        types = {node.get("@type") for node in nodes}
        self.assertTrue(
            {"Organization", "Person", "WebPage", "Article", "BreadcrumbList"}
            <= types
        )
        self.assertFalse(
            types
            & {"FAQPage", "HowTo", "Review", "AggregateRating", "Service", "Offer"}
        )
        article = next(node for node in nodes if node.get("@type") == "Article")
        self.assertEqual(SITE + ROUTE, article.get("url"))
        self.assertEqual(REVIEWED_ON, article.get("dateModified"))
        self.assertEqual(
            {"@id": SITE + ROUTE + "#primaryimage"}, article.get("image")
        )
        self.assertIn(article["headline"], self.text)
        self.assertGreaterEqual(len(article.get("citation", [])), 6)

    def test_tax_page_uses_official_2025_definitions_and_exact_dated_rows(self) -> None:
        for url in (STATS, RATES_2025, AVERAGES_2025, GENERAL_INFO, APPEALS, TAXPAYER_RIGHTS):
            self.assertIn(url, self.source)
        lowered = self.text.casefold()
        for phrase in (
            "2025 General Tax Rates",
            "2025 Average Residential Statistics",
            "general tax rate is the multiplier",
            "effective tax rate is a statistical study",
            "not used to compute a tax bill",
            "municipal average, not a median",
            "not current listings",
            "not a parcel-specific bill",
            "verify the current parcel",
            "sources checked August 27, 2026",
            "no outcome is promised",
        ):
            self.assertIn(phrase.casefold(), lowered)

        table_body = visible_text(
            re.search(r"<tbody>(.*?)</tbody>", self.source, re.I | re.S).group(1)
        )
        positions = []
        for town, values in EXPECTED_ROWS.items():
            positions.append(table_body.index(town))
            for value in values:
                self.assertIn(value, table_body, f"{town}: {value}")
        self.assertEqual(positions, sorted(positions), "municipalities must be alphabetical")

    def test_tax_page_removes_stale_rankings_experiments_and_causal_promises(self) -> None:
        self.assertNotRegex(self.text, STALE_TAX_CLAIMS)
        self.assertNotRegex(self.source, r'"@type"\s*:\s*"FAQPage"')
        self.assertNotRegex(
            self.text,
            re.compile(
                r"(?:best|top|strong|weak|excellent|great|good) schools?|"
                r"(?:safe|safer|safest|low-crime) (?:town|community|area)",
                re.I,
            ),
        )

    def test_tax_page_keeps_homepage_palette_accessibility_and_html_integrity(self) -> None:
        parser = IntegrityParser()
        parser.feed(self.source)
        for token in (
            "#1A1A1A",
            "#2C2C2C",
            "#C41230",
            "#8B0D22",
            "#B8962E",
            "#FAFAF8",
            "#F8F6F2",
        ):
            self.assertIn(token, self.source)
        for family in ("Playfair Display", "Inter"):
            self.assertIn(family, self.source)
        self.assertEqual(1, len(re.findall(r"<h1\b", self.source, re.I)))
        self.assertEqual(1, len(re.findall(r'<main\b[^>]*id="main"', self.source, re.I)))
        self.assertIn('href="#main"', self.source)
        self.assertIn('tabindex="-1"', self.source)
        self.assertIn(":focus-visible", self.source)
        self.assertIn("min-height:44px", self.source.replace(" ", ""))
        self.assertFalse(parser.external_rel_errors)
        self.assertEqual(len(parser.ids), len(set(parser.ids)))

    def test_all_legacy_mutators_are_compulsorily_retired(self) -> None:
        failures = []
        for path in LEGACY_MUTATORS:
            source = read(path)
            if not re.search(r'^STATUS\s*=\s*["\']retired["\']$', source, re.M):
                failures.append(f"{path.name}: missing retired status")
            if not re.search(r"^MUTATION_ENABLED\s*=\s*False$", source, re.M):
                failures.append(f"{path.name}: mutation is not disabled")
            if "--check" not in source or "read-only" not in source.casefold():
                failures.append(f"{path.name}: missing read-only check contract")
            for write_token in (
                ".write_text(",
                ".write_bytes(",
                ".rename(",
                ".replace(",
                ".unlink(",
                "shutil.",
                "re.sub(",
                'rglob("*.html")',
                'glob("*.html")',
            ):
                if write_token in source:
                    failures.append(f"{path.name}: unsafe operation {write_token}")
            if UNSAFE_SCRIPT_LITERALS.search(source):
                failures.append(f"{path.name}: retains an unsafe literal payload")
        self.assertEqual([], failures)

    def test_retired_entrypoints_fail_closed_and_cannot_mutate_live_pages(self) -> None:
        # Do not execute an entry point until the static retirement guard is satisfied.
        for path in LEGACY_MUTATORS:
            source = read(path)
            self.assertIn('STATUS = "retired"', source, path.name)
            self.assertIn("MUTATION_ENABLED = False", source, path.name)

        sentinels = (
            PAGE,
            ROOT / "404.html",
            ROOT / "blog" / "best-nj-towns-for-families.html",
            ROOT / "towns" / "summit.html",
        )

        def fingerprints() -> dict[str, str]:
            return {
                str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sentinels
            }

        before = fingerprints()
        for path in LEGACY_MUTATORS:
            default = subprocess.run(
                [sys.executable, str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(2, default.returncode, path.name)
            self.assertIn("RETIRED", default.stderr, path.name)
            self.assertIn("does not modify files", default.stderr, path.name)

            check = subprocess.run(
                [sys.executable, str(path), "--check"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, check.returncode, path.name)
            record = json.loads(check.stdout)
            self.assertEqual("retired", record.get("status"), path.name)
            self.assertFalse(record.get("mutationEnabled"), path.name)
            self.assertTrue(record.get("readOnly"), path.name)
            self.assertGreaterEqual(len(record.get("replacementChecks", [])), 2, path.name)
        self.assertEqual(before, fingerprints())

    def test_seo_doctor_is_read_only_by_default_and_has_no_external_side_effects(self) -> None:
        source = read(SEO_DOCTOR)
        for contract in (
            'MODE = "read-only"',
            "NETWORK_ENABLED = False",
            "PUSH_ENABLED = False",
            "EMAIL_ENABLED = False",
            OWNER_APPROVAL,
            "--apply-plan",
            "--owner-approval",
        ):
            self.assertIn(contract, source)
        for unsafe in (
            "subprocess",
            "smtplib",
            "googleapiclient",
            "MIMEText",
            "sendmail(",
            "git(",
            "git push",
            "git pull",
            "urlInspection",
            "refresh(Request())",
            "searchconsole",
            "sitemaps().submit",
            "urllib.request",
            "requests.",
            "socket.",
        ):
            self.assertNotIn(unsafe, source)

        sentinels = (PAGE, ROOT / "sitemap.xml", ROOT / "index.html")
        before = {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sentinels
        }
        default = subprocess.run(
            [sys.executable, str(SEO_DOCTOR)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, default.returncode, default.stderr)
        report = json.loads(default.stdout)
        self.assertEqual("read-only", report.get("mode"))
        self.assertFalse(report.get("networkEnabled"))
        self.assertFalse(report.get("mutationEnabled"))

        unauthorized = subprocess.run(
            [
                sys.executable,
                str(SEO_DOCTOR),
                "--apply-plan",
                "missing-plan.json",
                "--owner-approval",
                "not-approved",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(2, unauthorized.returncode)
        self.assertIn("exact owner approval", unauthorized.stderr.casefold())
        after = {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sentinels
        }
        self.assertEqual(before, after)

    def test_seo_doctor_docs_and_config_cannot_schedule_or_enable_writes(self) -> None:
        readme = read(SEO_DOCTOR_README)
        config = json.loads(read(SEO_DOCTOR_CONFIG))
        mail_notice = read(SEO_DOCTOR_MAIL_EXAMPLE)
        for required in (
            "read-only by default",
            "explicit local metadata plan",
            OWNER_APPROVAL,
            "never commits, pulls, pushes, deploys, emails, or submits",
        ):
            self.assertIn(required.casefold(), readme.casefold())
        self.assertNotRegex(
            readme,
            re.compile(
                r"launchctl|launchagent|every morning|auto-fix|auto-fixes|"
                r"smtp|gmail app password|--no-push|--no-email",
                re.I,
            ),
        )
        self.assertEqual("read-only", config.get("mode"))
        for key in (
            "network_enabled",
            "external_writes_enabled",
            "push_enabled",
            "email_enabled",
            "scheduled_run_enabled",
        ):
            self.assertIs(config.get(key), False, key)
        self.assertNotIn("report_email", config)
        self.assertNotIn("max_auto_edits_per_day", config)
        self.assertIn("Email delivery was retired", mail_notice)
        self.assertNotRegex(mail_notice, re.compile(r"SMTP_|GMAIL_|@gmail|password", re.I))

    def test_seo_doctor_apply_is_hash_pinned_allowlisted_and_local_only(self) -> None:
        spec = importlib.util.spec_from_file_location("safe_seo_daily", SEO_DOCTOR)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            target = temporary_root / "reviewed.html"
            original = (
                '<!doctype html><html><head><title>Reviewed</title></head>'
                '<body><main><h1>Reviewed</h1></main></body></html>'
            )
            target.write_text(original, encoding="utf-8")
            plan = temporary_root / "plan.json"
            plan.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "changes": [
                            {
                                "path": "reviewed.html",
                                "sha256": hashlib.sha256(original.encode()).hexdigest(),
                                "metadata": {
                                    "description": "Reviewed & property-specific.",
                                    "twitter:card": "summary_large_image",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            module.REPO = temporary_root.resolve()
            result = module.apply_reviewed_plan(plan, OWNER_APPROVAL)
            updated = target.read_text(encoding="utf-8")
            self.assertEqual(["reviewed.html"], result["changed"])
            self.assertIn(
                '<meta name="description" content="Reviewed &amp; property-specific.">',
                updated,
            )
            self.assertIn(
                '<meta name="twitter:card" content="summary_large_image">',
                updated,
            )
            self.assertNotIn("git", json.dumps(result).casefold())
            self.assertFalse(result["networkEnabled"])
            self.assertFalse(result["pushEnabled"])
            self.assertFalse(result["emailEnabled"])

            with self.assertRaisesRegex(ValueError, "content hash changed"):
                module.apply_reviewed_plan(plan, OWNER_APPROVAL)

            retired = temporary_root / "retired.html"
            retired_source = (
                '<!doctype html><html><head><meta content="noindex, follow" '
                'name="robots"><title>Retired</title></head><body></body></html>'
            )
            retired.write_text(retired_source, encoding="utf-8")
            retired_plan = temporary_root / "retired-plan.json"
            retired_plan.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "changes": [
                            {
                                "path": "retired.html",
                                "sha256": hashlib.sha256(
                                    retired_source.encode()
                                ).hexdigest(),
                                "metadata": {"description": "Must remain retired."},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "retired/noindex"):
                module.apply_reviewed_plan(retired_plan, OWNER_APPROVAL)
            self.assertEqual(retired_source, retired.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
