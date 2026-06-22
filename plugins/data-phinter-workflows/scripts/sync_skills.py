from __future__ import annotations

import shutil
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
SOURCE_ROOT = REPO_ROOT / ".codex" / "skills"
TARGET_ROOT = PLUGIN_ROOT / "skills"
SKILLS = (
    "read-effective-verbal-context",
    "notebooklm-sst-research",
    "app-sst-candidate-intake",
    "shopee-scrape-recovery",
)
NAV_START = "<!-- plugin-navigation:start -->"
NAV_END = "<!-- plugin-navigation:end -->"
NAVIGATION = f"""

{NAV_START}
## Plugin Navigation

- [Short workflow overview](../../references/overview.md)
- [Detailed architecture](../../references/architecture.md)
- [Artifact and status contract](../../references/artifact-and-status-contract.md)
- [Runtime prerequisites and stop behavior](../../references/runtime-prerequisites.md)

When an accepted workflow improvement changes entry points, responsibilities, status contracts, or
decision gates, synchronize plugin-owned skills/references and report the required README/local
handoff delta to the project owner. The committed context changes only through explicit
virtualization. Do not assume the owner-held handoff-writing skill is bundled.
{NAV_END}
"""


def ignored(_directory: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name == "__pycache__" or name.endswith((".pyc", ".pyo"))
    }


def ensure_within_plugin(path: Path) -> None:
    if PLUGIN_ROOT not in path.resolve().parents:
        raise RuntimeError(f"Refusing to modify a path outside the plugin: {path}")


def sync_skill(name: str) -> None:
    source = SOURCE_ROOT / name
    target = TARGET_ROOT / name
    if not (source / "SKILL.md").is_file():
        raise FileNotFoundError(f"Canonical skill is missing SKILL.md: {source}")
    ensure_within_plugin(target)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=ignored)
    skill_path = target / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    if NAV_START in text or NAV_END in text:
        raise ValueError(f"Canonical skill unexpectedly contains plugin navigation markers: {name}")
    skill_path.write_text((text.rstrip() + NAVIGATION).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    for child in TARGET_ROOT.iterdir():
        if child.is_dir() and child.name not in SKILLS:
            ensure_within_plugin(child)
            shutil.rmtree(child)
    for name in SKILLS:
        sync_skill(name)
        print(f"synced {name}")


if __name__ == "__main__":
    main()
