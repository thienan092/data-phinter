import sys
import os

# Import trực tiếp các hàm logic backend từ app.py (thay vì phải tương tác UI)
from app import verify_price_cloak, extract_price_cloak

def run_live_tests():
    print("="*60)
    print("BẮT ĐẦU KIỂM THỬ THỰC TẾ CLOAKBROWSER (BACKEND CALLBACK)")
    print("="*60)
    print("Lưu ý: Bạn có thể thay đổi URL bên dưới thành một URL sản phẩm đang sống (Live URL) để thấy trình duyệt hoạt động.")
    
    test_cases = [
        {
            "id": "Shopee",
            "url": "https://shopee.vn/Ca-ngu-ngam-dau-thuc-vat-Sea-Crown-170g-i.12345.67890", # Đổi URL này thành URL thật
            "price": 35500,
            "selector": ".pdt-price"
        },
        {
            "id": "Lazada",
            "url": "https://www.lazada.vn/products/combo-3-hop-ca-ngu-ngam-dau-huong-duong-dongwon-100g-i12345.html", # Đổi URL này thành URL thật
            "price": 115000,
            "selector": ".pdp-price"
        }
    ]

    for case in test_cases:
        print(f"\n[{case['id']}] Đang truy cập URL: {case['url']}")
        
        # 1. Gọi thẳng hàm Verify (Mô phỏng hành động người dùng bấm nút Check)
        print(f" ---> Đang chạy logic xác minh giá ({case['price']}) trong Background...")
        verify_result = verify_price_cloak(case['url'], case['price'])
        print(f" ---> Kết quả Verify: {verify_result}")
        
        # 2. Gọi thẳng hàm Extract (Mô phỏng hành động hệ thống tự sửa sai nếu giá lệch)
        print(f" ---> Đang chạy logic trích xuất lại giá bằng selector '{case['selector']}'...")
        extract_result = extract_price_cloak(case['url'], case['selector'])
        print(f" ---> Kết quả Extract: {extract_result}")

if __name__ == "__main__":
    # Đảm bảo bạn đã cài đặt đủ thư viện: pip install cloakbrowser playwright beautifulsoup4
    run_live_tests()
