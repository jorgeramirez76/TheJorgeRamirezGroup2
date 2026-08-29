#!/usr/bin/env python3
"""Fail closed when production has indexable blog routes absent from source.

The comparison logic is transport-agnostic and therefore safe for ordinary
unit tests. Network access is created only by the explicit ``--live`` command,
which is intended for the reviewed-publication and production-release gates.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Mapping
from urllib.parse import unquote, urljoin, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE_ORIGIN = "https://thejorgeramirezgroup.com"
SITE_HOSTS = {"thejorgeramirezgroup.com", "www.thejorgeramirezgroup.com"}
BLOG_INDEX_URL = f"{SITE_ORIGIN}/blog"
SITEMAP_URL = f"{SITE_ORIGIN}/sitemap.xml"
DEFAULT_DELAY_SECONDS = 5.0
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_DETAIL_REQUESTS = 20
MAX_RESPONSE_BYTES = 5 * 1024 * 1024


class DriftCheckError(RuntimeError):
    """The guard could not establish that production is safe to replace."""


@dataclass(frozen=True)
class FetchResponse:
    requested_url: str
    final_url: str
    status: int
    headers: Mapping[str, str]
    body: str


@dataclass(frozen=True)
class DriftReport:
    local_indexable: tuple[str, ...]
    production_discovered: tuple[str, ...]
    production_only_indexable: tuple[str, ...]
    production_nonindexable: tuple[str, ...]
    source_only_indexable: tuple[str, ...]

    @property
    def has_blocking_drift(self) -> bool:
        return bool(self.production_only_indexable)


Fetch = Callable[[str], FetchResponse]
Sleep = Callable[[float], None]


class _DocumentSignals(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.canonicals: list[str] = []
        self.robots: list[str] = []
        self.meta_refresh = False

    def _handle(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value or "" for name, value in attrs}
        tag = tag.lower()
        if tag == "a" and values.get("href"):
            self.hrefs.append(values["href"])
        elif tag == "link" and "canonical" in values.get("rel", "").lower().split():
            if values.get("href"):
                self.canonicals.append(values["href"])
        elif tag == "meta":
            name = values.get("name", "").lower()
            if name in {"robots", "googlebot"}:
                self.robots.append(values.get("content", ""))
            if values.get("http-equiv", "").lower() == "refresh":
                self.meta_refresh = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._handle(tag, attrs)


def document_signals(source: str) -> _DocumentSignals:
    parser = _DocumentSignals()
    try:
        parser.feed(source)
        parser.close()
    except Exception as exc:  # HTMLParser failures are rare, but releases fail closed.
        raise DriftCheckError(f"could not parse HTML discovery surface: {exc}") from exc
    return parser


def normalize_blog_route(value: str, *, base_url: str = f"{SITE_ORIGIN}/blog/") -> str | None:
    """Return one clean same-site article route, or ``None`` when out of scope."""

    candidate = value.strip()
    if not candidate:
        return None
    parsed = urlsplit(urljoin(base_url, candidate))
    if parsed.scheme not in {"http", "https"} or (parsed.hostname or "").lower() not in SITE_HOSTS:
        return None
    path = unquote(parsed.path or "/")
    path = re.sub(r"/+", "/", path)
    if path.endswith("/index.html"):
        path = path[: -len("/index.html")]
    elif path.endswith(".html"):
        path = path[:-5]
    if len(path) > 1:
        path = path.rstrip("/")
    if not path.startswith("/blog/"):
        return None
    slug = path.removeprefix("/blog/")
    if not slug or "/" in slug or slug in {".", ".."}:
        return None
    return f"/blog/{slug}"


def blog_routes_from_index(source: str) -> set[str]:
    signals = document_signals(source)
    return {
        route
        for href in signals.hrefs
        if (route := normalize_blog_route(href)) is not None
    }


def blog_routes_from_sitemap(source: str) -> set[str]:
    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        raise DriftCheckError(f"could not parse production sitemap: {exc}") from exc
    routes: set[str] = set()
    for node in root.findall(".//{*}loc"):
        if node.text and (route := normalize_blog_route(node.text)) is not None:
            routes.add(route)
    return routes


def _redirected_clean_routes(root: Path) -> set[str]:
    path = root / "vercel.json"
    if not path.is_file():
        raise DriftCheckError(f"local routing config is missing: {path}")
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DriftCheckError(f"could not read local routing config: {exc}") from exc
    redirects = config.get("redirects")
    if not isinstance(redirects, list):
        raise DriftCheckError("local routing config redirects must be an array")
    routes: set[str] = set()
    for entry in redirects:
        if not isinstance(entry, dict) or entry.get("has") or entry.get("missing"):
            continue
        source = entry.get("source")
        if not isinstance(source, str) or any(token in source for token in (":", "*", "(", ")")):
            continue
        route = normalize_blog_route(source)
        if route == source:
            routes.add(route)
    return routes


def _source_is_indexable(source: str, route: str) -> bool:
    signals = document_signals(source)
    if signals.meta_refresh or any("noindex" in value.lower() for value in signals.robots):
        return False
    if signals.canonicals:
        canonical = normalize_blog_route(signals.canonicals[0])
        if canonical != route:
            return False
    return True


def local_indexable_blog_routes(root: Path) -> set[str]:
    blog = root / "blog"
    if not blog.is_dir():
        raise DriftCheckError(f"local blog directory is missing: {blog}")
    redirected = _redirected_clean_routes(root)
    routes: set[str] = set()
    for path in sorted(blog.glob("*.html")):
        if path.name == "index.html":
            continue
        route = f"/blog/{path.stem}"
        if route in redirected:
            continue
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise DriftCheckError(f"could not read local blog page {path}: {exc}") from exc
        if _source_is_indexable(source, route):
            routes.add(route)
    return routes


def _headers_lower(headers: Mapping[str, str]) -> dict[str, str]:
    return {name.lower(): value for name, value in headers.items()}


def production_page_is_indexable(response: FetchResponse, route: str) -> bool:
    if not 200 <= response.status < 300:
        return False
    if normalize_blog_route(response.final_url) != route:
        return False
    if "noindex" in _headers_lower(response.headers).get("x-robots-tag", "").lower():
        return False
    return _source_is_indexable(response.body, route)


def _validate_discovery_response(response: FetchResponse, label: str) -> None:
    if not 200 <= response.status < 300:
        raise DriftCheckError(f"production {label} returned HTTP {response.status}")
    if (urlsplit(response.final_url).hostname or "").lower() not in SITE_HOSTS:
        raise DriftCheckError(f"production {label} redirected off the canonical site")
    if not response.body.strip():
        raise DriftCheckError(f"production {label} returned an empty document")


def check_production_source_drift(
    *,
    root: Path = ROOT,
    fetch: Fetch,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
    max_detail_requests: int = DEFAULT_MAX_DETAIL_REQUESTS,
    sleep: Sleep = time.sleep,
) -> DriftReport:
    """Compare production discovery surfaces with locally indexable blog files."""

    if delay_seconds < 0:
        raise ValueError("delay_seconds cannot be negative")
    if max_detail_requests < 0:
        raise ValueError("max_detail_requests cannot be negative")

    local = local_indexable_blog_routes(root)
    index_response = fetch(BLOG_INDEX_URL)
    _validate_discovery_response(index_response, "blog index")
    index_routes = blog_routes_from_index(index_response.body)
    if not index_routes:
        raise DriftCheckError("production blog index exposed no blog routes")

    if delay_seconds:
        sleep(delay_seconds)
    sitemap_response = fetch(SITEMAP_URL)
    _validate_discovery_response(sitemap_response, "sitemap")
    sitemap_routes = blog_routes_from_sitemap(sitemap_response.body)
    if not sitemap_routes:
        raise DriftCheckError("production sitemap exposed no blog routes")

    discovered = index_routes | sitemap_routes
    candidates = sorted(discovered - local)
    if len(candidates) > max_detail_requests:
        raise DriftCheckError(
            "production/source comparison exceeded the detail request cap "
            f"({len(candidates)} candidates > {max_detail_requests}); reconcile manually"
        )

    production_only_indexable: list[str] = []
    production_nonindexable: list[str] = []
    for route in candidates:
        if delay_seconds:
            sleep(delay_seconds)
        page_response = fetch(f"{SITE_ORIGIN}{route}")
        if production_page_is_indexable(page_response, route):
            production_only_indexable.append(route)
        else:
            production_nonindexable.append(route)

    return DriftReport(
        local_indexable=tuple(sorted(local)),
        production_discovered=tuple(sorted(discovered)),
        production_only_indexable=tuple(production_only_indexable),
        production_nonindexable=tuple(production_nonindexable),
        source_only_indexable=tuple(sorted(local - discovered)),
    )


def make_live_fetcher(*, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> Fetch:
    """Create the bounded transport used only by the explicit live CLI mode."""

    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    def fetch(url: str) -> FetchResponse:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "text/html,application/xml;q=0.9,*/*;q=0.1",
                "User-Agent": "JRG-Production-Source-Drift-Guard/1.0",
            },
        )
        try:
            handle = urllib.request.urlopen(request, timeout=timeout_seconds)
        except urllib.error.HTTPError as exc:
            handle = exc
        except (urllib.error.URLError, OSError) as exc:
            raise DriftCheckError(f"could not fetch {url}: {exc}") from exc
        try:
            payload = handle.read(MAX_RESPONSE_BYTES + 1)
            if len(payload) > MAX_RESPONSE_BYTES:
                raise DriftCheckError(f"production response exceeded {MAX_RESPONSE_BYTES} bytes: {url}")
            headers = {name: value for name, value in handle.headers.items()}
            charset = handle.headers.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="replace")
            return FetchResponse(
                requested_url=url,
                final_url=handle.geturl(),
                status=handle.getcode(),
                headers=headers,
                body=body,
            )
        except (LookupError, OSError) as exc:
            raise DriftCheckError(f"could not read {url}: {exc}") from exc
        finally:
            handle.close()

    return fetch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="explicitly compare the current production blog surface with this checkout",
    )
    parser.add_argument("--delay-seconds", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--max-detail-requests", type=int, default=DEFAULT_MAX_DETAIL_REQUESTS)
    args = parser.parse_args(argv)
    if not args.live:
        print("refusing implicit network access; rerun with --live at the release boundary", file=sys.stderr)
        return 2

    try:
        report = check_production_source_drift(
            root=ROOT,
            fetch=make_live_fetcher(timeout_seconds=args.timeout_seconds),
            delay_seconds=args.delay_seconds,
            max_detail_requests=args.max_detail_requests,
        )
    except (DriftCheckError, ValueError) as exc:
        print(f"production/source drift check inconclusive: {exc}", file=sys.stderr)
        return 2

    if report.has_blocking_drift:
        print("production has indexable blog routes absent from source:", file=sys.stderr)
        for route in report.production_only_indexable:
            print(f"- {route}", file=sys.stderr)
        return 1
    print(
        "production/source blog inventory is safe "
        f"({len(report.production_discovered)} production routes; "
        f"{len(report.source_only_indexable)} pending source-only routes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
