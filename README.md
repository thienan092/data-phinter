# Data Phin-ter: Hệ thống hỗ trợ thu thập và kiểm chứng dữ liệu "tìm kiếm sâu"

---

## 🇻🇳 Tiếng Việt

**Data Phin-ter** là một ứng dụng web, được thiết kế như một công cụ phân tích nhỏ gọn, dễ dàng **tùy chỉnh thông qua mô hình ngôn ngữ lớn Gemini của Google**.

Dự án này cung cấp các chức năng cơ bản nhất để có thể tận dụng tính năng **Deep Research của Gemini như là một công cụ sinh dữ liệu chất lượng cao** dùng cho việc quan sát thị trường trực tuyến, đồng thời tích hợp cơ chế **tự động hóa việc kiểm chứng dữ liệu tại nguồn trích dẫn** nhằm giám sát những sự thay đổi về giá sản phẩm và loại bỏ/chỉnh sửa các kết quả bị sai sót trong quá trình thu thập dữ liệu hoặc bị ảnh hưởng bởi hiện tượng "hallucination".

Hơn nữa, mã nguồn và giao diện được tổ chức theo các điểm vào, skill và tài liệu kiến trúc có thể tra cứu, giúp agent điều chỉnh ứng dụng qua quy trình prompting để **tương thích với các loại dữ liệu thị trường** khác ngoài cà phê. Không dựa vào một giới hạn số dòng cố định; hãy dùng các liên kết ngữ nghĩa ở phần Agent Entry Point.

### Điểm vào dành cho agent

Agent hoàn toàn mới phải đọc README này trước, sau đó dùng skill
[read-effective-verbal-context](.codex/skills/read-effective-verbal-context/) để phục hồi trạng thái khởi đầu từ
[STARTER-CONTEXT.md](STARTER-CONTEXT.md). Agent có thể tự diễn đạt prompt, nhưng kết
quả cần chỉ ra được các luồng công việc chính, skill phụ trách, ranh giới, artifact, việc đã đóng,
nhánh tùy chọn, xung đột và điểm vào tiếp theo; không chỉ tóm tắt README hoặc dựa vào chat cũ.

Sơ đồ đầu tiên cần đọc là [tổng quan workflow ngắn](plugins/data-phinter-workflows/references/overview.md);
[kiến trúc chi tiết](plugins/data-phinter-workflows/references/architecture.md) là tầng tra cứu tiếp theo.
Stranger audit là phép kiểm định độc lập từ bên ngoài plugin.

Audit đánh giá khả năng tiếp cận trong workspace hiện tại. Publication, installation và khả năng tái
tạo từ một committed checkout là các release gate riêng. Trong một blind audit, báo cáo của các vòng
trước có thể được tạm giữ ngoài workspace để không làm lộ đường khám phá kỳ vọng; khi đó lịch sử audit
có thể được ghi là chưa kiểm chứng, nhưng không được coi là context của plugin bị thiếu.

---

## 🇬🇧 English

**Data Phin-ter (Deep Research Data Collection and Verification System)** is a web application designed as a compact analysis tool, easily **customizable via Google's Gemini large language model**.

This project provides the most basic functionalities to leverage Gemini's **Deep Research feature as a high-quality data generation tool** for online market observation, while integrating an **automated data verification mechanism at the citation source** to monitor product price changes and eliminate/correct erroneous results during data collection or those affected by "hallucination".

Furthermore, source and UI behavior are organized through discoverable entry points, skills, and architecture references, allowing agents to adapt the application through prompting for **various market data types** beyond coffee. Do not rely on a fixed line-count claim; use the semantic links under Agent Entry Point.

---

## Agent Entry Point And Stranger Audit

An agent that is completely new to this project must start by reading this README, then use
[read-effective-verbal-context](.codex/skills/read-effective-verbal-context/) to recover the project's
starting state from [STARTER-CONTEXT.md](STARTER-CONTEXT.md). The skill should reconcile that context
with current source, config, tests, and artifacts instead of treating prose as unquestionable.

Suggested prompt (rephrasing is allowed):

> Read this README, then use `read-effective-verbal-context` to recover the project objective,
> top-level workstreams and responsible skills, active constraints, current state, artifacts,
> closed work, optional branches, conflicts, and next entry points. Verify material claims against
> source/config and give me a compact project map before continuing.

Anti-prompt: do **not** merely summarize the README, rely on previous chat, trust the handoff over
source/config, assume every selected artifact is complete, or automatically execute all open branches.

The first map to read after recovery is the plugin's
[short workflow overview](plugins/data-phinter-workflows/references/overview.md). Use the
[detailed architecture](plugins/data-phinter-workflows/references/architecture.md) only when deeper
mechanics are needed. The independent **Stranger audit** evaluates the plugin from outside under this
README-first condition; it is not a component of the plugin.

The audit evaluates accessibility in the current workspace. Publication, installation, and
reproducibility from a committed checkout are separate release gates. During a blind audit round,
prior audit reports may be temporarily withheld so they cannot reveal the expected discovery path;
their temporary absence may be recorded as unverified history, but is not missing plugin context.

The plugin exposes four skills: context recovery, NotebookLM generation, app-owned candidate intake,
and Shopee recovery. `write-effective-verbal-context` is intentionally retained by the project owner
outside the plugin. A stranger may report documentation or architecture deltas, but must not assume
access to that owner-held skill.

The app's **Accumulate approved unique** control is also intentionally agent-only. It stays hidden in
normal mode and appears only with `?agent=1`. It commits the already approved `unique` verification
artifact into the configured default CSV, deduplicates Links, creates a backup, atomically replaces
the file, and records events. It does not accumulate arbitrary grid contents. Before commit, the
workflow must report the preview and obtain a matching post-report decision; the backend rejects a
commit without that recorded approval. Information parity is carried by the report, decision,
preview counts, backup, before/after counts, and terminal result, not by showing automation controls
to normal users.

---

<img width="1913" height="878" alt="image" src="https://github.com/user-attachments/assets/379bc4b7-0588-4c55-a6f7-8a7d5f4442f8" />

<img width="1912" height="870" alt="image" src="https://github.com/user-attachments/assets/64578f3b-bbd2-4dc0-9c3a-a21675df0e9f" />

<img width="1915" height="878" alt="image" src="https://github.com/user-attachments/assets/f19b46a0-d010-4cf4-971c-abca2020d2d0" />

---

# 🚀 Tính năng chính / Key Features

### 🇻🇳 Cấu trúc file dữ liệu (.csv) đầu vào
* Xem file được khai báo tại `config/default-data.json` (hiện là `sample_data.csv`).
* Người dùng vẫn có thể dùng **Thêm dữ liệu** để nhập một CSV tức thời; thao tác đó không đổi file mặc định.
* Chế độ hỗ trợ agent (`?agent=1`) hiện một điều khiển riêng để nạp file mặc định đã cấu hình.
* Tập ứng viên đang được chọn được khai báo tại `config/current-candidate.json`; hãy đọc cả trường
  `status`/`strict_complete` trước khi coi nó là một run hoàn tất. Chế độ agent có điều khiển riêng để nạp nó sau dữ liệu mặc định.
* Trước khi xác minh, agent chạy skill `app-sst-candidate-intake` để audit bất thường. Cảnh báo
  mức `review` hoặc `blocker` phải được báo cho người dùng quyết định thay vì tự động bỏ qua.
* Sau kiểm chứng, agent chạy **Báo cáo, phân tích và góp ý/cải thiện** như một cổng quyết định;
  chỉ thực hiện tích lũy, sửa trang hoặc tối ưu tùy chọn sau khi người dùng chọn nhánh.
* Báo cáo xuyên suốt quy trình thuộc agent, không phải một bảng báo cáo trong ứng dụng.
  Nếu cần thêm bề mặt báo cáo mới vào ứng dụng, agent phải đề xuất và nhận xác nhận trước.
* Trong báo cáo sau kiểm chứng, agent đưa ra nhánh mở từng trang có vấn đề để sửa giá và phương pháp trích xuất;
  phương pháp có thể là selector ổn định hoặc công thức thích nghi tùy độ biến động của trang.
* Luồng agent dùng trạng thái ẩn trong DOM (`#agent-import-status`) và log JSON tiền tố
  `[agent-import]`, nên automation tiếp cận cùng thông tin nghiệp vụ mà không thêm chi tiết kỹ thuật vào UI.

### 🇬🇧 Input Data File Structure
* See the file declared in `config/default-data.json` (currently `sample_data.csv`).
* Users can still use **Add Data** for an ad-hoc CSV; doing so does not change the configured default.
* Agent-assisted mode (`?agent=1`) exposes a separate control for loading the configured default file.
* The selected candidate artifact is declared in `config/current-candidate.json`; read its
  `status`/`strict_complete` metadata before treating it as a completed run. Agent mode exposes a separate control for loading it after the default data.
* Before verification, the agent runs `app-sst-candidate-intake` to audit anomalies. `review` or
  `blocker` findings require a user decision instead of silent continuation.
* After verification, **Report, analyze, and advise/improve** is the decision gate. Accumulation,
  page repair, and optional optimization run only after the user chooses a branch.
* Cross-workflow reporting belongs to the agent, not an in-app reporting panel.
  Adding a new reporting surface to the app requires a proposal and user approval first.
* Agent imports publish hidden DOM status (`#agent-import-status`) and JSON console logs prefixed
  with `[agent-import]`, giving automation equivalent operational information without adding technical UI.

---

### 🇻🇳 Quản lý Dữ liệu Tập trung (SST)
* Giao diện lưới dữ liệu (AG Grid) cung cấp khả năng **xem, lọc, và quản lý tập trung toàn bộ dữ liệu sản phẩm** từ một nguồn duy nhất, đảm bảo tính nhất quán và chính xác.
* Hỗ trợ nhập liệu dễ dàng từ file CSV.

### 🇬🇧 Centralized Data Management (SST)
* The data grid interface (AG Grid) provides capabilities to **view, filter, and centrally manage all product data** from a single source, ensuring consistency and accuracy.
* Supports easy data import from CSV files.

---

### 🇻🇳 Cập nhật Giá Tự động
* Sử dụng BS4 cho trang tĩnh và CloakBrowser/provider chuyên biệt cho trang động hoặc bị chặn để **tự động thu thập dữ liệu giá mới nhất**.
* Các tác vụ được quản lý trong một hàng đợi trực quan, cho phép người dùng **kiểm chứng dữ liệu tai nguồn, theo dõi tiến trình và xử lý các thay đổi về giá**.

### 🇬🇧 Automatic Price Updates
* Uses BS4 for static pages and CloakBrowser/provider-specific handling for dynamic or blocked pages to **automatically collect the latest price data**.
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
* Ứng dụng dùng CloakBrowser/Playwright cho luồng trình duyệt và BeautifulSoup4 cho luồng HTML tĩnh. Các trạng thái captcha, đăng nhập, chặn truy cập và lỗi selector được phân biệt thay vì gộp thành một lỗi lấy giá.

### 🇬🇧 Automatic Browser Management
* The application uses CloakBrowser/Playwright for browser flows and BeautifulSoup4 for static HTML. Captcha, login, access blocking, and selector failures remain distinct operational states.

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
5.  **Giữ implementation hiện hành:** `app.py` là ứng dụng được hỗ trợ và chứa các API agent/accumulation hiện tại. `sel_app.py` (app Selenium cũ) và `live_test.py` (helper smoke-test CloakBrowser thủ công) chỉ để tham khảo; không đổi tên hoặc ghi đè lên `app.py`.
6.  **Chạy ứng dụng trên cổng mặc định 5000:**
    ```bash
    python app.py
    ```
    Nếu cổng 5000 đang bận, đặt biến `PORT` thành một cổng trống (ví dụ PowerShell:
    `$env:PORT=5002; python app.py`) và dùng chính URL đã chọn.
7.  **Truy cập ứng dụng:** mở `http://127.0.0.1:5000`; chế độ automation của agent là
    `http://127.0.0.1:5000/?agent=1`. Thay `5000` bằng giá trị `PORT` nếu đã đổi cổng.

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
5.  **Keep the current implementation:** `app.py` is the supported application and owns the current agent/accumulation APIs. `sel_app.py` (a legacy Selenium app) and `live_test.py` (a manual CloakBrowser smoke-test helper) are kept for reference only; do not rename them over `app.py`.
6.  **Run the application on default port 5000:**
    ```bash
    python app.py
    ```
    If port 5000 is occupied, set `PORT` to a free port (for example in PowerShell:
    `$env:PORT=5002; python app.py`) and use that same URL.
7.  **Access the application:** open `http://127.0.0.1:5000`; agent automation mode is
    `http://127.0.0.1:5000/?agent=1`. Replace `5000` with the chosen `PORT` when overridden.

---

# ☁️ Triển khai (Deployment)

### 🇻🇳 Cấu hình triển khai
Dự án đã được cấu hình để triển khai trên Render thông qua file `render.yaml`. Cấu hình này bao gồm:
* Sử dụng `gunicorn` để chạy ứng dụng web production.
* Giữ buildpack Chrome hiện có cho các tác vụ trình duyệt; cần xác minh khả năng tương thích CloakBrowser/Playwright trước mỗi lần triển khai.

### 🇬🇧 Deployment Configuration
The project is configured for deployment on Render via the `render.yaml` file. This configuration includes:
* Using `gunicorn` to run the production web application.
* Keeps the current Chrome buildpack for browser tasks; verify CloakBrowser/Playwright compatibility before each deployment.

---

### 🇻🇳 Các bước triển khai trên Render
Để triển khai dự án lên Render thông qua GitHub, hãy làm theo các bước sau:
1. **Đăng nhập vào Render:** Truy cập `https://render.com/` và đăng nhập bằng tài khoản GitHub của bạn.
2. **Tạo dự án mới:** Trên bảng điều khiển Render, nhấp vào `"+ New"` và chọn `"Web Service"`.
3. **Kết nối GitHub:** Render sẽ yêu cầu bạn kết nối tài khoản GitHub của mình. Cấp quyền truy cập cho kho chứa dự án này (hoặc tất cả các kho chứa).
4. **Chọn kho chứa:** Tìm và chọn kho chứa GitHub của dự án *data-phinter* của bạn.
5. **Cấu hình dịch vụ Web:**
   * **Tên (Name):** Đặt một tên dễ nhớ cho dịch vụ của bạn (ví dụ: `coffee-market-analysis`).
   * **Instance Type:** `render.yaml` hiện khai báo gói **Starter**; thay đổi gói chỉ sau khi kiểm tra nhu cầu và cấu hình Render hiện hành.
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
   * **Instance Type:** `render.yaml` currently declares the **Starter** plan; change it only after reviewing current workload and Render configuration.
   * **Service Type:** Select `"Web Service"`.
   * **Region:** Choose the region closest to your users (Singapore if you are in Vietnam).
   * **Other fields remain at their default settings**.
6. **Create Web Service:** Click `"Deploy Web Service"`. Render will automatically start the deployment process, installing dependencies and running your application. You can monitor the progress in the deployment logs.
7. **Access the application:** After successful deployment, Render will provide a public URL (`https://coffee-market-analysis.onrender.com` in this case) for your application.

---

# ⚠️ Sử dụng có trách nhiệm / Responsible Use

### 🇻🇳
Đây là công cụ phục vụ **nghiên cứu và quan sát thị trường cho mục đích được phép**. Khi sử dụng:
* Tôn trọng Điều khoản dịch vụ (ToS) và `robots.txt` của mỗi trang nguồn; chỉ thu thập dữ liệu công khai ở mức hợp lý, tránh gây tải bất thường.
* Các luồng khôi phục cho trang có thử thách đăng nhập/bot (ví dụ `shopee-scrape-recovery`, hồ sơ trình duyệt cục bộ) chỉ dùng cho **phiên hợp pháp của chính bạn và khi được ủy quyền**. Không bao giờ commit hồ sơ trình duyệt, cookie hay thông tin đăng nhập.
* Bạn chịu trách nhiệm tuân thủ pháp luật và quy định áp dụng tại khu vực của mình.

### 🇬🇧
This is a tool for **authorized market research and observation**. When using it:
* Respect each source site's Terms of Service and `robots.txt`; collect only public data at a reasonable rate and avoid abnormal load.
* Challenge-recovery flows for login/bot-walled sites (e.g. `shopee-scrape-recovery`, local browser profiles) are for **your own authorized sessions only**. Never commit browser profiles, cookies, or credentials.
* You are responsible for complying with the laws and regulations applicable in your jurisdiction.

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
