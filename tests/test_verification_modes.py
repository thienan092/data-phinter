import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import app as app_module


class VerificationModeTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def test_compatible_is_the_default_mode(self):
        self.assertEqual(app_module.DEFAULT_MODE, "compatible")
        response = self.client.get("/api/default-mode")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["default_mode"], "compatible")

    def test_default_extraction_uses_selenium(self):
        with patch.object(app_module, "extract_price_selenium", return_value=125000) as selenium, \
                patch.object(app_module, "extract_price_cloak") as cloak:
            response = self.client.post(
                "/api/check-price",
                json={"url": "https://example.com/product", "selector": ".price"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["verification_mode"], "compatible")
        selenium.assert_called_once()
        cloak.assert_not_called()

    def test_legacy_aliases_map_to_public_modes(self):
        cases = {
            "bs4": ("fast", "extract_price_bs4"),
            "selenium": ("compatible", "extract_price_selenium"),
            "cloak": ("adaptive", "extract_price_cloak"),
        }
        for alias, (public_mode, function_name) in cases.items():
            with self.subTest(alias=alias), \
                    patch.object(app_module, function_name, return_value=100):
                response = self.client.post(
                    "/api/check-price",
                    json={
                        "url": "https://example.com/product",
                        "selector": ".price",
                        "mode": alias,
                    },
                )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["verification_mode"], public_mode)

    def test_unknown_mode_is_rejected(self):
        response = self.client.post(
            "/api/check-price",
            json={
                "url": "https://example.com/product",
                "selector": ".price",
                "mode": "magic",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_matching_cached_selenium_pair_can_be_discovered_offline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            platform_name = "win64"
            version = "138.0.7204.157"
            driver_name = (
                "chromedriver.exe"
                if app_module.platform.system() == "Windows"
                else "chromedriver"
            )
            browser_name = (
                "chrome.exe"
                if app_module.platform.system() == "Windows"
                else "chrome"
            )
            driver = root / "chromedriver" / platform_name / version / driver_name
            browser = root / "chrome" / platform_name / version / browser_name
            driver.parent.mkdir(parents=True)
            browser.parent.mkdir(parents=True)
            driver.touch()
            browser.touch()

            found_driver, found_browser = app_module.find_cached_selenium_pair(root)

        self.assertEqual(found_driver, driver)
        self.assertEqual(found_browser, browser)


if __name__ == "__main__":
    unittest.main()
