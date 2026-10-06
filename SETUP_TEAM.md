# Thành viên mới: cài và chạy FallDetection trên Windows

Repo: https://github.com/fmdev23/fallDetection

Hướng dẫn này dùng Windows x64 và **Python 3.14.3 bản tiêu chuẩn 64-bit**, cùng phiên bản đã chạy trên máy phát triển. Không dùng bản free-threaded. Bộ requirements hiện tại có NumPy yêu cầu Python >=3.12; không dùng Python 3.10/3.11. macOS/Linux và Windows ARM chưa được kiểm chứng cho đầy đủ camera/âm thanh trong dự án.

## 1. Cài công cụ

1. Cài Python 3.14.3 từ python.org, gồm pip, Python launcher và Tcl/Tk (tkinter). Chọn Add Python to PATH nếu trình cài đặt có tùy chọn đó.
2. Cài Visual Studio Code. Cài Git nếu muốn clone/pull; tải ZIP thì không bắt buộc Git để chạy.
3. Đóng rồi mở lại terminal sau khi cài Python. Kiểm tra:

```powershell
py -3.14 --version
py -3.14 -c "import struct, tkinter; print('bits:', struct.calcsize('P')*8); print('Tk:', tkinter.TkVersion)"
```

Mong đợi Python 3.14.3, bits 64 và phiên bản Tk. Nếu không có Python phù hợp, sửa cài đặt trước, không tiếp tục tạo môi trường bằng một phiên bản ngẫu nhiên.

Nếu chỉ chạy video thì chưa cần PlatformIO/Wokwi. Hai extension này chỉ cần ở mục 7.

## 2. Lấy mã nguồn và mở đúng thư mục

Clone tại nơi bạn muốn lưu project:

```powershell
git clone https://github.com/fmdev23/fallDetection.git
cd fallDetection
```

Hoặc GitHub → Code → Download ZIP → giải nén hoàn toàn. Không chạy trong ZIP. Mở VS Code → Open Folder → thư mục có `requirements.txt`, `platformio.ini`, `run_app.bat`, `python_app`.

Mở Terminal → New Terminal trong VS Code. Kiểm tra:

```powershell
Get-Location
Test-Path .\requirements.txt
Test-Path .\python_app\gui.py
```

Hai Test-Path phải là True. Nếu sai, bạn đang đứng ngoài thư mục project hoặc mở nhầm tầng thư mục ZIP.

## 3. Tạo môi trường riêng trên từng máy

```powershell
py -3.14 -m venv venv
.\venv\Scripts\python.exe -X utf8 -m pip install --upgrade pip
.\venv\Scripts\python.exe -X utf8 -m pip install -r requirements.txt
.\venv\Scripts\python.exe -X utf8 -m pip check
```

Đợi từng lệnh hoàn tất. Lần đầu cần Internet và có thể mất thời gian vì PyTorch lớn. Dự án chạy CPU, không bắt buộc GPU/CUDA.

`pip check` phải báo **No broken requirements found**. Không bỏ qua lỗi cài đặt rồi tiếp tục mở GUI. Không cần Activate.ps1, vì các lệnh gọi thẳng Python trong venv; cách này tránh lỗi PowerShell execution policy và dùng nhầm Python.

Không chép `venv` từ máy khác. Nếu đã tạo venv bằng phiên bản Python sai, đóng app, đổi tên venv cũ để giữ lại rồi tạo venv mới bằng đúng lệnh trên.

## 4. Kiểm tra thư viện và model trước khi mở app

```powershell
.\venv\Scripts\python.exe -X utf8 -c "import tkinter, cv2, torch, ultralytics, serial; from PIL import Image; print('Imports OK'); print('Torch:', torch.__version__)"
.\venv\Scripts\python.exe -X utf8 -c "from python_app.pose_detector import PoseDetector; PoseDetector(); print('Model ready')"
```

Lệnh thứ hai nạp model; Ultralytics sẽ thử tải model nếu thiếu. Cần Internet ở lần đầu. Sau đó kiểm tra:

```powershell
Test-Path .\yolo11n-pose.pt
```

Phải là True và lệnh nạp model phải thành công. Nếu mạng chặn tải, nhận **đúng file `yolo11n-pose.pt`** đã chạy được từ trưởng nhóm, đặt ngang hàng `requirements.txt`, rồi chạy lại lệnh nạp. Không đổi tên một model khác thành tên này.

Không cần tải dataset hoặc training để chạy inference. Model/file video bị gitignore nên clone repository không tự có chúng.

## 5. Nhận video demo từ nhóm

Trưởng nhóm gửi các file hiện có, thành viên đặt vào đúng vị trí:

```text
fallDetection/
  yolo11n-pose.pt
  requirements.txt
  run_app.bat
  python_app/
  test_videos/
    demo_fall_01.mp4
    demo_fall_02.mp4
    solo_transition.avi
```

`demo_fall_02.mp4` cho cảnh báo sớm khoảng 3.5 giây; `demo_fall_01.mp4` khoảng 20.6 giây; `solo_transition.avi` có đoạn nằm ở cuối. Đây là kết quả đã quan sát trên máy phát triển, không phải bảo đảm mọi máy cho kết quả giống hệt.

Các file video **không đi theo Git** với .gitignore hiện tại. Chia sẻ qua thư mục dùng chung của nhóm; không trỏ tới đường dẫn ổ D: trên máy trưởng nhóm. Chưa có video thì vẫn thử được webcam, nhưng không thể chọn một video không tồn tại.

## 6. Chạy video trước để kiểm tra cài đặt

```powershell
.\venv\Scripts\python.exe -X utf8 python_app/gui.py
```

1. Bật Âm thanh → Thử chuông → Đã thấy — tắt chuông.
2. Chọn Video → Chọn video… → `test_videos/demo_fall_02.mp4`.
3. **Bỏ chọn Ghép Wokwi trực tiếp vào video**.
4. Bấm Bắt đầu. Phải thấy hình video và thông tin xử lý. Cảnh báo đã quan sát khoảng 3.5 giây theo đồng hồ Video trên app.
5. Bấm Dừng trước khi đổi file/nguồn.

Bài này không cần Wokwi, không đọc sensor và không tự tạo FALL_DETECTED từ hai nguồn. Video có thể phát chậm vì phân tích đủ frame. Sau khi lần chạy terminal thành công, có thể dùng `run_app.bat` hằng ngày. Khi cần xem lỗi, quay lại chạy terminal.

## 7. Cài và chạy Wokwi nếu cần cảm biến

1. Trong VS Code, cài **PlatformIO IDE** và **Wokwi Simulator**; chờ PlatformIO cài công cụ xong, reload VS Code nếu được yêu cầu.
2. Làm bước kích hoạt license của Wokwi bằng tài khoản riêng: F1 → **Wokwi: Request a new License** → hoàn thành hướng dẫn trên trình duyệt. Xem [hướng dẫn chính thức](https://docs.wokwi.com/vscode/getting-started). Không chia sẻ license/token cá nhân qua repo.
3. Mở đúng thư mục chứa platformio.ini. Chạy **PlatformIO: Build**; hoặc mở PlatformIO Core CLI/terminal rồi chạy `pio run`. Đợi báo SUCCESS.
4. Kiểm tra hai file sau đã xuất hiện:

```powershell
Test-Path .\.pio\build\esp32dev\firmware.bin
Test-Path .\.pio\build\esp32dev\firmware.elf
```

5. F1 → **Wokwi: Start Simulator**. Không dùng bản Wokwi trên trình duyệt thay cho extension trong bài kết nối này.
6. Giữ cấu hình `wokwi.toml`: RFC2217 cổng 4000. Kiểm tra:

```powershell
Test-NetConnection localhost -Port 4000
```

`TcpTestSucceeded` phải là True. Không có thư mục `.pio` ngay sau clone là bình thường: thư mục này được sinh ra khi Build và bị gitignore.

## 8. Chạy webcam hoặc video ghép sensor

**Webcam + Wokwi:**

1. Cho phép ứng dụng desktop dùng camera trong Windows Settings → Privacy & security → Camera; đóng app khác đang giữ webcam.
2. Wokwi đặt Acceleration `(0,0,1)`, Rotation `(0,0,0)`.
3. Mở GUI bằng lệnh mục 6, chọn Webcam, camera 0; giữ cổng `rfc2217://localhost:4000`.
4. Bấm Bắt đầu. Kiểm tra hình camera và số đo sensor. Nếu có nhiều camera, Dừng rồi thử camera 1.
5. Đặt Rotation X = 120 °/s trong Wokwi để thử cảnh báo sớm. Trả về 0 sau khi thử. Camera cần thấy rõ vai, hông và chân; không cần cố té thật.

**Video + Wokwi:**

1. Dừng lượt đang chạy, chọn Video → `solo_transition.avi`.
2. **Bật Ghép Wokwi trực tiếp vào video**; chỉ chạy Wokwi mà không bật ô này thì video vẫn độc lập.
3. Đặt Rotation `(200,0,0)` °/s, acceleration `(0,0,1)`, Bắt đầu. Sensor phải hiện IMPACT.
4. Khi nhận rõ nằm đủ 1.3 giây ở cuối clip cùng IMPACT, hệ thống có điều kiện tạo FALL_DETECTED. Tắt chuông, Dừng và trả Rotation về 0.

Đây là demo ghép cảm biến giả lập, không phải IMU được ghi cùng video. Chỉ mở một GUI/reader tại một thời điểm. Không đồng thời chạy sensor_reader.py hoặc console demo.

## 9. Lỗi hay gặp

| Lỗi | Cách xử lý |
|---|---|
| `py` không nhận / không có Python 3.14 | Cài Python launcher và đúng Python, mở lại terminal |
| Không thấy `venv\Scripts\python.exe` | Đứng đúng project rồi làm mục 3 |
| No matching distribution / Requires-Python | Kiểm tra Python 3.14.3 tiêu chuẩn x64; cập nhật pip; xem lỗi mạng/index. Không tự bỏ pin thư viện |
| ModuleNotFoundError | Cài requirements bằng chính `venv\Scripts\python.exe`, không dùng pip toàn máy |
| Không có tkinter | Sửa cài đặt Python, thêm Tcl/Tk; không cài gói tên tkinter từ pip |
| Tải model thất bại | Kiểm tra Internet hoặc lấy đúng model của nhóm, nạp lại theo mục 4 |
| Nhấp run_app.bat rồi app biến mất | Chạy GUI bằng terminal để đọc traceback |
| `pio` không nhận trong PowerShell thường | Dùng PlatformIO: Build hoặc terminal của PlatformIO |
| Wokwi báo thiếu firmware | Build SUCCESS trước khi Start Simulator |
| SENSOR_DISCONNECTED | Kiểm tra license, Simulator, cổng 4000 và đóng reader khác; Dừng/Bắt đầu lại |
| Camera không mở | Kiểm tra quyền camera, đóng Zoom/Teams/app khác, thử camera index khác |
| UNKNOWN kéo dài | Điều chỉnh góc máy/ánh sáng và để thấy toàn thân; chưa phải bằng chứng cài lỗi |
| Video có cảnh báo nhưng không FALL_DETECTED | Kiểm tra đang video độc lập hay ghép sensor; thiếu IMU thì chỉ cảnh báo nguy cơ/nằm lâu |

## 10. Kiểm tra và cập nhật chung

Sau khi cài xong có thể kiểm tra logic, không cần camera/Wokwi:

```powershell
.\venv\Scripts\python.exe -X utf8 -m unittest discover -s test -p "test_*.py"
```

Bản hiện tại có 50 tests; tests PASS không phải chứng nhận độ chính xác webcam. Trước buổi bảo vệ vẫn chạy thử loa, webcam và bài demo trên đúng máy.

Khi nhóm có code mới, dừng app, lưu/commit công việc riêng rồi cập nhật nhánh phù hợp. Nếu working tree sạch trên nhánh chính:

```powershell
git pull --ff-only
.\venv\Scripts\python.exe -X utf8 -m pip install -r requirements.txt
.\venv\Scripts\python.exe -X utf8 -m pip check
```

Nếu git pull báo lỗi, không dùng reset --hard để ép mất thay đổi. Firmware thay đổi thì Build và Stop/Start Wokwi lại. Mỗi người có venv riêng; không commit venv, `.pio`, license hoặc token.

Đối chiếu mô hình pose: [Ultralytics YOLO11](https://docs.ultralytics.com/models/yolo11/). Hướng dẫn thuyết trình: [HUONG_DAN_BAO_VE.md](HUONG_DAN_BAO_VE.md).
