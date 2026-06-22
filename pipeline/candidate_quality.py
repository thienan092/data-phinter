"""Shared strict-candidate rules for NotebookLM generation and app intake."""
from __future__ import annotations

from collections import Counter
from urllib.parse import urlparse


LINK_FIELD = "Link"
PRICE_FIELD = "Giá niêm yết (VND)"
TYPE_FIELD = "Loại SP"

BAD_PRODUCT_TYPES = {"phụ kiện", "vật phẩm", "phụ trợ"}
LISTING_MARKERS = (
    "/collections/",
    "/collection/",
    "/product-category/",
    "/category/",
    "/search",
    "/blogs/",
    "/blog/",
    "/tin-tuc/",
)
LISTING_SUFFIXES = (
    "/ban-moi",
    "/ca-phe-hoa-tan",
    "/ca-phe-phin",
    "/goi-rieng-cho-ban",
    "/cac-loai-thuc-uong-ca-phe",
)


def normalized_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return value.lower().split("?", 1)[0].rstrip("/")
    host = parsed.netloc.lower().removeprefix("www.")
    return f"{parsed.scheme.lower()}://{host}{parsed.path}".rstrip("/")


def host(value: str) -> str:
    parsed = urlparse((value or "").strip())
    return parsed.netloc.lower().removeprefix("www.")


def is_listing_like(value: str) -> bool:
    url = normalized_url(value)
    path = urlparse(url).path.lower().rstrip("/")
    return any(marker in f"{path}/" for marker in LISTING_MARKERS) or path.endswith(
        LISTING_SUFFIXES
    )


def row_exclusion_reasons(row: dict[str, str]) -> list[str]:
    reasons: list[str] = []
    url = normalized_url(row.get(LINK_FIELD, ""))
    if not url.startswith(("http://", "https://")):
        reasons.append("invalid_or_missing_url")
    if not (row.get(PRICE_FIELD) or "").strip():
        reasons.append("missing_price")
    if (row.get(TYPE_FIELD) or "").strip().lower() in BAD_PRODUCT_TYPES:
        reasons.append("non_topic_product_type")
    if url and is_listing_like(url):
        reasons.append("listing_like_url")
    return reasons


def analyze_rows(rows: list[dict[str, str]], target: int = 100) -> dict:
    strict_rows: list[dict[str, str]] = []
    seen: set[str] = set()
    excluded = Counter()
    duplicate_rows = 0

    for row in rows:
        reasons = row_exclusion_reasons(row)
        if reasons:
            excluded.update(reasons)
            continue
        key = normalized_url(row.get(LINK_FIELD, ""))
        if key in seen:
            duplicate_rows += 1
            excluded.update(["duplicate_url"])
            continue
        seen.add(key)
        strict_rows.append(row)

    strict_count = len(strict_rows)
    return {
        "candidate_rows": len(rows),
        "strict_candidate_rows": strict_count,
        "target": target,
        "strict_complete": strict_count >= target and duplicate_rows == 0 and not excluded,
        "shortfall": max(0, target - strict_count),
        "duplicate_rows": duplicate_rows,
        "excluded": dict(excluded),
        "strict_rows": strict_rows,
        "distinct_hosts": len(
            {host(row.get(LINK_FIELD, "")) for row in strict_rows if host(row.get(LINK_FIELD, ""))}
        ),
    }
