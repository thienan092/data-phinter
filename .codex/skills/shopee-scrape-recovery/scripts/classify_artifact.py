from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def classify_artifact(artifact: dict[str, Any]) -> tuple[str, list[str]]:
    error = (artifact.get("error") or "").lower()
    final_url = (artifact.get("final_url") or "").lower()
    title = (artifact.get("title") or "").lower()
    body_excerpt = (artifact.get("body_excerpt") or "").lower()
    combined = " ".join([final_url, title, body_excerpt, error])

    environment_block_markers = [
        "winerror 10013",
        "forbidden by its access permissions",
        "getaddrinfo failed",
        "connecterror",
        "primary download failed",
    ]
    if any(marker in combined for marker in environment_block_markers):
        return "environment_network_blocked", [
            "The probe did not reach Shopee; the local environment blocked network or binary download.",
            "Keep this separate from Shopee captcha, selector, and access-block classifications.",
            "If the user wants a true CloakBrowser binary test, run with approved network/cache access or preinstall the patched binary.",
        ]

    if "/verify/captcha" in combined or "captcha" in combined:
        return "captcha_required", [
            "Treat this as a captcha/anti-bot challenge, not selector failure.",
            "Retry with persistent headful manual session seeding if the user can solve the challenge.",
            "If manual seeding still lands on captcha/load-error, prefer direct product URL probe before adding proxy.",
        ]

    blocked_markers = [
        "page unavailable",
        "traffic",
        "robot",
        "unusual",
        "verify",
    ]
    login_markers = ["log in", "login", "dang nhap", "sign in", "is_logged_in=false"]

    if error and "timeout" in error:
        return "navigation_timeout", [
            "Retry with a less strict wait mode such as domcontentloaded or commit.",
            "Capture partial page evidence before changing selectors.",
        ]

    if "/verify/traffic" in final_url or "/verify/error" in final_url:
        return "access_blocked_or_session_required", [
            "Try persistent headful with manual wait so the user can solve login/verification once.",
            "Reuse the same profile directory and prefer direct product URLs next.",
        ]

    if (
        artifact.get("body_text_len", 0) < 500
        and artifact.get("product_link_count", 0) == 0
        and artifact.get("price_candidate_count", 0) == 0
    ):
        return "thin_or_empty_page", [
            "The page reached Shopee but did not render searchable product content.",
            "Retry with persistent headful profile, longer settle/scroll, or a direct product URL before changing selectors.",
            "Keep this separate from captcha, traffic verification, and selector failure.",
        ]

    if any(marker in combined for marker in blocked_markers):
        return "access_blocked_or_session_required", [
            "Try persistent headful with manual wait so the user can solve login/verification once.",
            "Reuse the same profile directory and prefer direct product URLs next.",
        ]

    if any(marker in combined for marker in login_markers):
        return "login_required", [
            "Seed a persistent headful profile through manual login.",
            "Keep login-required separate from selector failure.",
        ]

    if artifact.get("price_candidate_count", 0) > 0:
        return "loaded_with_price_candidates", [
            "Run selector rediscovery against visible price nodes.",
            "Map prices to product cards before patching extraction.",
        ]

    if artifact.get("product_link_count", 0) > 0:
        return "loaded_without_price_candidates", [
            "Inspect lazy loading, hidden DOM, or script data.",
            "Add scroll/wait probes before changing core backend behavior.",
        ]

    return "unknown_scrape_failure", [
        "Inspect screenshot and HTML before changing source.",
        "Improve artifact capture if evidence is insufficient.",
    ]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: classify_artifact.py <artifact.json>", file=sys.stderr)
        return 2

    artifact_path = Path(sys.argv[1])
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    classification, actions = classify_artifact(artifact)
    print(json.dumps({
        "artifact": str(artifact_path),
        "classification": classification,
        "recommended_next_actions": actions,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
