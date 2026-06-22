from __future__ import annotations

import argparse
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_CONTEXT = PROJECT_ROOT / "effective-verbal-context.md"
LOCAL_CONTEXT = PROJECT_ROOT / "effective-verbal-context.local.md"
LEGACY_LOCAL_CONTEXT = PROJECT_ROOT / "effective-verbal-context-local.md"

FORBIDDEN_PUBLIC_PATTERNS = {
    "Windows user path": re.compile(r"[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/]"),
    "macOS user path": re.compile(r"/Users/[^/\s]+/"),
    "Linux home path": re.compile(r"/home/[^/\s]+/"),
    "private NotebookLM notebook URL": re.compile(
        r"https://notebooklm\.google\.com/notebook/[A-Za-z0-9-]+"
    ),
    "Google account selector": re.compile(r"(?:\?|&)authuser=\d+"),
    "email address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "concrete automation run ID": re.compile(
        r"\bdaily-notebooklm-sst-data-run_\d{8}-\d{6}\b"
    ),
}


def is_git_workspace() -> bool:
    return (PROJECT_ROOT / ".git").exists()


def is_ignored(path: Path) -> bool:
    if not is_git_workspace():
        return True
    result = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", str(path.relative_to(PROJECT_ROOT))],
        cwd=PROJECT_ROOT,
        check=False,
    )
    return result.returncode == 0


def materialize() -> Path:
    if LOCAL_CONTEXT.exists():
        print(f"local context already exists: {LOCAL_CONTEXT}")
        return LOCAL_CONTEXT

    if not is_ignored(LOCAL_CONTEXT):
        raise SystemExit(
            "Refusing to create machine-specific context because "
            "effective-verbal-context.local.md is not gitignored."
        )

    if LEGACY_LOCAL_CONTEXT.exists():
        source_text = LEGACY_LOCAL_CONTEXT.read_text(encoding="utf-8")
        source_name = LEGACY_LOCAL_CONTEXT.name
    else:
        source_text = PUBLIC_CONTEXT.read_text(encoding="utf-8")
        source_name = PUBLIC_CONTEXT.name

    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    metadata = (
        "<!-- local-context\n"
        f"materialized-from: {source_name}\n"
        f"materialized-at: {now}\n"
        f"workspace-root: {PROJECT_ROOT}\n"
        "This file may contain machine/run state and must remain gitignored.\n"
        "-->\n\n"
    )
    with LOCAL_CONTEXT.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(metadata + source_text.lstrip())
    print(f"materialized local context: {LOCAL_CONTEXT}")
    return LOCAL_CONTEXT


def validate_public() -> None:
    text = PUBLIC_CONTEXT.read_text(encoding="utf-8")
    errors: list[str] = []

    for label, pattern in FORBIDDEN_PUBLIC_PATTERNS.items():
        if pattern.search(text):
            errors.append(f"public context contains {label}")

    for stale_name in ("STARTER-CONTEXT.md",):
        if stale_name in text:
            errors.append(f"public context references stale artifact: {stale_name}")

    if "effective-verbal-context.local.md" not in text:
        errors.append("public context does not explain the local materialized context")
    if is_git_workspace() and not is_ignored(LOCAL_CONTEXT):
        errors.append("effective-verbal-context.local.md is not gitignored")

    if errors:
        raise SystemExit("\n".join(f"ERROR: {error}" for error in errors))
    print("public context valid: portable and local overlay protected")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("materialize", "validate-public"))
    args = parser.parse_args()

    if args.command == "materialize":
        materialize()
    else:
        validate_public()


if __name__ == "__main__":
    main()
