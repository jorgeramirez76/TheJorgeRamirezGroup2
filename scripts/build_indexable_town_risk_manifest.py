#!/usr/bin/env python3
"""Audit or rebuild the managed town decision manifest from legacy evidence.

The default mode is a read-only action-inventory check. Snapshot writes require
``--write-snapshot`` and are accepted only on the exact pre-remediation
integration base, where the legacy pages still contain the evidence this tool
was designed to capture. The two filtered Search Console fixtures make the
numerical decision reproducible in CI without shipping or requiring access to
a Search Console account.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://thejorgeramirezgroup.com"
DEFAULT_COMPARE = Path(
    "/Users/teddy/Documents/Codex/2026-08-25/t/work/gsc_compare/Pages.csv"
)
DEFAULT_HISTORICAL = Path(
    "/Users/teddy/Documents/Codex/2026-08-25/t/work/gsc16/Pages.csv"
)
COMPARE_FIXTURE = ROOT / "tests" / "fixtures" / "gsc-indexable-town-pages.csv"
HISTORICAL_FIXTURE = (
    ROOT / "tests" / "fixtures" / "gsc-indexable-town-pages-16m.csv"
)
MANIFEST = ROOT / "data" / "indexable-town-risk-decisions.json"
EXPECTED_PRE_REMEDIATION_BASE = "2411cafd7e658b29ede321d99bc75abb1f958818"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.check_indexable_town_risks import fold_gsc_rows, lint_source  # noqa: E402


CANDIDATES = {
    "basking-ridge", "bernards-township", "boonton-township", "caldwell", "chatham",
    "dunellen", "edison", "elizabeth", "florham-park", "glen-ridge", "hoboken",
    "jefferson", "jersey-city", "livingston", "long-hill", "madison", "maplewood",
    "metuchen", "middlesex-borough", "millburn", "montclair", "morris-township",
    "morristown", "mountainside", "new-brunswick", "newark", "north-caldwell",
    "nutley", "parsippany-troy-hills", "peapack-gladstone", "perth-amboy", "plainfield",
    "plainsboro", "roselle", "scotch-plains", "short-hills", "south-orange", "summit",
    "union", "washington-township-morris", "weehawken", "west-orange", "westfield", "wharton",
}
REBUILDS = {
    "basking-ridge", "chatham", "hoboken", "jersey-city", "madison", "maplewood",
    "millburn", "montclair", "morristown", "newark", "summit", "westfield",
}
REDIRECTS = {
    "bernards-township": "/towns/basking-ridge",
    "middlesex-borough": "/towns/middlesex",
    "short-hills": "/towns/millburn",
}
QUARANTINES = CANDIDATES - REBUILDS - set(REDIRECTS)

COMPARE_PERIODS = {
    "current3m": {
        "clicks": "Last 3 months Clicks",
        "impressions": "Last 3 months Impressions",
        "position": "Last 3 months Position",
    },
    "previous3m": {
        "clicks": "Previous 3 months Clicks",
        "impressions": "Previous 3 months Impressions",
        "position": "Previous 3 months Position",
    },
}
HISTORICAL_PERIODS = {
    "last16m": {
        "clicks": "Clicks",
        "impressions": "Impressions",
        "position": "Position",
    }
}

SHARED = {
    "property": {
        "category": "property",
        "publisher": "New Jersey Division of Taxation",
        "url": "https://www.nj.gov/treasury/taxation/lpt/statdata.shtml",
        "fact_supported": "The state publishes year-labeled local property-tax and assessment files for independent research.",
        "accessed": "2026-08-26",
    },
    "school": {
        "category": "education",
        "publisher": "New Jersey Department of Education",
        "url": "https://www.nj.gov/education/schoolperformance/",
        "fact_supported": "The state provides School Performance Reports with reporting-period and methodology context.",
        "accessed": "2026-08-26",
    },
    "flood": {
        "category": "property",
        "publisher": "New Jersey Department of Environmental Protection",
        "url": "https://dep.nj.gov/flooddisclosure/",
        "fact_supported": "The state provides flood-disclosure guidance and address-based research tools.",
        "accessed": "2026-08-26",
    },
    "transit": {
        "category": "transit",
        "publisher": "NJ TRANSIT",
        "url": "https://www.njtransit.com/trip-planner-to",
        "fact_supported": "The official trip planner provides date- and time-specific itinerary research.",
        "accessed": "2026-08-26",
    },
}


def source(
    category: str, publisher: str, url: str, fact_supported: str
) -> dict[str, str]:
    return {
        "category": category,
        "publisher": publisher,
        "url": url,
        "fact_supported": fact_supported,
        "accessed": "2026-08-26",
    }


REBUILD_DETAILS: dict[str, dict[str, object]] = {
    "basking-ridge": {
        "displayName": "Basking Ridge",
        "county": "Somerset",
        "placeType": "community within Bernards Township",
        "identity": "Basking Ridge is a community within Bernards Township in Somerset County. Use the Bernards Township municipality, assessor, and land-use records for an address rather than treating Basking Ridge as a separate municipality.",
        "researchFocus": [
            "Confirm Bernards Township, block, and lot from the property record.",
            "Review the municipal zoning and permit sources for the specific parcel.",
            "For Gladstone Branch planning, check the current NJ TRANSIT schedule for the date and train under consideration.",
        ],
        "comparisonSourceKey": "basking-ridge-bernards-township",
    },
    "chatham": {
        "displayName": "Chatham",
        "county": "Morris",
        "placeType": "name shared by two municipalities",
        "identity": "Chatham Borough and Chatham Township are separate municipalities in Morris County. A mailing address alone may not identify which assessor, zoning office, permit record, or local rule applies, so begin with the parcel municipality.",
        "researchFocus": [
            "Confirm whether the address is in Chatham Borough or Chatham Township.",
            "Use the matching municipal assessor and land-use resources for that parcel.",
            "Use official station and date-specific service sources when transportation affects the decision.",
        ],
        "comparisonSourceKey": "chatham-borough-and-township",
    },
    "hoboken": {
        "displayName": "Hoboken",
        "county": "Hudson",
        "placeType": "city",
        "identity": "Hoboken is a city in Hudson County. Address-level research should start with City zoning, assessment, permit, and flood-disclosure sources and should not rely on a neighborhood label as a substitute for parcel records.",
        "researchFocus": [
            "Match the address to the City tax map and assessment record.",
            "Review zoning, permits, and any association documents that apply to the property.",
            "Check official PATH or NJ TRANSIT sources for the exact date and route being considered.",
        ],
        "sources": [
            source("municipality", "City of Hoboken", "https://www.hobokennj.gov/", "Official City government and department directory for Hoboken."),
            source("property", "City of Hoboken Tax Assessor", "https://www.hobokennj.gov/resources/tax-assessor", "Official assessment map, ownership-record, and assessor starting point."),
            source("land-use", "City of Hoboken Zoning Office", "https://www.hobokennj.gov/departments/zoning-office", "Official zoning code, map, application, and verification resources."),
            source("census", "U.S. Census Bureau", "https://www.census.gov/quickfacts/fact/table/hobokencitynewjersey/PST045225", "Official Census geography profile for Hoboken city."),
            source("transit", "Port Authority of New York and New Jersey", "https://www.panynj.gov/path/en/schedules-maps.html", "Official PATH schedules and maps for date-specific trip research."),
            SHARED["flood"],
        ],
    },
    "jersey-city": {
        "displayName": "Jersey City",
        "county": "Hudson",
        "placeType": "city",
        "identity": "Jersey City is a city in Hudson County. The City publishes address-oriented planning, zoning, redevelopment, assessment, and tax-map resources; verify the parcel rather than inferring rules from a neighborhood name.",
        "researchFocus": [
            "Use the City address and zoning tools to identify parcel-specific land-use rules.",
            "Review assessment, permit, redevelopment-plan, and association records that apply.",
            "Use official PATH or NJ TRANSIT tools for the exact trip and date being evaluated.",
        ],
        "sources": [
            source("municipality", "City of Jersey City", "https://www.jerseycitynj.gov/", "Official City government and department directory for Jersey City."),
            source("land-use", "Jersey City Division of City Planning", "https://www.jerseycitynj.gov/CityHall/HousingAndDevelopment/cityplanning", "Official planning, zoning-map, redevelopment-plan, and application resources."),
            source("property", "Jersey City Tax Assessor", "https://www.jerseycitynj.gov/residentresources/TaxAssessor", "Official assessment and tax-map research starting point."),
            source("census", "U.S. Census Bureau", "https://www.census.gov/quickfacts/fact/table/jerseycitycitynewjersey/PST045225", "Official Census geography profile for Jersey City."),
            source("transit", "Port Authority of New York and New Jersey", "https://www.panynj.gov/path/en/schedules-maps.html", "Official PATH schedules and maps for date-specific trip research."),
            SHARED["flood"],
        ],
    },
    "madison": {
        "displayName": "Madison",
        "county": "Morris",
        "placeType": "borough",
        "identity": "Madison is a borough in Morris County. Use Borough, county, state, and property-specific records to evaluate an address; a general town page cannot establish a parcel condition, cost, or outcome.",
        "researchFocus": [
            "Confirm the parcel, assessment record, zoning district, and permit history.",
            "Check municipal maps and public notices for address-specific context.",
            "Use current official rail tools for the exact travel date and service pattern.",
        ],
        "comparisonSourceKey": "madison",
    },
    "maplewood": {
        "displayName": "Maplewood",
        "county": "Essex",
        "placeType": "township",
        "identity": "Maplewood is a township in Essex County. Parcel, zoning, assessment, permit, and transportation research should be tied to the address and current official records.",
        "researchFocus": [
            "Match the address to municipal zoning, assessment, and permit records.",
            "Review official district-boundary information only if it matters to the buyer's own criteria.",
            "Check current official station and trip-planning information for the relevant date.",
        ],
        "comparisonSourceKey": "maplewood",
    },
    "millburn": {
        "displayName": "Millburn Township",
        "county": "Essex",
        "placeType": "township that includes Short Hills",
        "identity": "Short Hills is a community within Millburn Township in Essex County. Municipal, assessment, land-use, and Census research for a Short Hills address belongs under Millburn Township.",
        "researchFocus": [
            "Confirm Millburn Township, block, and lot even when the mailing label says Short Hills.",
            "Review Township zoning, assessment, permit, and flood-disclosure sources.",
            "Use the official station and trip tools for the exact service date being considered.",
        ],
        "comparisonSourceKey": "millburn-short-hills",
    },
    "montclair": {
        "displayName": "Montclair",
        "county": "Essex",
        "placeType": "township",
        "identity": "Montclair is a township in Essex County. Because land-use, assessment, permit, station, and property conditions are address-specific, use the official sources below for the parcel under review.",
        "researchFocus": [
            "Confirm the assessment record, block, lot, and zoning district for the address.",
            "Review permit, historic-preservation, and flood records when applicable.",
            "Use current NJ TRANSIT tools for the station, train, and date under consideration.",
        ],
        "sources": [
            source("municipality", "Township of Montclair", "https://www.montclairnjusa.org/", "Official Township government and department directory for Montclair."),
            source("property", "Township of Montclair Municipal Assessor", "https://www.montclairnjusa.org/Government/Departments/Finance-and-Taxes/Municipal-Assessor", "Official assessor contacts and assessment-research starting point."),
            source("census", "U.S. Census Bureau", "https://www.census.gov/quickfacts/fact/table/montclairtownshipessexcountynewjersey/PST045225", "Official Census geography profile for Montclair Township."),
            SHARED["transit"],
            SHARED["school"],
            SHARED["flood"],
        ],
    },
    "morristown": {
        "displayName": "Morristown",
        "county": "Morris",
        "placeType": "town",
        "identity": "Morristown is a town in Morris County and is separate from Morris Township. Confirm the parcel municipality before using assessor, zoning, permit, or local-service records.",
        "researchFocus": [
            "Confirm Morristown rather than Morris Township from the parcel record.",
            "Review Town land-use, assessment, permit, and public-notice sources.",
            "Use current official station and trip-planning information for the relevant date.",
        ],
        "sources": [
            source("municipality", "Town of Morristown", "https://www.townofmorristown.org/", "Official Town government, department, and public-record directory."),
            source("land-use", "Town of Morristown Planning Division", "https://www.townofmorristown.org/departments/planning_division/index.php", "Official planning, redevelopment, and master-plan research starting point."),
            source("census", "U.S. Census Bureau", "https://www.census.gov/quickfacts/fact/table/morristowntownnewjersey/PST045225", "Official Census geography profile for Morristown town."),
            source("transit", "NJ TRANSIT", "https://www.njtransit.com/station/morristown-station", "Official Morristown Station information for current trip research."),
            SHARED["property"],
            SHARED["flood"],
        ],
    },
    "newark": {
        "displayName": "Newark",
        "county": "Essex",
        "placeType": "city",
        "identity": "Newark is a city in Essex County. City planning, zoning, assessment, permit, redevelopment, and property records should be checked for the specific address and use under consideration.",
        "researchFocus": [
            "Identify the parcel, zoning district, and any applicable redevelopment plan.",
            "Review assessment, permit, title, flood, and building-specific records.",
            "Use current official transit tools for the exact origin, destination, and date.",
        ],
        "sources": [
            source("municipality", "City of Newark", "https://www.newarknj.gov/", "Official City government and department directory for Newark."),
            source("land-use", "City of Newark Department of Economic and Housing Development", "https://www.newarknj.gov/departments/economichousing", "Official City starting point for planning, zoning, housing, and development resources."),
            source("census", "U.S. Census Bureau", "https://www.census.gov/quickfacts/fact/table/newarkcitynewjersey/PST045225", "Official Census geography profile for Newark city."),
            source("transit", "NJ TRANSIT", "https://www.njtransit.com/station/newark-penn-station", "Official Newark Penn Station information for current trip research."),
            SHARED["property"],
            SHARED["flood"],
        ],
    },
    "summit": {
        "displayName": "Summit",
        "county": "Union",
        "placeType": "city",
        "identity": "Summit is a city in Union County. Use City and state sources for parcel, zoning, assessment, permit, and transportation research rather than relying on an area-wide estimate.",
        "researchFocus": [
            "Confirm the parcel record, zoning district, and permit history.",
            "Review official municipal maps and notices that apply to the address.",
            "Use the current official station and trip tools for the relevant date.",
        ],
        "comparisonSourceKey": "summit",
    },
    "westfield": {
        "displayName": "Westfield",
        "county": "Union",
        "placeType": "town",
        "identity": "Westfield is a town in Union County. A useful property comparison starts with the address, parcel, zoning, assessment, permit, and current transportation records—not a town-wide promise.",
        "researchFocus": [
            "Match the address to the assessment record, zoning district, and permit history.",
            "Review official maps, notices, and property disclosures that apply.",
            "Use current official station and trip-planning information for the relevant date.",
        ],
        "comparisonSourceKey": "westfield",
    },
}

INCOMING_REDIRECTS = [
    ("/blog/neighborhoods-maplewood-nj", "/counties/essex-county"),
    ("/blog/neighborhoods-livingston-nj", "/counties/essex-county"),
    ("/blog/neighborhoods-montclair-nj", "/counties/essex-county"),
    ("/blog/neighborhoods-millburn-nj", "/counties/essex-county"),
    ("/blog/neighborhoods-summit-nj", "/counties/union-county"),
    ("/blog/neighborhoods-scotch-plains-nj", "/counties/union-county"),
    ("/blog/neighborhoods-basking-ridge-nj", "/counties/somerset-county"),
    ("/blog/neighborhoods-madison-nj", "/counties/morris-county"),
    ("/blog/buying-home-montclair-nj-2026", "/buy-a-home"),
    ("/blog/buying-home-randolph-nj-2026", "/buy-a-home"),
    ("/blog/buying-home-jersey-city-nj-2026", "/buy-a-home"),
    ("/blog/buying-home-rahway-nj-2026", "/buy-a-home"),
    ("/blog/selling-home-maplewood-nj-2026", "/sell-your-home"),
]


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag.casefold() != "a":
            return
        values = {key.casefold(): value or "" for key, value in attrs}
        if values.get("href"):
            self.hrefs.append(values["href"])


def canonical_town(value: str) -> str | None:
    path = urlsplit(value).path.rstrip("/")
    if path.endswith(".html"):
        path = path[:-5]
    match = re.fullmatch(r"/towns/([^/]+)", path)
    if not match or match.group(1) not in CANDIDATES:
        return None
    return f"/towns/{match.group(1)}"


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise RuntimeError(f"{path}: missing CSV header")
        return list(reader.fieldnames), list(reader)


def filter_english_town_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if canonical_town(row.get("Top pages") or "")]


def write_fixture(
    path: Path, fieldnames: list[str], rows: list[dict[str, str]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def link_evidence() -> dict[str, dict[str, object]]:
    inbound: dict[str, set[str]] = defaultdict(set)
    for path in ROOT.rglob("*.html"):
        if any(part in {".git", ".vercel", "node_modules"} for part in path.parts):
            continue
        parser = LinkParser()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        relative = str(path.relative_to(ROOT))
        for href in parser.hrefs:
            if href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            absolute = urljoin(SITE + "/", href)
            if urlsplit(absolute).netloc not in {
                "thejorgeramirezgroup.com",
                "www.thejorgeramirezgroup.com",
            }:
                continue
            route = canonical_town(absolute)
            if route and relative != f"towns/{route.removeprefix('/towns/')}.html":
                inbound[route].add(relative)

    evidence: dict[str, dict[str, object]] = {}
    official_suffixes = (".gov", ".nj.us", "nj.gov", "census.gov", "njtransit.com")
    for slug in sorted(CANDIDATES):
        route = f"/towns/{slug}"
        parser = LinkParser()
        parser.feed(
            (ROOT / "towns" / f"{slug}.html").read_text(
                encoding="utf-8", errors="replace"
            )
        )
        external_hosts = sorted(
            {
                urlsplit(urljoin(SITE + "/", href)).netloc.casefold()
                for href in parser.hrefs
                if urlsplit(urljoin(SITE + "/", href)).scheme in {"http", "https"}
                and urlsplit(urljoin(SITE + "/", href)).netloc.casefold()
                not in {"thejorgeramirezgroup.com", "www.thejorgeramirezgroup.com"}
            }
        )
        official_count = sum(
            host.endswith(official_suffixes) for host in external_hosts
        )
        evidence[slug] = {
            "snapshotBase": git_head(),
            "internalInboundCount": len(inbound[route]),
            "internalInboundExamples": sorted(inbound[route])[:12],
            "legacyExternalHosts": external_hosts,
            "legacyOfficialSourceLinkCount": official_count,
            "externalBacklinkEvidence": "not available in supplied exports",
        }
    return evidence


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def export_metadata(
    source_path: Path,
    fixture_path: Path,
    periods: dict[str, dict[str, str]],
) -> dict[str, object]:
    modified = datetime.fromtimestamp(source_path.stat().st_mtime).astimezone()
    return {
        "sourceLabel": str(source_path),
        "sourceModified": modified.isoformat(timespec="seconds"),
        "sourceSha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "committedFixture": str(fixture_path.relative_to(ROOT)),
        "periods": periods,
        "endpointCaveat": "The export supplies relative period labels, not exact start and end dates.",
    }


def rebuild_sources() -> dict[str, list[dict[str, str]]]:
    comparison = json.loads(
        (ROOT / "data" / "nj-town-comparison-sources.json").read_text(
            encoding="utf-8"
        )
    )["towns"]
    resolved: dict[str, list[dict[str, str]]] = {}
    for slug, details in REBUILD_DETAILS.items():
        if "sources" in details:
            resolved[slug] = list(details["sources"])
        else:
            resolved[slug] = list(
                comparison[str(details["comparisonSourceKey"])]["sources"]
            )
    return resolved


def check_action_inventory() -> list[str]:
    """Compare the historical builder's action partition with the live owner."""
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    decisions = document.get("decisions")
    if not isinstance(decisions, dict):
        return ["managed manifest lacks a decisions object"]

    actual_rebuilds = {
        slug for slug, item in decisions.items()
        if isinstance(item, dict) and item.get("action") == "rebuild"
    }
    actual_redirects = {
        slug: str(item.get("destination", ""))
        for slug, item in decisions.items()
        if isinstance(item, dict) and item.get("action") == "redirect"
    }
    actual_quarantines = {
        slug for slug, item in decisions.items()
        if isinstance(item, dict) and item.get("action") == "quarantine"
    }

    failures: list[str] = []
    if set(decisions) != CANDIDATES:
        failures.append("candidate inventory differs from the managed manifest")
    if actual_rebuilds != REBUILDS:
        failures.append("rebuild inventory differs from the managed manifest")
    if actual_redirects != REDIRECTS:
        failures.append("redirect inventory differs from the managed manifest")
    if actual_quarantines != QUARANTINES:
        failures.append("quarantine inventory differs from the managed manifest")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", type=Path, default=DEFAULT_COMPARE)
    parser.add_argument("--historical", type=Path, default=DEFAULT_HISTORICAL)
    parser.add_argument(
        "--write-snapshot",
        action="store_true",
        help="rewrite fixtures and the manifest on the recorded legacy base",
    )
    args = parser.parse_args()

    if len(CANDIDATES) != 44 or len(REBUILDS) != 12 or len(REDIRECTS) != 3:
        raise RuntimeError("managed town action inventory changed unexpectedly")
    if CANDIDATES != REBUILDS | set(REDIRECTS) | QUARANTINES:
        raise RuntimeError("managed town action inventory is incomplete")

    action_failures = check_action_inventory()
    if action_failures:
        print("\n".join(action_failures), file=sys.stderr)
        return 1
    if not args.write_snapshot:
        print(
            "read-only action check passed: 44 routes, 12 rebuilds, "
            "3 redirects, 29 quarantines"
        )
        return 0
    if git_head() != EXPECTED_PRE_REMEDIATION_BASE:
        print(
            "snapshot write refused: this checkout is not the recorded "
            f"pre-remediation base {EXPECTED_PRE_REMEDIATION_BASE}",
            file=sys.stderr,
        )
        return 2

    compare_fields, compare_rows = read_rows(args.comparison)
    historical_fields, historical_rows = read_rows(args.historical)
    compare_filtered = filter_english_town_rows(compare_rows)
    historical_filtered = filter_english_town_rows(historical_rows)
    write_fixture(COMPARE_FIXTURE, compare_fields, compare_filtered)
    write_fixture(HISTORICAL_FIXTURE, historical_fields, historical_filtered)

    comparison = fold_gsc_rows(compare_filtered, CANDIDATES, COMPARE_PERIODS)
    historical = fold_gsc_rows(
        historical_filtered, CANDIDATES, HISTORICAL_PERIODS
    )
    links = link_evidence()
    sources = rebuild_sources()

    decisions: dict[str, dict[str, object]] = {}
    for slug in sorted(CANDIDATES):
        source_text = (ROOT / "towns" / f"{slug}.html").read_text(
            encoding="utf-8", errors="replace"
        )
        legacy_risks = sorted({item["rule"] for item in lint_source(source_text)})
        route = f"/towns/{slug}"
        if slug in REBUILDS:
            action = "rebuild"
            if slug == "basking-ridge":
                reason = (
                    "Relationship exception: this route is the stronger measured Basking Ridge/Bernards family and can accurately explain that Basking Ridge is within Bernards Township."
                )
            else:
                reason = (
                    "The route met the measured-demand rule and is retained with only official-source, property-specific research framing."
                )
        elif slug in REDIRECTS:
            action = "redirect"
            reason = (
                "The destination is the stronger same-intent route and resolves the duplicated geography without a second indexable page."
            )
        else:
            action = "quarantine"
            reason = (
                "The route earned no clicks and fewer than 100 impressions in each supplied comparison period; its generated legacy page had blocked risk and no official citations."
            )

        decision: dict[str, object] = {
            "action": action,
            "reason": reason,
            "gsc": {
                **comparison[route],
                **historical[route],
            },
            "linkEvidence": links[slug],
            "legacyRiskRules": legacy_risks,
        }
        if action == "rebuild":
            decision.update(REBUILD_DETAILS[slug])
            decision.pop("comparisonSourceKey", None)
            decision["sources"] = sources[slug]
        elif action == "redirect":
            decision["destination"] = REDIRECTS[slug]
        decisions[slug] = decision

    manifest = {
        "schemaVersion": 1,
        "effectiveDate": "2026-08-26",
        "scope": "Remaining indexable English town pages identified by the layer-aware fair-housing and factual-risk audit.",
        "preRemediationBase": git_head(),
        "decisionPolicy": {
            "measuredDemandRule": "clicks in either comparison period > 0 OR impressions in either comparison period >= 100",
            "relationshipException": "Basking Ridge is retained as the stronger measured Basking Ridge/Bernards route and explicitly identified as a community within Bernards Township.",
            "quarantineHandling": "compact noindex, follow fallback; excluded from English sitemap and canonical town hubs; untranslated hreflang removed",
            "redirectHandling": "permanent one-hop redirect with noindex HTML fallback, mirrored for the Spanish route and legacy entry families",
            "historicalUse": "The 16-month export is recorded as context but does not override the two-period comparison rule.",
        },
        "gscExports": {
            "comparison": export_metadata(
                args.comparison, COMPARE_FIXTURE, COMPARE_PERIODS
            ),
            "historical": export_metadata(
                args.historical, HISTORICAL_FIXTURE, HISTORICAL_PERIODS
            ),
        },
        "incomingRedirectFamilies": [
            {
                "source": source_route,
                "destination": destination,
                "dependency": "stable indexable non-town target; independent of this town decision",
            }
            for source_route, destination in INCOMING_REDIRECTS
        ],
        "decisions": decisions,
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {MANIFEST.relative_to(ROOT)}: {len(REBUILDS)} rebuild, "
        f"{len(REDIRECTS)} redirect, {len(QUARANTINES)} quarantine"
    )
    print(
        f"filtered GSC rows: {len(compare_filtered)} comparison, "
        f"{len(historical_filtered)} historical"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
