#!/usr/bin/env python3
"""Fail closed on the compiled Vercel routing order and static resolution contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_HOST = "thejorgeramirezgroup.com"
CANONICAL_ORIGIN = f"https://{CANONICAL_HOST}"
WWW_HOST = "www.thejorgeramirezgroup.com"
VERCEL_HOST = "thejorgeramirezgroup.vercel.app"

FORMER_BULK_REDIRECTS = [
    ("/blog/renting-vs-buying-nj-2026", "/rent-vs-buy-nj"),
    ("/blog/renting-vs-buying-nj-2026.html", "/rent-vs-buy-nj"),
    ("/best-real-estate-agents-essex-county-nj-2026", "/counties/essex-county"),
    ("/best-real-estate-agents-essex-county-nj-2026.html", "/counties/essex-county"),
    ("/best-real-estate-agents-morris-county-nj-2026", "/counties/morris-county"),
    ("/best-real-estate-agents-morris-county-nj-2026.html", "/counties/morris-county"),
]

EXPLICIT_CLEAN_URL_REDIRECTS = [
    {"source": "/:path*/index.html/", "destination": "/:path*", "permanent": True},
    {"source": "/:path*/index/", "destination": "/:path*", "permanent": True},
    {"source": "/:path*/index.html", "destination": "/:path*", "permanent": True},
    {"source": "/:path*/index", "destination": "/:path*", "permanent": True},
    {"source": "/(.*).html/", "destination": "/$1", "permanent": True},
    {"source": "/(.*).html", "destination": "/$1", "permanent": True},
    {"source": "/(.*)/", "destination": "/$1", "permanent": True},
]

EXPLICIT_STATIC_REWRITES = [
    {"source": "/", "destination": "/index.html"},
    {"source": "/(.*)", "destination": "/$1.html"},
    {"source": "/(.*)", "destination": "/$1/index.html"},
]

API_SOURCE_REDIRECT = {
    "source": "/api/lead.js",
    "destination": "/api/lead",
    "permanent": True,
}

DIRECTORY_INDEX_PREEMPTIONS = [
    {"source": "/communities/index.html/", "destination": "/communities", "permanent": True},
    {"source": "/communities/index/", "destination": "/communities", "permanent": True},
    {"source": "/communities/index.html", "destination": "/communities", "permanent": True},
    {"source": "/communities/index", "destination": "/communities", "permanent": True},
]


def source_contract_issues(config: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for key in ("cleanUrls", "trailingSlash", "bulkRedirectsPath"):
        if key in config:
            issues.append(f"vercel.json: platform-managed routing key remains: {key}")
    redirects = config.get("redirects")
    if not isinstance(redirects, list):
        return issues + ["vercel.json: redirects must be an array"]
    if redirects[-7:] != EXPLICIT_CLEAN_URL_REDIRECTS:
        issues.append("vercel.json: explicit clean URL normalizers must remain last")
    if config.get("rewrites") != EXPLICIT_STATIC_REWRITES:
        issues.append("vercel.json: extensionless static rewrites changed")
    if redirects.count(API_SOURCE_REDIRECT) != 1:
        issues.append("vercel.json: /api/lead.js canonical redirect changed")
    elif not 2 <= redirects.index(API_SOURCE_REDIRECT) < len(redirects) - 7:
        issues.append("vercel.json: /api/lead.js redirect precedence changed")
    preemption_indexes: list[int] = []
    for rule in DIRECTORY_INDEX_PREEMPTIONS:
        if redirects.count(rule) != 1:
            issues.append(f"vercel.json: directory-index preemption mismatch: {rule['source']}")
            continue
        preemption_indexes.append(redirects.index(rule))
    community_wildcard = next(
        (
            index
            for index, rule in enumerate(redirects)
            if rule.get("source") == "/communities/:slug.html"
        ),
        None,
    )
    if community_wildcard is None:
        issues.append("vercel.json: managed community wildcard is missing")
    elif len(preemption_indexes) == len(DIRECTORY_INDEX_PREEMPTIONS) and (
        preemption_indexes != list(
            range(preemption_indexes[0], preemption_indexes[0] + len(preemption_indexes))
        )
        or preemption_indexes[0] < 2
        or preemption_indexes[-1] >= community_wildcard
    ):
        issues.append("vercel.json: directory-index preemptions must be contiguous before the community wildcard")
    expected_consolidations = [
        {"source": source, "destination": destination, "permanent": True}
        for source, destination in FORMER_BULK_REDIRECTS
    ]
    for rule in expected_consolidations:
        if redirects.count(rule) != 1:
            issues.append(f"vercel.json: consolidation rule mismatch: {rule['source']}")
        elif redirects.index(rule) < 2 or redirects.index(rule) >= len(redirects) - 7:
            issues.append(f"vercel.json: consolidation precedence changed: {rule['source']}")
    declared = sum(
        len(config.get(key, []))
        for key in ("redirects", "rewrites", "headers")
        if isinstance(config.get(key, []), list)
    )
    if declared >= 2048:
        issues.append(f"vercel.json: route limit exceeded: {declared}")
    return issues


def _condition_matches(condition: dict[str, Any], hostname: str) -> bool:
    if condition.get("type") != "host":
        return False
    value = condition.get("value")
    if isinstance(value, str):
        try:
            return re.fullmatch(value, hostname) is not None
        except re.error:
            return False
    if not isinstance(value, dict):
        return False
    if set(value) == {"eq"}:
        return hostname == value["eq"]
    if set(value) == {"suf"}:
        return hostname.endswith(str(value["suf"]))
    return False


def _route_matches(route: dict[str, Any], hostname: str, path: str) -> re.Match[str] | None:
    source = route.get("src")
    if not isinstance(source, str):
        return None
    conditions = route.get("has", [])
    if conditions and not all(
        isinstance(condition, dict) and _condition_matches(condition, hostname)
        for condition in conditions
    ):
        return None
    try:
        return re.fullmatch(source, path)
    except re.error:
        return None


def _substitute(template: str, match: re.Match[str]) -> str:
    result = template
    for index, value in enumerate(match.groups(), start=1):
        result = result.replace(f"${index}", value or "")
    return result


def _preserve_query(location: str, query: str) -> str:
    """Model Vercel redirects, which pass source query strings by default."""

    if not query:
        return location
    separator = "&" if "?" in location else "?"
    return f"{location}{separator}{query}"


def first_redirect(
    routes: list[dict[str, Any]], hostname: str, path: str, query: str = ""
) -> tuple[int, int, str] | None:
    for index, route in enumerate(routes):
        if route.get("handle"):
            continue
        match = _route_matches(route, hostname, path)
        if match is None:
            continue
        status = route.get("status")
        location = route.get("headers", {}).get("Location")
        if isinstance(status, int) and 300 <= status < 400 and isinstance(location, str):
            return index, status, _preserve_query(_substitute(location, match), query)
        if route.get("continue"):
            continue
    return None


def _resources(output_dir: Path) -> tuple[set[str], set[str]]:
    static_root = output_dir / "static"
    static = {
        "/" + path.relative_to(static_root).as_posix()
        for path in static_root.rglob("*")
        if path.is_file()
    }
    function_root = output_dir / "functions"
    functions = {
        "/" + path.relative_to(function_root).as_posix().removesuffix(".func")
        for path in function_root.rglob("*.func")
        if path.is_dir()
    }
    return static, functions


def resolve_request(
    routes: list[dict[str, Any]],
    hostname: str,
    path: str,
    static: set[str],
    functions: set[str],
    query: str = "",
) -> tuple[str, Any]:
    resources = static | functions
    filesystem_phase = False
    for index, route in enumerate(routes):
        handle = route.get("handle")
        if handle == "filesystem":
            filesystem_phase = True
            if path in resources:
                return "serve", path
            continue
        if handle:
            continue
        match = _route_matches(route, hostname, path)
        if match is None:
            continue
        status = route.get("status")
        location = route.get("headers", {}).get("Location")
        if isinstance(status, int) and 300 <= status < 400 and isinstance(location, str):
            return (
                "redirect",
                (index, status, _preserve_query(_substitute(location, match), query)),
            )
        if route.get("continue"):
            continue
        destination = route.get("dest")
        if filesystem_phase and route.get("check") and isinstance(destination, str):
            target = _substitute(destination, match)
            if target in resources:
                return "serve", target
            continue
        if status == 404:
            return "status", 404
    return "status", 404


def compiled_contract_issues(
    compiled: dict[str, Any], output_dir: Path
) -> list[str]:
    issues: list[str] = []
    routes = compiled.get("routes")
    if compiled.get("version") != 3 or not isinstance(routes, list):
        return ["compiled config must use Build Output API v3 routes"]
    if len(routes) < 2:
        return ["compiled config has fewer than two host guards"]

    expected_conditions = [{"eq": WWW_HOST}, {"suf": ".vercel.app"}]
    for index, expected in enumerate(expected_conditions):
        route = routes[index]
        if route.get("status") != 308:
            issues.append(f"compiled route {index}: host guard is not 308")
        if route.get("headers", {}).get("Location") != f"{CANONICAL_ORIGIN}/$1":
            issues.append(f"compiled route {index}: canonical destination changed")
        conditions = route.get("has", [])
        if len(conditions) != 1 or conditions[0].get("type") != "host" or conditions[0].get("value") != expected:
            issues.append(f"compiled route {index}: host condition changed")

    filesystem_indexes = [
        index for index, route in enumerate(routes) if route.get("handle") == "filesystem"
    ]
    if len(filesystem_indexes) != 1:
        return issues + ["compiled config must have one filesystem phase"]
    filesystem_index = filesystem_indexes[0]
    expected_rewrites = [
        ("^/$", "/index.html"),
        ("^(?:/(.*))$", "/$1.html"),
        ("^(?:/(.*))$", "/$1/index.html"),
    ]
    actual_rewrites = [
        (route.get("src"), route.get("dest"))
        for route in routes[filesystem_index + 1 : filesystem_index + 4]
        if route.get("check") is True
    ]
    if actual_rewrites != expected_rewrites:
        issues.append("compiled extensionless rewrites are missing or misplaced")

    query = "utm_source=compiled-test&lead=1"
    for hostname in (WWW_HOST, VERCEL_HOST, "preview.branch.vercel.app"):
        for path in (
            "/",
            "/towns/summit",
            "/towns/summit/",
            "/ai-authority.html",
            "/blog/index.html",
            "/communities/index.html",
        ):
            result = first_redirect(routes, hostname, path, query)
            expected = f"{CANONICAL_ORIGIN}{path}?{query}"
            if result is None or result[0] not in (0, 1) or result[1:] != (308, expected):
                issues.append(f"compiled host precedence failed: {hostname}{path}")

    if first_redirect(routes, CANONICAL_HOST, "/") is not None:
        issues.append("compiled apex root enters a redirect loop")
    for lookalike in ("vercel.app", "preview.vercel.app.example.com"):
        if first_redirect(routes, lookalike, "/") is not None:
            issues.append(f"compiled lookalike host matched: {lookalike}")

    for source, destination in FORMER_BULK_REDIRECTS:
        noncanonical = first_redirect(routes, VERCEL_HOST, source, query)
        expected_host = f"{CANONICAL_ORIGIN}{source}?{query}"
        if noncanonical is None or noncanonical[0] != 1 or noncanonical[1:] != (308, expected_host):
            issues.append(f"compiled consolidation preempted host guard: {source}")
        apex = first_redirect(routes, CANONICAL_HOST, source, query)
        expected_apex = f"{destination}?{query}"
        if apex is None or apex[1:] != (308, expected_apex):
            issues.append(f"compiled consolidation destination failed: {source}")

    precedence_cases = {
        "/api/lead.js": "/api/lead",
        "/nj-real-estate-agent": "/ai-authority",
        "/nj-real-estate-agent.html": "/ai-authority",
        "/features/ai-email": "https://aisalespipeline.com/features/ai-email-real-estate.html",
        "/features/ai-email.html": "/features/ai-email",
        "/communities/basking-ridge": "/towns/basking-ridge",
    }
    for source, destination in precedence_cases.items():
        noncanonical = first_redirect(routes, VERCEL_HOST, source, query)
        expected_host = _preserve_query(f"{CANONICAL_ORIGIN}{source}", query)
        if noncanonical is None or noncanonical[0] != 1 or noncanonical[2] != expected_host:
            issues.append(f"compiled path migration preempted host guard: {source}")
        apex = first_redirect(routes, CANONICAL_HOST, source, query)
        expected_apex = _preserve_query(destination, query)
        if apex is None or apex[2] != expected_apex:
            issues.append(f"compiled apex migration failed: {source}")

    static, functions = _resources(output_dir)
    resolution_cases = {
        "/": ("serve", "/index.html"),
        "/ai-authority": ("serve", "/ai-authority.html"),
        "/blog": ("serve", "/blog/index.html"),
        "/css/styles.css": ("serve", "/css/styles.css"),
        "/api/lead": ("serve", "/api/lead"),
        "/route-that-does-not-exist": ("status", 404),
    }
    for path, expected in resolution_cases.items():
        actual = resolve_request(routes, CANONICAL_HOST, path, static, functions)
        if actual != expected:
            issues.append(f"compiled resolution failed: {path} -> {actual!r}")

    directory_index_failures: list[tuple[str, str, Any]] = []
    for raw in sorted(path for path in static if path.endswith("/index.html") or path == "/index.html"):
        canonical = "/" if raw == "/index.html" else raw.removesuffix("/index.html")
        prefix = "" if canonical == "/" else canonical
        variants = (
            f"{prefix}/index.html/",
            f"{prefix}/index/",
            f"{prefix}/index.html",
            f"{prefix}/index",
        )
        expected = _preserve_query(canonical, query)
        for variant in variants:
            actual = first_redirect(routes, CANONICAL_HOST, variant, query)
            if actual is None or actual[1:] != (308, expected):
                directory_index_failures.append((variant, expected, actual))
    if directory_index_failures:
        issues.append(
            "compiled directory-index canonicalization failed: "
            f"{directory_index_failures[:5]}"
        )

    raw_html_served: list[str] = []
    raw_index_served: list[str] = []
    for relative in sorted(path.removeprefix("/") for path in static if path.endswith(".html")):
        raw = "/" + relative
        if resolve_request(routes, CANONICAL_HOST, raw, static, functions)[0] != "redirect":
            raw_html_served.append(raw)
        if relative.endswith("/index.html") or relative == "index.html":
            index_path = "/" + relative.removesuffix(".html")
            if resolve_request(routes, CANONICAL_HOST, index_path, static, functions)[0] != "redirect":
                raw_index_served.append(index_path)
    if raw_html_served:
        issues.append(f"compiled raw HTML duplicates served: {raw_html_served[:5]}")
    if raw_index_served:
        issues.append(f"compiled index duplicates served: {raw_index_served[:5]}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / ".vercel" / "output",
        help="fresh Vercel Build Output directory",
    )
    args = parser.parse_args()
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    compiled_path = args.output / "config.json"
    if not compiled_path.is_file():
        print(f"missing compiled Vercel config: {compiled_path}")
        return 1
    compiled = json.loads(compiled_path.read_text(encoding="utf-8"))
    issues = source_contract_issues(config) + compiled_contract_issues(compiled, args.output)
    if issues:
        for issue in issues:
            print(f"FAIL: {issue}")
        return 1
    print(
        "compiled Vercel routing passed: host-first redirects, explicit clean URLs, "
        "static indexes, assets, API, missing routes, and migration precedence"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
