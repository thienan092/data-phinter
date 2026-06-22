import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "context_handoff.py"
SPEC = importlib.util.spec_from_file_location("context_handoff", MODULE_PATH)
context_handoff = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(context_handoff)


class ContextHandoffTests(unittest.TestCase):
    def test_materialize_prefers_legacy_local_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_path = root / "effective-verbal-context.md"
            local_path = root / "effective-verbal-context.local.md"
            legacy_path = root / "effective-verbal-context-local.md"
            public_path.write_text("public\n", encoding="utf-8")
            legacy_path.write_text("legacy local\n", encoding="utf-8")

            with patch.object(context_handoff, "PROJECT_ROOT", root), patch.object(
                context_handoff, "PUBLIC_CONTEXT", public_path
            ), patch.object(context_handoff, "LOCAL_CONTEXT", local_path), patch.object(
                context_handoff, "LEGACY_LOCAL_CONTEXT", legacy_path
            ), patch.object(context_handoff, "is_ignored", return_value=True):
                result = context_handoff.materialize()

            self.assertEqual(result, local_path)
            text = local_path.read_text(encoding="utf-8")
            self.assertIn("materialized-from: effective-verbal-context-local.md", text)
            self.assertIn("legacy local", text)

    def test_materialize_never_overwrites_existing_local(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_path = root / "effective-verbal-context.md"
            local_path = root / "effective-verbal-context.local.md"
            legacy_path = root / "effective-verbal-context-local.md"
            public_path.write_text("public\n", encoding="utf-8")
            local_path.write_text("keep me\n", encoding="utf-8")

            with patch.object(context_handoff, "PROJECT_ROOT", root), patch.object(
                context_handoff, "PUBLIC_CONTEXT", public_path
            ), patch.object(context_handoff, "LOCAL_CONTEXT", local_path), patch.object(
                context_handoff, "LEGACY_LOCAL_CONTEXT", legacy_path
            ):
                context_handoff.materialize()

            self.assertEqual(local_path.read_text(encoding="utf-8"), "keep me\n")

    def test_public_validation_rejects_machine_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_path = root / "effective-verbal-context.md"
            local_path = root / "effective-verbal-context.local.md"
            public_path.write_text(
                "effective-verbal-context.local.md\nC:\\Users\\Person\\project\n",
                encoding="utf-8",
            )

            with patch.object(context_handoff, "PROJECT_ROOT", root), patch.object(
                context_handoff, "PUBLIC_CONTEXT", public_path
            ), patch.object(context_handoff, "LOCAL_CONTEXT", local_path), patch.object(
                context_handoff, "is_git_workspace", return_value=False
            ):
                with self.assertRaises(SystemExit):
                    context_handoff.validate_public()

    def test_public_validation_rejects_concrete_run_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            public_path = root / "effective-verbal-context.md"
            local_path = root / "effective-verbal-context.local.md"
            public_path.write_text(
                "effective-verbal-context.local.md\n"
                "daily-notebooklm-sst-data-run_20260622-131925\n",
                encoding="utf-8",
            )

            with patch.object(context_handoff, "PROJECT_ROOT", root), patch.object(
                context_handoff, "PUBLIC_CONTEXT", public_path
            ), patch.object(context_handoff, "LOCAL_CONTEXT", local_path), patch.object(
                context_handoff, "is_git_workspace", return_value=False
            ):
                with self.assertRaises(SystemExit):
                    context_handoff.validate_public()


if __name__ == "__main__":
    unittest.main()
