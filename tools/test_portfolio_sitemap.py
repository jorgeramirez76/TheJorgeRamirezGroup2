import unittest
import xml.etree.ElementTree as ET
from audit_portfolio_seo import sitemap_locations

class SitemapExtensions(unittest.TestCase):
    def test_image_locations_are_not_html_pages(self):
        tree = ET.fromstring('''<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
          xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
          <url><loc>https://example.com/shirt/</loc><image:image>
          <image:loc>https://example.com/shirt.jpg</image:loc></image:image></url></urlset>''')
        self.assertEqual(sitemap_locations(tree), ['https://example.com/shirt/'])

    def test_sitemap_index_returns_child_sitemaps(self):
        tree = ET.fromstring('''<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <sitemap><loc>https://example.com/pages.xml</loc></sitemap></sitemapindex>''')
        self.assertEqual(sitemap_locations(tree), ['https://example.com/pages.xml'])

if __name__ == '__main__': unittest.main()
