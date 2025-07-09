import os
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# --- BẮT ĐẦU PHẦN THAY ĐỔI ---
# Không cần thư viện webdriver_manager nữa
# from webdriver_manager.chrome import ChromeDriverManager
# --- KẾT THÚC PHẦN THAY ĐỔI ---

# --- Cấu hình ---
app = Flask(__name__)
CORS(app)

# --- BẮT ĐẦU PHẦN THAY ĐỔI ---
def get_chrome_driver():
    """Khởi tạo và trả về một WebDriver Chrome sử dụng Selenium Manager tích hợp."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Selenium 4.6.0+ sẽ tự động quản lý driver khi Service() được gọi mà không có tham số
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver
# --- KẾT THÚC PHẦN THAY ĐỔI ---


def extract_price(url: str, selector: str):
    """Quét một URL với một bộ chọn CSS cho trước và trích xuất giá."""
    driver = None
    try:
        driver = get_chrome_driver()
        driver.get(url)
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        
        price_text = driver.find_element(By.CSS_SELECTOR, selector).text
        
        # Regex cải tiến để xử lý nhiều định dạng khác nhau
        numbers = re.findall(r'\d+', price_text.replace('.', '').replace(',', ''))
        if numbers:
            return int("".join(numbers))
        else:
            return None
            
    except Exception as e:
        print(f"Lỗi khi quét {url} với bộ chọn '{selector}': {e}")
        return None
    finally:
        if driver:
            driver.quit()

def verify_price_uniquely(driver, price: int):
    """
    Xác minh xem một mức giá cho trước có xuất hiện duy nhất trong văn bản của trang hay không.
    Hàm này kiểm tra nhiều định dạng và trả về số lần xuất hiện tối thiểu khác không.
    """
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # Xóa thẻ script và style để tránh khớp giá trong mã nguồn
        for script in soup(["script", "style"]):
            script.decompose()
        body_text = soup.body.get_text(separator=' ', strip=True)

        # Tạo các định dạng chuỗi khác nhau cho giá
        price_str = str(price)
        # Định dạng có dấu chấm ngăn cách hàng nghìn: 132.000
        formatted_price_dot = f"{price:,}".replace(",", ".")
        # Định dạng có dấu phẩy ngăn cách hàng nghìn: 132,000
        formatted_price_comma = f"{price:,}"

        # Xác định các mẫu với tên để rõ ràng.
        patterns_to_check = {
            "dot_separator": r'\b' + re.escape(formatted_price_dot) + r'\b',
            "comma_separator": r'\b' + re.escape(formatted_price_comma) + r'\b',
            "no_separator": r'\b' + re.escape(price_str) + r'\b'
        }
        
        counts = {}
        print("--- Đang xác minh giá bằng văn bản ---")
        for name, pattern in patterns_to_check.items():
            matches = re.findall(pattern, body_text)
            counts[name] = len(matches)
            print(f"DEBUG: Mẫu '{name}' ('{pattern}') được tìm thấy {len(matches)} lần.")

        non_zero_counts = [c for c in counts.values() if c > 0]
        
        if not non_zero_counts:
            print("Kết quả: Không tìm thấy giá ở bất kỳ định dạng nào.")
            return {"passed": False, "min_count": 0}

        min_count = min(non_zero_counts)
        passed = (min_count == 1)
        
        print(f"Kết quả: Trường hợp tốt nhất có {min_count} lần xuất hiện. Thành công: {passed}")
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

    print(f"Đang kiểm tra giá cho URL: {url} với bộ chọn: '{selector}'")
    
    price = extract_price(url, selector)
    
    if price is not None:
        return jsonify({"price": price})
    else:
        return jsonify({"error": "Không thể trích xuất giá.", "price": None}), 404

@app.route('/api/verify-price-by-text', methods=['POST'])
def handle_verify_price():
    """
    API dự phòng để xác minh một mức giá bằng cách tìm kiếm biểu diễn văn bản của nó
    một cách duy nhất trong phần thân của trang.
    """
    data = request.get_json()
    if not data or 'url' not in data or 'price' not in data:
        return jsonify({"error": "Thiếu URL hoặc giá để xác minh"}), 400

    url = data['url']
    price_to_verify = data['price']
    
    driver = None
    try:
        driver = get_chrome_driver()
        driver.get(url)
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        
        verification_result = verify_price_uniquely(driver, price_to_verify)
        
        return jsonify({
            "found_uniquely": verification_result["passed"],
            "match_count": verification_result["min_count"]
        })
        
    except Exception as e:
        print(f"Lỗi khi xác minh giá bằng văn bản cho {url}: {e}")
        return jsonify({"error": "Thất bại khi xác minh giá bằng văn bản", "found_uniquely": False, "match_count": -1}), 500
    finally:
        if driver:
            driver.quit()

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
