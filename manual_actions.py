from __future__ import annotations

import json
import threading
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_AUDIT_PATH = Path("diagnostics/manual-actions/events.jsonl")
_MAX_ACTIONS = 200
_ACTIONS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _append_event(event: str, action: dict[str, Any], **details: Any) -> None:
    payload = {
        "schema_version": 1,
        "event": event,
        "recorded_at": _now(),
        "request_id": action["request_id"],
        "state": action["state"],
        "status": action["status"],
        "action_kind": action.get("action_kind"),
        "requested_url": action.get("requested_url"),
        "final_url": action.get("final_url"),
        "artifact_path": action.get("artifact_path"),
        **details,
    }
    DEFAULT_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DEFAULT_AUDIT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _trim_actions() -> None:
    while len(_ACTIONS) > _MAX_ACTIONS:
        oldest_request_id = next(iter(_ACTIONS))
        del _ACTIONS[oldest_request_id]


def start_manual_action(
    request_id: str | None,
    *,
    status: str,
    action_kind: str,
    requested_url: str,
    final_url: str | None,
    artifact_path: str | None = None,
    interaction_url: str | None = None,
) -> dict[str, Any] | None:
    if not request_id:
        return None

    with _LOCK:
        action = {
            "request_id": request_id,
            "state": "pending",
            "status": status,
            "action_kind": action_kind,
            "requested_url": requested_url,
            "final_url": final_url,
            "artifact_path": artifact_path,
            "interaction_url": interaction_url,
            "detected_at": _now(),
            "finished_at": None,
            "heartbeat_count": 0,
            "open_count": 0,
            "last_opened_at": None,
            "last_client_event_at": None,
        }
        _ACTIONS[request_id] = action
        _trim_actions()
        _append_event("manual_action_detected", action)
        return deepcopy(action)


def update_manual_action(
    request_id: str | None,
    *,
    status: str,
    action_kind: str,
    final_url: str | None,
    interaction_url: str | None = None,
) -> dict[str, Any] | None:
    if not request_id:
        return None

    with _LOCK:
        action = _ACTIONS.get(request_id)
        if action is None or action["state"] != "pending":
            return deepcopy(action) if action else None
        changed = (
            action.get("status") != status
            or action.get("action_kind") != action_kind
            or action.get("final_url") != final_url
            or action.get("interaction_url") != interaction_url
        )
        action.update(
            {
                "status": status,
                "action_kind": action_kind,
                "final_url": final_url,
                "interaction_url": interaction_url,
            }
        )
        if changed:
            _append_event("manual_action_updated", action)
        return deepcopy(action)


def finish_manual_action(
    request_id: str | None,
    *,
    state: str,
    status: str,
    final_url: str | None,
    artifact_path: str | None = None,
) -> dict[str, Any] | None:
    if not request_id:
        return None
    if state not in {"resolved", "timed_out", "failed"}:
        raise ValueError(f"Unsupported manual-action state: {state}")

    with _LOCK:
        action = _ACTIONS.get(request_id)
        if action is None:
            return None
        action.update(
            {
                "state": state,
                "status": status,
                "final_url": final_url,
                "artifact_path": artifact_path or action.get("artifact_path"),
                "interaction_url": None,
                "finished_at": _now(),
            }
        )
        _append_event(f"manual_action_{state}", action)
        return deepcopy(action)


def get_manual_action(request_id: str) -> dict[str, Any] | None:
    with _LOCK:
        action = _ACTIONS.get(request_id)
        return deepcopy(action) if action else None


def record_verification_url_opened(request_id: str) -> dict[str, Any] | None:
    with _LOCK:
        action = _ACTIONS.get(request_id)
        if action is None or action["state"] != "pending" or not action.get("interaction_url"):
            return deepcopy(action) if action else None
        action["open_count"] += 1
        action["last_opened_at"] = _now()
        _append_event("verification_url_opened", action, open_count=action["open_count"])
        return deepcopy(action)


def record_client_event(request_id: str, event: str) -> dict[str, Any] | None:
    if event not in {"notification_shown", "heartbeat", "acknowledged"}:
        raise ValueError(f"Unsupported client event: {event}")

    with _LOCK:
        action = _ACTIONS.get(request_id)
        if action is None:
            return None
        if event == "heartbeat":
            action["heartbeat_count"] += 1
        action["last_client_event_at"] = _now()
        _append_event(event, action, heartbeat_count=action["heartbeat_count"])
        return deepcopy(action)
