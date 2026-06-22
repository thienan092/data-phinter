import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import manual_actions
from app import _manual_action_response, app


class ManualActionApiTests(unittest.TestCase):
    def setUp(self):
        manual_actions._ACTIONS.clear()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.audit_patch = patch.object(
            manual_actions,
            "DEFAULT_AUDIT_PATH",
            Path(self.temp_dir.name) / "events.jsonl",
        )
        self.audit_patch.start()
        app.config["TESTING"] = True
        self.client = app.test_client()

    def tearDown(self):
        manual_actions._ACTIONS.clear()
        self.audit_patch.stop()
        self.temp_dir.cleanup()

    def test_public_action_hides_token_and_open_endpoint_redirects(self):
        secret_url = "https://shopee.vn/verify/captcha?anti_bot_token=SECRET"
        manual_actions.start_manual_action(
            "request-api",
            status="captcha_required",
            action_kind="captcha_bootstrap",
            requested_url="https://shopee.vn/product-i.1.2",
            final_url="https://shopee.vn/verify/captcha",
            interaction_url=secret_url,
        )

        response = self.client.get("/api/manual-actions/request-api")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("SECRET", response.get_data(as_text=True))
        self.assertEqual(
            response.get_json()["open_url"],
            "/api/manual-actions/request-api/open",
        )

        redirect_response = self.client.get(
            "/api/manual-actions/request-api/open",
            follow_redirects=False,
        )
        self.assertEqual(redirect_response.status_code, 302)
        self.assertEqual(redirect_response.headers["Location"], secret_url)
        action_after_open = self.client.get("/api/manual-actions/request-api").get_json()
        self.assertEqual(action_after_open["open_count"], 1)
        self.assertIsNotNone(action_after_open["last_opened_at"])

    def test_manual_action_response_exposes_pending_open_endpoint_without_token(self):
        secret_url = "https://shopee.vn/verify/captcha?anti_bot_token=SECRET"
        manual_actions.start_manual_action(
            "request-response",
            status="captcha_required",
            action_kind="captcha_bootstrap",
            requested_url="https://shopee.vn/product-i.1.2",
            final_url="https://shopee.vn/verify/captcha",
            interaction_url=secret_url,
        )

        response = _manual_action_response("captcha_required", "request-response")

        self.assertTrue(response["manual_action_required"])
        self.assertEqual(response["manual_action_state"], "pending")
        self.assertEqual(response["manual_action_kind"], "captcha_bootstrap")
        self.assertEqual(
            response["manual_action_open_url"],
            "/api/manual-actions/request-response/open",
        )
        self.assertNotIn("SECRET", str(response))


if __name__ == "__main__":
    unittest.main()
