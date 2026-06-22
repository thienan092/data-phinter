from __future__ import annotations

import csv
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _normalized_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value if "://" in value else f"https://{value}")
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return f"{host}{parsed.path.rstrip('/')}".lower()


def _deduplicate(rows: list[dict[str, str]], link_field: str) -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for row in rows:
        key = _normalized_url(row.get(link_field, ""))
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def build_accumulation_plan(
    default_path: Path,
    accepted_path: Path,
    *,
    link_field: str = "Link",
) -> dict:
    default_fields, default_rows = _read_csv(default_path)
    accepted_fields, accepted_rows = _read_csv(accepted_path)
    if not default_fields or default_fields != accepted_fields:
        raise ValueError("Default and accepted CSV schemas must match exactly.")
    if link_field not in default_fields:
        raise ValueError(f"Missing deduplication field: {link_field}")

    canonical_default = _deduplicate(default_rows, link_field)
    canonical_union = _deduplicate(canonical_default + accepted_rows, link_field)
    accepted_keys = {
        _normalized_url(row.get(link_field, ""))
        for row in accepted_rows
        if _normalized_url(row.get(link_field, ""))
    }
    default_keys = {
        _normalized_url(row.get(link_field, ""))
        for row in canonical_default
        if _normalized_url(row.get(link_field, ""))
    }
    added_keys = accepted_keys - default_keys

    return {
        "fieldnames": default_fields,
        "rows": canonical_union,
        "default_rows_before": len(default_rows),
        "default_unique_before": len(canonical_default),
        "accepted_rows": len(accepted_rows),
        "accepted_novel_rows": len(added_keys),
        "rows_after": len(canonical_union),
        "legacy_duplicates_removed": len(default_rows) - len(canonical_default),
    }


def commit_accumulation(
    default_path: Path,
    accepted_path: Path,
    *,
    run_id: str,
    acceptance: str,
    events_path: Path,
    timestamp: datetime | None = None,
) -> dict:
    timestamp = timestamp or datetime.now().astimezone()
    plan = build_accumulation_plan(default_path, accepted_path)
    stamp = timestamp.strftime("%Y%m%d-%H%M%S-%f")
    backup_path = default_path.with_name(f"{default_path.stem}.{run_id}.{stamp}.bak.csv")

    events_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": timestamp.isoformat(),
        "run_id": run_id,
        "phase": "accumulation",
        "event": "commit_started",
        "acceptance": acceptance,
        "default_path": str(default_path),
        "accepted_path": str(accepted_path),
        "counts": {key: value for key, value in plan.items() if isinstance(value, int)},
    }
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    shutil.copy2(default_path, backup_path)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8-sig",
            newline="",
            dir=default_path.parent,
            prefix=f".{default_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=plan["fieldnames"], extrasaction="ignore")
            writer.writeheader()
            writer.writerows(plan["rows"])
        os.replace(temp_path, default_path)
    except Exception:
        if temp_path and temp_path.exists():
            temp_path.unlink()
        raise

    result = {
        key: value
        for key, value in plan.items()
        if key not in {"fieldnames", "rows"}
    }
    result.update({
        "run_id": run_id,
        "acceptance": acceptance,
        "default_path": str(default_path),
        "accepted_path": str(accepted_path),
        "backup_path": str(backup_path),
        "events_path": str(events_path),
    })
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "timestamp": datetime.now().astimezone().isoformat(),
            "run_id": run_id,
            "phase": "accumulation",
            "event": "commit_completed",
            "acceptance": acceptance,
            "artifacts": {
                "default": str(default_path),
                "backup": str(backup_path),
            },
            "counts": {key: value for key, value in result.items() if isinstance(value, int)},
        }, ensure_ascii=False, sort_keys=True) + "\n")
    return result
