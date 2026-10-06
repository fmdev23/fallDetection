# Dữ liệu huấn luyện FallDetection — 06/10/2026

Đã chuẩn bị **70 video, 11.936 khung hình RGB**: 30 chuỗi có ngã và 40 chuỗi hoạt động thường ngày (ADL). Đây là bộ khởi đầu cho thí nghiệm phân loại **cả chuỗi ngã / không ngã**, chưa đủ để khẳng định độ chính xác ngoài thực tế hoặc dự đoán trước ngã. Ứng dụng hiện vẫn dùng YOLO pretrained + luật chuyển động; tải dữ liệu không đồng nghĩa đã huấn luyện model mới.

## Nguồn và giấy phép

- Nguồn gốc: [UR Fall Detection Dataset — University of Rzeszów](https://fenix.ur.edu.pl/~mkepski/ds/uf.html).
- **CC BY-NC-SA 4.0**, dùng cho nghiên cứu/học thuật phi thương mại. Bản cắt RGB giữ cùng điều kiện giấy phép; không coi đây là tài nguyên thương mại tự do.
- Trích dẫn: Bogdan Kwolek, Michal Kepski, *Human fall detection on embedded platform using depth maps and wireless accelerometer*, Computer Methods and Programs in Biomedicine, 117(3), 2014, 489–501.
- `provenance.json`: URL, dung lượng và SHA-256 từng file tải. `source/`: 142 file gốc (~98 MB). `rgb/`: 70 bản RGB (~19 MB), cắt nửa phải video preview của tác giả, không giữ nửa depth. Không tải các archive RGB/depth hàng GB.

## File nào dùng để làm gì?

| File/thư mục | Nội dung và giới hạn |
|---|---|
| `rgb/*.mp4` | Video 320×240 dùng xem/gán nhãn/thử pipeline; bản preview nén, không thay thế ảnh RGB gốc độ phân giải đầy đủ |
| `manifest.csv` | Một hàng/video: nhãn **cả chuỗi**, split, số frame, FPS, hash, nguồn, tình trạng đồng bộ |
| `depth_annotations.csv` | 11.544 nhãn **depth** gốc, giữ nguyên số frame 1-based và thời gian nguồn; không tự coi là nhãn RGB chính xác |
| `audit.json` | Kết quả giải mã, số lượng, phân lớp, các chuỗi không khớp số frame |
| `provenance.json` | Kiểm tra nguồn và tính toàn vẹn |

Các nhãn gốc: `-1 = not_lying` (không nằm, **không đồng nghĩa đứng**), `0 = falling_transition`, `1 = lying_on_ground` (nằm trên mặt đất, **không tự chứng minh vừa té**). Chưa có nhãn `walking/sitting/bending/squatting/lying_down_deliberately` chính xác từng khoảng thời gian. Không tạo các nhãn này từ kết quả YOLO để giả làm ground truth.

18 chuỗi có thiếu nhãn depth hoặc khác số khung đồng bộ; liệt kê trong `audit.json`. Đặc biệt `adl-37` có 350 frame preview nhưng 330 hàng đồng bộ. **Không kéo giãn, lặp hoặc bù nhãn cho vừa video.** Ngay cả 52 chuỗi khớp số frame cũng chưa chứng minh đồng bộ RGB chính xác. Dữ liệu nguồn đồng bộ camera theo thời điểm gần nhất. Nhãn sự kiện theo chuỗi vẫn dùng được cho 70 video; muốn học từng frame phải rà soát RGB trước.

ADL `*-data.csv` chỉ có frame/thời gian, thiếu cột gia tốc; các ô gia tốc tương ứng để trống, không điền 0 hoặc 1 g. Đặc trưng depth trong CSV nguồn không được dùng làm đầu vào cho model triển khai trên webcam RGB.

## Chia tập và tránh đánh giá sai

| Tập | Ngã | ADL | Tổng |
|---|---:|---:|---:|
| Train | 18 | 24 | 42 |
| Validation | 6 | 8 | 14 |
| Test | 6 | 8 | 14 |

Chia cố định theo **toàn bộ chuỗi**, seed `20261005`; không trộn các frame/đoạn từ cùng video vào nhiều tập. Mọi bản mirror/resize/đổi tốc độ phải theo split của video gốc. Chưa có danh tính người trong manifest, nên **không gọi đây là đánh giá độc lập theo người**; cùng phòng/người có thể xuất hiện giữa các split. Không dùng test để chọn ngưỡng hoặc dừng training.

Các video cá nhân đã dùng sửa lỗi (`solo_*`, hai clip trong VidTestProject) là **development regression**, không phải test chưa từng xem. `test2.mp4` trùng nội dung clip thứ hai, không được đếm là mẫu độc lập.

## Gán nhãn hoạt động rõ ràng

Mở `label_videos.bat` ở gốc project. Chọn video trong `data/urfall/rgb`, điền tên người rà soát; phát/dừng, dùng ←/→ để xem từng frame. Đánh dấu bắt đầu, chọn nhãn, đến cuối hành động rồi bấm **Kết thúc + lưu nhãn**. Nhãn lưu trong `data/reviewed_intervals.json`, gồm hash video, reviewer và khoảng frame **0-based, bao gồm hai đầu**. Công cụ từ chối đoạn chồng nhau; có hoàn tác nhãn cuối clip. Không tự đưa nhãn vào model đang chạy.

| Nhãn | Quy tắc |
|---|---|
| `walking` / `standing` | Bước đi / đứng yên rõ; không dùng nhãn không-nằm để suy ra hai loại này |
| `sitting` | Đã ngồi hoặc đang chuyển vào ghế; nếu cần bài toán tư thế tĩnh thì chỉ lấy đoạn đã ngồi ổn định |
| `bending` / `squatting` | Cúi thân / hạ người bằng gập gối; tách khỏi ngã |
| `lying_down_deliberately` | Chuyển xuống nằm có kiểm soát, chỉ gán khi nội dung xác nhận hành động chủ động |
| `falling` | Khoảng chuyển động mất thăng bằng/ngã đã xác nhận; không gán toàn video fall là falling |
| `lying` | Đã nằm; nhãn tư thế không thể hiện nguyên nhân |
| `uncertain` | Che khuất, cắt cảnh, không rõ hành động; loại khỏi supervised loss, không biến thành non-fall |

URFD ADL có các cảnh cúi, ngồi, ngồi xổm và nằm lên ghế; đã xem mẫu nhưng **chưa gán nhãn chi tiết toàn bộ**. Cần người thứ hai rà lại ranh giới hành động trước khi gọi là ground truth đáng tin cậy. Với dữ liệu webcam bổ sung, ưu tiên nhiều người, góc máy, khoảng cách, sáng/tối và các âm tính khó (ngồi nhanh, cúi nhặt đồ, ra khỏi khung). Chia theo người/buổi quay; không tự té thật để thu dữ liệu. Hiện chưa có nhãn dự báo trước ngã nên không dùng bộ này để tuyên bố đã học dự báo.

## Tái tạo và kiểm tra

Từ thư mục project:

```powershell
.\venv\Scripts\python.exe tools/prepare_urfall.py
.\venv\Scripts\python.exe tools/prepare_urfall.py --offline
```

Lệnh thứ nhất tải có kiểm tra dung lượng và ghi hash; lệnh thứ hai giải mã, cắt lại RGB và dựng manifest/nhãn/audit từ nguồn đã tải. Không sửa file nguồn hoặc file nhãn rà soát riêng. Dữ liệu lớn được gitignore; giữ lại README và script để tái tạo.
