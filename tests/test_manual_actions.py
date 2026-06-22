import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import manual_actions


class ManualActionTests(unittest.TestCase):
    def setUp(self):
        manual_actions._ACTIONS.clear()

    def tearDown(self):
        manual_actions._ACTIONS.clear()

    def test_interaction_url_is_ephemeral_and_not_audited(self):
        secret_url = "https://shopee.vn/verify/captcha?anti_bot_token=SECRET"
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_path = Path(temp_dir) / "events.jsonl"
            with patch.object(manual_actions, "DEFAULT_AUDIT_PATH", audit_path):
                action = manual_actions.start_manual_action(
                    "request-1",
                    status="captcha_required",
                    action_kind="captcha_bootstrap",
                    requested_url="https://shopee.vn/product-i.1.2",
                    final_url="https://shopee.vn/verify/captcha",
                    interaction_url=secret_url,
                )
                self.assertEqual(action["interaction_url"], secret_url)
                self.assertNotIn("SECRET", audit_path.read_text(encoding="utf-8"))

                opened = manual_actions.record_verification_url_opened("request-1")
                self.assertEqual(opened["open_count"], 1)
                self.assertIn("verification_url_opened", audit_path.read_text(encoding="utf-8"))
                self.assertNotIn("SECRET", audit_path.read_text(encoding="utf-8"))

                finished = manual_actions.finish_manual_action(
                    "request-1",
                    state="timed_out",
                    status="captcha_required",
                    final_url="https://shopee.vn/verify/captcha",
                )
                self.assertIsNone(finished["interaction_url"])
                self.assertNotIn("SECRET", audit_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
