import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

from candidate_quality import analyze_rows  # noqa: E402


def candidate(index, link=None):
    return {
        "Link": link or f"https://example.com/products/item-{index}",
        "Giá niêm yết (VND)": "100000",
        "Loại SP": "Cà phê",
    }


class CandidateQualityTests(unittest.TestCase):
    def test_one_hundred_valid_unique_rows_are_strict_complete(self):
        analysis = analyze_rows([candidate(index) for index in range(100)])

        self.assertTrue(analysis["strict_complete"])
        self.assertEqual(analysis["strict_candidate_rows"], 100)
        self.assertEqual(analysis["excluded"], {})

    def test_listing_like_row_is_excluded_before_target_count(self):
        rows = [candidate(index) for index in range(99)]
        rows.append(candidate(99, "https://example.com/collections/coffee"))

        analysis = analyze_rows(rows)

        self.assertFalse(analysis["strict_complete"])
        self.assertEqual(analysis["strict_candidate_rows"], 99)
        self.assertEqual(analysis["excluded"]["listing_like_url"], 1)
        self.assertEqual(analysis["shortfall"], 1)

    def test_duplicate_url_prevents_strict_completion(self):
        rows = [candidate(index) for index in range(100)]
        rows.append(candidate(100, rows[0]["Link"] + "?tracking=1"))

        analysis = analyze_rows(rows)

        self.assertFalse(analysis["strict_complete"])
        self.assertEqual(analysis["strict_candidate_rows"], 100)
        self.assertEqual(analysis["duplicate_rows"], 1)
        self.assertEqual(analysis["excluded"]["duplicate_url"], 1)


if __name__ == "__main__":
    unittest.main()
