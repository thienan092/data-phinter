# Hệ Thống Phân Tích Thị Trường Cà Phê (Data Phin-ter)
**Hệ thống Phân tích Thị trường Cà phê (Data Phin-ter)** là một ứng dụng web tiên tiến, được thiết kế như một công cụ phân tích nhỏ gọn, dễ dàng **tùy chỉnh thông qua mô hình ngôn ngữ lớn Gemini Pro 2.5**. Dự án này thể hiện cách tận dụng tính năng **Deep Research của Gemini để sinh dữ liệu chất lượng cao** cho phân tích, đồng thời tích hợp cơ chế **kiểm chứng dữ liệu tại nguồn** nhằm loại bỏ các kết quả bị ảnh hưởng bởi hiện tượng "hallucination". Hơn nữa, toàn bộ giao diện người dùng cũng được hỗ trợ đáng kể (ước tính hơn 50%) từ Gemini thông qua quy trình "prompting", giúp rút ngắn đáng kể thời gian phát triển và có **tính tương thích cao với các loại dữ liệu thị trường** khác ngoài cà phê.

---

## Tính năng chính

* **Quản lý Dữ liệu Tập trung (SST):** Giao diện lưới dữ liệu (AG Grid) cung cấp khả năng **xem, lọc, và quản lý tập trung toàn bộ dữ liệu sản phẩm** từ một nguồn duy nhất, đảm bảo tính nhất quán và chính xác. Hỗ trợ nhập liệu dễ dàng từ file CSV.
* **Cập nhật Giá Tự động:** Sử dụng Selenium để truy cập các URL sản phẩm và **tự động thu thập dữ liệu giá mới nhất**. Các tác vụ được quản lý trong một hàng đợi trực quan, cho phép người dùng **kiểm chứng dữ liệu tai nguồn, theo dõi tiến trình và xử lý các thay đổi về giá**.
* **Trực quan hóa Dữ liệu:** Tạo ra các biểu đồ tương tác (Chart.js) một cách tự động từ dữ liệu đã lọc, giúp người dùng **dễ dàng nắm bắt insight thị trường**, bao gồm:
    * Định vị giá trung bình của các thương hiệu.
    * Phân bổ chủng loại cà phê.
    * Bản đồ định vị thương hiệu (dựa trên giá và số lượng SKUs).
    * Phân tích hiệu quả ngưỡng Freeship.
* **Phân tích bằng AI:** Tích hợp giao diện chatbot, cho phép người dùng gửi câu hỏi bằng ngôn ngữ tự nhiên để nhận các **phân tích chuyên sâu và khuyến nghị chiến lược** từ AI, dựa trên các thống kê từ tập dữ liệu được hiển thị.
* **Tùy chỉnh Giao diện và Logic:** Cung cấp các tùy chọn linh hoạt để **ẩn/hiện các cột dữ liệu** và định nghĩa các khóa chống trùng lặp, cho phép người dùng **tùy chỉnh công cụ phù hợp với nhu cầu phân tích cụ thể** của họ.

---

## Bảo mật và Tin cậy

* **Quản lý Trình duyệt Tự động:** Ứng dụng sử dụng Selenium Manager (tích hợp trong Selenium 4.6.0+) để **tự động quản lý phiên bản trình duyệt**, loại bỏ hoàn toàn nhu cầu tải thủ công các file thực thi (như `chromedriver.exe`) và **đảm bảo hoạt động ổn định**.
* **Thư viện từ Nguồn Chính thức:** Tất cả các thư viện phụ thuộc được cài đặt từ Python Package Index (PyPI) thông qua file `requirements.txt`.
* **Lưu trữ API Key Phía Client:** Khóa API của Gemini được lưu trữ an toàn trong `sessionStorage` của trình duyệt. Điều này có nghĩa là khóa sẽ tự động bị xóa khi phiên làm việc kết thúc và **không bao giờ được lưu trữ trên bất kỳ máy chủ nào**, tuyệt đối bảo mật dữ liệu người dùng.
---

## Hướng dẫn Cài đặt Local

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

5.  **Chạy ứng dụng:**
    ```bash
    flask run
    ```

6.  **Truy cập ứng dụng:**
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

   * **Nhánh (Branch):** Chọn nhánh mà bạn muốn triển khai (thường là `main` hoặc `master`).

   * **Thư mục gốc (Root Directory):** Để trống nếu dự án của bạn nằm ở thư mục gốc của kho chứa.

   * **Môi trường (Runtime):** Chọn `"Python 3"`.

   * **Lệnh Build (Build Command):** `pip install -r requirements.txt`

   * **Lệnh Khởi động (Start Command):** `gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker app:app`
  
   * **Instance Type:** Cấu hình tối thiểu cho dự án là **Free**. 

   * **Kiểu Dịch vụ (Service Type):** Chọn `"Web Service"`.

   * **Khu vực (Region):** Chọn khu vực gần người dùng của bạn nhất (Singapore nếu bạn ở Việt Nam). 

6. **Tạo Web Service:** Nhấp vào `"Deploy Web Service"`. Render sẽ tự động bắt đầu quá trình triển khai, cài đặt các phụ thuộc và chạy ứng dụng của bạn. Bạn có thể theo dõi tiến trình trong nhật ký triển khai.

7. **Truy cập ứng dụng:** Sau khi triển khai thành công, Render sẽ cung cấp một URL (`https://coffee-market-analysis.onrender.com` trong trường hợp này) công khai cho ứng dụng của bạn.

---

## Giấy phép (License)

Dự án này được cấp phép dưới Giấy phép Apache 2.0.

Điều này có nghĩa là bạn được tự do sử dụng, sửa đổi và phân phối mã nguồn cho bất kỳ mục đích nào, kể cả mục đích thương mại, miễn là tuân thủ các điều kiện được nêu trong giấy phép. Để xem toàn bộ nội dung giấy phép, vui lòng đọc file `LICENSE`.