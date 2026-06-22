import json
import unittest
from pathlib import Path

from tools.shopee_failure_taxonomy import TAXONOMY_VERSION, classify_artifact


ROOT = Path(__file__).resolve().parents[1]


class ShopeeTaxonomyTests(unittest.TestCase):
    def test_current_taxonomy_reclassifies_saved_captcha_artifact(self):
        artifact_path = (
            ROOT / "tests" / "fixtures" / "shopee" / "captcha_artifact.json"
        )
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))

        classification, actions = classify_artifact(artifact)

        self.assertEqual(TAXONOMY_VERSION, 2)
        self.assertEqual(artifact.get("classification"), "access_blocked_or_session_required")
        self.assertEqual(classification, "captcha_required")
        self.assertTrue(actions)

    def test_environment_failure_is_not_classified_as_shopee_behavior(self):
        classification, _ = classify_artifact(
            {"error": "ConnectError: getaddrinfo failed"}
        )

        self.assertEqual(classification, "environment_network_blocked")


if __name__ == "__main__":
    unittest.main()
