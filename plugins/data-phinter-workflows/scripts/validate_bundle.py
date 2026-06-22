from __future__ import annotations

import json
import re
import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
SOURCE_ROOT = REPO_ROOT / ".codex" / "skills"
BUNDLE_ROOT = PLUGIN_ROOT / "skills"
SKILLS = (
    "read-effective-verbal-context",
    "notebooklm-sst-research",
    "app-sst-candidate-intake",
    "shopee-scrape-recovery",
)
NAV_START = "<!-- plugin-navigation:start -->"
NAV_END = "<!-- plugin-navigation:end -->"
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


def files_under(root: Path) -> dict[Path, Path]:
    return {
        path.relative_to(root): path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
    }


def strip_navigation(text: str) -> str:
    start = text.find(NAV_START)
    end = text.find(NAV_END)
    if start < 0 or end < 0 or end < start:
        raise ValueError("bundled SKILL.md is missing deterministic plugin navigation")
    return text[:start].rstrip() + "\n"


def validate_manifest(errors: list[str]) -> None:
    path = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid plugin manifest: {exc}")
        return
    if manifest.get("name") != PLUGIN_ROOT.name:
        errors.append("manifest name must match the plugin directory")
    if not SEMVER.fullmatch(str(manifest.get("version", ""))):
        errors.append("manifest version is not semantic versioning")
    if manifest.get("skills") != "./skills/":
        errors.append("manifest skills path must be ./skills/")


def validate_skill_snapshot(errors: list[str]) -> None:
    if (BUNDLE_ROOT / "stranger-audit").exists():
        errors.append("Stranger audit must remain external to the plugin")
    if (BUNDLE_ROOT / "write-effective-verbal-context").exists():
        errors.append("The owner-retained write-effective-verbal-context skill must not be bundled")
    for name in SKILLS:
        source = SOURCE_ROOT / name
        bundled = BUNDLE_ROOT / name
        source_files = files_under(source)
        bundled_files = files_under(bundled) if bundled.exists() else {}
        if set(source_files) != set(bundled_files):
            errors.append(
                f"{name}: canonical/bundled file sets differ: "
                f"source={sorted(map(str, source_files))}, bundle={sorted(map(str, bundled_files))}"
            )
            continue
        for relative, source_path in source_files.items():
            bundled_path = bundled_files[relative]
            if relative == Path("SKILL.md"):
                try:
                    bundled_text = strip_navigation(bundled_path.read_text(encoding="utf-8"))
                except ValueError as exc:
                    errors.append(f"{name}: {exc}")
                    continue
                source_text = source_path.read_text(encoding="utf-8").rstrip() + "\n"
                if bundled_text != source_text:
                    errors.append(f"{name}: bundled SKILL.md differs before navigation footer")
            elif source_path.read_bytes() != bundled_path.read_bytes():
                errors.append(f"{name}: bundled file differs: {relative}")


def validate_links(errors: list[str]) -> None:
    for markdown in PLUGIN_ROOT.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(text):
            target = target.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (markdown.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"broken link in {markdown.relative_to(PLUGIN_ROOT)}: {target}")


def validate_access_contract(errors: list[str]) -> None:
    overview = (PLUGIN_ROOT / "references" / "overview.md").read_text(encoding="utf-8")
    architecture = (PLUGIN_ROOT / "references" / "architecture.md").read_text(encoding="utf-8")
    artifact_contract = (
        PLUGIN_ROOT / "references" / "artifact-and-status-contract.md"
    ).read_text(encoding="utf-8")
    prerequisites = (
        PLUGIN_ROOT / "references" / "runtime-prerequisites.md"
    ).read_text(encoding="utf-8")
    plugin_readme = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")
    repo_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    for name in SKILLS:
        if name not in overview:
            errors.append(f"short overview does not expose plugin skill: {name}")
    if "write-effective-verbal-context" not in plugin_readme or "not bundled" not in plugin_readme:
        errors.append("plugin README does not state the owner-held write-skill boundary")
    if "Agent Controls And Information Parity" not in architecture:
        errors.append("detailed architecture is missing the information-parity contract")
    if "Accumulate approved unique" not in repo_readme:
        errors.append("repository README does not explain the agent-only accumulation control")
    if "read-effective-verbal-context" not in repo_readme:
        errors.append("repository README does not expose the required stranger entry skill")
    if "Runtime Prerequisites And Stop Behavior" not in prerequisites:
        errors.append("runtime prerequisites do not expose pre-execution stop behavior")
    if "Legacy Provenance" not in artifact_contract:
        errors.append("artifact contract does not explain historical provenance limitations")


def validate_policy_regressions(errors: list[str]) -> None:
    notebook_skill = (
        SOURCE_ROOT / "notebooklm-sst-research" / "SKILL.md"
    ).read_text(encoding="utf-8")
    intake_audit = (
        SOURCE_ROOT
        / "app-sst-candidate-intake"
        / "scripts"
        / "audit_candidates.py"
    ).read_text(encoding="utf-8")
    shopee_skill = (
        SOURCE_ROOT / "shopee-scrape-recovery" / "SKILL.md"
    ).read_text(encoding="utf-8")
    legacy_builder = (REPO_ROOT / "pipeline" / "build_request.py").read_text(
        encoding="utf-8"
    )
    exemplar_builder = (REPO_ROOT / "pipeline" / "build_exemplar.py").read_text(
        encoding="utf-8"
    )
    manifest = json.loads(
        (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    repo_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    intake_skill = (
        SOURCE_ROOT / "app-sst-candidate-intake" / "SKILL.md"
    ).read_text(encoding="utf-8")

    for required in (
        REPO_ROOT / "pipeline" / "candidate_quality.py",
        REPO_ROOT / "pipeline" / "validate_candidates.py",
    ):
        if not required.is_file():
            errors.append(f"shared strict-candidate component is missing: {required.name}")
    if "candidate_quality" not in intake_audit:
        errors.append("app intake audit does not use the shared strict-candidate rules")
    if "Claude-in-Chrome" in notebook_skill:
        errors.append("NotebookLM skill still requires the obsolete Claude-in-Chrome interface")
    if "tabs_context_mcp (createIfEmpty)" in notebook_skill:
        errors.append("NotebookLM skill still prescribes an obsolete browser tool call")
    if "LEGACY_UNSUPPORTED" not in legacy_builder:
        errors.append("legacy steered request builder is not clearly disabled")
    if "audit-only" not in exemplar_builder.lower():
        errors.append("exemplar niche-gap output is not marked audit-only")
    if "Update effective-verbal-context.md" in shopee_skill:
        errors.append("Shopee skill directly claims the owner-held handoff-writing action")
    if re.search(r"[A-Za-z]:\\Users\\", shopee_skill):
        errors.append("Shopee skill contains a machine-specific user path")
    if "127.0.0.1:5002" in intake_skill:
        errors.append("app intake skill hard-codes a prior-session port")
    if "python app.py" not in intake_skill or "default `5000`" not in intake_skill:
        errors.append("app intake skill does not expose the supported start command and port rule")
    if "Delete the `app.py` file" in repo_readme or "Xóa file `app.py`" in repo_readme:
        errors.append("repository README still tells strangers to replace the supported app")
    if "under 3k lines" in repo_readme or "dưới 3k dòng" in repo_readme:
        errors.append("repository README contains a stale fixed source-line claim")
    default_prompts = manifest.get("interface", {}).get("defaultPrompt", [])
    if any(
        prompt == "Audit and process the current SST candidate set."
        for prompt in default_prompts
    ):
        errors.append("plugin default prompt assumes the selected candidate is eligible")


def main() -> None:
    errors: list[str] = []
    validate_manifest(errors)
    validate_skill_snapshot(errors)
    validate_links(errors)
    validate_access_contract(errors)
    validate_policy_regressions(errors)
    forbidden = [
        path.relative_to(PLUGIN_ROOT)
        for path in PLUGIN_ROOT.rglob("*")
        if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}
    ]
    if forbidden:
        errors.append(f"runtime cache files are bundled: {forbidden}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"bundle valid: {len(SKILLS)} skills, semantic links intact")


if __name__ == "__main__":
    main()
