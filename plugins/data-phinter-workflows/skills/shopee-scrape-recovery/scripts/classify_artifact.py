from __future__ import annotations

import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from tools.shopee_failure_taxonomy import (  # noqa: E402
    TAXONOMY_VERSION,
    classify_artifact,
)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: classify_artifact.py <artifact.json>", file=sys.stderr)
        return 2

    artifact_path = Path(sys.argv[1])
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    classification, actions = classify_artifact(artifact)
    stored_classification = artifact.get("classification")
    stored_taxonomy_version = artifact.get("classification_taxonomy_version")
    changed = bool(stored_classification and stored_classification != classification)
    print(json.dumps({
        "artifact": str(artifact_path),
        "taxonomy_version": TAXONOMY_VERSION,
        "classification": classification,
        "stored_classification": stored_classification,
        "stored_taxonomy_version": stored_taxonomy_version,
        "classification_changed": changed,
        "reclassification_note": (
            "Current taxonomy interpretation differs from the immutable stored artifact."
            if changed
            else "Current taxonomy agrees with the stored classification or no stored classification exists."
        ),
        "recommended_next_actions": actions,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
