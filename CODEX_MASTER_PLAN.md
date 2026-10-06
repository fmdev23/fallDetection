# CODEX_MASTER_PLAN.md

## Bổ sung hướng dẫn bảo vệ và cleanup 06/10/2026
- Đã viết HUONG_DAN_BAO_VE.md: ba bài video độc lập / webcam + Wokwi / video ghép Wokwi, từng bước và trạng thái mong đợi. README dẫn tới tài liệu này.
- Đã sao chép có kiểm tra hash hai clip gốc thành test_videos/demo_fall_01.mp4 và demo_fall_02.mp4 (tổng 3.25 MB); không chép bản quay màn hình/trùng nội dung, không sửa/xóa video gốc.
- Cleanup có giới hạn: bỏ FallFusion import không dùng trong main, trạng thái since thừa của BodyDescent, mock posture không còn tham gia pipeline; test ảnh theo đúng SceneAnalyzer. Không thêm model/dependency/kiến trúc mới, không thay ngưỡng.
- Kiểm tra sau cleanup: 50 unittest PASS. Replay cached detections solo_transition + IMU IMPACT có kiểm soát: đúng 1 FALL_DETECTED ở 41.1 s / lying 1.3 s. Không gọi đây là Wokwi live.
- Cách user đang chạy gui.py là đúng; chọn Video chỉ đọc Wokwi khi checkbox ghép được bật. Demo video độc lập không cần Wokwi và không tự kết luận FALL từ hai nguồn.


## Trạng thái hiện tại 06/10/2026 — webcam/video chung và dữ liệu có nhãn

- Yêu cầu mới của người dùng: không tối ưu riêng một clip; hỗ trợ webcam trực tiếp; chuẩn bị dữ liệu gán nhãn để học thêm. Yêu cầu mới cho phép chuẩn bị training dù mục giới hạn cũ bên dưới ghi không training. **Chưa huấn luyện/triển khai model mới.**
- [x] Dùng chung SceneAnalyzer cho webcam/video; mỗi người có lịch sử riêng. Không ghép một IMU vào nhiều người để xác nhận FALL. Video độc lập giữ mọi frame và clip clock; webcam dùng realtime.
- [x] BodyDescent nhận hạ vai/hông tương đối với chân, yêu cầu cả hạ tuyệt đối trên ảnh để giảm nhầm khi bước/nhấc chân. PoseMotion loại vùng bị cắt mép. Optical flow DIS nối ngắn mất pose, chỉ báo nguy cơ, không gán LYING/FALL giả.
- [x] 50 unittest PASS, bao gồm thời gian nằm 1.3 s, webcam/video cùng timing, tracking, IMU không gán nhầm nhiều người, chuyển động 10–30 FPS, negative pan/static/cut, dataset split và chống nhãn chồng nhau.
- [x] Model thật: hai clip gốc 783/512 frame, mỗi clip một EARLY_WARNING (~20.60 s / ~3.50 s). Người dùng đã xác nhận nhìn/nghe cảnh báo GUI ở lượt trước; không còn chờ phản hồi âm thanh đó.
- [x] 7 biến thể trên detector outputs đã lưu cho mỗi clip: cả hai bắt sự kiện ở 30/15/10 FPS, resize/mirror/speed. Clip 2 thêm cảnh báo ~13.82 s ở 10–15 FPS; chưa loại hết báo nhầm. Negative solo_lying không cảnh báo trong 7 biến thể, solo_transition có LYING_CHECK. Đây là development regression, không phải test độc lập hoặc benchmark YOLO ảnh biến đổi.
- [x] Webcam thật bản cuối: 152 frame, ~18.6 FPS, median inference ~42.3 ms; chưa thấy đủ tư thế (UNKNOWN), sensor disconnected, không có cảnh báo. Chỉ xác minh capture/pipeline, **không ghi thành test ngã webcam hay Wokwi live**.
- [x] URFD: tải 142 file nguồn, hash khớp; 70 video RGB giải mã đủ 11,936 frame; 30 fall / 40 ADL; chia theo video 42 train / 14 validation / 14 test. Nguồn + RGB 116.67 MB, không thêm model/dependency. CC BY-NC-SA 4.0, nguồn/citation trong data/urfall/README.md.
- [x] Giữ 11,544 nhãn depth gốc, không dùng depth features cho webcam RGB. 18 chuỗi thiếu/khác số frame được đánh dấu; 52 chuỗi khớp count vẫn chưa xác minh RGB frame alignment. ADL thiếu cột accel để trống. Nhãn cả chuỗi dùng được cho thí nghiệm fall/non-fall; không gán toàn video là falling.
- [x] Thêm label_videos.bat + tools/label_video.py: rà video, gán khoảng frame, reviewer/hash, chống chồng nhau, hoàn tác; Tk thực open/seek/save/undo/close PASS với file tạm. Không tự nhận dự đoán model thành ground truth.
- [ ] Chưa có nhãn chi tiết toàn bộ walking/sitting/bending/squatting/lying_down_deliberately đã rà soát độc lập; chưa có nhãn trước ngã; chưa có training mới hay đánh giá độc lập theo người. Không đánh dấu các mục này hoàn tất chỉ vì đã tải data hoặc unit tests đạt.
- Cách chạy: run_app.bat cho ứng dụng; Webcam dùng camera thật, Video mặc định không cần Wokwi. label_videos.bat cho gán nhãn. Hướng dẫn mới nhất: README.md và data/urfall/README.md.
- Minh chứng bản cuối: results/video_review/final_model_audit.json, final_webcam.json, *variants.json; data/urfall/audit.json, manifest.csv, provenance.json. Các log/ảnh chẩn đoán cũ giữ để đối chiếu, không coi là kết quả bản mới nhất.
- Firmware và cấu hình Wokwi không đổi phiên này. Không cần yêu cầu người dùng té thật; thiếu dữ liệu huấn luyện/đánh giá không được thay bằng bảo đảm phát hiện mọi cú té.

## Cập nhật mới nhất 05/10/2026 — sửa bỏ sót clip upload
- Đã đọc result-vid1.mp4 (quay màn hình) và clip gốc 1791207553755_7475990038420026036_g806362387283209796.mp4.
- Nguyên nhân: pose/box mất dấu khi ngã, không có LYING; vòng video bỏ frame để bám Wokwi. Không sửa bằng cách giả định UNKNOWN là té.
- Đã thêm VisualMotion optical flow có giới hạn/lọc nhiễu, video-only mặc định giữ đủ frame theo clip clock, checkbox ghép Wokwi explicit. GUI phân biệt mất nhận diện với nhiều người, có tổng số cảnh báo cuối lượt.
- Kiểm tra GUI: đủ 783 frame, một EARLY_WARNING ở khoảng 20.63 s; đã lọc cảnh báo thừa gần mép dưới ở lượt đầu. 38/38 tests PASS. Không tải model/dependency mới.
- Minh chứng chi tiết: results/video_review/diagnosis.md, gui_verified.json; log results/gui_20261005_211016_142821.csv.
- Cách chạy: đóng bản app cũ → run_app.bat → Video → chọn clip gốc → để ô ghép Wokwi trống → Bắt đầu. Video-only không cần Wokwi.
- Nội dung bên dưới giữ lịch sử các bản trước; thông số/chế độ mới nhất theo README và mục này.


## 0. MASTER PROMPT — DÁN NGUYÊN KHỐI NÀY VÀO CODEX WORK

Bạn đang làm việc trực tiếp trên toàn bộ project **FallDetection** đã được import vào Codex Work.

### Bối cảnh hiện tại
Project là đồ án nhỏ học phần **Xử lý ảnh / Nhận dạng**, mục tiêu:

> **Xây dựng hệ thống phát hiện và cảnh báo té ngã bằng nhận dạng tư thế kết hợp cảm biến IMU MPU6050 giả lập.**

Phần cảm biến hiện đã chạy được đến **STEP 14**:
- ESP32 + MPU6050 giả lập trên Wokwi hoạt động.
- Wokwi chạy trong VS Code.
- ESP32 gửi Serial dạng:
  `SENSOR,ax,ay,az,gx,gy,gz`
- Python kết nối Wokwi qua:
  `rfc2217://localhost:4000`
- `python_app/sensor_reader.py` đọc được dữ liệu thật từ Wokwi.
- Khi thay đổi Acceleration/Rotation trên MPU6050 trong Wokwi, dữ liệu Python thay đổi đúng.
- Python đã tính được `Accel Total` và `Gyro Total`.
- Không được phá hỏng phần đang chạy này.

### Mục tiêu cuối
Hoàn thiện một hệ thống vừa và nhỏ nhưng demo tốt, dễ bảo vệ:
1. Đọc cảm biến MPU6050 giả lập.
2. Phân tích cảm biến thành `NORMAL` / `IMPACT`.
3. Dùng **YOLO11n Pose pretrained**, không train từ đầu.
4. Nhận skeleton/keypoints người từ webcam hoặc video.
5. Phân tích tư thế thành tối thiểu `UPRIGHT`, `LYING`, `UNKNOWN`.
6. Kết hợp Vision + Sensor bằng state machine:
   - `NORMAL`
   - `SUSPICIOUS`
   - `FALL_DETECTED`
7. Cảnh báo khi có bằng chứng hợp lý từ cả tư thế và cảm biến.
8. Hiển thị trực quan skeleton, trạng thái tư thế, sensor, trạng thái cuối.
9. Hỗ trợ:
   - webcam là demo chính;
   - video file là chế độ test;
   - ảnh chỉ dùng kiểm tra tư thế, KHÔNG kết luận “té ngã” từ một ảnh tĩnh.
10. Có README, requirements, hướng dẫn chạy và checklist bảo vệ.

### Giới hạn phạm vi — TUYỆT ĐỐI KHÔNG OVERKILL
Không tự ý thêm:
- database;
- đăng nhập/phân quyền;
- Docker;
- cloud;
- mobile app;
- MQTT nếu không thật sự cần;
- IoT dashboard online;
- SMS/email;
- GPS;
- LLM/chatbot;
- training model mới;
- dataset hàng GB;
- nhiều model cùng lúc;
- microservices;
- TensorRT;
- kiến trúc phức tạp ngoài yêu cầu.

Giữ project ở mức **đồ án môn học vừa/nhỏ, đủ WOW, dễ giải thích và dễ chạy trên máy trung bình/yếu**.

### Nguyên tắc làm việc
1. **Đọc toàn bộ cấu trúc project trước khi sửa.**
2. Không đoán tên file; kiểm tra file thật.
3. Không xóa hoặc viết lại phần Wokwi/sensor đang hoạt động nếu không cần.
4. Mỗi TASK phải:
   - kiểm tra đầu vào;
   - sửa/code;
   - chạy test tối thiểu;
   - chỉ đánh dấu `[x]` khi test đạt;
   - cập nhật mục `PROGRESS / HANDOFF` ở cuối file này.
5. Hoàn thành TASK hiện tại rồi tự chuyển sang TASK kế tiếp.
6. Nếu gặp lỗi:
   - ưu tiên sửa lỗi;
   - không bỏ qua để chạy sang task khác.
7. Không tạo file rác, demo thừa, code duplicate, notebook, ảnh/video giả không cần thiết.
8. Ưu tiên code dễ đọc, tên biến rõ ràng, comment vừa đủ bằng tiếng Việt hoặc tiếng Anh đơn giản.
9. Nếu cần cài thư viện, cập nhật `requirements.txt`.
10. Nếu một thư viện nặng/khó cài có thể tránh được thì chọn cách nhẹ hơn.

### QUY TẮC QUOTA / HANDOFF — RẤT QUAN TRỌNG
Bạn phải tự làm việc theo từng **atomic task**.

Sau MỖI task:
- cập nhật checkbox;
- ghi file nào đã sửa;
- ghi lệnh đã test;
- ghi kết quả;
- ghi task kế tiếp.

Nếu nhận thấy phiên làm việc, quota, context hoặc tool budget có nguy cơ gần giới hạn:
1. KHÔNG bắt đầu task lớn mới.
2. Hoàn tất hoặc rollback phần task đang dở để project ở trạng thái chạy được.
3. Cập nhật đầy đủ `PROGRESS / HANDOFF` trong file này.
4. Ghi chính xác:
   - task cuối đã hoàn thành;
   - task đang dở nếu có;
   - lỗi còn lại;
   - lệnh cần chạy tiếp;
   - file cần mở tiếp;
   - bước tiếp theo.
5. Dừng lại an toàn để một Codex/Agent khác có thể tiếp tục **không cần suy đoán**.

Không cố “làm thêm cho đủ quota”. Không mở rộng scope ngoài checklist.

---

# 1. KIẾN TRÚC MỤC TIÊU

```text
MPU6050 giả lập (Wokwi)
        ↓
ESP32
        ↓
Serial RFC2217 localhost:4000
        ↓
Python Sensor Reader
        ↓
Sensor Analyzer
NORMAL / IMPACT
        │
        │
        ├──────────────────────┐
        │                      │
        │                  Camera / Video
        │                      ↓
        │                 YOLO11n Pose
        │                      ↓
        │              Posture Analyzer
        │         UPRIGHT / LYING / UNKNOWN
        │                      │
        └──────────┬───────────┘
                   ↓
             Fusion Logic
    NORMAL / SUSPICIOUS / FALL_DETECTED
                   ↓
        Overlay + Alert + Event Log
```

---

# 2. CẤU TRÚC PROJECT MỤC TIÊU

Không bắt buộc đổi nếu project hiện tại đã có cấu trúc hợp lý. Chỉ tạo phần còn thiếu.

```text
FallDetection/
│
├── diagram.json
├── wokwi.toml
├── platformio.ini
├── requirements.txt
├── README.md
├── CODEX_MASTER_PLAN.md
│
├── src/
│   └── main.cpp
│
├── python_app/
│   ├── sensor_reader.py
│   ├── sensor_analyzer.py
│   ├── pose_detector.py
│   ├── posture_analyzer.py
│   ├── fall_fusion.py
│   ├── main.py
│   └── evaluation.py          # chỉ tạo nếu thật sự cần
│
├── test_videos/               # có thể rỗng
└── results/                   # log/kết quả, không sinh file rác
```

Nếu có thể đơn giản hơn mà vẫn rõ ràng, được phép giữ ít file hơn.

---

# 3. TASK CHECKLIST

## TASK 0 — Audit project và khóa baseline
- [x] Đọc cấu trúc project.
- [x] Xác định chính xác các file Wokwi/ESP32/Python hiện có.
- [x] Kiểm tra `sensor_reader.py` hiện đang đọc được RFC2217.
- [x] Không sửa phần chạy tốt nếu chưa cần.
- [x] Ghi baseline vào `PROGRESS / HANDOFF`.

### Acceptance
- Biết chính xác project hiện có gì.
- Không làm hỏng STEP 14.

---

## TASK 1 — Hoàn thiện phân tích cảm biến
Mục tiêu: từ `ax ay az gx gy gz` tạo trạng thái sensor đơn giản.

### Yêu cầu
- [x] Tách hoặc giữ logic hợp lý trong `python_app/sensor_analyzer.py`.
- [x] Tính:
  - `accel_total = sqrt(ax² + ay² + az²)`
  - `gyro_total = sqrt(gx² + gy² + gz²)`
- [x] Có ngưỡng cấu hình ban đầu, ví dụ:
  - accel khoảng `2.0 g`
  - gyro khoảng `150 deg/s`
- [x] Ghi rõ đây là **ngưỡng thử nghiệm**, không phải ngưỡng y khoa.
- [x] Trả về `NORMAL` hoặc `IMPACT`.
- [x] Không spam terminal quá mức.
- [x] Test bằng cách thay đổi MPU6050 trong Wokwi.

### Acceptance
- Bình thường → `NORMAL`.
- Tăng gia tốc/quay mạnh → `IMPACT`.
- Wokwi → Python vẫn hoạt động.

---

## TASK 2 — Cài và test YOLO11n Pose độc lập
Mục tiêu: chưa ghép sensor, chỉ làm vision chạy chắc.

### Yêu cầu
- [x] Cập nhật `requirements.txt` tối thiểu:
  - `ultralytics`
  - `opencv-python`
  - `pyserial`
  - các dependency thật sự cần.
- [x] Dùng model nhẹ:
  `yolo11n-pose.pt`
- [x] Tạo `python_app/pose_detector.py`.
- [x] Test webcam mặc định `0`.
- [x] Vẽ skeleton/keypoints và bounding box.
- [x] Hiển thị confidence cơ bản.
- [x] Cho phép thoát bằng phím `q`.
- [x] Nếu không có webcam thì hỗ trợ video file để test.

### Acceptance
- Webcam/video hiện skeleton người ổn định.
- Không cần sensor để task này chạy.

---

## TASK 3 — Phân tích tư thế từ keypoints
Mục tiêu: phân biệt tư thế cơ bản, không xây classifier phức tạp.

### Yêu cầu
- [x] Tạo `python_app/posture_analyzer.py`.
- [x] Dùng các điểm ổn định như vai, hông, đầu gối/mắt cá khi đủ confidence.
- [x] Ước lượng hướng thân người.
- [x] Trả về tối thiểu:
  - `UPRIGHT`
  - `LYING`
  - `UNKNOWN`
- [x] Có xử lý khi keypoints thiếu/che khuất.
- [x] Không kết luận té ngã chỉ vì `LYING`.
- [x] Giữ thuật toán rule-based đơn giản, dễ giải thích.

### Acceptance
- Người đứng → phần lớn `UPRIGHT`.
- Người nằm/nghiêng ngang rõ → phần lớn `LYING`.
- Thiếu điểm → `UNKNOWN`, không crash.

---

## TASK 4 — Fusion sensor + vision
Đây là phần quan trọng nhất của đồ án.

### Yêu cầu
- [x] Tạo `python_app/fall_fusion.py`.
- [x] Không dùng luật “LYING = FALL”.
- [x] Xây state machine dễ bảo vệ:
  - `NORMAL`
  - `SUSPICIOUS`
  - `FALL_DETECTED`
- [x] Logic gợi ý:
  - `UPRIGHT + NORMAL` → `NORMAL`
  - `LYING + NORMAL` → `SUSPICIOUS`
  - `UPRIGHT + IMPACT` → `SUSPICIOUS`
  - `LYING + IMPACT` gần nhau theo thời gian → nghi ngờ mạnh
  - nếu sau impact người vẫn `LYING` trong khoảng thời gian cấu hình → `FALL_DETECTED`
- [x] Dùng timestamp/window đơn giản.
- [x] Tránh cảnh báo lặp liên tục.
- [x] Có reset về NORMAL khi trạng thái ổn định lại.

### Acceptance
- Sensor hoặc Vision đơn lẻ không dễ gây báo động sai.
- Hai nguồn phù hợp nhau → `FALL_DETECTED`.
- Logic dễ trình bày bằng sơ đồ.

---

## TASK 5 — Tạo chương trình demo chính `main.py`
Mục tiêu: 1 lệnh chạy được project.

### File mục tiêu
`python_app/main.py`

### Yêu cầu
- [x] Chế độ chính: webcam + sensor Wokwi.
- [x] Chế độ phụ: video file + sensor.
- [x] Có CLI đơn giản, ví dụ:
  - `python python_app/main.py --source webcam`
  - `python python_app/main.py --source video --path test_videos/fall.mp4`
- [x] Overlay lên frame:
  - skeleton;
  - posture;
  - accel total;
  - gyro total;
  - sensor status;
  - final status.
- [x] `FALL_DETECTED` phải nổi bật.
- [x] Nhấn `q` để thoát sạch.
- [x] Nếu sensor mất kết nối, không crash; hiển thị `SENSOR_DISCONNECTED`.
- [x] Nếu camera lỗi, báo rõ và thoát sạch.

### Acceptance
Một người xem demo phải hiểu ngay:
“camera nhìn tư thế + sensor phát hiện chuyển động + hệ thống kết hợp để cảnh báo”.

---

## TASK 6 — Event log tối thiểu
Không dùng database.

### Yêu cầu
- [x] Chỉ log khi trạng thái quan trọng thay đổi.
- [x] Có thể ghi CSV đơn giản vào `results/events.csv`.
- [x] Tối thiểu:
  - timestamp;
  - posture;
  - sensor_status;
  - final_status.
- [x] Không ghi từng frame để tránh file rác.
- [x] Không log vô hạn dữ liệu sensor.

### Acceptance
- Có bằng chứng kết quả để đưa vào báo cáo.
- File log nhỏ và dễ đọc.

---

## TASK 7 — Chế độ ảnh tĩnh an toàn về mặt học thuật
Ảnh tĩnh không chứng minh được “quá trình té”.

### Yêu cầu
- [x] Nếu hỗ trợ image:
  - chỉ hiển thị skeleton;
  - chỉ kết luận `UPRIGHT / LYING / UNKNOWN`;
  - ghi rõ: `Ảnh tĩnh chỉ đánh giá tư thế, không đủ dữ liệu để kết luận té ngã`.
- [x] Không ép image vào fusion sensor.

### Acceptance
- Không có claim sai về fall detection từ một ảnh.

---

## TASK 8 — Kiểm thử end-to-end
### Test bắt buộc
- [x] Wokwi NORMAL + người đứng → NORMAL.
- [x] Wokwi IMPACT + người đứng → SUSPICIOUS, không báo té ngay.
- [x] Wokwi NORMAL + người nằm → SUSPICIOUS.
- [x] Wokwi IMPACT + người chuyển/nằm → FALL_DETECTED sau khoảng giữ trạng thái.
- [x] Sensor disconnect → app không crash.
- [x] Không có người trong frame → app không crash.
- [x] Keypoints thiếu → UNKNOWN.
- [x] `q` thoát sạch webcam/video.

### Không cần
- hàng trăm test unit;
- CI/CD;
- benchmark GPU phức tạp.

---

## TASK 9 — Evaluation nhỏ, vừa đủ báo cáo
Không train model, không cần dataset lớn.

### Yêu cầu
- [x] Nếu project có sẵn video test thì dùng chúng.
- [x] Nếu chưa có, chuẩn bị framework đánh giá để người dùng bỏ video vào `test_videos/`.
- [x] Khuyến nghị 10–20 tình huống:
  - đứng;
  - ngồi;
  - nằm chủ động;
  - cúi;
  - giả lập té;
  - che khuất một phần.
- [x] Tổng hợp:
  - TP;
  - FP;
  - TN;
  - FN;
  - Accuracy/Precision/Recall/F1 nếu đủ ground truth.
- [x] Không tự bịa kết quả đánh giá.
- [x] Không tự download dataset lớn nếu chưa cần.

### Dataset tham khảo
Có thể ghi trong README/báo cáo:
- UR Fall Detection Dataset là nguồn tham khảo phù hợp.
Nhưng không bắt buộc tải để project chạy.

---

## TASK 10 — README hoàn chỉnh, dễ bảo vệ
### README phải có
- [x] Tên đề tài.
- [x] Mục tiêu.
- [x] Kiến trúc hệ thống.
- [x] Giải thích ESP32, MPU6050, accelerometer, gyroscope bằng ngôn ngữ dễ hiểu.
- [x] Vì sao dùng sensor + camera.
- [x] Vì sao không dùng chỉ camera.
- [x] Cách cài.
- [x] Cách chạy Wokwi.
- [x] Cách chạy Python.
- [x] Cách demo.
- [x] Cấu trúc project.
- [x] Ý nghĩa các trạng thái.
- [x] Hạn chế:
  - sensor đang giả lập;
  - threshold cần hiệu chỉnh;
  - pose phụ thuộc góc camera/che khuất;
  - đây là prototype học thuật, không phải thiết bị y tế.
- [x] Hướng phát triển:
  - thay Wokwi bằng ESP32 + MPU6050 thật.

### Không viết
- quảng cáo;
- claim “100% chính xác”;
- claim “đảm bảo cứu người”;
- lý thuyết dài dòng.

---

## TASK 11 — Checklist bảo vệ
Tạo cuối README hoặc một section gọn trong file này.

Phải trả lời được:
- [x] MPU6050 là gì?
- [x] Accelerometer khác Gyroscope thế nào?
- [x] Sensor giả lập được truyền sang Python bằng cách nào?
- [x] YOLO Pose làm gì?
- [x] Keypoint là gì?
- [x] Vì sao người nằm chưa chắc là té?
- [x] Vì sao cần sensor fusion?
- [x] `NORMAL / SUSPICIOUS / FALL_DETECTED` hoạt động thế nào?
- [x] Threshold sensor lấy ở đâu?
- [x] Hạn chế của mô hình?
- [x] Nếu có sensor thật thì thay thế thế nào?
- [x] Phần nào là pretrained, phần nào là phần sinh viên tự xây?

---

## TASK 12 — Final audit, dọn project và khóa scope
### Bắt buộc
- [x] Chạy lại end-to-end.
- [x] Không còn import thừa.
- [x] Không có hard-code path cá nhân.
- [x] Không có file test rác.
- [x] Không commit model nặng nếu không cần.
- [x] `requirements.txt` đúng.
- [x] README đúng lệnh chạy thật.
- [x] Không có TODO quan trọng chưa xử lý.
- [x] Không thêm tính năng ngoài scope.
- [x] Cập nhật `PROGRESS / HANDOFF` thành hoàn tất.

### Definition of Done
Project chỉ được coi là hoàn thành khi:
1. Sensor Wokwi → Python hoạt động.
2. YOLO Pose webcam/video hoạt động.
3. Posture analyzer hoạt động.
4. Fusion hoạt động.
5. Demo chính chạy bằng 1 lệnh Python rõ ràng.
6. Có alert trực quan.
7. Có log tối thiểu.
8. Có README.
9. Có checklist bảo vệ.
10. Không có phần thừa/overkill.

---

# 4. TIÊU CHÍ KỸ THUẬT NÊN GIỮ

## Sensor
- Wokwi MPU6050.
- ESP32.
- RFC2217 port 4000.
- Data:
  `SENSOR,ax,ay,az,gx,gy,gz`

## Vision
- `yolo11n-pose.pt`
- Ưu tiên CPU-friendly.
- Webcam resolution vừa phải, ví dụ 640x480.
- Không ép FPS cao.

## Fusion
Rule-based + temporal state machine.

Không cần ML thứ hai.

## UI
Ưu tiên OpenCV overlay ổn định.
Chỉ dùng Streamlit nếu sau khi core hoàn chỉnh và việc thêm UI không làm tăng rủi ro.

**Không bắt buộc Streamlit để hoàn thành đồ án.**

---

# 5. PHẦN “WOW” VỪA ĐỦ

WOW đến từ:
- skeleton chạy real-time;
- sensor thay đổi trên Wokwi và Python nhận ngay;
- sensor + vision cho hai nguồn bằng chứng khác nhau;
- state machine chuyển:
  `NORMAL → SUSPICIOUS → FALL_DETECTED`;
- cảnh báo trực quan;
- có thể chứng minh vì sao một người chủ động nằm xuống không giống một cú té có impact.

Không cần thêm tính năng khác để tạo WOW.

---

# 6. PHẦN CỦA SINH VIÊN

Khi bảo vệ, mô tả chính xác:

### Có sẵn / pretrained
- YOLO11n Pose.
- Wokwi ESP32/MPU6050 simulator.
- Thư viện OpenCV, Ultralytics, PySerial.

### Tự xây
- pipeline đọc sensor;
- chuẩn hóa dữ liệu sensor;
- sensor analyzer;
- posture analyzer;
- thuật toán fusion;
- temporal state machine;
- cảnh báo;
- overlay;
- event logging;
- quy trình test/evaluation;
- tích hợp tất cả thành một hệ thống.

Không nói “em xây YOLO”.

---

# 7. PROGRESS / HANDOFF

> Codex phải cập nhật phần này sau mỗi TASK.  
> Không xóa lịch sử quan trọng; chỉ giữ ngắn gọn và đủ để Agent khác tiếp tục.

## Yêu cầu mới nhất — HOÀN TẤT tối ưu cảnh báo sớm và độ trễ

- [x] Cảnh báo IMU riêng với Tkinter, không chờ vòng xử lý ảnh; đọc gia tốc, gyro và biến thiên gia tốc. Firmware gửi khoảng 20 ms/mẫu.
- [x] Cảnh báo camera khi thân nghiêng nhanh qua nhiều mẫu; không giả định dự đoán chắc chắn té.
- [x] Nhắc nằm và xác nhận nằm mặc định 1.3 s; popup/chuông lặp, giao diện nháy khi nguy cơ còn hoạt động; ưu tiên FALL hơn cảnh báo sớm.
- [x] Giảm kích thước inference 640 → 480, giữ một model; so sánh trên clip thật trước khi đổi.
- [x] 34 tests PASS, có test cảnh báo đến Tkinter trước frame đầu khi vision bị chậm; build firmware SUCCESS.
- [x] Test thật GUI/Wokwi gyro 120: người dùng xác nhận thấy cảnh báo sớm; log gui_20260930_221108_024870.csv.
- [x] Replay clip thật + sensor NORMAL có kiểm soát: LYING_CHECK sau 1.324 s quan sát nằm, 0 FALL; cập nhật hướng dẫn Tkinter.

Các phần TASK 0–12 và yêu cầu bổ sung trước ở dưới là lịch sử, không phải thông số mặc định mới nhất. Không có cam kết bắt mọi cú té hay accuracy chưa đo.

## Bản console trước khi có yêu cầu bổ sung — TASK 0–12 (2026-09-30)

- Project đang làm: FallDetection trong workspace hiện tại; master plan gốc và bản trong project đã đồng bộ.
- Last completed task: TASK 12. Task đang dở: KHÔNG. Lỗi chặn còn lại: KHÔNG.
- Test cuối: 20/20 unittest PASS; pip check PASS; compileall PASS; kiểm tra import/path/TODO PASS; SHA256 firmware và cấu hình Wokwi không đổi.
- End-to-end dương tính: video webcam thật + Wokwi impact → FALL_DETECTED, một cảnh báo, 398 frames, exit 0. Log: results/video_fusion_trial.csv.
- End-to-end đối chứng cuối: cùng video + sensor NORMAL → LYING/SUSPICIOUS, không cảnh báo, 390 frames, exit 0. Log: results/final_audit.csv.
- Demo: mở Wokwi rồi chạy `venv\Scripts\python.exe python_app/main.py --source webcam`.
- Demo một mình: `venv\Scripts\python.exe python_app/main.py --source video --path test_videos/solo_transition.avi --log results/trial_02.csv`; tạo impact khoảng giây video 38–39.
- File cần đọc: README.md (hướng dẫn và 12 câu hỏi bảo vệ).
- Chưa có bộ ground truth 10–20 tình huống, chưa có số liệu Accuracy/Precision/Recall/F1 thực nghiệm. Framework sẵn sàng; đây là bước thu thập dữ liệu tự chọn sau khi hoàn thành tích hợp, không bịa nhãn/kết quả.
- Hạn chế đã ghi rõ: IMU giả lập, một người, góc camera/che khuất, nhiều người giả do nền có thể làm UNKNOWN; q được kiểm thử bằng mock; không claim ảnh tĩnh chứng minh té.
- Next task: KHÔNG còn task triển khai bắt buộc. Nếu đánh giá thêm, gán nhãn từng lượt trong test_videos/evaluation.csv và chạy evaluation.py.
- Safe to hand off: YES — không còn tiến trình demo do tác vụ này cần giữ chạy.

## Trạng thái ban đầu trước khi Codex chạy
- STEP 14: ✅ Hoàn thành.
- ESP32 + MPU6050 trên Wokwi: ✅
- RFC2217 `localhost:4000`: ✅
- Python đọc `SENSOR,...`: ✅
- Thay đổi sensor trên Wokwi phản ánh ở Python: ✅
- `Accel Total` và `Gyro Total`: ✅
- TASK tiếp theo: **TASK 0 audit → TASK 1 sensor analyzer**

## Cập nhật bởi Codex

### 2026-09-30 — TASK 0 hoàn thành
- Đã đọc toàn bộ mã nguồn/cấu hình do sinh viên quản lý, README mẫu PlatformIO và cấu trúc thư mục; không coi venv/.pio là mã nguồn sinh viên.
- Project thực tế: src/main.cpp, python_app/sensor_reader.py, diagram.json, wokwi.toml, platformio.ini; chưa có vision, fusion, README chính hay requirements. Không có Git repository, không có AGENTS.md áp dụng.
- Firmware gửi g và deg/s, 115200 baud, chu kỳ 100 ms; giữ nguyên firmware và cấu hình Wokwi.
- Môi trường hiện tại: venv Python 3.14.3, pyserial 3.5.
- Test: PlatformIO `platformio run` PASS; đọc RFC2217 localhost:4000 nhận 5 dòng SENSOR hợp lệ; chạy sensor_reader.py gốc có Status: NORMAL (dừng tiến trình kiểm thử sau 4 giây).
- Các mẫu hiện tại đều bằng 0; đây là giá trị đang mô phỏng, chưa xác nhận phản ứng khi chỉnh MPU6050 trong phiên này.
- SHA256 baseline:
  - src/main.cpp: D0E81B8D114A45711B1DA60E61D5DB40684CEA6E3E04669AD4217813283D8BA3
  - diagram.json: 724898A63455ED1AD72535E9E85E309AD5BBAE0C282115C0C2032F63A7A68CF0
  - platformio.ini: 18A697CC6A8CC695ECE3AF6340789BA52199ABF6B3602FC96B38F28292103D02
  - wokwi.toml: B79B0C84AD3EC4F56C68F2171EDF7922FD45F6AF55A71C9E15739C2EB33BEFEA
  - python_app/sensor_reader.py (trước sửa): 1FBBFD2C806DD0178CC247464FC65421CEE4EF028283AA3A28F691CF5EFFEF81
- Files changed: CODEX_MASTER_PLAN.md (bản gốc và bản trong project).
- Last completed task: TASK 0.
- Current issue: chưa có lỗi baseline; cần test thay đổi sensor trực tiếp cho TASK 1.
- Next task: TASK 1 — tách analyzer và giữ reader tương thích.
- Exact next action: tạo python_app/sensor_analyzer.py, kiểm thử logic và dữ liệu Wokwi.
- Safe to hand off: YES.

### 2026-09-30 — TASK 1 đang kiểm thử trực tiếp
- Files changed: python_app/sensor_analyzer.py, python_app/sensor_reader.py, test/test_sensor.py.
- Reader giữ giao thức/baudrate/URL; thêm main guard, parser bỏ dữ liệu lỗi/nonfinite, đóng serial bằng context manager, hiển thị mất dữ liệu, CLI ngưỡng và --duration, giới hạn in 1 lần/giây ngoài lúc đổi trạng thái.
- Tests: `venv\Scripts\python.exe -m unittest discover -s test -v` PASS 4/4.
- `venv\Scripts\python.exe python_app/sensor_reader.py --duration 4` PASS, Wokwi nhận NORMAL.
- Current issue: chờ test thay đổi Rotation X=200 rồi 0; Acceleration Z=2.5 rồi 1 trực tiếp trên Wokwi. Chưa đánh dấu test này đạt, chưa bắt đầu TASK 2.
- Next action: đọc kết quả phiên reader 120 giây; xác nhận NORMAL → IMPACT → NORMAL cho cả gyro và accel.
- Safe to hand off: YES; reader vẫn chạy độc lập bằng lệnh cũ.

### 2026-09-30 — TASK 1 hoàn thành
- Live test `venv\Scripts\python.exe python_app/sensor_reader.py --duration 120`: gyro thay đổi 0 → 240/204.99 → 144.99/130 deg/s; trạng thái NORMAL → IMPACT → NORMAL đúng. Đã xác nhận phản ứng trên Wokwi thật, không dùng dữ liệu giả thay thế.
- Nhánh accel đã kiểm bằng unit test (2.1 g IMPACT; đúng 2.0 g NORMAL); chưa đo riêng nhánh accel bằng thao tác Wokwi. Tiêu chí thay đổi MPU6050 đã đạt qua nhánh gyro.
- Test cổng không hoạt động: --port rfc2217://localhost:49999 --duration 2 → exit 1, SENSOR_DISCONNECTED, không traceback.
- SHA256 firmware/cấu hình Wokwi khớp baseline.
- Last completed task: TASK 1. Next task: TASK 2 — kiểm tra dependency, tạo pose detector độc lập, test webcam/video.
- Current issue: không có lỗi TASK 1. Safe to hand off: YES.

### 2026-09-30 — TASK 2 đang triển khai
- Files changed: requirements.txt, .gitignore, python_app/pose_detector.py.
- Đã tạo detector YOLO11n Pose CPU, model yolo11n-pose.pt, webcam/video CLI, plot skeleton/bbox/confidence, q/đóng cửa sổ, release capture.
- Tests: py_compile và --help PASS; OpenCV mở webcam 0 và đọc frame 640x480 PASS.
- Đang cài `venv\Scripts\python.exe -m pip install -r requirements.txt`; chưa ghi cài đặt/inference thành công khi tiến trình chưa kết thúc.
- Sensor live bổ sung: 1.00 g, 0 deg/s → NORMAL.
- Next action: pip check; chạy `venv\Scripts\python.exe python_app/pose_detector.py --source webcam --duration 20`, kiểm tra skeleton thực tế. Chưa bắt đầu TASK 3.

### 2026-09-30 — TASK 2 hoàn thành
- `venv\Scripts\python.exe -m pip install -r requirements.txt` PASS; `-m pip check` PASS.
- `venv\Scripts\python.exe python_app/pose_detector.py --source webcam --duration 20` PASS: 162 frames, 162 frames có người, cửa sổ skeleton/bbox/confidence chạy, exit 0 và giải phóng webcam.
- YOLO11n Pose pretrained tải từ Ultralytics (~6 MB), được .gitignore loại khỏi commit; inference CPU.
- Files changed: requirements.txt, .gitignore, python_app/pose_detector.py, hai bản master plan.
- Last completed task: TASK 2. Next: TASK 3 — posture analyzer + test đủ/thiếu keypoints. Safe to hand off: YES.
- Video file được hỗ trợ qua --source video --path; project chưa có video thực để đánh giá. Test thao tác q trực tiếp để lại cho TASK 8.

### 2026-09-30 — TASK 3 hoàn thành phần logic
- Files changed: python_app/posture_analyzer.py, test/test_posture.py.
- `venv\Scripts\python.exe -m unittest discover -s test -v` PASS 8/8 tổng cộng, gồm đứng/nằm/cúi/che khuất/keypoints lỗi.
- Rule: torso lệch dọc <=30° UPRIGHT; torso >=60° và chân >=50° LYING; còn lại UNKNOWN. Cần ít nhất cặp vai-hông cùng phía đủ confidence; LYING cần đầu gối/mắt cá.
- Nhiều người → UNKNOWN vì chỉ có một IMU, không tự gán IMU cho người bất kỳ.
- Đây là test hình học bằng dữ liệu kiểm thử, không phải accuracy trên video thật. Kiểm tra tư thế webcam thực tế thuộc TASK 8.
- Last completed task: TASK 3 (implementation + unit tests). Next: TASK 4. Safe to hand off: YES.

### 2026-09-30 — TASK 4 hoàn thành
- Files changed: python_app/fall_fusion.py, test/test_fusion.py.
- Test: `venv\Scripts\python.exe -m unittest discover -s test -v` PASS 13/13.
- Fusion mặc định: impact trong 3 s quanh lúc bắt đầu LYING; giữ LYING 2 s sau bằng chứng muộn hơn; hồi phục UPRIGHT+NORMAL 2 s; gián đoạn frame >1 s hủy đếm liên tục.
- Test phủ nguồn đơn lẻ, impact hết hạn, người đã nằm từ lâu, mất sensor/che khuất/frame gap, xung impact giữa hai frame, alert một lần và reset.
- Last completed task: TASK 4. Next: TASK 5 — reader nền + demo tích hợp. Safe to hand off: YES.

### 2026-09-30 — TASK 5 hoàn thành
- Files changed: python_app/main.py, python_app/sensor_reader.py (SensorStream nền và snapshot có timeout).
- Live `venv\Scripts\python.exe python_app/main.py --source webcam --duration 12`: exit 0, sensor NORMAL, posture UNKNOWN vì thiếu vai/hông, final SUSPICIOUS; đóng sạch.
- Live `venv\Scripts\python.exe python_app/main.py --source webcam --port rfc2217://localhost:49999 --duration 6`: 39 frames, SENSOR_DISCONNECTED, không crash, exit 0.
- Kiểm tra camera mở thất bại bằng mock: thông báo rõ + release PASS. Reader mất kết nối: snapshot đúng + thread dừng sạch PASS.
- Timing detector trực tiếp: frame đầu 2.34 s; các frame tiếp theo 0.15/0.09/0.09 s. Không benchmark accuracy.
- Video bỏ frame khi cần để giữ gần thời gian thực, dùng cùng monotonic clock với IMU; video và Wokwi phải được thao tác đồng bộ khi test.
- Last completed task: TASK 5. Next: TASK 6 CSV event log. Safe to hand off: YES.

### 2026-09-30 — TASK 6 hoàn thành
- Files changed: python_app/main.py (EventLogger, --log), test/test_events.py.
- `venv\Scripts\python.exe -m unittest discover -s test -v` PASS 14/14.
- CSV timestamp UTC, posture, sensor_status, final_status; ghi lúc final status hoặc kết nối thay đổi, không ghi mỗi frame/dao động posture.
- Test 100 frame trạng thái lặp không thêm dòng; append không lặp header; 5 chuyển đổi quan trọng → 5 dòng. Test dùng thư mục tạm tự dọn.
- Last completed task: TASK 6. Next: TASK 7 — image posture-only. Safe to hand off: YES.

### 2026-09-30 — TASK 7 hoàn thành
- Files changed: python_app/main.py (image mode), test/test_image.py.
- Test `venv\Scripts\python.exe -m unittest discover -s test -v` PASS 15/15 sau sửa stdout UTF-8 trên Windows.
- Test chứng minh --source image không tạo SensorStream, FallFusion hoặc EventLogger, chỉ in/hiển thị tư thế và giới hạn ảnh tĩnh. Ảnh fixture chỉ nằm thư mục tạm tự dọn.
- Last completed task: TASK 7. Next: TASK 8 — tích hợp có kiểm soát và webcam/Wokwi thực tế. Safe to hand off: YES.

### 2026-09-30 — TASK 8 đang kiểm thử
- Files changed: test/test_pipeline.py; log thực results/events.csv do ứng dụng tạo.
- Automated tests: `venv\Scripts\python.exe -m unittest discover -s test -v` PASS 17/17. Pipeline có kiểm soát sensor packet → analyzer → posture → fusion → CSV đạt cả 4 tổ hợp chính. Đây là fixtures kiểm thử, không thay cho test webcam thực.
- YOLO inference trên frame trống + plot: không có người → UNKNOWN, PASS.
- Nhánh q webcam/video được test bằng phím q giả lập qua mock cv2.waitKey, cleanup PASS; không coi đây là kiểm tra bàn phím vật lý.
- Live webcam/Wokwi: đã quan sát UPRIGHT + NORMAL → NORMAL; che khuất → UNKNOWN/SUSPICIOUS và hồi phục NORMAL khi nhìn rõ.
- Đang chạy `venv\Scripts\python.exe python_app/main.py --source webcam --duration 180` để xác nhận impact/nằm và FALL_DETECTED thực tế.
- Chưa bắt đầu TASK 9; còn chờ các tình huống live theo kế hoạch.

### 2026-09-30 — TASK 8 kết quả live và giới hạn thao tác
- Live --duration 180: 1808 frames, exit 0. Live --duration 240: 2494 frames, exit 0.
- Đã quan sát UPRIGHT+IMPACT → SUSPICIOUS và LYING+NORMAL → SUSPICIOUS; chưa quan sát FALL_DETECTED live vì LYING xen kẽ UNKNOWN và thao tác impact khó đồng bộ khi chỉ có một người.
- Người dùng xác nhận chỉ có một mình, không nhìn thấy màn hình khi đứng xa. Không yêu cầu người dùng đọc overlay trong lúc đứng xa nữa.
- Sửa posture analyzer: khi phía thân có confidence cao nhất bị che chân, kiểm tra chân phía còn lại nếu torso cùng phía đủ confidence và nằm ngang; không hạ ngưỡng. Thêm regression test: PASS 18/18.
- Thêm lý do UNKNOWN vào overlay để hỗ trợ chẩn đoán.
- Chờ lựa chọn: ghi clip webcam ngắn để người dùng có thể phát lại/chỉnh Wokwi tại máy, hoặc người dùng cho phép để test live này chưa hoàn tất và tiếp tục tài liệu. Không tự đánh dấu FALL_DETECTED live đã đạt.
- Task đang dở: TASK 8; last fully implemented task TASK 7. Safe to hand off: YES.

### 2026-09-30 — TASK 8 tiếp tục sau gián đoạn quota
- Người dùng chọn ghi clip thật để test một mình; không yêu cầu đọc màn hình từ xa.
- Đã ghi test_videos/solo_posture.avi (30 s, 300 frame, 10 FPS) và solo_lying.avi (60 s, 600 frame). Đây là video webcam thật, không phải dữ liệu giả.
- Phân tích clip đầu: LYING bắt đầu khoảng 27.8 s, đoạn liên tục dài nhất 1.6 s; chưa đủ lying_hold=2 s.
- Clip thứ hai ghi trong lúc gián đoạn: chủ yếu UPRIGHT rồi người quay gần camera, không có đoạn LYING sử dụng được.
- Đang ghi clip mới test_videos/solo_transition.avi (45 s) sau khi người dùng yêu cầu tiếp tục.
- Camera Windows dùng DirectShow, fallback backend mặc định nếu mở thất bại, để giảm trễ khởi động. Main overlay video có thời gian phát giúp đồng bộ Wokwi.
- Next: phân tích solo_transition.avi, xác định thời điểm LYING, phát lại với Wokwi tạo impact đúng lúc, chỉ đánh dấu TASK 8 khi có bằng chứng live.

### 2026-09-30 — TASK 8 hoàn thành
- Video thật solo_transition.avi (45 s, 450 frames) có LYING liên tục khoảng 39.8–45.0 s (phân tích mỗi 2 frame).
- Live `venv\Scripts\python.exe python_app/main.py --source video --path test_videos/solo_transition.avi --log results/video_fusion_trial.csv`: PASS, 398 frames xử lý, exit 0; Wokwi thay đổi gyro thật; quan sát LYING+IMPACT → SUSPICIOUS → FALL_DETECTED, đúng một FALL ALERT.
- Đối chiếu CSV có đúng một dòng FALL_DETECTED. Đây là demo tư thế nằm chủ động + IMU giả lập impact, không phải bằng chứng phát hiện cú té thật hay thống kê accuracy.
- Ba tổ hợp còn lại đã quan sát qua webcam/Wokwi. Mất kết nối sensor, frame không người, keypoints thiếu và nhánh q đã được kiểm thử như ghi ở trên.
- Files changed trong TASK 8: test/test_pipeline.py, test/test_posture.py, python_app/posture_analyzer.py, python_app/pose_detector.py (DirectShow), python_app/main.py (reason/video time overlay); video webcam thật và event logs. Ảnh chẩn đoán tạm đã dọn.
- Last completed task: TASK 8. Next: TASK 9 — framework đánh giá nhỏ không bịa ground truth. Safe to hand off: YES.

### 2026-09-30 — TASK 9 hoàn thành framework đánh giá
- Files changed: python_app/evaluation.py, test/test_evaluation.py, test_videos/evaluation.csv; requirements thêm numpy dùng trực tiếp trong test.
- CLI đọc manifest do người dùng gán nhãn 0/1 và event log riêng cho từng tình huống; tổng hợp TP/FP/TN/FN, Accuracy/Precision/Recall/F1; N/A khi mẫu số bằng 0.
- Test suite PASS 20/20, bao gồm confusion matrix đã biết (fixture kiểm thử) và không có ground truth. Manifest thật hiện chỉ có header; lệnh evaluation trả exit 1 có giải thích, không tạo accuracy giả.
- Đã có 3 video thật từ các lượt thử; giữ làm dữ liệu thực, chưa gán nhãn đánh giá thay người dùng. Hướng dẫn 10–20 tình huống và cách ghi log riêng sẽ nằm trong README TASK 10.
- Last completed task: TASK 9. Next: TASK 10 README. Safe to hand off: YES.

### 2026-09-30 — TASK 10 hoàn thành
- Files changed: README.md.
- README có hướng dẫn cài/build/Wokwi/chạy 3 chế độ, kiến trúc, đơn vị, quy tắc fusion, thông số thật, demo một người bằng video, log/evaluation, hạn chế và thay sensor thật.
- Kiểm tra các ví dụ CLI bằng build_parser và kiểm tra đường dẫn file thật: PASS. Các lệnh chính đã chạy trong TASK 0–8.
- Ghi rõ chưa có accuracy thực nghiệm, tách test fixtures và video thật; không claim té thật từ ảnh hoặc từ nằm chủ động.
- Last completed task: TASK 10. Next: TASK 11 checklist bảo vệ. Safe to hand off: YES.

### 2026-09-30 — TASK 11 hoàn thành
- Files changed: README.md (12 câu hỏi/trả lời bảo vệ).
- Kiểm tra đủ 12 câu hỏi, đúng tên thành phần/đơn vị/giới hạn so với code: PASS.
- .gitignore bổ sung video thử cá nhân; giữ video thật tại máy để demo, không tự đưa vào commit.
- Last completed task: TASK 11. Next: TASK 12 final audit. Safe to hand off: YES.

### 2026-09-30 — TASK 12 hoàn thành, khóa scope
- Kiểm thử cuối: `venv\Scripts\python.exe -m unittest discover -s test -v` PASS 20/20; `-m pip check` PASS; `-m compileall -q python_app test` PASS.
- Static audit mã Python: không import thừa, không TODO/FIXME, không hard-code đường dẫn cá nhân. Cấu hình .vscode do PlatformIO tự sinh được giữ nguyên, nằm trong ignore.
- SHA256 src/main.cpp, diagram.json, platformio.ini, wokwi.toml khớp baseline TASK 0. Firmware build TASK 0 PASS và chưa bị sửa.
- Live reader sau cùng vẫn nhận SENSOR và NORMAL từ RFC2217.
- Chạy lại full video với Wokwi NORMAL: `venv\Scripts\python.exe python_app/main.py --source video --path test_videos/solo_transition.avi --log results/final_audit.csv` → 390 frames, exit 0, LYING/NORMAL chỉ SUSPICIOUS, không có FALL_DETECTED. Đối chiếu log PASS.
- Giữ 3 video webcam thật và các CSV minh chứng; không có ảnh QA tạm còn lại. Model/venv/video/log đã được .gitignore loại khỏi commit; project hiện chưa phải Git repository và không tạo commit.
- README đúng cấu trúc/lệnh thật, requirements đúng môi trường đã test. Không thêm database/cloud/training/UI framework ngoài kế hoạch.
- Last completed task: TASK 12. Current issue: không có lỗi chặn; giới hạn và việc chưa có ground truth đã nêu trong README.
- Next action: sử dụng demo hoặc thu thập/gán nhãn thêm nếu muốn đánh giá định lượng.
- Safe to hand off: YES. Trạng thái tổng: HOÀN TẤT phạm vi triển khai theo master plan.

### Bổ sung sau phản hồi người dùng — sửa SUSPICIOUS và ứng dụng Tkinter
- Files changed: fall_fusion.py, main.py (monitor_frames dùng chung), pose_detector.py (confidence người 0.5 giảm detection nền yếu), alerts.py, gui.py, run_app.bat, requirements (Pillow), test_fusion.py, test_gui.py.
- Default mới: impact_window 5 s, lying_hold 1.5 s, occlusion_grace 0.6 s, lying_warning 6 s. Sensor ngưỡng 2 g/150 deg/s giữ nguyên.
- Regression tests: 24 tests toàn suite trước test GUI PASS; thêm 2 test GUI PASS (Tk thật, inference giả lập, tắt âm để test).
- Replay model thật trên solo_transition.avi: impact giữ từ trước → FALL_DETECTED một lần ở giây 41.4; sensor NORMAL → không báo té. Sensor states trong bài này có kiểm soát, KHÔNG ghi thành test Wokwi live.
- Test popup Tk thật: không modal, xác nhận đóng, không tạo popup lặp; worker vẫn đưa sự kiện alert dù bỏ frame UI cũ.
- Next: chạy GUI thật với Wokwi, xác nhận âm thanh và cập nhật README.

### Bàn giao tiếp tục sau gián đoạn — GUI đạt, chờ test gia tốc firmware mới
- GUI + solo_transition.avi + Wokwi thật giữ gyro 200: FALL_DETECTED khoảng giây 41.7; log results/gui_20260930_213837_908313.csv, 409 frames, đúng một FALL. Người dùng xác nhận có tiếng chuông và bấm “Đã thấy — tắt chuông” thì dừng.
- Sửa src/main.cpp: đặt MPU6050_RANGE_8_G sau mpu.begin. Mặc định thư viện ±2 g có thể cắt tín hiệu một trục trước ngưỡng >2 g. Giao thức/đơn vị không đổi; diagram.json, platformio.ini, wokwi.toml không sửa.
- PlatformIO build firmware mới SUCCESS; 26/26 unittest PASS, pip check và compileall PASS. GUI giữ thông báo lỗi khi còn frame cũ trong hàng đợi. README đã cập nhật launcher, popup/chuông, các ngưỡng, loại nhắc nằm kéo dài và giới hạn thử nghiệm.
- Người dùng quay lại sau quota, xác nhận reset nhưng chưa làm test gia tốc. Hiện không có Python reader/demo đang chạy. Đang chờ mở Wokwi và đặt gyro cả ba trục = 0, acceleration X/Y = 0, Z = 3 g để đọc xác nhận; tiếp theo trả Z = 1 g. Không đánh dấu test này đạt trước khi quan sát số liệu.
- Next: đọc sensor trực tiếp, lưu minh chứng test gia tốc, hoàn tất checklist hiện tại và đồng bộ hai bản master plan. Không cần làm lại GUI/chuông đã đạt.

- Điều chỉnh hướng dẫn live: người dùng xác nhận slider Wokwi chỉ tối đa 2 g/trục. Đã đọc Z = 2 g, gyro = 0 → NORMAL đúng vì ngưỡng >2. Yêu cầu Z = 3 trước đó không khả thi với slider này. Thử thay thế X = 2, Y = 0, Z = 2 (tổng 2.83 g), sau đó trả X/Y = 0, Z = 1. Dải đo firmware ±8 g không mở rộng giới hạn slider Wokwi. Không quy toàn bộ lỗi demo trước đây cho bão hòa cảm biến; lỗi timing/occlusion đã được sửa và GUI test đạt.

### Hoàn tất yêu cầu bổ sung — kiểm tra gia tốc thật từ Wokwi
- Reader nền trực tiếp xác nhận gyro = 0, Z = 2 g → NORMAL; X = 2, Y = 0, Z = 2 g → tổng 2.83 g / IMPACT; trả X/Y = 0, Z = 1 g → tổng 1.00 g / NORMAL. Người dùng xác nhận đã thực hiện đúng các thiết lập. Không dùng mock sensor cho bài này.
- Trong lúc thao tác có các khoảng SENSOR_DISCONNECTED; reader tự kết nối/nhận lại, không dùng mẫu quá hạn. Không coi một vài lượt demo là chứng minh độ ổn định dài hạn.
- Toàn bộ checklist bổ sung đã đạt: logic thời gian, giao diện Tkinter, popup/chuông được người dùng nghe và tắt, test gia tốc/gyro, 26 tests tự động, firmware build, tài liệu và launcher.
- README hướng dẫn đúng slider Wokwi (±2 g/trục), thử gia tốc tổng bằng X/Z = 2 thay cho yêu cầu Z = 3 không khả thi. Dải ±8 g firmware giữ khả năng đọc tín hiệu lớn hơn cho phần cứng, không đổi slider mô phỏng.
- Next: dùng run_app.bat → chọn Webcam/Video → Bắt đầu. Một reader sensor tại một thời điểm. Nằm lâu thiếu impact là nhắc kiểm tra; FALL vẫn cần cả tư thế và IMU. Bộ clip diễn thử chưa chứng minh phát hiện mọi cú té hoặc accuracy thực tế.
- Safe to hand off: YES. Hai bản master plan được đồng bộ; không có hạng mục triển khai/test đã hứa còn bỏ dở.

### Tối ưu lần cuối theo yêu cầu mới — đang chốt kiểm tra
- Không tải model/tài nguyên thêm. MotionRisk đánh giá trên reader: moderate acceleration/gyro cần 80 ms, impact/jerk có điều kiện phát ngay, rearm sau 1 s yên. Snapshot/queue đưa event tới Tk mỗi 40 ms, không chờ YOLO. Stale sensor 0.75 s, không dùng mẫu cũ.
- PoseMotion xét tốc độ tăng góc thân, ít nhất 3 mẫu; cảnh báo nguy cơ riêng, không tự kết luận FALL. Lying_hold và lying_warning = 1.3 s, vẫn không cộng UNKNOWN.
- Alert priority TEST < EARLY_WARNING < LYING_CHECK < FALL, một popup/incident, nháy 400 ms, chuông lặp đến xác nhận; giao diện vẫn nháy khi nguy cơ tồn tại sau mute.
- Benchmark thật 27 frame solo_transition: 640 median 72.5 ms (13 LYING), 480 median 49.4 ms (12 LYING); cùng nhận đoạn nằm cuối. Không gọi đây là benchmark accuracy toàn hệ thống.
- Live GUI clip + Wokwi: gui_20260930_220847_599356.csv có early IMU khi chưa nằm, early camera khoảng 38.7 s, FALL khoảng 41.2 s (lying 1.33 s), 426 frames. Sensor được người dùng chỉnh trong lượt nên không suy ra toàn lượt chỉ gyro120.
- Live lượt kế tiếp gui_20260930_221108_024870.csv: EARLY_WARNING 1 g / 120 deg/s khi chưa nằm. Người dùng trả lời “Đã đặt 120, thấy cảnh báo sớm”.
- 34/34 unittest PASS, pip check PASS, PlatformIO SUCCESS. Venv 1061.93 MB là runtime hiện có, model khoảng 6 MB; giữ runtime và video/log của người dùng. Không thêm dependency.
- Tiếp: replay model thật với sensor NORMAL có kiểm soát (không đọc Wokwi) để kiểm tra LYING_CHECK, dọn cache sinh lại được và đồng bộ bàn giao.

### Chốt phiên tối ưu
- Replay solo_transition.avi bằng model thật 480, sensor NORMAL có kiểm soát: 427 frames, 1 LYING_CHECK ở video 41.2 s / nằm quan sát 1.324 s, 0 FALL, 2 early camera. Median inference 54.0 ms. Log results/optimization_lying_replay.csv. Không ghi bài sensor có kiểm soát này thành Wokwi live.
- README cập nhật 3 loại cảnh báo, ngưỡng sớm, lying 1.3 s, cách Build/Stop-Start Wokwi/run_app.bat và giới hạn. Không thêm model/dependency. Người dùng xác nhận cảnh báo sớm từ Wokwi 120 deg/s.
- Cleanup: không xóa runtime/model/video/log. Cache và artifact sinh lại đã được ignore. Công cụ từ chối xóa hai thư mục __pycache__ đã kiểm tra nằm trong workspace, với lý do blocked by policy; cache còn nguyên, không gây lỗi chạy. Không tuyên bố đã xóa chúng.
- Last completed: logic cảnh báo sớm, UI nháy/chuông, giảm trễ inference, test nằm 1.3 s, 34 tests, firmware build, README. Remaining: giới hạn xóa cache bởi công cụ; đánh giá độ chính xác/prediction trên dữ liệu có nhãn nằm ngoài các demo đã đạt. Safe to hand off: YES.

### Handoff 05/10/2026 — sửa test video upload
- Files changed: visual_motion.py (mới), main.py, gui.py, fall_fusion.py, posture_analyzer.py, test_visual_motion.py (mới), test_pipeline.py, README.md, .gitignore, master plan.
- Test thực đã qua GUI, không mock detector. Optical flow chỉ tạo EARLY_WARNING, không gán FALL cho clip không có IMU. Frame time dùng clip clock trong video-only, actual realtime giữ nguyên cho webcam/video-live-sensor.
- Firmware không đổi phiên này. Không tải model, không sao chép video nguồn; ảnh/json chẩn đoán cỡ nhỏ lưu riêng trong results/video_review và gitignored.
- Regression suite 38 PASS; test video clock bảo đảm máy chậm không kéo dài bằng chứng nằm, không skip frame. Lượt GUI cuối 783/783 frames, một cảnh báo quanh 20.63s. Chi tiết giới hạn/baseline/lượt thử có cảnh báo thừa giữ trong diagnosis.md để không nhầm với kết quả cuối.
- Còn chờ phản hồi người dùng thấy/nghe popup ở lượt mới; không cần cho người dùng té thật hoặc chỉnh Wokwi để test clip này.


### Handoff 06/10/2026
Bản triển khai và dữ liệu nền đã xác minh theo mục trạng thái đầu file. 50 tests PASS; 70 video URFD có nhãn sự kiện theo chuỗi, công cụ gán nhãn chi tiết sẵn dùng. Chưa train model mới, chưa có toàn bộ nhãn hoạt động chi tiết hoặc nhãn trước ngã. Giữ các giới hạn và false warnings đã ghi nhận; không lấy development clips làm unseen test. Hai bản master plan được đồng bộ.
