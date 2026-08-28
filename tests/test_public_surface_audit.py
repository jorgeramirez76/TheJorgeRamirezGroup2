import unittest
from pathlib import Path

import audit_site


class PublicSurfaceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = audit_site.build_audit()
        cls.by_path = {report["path"]: report for report in cls.audit["reports"]}

    def test_intentional_nonindex_surfaces_are_classified_not_scored(self):
        self.assertEqual(self.by_path["best-real-estate-agents-union-county-nj-2026.html"]["classification"], "redirect")
        self.assertEqual(self.by_path["thank-you.html"]["classification"], "noindex")
        self.assertEqual(self.by_path["index.html"]["classification"], "indexable")
        self.assertEqual(self.by_path["communities/index.html"]["classification"], "route-alias")
        self.assertEqual(
            self.audit["route_aliases"]["/communities"],
            ["communities.html", "communities/index.html"],
        )

    def test_redirect_inventory_distinguishes_clean_migrations_from_raw_normalizers(self):
        redirect_sources = audit_site.load_redirect_sources()
        self.assertIn("/best-real-estate-agents-union-county-nj-2026", redirect_sources)
        self.assertNotIn("/communities", redirect_sources)

    def test_public_indexable_surface_has_no_actionable_defects(self):
        self.assertEqual(self.audit["actionable_count"], 0)
        self.assertFalse(self.audit["missing_from_sitemap"])
        self.assertFalse(self.audit["stale_in_sitemap"])
        self.assertFalse(self.audit["duplicate_sitemap_routes"])
        self.assertFalse(self.audit["wrong_locale_sitemap"])
        self.assertFalse(self.audit["conflicting_route_files"])

    def test_internal_source_templates_are_not_public_pages(self):
        paths = {str(path.relative_to(audit_site.ROOT)) for path in self.audit["pages"]}
        self.assertNotIn("tools/blog-automation/template_source.html", paths)
        self.assertFalse(any(path.startswith("tools/seo-optimizer/") for path in paths))

    def test_clean_route_normalization_matches_vercel_urls(self):
        self.assertEqual(audit_site.clean_route(Path(audit_site.ROOT / "index.html")), "/")
        self.assertEqual(audit_site.clean_route(Path(audit_site.ROOT / "blog/index.html")), "/blog")
        self.assertEqual(audit_site.normalize_route("https://thejorgeramirezgroup.com/es/rent-vs-buy-nj.html?x=1#result"), "/es/rent-vs-buy-nj")

    def test_same_site_absolute_links_and_fragments_are_checked_locally(self):
        homepage = audit_site.ROOT / "index.html"
        self.assertEqual(
            audit_site.resolve_link(homepage, "https://www.thejorgeramirezgroup.com/es/#contact"),
            audit_site.ROOT / "es",
        )
        self.assertTrue(audit_site.fragment_exists(audit_site.ROOT / "es", "contact"))
        self.assertFalse(audit_site.fragment_exists(audit_site.ROOT / "es", "not-a-real-section"))


if __name__ == "__main__":
    unittest.main()
