# Phát hiện và cảnh báo té ngã bằng tư thế và IMU giả lập

**Thành viên mới tải từ GitHub:** làm theo [SETUP_TEAM.md](SETUP_TEAM.md), gồm Python, thư viện, model/video còn thiếu, Wokwi và xử lý lỗi thường gặp.

**Mang đi bảo vệ:** đọc [hướng dẫn từng bước và danh sách video demo](HUONG_DAN_BAO_VE.md). Video đã kiểm tra nằm trong `test_videos`: `demo_fall_01.mp4`, `demo_fall_02.mp4`, `solo_transition.avi`. Chọn Video mặc định **không dùng Wokwi**; phải bật ô ghép Wokwi nếu muốn demo video + sensor.

Đồ án Xử lý ảnh / Nhận dạng: dùng **YOLO11n Pose pretrained** để nhận tư thế, kết hợp dữ liệu MPU6050 trên Wokwi bằng luật và thời gian. Chương trình chạy trên CPU, không train model, không cần database hay dịch vụ cloud.

**Cập nhật 06/10/2026:** webcam và video dùng chung `SceneAnalyzer`, theo dõi bằng chứng riêng từng người. Có thêm nhận biết thân/hông hạ nhanh so với chân; lọc chuyển động do đi gần camera và tư thế bị cắt ở mép ảnh. Optical flow DIS xử lý chuyển động lớn giữa các frame, chỉ bổ sung cảnh báo khi tư thế không rõ. Với nhiều người, một IMU không được tự gán cho bất kỳ người nào để xác nhận FALL; cảnh báo camera vẫn hoạt động. Ghép người khi giao nhau/che khuất vẫn có thể sai, chưa phải hệ thống theo dõi danh tính.

**Dữ liệu học bổ sung:** đã tải 70 video URFD (30 ngã/40 ADL), cắt RGB và chia 42 train / 14 validation / 14 test theo video, tổng khoảng 117 MB gồm nguồn + RGB. Xem [hướng dẫn dữ liệu, giấy phép và giới hạn nhãn](data/urfall/README.md). Chạy **`label_videos.bat`** để rà soát/gán nhãn từng đoạn. Dữ liệu chưa tự động huấn luyện hoặc thay model ứng dụng; nhãn depth không bị giả định là nhãn RGB chính xác, và chưa có nhãn dự báo trước ngã.

Kiểm tra bản hiện tại: **50 unittest PASS**; replay model thật đủ 783/512 frame của hai clip phát một EARLY_WARNING mỗi clip (~20,60 s và ~3,50 s). Kiểm tra logic/optical flow trên kết quả detector đã lưu với 7 biến thể mỗi clip (30/15/10 FPS, resize, mirror, đổi tốc độ) vẫn bắt được sự kiện ở cả hai; clip thứ hai có thêm cảnh báo nguy cơ tại ~13,82 s ở bản 10–15 FPS. Clip đứng/không ngã `solo_lying.avi` không phát cảnh báo trong 7 biến thể; `solo_transition.avi` có LYING_CHECK. Đây là kiểm tra hồi quy trên dữ liệu đã xem, **không phải accuracy trên test độc lập**, và biến đổi keypoints đã lưu không đo độ bền của YOLO với ảnh biến đổi. Chi tiết nằm trong `results/video_review/*variants.json` và `final_model_audit.json`.

## Chạy nhanh trên máy hiện tại

**Sửa chế độ video ngày 05/10/2026:** mở lại `run_app.bat` → **Video → Chọn video… → Bắt đầu**. Chọn clip gốc, không chọn bản quay màn hình ứng dụng. Mặc định video chạy độc lập, **không cần Wokwi**. Để trống ô “Ghép Wokwi trực tiếp vào video”; chỉ bật khi chủ động demo dữ liệu IMU cùng clip.

Video độc lập phân tích **đủ từng frame**, tính thời gian từ FPS của clip, không bỏ frame theo tốc độ CPU. Phát có thể chậm hơn thời gian thực; mốc thời gian trong giao diện vẫn là thời gian clip. Camera/Webcam vẫn dùng thời gian thực. Video không có dữ liệu IMU không tự ghép sensor hiện tại vào sự kiện đã ghi trước đó.

Khi người vừa được nhận diện bị mất keypoint, nhánh optical flow theo dõi vùng đó tối đa 1,2 giây để phát hiện chuyển động xuống nhanh. Có bù pan toàn ảnh, lọc cắt cảnh, vùng sát mép dưới và nhiễu ngắn; bằng chứng giữ riêng theo từng track. Nó phát **EARLY_WARNING — cần kiểm tra**, không giả mạo tư thế LYING hay xác nhận FALL. Đồ vật/người khác chuyển động gần vùng theo dõi hoặc camera chuyển động phức tạp vẫn có thể gây báo nhầm; cần thêm bộ thử độc lập để đánh giá.

**Webcam + IMU:** đóng ứng dụng cũ, Build rồi Stop/Start Wokwi để nạp firmware gửi khoảng 50 mẫu/giây. Mở lại `run_app.bat`. Ưu tiên Tkinter: cảnh báo IMU chạy riêng, không đợi YOLO xử lý ảnh.

| Thông báo | Khi nào | Hành vi |
|---|---|---|
| EARLY_WARNING — cảnh báo nguy cơ | IMU bất thường, thân nghiêng nhanh, hoặc chuyển động xuống nhanh gần người vừa nhận diện | Nháy giao diện/popup và chuông, không đợi nằm |
| LYING_CHECK — cần kiểm tra | Nằm quan sát rõ đủ **1,3 giây**, kể cả thiếu IMU | Nháy/chuông; chưa khẳng định té |
| FALL — xác nhận theo hai nguồn | Impact phù hợp và nằm đủ **1,3 giây** | Cảnh báo đỏ, ưu tiên cao nhất |

Mọi loại chuông lặp đến khi bấm **Đã thấy — tắt chuông**. Khi đã tắt tiếng, viền/trạng thái vẫn nháy nếu nguy cơ còn hoạt động. Mỗi đợt chỉ có một popup, không mở liên tục cửa sổ mới. GUI hiển thị số đo sensor cập nhật riêng và thời gian xử lý ảnh; nếu ảnh chậm cập nhật sẽ có thông báo.

**Thử nhanh cảnh báo sớm:** acceleration `(0,0,1)`, rotation `(120,0,0)` °/s. Sensor có thể vẫn ghi NORMAL (chưa tới IMPACT) nhưng phải cảnh báo sớm ngay cả khi người còn đứng. Đưa rotation về 0 sau khi thử. Với clip `solo_transition.avi` và sensor bình thường, nằm đủ 1,3 giây phải có LYING_CHECK; chuyển động thân nhanh có thể báo sớm trước đó.

### Luật cảnh báo sớm thử nghiệm

- Gia tốc tổng ≥1,6 g hoặc ≤0,55 g, hoặc gyro tổng ≥100 °/s: nhiều mẫu trải ít nhất 80 ms.
- IMPACT, hoặc biến thiên vector gia tốc ≥5 g/s kèm lệch khỏi 1 g ≥0,25 g / gyro ≥60 °/s: cảnh báo ngay mẫu hợp lệ.
- Camera: ít nhất 3 mẫu thân rõ trong 0,4 giây, góc nghiêng tăng ≥18°, tốc độ ≥90°/s, khoảng quan sát ≥0,1 giây. Mất keypoint hoặc gián đoạn dài xóa lịch sử so sánh.
- Hạ người nhanh: vai và hông cùng hạ tương đối so với chân trong khoảng 0,15–0,6 giây, chuẩn hóa theo chiều cao người. Đòi hỏi cả dịch chuyển xuống trên ảnh và dịch chuyển so với chân để giảm nhầm khi đi lại/nhấc chân. Ngồi nhanh/ngồi xổm vẫn có thể phát cảnh báo nguy cơ.
- IMU yên 1 giây thì tái kích hoạt cho sự kiện mới. Mẫu sensor quá 0,75 giây không được dùng. Tkinter kiểm tra hàng đợi mỗi 40 ms; độ trễ thực còn phụ thuộc mô phỏng/truyền dữ liệu/máy tính.

Đây là **cảnh báo nguy cơ**, không phải dự đoán chắc chắn sẽ té. Cúi hoặc vận động mạnh cũng có thể báo. Wokwi không tự đo cơ thể trong webcam; muốn cảnh báo dựa trên gia tốc cơ thể cần IMU thật gắn đúng người và đánh giá lại. Camera không thấy được mọi hướng lao đao/che khuất. Không thể bảo đảm báo trước mọi cú té trước khi có dấu hiệu đo được.

### Tài nguyên và tốc độ

Giữ một model YOLO11n Pose, không tải thêm. Kích thước xử lý 480 thay 640: trên 27 frame chọn từ clip hiện có, trung vị khoảng 49 ms thay 73 ms; đoạn nằm cuối clip vẫn được nhận ra. Đây là phép đo nhỏ trên máy hiện tại, không bảo đảm FPS/accuracy mọi tình huống. GUI chỉ giữ frame mới nhất; gợi ý buffer camera = 1 có thể bị backend bỏ qua.

Môi trường `venv` khoảng 1,04 GB chủ yếu là PyTorch/thư viện cần để chạy; không gửi kèm khi chia sẻ mã. Model khoảng 6 MB. Giữ video cá nhân và CSV minh chứng. `.gitignore` loại môi trường, model, build, cache, video và log khỏi commit. Công cụ chặn xóa `__pycache__` trong phiên này, nên cache nhỏ vẫn còn; không ảnh hưởng ứng dụng.

1. Mở project trong VS Code, **Build** firmware rồi chạy **Wokwi: Start Simulator**. Nếu Wokwi đang chạy firmware cũ, dừng và khởi động lại mô phỏng sau Build.
2. Nhấp đúp **`run_app.bat`** tại gốc project để mở ứng dụng Tkinter.
3. Chọn **Webcam**, bấm **Bắt đầu**. Để rõ một người, gồm vai, hông và chân.
4. Bấm **Thử chuông** để kiểm tra loa. Cảnh báo té có cửa sổ đỏ và chuông lặp; bấm **Đã thấy — tắt chuông** để tắt. Việc xác nhận không xóa trạng thái té; hệ thống tự hồi phục khi đứng và sensor bình thường ổn định 2 giây.

Giao diện có hình/skeleton, tư thế, số đo sensor, thời gian impact, tiến độ xác nhận nằm và lý do chưa đủ điều kiện. Nút **Dừng** giải phóng camera/sensor. Có thể chỉnh ngưỡng trước khi bắt đầu lượt mới; mỗi lượt có CSV riêng trong `results/gui_*.csv`.

Chạy giao diện từ terminal:

```powershell
.\venv\Scripts\python.exe python_app/gui.py
```

Hoặc dùng phiên bản console/OpenCV, cũng có popup và tiếng chuông:

```powershell
.\venv\Scripts\python.exe python_app/main.py --source webcam
```

Nhấn **q trong cửa sổ hình ảnh** hoặc đóng cửa sổ để thoát console. Chỉ mở một chương trình đọc Wokwi tại một thời điểm; dừng GUI trước khi chạy `sensor_reader.py` hoặc demo console.

## Kiến trúc và phần cứng

```text
MPU6050 (Wokwi) → ESP32 → Serial RFC2217 localhost:4000
                                      ↓
                               Sensor analyzer
                                NORMAL / IMPACT
                                      ↓
Webcam / video → YOLO11n Pose → Posture analyzer → Fusion theo thời gian
                               UPRIGHT / LYING      ↓
                                  / UNKNOWN       Overlay + cảnh báo + CSV
```

- **ESP32** đọc cảm biến rồi gửi số liệu qua Serial, chu kỳ khoảng 20 ms.
- **MPU6050** là cảm biến IMU gồm gia tốc kế và con quay hồi chuyển, mỗi loại có ba trục.
- **Accelerometer** đo gia tốc, bao gồm ảnh hưởng trọng lực; firmware gửi đơn vị **g**, dải đo **±8 g**. Dải mặc định của thư viện là ±2 g, không phù hợp ngưỡng impact >2 g khi thử trên một trục; firmware đã đặt rõ dải mới.
- **Gyroscope** đo tốc độ quay; firmware gửi đơn vị **deg/s**.
- I2C nối SDA vào GPIO 21, SCL vào GPIO 22, VCC 3V3 và GND theo `diagram.json`.

Firmware giữ giao thức STEP 14:

```text
SENSOR,ax,ay,az,gx,gy,gz
```

Camera cung cấp hình dạng/tư thế; IMU cung cấp dấu hiệu chuyển động mạnh. Chỉ camera có thể nhầm nằm chủ động với té; chỉ IMU có thể nhầm chuyển động mạnh khi vẫn đứng với té. Kết hợp hai nguồn giúp bổ sung bằng chứng, nhưng không loại bỏ mọi sai số.

## Cài đặt

Đã kiểm tra trên Windows, Python **3.14.3**, PySerial 3.5 và các phiên bản trong `requirements.txt`. Cần VS Code có PlatformIO, Wokwi và quyền sử dụng webcam. Môi trường Python khác chưa được kiểm chứng trong phiên này.

Nếu chưa có thư mục `venv`, tạo một lần:

```powershell
py -3.14 -m venv venv
```

Cài và kiểm tra thư viện:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m pip check
```

Lần chạy vision đầu tiên cần Internet để tải `yolo11n-pose.pt` khoảng 6 MB từ Ultralytics. Model được đặt tại gốc project; các lần sau dùng file đó. PyTorch và các thư viện phụ thuộc lớn hơn file model. Không cần CUDA/TensorRT.

## Chạy Wokwi và kiểm tra sensor

1. Mở đúng thư mục FallDetection trong VS Code.
2. Bấm **PlatformIO: Build**, hoặc chạy `pio run` trong PlatformIO terminal.
3. `wokwi.toml` trỏ tới `.pio/build/esp32dev/firmware.bin` và `firmware.elf`, mở RFC2217 cổng 4000.
4. Chạy **Wokwi: Start Simulator** từ Command Palette.
5. Mở bộ điều khiển MPU6050 để thay đổi acceleration/rotation.

Kiểm tra độc lập trong 10 giây:

```powershell
.\venv\Scripts\python.exe python_app/sensor_reader.py --duration 10
```

Gia tốc `(0, 0, 1)` g và gyro `(0, 0, 0)` deg/s cho `NORMAL`. Rotation X khoảng 200 deg/s cho `IMPACT`; đưa về 0 để tạo lần thử tiếp theo. Thanh chỉnh Wokwi hiện giới hạn ±2 g mỗi trục. Để thử riêng gia tốc, đặt gyro cả ba trục về 0, acceleration X = 2, Y = 0, Z = 2 g: tổng khoảng 2,83 g / IMPACT. Đưa X/Y về 0 và Z về 1 g: NORMAL. Chỉ Z = 2 g thì bằng ngưỡng IMPACT, vẫn NORMAL nhưng đã đủ cảnh báo sớm; không cần cố tăng vượt giới hạn thanh chỉnh. Cần khởi động lại Wokwi để nạp firmware ±8 g mới.

## Các chế độ Python

YOLO độc lập, không cần sensor:

```powershell
.\venv\Scripts\python.exe python_app/pose_detector.py --source webcam
```

Demo webcam với sensor:

```powershell
.\venv\Scripts\python.exe python_app/main.py --source webcam
```

Video thật đã ghi khi kiểm thử, kết hợp **sensor Wokwi đang chạy trực tiếp**:

```powershell
.\venv\Scripts\python.exe python_app/main.py --source video --path test_videos/solo_transition.avi --video-live-sensor --log results/trial_02.csv
```

Video này dài khoảng 45 giây, có đoạn nằm rõ từ khoảng 39,8 giây. Để thử một mình: chọn Video trong GUI và chọn file này, bật ô “Ghép Wokwi trực tiếp vào video”, đặt Rotation X = 200 deg/s rồi giữ nguyên, bấm Bắt đầu. Impact đang duy trì được coi là bằng chứng hiện tại nên không cần canh đúng giây; dự kiến cảnh báo khi nằm rõ đủ 1,3 giây (khoảng giây 41–42 của clip). Sau lượt thử đưa Rotation X về 0. **Không cần thực hiện té thật.** Đồng hồ video hiển thị trên cửa sổ. Chọn tên log mới cho mỗi lượt đánh giá.

Hai bản ghi trước được giữ để đối chiếu: `solo_posture.avi` dài 30 giây, đoạn nằm nằm sát cuối nên quá ngắn để xác nhận; `solo_lying.avi` dài 60 giây nhưng chủ yếu đứng và quay gần camera, không có đoạn nằm dùng được. Tên clip thứ hai là tên lượt ghi, không phải nhãn ground truth.

Chỉ khi bật --video-live-sensor/ô ghép Wokwi, video mới phát theo thời gian thực và có thể bỏ frame để giữ gần đồng hồ sensor. Video độc lập mặc định phân tích đủ frame theo thời gian clip. Video không chứa dữ liệu IMU và không tự sinh impact. Đây là kiểm thử phối hợp hai nguồn giả lập, không chứng minh accuracy trên các cú té thật.

Ảnh tĩnh của bạn:

```powershell
.\venv\Scripts\python.exe python_app/main.py --source image --path "duong_dan_anh.jpg"
```

Thay đường dẫn trên bằng file có thật. **Ảnh tĩnh chỉ đánh giá tư thế, không đủ dữ liệu để kết luận té ngã.** Chế độ image không mở sensor, không chạy fusion, không ghi log té ngã. Thông báo trên cửa sổ dùng tiếng Anh để tương thích font OpenCV; terminal có giải thích tiếng Việt.

Tùy chọn thường dùng:

| Tùy chọn | Mặc định | Ý nghĩa |
|---|---|---|
| `--video-live-sensor` | tắt | Chỉ dùng khi cố ý demo video cùng IMU đang chạy; mặc định video độc lập không mở sensor |
| `--camera` | `0` | Chọn webcam khác |
| `--port` | `rfc2217://localhost:4000` | Cổng sensor, có thể đổi sang COM khi dùng phần cứng thật |
| `--accel-threshold` | `2.0` | Ngưỡng gia tốc tổng, g |
| `--gyro-threshold` | `150.0` | Ngưỡng tốc độ quay tổng, deg/s |
| `--impact-window` | `5.0` | Khoảng gần nhau giữa impact và bắt đầu nằm, giây |
| `--lying-hold` | `1.3` | Thời gian duy trì nằm sau hai bằng chứng, giây |
| `--recovery-hold` | `2.0` | Thời gian đứng + sensor bình thường để reset |
| `--occlusion-grace` | `0.6` | Cho phép mất keypoints ngắn; thời gian thiếu điểm không được cộng |
| `--lying-warning` | `1.3` | Nằm quan sát được đủ thời gian thì nhắc kiểm tra, kể cả thiếu impact |
| `--no-alerts` | tắt | Khi truyền cờ: tắt popup/chuông cho kiểm thử tự động |
| `--duration` | `0` | Tự dừng sau N giây; 0 là chạy đến khi thoát |
| `--log` | `results/events.csv` | CSV của console; GUI tự tạo tên riêng cho từng lượt |

## Quy tắc xử lý

`accel_total = sqrt(ax² + ay² + az²)`; `gyro_total = sqrt(gx² + gy² + gz²)`. Sensor là `IMPACT` khi một tổng **lớn hơn** ngưỡng tương ứng; bằng ngưỡng vẫn là `NORMAL`. Đây là **ngưỡng thử nghiệm, không phải ngưỡng y khoa**.

YOLO trả 17 keypoints COCO cùng confidence. Posture analyzer dùng vai, hông và chân đủ confidence (mặc định 0,5):

- `UPRIGHT`: thân lệch phương thẳng đứng không quá 30°. Có thể bao gồm người ngồi với thân thẳng.
- `LYING`: thân lệch ít nhất 60° và một đoạn chân cùng phía lệch ít nhất 50°; xét phía còn lại nếu đủ điểm rõ.
- `UNKNOWN`: thiếu/che khuất điểm, góc chưa rõ, không có người hoặc phát hiện nhiều người. Đồ án giả định **một người tương ứng một IMU**.

| Bằng chứng | Trạng thái cuối |
|---|---|
| Đứng + sensor bình thường | `NORMAL` (hoặc chờ hồi phục nếu vừa nghi ngờ/cảnh báo) |
| Nằm + sensor bình thường | `SUSPICIOUS`; sau 1,3 giây nằm quan sát được có thông báo vàng `LYING_CHECK` và âm nhắc |
| Đứng + impact | `SUSPICIOUS` |
| Impact gần lúc bắt đầu nằm, rồi nằm đủ thời gian | `FALL_DETECTED` |
| Thiếu pose/sensor | `SUSPICIOUS`; nếu đã cảnh báo thì giữ cảnh báo |

```text
NORMAL → SUSPICIOUS → FALL_DETECTED
   ↑          │             │
   └──────────┴─────────────┘
        UPRIGHT + NORMAL ổn định 2 giây
```

Thời gian dùng đồng hồ monotonic. Xung impact giữa hai frame được giữ lại; sensor còn IMPACT thì bằng chứng được cập nhật liên tục. Bắt đầu nằm trong cửa sổ impact 5 giây rồi xác nhận 1,3 giây nằm quan sát được. `UNKNOWN` ngắn tối đa 0,6 giây tạm dừng bộ đếm; không cộng thời gian không nhìn thấy vào bằng chứng nằm. Che khuất dài hơn, tư thế không nằm hoặc gián đoạn frame quá 1,5 giây làm lại bộ đếm. Mất sensor hủy bằng chứng impact; không tự xác nhận té từ camera đơn lẻ.

`FALL_DETECTED` được giữ đến khi đứng + sensor bình thường 2 giây; mỗi sự kiện chỉ phát một cảnh báo. Nằm từ lâu rồi mới có impact ngoài cửa sổ không được xác nhận theo sự kiện đó. Cảnh báo **nằm kéo dài** là yêu cầu kiểm tra người trong hình, không phải kết luận té; nó có popup vàng và chuông lặp đến khi xác nhận. Cảnh báo té có popup đỏ và chuông lặp đến khi xác nhận. Hai loại đều ghi `alert_kind` vào log.

## Demo và kiểm thử

```powershell
.\venv\Scripts\python.exe -m unittest discover -s test -v
```

Các test dùng fixtures để kiểm tra logic, không phải bộ dữ liệu đo độ chính xác. Kiểm tra thực tế đã thực hiện ngày 30/09/2026:

| Tình huống | Kết quả |
|---|---|
| Wokwi bình thường + đứng | NORMAL |
| Wokwi impact + đứng | SUSPICIOUS |
| Wokwi chỉ gia tốc: X/Z = 2 g, gyro = 0; rồi X/Y = 0, Z = 1 g | 2,83 g / IMPACT → 1,00 g / NORMAL |
| Wokwi bình thường + nằm | SUSPICIOUS |
| Video webcam thật + impact Wokwi đúng thời điểm | FALL_DETECTED, một cảnh báo |
| Sensor không kết nối | Demo tiếp tục, SENSOR_DISCONNECTED |
| Frame trống / keypoints thiếu | UNKNOWN, không crash |

Nhánh phím `q` cho webcam/video được kiểm tra tự động với phím giả lập; các lượt demo thật cũng đã kết thúc sạch. Log console trước đây: `results/video_fusion_trial.csv`. Bản Tkinter mới đã chạy clip thật + Wokwi giữ gyro 200 từ trước: `results/gui_20260930_213837_908313.csv` có một FALL ở khoảng giây 41,7, xử lý 409 frame. Người dùng xác nhận nghe chuông và bấm xác nhận thì dừng. Các test logic/GUI dùng dữ liệu có kiểm soát; không coi chúng là cú té thật. Đây là kết quả tích hợp, chưa phải Accuracy/Precision/Recall trên bộ tình huống độc lập.

## Event log và đánh giá nhỏ

CSV mới có `timestamp` UTC, `posture`, `sensor_status`, `final_status`, `reason`, `alert_kind`. Vẫn đọc/append được log cũ 4 cột (không bổ sung cột vào file cũ). Ghi khi trạng thái cuối, tình trạng kết nối đổi hoặc có thông báo; không lưu mỗi frame. EARLY_WARNING ghi riêng, không được tính là FALL trong evaluation. File được append khi chạy lại, vì vậy mỗi tình huống đánh giá cần **một tên log mới**, bắt đầu khi người đứng và sensor bình thường. Không trộn nhiều lượt vào một log đem chấm điểm.

Điền `test_videos/evaluation.csv` sau khi chạy từng lượt và xác định nhãn thực tế theo kịch bản. Các cột:

| Cột | Nội dung |
|---|---|
| `scenario_id` | Mã duy nhất của lượt thử |
| `source` | `webcam` hoặc đường dẫn video tương đối từ thư mục manifest |
| `expected_fall` | `0` không té / `1` kịch bản té giả lập, do người đánh giá gán |
| `event_log` | Đường dẫn CSV của riêng lượt đó, tương đối từ manifest |
| `notes` | Điều kiện quay, che khuất, thời điểm điều khiển IMU |

Ví dụ cách ghi đường dẫn: `source` là `solo_transition.avi`, `event_log` là `../results/trial_02.csv`. Không tự gán nhãn chỉ vì video có người nằm. Các video hiện có chưa được gán ground truth thay bạn; manifest được để trống có chủ đích.

Chuẩn bị khoảng **10–20 tình huống**, chẳng hạn 12 lượt: 2 đứng, 2 ngồi, 2 nằm chủ động không impact, 2 cúi, 2 chuyển sang nằm kèm impact giả lập, 2 che khuất một phần. Ghi rõ đây là tình huống diễn thử. Có thể tham khảo UR Fall Detection Dataset; không cần tải dataset lớn để chạy project.

```powershell
.\venv\Scripts\python.exe python_app/evaluation.py --manifest test_videos/evaluation.csv --output results/evaluation_summary.csv
```

Mỗi lượt được dự đoán dương tính nếu log có `FALL_DETECTED`. Chương trình tính TP/FP/TN/FN, Accuracy, Precision, Recall và F1 ở **mức lượt thử**, không đo độ trễ hay accuracy từng frame. Mẫu số bằng 0 hiển thị `N/A`. Chưa có nhãn thì chương trình giải thích và không tạo điểm số.

## Cấu trúc project

```text
src/main.cpp                  Firmware STEP 14, dải gia tốc ±8 g
diagram.json, wokwi.toml       Mạch và cầu nối RFC2217
platformio.ini                Cấu hình build ESP32
python_app/sensor_reader.py    Parser, reader độc lập và reader nền
python_app/sensor_analyzer.py  Độ lớn gia tốc/gyro và NORMAL/IMPACT
python_app/pose_detector.py    YOLO11n Pose độc lập
python_app/posture_analyzer.py Quy tắc hình học từ keypoints
python_app/visual_motion.py    Cảnh báo chuyển động xuống nhanh khi pose mất dấu ngắn
python_app/fall_fusion.py      State machine có cửa sổ thời gian
python_app/main.py             Engine chung, console, event log, image
python_app/gui.py              Ứng dụng Tkinter
python_app/alerts.py           Popup và chuông, xác nhận/tắt âm
run_app.bat                    Nhấp đúp để mở ứng dụng
python_app/evaluation.py       Tổng hợp các lượt đã gán nhãn
test/                         Các kiểm thử tự động
test_videos/                  Video thật và manifest đánh giá
results/                      CSV của các lượt chạy
requirements.txt              Thư viện Python
CODEX_MASTER_PLAN.md           Checklist và lịch sử bàn giao
```

## Khắc phục nhanh

- `SENSOR_DISCONNECTED`: kiểm tra Wokwi đang chạy, đúng cổng 4000 và không có reader khác. Main tự thử kết nối lại; dữ liệu quá 0,75 giây không còn được dùng như mẫu mới.
- `UNKNOWN`: để rõ vai–hông; nằm cần thêm chân. Tránh nhiều người, hình phản chiếu hoặc vật trong nền bị model nhận nhầm thành người. Xem dòng `Pose` để biết lý do.
- Chỉ thấy SUSPICIOUS: xem lý do và tiến độ bên phải. Impact + đứng chưa đủ; LYING phải được xác nhận đủ thời gian. Sensor Wokwi không tự thay đổi theo cơ thể bạn. Với clip demo ghép Wokwi, bật ô ghép sensor và giữ gyro 200 từ trước; với camera đặt góc nhìn đủ vai/hông/chân. Nằm lâu thiếu impact vẫn có thông báo vàng, không tự chuyển thành FALL. Đứng + sensor bình thường để reset.
- Tăng gia tốc nhưng vẫn NORMAL: kiểm tra đã Build và khởi động lại Wokwi với firmware ±8 g; thử X = 2, Y = 0, Z = 2 g, gyro = 0; tổng khoảng 2,83 g. Z = 2 g đơn lẻ chưa vượt ngưỡng.
- Có popup nhưng không nghe: bật ô Âm thanh, bấm Thử chuông, kiểm tra âm lượng Windows và loa. Console cũng có tiếng nếu không dùng --no-alerts.
- Camera không mở: đóng app khác đang dùng camera, kiểm tra quyền camera, thử `--camera 1`. Trên Windows ưu tiên DirectShow, có fallback nếu mở thất bại.
- Lần đầu vision chậm: chờ tải model/khởi tạo. Model chạy CPU, không ép FPS cao.

## Hạn chế và hướng phát triển

Sensor hiện là giả lập và không thực sự đeo lên người trong các lượt demo. Riêng demo ghép IMU với video phụ thuộc thao tác đồng bộ Wokwi. Video độc lập không lấy IMU hiện tại làm bằng chứng cho clip. Ngưỡng, vị trí gắn IMU và góc camera cần hiệu chỉnh trên nhiều tình huống. Che khuất hoặc góc nhìn không thuận lợi có thể làm bỏ sót, trì hoãn hoặc báo sai. Luật thân/chân đơn giản không phân biệt được mọi tư thế; đây là **prototype học thuật, không phải thiết bị y tế**.

Có thể thay Wokwi bằng ESP32 + MPU6050 thật, giữ giao thức và đơn vị hiện tại, đổi `--port` sang cổng Serial thực tế (ví dụ `COM3`), rồi hiệu chỉnh và đánh giá lại. Khi đó cần đảm bảo người trong hình chính là người mang sensor.

Phần pretrained/sẵn có: [YOLO11 Pose của Ultralytics](https://docs.ultralytics.com/models/yolo11/), Wokwi và các thư viện. Phần tự xây là pipeline sensor, posture rules, temporal fusion, overlay/cảnh báo, logging, kiểm thử và tích hợp. Không mô tả đồ án là tự xây hoặc tự train YOLO.

## Checklist bảo vệ

| Câu hỏi | Câu trả lời ngắn cần nắm |
|---|---|
| MPU6050 là gì? | IMU gồm gia tốc kế và gyro ba trục, giao tiếp I2C với ESP32. |
| Accelerometer khác gyroscope thế nào? | Một bên đo gia tốc (g), một bên đo tốc độ quay (deg/s); không phải cùng đại lượng. |
| Sensor giả lập truyền sang Python thế nào? | ESP32 in SENSOR qua Serial 115200 baud; Wokwi mở RFC2217 cổng 4000; PySerial đọc, parse và kiểm tra sáu số. |
| YOLO Pose làm gì? | Model pretrained nhận người, bounding box và vị trí các khớp/điểm cơ thể từ ảnh. |
| Keypoint là gì? | Một điểm đặc trưng như vai, hông, đầu gối; gồm tọa độ và độ tin cậy để quyết định có dùng được không. |
| Vì sao người nằm chưa chắc té? | Có thể chủ động nghỉ/nằm; ảnh tư thế không chứng minh quá trình té hay va chạm. |
| Vì sao cần sensor fusion? | Kết hợp tư thế và chuyển động, cần bằng chứng phù hợp theo thời gian thay vì dựa vào một nguồn. |
| Ba trạng thái hoạt động thế nào? | NORMAL khi đứng và sensor bình thường; SUSPICIOUS khi có dấu hiệu/thiếu bằng chứng; FALL_DETECTED khi impact gần lúc nằm và nằm đủ thời gian. |
| Threshold lấy ở đâu? | 2 g, 150 deg/s và các cửa sổ thời gian là giá trị thử nghiệm ban đầu; cần hiệu chỉnh, không phải chuẩn y khoa. |
| Hạn chế chính? | IMU giả lập, đồng bộ thủ công, góc camera/che khuất, nhận nhầm người trong nền, một người, chưa có bộ ground truth để báo accuracy. |
| Thay bằng sensor thật thế nào? | Giữ I2C, định dạng và đơn vị; đổi RFC2217 sang cổng COM thực, gắn sensor đúng người rồi hiệu chỉnh/đánh giá lại. |
| Phần nào pretrained, phần nào tự xây? | YOLO11n Pose pretrained và Wokwi/thư viện có sẵn; sinh viên xây pipeline, luật posture, fusion, giao diện cảnh báo, log và quy trình kiểm thử. |

Trước buổi bảo vệ: build firmware, mở Wokwi, kiểm tra sensor độc lập rồi đóng reader; mở demo chính, thử một tình huống âm tính và một tình huống phối hợp có cảnh báo, chuẩn bị CSV minh chứng. Nếu demo một mình, dùng video thật `solo_transition.avi` để ngồi tại máy điều khiển Wokwi.
