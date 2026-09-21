# Bigo Recorder

Công cụ quay livestream Bigo bằng link `.m3u8` dán tay — ổn định, không phụ thuộc vào việc Bigo/yt-dlp có đang lỗi hay không. Quay được nhiều phòng cùng lúc, tự phát hiện khi link hết hạn.

## 1. Chuẩn bị

1. Cài Python 3.10+ (tick "Add Python to PATH" khi cài): https://www.python.org/downloads/
2. Copy `ffmpeg.exe` vào **thẳng trong thư mục này** (cùng cấp với `app.py`).
   - Hoặc để chỗ khác và sửa `config.json`: `"ffmpeg_path": "D:\\yt-dlp\\ffmpeg.exe"`

## 2. Chạy

Click đúp `start.bat`. Lần đầu tự cài Flask, sau đó tự mở trình duyệt `http://127.0.0.1:5000`.
Trình duyệt có thể hỏi quyền "Thông báo" — bấm **Allow/Cho phép** để nhận cảnh báo khi link hết hạn dù đang làm việc khác.

## 3. Cách dùng

1. **Tên phòng**: đặt tên tùy ý để nhận diện, dùng làm tên file (VD: `anubdn2s`).
2. **Link .m3u8**: lấy bằng cách mở phòng trên trình duyệt → F12 → tab Network → gõ lọc `m3u8` → copy link `.m3u8` đang chạy (loại có đuôi `.m3u8` trong URL).
3. **Thư mục lưu**: bấm **"Duyệt..."** để chọn bằng hộp thoại Windows thật, không cần gõ tay.
4. Bấm **"▶ Bắt đầu quay"**. Lặp lại để thêm phòng khác — chạy song song, độc lập nhau.
5. Bấm vào 1 thẻ phòng để xem log chi tiết bên dưới.
6. Bấm **"Dừng"** để dừng riêng 1 phòng, hoặc **"Dừng tất cả"** ở góc trên để dừng toàn bộ.

## 4. Khi link hết hạn giữa chừng

Link `.m3u8` thường chỉ sống được một khoảng thời gian nhất định (tùy CDN, có thể vài chục phút). Khi hết hạn, ffmpeg sẽ tự dừng, và trong app:

- Thẻ phòng chuyển sang trạng thái **"Link đã hết hạn"** (viền đỏ) hoặc **"Có thể sắp mất kết nối"** (viền cam, cảnh báo sớm khi log ngừng cập nhật bất thường).
- Trình duyệt bắn thông báo (nếu đã cho phép quyền) + tiêu đề tab đổi thành `(1) Bigo Recorder — cần xử lý` để bạn nhận ra dù đang làm việc khác.
- Bấm nút **"Dán link mới"** trên thẻ đó → tự điền sẵn Tên phòng, bạn chỉ cần lấy link `.m3u8` mới (F12 lại) và dán → bấm Bắt đầu quay. File mới sẽ được lưu tiếp nối, đặt tên `..._p2.mp4`, `..._p3.mp4`... không mất phần đã quay trước đó.

## 5. Trạng thái

| Trạng thái | Ý nghĩa |
|---|---|
| Đang khởi động | Vừa bấm quay, ffmpeg đang mở kết nối |
| Đang quay | Đang tải bình thường |
| Có thể sắp mất kết nối | Log không cập nhật > 20 giây dù tiến trình còn sống — kiểm tra lại |
| Link đã hết hạn | ffmpeg đã dừng do lỗi kết nối/từ chối truy cập |
| Lỗi | Dừng vì lý do khác — xem log để biết chi tiết |
| Đã dừng / Hoàn tất | Kết thúc bình thường |

## 6. Cấu trúc thư mục

```
MyTool/
├── app.py
├── recorder.py
├── pick_folder.py
├── config.json
├── requirements.txt
├── start.bat
├── templates/index.html
├── static/style.css
├── static/app.js
├── logs/
└── ffmpeg.exe   ← bạn tự đem vào
```

## Lưu ý

Chỉ dùng để quay các phòng bạn có sự cấp phép/thỏa thuận từ chủ phòng.
