#!/usr/bin/env python3
"""Guard the verified town-photo inventory, locality, and attribution contract."""

from __future__ import annotations

import json
import re
import struct
import unittest
from pathlib import Path

import apply_town_photos
import fetch_town_photos
from scripts import rebuild_union_priority_towns
from town_photo_integrity import (
    REJECTED_TOWN_PHOTOS,
    filter_photo_credits,
    is_rejected_photo,
)


ROOT = Path(__file__).resolve().parents[1]

TOWN_MEDIA = {
    "berkeley-heights": ("berkeley-heights-1.webp", 0, "lazy"),
    "chatham-borough": ("chatham-borough-1.webp", 0, "hero"),
    "chatham-township": ("chatham-township-2.webp", 1, "hero"),
    "cranford": ("cranford-1.webp", 0, "lazy"),
    "denville": ("denville-1.webp", 0, "hero"),
    "east-hanover": ("east-hanover-1.webp", 0, "hero"),
    "fanwood": ("fanwood-1.webp", 0, "lazy"),
    "morris-plains": ("morris-plains-1.webp", 0, "hero"),
    "new-providence": ("new-providence-1.webp", 0, "lazy"),
    "roselle-park": ("roselle-park-1.webp", 0, "lazy"),
    "springfield": ("springfield-1.webp", 0, "lazy"),
}

CHATHAM_TOWNSHIP_VARIANTS = {
    "chatham-township-2-640.webp": (640, 640),
    "chatham-township-2-960.webp": (960, 960),
}


def lossy_webp_dimensions(path: Path) -> tuple[int, int]:
    """Read the VP8 frame dimensions without adding an image-library dependency."""
    data = path.read_bytes()
    self_describing_frame = data.find(b"\x9d\x01\x2a")
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP" or self_describing_frame < 0:
        raise AssertionError(f"Expected a lossy WebP image: {path}")
    width, height = struct.unpack_from("<HH", data, self_describing_frame + 3)
    return width & 0x3FFF, height & 0x3FFF


def public_html_paths() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*.html")
        if ".vercel" not in path.parts and "node_modules" not in path.parts
    ]


class TownMediaIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.credits = json.loads(
            (ROOT / "images/towns/credits.json").read_text(encoding="utf-8")
        )

    def test_public_reference_inventory_is_exact(self) -> None:
        referenced: set[str] = set()
        for path in public_html_paths():
            source = path.read_text(encoding="utf-8", errors="replace")
            referenced.update(
                re.findall(r"/images/towns/([A-Za-z0-9._-]+\.webp)", source)
            )
        expected = {item[0] for item in TOWN_MEDIA.values()} | set(CHATHAM_TOWNSHIP_VARIANTS)
        self.assertEqual(expected, referenced)
        self.assertNotIn("chatham-township-1.webp", referenced)

    def test_town_media_release_dates_do_not_replace_source_review_dates(self) -> None:
        self.assertEqual(set(TOWN_MEDIA), apply_town_photos.RELEASE_MODIFIED_TOWN_SLUGS)
        for slug in TOWN_MEDIA:
            with self.subTest(slug=slug):
                source = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
                self.assertEqual(
                    [apply_town_photos.PAGE_MODIFIED_ON],
                    re.findall(r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})"', source),
                )
                self.assertNotIn("Updated August 25, 2026", source)
        self.assertIn("Accessed August 25, 2026", (ROOT / "towns/cranford.html").read_text(encoding="utf-8"))

    def test_displayed_photos_match_credits_and_publish_complete_attribution(self) -> None:
        for slug, (filename, credit_index, loading_mode) in TOWN_MEDIA.items():
            with self.subTest(slug=slug):
                page = (ROOT / "towns" / f"{slug}.html").read_text(encoding="utf-8")
                credit = self.credits[slug][credit_index]
                self.assertEqual(filename, credit["file"])
                self.assertIn(f'src="/images/towns/{filename}"', page)
                self.assertIn("resized to WebP.", page)
                self.assertIn(credit["artist"], page)
                self.assertIn(credit["license"], page)

                source_slug = credit["source"].removeprefix("File:").replace(" ", "_")
                self.assertIn(f"commons.wikimedia.org/wiki/File:{source_slug}", page)

                image = re.search(
                    rf'<img\b[^>]*src="/images/towns/{re.escape(filename)}"[^>]*>', page
                )
                self.assertIsNotNone(image)
                tag = image.group(0)
                self.assertRegex(tag, r'alt="[^\"]{20,}"')
                self.assertIn('decoding="async"', tag)
                if loading_mode == "hero":
                    self.assertIn('fetchpriority="high"', tag)
                    self.assertNotIn('loading="lazy"', tag)
                else:
                    self.assertIn('loading="lazy"', tag)

                asset = ROOT / "images/towns" / filename
                self.assertTrue(asset.is_file())
                data = asset.read_bytes()[:12]
                self.assertEqual(b"RIFF", data[:4])
                self.assertEqual(b"WEBP", data[8:12])

    def test_chatham_pages_do_not_cross_assign_borough_and_township_media(self) -> None:
        borough = (ROOT / "towns/chatham-borough.html").read_text(encoding="utf-8")
        township = (ROOT / "towns/chatham-township.html").read_text(encoding="utf-8")
        self.assertIn("chatham-borough-1.webp", borough)
        self.assertNotIn("chatham-township-2.webp", borough)
        self.assertIn("chatham-township-2.webp", township)
        self.assertNotIn("chatham-township-1.webp", township)
        self.assertIn("Mount Vernon School", township)
        self.assertNotIn("Chatham,_NJ,_train_station.jpg", township)

    def test_chatham_township_hero_has_responsive_verified_derivatives(self) -> None:
        township = (ROOT / "towns/chatham-township.html").read_text(encoding="utf-8")
        image = re.search(
            r'<img\b[^>]*src="/images/towns/chatham-township-2\.webp"[^>]*>',
            township,
        )
        self.assertIsNotNone(image)
        tag = image.group(0)
        self.assertIn(
            'srcset="/images/towns/chatham-township-2-640.webp 640w, '
            '/images/towns/chatham-township-2-960.webp 960w, '
            '/images/towns/chatham-township-2.webp 1280w"',
            tag,
        )
        self.assertIn(
            'sizes="(max-width: 430px) calc(100vw - 1.35rem), '
            '(max-width: 652px) calc(100vw - 2rem), (max-width: 820px) 620px, '
            '(max-width: 1152px) 42vw, 472px"',
            tag,
        )
        self.assertIn('width="1280" height="1280"', tag)
        self.assertIn('fetchpriority="high"', tag)
        self.assertNotIn('loading="lazy"', tag)
        self.assertIn(
            'alt="Mount Vernon School, the Red Brick Schoolhouse Museum, '
            'in Chatham Township, New Jersey"',
            tag,
        )

        original_size = (ROOT / "images/towns/chatham-township-2.webp").stat().st_size
        for filename, expected_dimensions in CHATHAM_TOWNSHIP_VARIANTS.items():
            with self.subTest(filename=filename):
                asset = ROOT / "images/towns" / filename
                self.assertTrue(asset.is_file())
                self.assertEqual(expected_dimensions, lossy_webp_dimensions(asset))
                self.assertLess(asset.stat().st_size, original_size)

        self.assertLess(
            (ROOT / "images/towns/chatham-township-2-640.webp").stat().st_size,
            130_000,
        )
        self.assertLess(
            (ROOT / "images/towns/chatham-township-2-960.webp").stat().st_size,
            210_000,
        )

    def test_union_town_emitter_keeps_media_contract(self) -> None:
        for slug, town in rebuild_union_priority_towns.TOWNS.items():
            with self.subTest(slug=slug):
                rendered = rebuild_union_priority_towns.render_main(slug, town)
                filename = TOWN_MEDIA[slug][0]
                self.assertIn(f'src="/images/towns/{filename}"', rendered)
                self.assertIn('loading="lazy" decoding="async"', rendered)
                self.assertIn("Wikimedia Commons", rendered)
                self.assertIn("resized to WebP.", rendered)

    def test_union_town_emitter_preserves_local_search_pathway(self) -> None:
        block = """  <!-- local-search-pathways:start -->
  <section class="local-search-pathways">Pathway</section>
  <!-- local-search-pathways:end -->
"""
        rendered = "<main id=\"main\"><p>Generated</p></main>"
        source = f"<main id=\"main\"><p>Old</p>{block}</main>"
        preserved = rebuild_union_priority_towns.preserve_local_search_pathway(
            rendered, source
        )
        self.assertEqual(1, preserved.count("local-search-pathways:start"))
        self.assertEqual(1, preserved.count("local-search-pathways:end"))
        self.assertLess(preserved.index("local-search-pathways:start"), preserved.index("</main>"))

    def test_exact_off_location_archive_records_are_removed_and_blocked(self) -> None:
        expected_files = {
            ("bloomfield", "bloomfield-2.webp"),
            ("east-brunswick", "east-brunswick-2.webp"),
            ("south-bound-brook", "south-bound-brook-1.webp"),
            ("south-brunswick", "south-brunswick-1.webp"),
            ("south-plainfield", "south-plainfield-1.webp"),
            ("south-plainfield", "south-plainfield-2.webp"),
            ("south-river", "south-river-2.webp"),
        }
        blocked_files = {
            (town, filename)
            for town, filename, _source, _actual_place in REJECTED_TOWN_PHOTOS
        }
        self.assertEqual(expected_files, blocked_files)
        self.assertEqual(7, len(REJECTED_TOWN_PHOTOS))
        for town, filename, source, _actual_place in REJECTED_TOWN_PHOTOS:
            with self.subTest(town=town, filename=filename):
                self.assertTrue((ROOT / "images/towns" / filename).is_file())
                self.assertFalse(
                    any(
                        photo.get("file") == filename or photo.get("source") == source
                        for photo in self.credits[town]
                    )
                )

    def test_fetcher_and_publisher_enforce_shared_off_location_denylist(self) -> None:
        for town, filename, source, _actual_place in REJECTED_TOWN_PHOTOS:
            with self.subTest(town=town, filename=filename):
                candidate = {
                    "title": source,
                    "license": "CC BY-SA 4.0",
                    "width": 1280,
                    "height": 960,
                }
                self.assertEqual([], fetch_town_photos.pick(town, [candidate]))
                self.assertTrue(
                    is_rejected_photo(town, {"file": filename, "source": source})
                )
                sanitized = filter_photo_credits(
                    {town: [{"file": filename, "source": source}]}
                )
                self.assertEqual([], sanitized[town])

        for town, photos in apply_town_photos.CREDITS.items():
            self.assertFalse(any(is_rejected_photo(town, photo) for photo in photos))


if __name__ == "__main__":
    unittest.main(verbosity=2)
