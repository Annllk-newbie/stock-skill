# stock-skill

Code của skill `stock-research-analyzer` (bản tin sáng và phân tích sâu chứng khoán). Đây là nguồn duy nhất: mỗi lần chạy, skill trên claude.ai `git clone` kho này về `research/skill`.

- `references/` – hướng dẫn từng chế độ (bản tin sáng, phân tích sâu, thu thập, chuỗi truyền dẫn, kiểm tra chéo, kỹ thuật).
- `scripts/` – script Python (giá từ VND MCP qua gia_vnd.py, chu kỳ, kiểm định, dự báo 6 phiên, biểu đồ, khối ngoại, chuỗi truyền dẫn vĩ mô, nén dữ liệu).
- Dữ liệu (giá, nhật ký, báo cáo) KHÔNG nằm ở đây: nằm trong Project "Economy and trading" và vault Obsidian.

## Khi một lần chạy bị lỗi

Mỗi lần chạy ghi `research/nhat-ky-chay.txt` (script `scripts/nhat_ky.py`): mỗi bước một dòng `giờ | trạng thái | bước | chi tiết | Gợi ý: cách sửa`. Trạng thái: OK · CẢNH BÁO · LỖI · BỎ QUA · DỪNG. Nhật ký nằm ở cuối phụ lục bản tin / cuối báo cáo sâu (ghi chú Obsidian), và trong thông báo khi lần chạy DỪNG. Muốn sửa: gửi dòng không OK cho Claude. Gặp lỗi mới thì thêm mẫu vào bảng `GOI_Y` trong `nhat_ky.py`.

## Sơ đồ luồng

Đọc cùng nhật ký chạy: số bước dưới đây trùng số bước trong nhật ký. Dòng nhật ký báo lỗi ở bước nào thì xem bước đó ở đây để biết nó đọc file gì, ghi file gì và hướng dẫn nằm ở đâu.

Quy ước: `<W>` = `research/` (thư mục làm việc của lần chạy) · `<S>` = `research/skill/` (bản clone kho này) · "dự án" = `claude/chung-khoan/` trong Project · B = bản tin sáng · A = phân tích sâu (Ađ = bản đầy đủ cuối tuần, Ac = bản cập nhật giữa tuần).

```
 01 Tải code ──► 02–05 Giá (VND) ──┐            ┌─► 09–17 Thu thập (Haiku, song song)
                 06 Agent T ───────┼─► (A: 07–08 vault, chấm dự báo) ─┤
                                   │            └─► 18 A5 kiểm chứng ─► 19 gắn nhãn
                                   │
 19 ─► 20–23 script (B)  hoặc  24 chay_sau.py (A) ─► (A: 25 tổng hợp ─► 26 Opus ─► 27 agent O)
     ─► 28 viết bản tin/báo cáo ─► 29 nén dữ liệu ─► 30 lưu vào dự án ─► 31 gửi điện thoại
 Lỗi ở 01–04 (code hoặc giá) = DỪNG cả lần chạy, chỉ gửi thông báo kèm nhật ký.
```

### Lệnh điều phối `scripts/chay.py`
Mọi bước script gom vào 5 lệnh, chạy đúng thứ tự: `python research/skill/scripts/chay.py <ban-tin|sau|sau-nhe> <lệnh>`.
- `bat-dau --ma …` → bước 01 (tạo nhật ký, in kế hoạch).
- `gia --phien … --cong-cu …` → bước 04–05 (sau 03 và 06). Mã thoát 2 = DỪNG.
- `tinh` → B: bước 20–23 + `tb20.txt`; A: bước 24.
- `ghep` → bước 28 (B: phụ lục + ghi chú bản tin; A: thêm nhật ký vào `bao_cao.md`).
- `luu` → bước 29 + danh sách file cần `project_write` (`<W>/can-luu.json`), tính bằng so nội dung với lúc agent T vừa tải xong.
Các bước còn lại (VND MCP, agent, viết lời văn, `project_write`, gửi) là việc của phiên chính. `chay.py <chế độ> ke-hoach` in thứ tự đầy đủ.

### Chuẩn bị (cả B và A)
- **01 Tải code GitHub** – lệnh `git clone` ở mục 0 của SKILL.md. Ghi `<S>`. Lỗi → DỪNG (chưa có nhật ký, thông báo kèm nguyên văn lỗi).
- **02 VND health và công cụ** – MCP `mcp__VND__health`, nạp công cụ bằng ToolSearch `mcp__VND__`. Hướng dẫn: SKILL.md mục 1.5. Lỗi sau một lần thử lại → DỪNG.
- **03 VND lịch, giá, chỉ số, khối ngoại sàn** – MCP `get_trading_calendar`, `get_stock_price_by_date`, `get_vnmarket_prices` (mỗi chỉ số một lần), `get_foreign_trading` (VNINDEX), `get_change_prices` (Brent, vàng). Ghi `<W>/gia/vnd.json`.
- **04 gia_vnd.py** – đọc `<W>/gia/vnd.json`, `<W>/du-an/data/<MÃ>.csv`, `VNINDEX.csv`, `VN30.csv`, `vnd-cong-cu.txt`. Ghi `<W>/gia/gia_<MÃ>_ctck.csv`, `gia_VNINDEX_ctck.csv`, `gia_VN30_ctck.csv`, `<W>/gia/ket-qua.json`. Mã thoát 2 → DỪNG (PHẦN 3 `thu-thap.md`). Cần bước 06 xong trước (lịch sử giá).
- **05 kiem_tra_du_lieu.py** – đọc các file `gia_*_ctck.csv`. Có `loi` thì phiên đó không dùng cho dự báo.
- **06 Agent T** (Haiku) – `project_read` các file dự án, rồi `du_an.py luu` ghi ra `<W>/du-an/` (cùng cấu trúc với dự án). Danh sách file: mục "Agent T" trong `ban-tin-sang.md` (A thêm file ở bước 1 của `phan-tich-sau.md`). Lỗi → bước sau báo "Thiếu file".

### Chỉ phân tích sâu
- **07 Đồng bộ và liệt kê vault** – skill `dong-bo-obsidian`, máy tính của người dùng. Ghi ghi chú người dùng tự sửa vào `<W>/vault/`. Máy tắt → CẢNH BÁO, chạy tiếp bằng dữ liệu dự án.
- **08 Chấm dự báo kỳ trước** – đọc `<W>/du-an/<MÃ>/nhat-ky-du-bao.md` và giá mới; ghi thêm dòng Đúng/Sai/Chưa rõ vào cuối file đó.

### Thu thập (Haiku, chạy song song)
Hướng dẫn: PHẦN 2 `thu-thap.md` (agent theo mã: `agent-ma.md`). Mỗi agent ghi file kết quả của mình, `danh_muc_<agent>.md` và `nguon_<agent>.md` trong `<W>`.
- **09 Agent B1** (B) – tự doanh, tỷ giá, USD, liên ngân hàng, OMO (cột hằng ngày của `von-ngoai.csv`).
- **10 Agent B2** (B) – tin chung, quốc tế đêm qua, doanh nghiệp tham chiếu.
- **11 Agent A2** (A) – lịch 10 ngày, sự kiện quá khứ chung, tham chiếu.
- **12 Agent A3** (A) – dòng tiền, ngành, vĩ mô, quốc tế, Fed, ETF.
- **13 Agent A4** (chỉ Ađ; Ac ghi BỎ QUA) – NHNN, trái phiếu, đầu tư công và FDI.
- **14–17 Agent M-MBB, M-TCB, M-CTG, M-HPG** (B và A) – tự gọi VND phần theo mã. Ghi `<W>/ma/<MÃ>.md`, `<W>/ma/su_kien_<MÃ>.csv`.
- **18 Agent A5** – đọc `<W>/can_kiem_chung.md`, tìm nguồn thứ hai. A: luôn chạy; B: chỉ khi còn số chưa ✔, không thì BỎ QUA.
- **19 Gắn nhãn và ghi nhật ký CSV** – phiên chính, Python. Thêm dòng vào `<W>/du-an/data/kiem-chung.csv`, `von-ngoai.csv`, `tham-chieu.csv`, `<W>/du-an/su-kien-nen-tang.csv` (A thêm `<W>/du-an/<MÃ>/su-kien.csv`).

### Tính toán
- **20 ap_luc_von_ngoai.py** (B) – đọc `von-ngoai.csv`, ghi `<W>/ap_luc.txt`.
- **21 chuoi_truyen_dan.py** (B) – đọc `von-ngoai.csv`, `gia_VNINDEX_ctck.csv`, ghi `<W>/chuoi.txt`.
- **22–23 forecast6/chart6 MBB, TCB** (B) – đọc file giá và lịch sử dự báo (`MBB/du-bao-6-phien.json`, `TCB/du-bao-6-phien-dieu-chinh.json`). Ghi `<W>/<MÃ>-6-phien.png`, `<W>/<MÃ>-6-phien.txt`, thêm dòng vào lịch sử dự báo.
- **24 chay_sau.py** (A) – một lệnh chạy cycles, indicators, risk, kiem_dinh, forecast6, chart6, ap_luc, chuoi cho mọi mã; mỗi script con ghi một dòng nhật ký riêng (`chay_sau · <MÃ> <script>`). Ghi `<W>/<MÃ>/*.json`, `<W>/tom_tat_script.md`, `<W>/moc_nhap.md`, `<W>/ap_luc.txt`, `<W>/chuoi.txt`.

### Viết và kiểm tra (chỉ A cho 25–27)
- **25 Agent tổng hợp** (Sonnet) – PHẦN 2 `phan-tich-sau.md`, `chuoi-truyen-dan.md`, `ky-thuat.md`. Đọc `tom_tat_script.md`, kết quả thu thập, `<W>/vault/`. Ghi `<W>/bao_cao.md`.
- **26 Kiểm tra chéo Opus** – `kiem-tra-cheo.md`. Đọc `bao_cao.md` và các JSON. Có lỗi thì gửi lại agent 25 sửa.
- **27 Agent O** (Sonnet) – mục "Obsidian" của `phan-tich-sau.md`. Ghi `<W>/du-an/obsidian/Báo cáo sâu/<ngày> Phân tích sâu.md` và sửa các ghi chú sống (`Mã/`, `Vĩ mô & dòng vốn/`, `00 Tổng quan.md`).
- **28 Viết bản tin/báo cáo và phụ lục** – B: `<W>/ban_tin.md`, `<W>/phu_luc.md`, ghép thành `<W>/du-an/obsidian/Bản tin/<ngày> Bản tin.md`. A: nối `bao_cao.md` vào ghi chú báo cáo. Cuối phụ lục/báo cáo luôn có "Nhật ký chạy".

### Lưu và gửi
- **29 nen_du_lieu.py** – đọc các nhật ký CSV trong `<W>/du-an/`. Ghi `data/TOM-TAT.md`, chuyển dòng cũ sang `luu-tru/<tên>.csv`, in danh sách `can_ghi_lai_vao_du_an`.
- **30 Lưu vào dự án** – `project_write` với `local_path`, đúng danh sách ở mục "Lưu" của `ban-tin-sang.md` / `phan-tich-sau.md`. Mỗi lần chạy chỉ một file mới (ghi chú Obsidian); còn lại ghi đè. File nào lỗi thì ghi đường dẫn file đó vào nhật ký.
- **31 Gửi người dùng** – PushNotification hoặc câu trả lời cuối, kèm ảnh `MBB-6-phien.png`, `TCB-6-phien.png` (SendUserFile).

### Nơi dữ liệu sống
- **Kho này (GitHub):** chỉ code và hướng dẫn.
- **Dự án (Project):** trạng thái giữa các lần chạy: lịch sử giá `data/<MÃ>.csv`, các nhật ký CSV, `TOM-TAT.md`, `MOC-THEO-DOI.md`, lịch sử dự báo, ghi chú Obsidian 14 ngày gần nhất.
- **Vault Obsidian trên máy tính** (`Documents\Data\Stock data`): kho lưu trữ lâu dài, đồng bộ bằng skill `dong-bo-obsidian`.
- **`<W>` trong phiên chạy:** tạm thời, mất khi phiên kết thúc; cái gì cần giữ phải qua bước 30.

Mỗi thay đổi là một commit có ghi lý do. Muốn quay lại bản trước: `git revert`. Đổi bước, thêm script hay đổi file đầu vào/đầu ra thì sửa luôn sơ đồ này và danh sách tên bước trong PHẦN 1 của `thu-thap.md`.
