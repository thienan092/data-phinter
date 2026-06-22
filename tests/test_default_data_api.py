import csv
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as app_module


class DefaultDataApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def test_agent_header_is_required(self):
        response = self.client.get("/api/agent/default-data")
        self.assertEqual(response.status_code, 403)
        response = self.client.get("/api/agent/candidate-data")
        self.assertEqual(response.status_code, 403)
        response = self.client.get("/api/agent/verification-summary")
        self.assertEqual(response.status_code, 403)
        response = self.client.post("/api/agent/accumulation")
        self.assertEqual(response.status_code, 403)

    def test_remote_agent_request_requires_explicit_enablement_and_token(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ENABLE_REMOTE_AGENT_AUTOMATION", None)
            os.environ.pop("AGENT_AUTOMATION_TOKEN", None)
            response = self.client.get(
                "/api/agent/default-data",
                headers={"X-Agent-Automation": "1"},
                environ_overrides={"REMOTE_ADDR": "203.0.113.20"},
            )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.get_json()["code"],
            "remote_agent_automation_forbidden",
        )

    def test_public_host_through_loopback_proxy_still_requires_token(self):
        response = self.client.get(
            "/api/agent/default-data",
            headers={"X-Agent-Automation": "1", "Host": "data-phinter.example"},
            environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.get_json()["code"],
            "remote_agent_automation_forbidden",
        )

    def test_remote_agent_request_accepts_enabled_matching_token(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "current.csv"
            csv_path.write_text("ID,Product\n1,Coffee\n", encoding="utf-8")
            config_path = root / "default-data.json"
            config_path.write_text(json.dumps({"path": str(csv_path)}), encoding="utf-8")

            with patch.object(app_module, "DEFAULT_DATA_CONFIG", config_path), patch.dict(
                os.environ,
                {
                    "ENABLE_REMOTE_AGENT_AUTOMATION": "1",
                    "AGENT_AUTOMATION_TOKEN": "test-secret",
                },
                clear=False,
            ):
                response = self.client.get(
                    "/api/agent/default-data",
                    headers={
                        "X-Agent-Automation": "1",
                        "X-Agent-Automation-Token": "test-secret",
                    },
                    environ_overrides={"REMOTE_ADDR": "203.0.113.20"},
                )
                response.close()

        self.assertEqual(response.status_code, 200)

    def test_configured_csv_is_returned(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "current.csv"
            csv_path.write_text("ID,Product\n1,Coffee\n", encoding="utf-8")
            config_path = root / "default-data.json"
            config_path.write_text(
                json.dumps({"path": str(csv_path)}),
                encoding="utf-8",
            )

            with patch.object(app_module, "DEFAULT_DATA_CONFIG", config_path):
                response = self.client.get(
                    "/api/agent/default-data",
                    headers={"X-Agent-Automation": "1"},
                )
                body = response.get_data(as_text=True)
                response.close()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Default-Data-Name"], "current.csv")
        self.assertEqual(response.headers["X-Default-Data-Path"], str(csv_path))
        self.assertEqual(body.replace("\r\n", "\n"), "ID,Product\n1,Coffee\n")

    def test_configured_candidate_csv_is_returned(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "candidate.csv"
            csv_path.write_text("ID,Product\nNB1,Coffee\n", encoding="utf-8")
            config_path = root / "current-candidate.json"
            config_path.write_text(json.dumps({"path": str(csv_path)}), encoding="utf-8")

            with patch.object(app_module, "CANDIDATE_DATA_CONFIG", config_path):
                response = self.client.get(
                    "/api/agent/candidate-data",
                    headers={"X-Agent-Automation": "1"},
                )
                body = response.get_data(as_text=True)
                response.close()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Candidate-Data-Name"], "candidate.csv")
        self.assertEqual(body.replace("\r\n", "\n"), "ID,Product\nNB1,Coffee\n")

    def test_verification_summary_is_returned(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = root / "report.csv"
            report_path.write_text(
                "ID,Product,Link,Price,verify_stage,match_count,price_present,verified\n"
                "NB1,Coffee A,https://example.com/a,100,cloak,1,True,True\n"
                "NB2,Coffee B,https://example.com/b,200,cloak,3,True,True\n"
                "NB3,Coffee C,https://example.com/c,300,cloak,0,False,False\n",
                encoding="utf-8",
            )
            config_path = root / "current-verification.json"
            config_path.write_text(
                json.dumps({
                    "run_id": "run-1",
                    "report_path": str(report_path),
                    "novel_candidates": 3,
                    "unique_matches": 1,
                    "ambiguous_price_present": 1,
                    "price_absent": 1,
                    "user_decision_required": True,
                }),
                encoding="utf-8",
            )

            with patch.object(app_module, "VERIFICATION_CONFIG", config_path):
                response = self.client.get(
                    "/api/agent/verification-summary",
                    headers={"X-Agent-Automation": "1"},
                )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["run_id"], "run-1")
        self.assertEqual(payload["unique_matches"], 1)
        self.assertEqual(len(payload["problem_rows"]), 2)
        self.assertEqual(payload["problem_rows"][0]["kind"], "ambiguous")
        self.assertEqual(payload["problem_rows"][1]["kind"], "price_absent")

    def test_accumulation_preview_and_commit_are_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fields = ["ID", "Product", "Link"]
            default_path = root / "default.csv"
            accepted_path = root / "accepted.csv"
            default_path.write_text(
                "ID,Product,Link\n"
                "D1,Old,https://example.com/a\n"
                "D2,Duplicate,https://example.com/a/\n",
                encoding="utf-8",
            )
            accepted_path.write_text(
                "ID,Product,Link\n"
                "N1,New,https://example.com/b\n",
                encoding="utf-8",
            )
            default_config = root / "default-data.json"
            default_config.write_text(json.dumps({"path": str(default_path)}), encoding="utf-8")
            verification_config = root / "current-verification.json"
            verification_config.write_text(json.dumps({
                "run_id": "run-1",
                "unique_match_path": str(accepted_path),
                "price_present_path": str(accepted_path),
                "user_decision_required": False,
                "post_report_decision": {"acceptance": "unique"},
            }), encoding="utf-8")

            with patch.object(app_module, "PROJECT_ROOT", root), \
                    patch.object(app_module, "DEFAULT_DATA_CONFIG", default_config), \
                    patch.object(app_module, "VERIFICATION_CONFIG", verification_config):
                preview = self.client.post(
                    "/api/agent/accumulation",
                    headers={"X-Agent-Automation": "1"},
                    json={"run_id": "run-1", "acceptance": "unique", "commit": False},
                )
                first = self.client.post(
                    "/api/agent/accumulation",
                    headers={"X-Agent-Automation": "1"},
                    json={"run_id": "run-1", "acceptance": "unique", "commit": True},
                )
                second = self.client.post(
                    "/api/agent/accumulation",
                    headers={"X-Agent-Automation": "1"},
                    json={"run_id": "run-1", "acceptance": "unique", "commit": True},
                )

            self.assertEqual(preview.status_code, 200)
            self.assertEqual(preview.get_json()["rows_after"], 2)
            self.assertEqual(preview.get_json()["legacy_duplicates_removed"], 1)
            self.assertEqual(first.status_code, 200)
            self.assertEqual(first.get_json()["accepted_novel_rows"], 1)
            self.assertEqual(second.status_code, 200)
            self.assertEqual(second.get_json()["accepted_novel_rows"], 0)
            with default_path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)

    def test_accumulation_commit_requires_recorded_post_report_approval(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            default_path = root / "default.csv"
            accepted_path = root / "accepted.csv"
            default_path.write_text(
                "ID,Product,Link\nD1,Old,https://example.com/a\n",
                encoding="utf-8",
            )
            accepted_path.write_text(
                "ID,Product,Link\nN1,New,https://example.com/b\n",
                encoding="utf-8",
            )
            default_config = root / "default-data.json"
            default_config.write_text(json.dumps({"path": str(default_path)}), encoding="utf-8")
            verification_config = root / "current-verification.json"
            verification_config.write_text(json.dumps({
                "run_id": "run-1",
                "unique_match_path": str(accepted_path),
                "price_present_path": str(accepted_path),
                "user_decision_required": True,
            }), encoding="utf-8")

            with patch.object(app_module, "PROJECT_ROOT", root), \
                    patch.object(app_module, "DEFAULT_DATA_CONFIG", default_config), \
                    patch.object(app_module, "VERIFICATION_CONFIG", verification_config):
                preview = self.client.post(
                    "/api/agent/accumulation",
                    headers={"X-Agent-Automation": "1"},
                    json={"run_id": "run-1", "acceptance": "unique", "commit": False},
                )
                commit = self.client.post(
                    "/api/agent/accumulation",
                    headers={"X-Agent-Automation": "1"},
                    json={"run_id": "run-1", "acceptance": "unique", "commit": True},
                )

            self.assertEqual(preview.status_code, 200)
            self.assertEqual(commit.status_code, 409)
            self.assertIn("post-report user approval", commit.get_json()["error"])
            with default_path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
