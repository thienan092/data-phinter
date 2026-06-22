import unittest

from bs4 import BeautifulSoup

from tools.analyze_price_pages import choose_recipe, resolve_listing_url


class AnalyzePricePagesTests(unittest.TestCase):
    def test_prefers_product_scoped_dom_selector(self):
        soup = BeautifulSoup(
            '<div id="price-preview"><span class="pro-price">135.000đ</span></div>',
            "html.parser",
        )
        self.assertEqual(
            choose_recipe(soup, 135000),
            ("#price-preview .pro-price", 135000, "stable_dom"),
        )

    def test_reports_current_jsonld_price(self):
        soup = BeautifulSoup(
            '<script type="application/ld+json">'
            '{"@type":"Product","offers":{"price":"172.000₫"}}'
            "</script>",
            "html.parser",
        )
        self.assertEqual(
            choose_recipe(soup, 163000),
            ("jsonld:Product.offers.price", 172000, "structured_data"),
        )

    def test_resolves_direct_product_link_from_listing(self):
        soup = BeautifulSoup(
            '<a href="/product/g7-gold-picasso/">G7 GOLD PICASSO</a>',
            "html.parser",
        )
        url, score = resolve_listing_url(
            soup,
            "https://example.com/product-category/coffee/",
            "G7 GOLD PICASSO",
        )
        self.assertEqual(url, "https://example.com/product/g7-gold-picasso/")
        self.assertEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
