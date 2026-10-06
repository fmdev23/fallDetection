# Chạy demo bảo vệ FallDetection

## 1. Mở ứng dụng

Mở project `C:\Users\PC\Documents\PlatformIO\Projects\FallDetection` trong VS Code.

Cách đang dùng là đúng: mở terminal tại thư mục project rồi chạy:

```powershell
.\venv\Scripts\python.exe python_app/gui.py
```

Hoặc nhấp đúp **run_app.bat**; hai cách mở cùng một ứng dụng. Không mở cả hai cùng lúc. Không cần chạy riêng sensor_reader.py, pose_detector.py hay công cụ training.

**Chọn bài demo trước khi bật Wokwi:**

| Bài demo | Nguồn trong app | Ô “Ghép Wokwi trực tiếp vào video” | Cần Wokwi? |
|---|---|---|---|
| Video độc lập | Video | Bỏ chọn | Không |
| Webcam + cảm biến | Webcam | Không áp dụng | Có |
| Video + cảm biến giả lập | Video | **Bật** | Có |

Wokwi đang chạy không có nghĩa app đang dùng Wokwi. Ở video độc lập, dòng sensor hiển thị **“Video độc lập — không ghép IMU”**. “Upload” ở đây chỉ là chọn file trên máy, không gửi video lên mạng.

## 2. Các video dùng khi bảo vệ

Tất cả video demo bên dưới ở **test_videos** trong project; nút **Chọn video…** mở sẵn thư mục này.

| Tên file | Nội dung / dùng để chứng minh | Kết quả đã quan sát |
|---|---|---|
| `demo_fall_02.mp4` | Clip ngắn, có chuyển động ngã/hạ người nhanh; nên chạy đầu tiên | EARLY_WARNING khoảng **3,5 s** |
| `demo_fall_01.mp4` | Người ngã và mất keypoints/che khuất | EARLY_WARNING khoảng **20,6 s** |
| `solo_transition.avi` | Bạn đứng rồi chủ động nằm, dùng kiểm tra nằm lâu | LYING_CHECK khoảng **41,1 s** ở video độc lập; có thể có cảnh báo chuyển động trước đó |
| `solo_lying.avi` | Đoạn chủ yếu đứng/không có tư thế nằm rõ; tên file cũ dễ gây nhầm | Không có cảnh báo trong lượt hồi quy đã kiểm tra |

Hai file `demo_fall_*.mp4` là bản sao đúng nội dung các clip gốc trong `D:\NCTU\XLA\VidTestProject`, tổng chỉ khoảng **3,25 MB**; dùng tên ngắn để dễ mang project sang máy khác. Giữ nguyên bản gốc. Không chọn `result-vid1.mp4`: đó là quay màn hình app. `test2.mp4` trùng clip thứ hai, không cần mang thêm.

70 video nghiên cứu ở `data\urfall\rgb` là dữ liệu bổ sung, **không phải danh sách demo đã bảo đảm cảnh báo**. Không chọn thư mục `source` vì video gốc ghép hình depth và RGB. Không cần mở label_videos.bat trong buổi demo.

## 3. Bài A — video độc lập, dễ trình bày nhất

1. Mở app; không cần bật Wokwi. Nếu Wokwi đã chạy thì vẫn có thể để nguyên.
2. Bật **Âm thanh**, bấm **Thử chuông**, sau đó **Đã thấy — tắt chuông** để kiểm tra loa.
3. Chọn nguồn **Video**.
4. **Bỏ chọn** “Ghép Wokwi trực tiếp vào video”.
5. Bấm **Chọn video…**, chọn `test_videos\demo_fall_02.mp4`.
6. Giữ các ngưỡng mặc định, bấm **Bắt đầu**.
7. Theo dõi thời gian **Video** trên app: khoảng 3,5 giây có cảnh báo nguy cơ, popup/nháy/chuông. Bấm tắt chuông; việc phân tích vẫn tiếp tục.
8. Bấm **Dừng** và đợi app dừng trước khi đổi clip. Chạy `demo_fall_01.mp4` để minh họa cảnh báo khi mất keypoints.
9. Nếu cần minh họa nằm 1,3 giây: chạy `solo_transition.avi`, đợi đến đoạn cuối; có thể tắt chuông sớm để quan sát LYING_CHECK sau đó.

Video độc lập phân tích đủ frame, nên tốc độ phát có thể chậm hơn video gốc. Mốc 3,5/20,6/41,1 giây là **thời gian trong clip**, không phải thời gian bấm đồng hồ ngoài đời.

Trong bài này mong đợi **EARLY_WARNING/LYING_CHECK**, không mong đợi FALL_DETECTED vì không có IMU thuộc sự kiện trong video.

## 4. Bài B — webcam + Wokwi, minh họa cảm biến đang hoạt động

1. Trong VS Code, Build firmware nếu vừa sửa code hoặc chưa có bản build; sau đó chạy **Wokwi: Start Simulator**. Nếu đã sửa firmware khi Wokwi đang mở, Stop rồi Start lại.
2. Đặt MPU6050 về bình thường: **Acceleration X/Y/Z = (0,0,1) g**, **Rotation X/Y/Z = (0,0,0) °/s**.
3. Mở app bằng lệnh ở mục 1 hoặc run_app.bat.
4. Chọn **Webcam**, camera `0`, giữ cổng `rfc2217://localhost:4000`.
5. Bấm **Bắt đầu**. Đặt camera thấy rõ vai, hông và chân của một người; xác nhận số đo sensor xuất hiện, thường khoảng 1 g và 0 °/s.
6. Trong Wokwi, đặt **Rotation X = 120**, Y/Z = 0, giữ vài giây. Phải thấy cảnh báo sớm dù người còn đứng. Sensor có thể vẫn NORMAL vì mức này chưa vượt ngưỡng IMPACT 150 °/s.
7. Bấm tắt chuông; trả Rotation X = 0, đợi ổn định.
8. Nếu muốn chứng minh riêng gia tốc: giữ Rotation = 0, đặt **Acceleration X = 2, Y = 0, Z = 2**. Gia tốc tổng khoảng 2,83 g → IMPACT. Sau đó trả về `(0,0,1)`.
9. Kết thúc: bấm **Dừng**, rồi dừng Wokwi.

Không cần cố té thật. Wokwi là tín hiệu giả lập do bạn điều chỉnh, không tự đo chuyển động cơ thể. Bài này minh họa cảnh báo theo IMU; kiểm tra ngã webcam thực tế còn phụ thuộc góc máy, keypoints và cần đánh giá riêng.

## 5. Bài C — video ghép Wokwi, minh họa hai nguồn xác nhận FALL

Đây là **demo ghép có chủ động**, không phải dữ liệu IMU được ghi cùng video.

1. Chạy Wokwi và đặt cảm biến bình thường như bài B.
2. Trong app, bấm **Dừng** nếu đang chạy; chọn **Video** và `test_videos\solo_transition.avi`.
3. **Bật** ô “Ghép Wokwi trực tiếp vào video”.
4. Đặt **Rotation X = 200 °/s**, Y/Z = 0; giữ acceleration `(0,0,1)`.
5. Bấm **Bắt đầu**; kiểm tra sensor hiển thị **IMPACT**. Có cảnh báo sớm ngay; có thể bấm tắt chuông đó.
6. Giữ Rotation X = 200 để không cần canh đúng giây. Khi clip tới đoạn nằm cuối, tư thế LYING được quan sát đủ **1,3 giây** cùng IMPACT sẽ tạo **FALL_DETECTED**, cảnh báo ưu tiên cao hơn sẽ xuất hiện.
7. Nếu chỉ SUSPICIOUS, kiểm tra dòng **Tư thế**, **Nằm rõ**, **lý do** và sensor. UNKNOWN không được cộng vào 1,3 giây; không tăng ngưỡng tùy tiện để ép kết quả.
8. Bấm **Đã thấy — tắt chuông**, **Dừng**, trả Rotation về 0 rồi dừng Wokwi.

Chế độ ghép dùng thời gian thực và có thể bỏ frame để bám sensor; không giống bài A. Kết quả còn phụ thuộc tốc độ máy/kết nối. Lượt chạy thật với Wokwi + clip này đã đạt ở các phiên trước; nên chạy thử nguyên bài trên đúng máy trước buổi bảo vệ.

## 6. Giải thích trạng thái khi thuyết trình

| Trạng thái | Cách giải thích |
|---|---|
| NORMAL | Chưa thấy bằng chứng bất thường theo luật hiện tại |
| SUSPICIOUS | Có dấu hiệu hoặc thiếu bằng chứng rõ; đọc lý do bên cạnh |
| EARLY_WARNING | Chuyển động/cảm biến bất thường, cảnh báo nguy cơ, chưa khẳng định té |
| LYING_CHECK | Thấy nằm đủ 1,3 giây, cần kiểm tra dù chưa có IMU xác nhận |
| FALL_DETECTED | Cả điều kiện tư thế và IMU của hệ thống cùng đạt |

Mô hình tư thế là YOLO11n pretrained; logic chuyển động và kết hợp cảm biến dùng luật/thời gian. Dữ liệu nghiên cứu đã chuẩn bị nhưng **chưa train model mới**. Không nói hệ thống đã tự học mọi tư thế hoặc bảo đảm cảnh báo trước mọi cú té.

## 7. Chuẩn bị trước khi lên bảo vệ

1. Thử trước cả loa, camera và kết nối Wokwi trên chính máy mang đi; cắm sạc.
2. Chạy bài A trước, bài B tiếp theo, bài C nếu cần giải thích xác nhận hai nguồn. Mỗi lần đổi chế độ bấm Dừng trước.
3. Không mở thêm sensor_reader.py, console demo hoặc một GUI thứ hai: chỉ một chương trình đọc Wokwi/camera.
4. Nếu thấy SENSOR_DISCONNECTED: kiểm tra Simulator đang chạy và cổng `localhost:4000`; đóng chương trình đọc sensor khác rồi Dừng/Bắt đầu lại.
5. Nếu UNKNOWN kéo dài: chỉnh góc máy/ánh sáng để thấy vai–hông–chân; không tự coi UNKNOWN là ngã.
6. Log mỗi lượt nằm trong `results\gui_*.csv`; dùng khi cần trình bày quá trình chuyển trạng thái.
7. Sang máy khác: không chép venv để dùng trực tiếp; tạo môi trường và cài requirements theo README. Cần mang `yolo11n-pose.pt`, mã nguồn, launcher và video demo. Chỉ demo video thì không cần data/URFD, tools gán nhãn hoặc bộ firmware build; demo Wokwi phải có cấu hình và firmware đã build. Những file bị gitignore như model/video không tự đi theo Git.

## 8. Phạm vi code gọn

Luồng chạy: **gui.py → main.py → scene_analyzer.py + sensor_reader.py → alerts.py**. Posture/motion/fusion là các phần xử lý dùng chung; không có một bộ nhận diện riêng cho từng video. `tools/` chỉ phục vụ chuẩn bị dữ liệu/kiểm tra, không được tải vào luồng chạy demo. Giữ một model, không thêm Flask, database, cloud hoặc thư viện mới cho hướng dẫn này.
