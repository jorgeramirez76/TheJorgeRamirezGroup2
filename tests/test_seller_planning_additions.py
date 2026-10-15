"""Contracts for maintained seller guidance and its structured answers."""
import html
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit
from tools.seller_planning_additions import apply_seller_planning

ROOT = Path(__file__).resolve().parents[1]
PAGES = json.loads((ROOT / 'data/seller-planning-additions.json').read_text())['pages']
ARTICLES = ('selling-nj-home-with-pets-cleaning-showings-2026', 'living-room-spend-vs-save-nj-home-sellers-2026')


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

    def test_revised_articles_do_not_claim_personal_authorship_or_experience(self):
        for slug in ARTICLES:
            source = (ROOT / 'blog' / (slug + '.html')).read_text()
            self.assertNotIn('Written by', source)
            self.assertNotIn('myself included', source)
            self.assertNotIn('rooms I walk through', source)
            self.assertIn('AI-assisted guidance', source)
            article = next(json.loads(raw) for raw in re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', source, re.S) if json.loads(raw).get('@type') == 'BlogPosting')
            self.assertNotIn('author', article)
            self.assertEqual('The Jorge Ramirez Group', article['publisher']['name'])

    def test_faq_schema_matches_visible_answers(self):
        for slug in ARTICLES:
            source = (ROOT / 'blog' / (slug + '.html')).read_text()
            visible = html.unescape(re.sub('<[^>]+>', '', source.split('<body>')[1]))
            faq = next(json.loads(raw) for raw in re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', source, re.S) if json.loads(raw).get('@type') == 'FAQPage')
            self.assertEqual(5, len(faq['mainEntity']))
            for answer in faq['mainEntity']:
                with self.subTest(slug=slug, question=answer['name']):
                    self.assertIn(answer['name'], visible)
                    self.assertIn(answer['acceptedAnswer']['text'], visible)


if __name__ == '__main__':
    unittest.main()
