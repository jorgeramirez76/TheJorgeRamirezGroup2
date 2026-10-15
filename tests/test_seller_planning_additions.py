"""Contracts for maintained seller guidance and its structured answers."""
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit
from tools.seller_planning_additions import apply_seller_planning

ROOT = Path(__file__).resolve().parents[1]
PAGES = json.loads((ROOT / 'data/seller-planning-additions.json').read_text())['pages']


class SellerPlanningTests(unittest.TestCase):
    def test_repeat_application_is_idempotent_and_template_drift_fails(self):
        for route, addition in PAGES.items():
            source = (ROOT / (route.lstrip('/') + '.html')).read_text()
            with self.subTest(route=route):
                self.assertEqual(source, apply_seller_planning(route, source))
                with self.assertRaises(ValueError):
                    apply_seller_planning(route, source.replace(addition['before'], ''))
                with self.assertRaises(ValueError):
                    apply_seller_planning(route, source + addition['before'])
        self.assertEqual('untouched', apply_seller_planning('/es/sell-your-home', 'untouched'))

    def test_planning_links_have_existing_files_and_fragment_targets(self):
        for addition in PAGES.values():
            for href in re.findall(r'href="([^"]+)"', addition['html']):
                link = urlsplit(href)
                if link.scheme or not link.path.startswith('/'):
                    continue
                target = ROOT / (link.path.lstrip('/') + '.html')
                with self.subTest(href=href):
                    self.assertTrue(target.is_file())
                    if link.fragment:
                        self.assertIn(f'id="{link.fragment}"', target.read_text())


if __name__ == '__main__':
    unittest.main()
