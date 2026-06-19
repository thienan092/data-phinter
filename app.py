import os
import platform
import sys

DEFAULT_MODE = "cloak"
import re
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from bs4 import BeautifulSoup
from providers.shopee import (
    extract_price_shopee,
    http_status_for as shopee_http_status_for,
    is_shopee_url,
    verify_price_shopee,
)

# CloakBrowser imports
from cloakbrowser import launch

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

app = Flask(__name__)
CORS(app)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

# ========== CLOAKBROWSER ==========

def get_cloak_browser():
    proxy = os.environ.get("CLOAK_PROXY")
    proxy_dict = {"server": proxy} if proxy else None
    # Default to headless=True as requested, with humanize=True for stealth
    return launch(headless=True, humanize=True, proxy=proxy_dict)

def extract_price_cloak(url: str, selector: str):
    browser = None
    try:
        browser = get_cloak_browser()
        page = browser.new_page()
        page.goto(url, timeout=30000)
        page.wait_for_selector(selector, timeout=20000)
        price_text = page.locator(selector).first.inner_text()
        numbers = re.findall(r'\d+', price_text.replace('.', '').replace(',', ''))
        if numbers:
            return int("".join(numbers))
    except Exception as e:
        print(f"[Cloak] Lỗi trích xuất {url}: {e}")
    finally:
        if browser:
            browser.close()
    return None

def verify_price_cloak(url: str, price: int):
    browser = None
    try:
        browser = get_cloak_browser()
        page = browser.new_page()
        page.goto(url, timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        browser.close()
        return _verify_price_from_soup(soup, price)
    except Exception as e:
        print(f"[Cloak] Lỗi xác minh {url}: {e}")
        if browser:
            browser.close()
        return {"passed": False, "min_count": -1}

# ========== BS4 ==========

def extract_price_bs4(url: str, selector: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        price_element = soup.select_one(selector)
        if price_element:
            price_text = price_element.get_text()
            numbers = re.findall(r'\d+', price_text.replace('.', '').replace(',', ''))
            if numbers:
                return int("".join(numbers))
    except Exception as e:
        print(f"[BS4] Lỗi trích xuất {url}: {e}")
    return None

def verify_price_bs4(url: str, price: int):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return _verify_price_from_soup(soup, price)
    except Exception as e:
        print(f"[BS4] Lỗi xác minh {url}: {e}")
        return {"passed": False, "min_count": -1}

# ========== CHUNG ==========
def _verify_price_from_soup(soup, price: int):
    for script in soup(["script", "style"]):
        script.decompose()
    body_text = soup.body.get_text(separator=' ', strip=True)
    price_str = str(price)
    formatted_price_dot = f"{price:,}".replace(",", ".")
    formatted_price_comma = f"{price:,}"

    patterns_to_check = {
        "dot_separator": r'(?<!\d)' + re.escape(formatted_price_dot) + r'(?!\d)',
        "comma_separator": r'(?<!\d)' + re.escape(formatted_price_comma) + r'(?!\d)',
        "no_separator": r'(?<!\d)' + re.escape(price_str) + r'(?!\d)'
    }

    counts = {}
    for name, pattern in patterns_to_check.items():
        matches = re.findall(pattern, body_text)
        counts[name] = len(matches)
        print(f"[Check] Pattern '{name}' → {counts[name]} matches")

    non_zero_counts = [c for c in counts.values() if c > 0]
    if not non_zero_counts:
        return {"passed": False, "min_count": 0}
    min_count = min(non_zero_counts)
    return {"passed": min_count == 1, "min_count": min_count}

# ========== API ==========

@app.route('/api/check-price', methods=['POST'])
def handle_check_price():
    data = request.get_json()
    url = data.get('url')
    selector = data.get('selector')
    mode = data.get('mode', DEFAULT_MODE).lower()  # ✅ Mặc định cloak

    if not url or (not selector and not (mode != 'bs4' and is_shopee_url(url))):
        return jsonify({"error": "Thiếu URL hoặc bộ chọn"}), 400

    print(f"[Check Price] URL: {url}, Selector: {selector}, Mode: {mode}")

    if mode != 'bs4' and is_shopee_url(url):
        result = extract_price_shopee(url, selector)
        response = result.to_response()
        if result.price is not None:
            return jsonify(response), shopee_http_status_for(result, "extract")
        response["error"] = response.get("error") or f"Shopee extraction status: {result.status}"
        return jsonify(response), shopee_http_status_for(result, "extract")

    if mode == 'bs4':
        price = extract_price_bs4(url, selector)
    else:
        price = extract_price_cloak(url, selector)

    if price is not None:
        return jsonify({"price": price})
    return jsonify({"error": "Không thể trích xuất giá.", "price": None}), 404

@app.route('/api/verify-price-by-text', methods=['POST'])
def handle_verify_price():
    data = request.get_json()
    url = data.get('url')
    price = data.get('price')
    mode = data.get('mode', DEFAULT_MODE).lower()  # ✅ Mặc định cloak

    if not url or price is None:
        return jsonify({"error": "Thiếu URL hoặc giá để xác minh"}), 400

    try:
        price = int(str(price).replace(".", "").replace(",", ""))
    except ValueError:
        return jsonify({"error": "Gia khong hop le"}), 400

    print(f"[Verify Price] URL: {url}, Price: {price}, Mode: {mode}")

    if mode != 'bs4' and is_shopee_url(url):
        result = verify_price_shopee(url, price)
        response = result.to_response()
        response.update({
            "found_uniquely": result.passed,
            "match_count": result.match_count,
        })
        if result.status not in {"ok", "price_changed"}:
            response["error"] = response.get("error") or f"Shopee verification status: {result.status}"
        return jsonify(response), shopee_http_status_for(result, "verify")

    if mode == 'bs4':
        result = verify_price_bs4(url, price)
    else:
        result = verify_price_cloak(url, price)

    return jsonify({
        "found_uniquely": result["passed"],
        "match_count": result["min_count"]
    })

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)
    
@app.route('/api/default-mode', methods=['GET'])
def get_default_mode():
    return jsonify({"default_mode": DEFAULT_MODE})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
