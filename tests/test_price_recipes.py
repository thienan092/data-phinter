import unittest

from bs4 import BeautifulSoup

from app import _extract_price_from_soup


class PriceRecipeTests(unittest.TestCase):
    def test_text_selector(self):
        soup = BeautifulSoup('<span class="price">135.000đ</span>', "html.parser")
        self.assertEqual(_extract_price_from_soup(soup, ".price"), 135000)

    def test_attribute_selector(self):
        soup = BeautifulSoup('<meta itemprop="price" content="135000">', "html.parser")
        self.assertEqual(
            _extract_price_from_soup(soup, "meta[itemprop='price']::content"),
            135000,
        )

    def test_jsonld_recipe(self):
        soup = BeautifulSoup(
            '<script type="application/ld+json">'
            '{"@type":"Product","offers":{"@type":"Offer","price":"75.000₫"}}'
            "</script>",
            "html.parser",
        )
        self.assertEqual(
            _extract_price_from_soup(soup, "jsonld:Product.offers.price"),
            75000,
        )


if __name__ == "__main__":
    unittest.main()
