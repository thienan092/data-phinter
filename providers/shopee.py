from __future__ import annotations

import os
import re
import time
import json
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup
from cloakbrowser.browser import launch_persistent_context


PROVIDER = "shopee"
STRATEGY = "seeded_persistent_profile"
DEFAULT_CACHE_DIR = "diagnostics/cache/cloakbrowser"
DEFAULT_PROFILE_DIR = "diagnostics/profiles/shopee-cloak"
DEFAULT_ARTIFACT_DIR = "diagnostics/shopee-provider"
PRICE_RE = re.compile(
    r"(?<!\d)(?:(?:\u20ab|\u0111|VND)\s*)?\d{1,3}(?:[.,]\d{3})+(?:\s*(?:\u20ab|\u0111|VND))?"
    r"|(?<!\d)\d{4,}\s*(?:\u20ab|\u0111|VND)",
    re.IGNORECASE,
)


@dataclass
class ShopeeResult:
    status: str
    price: int | None = None
    passed: bool = False
    match_count: int = -1
    provider: str = PROVIDER
    strategy: str = STRATEGY
    classification: str | None = None
    final_url: str | None = None
    response_status: int | None = None
    error: str | None = None
    artifact_path: str | None = None
    price_candidates: list[int] = field(default_factory=list)
    price_candidates_sample: list[str] = field(default_factory=list)
    product_link_count: int = 0
    product_cards: list[dict[str, Any]] = field(default_factory=list)
    selected_product: dict[str, Any] | None = None

    def to_response(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "strategy": self.strategy,
            "status": self.status,
            "classification": self.classification or self.status,
            "price": self.price,
            "passed": self.passed,
            "match_count": self.match_count,
            "final_url": self.final_url,
            "response_status": self.response_status,
            "error": self.error,
            "artifact_path": self.artifact_path,
            "price_candidates": self.price_candidates,
            "price_candidates_sample": self.price_candidates_sample,
            "product_link_count": self.product_link_count,
            "product_cards": self.product_cards[:20],
            "selected_product": self.selected_product,
        }


def is_shopee_url(url: str | None) -> bool:
    if not url:
        return False
    host = urlparse(url).netloc.lower()
    return host == "shopee.vn" or host.endswith(".shopee.vn")


def extract_price_shopee(url: str, selector: str | None = None) -> ShopeeResult:
    page_result = load_shopee_page(url)
    if page_result.status != "loaded":
        return result_from_loaded_page(page_result)

    if page_result.product_cards:
        result = extract_price_from_cards(
            page_result.product_cards,
            final_url=page_result.final_url,
            response_status=page_result.response_status,
        )
        result.artifact_path = page_result.artifact_path
        return result

    result = extract_price_from_text(
        page_result.body_text or "",
        selector=selector,
        final_url=page_result.final_url,
        response_status=page_result.response_status,
    )
    result.product_link_count = page_result.product_link_count
    result.product_cards = page_result.product_cards
    result.artifact_path = page_result.artifact_path
    return result


def verify_price_shopee(url: str, price: int) -> ShopeeResult:
    page_result = load_shopee_page(url)
    if page_result.status != "loaded":
        return result_from_loaded_page(page_result)

    if page_result.product_cards:
        result = verify_price_in_cards(
            page_result.product_cards,
            price,
            final_url=page_result.final_url,
            response_status=page_result.response_status,
        )
        result.artifact_path = page_result.artifact_path
        return result

    result = verify_price_in_text(
        page_result.body_text or "",
        price,
        final_url=page_result.final_url,
        response_status=page_result.response_status,
    )
    result.product_link_count = page_result.product_link_count
    result.price_candidates = page_result.price_candidates
    result.price_candidates_sample = page_result.price_candidates_sample
    result.product_cards = page_result.product_cards
    result.artifact_path = page_result.artifact_path
    return result


def extract_price_from_cards(
    product_cards: list[dict[str, Any]],
    final_url: str | None = None,
    response_status: int | None = None,
) -> ShopeeResult:
    priced_cards = dedupe_product_cards([card for card in product_cards if card.get("price") is not None])
    chosen = first_preferred_card(priced_cards, final_url)
    prices = [int(card["price"]) for card in priced_cards if card.get("price") is not None]
    if chosen:
        return ShopeeResult(
            status="ok",
            classification="loaded_with_price_candidates",
            price=int(chosen["price"]),
            final_url=final_url,
            response_status=response_status,
            price_candidates=prices[:20],
            price_candidates_sample=[card.get("price_text", "") for card in priced_cards[:20]],
            product_link_count=len(product_cards),
            product_cards=product_cards[:20],
            selected_product=chosen,
        )

    return ShopeeResult(
        status="price_changed",
        classification="loaded_without_price_candidates",
        final_url=final_url,
        response_status=response_status,
        product_link_count=len(product_cards),
        product_cards=product_cards[:20],
    )


def verify_price_in_cards(
    product_cards: list[dict[str, Any]],
    price: int,
    final_url: str | None = None,
    response_status: int | None = None,
) -> ShopeeResult:
    priced_cards = dedupe_product_cards([card for card in product_cards if card.get("price") is not None])
    matches = [card for card in priced_cards if int(card["price"]) == price]
    prices = [int(card["price"]) for card in priced_cards]
    if not matches:
        return ShopeeResult(
            status="price_changed",
            classification="loaded_with_price_candidates" if priced_cards else "loaded_without_price_candidates",
            passed=False,
            match_count=0,
            final_url=final_url,
            response_status=response_status,
            price_candidates=prices[:20],
            price_candidates_sample=[card.get("price_text", "") for card in priced_cards[:20]],
            product_link_count=len(product_cards),
            product_cards=product_cards[:20],
        )

    return ShopeeResult(
        status="ok",
        classification="loaded_with_price_candidates",
        passed=len(matches) == 1,
        match_count=len(matches),
        final_url=final_url,
        response_status=response_status,
        price_candidates=prices[:20],
        price_candidates_sample=[card.get("price_text", "") for card in priced_cards[:20]],
        product_link_count=len(product_cards),
        product_cards=product_cards[:20],
        selected_product=first_preferred_card(matches, final_url),
    )


def extract_price_from_html(
    html: str,
    selector: str | None = None,
    final_url: str | None = None,
    response_status: int | None = None,
) -> ShopeeResult:
    soup = BeautifulSoup(html, "html.parser")
    body_text = visible_text_from_soup(soup)
    status = classify_loaded_content(final_url or "", body_text, html)
    if status != "loaded":
        return ShopeeResult(status=status, classification=status, final_url=final_url, response_status=response_status)

    raw_candidates = price_strings(body_text)
    prices = [value for value in (parse_price_text(raw) for raw in raw_candidates) if value is not None]
    selected_text = None
    if selector:
        selected = soup.select_one(selector)
        selected_text = selected.get_text(" ", strip=True) if selected else None
        selected_price = parse_price_text(selected_text or "")
        if selected_price is not None:
            return ShopeeResult(
                status="ok",
                classification="loaded_with_price_candidates",
                price=selected_price,
                final_url=final_url,
                response_status=response_status,
                price_candidates=prices[:20],
                price_candidates_sample=raw_candidates[:20],
                product_link_count=count_product_links(html),
            )

    if prices:
        return ShopeeResult(
            status="ok",
            classification="loaded_with_price_candidates",
            price=prices[0],
            final_url=final_url,
            response_status=response_status,
            price_candidates=prices[:20],
            price_candidates_sample=raw_candidates[:20],
            product_link_count=count_product_links(html),
        )

    return ShopeeResult(
        status="selector_failed" if selected_text is not None else "price_changed",
        classification="loaded_without_price_candidates",
        final_url=final_url,
        response_status=response_status,
        product_link_count=count_product_links(html),
    )


def extract_price_from_text(
    body_text: str,
    selector: str | None = None,
    final_url: str | None = None,
    response_status: int | None = None,
) -> ShopeeResult:
    status = classify_loaded_content(final_url or "", body_text, "")
    if status != "loaded":
        return ShopeeResult(status=status, classification=status, final_url=final_url, response_status=response_status)

    raw_candidates = price_strings(body_text)
    prices = [value for value in (parse_price_text(raw) for raw in raw_candidates) if value is not None]
    if prices:
        return ShopeeResult(
            status="ok",
            classification="loaded_with_price_candidates",
            price=prices[0],
            final_url=final_url,
            response_status=response_status,
            price_candidates=prices[:20],
            price_candidates_sample=raw_candidates[:20],
        )

    return ShopeeResult(
        status="selector_failed" if selector else "price_changed",
        classification="loaded_without_price_candidates",
        final_url=final_url,
        response_status=response_status,
    )


def verify_price_in_text(
    body_text: str,
    price: int,
    final_url: str | None = None,
    response_status: int | None = None,
) -> ShopeeResult:
    status = classify_loaded_content(final_url or "", body_text, body_text)
    raw_candidates = price_strings(body_text)
    prices = [value for value in (parse_price_text(raw) for raw in raw_candidates) if value is not None]
    if status != "loaded":
        return ShopeeResult(
            status=status,
            classification=status,
            final_url=final_url,
            response_status=response_status,
            price_candidates=prices[:20],
            price_candidates_sample=raw_candidates[:20],
        )

    match_count = count_price_matches(body_text, price)
    if match_count == 0:
        return ShopeeResult(
            status="price_changed",
            classification="loaded_with_price_candidates" if prices else "loaded_without_price_candidates",
            passed=False,
            match_count=0,
            final_url=final_url,
            response_status=response_status,
            price_candidates=prices[:20],
            price_candidates_sample=raw_candidates[:20],
        )

    return ShopeeResult(
        status="ok",
        classification="loaded_with_price_candidates",
        passed=match_count == 1,
        match_count=match_count,
        final_url=final_url,
        response_status=response_status,
        price_candidates=prices[:20],
        price_candidates_sample=raw_candidates[:20],
    )


@dataclass
class LoadedPage:
    status: str
    html: str | None = None
    body_text: str | None = None
    final_url: str | None = None
    response_status: int | None = None
    error: str | None = None
    artifact_path: str | None = None
    price_candidates: list[int] = field(default_factory=list)
    price_candidates_sample: list[str] = field(default_factory=list)
    product_link_count: int = 0
    product_cards: list[dict[str, Any]] = field(default_factory=list)


def result_from_loaded_page(page_result: LoadedPage) -> ShopeeResult:
    return ShopeeResult(
        status=page_result.status,
        classification=page_result.status,
        final_url=page_result.final_url,
        response_status=page_result.response_status,
        error=page_result.error,
        artifact_path=page_result.artifact_path,
        price_candidates=page_result.price_candidates,
        price_candidates_sample=page_result.price_candidates_sample,
        product_link_count=page_result.product_link_count,
        product_cards=page_result.product_cards,
    )


def load_shopee_page(url: str) -> LoadedPage:
    previous_env = apply_true_cloak_env()
    context = None
    try:
        profile_dir = Path(env_value("SHOPEE_CLOAK_PROFILE_DIR", DEFAULT_PROFILE_DIR))
        profile_dir.mkdir(parents=True, exist_ok=True)
        context = launch_persistent_context(
            profile_dir,
            headless=env_bool("SHOPEE_CLOAK_HEADLESS", False),
            humanize=True,
            human_preset="careful",
            locale="vi-VN",
            timezone="Asia/Ho_Chi_Minh",
            viewport=None,
        )
        page = context.new_page()
        response = page.goto(
            url,
            timeout=env_int("SHOPEE_CLOAK_TIMEOUT_MS", 60000),
            wait_until=env_value("SHOPEE_CLOAK_WAIT_UNTIL", "domcontentloaded"),
        )
        time.sleep(env_int("SHOPEE_CLOAK_SETTLE_MS", 8000) / 1000)
        final_url = page.url
        html = ""
        body_text = ""
        product_link_count = 0
        product_cards: list[dict[str, Any]] = []
        status = "unknown"
        retries = env_int("SHOPEE_CLOAK_CONTENT_RETRIES", 2)
        for attempt in range(retries + 1):
            html = page.content()
            body_locator = page.locator("body")
            body_text = body_locator.inner_text(timeout=5000) if body_locator.count() else ""
            product_cards = extract_product_cards_on_page(page)
            product_link_count = len(product_cards) or count_product_links_on_page(page)
            status = classify_loaded_content(final_url, body_text, html, product_link_count)
            if (
                status in {"session_expired", "captcha_required", "access_blocked"}
                or (status == "loaded" and product_cards)
                or (status == "loaded" and product_link_count and attempt >= 1)
            ):
                break
            if attempt < retries:
                try:
                    page.evaluate("window.scrollBy(0, Math.floor(window.innerHeight * 0.8))")
                except Exception:
                    pass
                time.sleep(env_int("SHOPEE_CLOAK_RETRY_SETTLE_MS", 3000) / 1000)
        raw_candidates = price_strings(body_text)
        prices = [value for value in (parse_price_text(raw) for raw in raw_candidates) if value is not None]
        artifact_path = save_provider_artifact(
            requested_url=url,
            final_url=final_url,
            response_status=response.status if response else None,
            status=status,
            body_text=body_text,
            product_cards=product_cards,
            price_candidates=prices,
            error=None,
        )
        return LoadedPage(
            status=status,
            html=html,
            body_text=body_text,
            final_url=final_url,
            response_status=response.status if response else None,
            artifact_path=artifact_path,
            price_candidates=prices[:20],
            price_candidates_sample=raw_candidates[:20],
            product_link_count=product_link_count,
            product_cards=product_cards[:20],
        )
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        status = classify_error(error)
        artifact_path = save_provider_artifact(
            requested_url=url,
            final_url=None,
            response_status=None,
            status=status,
            body_text="",
            product_cards=[],
            price_candidates=[],
            error=error,
        )
        return LoadedPage(status=status, error=error, artifact_path=artifact_path)
    finally:
        try:
            if context is not None:
                context.close()
        finally:
            restore_env(previous_env)


def classify_loaded_content(final_url: str, body_text: str, html: str, product_link_count: int | None = None) -> str:
    combined = " ".join([final_url, body_text[:2000]]).lower()
    if "/buyer/login" in combined or "/user/account/login" in combined:
        return "session_expired"
    if "/verify/captcha" in combined or "captcha" in combined:
        return "captcha_required"
    if "/verify/traffic" in combined or "/verify/error" in combined or "page unavailable" in combined:
        return "access_blocked"

    raw_prices = price_strings(body_text)
    if product_link_count is None:
        product_link_count = count_product_links(html)
    if len(body_text) < 500 and not raw_prices and product_link_count == 0:
        return "thin_page"
    if raw_prices or product_link_count > 0:
        return "loaded"
    return "selector_failed"


def classify_error(error: str) -> str:
    lowered = error.lower()
    if "timeout" in lowered:
        return "timeout"
    if "winerror 10013" in lowered or "forbidden by its access permissions" in lowered:
        return "environment_network_blocked"
    return "unknown"


def price_strings(text: str) -> list[str]:
    return PRICE_RE.findall(text or "")


def visible_text_from_soup(soup: BeautifulSoup) -> str:
    for hidden in soup(["script", "style", "noscript"]):
        hidden.decompose()
    target = soup.body if soup.body else soup
    return target.get_text(separator=" ", strip=True)


def parse_price_text(text: str) -> int | None:
    match = PRICE_RE.search(text or "")
    if not match:
        return None
    digits = re.sub(r"\D", "", match.group(0))
    return int(digits) if digits else None


def count_price_matches(text: str, price: int) -> int:
    price_str = str(price)
    formatted_dot = f"{price:,}".replace(",", ".")
    formatted_comma = f"{price:,}"
    patterns = [
        r"(?<!\d)" + re.escape(formatted_dot) + r"(?!\d)",
        r"(?<!\d)" + re.escape(formatted_comma) + r"(?!\d)",
        r"(?<!\d)" + re.escape(price_str) + r"(?!\d)",
    ]
    counts = [len(re.findall(pattern, text or "")) for pattern in patterns]
    non_zero = [count for count in counts if count > 0]
    return min(non_zero) if non_zero else 0


def count_product_links(html: str) -> int:
    soup = BeautifulSoup(html or "", "html.parser")
    links = {
        item.get("href")
        for item in soup.find_all("a", href=True)
        if "-i." in item.get("href", "") or "/product/" in item.get("href", "") or "/products/" in item.get("href", "")
    }
    return len(links)


def count_product_links_on_page(page: Any) -> int:
    try:
        return int(
            page.locator("a").evaluate_all(
                """els => new Set(els.map(a => a.href).filter(h => h && (h.includes('-i.') || h.includes('/product/') || h.includes('/products/')))).size"""
            )
        )
    except Exception:
        return 0


def extract_product_cards_on_page(page: Any) -> list[dict[str, Any]]:
    try:
        raw_cards = page.locator("a").evaluate_all(
            """
            els => {
              const productHref = h => h && (h.includes('-i.') || h.includes('/product/') || h.includes('/products/'));
              const priceRe = /(?:₫|đ|VND)?\\s*\\d{1,3}(?:[.,]\\d{3})+(?:\\s*(?:₫|đ|VND))?/i;
              const seen = new Set();
              const cards = [];
              for (const anchor of els) {
                const href = anchor.href || '';
                if (!productHref(href) || seen.has(href)) continue;
                seen.add(href);
                let node = anchor;
                let best = anchor;
                for (let depth = 0; node && depth < 8; depth += 1, node = node.parentElement) {
                  const text = (node.innerText || '').trim();
                  if (text && priceRe.test(text) && text.length < 2500) {
                    best = node;
                    break;
                  }
                }
                cards.push({
                  href,
                  anchorText: (anchor.innerText || '').trim(),
                  text: (best.innerText || anchor.innerText || '').trim()
                });
              }
              return cards.slice(0, 80);
            }
            """
        )
    except Exception:
        return []

    cards = [normalize_product_card(card, index) for index, card in enumerate(raw_cards or [])]
    return [card for card in cards if card.get("href")]


def normalize_product_card(card: dict[str, Any], index: int) -> dict[str, Any]:
    text = clean_space(card.get("text") or card.get("anchorText") or "")
    anchor_text = clean_space(card.get("anchorText") or "")
    price_text = first_price_string(text)
    title = infer_product_title(text, anchor_text)
    href = card.get("href")
    return {
        "rank": index + 1,
        "href": href,
        "product_key": product_key_from_href(href),
        "title": title,
        "price": parse_price_text(price_text or ""),
        "price_text": price_text,
        "is_ad": is_ad_card(text),
        "text_excerpt": text[:500],
    }


def dedupe_product_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for card in cards:
        key = str(card.get("product_key") or product_key_from_href(card.get("href")) or card.get("href") or "")
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        unique.append(card)
    return unique


def product_key_from_href(href: str | None) -> str | None:
    if not href:
        return None
    parsed = urlparse(href)
    path = parsed.path or href
    match = re.search(r"(?:^|-)i\.(\d+)\.(\d+)", path)
    if match:
        return f"{match.group(1)}.{match.group(2)}"
    match = re.search(r"/(?:product|products)/(\d+)/(\d+)", path)
    if match:
        return f"{match.group(1)}.{match.group(2)}"
    return parsed._replace(query="", fragment="").geturl()


def first_preferred_card(cards: list[dict[str, Any]], target_url: str | None = None) -> dict[str, Any] | None:
    if not cards:
        return None

    terms = search_terms_from_url(target_url)
    if terms:
        scored = [
            (
                score_product_card(card, terms),
                0 if not card.get("is_ad") else -1,
                -(int(card.get("rank") or 0)),
                card,
            )
            for card in cards
        ]
        best = max(scored, key=lambda item: item[:3])
        if best[0] > 0:
            return best[3]

    for card in cards:
        if not card.get("is_ad"):
            return card
    return cards[0]


def search_terms_from_url(url: str | None) -> list[str]:
    if not url:
        return []
    query = parse_qs(urlparse(url).query)
    raw = " ".join(query.get("keyword", []) or query.get("q", []))
    normalized = normalize_for_match(raw)
    return [term for term in normalized.split() if len(term) >= 2]


def score_product_card(card: dict[str, Any], terms: list[str]) -> int:
    haystack = normalize_for_match(" ".join([str(card.get("title") or ""), str(card.get("text_excerpt") or "")]))
    return sum(1 for term in terms if term in haystack)


def normalize_for_match(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    asciiish = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^0-9a-zA-Z]+", " ", asciiish).lower().strip()


def infer_product_title(text: str, anchor_text: str) -> str | None:
    candidates = split_meaningful_lines(anchor_text) or split_meaningful_lines(text)
    for line in candidates:
        if is_title_line(line):
            return line
    return candidates[0] if candidates else None


def split_meaningful_lines(text: str) -> list[str]:
    return [line.strip() for line in re.split(r"[\r\n]+", text or "") if line.strip()]


def is_title_line(line: str) -> bool:
    lowered = line.lower()
    if len(line) < 8:
        return False
    if PRICE_RE.search(line):
        return False
    skip_markers = [
        "tìm sản phẩm tương tự",
        "đã bán",
        "followers",
        "xem shop",
        "thành phố",
        "hà nội",
        "hồ chí minh",
        "ad",
    ]
    if any(marker in lowered for marker in skip_markers):
        return False
    if re.fullmatch(r"[-+]?\d+(?:[.,]\d+)?%?", line):
        return False
    return True


def is_ad_card(text: str) -> bool:
    lines = [line.lower() for line in split_meaningful_lines(text)]
    return any(line == "ad" or line.startswith("ad ") for line in lines)


def first_price_string(text: str) -> str | None:
    match = PRICE_RE.search(text or "")
    return match.group(0) if match else None


def clean_space(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text or "").strip()


def save_provider_artifact(
    requested_url: str,
    final_url: str | None,
    response_status: int | None,
    status: str,
    body_text: str,
    product_cards: list[dict[str, Any]],
    price_candidates: list[int],
    error: str | None,
) -> str | None:
    if not env_bool("SHOPEE_PROVIDER_ARTIFACTS", True):
        return None

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    out_dir = Path(env_value("SHOPEE_PROVIDER_ARTIFACT_DIR", DEFAULT_ARTIFACT_DIR)) / run_id
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        artifact = {
            "schema_version": 1,
            "provider": PROVIDER,
            "strategy": STRATEGY,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "requested_url": requested_url,
            "final_url": final_url,
            "response_status": response_status,
            "status": status,
            "classification": status,
            "error": error,
            "body_text_len": len(body_text or ""),
            "body_excerpt": (body_text or "")[:3000],
            "price_candidate_count": len(price_candidates),
            "price_candidates_sample": price_candidates[:20],
            "product_link_count": len(product_cards),
            "product_cards_sample": product_cards[:20],
        }
        artifact_path = out_dir / "artifact.json"
        artifact_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(artifact_path)
    except Exception:
        return None


def http_status_for(result: ShopeeResult, operation: str) -> int:
    if result.status == "ok":
        return 200
    if operation == "verify" and result.status == "price_changed":
        return 200
    if result.status in {"session_expired", "captcha_required", "access_blocked"}:
        return 409
    if result.status == "timeout":
        return 504
    if result.status == "environment_network_blocked":
        return 503
    if result.status in {"thin_page", "selector_failed", "price_changed"}:
        return 404
    return 500


def env_value(name: str, default: str) -> str:
    return os.environ.get(name) or default


def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, ""))
    except ValueError:
        return default


def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def apply_true_cloak_env() -> dict[str, str | None]:
    previous = {
        "CLOAKBROWSER_BINARY_PATH": os.environ.get("CLOAKBROWSER_BINARY_PATH"),
        "CLOAKBROWSER_CACHE_DIR": os.environ.get("CLOAKBROWSER_CACHE_DIR"),
        "CLOAKBROWSER_AUTO_UPDATE": os.environ.get("CLOAKBROWSER_AUTO_UPDATE"),
    }
    os.environ.pop("CLOAKBROWSER_BINARY_PATH", None)
    os.environ["CLOAKBROWSER_CACHE_DIR"] = env_value("SHOPEE_CLOAK_CACHE_DIR", DEFAULT_CACHE_DIR)
    os.environ["CLOAKBROWSER_AUTO_UPDATE"] = "false"
    return previous


def restore_env(previous: dict[str, str | None]) -> None:
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
