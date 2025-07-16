import os
import re
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from bs4 import BeautifulSoup

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
CORS(app)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

# ========== SELENIUM ==========

def get_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--remote-debugging-port=9222")
    service = Service()
    return webdriver.Chrome(service=service, options=chrome_options)

def extract_price_selenium(url: str, selector: str):
    driver = None
    try:
        driver = get_chrome_driver()
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        price_text = driver.find_element(By.CSS_SELECTOR, selector).text
        numbers = re.findall(r'\d+', price_text.replace('.', '').replace(',', ''))
        if numbers:
            return int("".join(numbers))
    except Exception as e:
        print(f"[Selenium] Lỗi trích xuất {url}: {e}")
    finally:
        if driver:
            driver.quit()
    return None

def verify_price_selenium(url: str, price: int):
    driver = None
    try:
        driver = get_chrome_driver()
        driver.get(url)
        WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        return _verify_price_from_soup(soup, price)
    except Exception as e:
        print(f"[Selenium] Lỗi xác minh {url}: {e}")
        if driver:
            driver.quit()
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
        "dot_separator": r'\b' + re.escape(formatted_price_dot) + r'\b',
        "comma_separator": r'\b' + re.escape(formatted_price_comma) + r'\b',
        "no_separator": r'\b' + re.escape(price_str) + r'\b'
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
    mode = data.get('mode', 'selenium').lower()  # ✅ Mặc định selenium

    if not url or not selector:
        return jsonify({"error": "Thiếu URL hoặc bộ chọn"}), 400

    print(f"[Check Price] URL: {url}, Selector: {selector}, Mode: {mode}")

    if mode == 'bs4':
        price = extract_price_bs4(url, selector)
    else:
        price = extract_price_selenium(url, selector)

    if price is not None:
        return jsonify({"price": price})
    return jsonify({"error": "Không thể trích xuất giá.", "price": None}), 404

@app.route('/api/verify-price-by-text', methods=['POST'])
def handle_verify_price():
    data = request.get_json()
    url = data.get('url')
    price = data.get('price')
    mode = data.get('mode', 'selenium').lower()  # ✅ Mặc định selenium

    if not url or price is None:
        return jsonify({"error": "Thiếu URL hoặc giá để xác minh"}), 400

    print(f"[Verify Price] URL: {url}, Price: {price}, Mode: {mode}")

    if mode == 'bs4':
        result = verify_price_bs4(url, price)
    else:
        result = verify_price_selenium(url, price)

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
