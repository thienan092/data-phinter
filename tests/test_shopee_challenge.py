import os
import unittest
from unittest.mock import patch

from providers.shopee import (
    attach_challenge_logger,
    attach_runtime_logger,
    challenge_bootstrap_observed,
    classify_loaded_content_with_challenge,
    capture_page_screenshot,
    manual_action_kind_for,
    sanitized_challenge_url,
    sanitize_runtime_text,
    shopee_cloak_args,
    summarize_challenge_events,
    url_without_query,
    verification_interaction_url,
)


class FakePage:
    def __init__(self):
        self.handlers = {}

    def on(self, name, handler):
        self.handlers[name] = handler


class FakeObject:
    pass


class ShopeeChallengeTests(unittest.TestCase):
    def test_load_error_stays_passive_during_challenge_grace(self):
        body = "Loi tai Thu lai gap su co tai"
        url = "https://shopee.vn/product-name-i.1.2"

        self.assertEqual(
            manual_action_kind_for(
                "captcha_required",
                body,
                final_url=url,
                passive_grace_active=True,
            ),
            "captcha_bootstrap",
        )
        self.assertEqual(
            manual_action_kind_for("captcha_required", body, final_url=url),
            "retry_load_error",
        )

    def test_challenge_log_redacts_query_and_summarizes_phase(self):
        page = FakePage()
        events = []
        attach_challenge_logger(page, events)

        request = FakeObject()
        request.url = "https://shopee.vn/api/v4/anti_fraud/captcha/generate?token=SECRET"
        request.method = "POST"
        request.resource_type = "xhr"
        response = FakeObject()
        response.url = request.url
        response.status = 200
        response.request = request

        page.handlers["request"](request)
        page.handlers["response"](response)

        self.assertNotIn("SECRET", str(events))
        self.assertEqual(
            sanitized_challenge_url(request.url),
            "https://shopee.vn/api/v4/anti_fraud/captcha/generate",
        )
        self.assertEqual(
            url_without_query("https://shopee.vn/verify/captcha?anti_bot_token=SECRET"),
            "https://shopee.vn/verify/captcha",
        )
        summary = summarize_challenge_events(events)
        self.assertTrue(challenge_bootstrap_observed(events))
        self.assertEqual(
            classify_loaded_content_with_challenge(
                "https://shopee.vn/product-name-i.1.2",
                "Loi tai Thu lai gap su co tai",
                "<html></html>",
                0,
                events,
            ),
            "captcha_required",
        )
        self.assertEqual(
            classify_loaded_content_with_challenge(
                "https://shopee.vn/product-name-i.1.2",
                "bo qua noi dung chinh can tro giup",
                "<html></html>",
                0,
                events,
            ),
            "captcha_required",
        )
        self.assertIsNone(verification_interaction_url("https://shopee.vn/product-i.1.2"))
        self.assertIn(
            "anti_bot_token=SECRET",
            verification_interaction_url(
                "https://shopee.vn/verify/captcha?anti_bot_token=SECRET"
            ),
        )
        self.assertEqual(
            classify_loaded_content_with_challenge(
                "https://shopee.vn/product-name-i.1.2",
                "Loi tai Thu lai gap su co tai",
                "<html></html>",
                0,
                [],
            ),
            "captcha_required",
        )
        self.assertTrue(summary["phases"]["generate_succeeded"])
        self.assertFalse(summary["phases"]["verify_v2_succeeded"])

    def test_fingerprint_seed_is_stable_and_configurable(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SHOPEE_CLOAK_FINGERPRINT_SEED", None)
            self.assertEqual(shopee_cloak_args(), ["--fingerprint=73192"])
        with patch.dict(os.environ, {"SHOPEE_CLOAK_FINGERPRINT_SEED": "45678"}):
            self.assertEqual(shopee_cloak_args(), ["--fingerprint=45678"])
        with patch.dict(
            os.environ,
            {
                "SHOPEE_CLOAK_FINGERPRINT_SEED": "45678",
                "SHOPEE_CLOAK_FINGERPRINT_NOISE": "false",
            },
        ):
            self.assertEqual(
                shopee_cloak_args(),
                ["--fingerprint=45678", "--fingerprint-noise=false"],
            )

    def test_screenshot_failure_is_auditable(self):
        class BrokenPage:
            def screenshot(self, **kwargs):
                raise RuntimeError("capture failed")

        events = []
        self.assertIsNone(capture_page_screenshot(BrokenPage(), events))
        self.assertEqual(events, ["screenshot_failed:RuntimeError"])

    def test_runtime_events_redact_sensitive_values(self):
        self.assertNotIn(
            "SECRET",
            sanitize_runtime_text("https://x.test/?token=SECRET&next=value"),
        )

        page = FakePage()
        events = []
        attach_runtime_logger(page, events)
        message = FakeObject()
        message.type = "error"
        message.text = "failed ?token=SECRET&next=value"
        page.handlers["console"](message)
        self.assertNotIn("SECRET", str(events))


if __name__ == "__main__":
    unittest.main()
