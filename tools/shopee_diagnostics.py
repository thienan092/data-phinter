from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import cloakbrowser
from cloakbrowser import launch
from cloakbrowser.browser import launch_persistent_context
from tools.shopee_failure_taxonomy import (
    TAXONOMY_VERSION,
    classify_artifact as classify_artifact_shared,
)


DEFAULT_CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PRICE_RE = re.compile(
    r"(?<!\d)(?:(?:\u20ab|\u0111|VND)\s*)?\d{1,3}(?:[.,]\d{3})+(?:\s*(?:\u20ab|\u0111|VND))?"
    r"|(?<!\d)\d{4,}\s*(?:\u20ab|\u0111|VND)",
    re.IGNORECASE,
)


def configure_browser_binary(
    binary_mode: str,
    browser_path: str | None,
    cache_dir: str | None,
    allow_auto_update: bool,
) -> tuple[str, str | None, str | None]:
    """Select whether the probe uses CloakBrowser's patched binary or a local browser."""
    if not allow_auto_update:
        os.environ["CLOAKBROWSER_AUTO_UPDATE"] = "false"

    resolved_cache = str(Path(cache_dir)) if cache_dir else None
    if binary_mode == "cloak":
        os.environ.pop("CLOAKBROWSER_BINARY_PATH", None)
        if resolved_cache:
            os.environ["CLOAKBROWSER_CACHE_DIR"] = resolved_cache
        return "cloak", None, resolved_cache

    if binary_mode == "local":
        resolved = browser_path or os.environ.get("CLOAKBROWSER_BINARY_PATH") or DEFAULT_CHROME
        if not Path(resolved).exists():
            raise FileNotFoundError(f"Local browser binary does not exist: {resolved}")
        os.environ["CLOAKBROWSER_BINARY_PATH"] = resolved
        return "local", resolved, os.environ.get("CLOAKBROWSER_CACHE_DIR")

    existing = os.environ.get("CLOAKBROWSER_BINARY_PATH")
    if existing:
        return "auto_env", existing, os.environ.get("CLOAKBROWSER_CACHE_DIR")
    if resolved_cache:
        os.environ["CLOAKBROWSER_CACHE_DIR"] = resolved_cache
    return "auto_cloak", None, resolved_cache


def snapshot_path(path: str | None, max_entries: int = 25) -> dict[str, Any]:
    if not path:
        return {"path": None, "exists": False}

    target = Path(path)
    snapshot: dict[str, Any] = {
        "path": str(target),
        "exists": target.exists(),
        "is_dir": target.is_dir() if target.exists() else False,
    }
    if target.exists() and target.is_dir():
        entries = sorted(target.iterdir(), key=lambda item: item.name.lower())
        snapshot["direct_entry_count"] = len(entries)
        snapshot["direct_entries_sample"] = [item.name for item in entries[:max_entries]]
    elif target.exists():
        snapshot["size_bytes"] = target.stat().st_size
    return snapshot


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_tree(path: str | None, max_files: int, hash_files: bool) -> dict[str, Any]:
    if not path:
        return {"path": None, "exists": False, "files": []}

    root = Path(path)
    snapshot: dict[str, Any] = {
        "path": str(root),
        "exists": root.exists(),
        "is_dir": root.is_dir() if root.exists() else False,
        "max_files": max_files,
        "hash_files": hash_files,
        "truncated": False,
        "files": [],
    }
    if not root.exists():
        return snapshot

    if root.is_file():
        entry = file_entry(root, root.parent, hash_files)
        snapshot["files"] = [entry]
        snapshot["file_count"] = 1
        snapshot["total_size_bytes"] = entry.get("size_bytes", 0)
        snapshot["tree_sha256"] = digest_json(snapshot["files"])
        return snapshot

    files = [item for item in root.rglob("*") if item.is_file()]
    files.sort(key=lambda item: str(item.relative_to(root)).lower())
    selected = files[:max_files]
    snapshot["file_count"] = len(files)
    snapshot["captured_file_count"] = len(selected)
    snapshot["truncated"] = len(files) > len(selected)
    snapshot["total_size_bytes"] = sum(item.stat().st_size for item in selected)
    snapshot["files"] = [file_entry(item, root, hash_files) for item in selected]
    snapshot["tree_sha256"] = digest_json(snapshot["files"])
    return snapshot


def digest_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_entry(path: Path, root: Path, hash_files: bool) -> dict[str, Any]:
    stat = path.stat()
    entry: dict[str, Any] = {
        "path": str(path.relative_to(root)),
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }
    if hash_files:
        try:
            entry["sha256"] = hash_file(path)
        except OSError as exc:
            entry["sha256_error"] = f"{type(exc).__name__}: {exc}"
    return entry


def tree_file_map(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["path"]: item for item in snapshot.get("files", [])}


def diff_tree_snapshots(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_files = tree_file_map(before)
    after_files = tree_file_map(after)
    added = sorted(set(after_files) - set(before_files))
    removed = sorted(set(before_files) - set(after_files))
    common = sorted(set(before_files) & set(after_files))
    modified = [
        path
        for path in common
        if (
            before_files[path].get("size_bytes") != after_files[path].get("size_bytes")
            or before_files[path].get("sha256") != after_files[path].get("sha256")
            or before_files[path].get("mtime_ns") != after_files[path].get("mtime_ns")
        )
    ]
    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "added_count": len(added),
        "removed_count": len(removed),
        "modified_count": len(modified),
        "before_truncated": before.get("truncated", False),
        "after_truncated": after.get("truncated", False),
    }


def expected_binary_path(binary_mode: str, browser_override: str | None) -> str | None:
    if browser_override:
        return browser_override
    if binary_mode not in {"cloak", "auto_cloak"}:
        return None
    try:
        from cloakbrowser.config import get_binary_path

        return str(get_binary_path())
    except Exception:
        return None


def redacted_env_value(key: str) -> str | None:
    value = os.environ.get(key)
    if not value:
        return None
    if "PROXY" in key.upper():
        return "<set:redacted>"
    return value


def build_control_manifest(
    args: argparse.Namespace,
    out_dir: Path,
    binary_mode: str,
    browser_override: str | None,
    cache_dir: str | None,
) -> dict[str, Any]:
    relevant_env = [
        "CLOAKBROWSER_BINARY_PATH",
        "CLOAKBROWSER_CACHE_DIR",
        "CLOAKBROWSER_AUTO_UPDATE",
        "CLOAKBROWSER_DOWNLOAD_URL",
        "CLOAK_PROXY",
    ]
    expected_binary = expected_binary_path(binary_mode, browser_override)
    profile_dir = args.profile_dir if "persistent" in args.strategy else None
    return {
        "control_schema_version": 1,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "configured",
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "pid": os.getpid(),
            "platform": platform.platform(),
        },
        "cloakbrowser": {
            "version": getattr(cloakbrowser, "__version__", "unknown"),
            "module": str(Path(cloakbrowser.__file__).resolve()),
        },
        "command": {
            "argv": sys.argv,
            "cwd": str(Path.cwd()),
        },
        "runtime_controls": {
            "headless": "headful" not in args.strategy,
            "persistent": "persistent" in args.strategy,
            "binary_mode": binary_mode,
            "expected_binary_path": expected_binary,
            "browser_override": browser_override,
            "cache_dir": cache_dir,
            "profile_dir": profile_dir,
            "proxy_configured": bool(os.environ.get("CLOAK_PROXY")),
            "auto_update_allowed": args.allow_cloakbrowser_auto_update,
            "network_log_enabled": not args.disable_network_log,
            "hash_files": not args.no_file_hash,
            "snapshot_max_files": args.snapshot_max_files,
            "manual_wait_seconds": args.manual_wait_seconds,
            "timeout_ms": args.timeout_ms,
            "settle_ms": args.settle_ms,
            "wait_until": args.wait_until,
        },
        "expected_write_scope": {
            "artifact_dir": str(out_dir),
            "cache_dir": cache_dir,
            "profile_dir": profile_dir,
            "expected_binary_path": expected_binary,
        },
        "environment": {key: redacted_env_value(key) for key in relevant_env},
        "path_state_before": {
            "artifact_dir": snapshot_path(str(out_dir)),
            "cache_dir": snapshot_path(cache_dir),
            "profile_dir": snapshot_path(profile_dir),
            "expected_binary": snapshot_path(expected_binary),
        },
        "tree_state_before": {
            "artifact_dir": snapshot_tree(str(out_dir), args.snapshot_max_files, not args.no_file_hash),
            "cache_dir": snapshot_tree(cache_dir, args.snapshot_max_files, not args.no_file_hash),
            "profile_dir": snapshot_tree(profile_dir, args.snapshot_max_files, not args.no_file_hash),
            "expected_binary": snapshot_tree(expected_binary, args.snapshot_max_files, not args.no_file_hash),
        },
        "events": [],
        "network_counts": {"request": 0, "response": 0, "requestfailed": 0, "write_errors": 0},
        "context_created": False,
        "page_created": False,
        "navigation_attempted": False,
        "capture_attempted": False,
        "context_close_attempted": False,
        "context_closed": False,
        "close_error": None,
    }


def add_event(control: dict[str, Any], name: str, detail: str | None = None) -> None:
    event: dict[str, Any] = {
        "at": datetime.now().isoformat(timespec="seconds"),
        "name": name,
    }
    if detail:
        event["detail"] = detail
    control["events"].append(event)
    persist_control(control)


def persist_control(control: dict[str, Any]) -> None:
    path = control.get("control_manifest_path")
    if not path:
        return
    try:
        Path(path).write_text(json.dumps(control, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        control["control_manifest_write_error"] = f"{type(exc).__name__}: {exc}"


def context_status(control: dict[str, Any]) -> str:
    if not control.get("context_created"):
        return "not_created"
    if control.get("context_closed"):
        return "closed"
    if control.get("close_error"):
        return "close_failed"
    return "created_not_closed"


def write_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def attach_network_logger(page: Any, path: Path, control: dict[str, Any]) -> None:
    path.write_text("", encoding="utf-8")
    control["network_log_path"] = str(path)

    def record(kind: str, payload: dict[str, Any]) -> None:
        payload.update({"at": datetime.now().isoformat(timespec="seconds"), "event": kind})
        try:
            write_jsonl(path, payload)
            control["network_counts"][kind] = control["network_counts"].get(kind, 0) + 1
        except Exception:
            control["network_counts"]["write_errors"] = control["network_counts"].get("write_errors", 0) + 1

    page.on(
        "request",
        lambda request: record(
            "request",
            {
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type,
            },
        ),
    )
    page.on(
        "response",
        lambda response: record(
            "response",
            {
                "url": response.url,
                "status": response.status,
                "request_method": response.request.method,
                "resource_type": response.request.resource_type,
            },
        ),
    )
    page.on(
        "requestfailed",
        lambda request: record(
            "requestfailed",
            {
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type,
                "failure": request.failure,
            },
        ),
    )


def classify_artifact(artifact: dict[str, Any]) -> tuple[str, list[str]]:
    return classify_artifact_shared(artifact)


def write_report(out_dir: Path, artifact: dict[str, Any]) -> None:
    control = artifact.get("control", {})
    lines = [
        "# Shopee Diagnostic Report",
        "",
        f"- Strategy: `{artifact['strategy']}`",
        f"- Binary mode: `{artifact.get('binary_mode') or ''}`",
        f"- Browser override: `{artifact.get('browser_override') or ''}`",
        f"- Cache dir: `{artifact.get('cache_dir') or ''}`",
        f"- Control manifest: `{artifact.get('control_manifest_path') or ''}`",
        f"- Network log: `{control.get('network_log_path') or ''}`",
        f"- File tree diff: `{control.get('file_tree_diff_path') or ''}`",
        f"- Context status: `{context_status(control)}`",
        f"- Requested URL: {artifact['requested_url']}",
        f"- Final URL: {artifact.get('final_url') or '(none)'}",
        f"- Title: {artifact.get('title') or '(none)'}",
        f"- Classification: `{artifact['classification']}`",
        f"- Error: `{artifact.get('error') or ''}`",
        f"- HTML length: {artifact.get('html_len', 0)}",
        f"- Body text length: {artifact.get('body_text_len', 0)}",
        f"- Price candidate count: {artifact.get('price_candidate_count', 0)}",
        f"- Product link count: {artifact.get('product_link_count', 0)}",
        f"- Screenshot: `{artifact.get('screenshot_path') or ''}`",
        f"- HTML: `{artifact.get('html_path') or ''}`",
        "",
        "## Next Actions",
    ]
    lines.extend([f"- {item}" for item in artifact["recommended_next_actions"]])
    lines.extend(["", "## Body Excerpt", "", "```text", artifact.get("body_excerpt", ""), "```", ""])
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def run_probe(args: argparse.Namespace) -> Path:
    binary_mode, browser_override, cache_dir = configure_browser_binary(
        args.binary_mode,
        args.browser_path,
        args.cache_dir,
        args.allow_cloakbrowser_auto_update,
    )
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = Path(args.out_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    control = build_control_manifest(args, out_dir, binary_mode, browser_override, cache_dir)
    artifact_path = out_dir / "artifact.json"
    control_manifest_path = out_dir / "control_manifest.json"
    file_tree_diff_path = out_dir / "file_tree_diff.json"
    control["control_manifest_path"] = str(control_manifest_path)
    control["file_tree_diff_path"] = str(file_tree_diff_path)
    network_log_path = out_dir / "network_requests.jsonl"
    if not args.disable_network_log:
        network_log_path.write_text("", encoding="utf-8")
        control["network_log_path"] = str(network_log_path)
    persist_control(control)
    add_event(control, "artifact_dir_ready")

    artifact: dict[str, Any] = {
        "schema_version": 1,
        "classification_taxonomy_version": TAXONOMY_VERSION,
        "provider": "shopee",
        "strategy": args.strategy,
        "binary_mode": binary_mode,
        "requested_url": args.url,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "browser_override": browser_override,
        "cache_dir": cache_dir,
        "timeout_ms": args.timeout_ms,
        "settle_ms": args.settle_ms,
        "manual_wait_seconds": args.manual_wait_seconds,
        "control": control,
        "error": None,
    }

    context_or_browser = None
    page = None
    try:
        headless = "headful" not in args.strategy
        if "persistent" in args.strategy:
            control["phase"] = "launching_persistent_context"
            add_event(control, "launch_persistent_context_start")
            profile_dir = Path(args.profile_dir)
            profile_dir.mkdir(parents=True, exist_ok=True)
            context_or_browser = launch_persistent_context(
                profile_dir,
                headless=headless,
                humanize=True,
                human_preset="careful",
                locale="vi-VN",
                timezone="Asia/Ho_Chi_Minh",
                viewport=None,
            )
            control["context_created"] = True
            page = context_or_browser.new_page()
            control["page_created"] = True
            if not args.disable_network_log:
                attach_network_logger(page, network_log_path, control)
                add_event(control, "network_logger_attached", str(network_log_path))
            add_event(control, "page_created")
        else:
            control["phase"] = "launching_ephemeral_browser"
            add_event(control, "launch_start")
            context_or_browser = launch(
                headless=headless,
                humanize=True,
                human_preset="careful",
                locale="vi-VN",
                timezone="Asia/Ho_Chi_Minh",
            )
            control["context_created"] = True
            page = context_or_browser.new_page()
            control["page_created"] = True
            if not args.disable_network_log:
                attach_network_logger(page, network_log_path, control)
                add_event(control, "network_logger_attached", str(network_log_path))
            add_event(control, "page_created")

        response_status = None
        try:
            control["phase"] = "navigating"
            control["navigation_attempted"] = True
            add_event(control, "navigation_start", args.url)
            response = page.goto(args.url, timeout=args.timeout_ms, wait_until=args.wait_until)
            response_status = response.status if response else None
            add_event(control, "navigation_end", str(response_status))
        except Exception as exc:  # Keep partial page evidence when navigation fails.
            artifact["error"] = f"{type(exc).__name__}: {exc}"
            add_event(control, "navigation_error", artifact["error"])

        if args.manual_wait_seconds:
            print(
                f"Manual wait active for {args.manual_wait_seconds}s. "
                "Use the opened browser window if this is a headful strategy."
            )
            add_event(control, "manual_wait_start", str(args.manual_wait_seconds))
            time.sleep(args.manual_wait_seconds)
            add_event(control, "manual_wait_end")

        control["phase"] = "settling"
        add_event(control, "settle_start", str(args.settle_ms))
        time.sleep(args.settle_ms / 1000)
        add_event(control, "settle_end")
        control["phase"] = "capturing"
        control["capture_attempted"] = True
        title = page.title()
        final_url = page.url
        html = page.content()
        body_text = page.locator("body").inner_text(timeout=5000) if page.locator("body").count() else ""
        price_candidates = PRICE_RE.findall(body_text)
        product_links = page.locator("a").evaluate_all(
            """els => els.map(a => a.href).filter(h => h && (h.includes('-i.') || h.includes('/product/') || h.includes('/products/'))).slice(0, 50)"""
        )

        html_path = out_dir / "page.html"
        screenshot_path = out_dir / "screenshot.png"
        html_path.write_text(html, encoding="utf-8", errors="replace")
        page.screenshot(path=str(screenshot_path), full_page=True)
        add_event(control, "capture_saved")

        artifact.update(
            {
                "response_status": response_status,
                "final_url": final_url,
                "title": title,
                "html_len": len(html),
                "body_text_len": len(body_text),
                "body_excerpt": body_text[:2000],
                "price_candidate_count": len(price_candidates),
                "price_candidates_sample": price_candidates[:20],
                "product_link_count": len(product_links),
                "product_links_sample": product_links[:10],
                "html_path": str(html_path),
                "screenshot_path": str(screenshot_path),
            }
        )
    except Exception as exc:
        artifact["error"] = f"{type(exc).__name__}: {exc}"
        add_event(control, "probe_error", artifact["error"])
        if page is not None:
            try:
                control["phase"] = "capturing_after_error"
                control["capture_attempted"] = True
                artifact["final_url"] = page.url
                artifact["title"] = page.title()
                html = page.content()
                body_locator = page.locator("body")
                body_text = body_locator.inner_text(timeout=5000) if body_locator.count() else ""
                html_path = out_dir / "page.html"
                screenshot_path = out_dir / "screenshot.png"
                html_path.write_text(html, encoding="utf-8", errors="replace")
                page.screenshot(path=str(screenshot_path), full_page=True)
                add_event(control, "partial_capture_saved")
                artifact.update(
                    {
                        "html_len": len(html),
                        "body_text_len": len(body_text),
                        "body_excerpt": body_text[:2000],
                        "price_candidate_count": len(PRICE_RE.findall(body_text)),
                        "price_candidates_sample": PRICE_RE.findall(body_text)[:20],
                        "product_link_count": 0,
                        "product_links_sample": [],
                        "html_path": str(html_path),
                        "screenshot_path": str(screenshot_path),
                    }
                )
            except Exception as capture_exc:
                artifact["capture_error"] = f"{type(capture_exc).__name__}: {capture_exc}"
                add_event(control, "capture_error", artifact["capture_error"])
    finally:
        if context_or_browser is not None:
            control["context_close_attempted"] = True
            add_event(control, "context_close_start")
            try:
                context_or_browser.close()
                control["context_closed"] = True
                add_event(control, "context_close_end")
            except Exception as close_exc:
                control["close_error"] = f"{type(close_exc).__name__}: {close_exc}"
                add_event(control, "context_close_error", control["close_error"])
        control["phase"] = "complete"
        control["completed_at"] = datetime.now().isoformat(timespec="seconds")
        control["path_state_after"] = {
            "artifact_dir": snapshot_path(str(out_dir)),
            "cache_dir": snapshot_path(cache_dir),
            "profile_dir": snapshot_path(args.profile_dir if "persistent" in args.strategy else None),
            "expected_binary": snapshot_path(control["runtime_controls"].get("expected_binary_path")),
        }

    classification, next_actions = classify_artifact(artifact)
    artifact["classification"] = classification
    artifact["recommended_next_actions"] = next_actions

    artifact["control_manifest_path"] = str(control_manifest_path)
    control["posthoc_files"] = {
        "artifact": str(artifact_path),
        "report": str(out_dir / "report.md"),
        "control_manifest": str(control_manifest_path),
        "file_tree_diff": str(file_tree_diff_path),
        "network_requests": str(network_log_path) if not args.disable_network_log else None,
        "html": artifact.get("html_path"),
        "screenshot": artifact.get("screenshot_path"),
    }
    tree_state_after = {
        "artifact_dir": snapshot_tree(str(out_dir), args.snapshot_max_files, not args.no_file_hash),
        "cache_dir": snapshot_tree(cache_dir, args.snapshot_max_files, not args.no_file_hash),
        "profile_dir": snapshot_tree(
            args.profile_dir if "persistent" in args.strategy else None,
            args.snapshot_max_files,
            not args.no_file_hash,
        ),
        "expected_binary": snapshot_tree(
            control["runtime_controls"].get("expected_binary_path"),
            args.snapshot_max_files,
            not args.no_file_hash,
        ),
    }
    tree_diff = {
        key: diff_tree_snapshots(control["tree_state_before"][key], tree_state_after[key])
        for key in tree_state_after
        if key in control["tree_state_before"]
    }
    control["tree_state_after_digest"] = {
        key: value.get("tree_sha256") for key, value in tree_state_after.items()
    }
    control["tree_diff_summary"] = {
        key: {
            "added_count": value["added_count"],
            "removed_count": value["removed_count"],
            "modified_count": value["modified_count"],
            "before_truncated": value["before_truncated"],
            "after_truncated": value["after_truncated"],
        }
        for key, value in tree_diff.items()
    }
    file_tree_diff_path.write_text(
        json.dumps(
            {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "note": "Snapshot is stored outside artifact/control_manifest to avoid self-referential hashes.",
                "tree_state_before": control["tree_state_before"],
                "tree_state_after": tree_state_after,
                "tree_diff": tree_diff,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    artifact_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
    control_manifest_path.write_text(json.dumps(control, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(out_dir, artifact)
    return artifact_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture a Shopee scraping failure artifact.")
    parser.add_argument("--url", required=True)
    parser.add_argument(
        "--strategy",
        choices=["headless_ephemeral", "headless_persistent", "headful_persistent"],
        default="headless_ephemeral",
    )
    parser.add_argument("--out-dir", default="diagnostics/shopee")
    parser.add_argument("--profile-dir", default="diagnostics/profiles/shopee")
    parser.add_argument(
        "--cache-dir",
        default="diagnostics/cache/cloakbrowser",
        help="Workspace cache for CloakBrowser's patched binary when --binary-mode uses cloak.",
    )
    parser.add_argument(
        "--binary-mode",
        choices=["cloak", "local", "auto"],
        default="cloak",
        help="Use CloakBrowser's patched binary by default; use local only for fallback diagnostics.",
    )
    parser.add_argument(
        "--browser-path",
        default=None,
        help="Local browser path used only with --binary-mode local.",
    )
    parser.add_argument(
        "--allow-cloakbrowser-auto-update",
        action="store_true",
        help="Allow CloakBrowser wrapper update checks. Disabled by default for bounded diagnostics.",
    )
    parser.add_argument("--timeout-ms", type=int, default=45000)
    parser.add_argument("--settle-ms", type=int, default=8000)
    parser.add_argument(
        "--snapshot-max-files",
        type=int,
        default=5000,
        help="Maximum files per tree snapshot for artifact/cache/profile hashing.",
    )
    parser.add_argument(
        "--no-file-hash",
        action="store_true",
        help="Record file sizes/mtimes without SHA-256 hashes.",
    )
    parser.add_argument(
        "--disable-network-log",
        action="store_true",
        help="Disable Playwright request/response JSONL logging.",
    )
    parser.add_argument(
        "--manual-wait-seconds",
        type=int,
        default=0,
        help="Keep the page open before capture so a human can solve login/captcha in headful mode.",
    )
    parser.add_argument("--wait-until", default="domcontentloaded")
    args = parser.parse_args()

    artifact_path = run_probe(args)
    print(artifact_path)


if __name__ == "__main__":
    main()
