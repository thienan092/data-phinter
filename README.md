# Data Phin-ter
**Hệ thống hỗ trợ thu thập và kiểm chứng dữ liệu "tìm kiếm sâu" (Data Phin-ter)** là một ứng dụng web, được thiết kế như một công cụ phân tích nhỏ gọn, dễ dàng **tùy chỉnh thông qua mô hình ngôn ngữ lớn Gemini của Google**. 

Dự án này cung cấp các chức năng cơ bản nhất để có thể tận dụng tính năng **Deep Research của Gemini như là một công cụ sinh dữ liệu chất lượng cao** dùng cho việc quan sát thị trường trực tuyến, đồng thời tích hợp cơ chế **tự động hóa việc kiểm chứng dữ liệu tại nguồn trích dẫn** nhằm giám sát những sự thay đổi về giá sản phẩm và loại bỏ/chỉnh sửa các kết quả bị sai sót trong quá trình thu thập dữ liệu hoặc bị ảnh hưởng bởi hiện tượng "hallucination". 

Hơn nữa, toàn bộ mã nguồn và giao diện người dùng cũng được "làm phẳng" và nằm trong phạm vi hiểu của các chatbot (dưới 3k dòng lệnh), giúp nó có thể được điều chỉnh thông qua quy trình prompting để có thể **tương thích với các loại dữ liệu thị trường** khác ngoài cà phê.

---
<img width="1913" height="878" alt="image" src="https://github.com/user-attachments/assets/379bc4b7-0588-4c55-a6f7-8a7d5f4442f8" />

<img width="1912" height="870" alt="image" src="https://github.com/user-attachments/assets/64578f3b-bbd2-4dc0-9c3a-a21675df0e9f" />

<img width="1915" height="878" alt="image" src="https://github.com/user-attachments/assets/f19b46a0-d010-4cf4-971c-abca2020d2d0" />


---

## Tính năng chính

* **Cấu trúc file dữ liệu (.csv) đầu vào:** Xem `sample_data.csv`. 
* **Quản lý Dữ liệu Tập trung (SST):** Giao diện lưới dữ liệu (AG Grid) cung cấp khả năng **xem, lọc, và quản lý tập trung toàn bộ dữ liệu sản phẩm** từ một nguồn duy nhất, đảm bảo tính nhất quán và chính xác. Hỗ trợ nhập liệu dễ dàng từ file CSV.
* **Cập nhật Giá Tự động:** Sử dụng Selenium/BS4 để truy cập các URL sản phẩm và **tự động thu thập dữ liệu giá mới nhất**. Các tác vụ được quản lý trong một hàng đợi trực quan, cho phép người dùng **kiểm chứng dữ liệu tai nguồn, theo dõi tiến trình và xử lý các thay đổi về giá**.
* **Trực quan hóa Dữ liệu:** Tạo ra các biểu đồ tương tác (Chart.js) một cách tự động từ dữ liệu đã lọc, giúp người dùng **dễ dàng nắm bắt insight thị trường**, bao gồm:
    * Định vị giá trung bình của các thương hiệu.
    * Phân bổ chủng loại cà phê.
    * Bản đồ định vị thương hiệu (dựa trên giá và số lượng SKUs).
    * Phân tích hiệu quả ngưỡng Freeship.
* **Phân tích bằng AI:** Tích hợp giao diện chatbot, cho phép người dùng gửi câu hỏi bằng ngôn ngữ tự nhiên để nhận các **phân tích chuyên sâu và khuyến nghị chiến lược** từ AI, dựa trên các thống kê từ tập dữ liệu được hiển thị.
* **Tùy chỉnh Giao diện và Logic:** Cung cấp các tùy chọn linh hoạt để **ẩn/hiện các cột dữ liệu** và định nghĩa các khóa chống trùng lặp, cho phép người dùng **tùy chỉnh công cụ phù hợp với nhu cầu phân tích cụ thể** của họ.

***Lưu ý:*** *Những tính năng này được tích hợp nhằm mục đích hỗ trợ người sử dụng trong việc đánh giá chất lượng dữ liệu thông qua việc quan sát dữ liệu trực quan và hình dung được việc ứng dụng Trí tuệ nhân tạo (AI) vào giải quyết các bài toán kinh doanh.*

---

## Bảo mật và Tin cậy

* **Quản lý Trình duyệt Tự động:** Ứng dụng sử dụng thư viện Selenium Manager (bản stable) và BeautifulSoup4 (bản speed) của Python để **tự động quản lý phiên bản trình duyệt**, loại bỏ hoàn toàn nhu cầu tải thủ công các file thực thi (như `chromedriver.exe`) và **đảm bảo hoạt động ổn định**.
* **Thư viện từ Nguồn Chính thức:** Tất cả các thư viện phụ thuộc được cài đặt từ Python Package Index (PyPI) thông qua file `requirements.txt`.
* **Lưu trữ API Key Phía Client:** Khóa API của Gemini được lưu trữ an toàn trong `sessionStorage` của trình duyệt. Điều này có nghĩa là khóa sẽ tự động bị xóa khi phiên làm việc kết thúc và **không bao giờ được lưu trữ trên bất kỳ máy chủ nào**, tuyệt đối bảo mật dữ liệu người dùng.
---

## Hướng dẫn Cài đặt Local (Khuyến khích)

**Yêu cầu:**

* Python 3.9+
* Trình duyệt Google Chrome

**Các bước:**

1.  **Fork dự án**: Truy cập kho chứa GitHub của dự án này và nhấp vào nút **"Fork"** ở góc trên bên phải để tạo một bản sao của dự án về tài khoản GitHub của bạn.

2.  **Sao chép kho chứa code:**
    ```bash
    git clone <URL_REPOSITORY_CỦA_BẠN> # Thay thế bằng URL kho chứa của bạn
    cd <TEN_THU_MUC_DU_AN> # Thay thế bằng tên thư mục dự án sau khi clone
    ```

3.  **Tạo và kích hoạt môi trường ảo** để cô lập các thư viện của dự án:
    * Trên macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    * Trên Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

4.  **Cài đặt các thư viện phụ thuộc:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Chuyển đổi sang bản stable (khuyến khích):**
    Xóa file `app.py` và đổi tên file `sel_app.py` thành `app.py`

6.  **Chạy ứng dụng:**
    ```bash
    flask run
    ```

7.  **Truy cập ứng dụng:**
    Mở trình duyệt và truy cập địa chỉ: `http://127.0.0.1:5000`

---

## Triển khai (Deployment)

Dự án đã được cấu hình để triển khai trên Render thông qua file `render.yaml`. Cấu hình này bao gồm:

* Sử dụng `gunicorn` để chạy ứng dụng web production.

* Tự động cài đặt Google Chrome thông qua buildpack để phục vụ cho các tác vụ của Selenium.

Để triển khai dự án lên Render thông qua GitHub, hãy làm theo các bước sau:

1. **Đăng nhập vào Render:** Truy cập `https://render.com/` và đăng nhập bằng tài khoản GitHub của bạn.

2. **Tạo dự án mới:** Trên bảng điều khiển Render, nhấp vào `"+ New"` và chọn `"Web Service"`.

3. **Kết nối GitHub:** Render sẽ yêu cầu bạn kết nối tài khoản GitHub của mình. Cấp quyền truy cập cho kho chứa dự án này (hoặc tất cả các kho chứa).

4. **Chọn kho chứa:** Tìm và chọn kho chứa GitHub của dự án *data-phinter* của bạn.

5. **Cấu hình dịch vụ Web:**

   * **Tên (Name):** Đặt một tên dễ nhớ cho dịch vụ của bạn (ví dụ: `coffee-market-analysis`).
  
   * **Instance Type:** Cấu hình tối thiểu cho dự án là **Free**. 

   * **Kiểu Dịch vụ (Service Type):** Chọn `"Web Service"`.

   * **Khu vực (Region):** Chọn khu vực gần người dùng của bạn nhất (Singapore nếu bạn ở Việt Nam).
  
   * **Các trường khác vẫn giữ mặc định.**

6. **Tạo Web Service:** Nhấp vào `"Deploy Web Service"`. Render sẽ tự động bắt đầu quá trình triển khai, cài đặt các phụ thuộc và chạy ứng dụng của bạn. Bạn có thể theo dõi tiến trình trong nhật ký triển khai.

7. **Truy cập ứng dụng:** Sau khi triển khai thành công, Render sẽ cung cấp một URL (`https://coffee-market-analysis.onrender.com` trong trường hợp này) công khai cho ứng dụng của bạn.

---

## Giấy phép (License)

Dự án này được cấp phép dưới Giấy phép Apache 2.0.

Điều này có nghĩa là bạn được tự do sử dụng, sửa đổi và phân phối mã nguồn cho bất kỳ mục đích nào, kể cả mục đích thương mại, miễn là tuân thủ các điều kiện được nêu trong giấy phép. Để xem toàn bộ nội dung giấy phép, vui lòng đọc file [`LICENSE`](LICENSE).

## Hỗ trợ tác giả

🎉 Bạn thấy ứng dụng này hữu ích?

Hãy [mua cho tôi một ly cà phê](https://www.buymeacoffee.com/anlt) để tiếp thêm động lực phát triển ☕.

Mọi sự ủng hộ của bạn là nguồn cảm hứng rất lớn. Chân thành cảm ơn 💛
