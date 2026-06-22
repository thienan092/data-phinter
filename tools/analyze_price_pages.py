"""Analyze ambiguous price pages and produce reusable extraction repairs."""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
}
LISTING_PARTS = (
    "/collections/",
    "/collection/",
    "/product-category/",
    "/category/",
    "/search",
    "/goi-rieng-cho-ban",
)
SELECTORS = (
    "#price-preview .pro-price",
    ".summary .price ins .woocommerce-Price-amount",
    ".product-info .price ins .woocommerce-Price-amount",
    ".summary .price > .woocommerce-Price-amount",
    ".product-info .price > .woocommerce-Price-amount",
    "meta[itemprop='price']::content",
    "meta[property='og:price:amount']::content",
)


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_price(value) -> int | None:
    if value is None:
        return None
    digits = re.sub(r"[^0-9]", "", str(value))
    return int(digits) if digits else None


def normalized_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def is_listing_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(part in path for part in LISTING_PARTS) or path.rstrip("/").endswith("/ca-phe-phin")


def text_price(element, attribute: str | None = None) -> int | None:
    value = element.get(attribute) if attribute else element.get_text(" ", strip=True)
    return parse_price(value)


def jsonld_product_prices(soup: BeautifulSoup) -> list[int]:
    prices: list[int] = []
    for script in soup.select("script[type='application/ld+json']"):
        try:
            root = json.loads(script.string or script.get_text())
        except (TypeError, json.JSONDecodeError):
            continue
        stack = root if isinstance(root, list) else [root]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
                continue
            if not isinstance(node, dict):
                continue
            node_type = node.get("@type")
            if node_type == "Product" or (isinstance(node_type, list) and "Product" in node_type):
                offers = node.get("offers")
                offer_list = offers if isinstance(offers, list) else [offers]
                for offer in offer_list:
                    if not isinstance(offer, dict):
                        continue
                    for key in ("price", "lowPrice", "highPrice"):
                        price = parse_price(offer.get(key))
                        if price is not None:
                            prices.append(price)
            stack.extend(value for value in node.values() if isinstance(value, (dict, list)))
    return prices


def resolve_listing_url(soup: BeautifulSoup, listing_url: str, product: str) -> tuple[str | None, float]:
    target = normalized_text(product)
    best_url = None
    best_score = 0.0
    for anchor in soup.select("a[href]"):
        text = normalized_text(anchor.get_text(" ", strip=True))
        if not text:
            continue
        href = urljoin(listing_url, anchor.get("href"))
        if is_listing_url(href):
            continue
        score = SequenceMatcher(None, target, text).ratio()
        if target in text or text in target:
            score = max(score, min(len(target), len(text)) / max(len(target), len(text)))
        if score > best_score:
            best_url, best_score = href, score
    return (best_url, best_score) if best_score >= 0.72 else (None, best_score)


def choose_recipe(soup: BeautifulSoup, expected_price: int) -> tuple[str | None, int | None, str]:
    fallback = None
    for recipe in SELECTORS:
        selector, _, attribute = recipe.partition("::")
        elements = soup.select(selector)
        values = [
            text_price(element, attribute or None)
            for element in elements
        ]
        matching = [value for value in values if value == expected_price]
        if len(elements) == 1 and len(matching) == 1:
            return recipe, expected_price, "stable_dom"
        if len(elements) == 1 and values[0] is not None and fallback is None:
            fallback = (recipe, values[0], "stable_dom")

    prices = jsonld_product_prices(soup)
    if expected_price in prices:
        return "jsonld:Product.offers.price", expected_price, "structured_data"
    distinct_prices = list(dict.fromkeys(prices))
    if len(distinct_prices) == 1:
        return "jsonld:Product.offers.price", distinct_prices[0], "structured_data"
    if fallback:
        return fallback
    return None, None, "unresolved"


def analyze_row(row: dict[str, str], session: requests.Session) -> dict[str, str | int | float | None]:
    original_url = row["Link"]
    expected_price = parse_price(row.get("Giá niêm yết (VND)"))
    result = {
        "ID": row["ID"],
        "product": row.get("Sản phẩm"),
        "original_url": original_url,
        "resolved_url": original_url,
        "url_action": "keep",
        "expected_price": expected_price,
        "observed_price": None,
        "method": None,
        "selector_or_recipe": None,
        "status": "unresolved",
        "rationale": "",
    }
    try:
        response = session.get(original_url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        result["status"] = "fetch_failed"
        result["rationale"] = str(exc)
        return result

    soup = BeautifulSoup(response.text, "html.parser")
    target_url = response.url
    if is_listing_url(target_url):
        resolved_url, score = resolve_listing_url(soup, target_url, row.get("Sản phẩm", ""))
        if not resolved_url:
            result["url_action"] = "replace_or_reject"
            result["status"] = "listing_unresolved"
            result["rationale"] = f"No trustworthy direct product URL; best title score={score:.2f}."
            return result
        result["resolved_url"] = resolved_url
        result["url_action"] = "replace"
        try:
            response = session.get(resolved_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as exc:
            result["status"] = "replacement_fetch_failed"
            result["rationale"] = str(exc)
            return result

    if expected_price is None:
        result["status"] = "invalid_expected_price"
        result["rationale"] = "Candidate price is missing or invalid."
        return result

    recipe, observed, method = choose_recipe(soup, expected_price)
    result["selector_or_recipe"] = recipe
    result["observed_price"] = observed
    result["method"] = method
    if recipe:
        if observed == expected_price:
            result["status"] = "repair_ready"
            result["rationale"] = (
                "Price is product-scoped and uniquely extractable with the proposed method."
            )
        else:
            result["status"] = "price_changed"
            result["rationale"] = (
                f"Product-scoped current price changed from {expected_price} to {observed}."
            )
    else:
        result["rationale"] = (
            "Expected price is present multiple times or lacks a stable product-scoped extraction path."
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--verification-report", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repaired-csv", type=Path)
    args = parser.parse_args()

    candidates = {row["ID"]: row for row in load_rows(args.candidates)}
    report = load_rows(args.verification_report)
    selected = [
        candidates[row["ID"]]
        for row in report
        if int(row.get("match_count") or 0) > 1
    ]

    session = requests.Session()
    session.headers.update(HEADERS)
    session.mount(
        "https://",
        HTTPAdapter(max_retries=Retry(total=3, backoff_factor=0.8, status_forcelist=(429, 500, 502, 503, 504))),
    )
    results = [analyze_row(row, session) for row in selected]
    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "input_count": len(selected),
        "repair_ready": sum(row["status"] == "repair_ready" for row in results),
        "price_changed": sum(row["status"] == "price_changed" for row in results),
        "listing_unresolved": sum(row["status"] == "listing_unresolved" for row in results),
        "unresolved": sum(
            row["status"] not in {"repair_ready", "price_changed", "listing_unresolved"}
            for row in results
        ),
        "rows": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.repaired_csv:
        resolved = {
            row["ID"]: row
            for row in results
            if row["status"] in {"repair_ready", "price_changed"}
        }
        fieldnames = list(selected[0].keys()) if selected else []
        args.repaired_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.repaired_csv.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for candidate in selected:
                repair = resolved.get(candidate["ID"])
                if not repair:
                    continue
                output = dict(candidate)
                output["Link"] = repair["resolved_url"]
                output["Giá niêm yết (VND)"] = repair["observed_price"]
                output["HTML"] = repair["selector_or_recipe"]
                writer.writerow(output)
    print(json.dumps({key: value for key, value in payload.items() if key != "rows"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
