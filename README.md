# 📸 Ref – Ứng dụng Tham Khảo Ảnh Nhanh cho Nhiếp Ảnh Gia  

Ref là ứng dụng desktop giúp nhiếp ảnh gia lưu trữ, quản lý và xem nhanh ảnh tham khảo (reference photos) để tìm ý tưởng về **pose, góc chụp, ánh sáng, lens và style**, đặc biệt khi đang chụp ngoài hiện trường.

Không chỉnh sửa ảnh.  
Không xử lý phức tạp.  
Chỉ cần mở là **xem Ref ngay**.

---

## 🎯 Mục tiêu

- Gom ảnh tham khảo từ Google Drive (tương lai Pinterest & web nguồn khác)
- Lưu trữ theo concept, lens, lighting & tag
- Xem EXIF nhanh và ghi chú phân tích
- Tìm ý tưởng khi bí góc hoặc cần reference ngay tại buổi chụp

👉 Mục tiêu cuối: **không còn bí pose, bí ánh sáng, bí góc nhìn**.

---

## 🌟 Điểm mạnh của Ref

- Xem ảnh nhanh, offline
- Giao diện tối ưu cho nhiếp ảnh
- Metadata tập trung vào học góc chụp
- Hỗ trợ xem EXIF đã được rút gọn
- Dễ sử dụng trong môi trường chụp thật

---

## 🔍 Tính năng chính

### 1. Ref Library (Sidebar)
- All photos
- Recently viewed
- Tag groups
- Category (Kỷ yếu / Wedding)
- Smart filter theo lens, style, lighting
- Favorites, Trash

### 2. Gallery View
- Masonry layout kiểu Pinterest
- Lazy loading thumbnail
- Quick view metadata
- Grid/compact mode

### 3. Inspector View
Double-click ảnh để xem:
- Zoom/Pan
- EXIF ngắn gọn:
  - ISO
  - Focal length
  - Aperture
  - Shutter speed
- Metadata:
  - Lens
  - Style
  - Lighting
  - Category
  - Tags
- Note (ghi chú phân tích, gợi ý, pose…)

---

## 🧠 Metadata hỗ trợ học nhiếp ảnh

Lưu theo:
- category (kyeu, cuoi,…)
- lens
- style
- lighting
- tags
- note
- EXIF cần thiết

Ví dụ hướng ánh sáng:
- Backlight
- Side light
- Golden hour

Lens gợi ý:
- 24-35mm
- 50mm
- 85mm

---

## 🔎 Tìm kiếm & lọc

Có thể tìm theo:
- lens
- style
- lighting
- tag
- note

Ví dụ:
35mm + backlight + outdoor

## 🏗 Kiến trúc

Ref/
├── assets/
│ ├── icons/
│ └── style.qss
├── data/
│ ├── images/
│ └── ref.db
├── src/
│ ├── backend/
│ │ ├── file_manager.py
│ │ └── exif_reader.py
│ ├── services/
│ │ ├── drive_sync.py
│ │ └── import_service.py
│ ├── ui/
│ │ ├── main_window.py
│ │ ├── sidebar.py
│ │ ├── toolbar.py
│ │ ├── gallery_view.py
│ │ ├── inspector_view.py
│ │ └── filter_bar.py
│ └── utils/
│ ├── thread_worker.py
│ └── config.py
├── main.py
└── requirements.txt


---

## 🧱 SQLite Database (chỉ EXIF cần thiết)

### photos
- file_path
- source
- created_at
- updated_at
- is_favorite
- is_trashed

### photo_meta
- category
- lens
- style
- lighting
- note
- exif_iso
- exif_focal
- exif_aperture
- exif_shutter

---

## 🚀 Cài đặt

```bash
pip install -r requirements.txt
python main.py

Yêu cầu:

Python 3.10+

Windows 10/11

🔄 Drive Sync (Two-way)

Phase đầu:

Import ảnh từ thư mục local (đã sync Google Drive)

Phase sau:

Đồng bộ 2 chiều

Conflict resolution

🗂 Roadmap
Phase 1 (Kỷ yếu)

SQLite

Gallery + Inspector

EXIF + Note

Filter lens/style/lighting

Import local

Phase 2

Drive Sync

Export iCloud folder (đưa vào iPhone)

Phase 3 (Wedding)

Concept cưới

Lighting/Staging

Metadata sâu hơn

Phase 4 (Web/Pinterest)

Import board

Auto download originals

📌 Slogan

Ref – Tham khảo ảnh ngay khi cần
Ref – Thư viện góc chụp bỏ túi

🔑 Giấy phép

MIT License

Ref giúp nhiếp ảnh gia tìm ý tưởng nhanh, học góc ánh sáng hiệu quả, và luôn có thư viện tham khảo bên cạnh khi đang chụp.