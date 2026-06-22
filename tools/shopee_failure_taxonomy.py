"""Shared Shopee diagnostic artifact taxonomy."""
from __future__ import annotations

from typing import Any


TAXONOMY_VERSION = 2


def classify_artifact(artifact: dict[str, Any]) -> tuple[str, list[str]]:
    error = (artifact.get("error") or "").lower()
    final_url = (artifact.get("final_url") or "").lower()
    title = (artifact.get("title") or "").lower()
    body_excerpt = (artifact.get("body_excerpt") or "").lower()
    combined = " ".join([final_url, title, body_excerpt, error])

    environment_markers = (
        "winerror 10013",
        "forbidden by its access permissions",
        "getaddrinfo failed",
        "connecterror",
        "primary download failed",
    )
    if any(marker in combined for marker in environment_markers):
        return "environment_network_blocked", [
            "The probe did not reach Shopee; the environment blocked network or browser access.",
            "Keep this separate from Shopee captcha, selector, and access-block classifications.",
        ]
    if "/verify/captcha" in combined or "captcha" in combined:
        return "captcha_required", [
            "Treat this as a captcha challenge, not selector failure.",
            "Use a user-seeded persistent session and prefer a direct product URL.",
        ]
    if error and "timeout" in error:
        return "navigation_timeout", [
            "Retry with a less strict wait mode and capture partial evidence.",
        ]
    if "/verify/traffic" in final_url or "/verify/error" in final_url:
        return "access_blocked_or_session_required", [
            "Use a persistent headful session and prefer a direct product URL.",
        ]
    if (
        artifact.get("body_text_len", 0) < 500
        and artifact.get("product_link_count", 0) == 0
        and artifact.get("price_candidate_count", 0) == 0
    ):
        return "thin_or_empty_page", [
            "Retry with a persistent profile, longer settle/scroll, or a direct product URL.",
        ]
    if any(marker in combined for marker in ("page unavailable", "traffic", "robot", "unusual", "verify")):
        return "access_blocked_or_session_required", [
            "Use a persistent headful session and preserve the access-block state.",
        ]
    if any(marker in combined for marker in ("log in", "login", "dang nhap", "sign in", "is_logged_in=false")):
        return "login_required", [
            "Seed a persistent headful profile through manual login.",
        ]
    if artifact.get("price_candidate_count", 0) > 0:
        return "loaded_with_price_candidates", [
            "Run selector rediscovery and map prices to product cards.",
        ]
    if artifact.get("product_link_count", 0) > 0:
        return "loaded_without_price_candidates", [
            "Inspect lazy loading, hidden DOM, or script data.",
        ]
    return "unknown_scrape_failure", [
        "Inspect screenshot and HTML before changing source.",
    ]
