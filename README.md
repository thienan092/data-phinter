# Data Phin-ter: Hệ thống hỗ trợ thu thập và kiểm chứng dữ liệu "tìm kiếm sâu"

---

## 🇻🇳 Tiếng Việt

**Data Phin-ter** là một ứng dụng web, được thiết kế như một công cụ phân tích nhỏ gọn, dễ dàng **tùy chỉnh thông qua mô hình ngôn ngữ lớn Gemini của Google**.

Dự án này cung cấp các chức năng cơ bản nhất để có thể tận dụng tính năng **Deep Research của Gemini như là một công cụ sinh dữ liệu chất lượng cao** dùng cho việc quan sát thị trường trực tuyến, đồng thời tích hợp cơ chế **tự động hóa việc kiểm chứng dữ liệu tại nguồn trích dẫn** nhằm giám sát những sự thay đổi về giá sản phẩm và loại bỏ/chỉnh sửa các kết quả bị sai sót trong quá trình thu thập dữ liệu hoặc bị ảnh hưởng bởi hiện tượng "hallucination".

Hơn nữa, toàn bộ mã nguồn và giao diện người dùng cũng được "làm phẳng" và nằm trong phạm vi hiểu của các chatbot (dưới 3k dòng lệnh), giúp nó có thể được điều chỉnh thông qua quy trình prompting để có thể **tương thích với các loại dữ liệu thị trường** khác ngoài cà phê.

---

## 🇬🇧 English

**Data Phin-ter (Deep Research Data Collection and Verification System)** is a web application designed as a compact analysis tool, easily **customizable via Google's Gemini large language model**.

This project provides the most basic functionalities to leverage Gemini's **Deep Research feature as a high-quality data generation tool** for online market observation, while integrating an **automated data verification mechanism at the citation source** to monitor product price changes and eliminate/correct erroneous results during data collection or those affected by "hallucination".

Furthermore, the entire source code and user interface are "flattened" and within the comprehension scope of chatbots (under 3k lines of code), allowing for adjustments through prompting to be **compatible with various market data types** beyond coffee.

---

<img width="1913" height="878" alt="image" src="https://github.com/user-attachments/assets/379bc4b7-0588-4c55-a6f7-8a7d5f4442f8" />

<img width="1912" height="870" alt="image" src="https://github.com/user-attachments/assets/64578f3b-bbd2-4dc0-9c3a-a21675df0e9f" />

<img width="1915" height="878" alt="image" src="https://github.com/user-attachments/assets/f19b46a0-d010-4cf4-971c-abca2020d2d0" />

---

# 🚀 Tính năng chính / Key Features

### 🇻🇳 Cấu trúc file dữ liệu (.csv) đầu vào
* Xem `sample_data.csv`.

### 🇬🇧 Input Data File Structure
* See `sample_data.csv`.

---

### 🇻🇳 Quản lý Dữ liệu Tập trung (SST)
* Giao diện lưới dữ liệu (AG Grid) cung cấp khả năng **xem, lọc, và quản lý tập trung toàn bộ dữ liệu sản phẩm** từ một nguồn duy nhất, đảm bảo tính nhất quán và chính xác.
* Hỗ trợ nhập liệu dễ dàng từ file CSV.

### 🇬🇧 Centralized Data Management (SST)
* The data grid interface (AG Grid) provides capabilities to **view, filter, and centrally manage all product data** from a single source, ensuring consistency and accuracy.
* Supports easy data import from CSV files.

---

### 🇻🇳 Cập nhật Giá Tự động
* Sử dụng Selenium/BS4 để truy cập các URL sản phẩm và **tự động thu thập dữ liệu giá mới nhất**.
* Các tác vụ được quản lý trong một hàng đợi trực quan, cho phép người dùng **kiểm chứng dữ liệu tai nguồn, theo dõi tiến trình và xử lý các thay đổi về giá**.

### 🇬🇧 Automatic Price Updates
* Uses Selenium/BS4 to access product URLs and **automatically collect the latest price data**.
* Tasks are managed in a visual queue, allowing users to **verify data at the source, track progress, and handle price changes**.

---

### 🇻🇳 Trực quan hóa Dữ liệu
* Tạo ra các biểu đồ tương tác (Chart.js) một cách tự động từ dữ liệu đã lọc, giúp người dùng **dễ dàng nắm bắt insight thị trường**, bao gồm:
    * Định vị giá trung bình của các thương hiệu.
    * Phân bổ chủng loại cà phê.
    * Bản đồ định vị thương hiệu (dựa trên giá và số lượng SKUs).
    * Phân tích hiệu quả ngưỡng Freeship.

### 🇬🇧 Data Visualization
* Automatically generates interactive charts (Chart.js) from filtered data, helping users **easily grasp market insights**, including:
    * Average price positioning of brands.
    * Coffee type distribution.
    * Brand positioning map (based on price and number of SKUs).
    * Freeship threshold effectiveness analysis.

---

### 🇻🇳 Phân tích bằng AI
* Tích hợp giao diện chatbot, cho phép người dùng gửi câu hỏi bằng ngôn ngữ tự nhiên để nhận các **phân tích chuyên sâu và khuyến nghị chiến lược** từ AI, dựa trên các thống kê từ tập dữ liệu được hiển thị.

### 🇬🇧 AI-Powered Analysis
* Integrates a chatbot interface, allowing users to ask questions in natural language to receive **in-depth analysis and strategic recommendations** from AI, based on statistics from the displayed dataset.

---

### 🇻🇳 Tùy chỉnh Giao diện và Logic
* Cung cấp các tùy chọn linh hoạt để **ẩn/hiện các cột dữ liệu** và định nghĩa các khóa chống trùng lặp, cho phép người dùng **tùy chỉnh công cụ phù hợp với nhu cầu phân tích cụ thể** của họ.

### 🇬🇧 Interface and Logic Customization
* Provides flexible options to **hide/show data columns** and define deduplication keys, allowing users to **customize the tool to their specific analysis needs**.

---

***🇻🇳 Lưu ý:*** *Những tính năng này được tích hợp nhằm mục đích hỗ trợ người sử dụng trong việc đánh giá chất lượng dữ liệu thông qua việc quan sát dữ liệu trực quan và hình dung được việc ứng dụng Trí tuệ nhân tạo (AI) vào giải quyết các bài toán kinh doanh.*

***🇬🇧 Note:*** *These features are integrated to assist users in evaluating data quality through visual data observation and to envision the application of Artificial Intelligence (AI) in solving business problems.*

---

# 🔒 Bảo mật và Tin cậy / Security and Reliability

### 🇻🇳 Quản lý Trình duyệt Tự động
* Ứng dụng sử dụng thư viện Selenium Manager (bản stable) và BeautifulSoup4 (bản speed) của Python để **tự động quản lý phiên bản trình duyệt**, loại bỏ hoàn toàn nhu cầu tải thủ công các file thực thi (như `chromedriver.exe`) và **đảm bảo hoạt động ổn định**.

### 🇬🇧 Automatic Browser Management
* The application uses Python's Selenium Manager (stable version) and BeautifulSoup4 (speed version) libraries to **automatically manage browser versions**, completely eliminating the need for manual downloads of executable files (like `chromedriver.exe`) and **ensuring stable operation**.

---

### 🇻🇳 Thư viện từ Nguồn Chính thức
* Tất cả các thư viện phụ thuộc được cài đặt từ Python Package Index (PyPI) thông qua file `requirements.txt`.

### 🇬🇧 Libraries from Official Sources
* All dependent libraries are installed from the Python Package Index (PyPI) via the `requirements.txt` file.

---

### 🇻🇳 Lưu trữ API Key Phía Client
* Khóa API của Gemini được lưu trữ an toàn trong `sessionStorage` của trình duyệt.
* Điều này có nghĩa là khóa sẽ tự động bị xóa khi phiên làm việc kết thúc và **không bao giờ được lưu trữ trên bất kỳ máy chủ nào**, tuyệt đối bảo mật dữ liệu người dùng.

### 🇬🇧 Client-Side API Key Storage
* The Gemini API key is securely stored in the browser's `sessionStorage`.
* This means the key is automatically deleted when the session ends and is **never stored on any server**, ensuring absolute user data security.

---

# ⚙️ Hướng dẫn Cài đặt Local (Khuyến khích) / Local Installation Guide (Recommended)

### 🇻🇳 Yêu cầu
* Python 3.9+
* Trình duyệt Google Chrome

### 🇬🇧 Requirements
* Python 3.9+
* Google Chrome Browser

---

### 🇻🇳 Các bước
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

### 🇬🇧 Steps
1.  **Fork the project**: Access the GitHub repository of this project and click the **"Fork"** button in the top right corner to create a copy of the project to your GitHub account.
2.  **Clone the repository:**
    ```bash
    git clone <YOUR_REPOSITORY_URL> # Replace with your repository URL
    cd <YOUR_PROJECT_DIRECTORY_NAME> # Replace with your project directory name after cloning
    ```
3.  **Create and activate a virtual environment** to isolate project libraries:
    * On macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    * On Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Switch to the stable version (recommended):**
    Delete the `app.py` file and rename `sel_app.py` to `app.py`
6.  **Run the application:**
    ```bash
    flask run
    ```
7.  **Access the application:**
    Open your browser and go to: `http://127.0.0.1:5000`

---

# ☁️ Triển khai (Deployment)

### 🇻🇳 Cấu hình triển khai
Dự án đã được cấu hình để triển khai trên Render thông qua file `render.yaml`. Cấu hình này bao gồm:
* Sử dụng `gunicorn` để chạy ứng dụng web production.
* Tự động cài đặt Google Chrome thông qua buildpack để phục vụ cho các tác vụ của Selenium.

### 🇬🇧 Deployment Configuration
The project is configured for deployment on Render via the `render.yaml` file. This configuration includes:
* Using `gunicorn` to run the production web application.
* Automatic installation of Google Chrome via buildpack for Selenium tasks.

---

### 🇻🇳 Các bước triển khai trên Render
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
   * **Các trường khác vẫn giữ mặc định**.
6. **Tạo Web Service:** Nhấp vào `"Deploy Web Service"`. Render sẽ tự động bắt đầu quá trình triển khai, cài đặt các phụ thuộc và chạy ứng dụng của bạn. Bạn có thể theo dõi tiến trình trong nhật ký triển khai.
7. **Truy cập ứng dụng:** Sau khi triển khai thành công, Render sẽ cung cấp một URL (`https://coffee-market-analysis.onrender.com` trong trường hợp này) công khai cho ứng dụng của bạn.

### 🇬🇧 Render Deployment Steps
To deploy the project to Render via GitHub, follow these steps:
1. **Log in to Render:** Go to `https://render.com/` and log in with your GitHub account.
2. **Create a new project:** On the Render dashboard, click `"+ New"` and select `"Web Service"`.
3. **Connect GitHub:** Render will ask you to connect your GitHub account. Grant access to this project's repository (or all repositories).
4. **Select repository:** Find and select your *data-phinter* project's GitHub repository.
5. **Configure Web Service:**
   * **Name:** Give your service a memorable name (e.g., `coffee-market-analysis`).
   * **Instance Type:** The minimum configuration for the project is **Free**.
   * **Service Type:** Select `"Web Service"`.
   * **Region:** Choose the region closest to your users (Singapore if you are in Vietnam).
   * **Other fields remain at their default settings**.
6. **Create Web Service:** Click `"Deploy Web Service"`. Render will automatically start the deployment process, installing dependencies and running your application. You can monitor the progress in the deployment logs.
7. **Access the application:** After successful deployment, Render will provide a public URL (`https://coffee-market-analysis.onrender.com` in this case) for your application.

---

# 📄 Giấy phép / License

### 🇻🇳
Dự án này được cấp phép dưới Giấy phép Apache 2.0.

Điều này có nghĩa là bạn được tự do sử dụng, sửa đổi và phân phối mã nguồn cho bất kỳ mục đích nào, kể cả mục đích thương mại, miễn là tuân thủ các điều kiện được nêu trong giấy phép. Để xem toàn bộ nội dung giấy phép, vui lòng đọc file [`LICENSE`](LICENSE).

### 🇬🇧
This project is licensed under the Apache 2.0 License.

This means you are free to use, modify, and distribute the source code for any purpose, including commercial purposes, provided you comply with the conditions outlined in the license. To view the full license content, please read the [`LICENSE`](LICENSE) file.

---

# ❤️ Hỗ trợ tác giả / Support the Author

### 🇻🇳
🎉 Bạn thấy ứng dụng này hữu ích?
Hãy [mua cho tôi một ly cà phê](https://www.buymeacoffee.com/anlt) để tiếp thêm động lực phát triển ☕.
Mọi sự ủng hộ của bạn là nguồn cảm hứng rất lớn. Chân thành cảm ơn 💛

### 🇬🇧
🎉 Do you find this application useful?
[Buy me a coffee](https://www.buymeacoffee.com/anlt) to fuel further development ☕.
Your support is a great source of inspiration. Thank you sincerely 💛
