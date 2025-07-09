import os
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests

# --- Cấu hình ---
app = Flask(__name__)
CORS(app)

# Headers để giả mạo một trình duyệt thông thường
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

def extract_price(url: str, selector: str):
    """
    Quét một URL bằng requests, phân tích bằng BeautifulSoup và trích xuất giá.
    LƯU Ý: Sẽ không hoạt động nếu giá được tải bằng JavaScript.
    """
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
        
        return None
            
    except requests.exceptions.RequestException as e:
        print(f"Lỗi mạng khi truy cập {url}: {e}")
        return None
    except Exception as e:
        print(f"Lỗi khi quét {url} với bộ chọn '{selector}': {e}")
        return None

def verify_price_uniquely(url: str, price: int):
    """
    Xác minh xem một mức giá cho trước có xuất hiện duy nhất trong văn bản của trang hay không.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
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
        print("--- Đang xác minh giá bằng văn bản (requests) ---")
        for name, pattern in patterns_to_check.items():
            matches = re.findall(pattern, body_text)
            counts[name] = len(matches)
            print(f"DEBUG: Mẫu '{name}' ('{pattern}') được tìm thấy {len(matches)} lần.")

        non_zero_counts = [c for c in counts.values() if c > 0]
        
        if not non_zero_counts:
            return {"passed": False, "min_count": 0}

        min_count = min(non_zero_counts)
        passed = (min_count == 1)
        
        return {"passed": passed, "min_count": min_count}
        
    except Exception as e:
        print(f"Lỗi trong quá trình xác minh bằng văn bản: {e}")
        return {"passed": False, "min_count": -1}

@app.route('/api/check-price', methods=['POST'])
def handle_check_price():
    data = request.get_json()
    if not data or 'url' not in data or 'selector' not in data:
        return jsonify({"error": "Thiếu URL hoặc bộ chọn"}), 400

    url = data['url']
    selector = data['selector']

    print(f"Đang kiểm tra giá cho URL: {url} với bộ chọn đã chuẩn hóa: '{selector}'")
    
    price = extract_price(url, selector)
    
    if price is not None:
        return jsonify({"price": price})
    else:
        return jsonify({"error": "Không thể trích xuất giá.", "price": None}), 404

@app.route('/api/verify-price-by-text', methods=['POST'])
def handle_verify_price():
    data = request.get_json()
    if not data or 'url' not in data or 'price' not in data:
        return jsonify({"error": "Thiếu URL hoặc giá để xác minh"}), 400

    url = data['url']
    price_to_verify = data['price']
    
    try:
        verification_result = verify_price_uniquely(url, price_to_verify)
        
        return jsonify({
            "found_uniquely": verification_result["passed"],
            "match_count": verification_result["min_count"]
        })
        
    except Exception as e:
        print(f"Lỗi khi xác minh giá bằng văn bản cho {url}: {e}")
        return jsonify({"error": "Thất bại khi xác minh giá bằng văn bản", "found_uniquely": False, "match_count": -1}), 500

@app.route('/')
def serve_index():
    """Phục vụ file web_page.html làm trang chính."""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Phục vụ các file tĩnh khác nếu cần (ví dụ: CSS, JS riêng)."""
    return send_from_directory('.', path)

if __name__ == '__main__':
    # Sửa lại lệnh app.run để phù hợp với production hơn
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
