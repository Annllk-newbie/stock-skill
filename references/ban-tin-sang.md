# Chế độ B: Bản tin sáng

Phiên chính đọc file này và PHẦN 1 của `thu-thap.md`. Không đọc file tham chiếu nào khác.

Mục tiêu: đọc xong trong **3 phút trên điện thoại** (thân bản tin **tối đa khoảng 380 từ**, không tính ảnh). Chỉ cung cấp thông tin: không phân tích lại nguyên nhân, không chạy lại kiểm định, không gọi Opus, không đọc vault, không đọc bản tin hay báo cáo cũ. Thứ gì cần lưu để kiểm tra nhưng không cần đọc hằng ngày thì vào **phụ lục**.

## Quy trình

`<W>` = thư mục làm việc `research/`. `<S>` = thư mục skill.

**Lệnh điều phối:** mọi việc script làm bằng `C` = `python <S>/scripts/chay.py ban-tin <lệnh>` (5 lệnh, đúng thứ tự dưới đây). Mỗi lệnh tự ghi nhật ký chạy và chỉ in kết quả ngắn: đọc phần in ra, không mở file kết quả. Việc không phải script (VND MCP, agent, viết, `project_write`, gửi) phiên chính tự làm rồi ghi nhật ký bằng `nhat_ky.py ghi` theo PHẦN 1 của `thu-thap.md`. `C ke-hoach` in lại danh sách bước khi cần.

0. Hôm nay là thứ 2 hoặc không phải ngày sau một phiên giao dịch (nghỉ lễ) thì dừng, trả lời một dòng. Bản tin gộp mọi phiên kể từ bản tin hoặc báo cáo sâu trước (thứ 3 gộp phiên thứ 2; thứ 5 gộp thứ 3 và thứ 4).
1. `C bat-dau --ma <DANH_SÁCH_MÃ> --bieu-do MBB TCB` (ngay sau khi clone code).
2. **Song song:** gọi **agent T** (Haiku, effort low) với đúng lời giao việc ở mục "Agent T" dưới đây (không tự gọi `project_read`); trong lúc đó phiên chính gọi VND theo mục 1.5 của SKILL.md và ghi `<W>/gia/vnd.json`.
3. Agent T xong: `C gia --phien <phiên gần nhất đã đóng cửa> --cong-cu "<tên các công cụ mcp__VND__ đã nạp>"` (thay cho lệnh `gia_vnd.py` ở mục "Giá" của SKILL.md; lệnh này chạy cả `gia_vnd.py` và `kiem_tra_du_lieu.py`). Mã thoát 2 → DỪNG theo PHẦN 3 của `thu-thap.md`.
4. Đọc từ đĩa: `<W>/du-an/data/TOM-TAT.md` và `<W>/du-an/data/MOC-THEO-DOI.md`. Không đọc các CSV: xử lý bằng Python, chỉ in vài dòng.
5. Gọi song song **B1, B2** và bốn **agent theo mã M-MBB, M-TCB, M-CTG, M-HPG** (Haiku, effort medium). Lời giao việc ngắn: B1, B2 theo đầu file `thu-thap.md`, agent theo mã theo đầu file `agent-ma.md` (chế độ B). File kết quả bắt buộc đúng tên: `<W>/ket_qua_B1.md`, `<W>/ket_qua_B2.md`, `<W>/tham_chieu_B2.csv`, `<W>/ma/<MÃ>.md` (lệnh `ghep` tìm đúng các tên này). Tin "T1" của bản tin lấy từ mục "Tin doanh nghiệp", "Sự kiện công bố", "Hệ sinh thái" của `<W>/ma/<MÃ>.md`.
6. Gắn nhãn theo "Quy tắc chính xác" (giá và chỉ số VND đã có nhãn). Chỉ khi còn số quan trọng chưa ✔ mới gọi A5 (tối đa 10 dòng, ghi `<W>/kiem_chung.md`). Ghi thêm dòng vào `kiem-chung.csv`, `von-ngoai.csv`, `su-kien-nen-tang.csv`, `tham-chieu.csv` trong `<W>/du-an/` bằng Python (chỉ thêm dòng).
7. `C tinh [--nghi yyyy-mm-dd …]`: điểm áp lực khối ngoại, chuỗi truyền dẫn (tự thêm cột `vix` nếu thiếu), dự báo 6 phiên và biểu đồ MBB, TCB (tự chọn file lịch sử dự báo và hệ số giãn vùng), giá so với TB20 của các mã còn lại (`<W>/tb20.txt`). Không chạy `cycles.py`: vị trí chu kỳ = vị trí trong `MOC-THEO-DOI.md` cộng số phiên đã qua.
8. Viết **thân bản tin** theo mẫu vào `<W>/ban_tin.md`, phần đầu ghi chú vào `<W>/ghi_chu_dau.md` (mẫu ở mục "Lưu"), và ba mục tự viết vào `<W>/phu_luc_tu_viet.md` dưới đúng tiêu đề mẫu: `## Chưa kiểm chứng`, `## Đã thu thập nhưng không dùng`, `## Độ chính xác dự báo` (thêm nội dung cho tiêu đề mẫu khác nếu cần, ví dụ `## Tin nền tảng mới`, `## Lịch sự kiện 10 ngày tới`). Rồi `C ghep`: ghép `<W>/phu_luc.md` đúng mẫu phụ lục từ các file trên (mục thiếu ghi "(không có)") và ghép ghi chú Obsidian bản tin. Lệnh in dòng "Nhật ký: …" thì thêm dòng đó vào mục "Dữ liệu" của `ban_tin.md` và chạy lại `C ghep`.
9. `C luu`: chép giá về lịch sử, `nen_du_lieu.py`, thêm ghi chú mới vào `NHAC-DONG-BO.md`, in danh sách file cần lưu. Phiên chính `project_write` (với `local_path`) **đúng từng dòng** danh sách đó, không thêm không bớt, ghi nhật ký bước 30, rồi trả lời (bước 31).

## Agent T – tải trạng thái (lời giao việc, chép nguyên văn, thay `<S>`, `<W>`)

```
Bạn là agent TẢI DỮ LIỆU. Không phân tích, không tóm tắt, không chép nội dung file vào câu trả lời.
1. Gọi công cụ Projects (method project_read) lần lượt cho từng đường dẫn:
   claude/chung-khoan/data/TOM-TAT.md
   claude/chung-khoan/data/MOC-THEO-DOI.md
   claude/chung-khoan/data/von-ngoai.csv
   claude/chung-khoan/data/kiem-chung.csv
   claude/chung-khoan/data/tham-chieu.csv
   claude/chung-khoan/su-kien-nen-tang.csv
   claude/chung-khoan/MBB/du-bao-6-phien.json
   claude/chung-khoan/TCB/du-bao-6-phien-dieu-chinh.json
   claude/chung-khoan/NHAC-DONG-BO.md
   claude/chung-khoan/data/MBB.csv
   claude/chung-khoan/data/TCB.csv
   claude/chung-khoan/data/CTG.csv
   claude/chung-khoan/data/HPG.csv
   claude/chung-khoan/data/VNINDEX.csv
   claude/chung-khoan/data/VN30.csv
   claude/chung-khoan/data/vnd-cong-cu.txt
   claude/chung-khoan/luu-tru/kiem-chung.csv
   claude/chung-khoan/luu-tru/su-kien-nen-tang.csv
   claude/chung-khoan/luu-tru/tham-chieu.csv
   claude/chung-khoan/luu-tru/von-ngoai.csv
   (4 file luu-tru có thể chưa có trong dự án: lỗi "không tìm thấy" thì bỏ qua, không thử lại)
2. Chạy: python <S>/scripts/du_an.py luu --out <W>/du-an
3. Trả lời đúng dòng JSON mà lệnh đó in ra, không thêm gì khác.
```
Agent T báo lỗi, không có công cụ Projects, hoặc `da_luu` rỗng: phiên chính tự gọi `project_read` cho các đường dẫn trên rồi chạy lệnh đó (không chép tay nội dung). File nào dự án chưa có (lần đầu) thì bỏ qua và ghi ở mục "Dữ liệu". Code của skill không bao giờ tải từ dự án: nó nằm trong `<S>` (bản GitHub, xem SKILL.md).

## Quy tắc lọc cho thân bản tin
- Chỉ đưa vào điều **khác hôm qua** hoặc **cần chú ý hôm nay**: mốc bị chạm, giá ra ngoài vùng 80%, khối lượng ≥ 1,5 lần TB20, giá thay đổi ≥ 2 lần độ lệch chuẩn ngày, tin T1 của mã theo dõi, tin nền tảng làm đổi điểm áp lực khối ngoại, sự kiện trong 3 phiên tới. Còn lại để phụ lục.
- Chỉ dùng số ✔, không gắn nhãn từng số (dòng đầu đã ghi tổng). Số ◐ ghi "[mục] chưa xác nhận"; số ✖ ghi "[mục]: các nguồn mâu thuẫn".
- **Chuỗi truyền dẫn** (một dòng, tối đa 40 từ, chép từ phần "Đọc chuỗi" của `chuoi.txt`, không tự suy luận thêm): mắt xích quốc tế nào ĐÁNG KỂ và chiều của nó → đã truyền tới đâu → chỗ đứt đầu tiên. Không mắt xích quốc tế nào vượt ngưỡng thì ghi đúng "Chuỗi truyền dẫn: không có cú sốc mới"; script ghi "chưa đủ số quốc tế" thì ghi đúng "Chuỗi truyền dẫn: chưa đủ số liệu". Mắt xích mang số ◐ thì thêm "chưa xác nhận"; mắt xích script ghi "chưa có số liệu" hay "số cũ" thì không dùng. Không viết lý do của chỗ đứt (việc của phân tích sâu), trừ khi `MOC-THEO-DOI.md` đã ghi sẵn. Chỗ đứt mới so với dòng "Chuỗi truyền dẫn" trong `MOC-THEO-DOI.md` thì đưa lên "Đáng chú ý hôm nay".
- Chu kỳ chỉ nêu khi `MOC-THEO-DOI.md` ghi kiểm định của mã là `co_co_so` hoặc `goi_y_yeu`; `khong_khac_ngau_nhien` thì ghi "chu kỳ: không khác ngẫu nhiên"; chưa có kết quả kiểm định thì ghi "chu kỳ: chưa kiểm định".
- Độ chính xác dự báo chỉ nêu khi đã có ≥ 10 dự báo độc lập; chưa đủ thì bỏ hẳn.
- Không bảng, không biểu đồ chữ, không lặp số đã có trong ảnh `chart6.py`.

## Mẫu thân bản tin (giữ đúng thứ tự và tên mục mọi ngày)
```
# Bản tin sáng [thứ, dd/mm] · Kiểm chứng: x ✔ · y ◐ · z ✖ · w ⊘
## Đáng chú ý hôm nay
(1–3 gạch đầu dòng, quan trọng nhất trước. Không có gì nổi bật thì ghi "Không có thay đổi lớn so với hôm qua".)
## Thị trường
- Việt Nam: VN-Index [điểm, %], thanh khoản [so với TB20], khối ngoại HOSE [ròng], tự doanh [ròng].
- Thế giới đêm qua: chỉ nêu biến động đáng kể (S&P 500/Nasdaq ≥ 1%, lợi suất Mỹ 10 năm ≥ 5 điểm cơ bản, DXY ≥ 0,5%, dầu ≥ 2%, châu Á ≥ 1,5%); không có thì ghi "yên ắng".
- Khối ngoại toàn thị trường: điểm áp lực [x/100, mức], đổi [±] so với hôm qua vì [chỉ báo chính] (thêm "chưa kiểm chứng" khi chưa đủ 40 phiên).
- Chuỗi truyền dẫn: [mắt xích quốc tế đáng kể ↑/↓] → [đã truyền tới] · đứt ở [mắt xích] (hoặc "không có cú sốc mới").
## Từng mã (mỗi mã 1 dòng, thêm dòng thứ 2 chỉ khi có tin T1 hoặc mốc bị chạm)
- MBB [giá] ([%], KL [x]×TB20) · vùng 80% phiên 6: [a–b] · [trong/ngoài vùng hôm qua] · chu kỳ: [pha, phiên thứ n] · mốc: [chưa chạm / đã chạm …]
- CTG [giá] ([%], KL [x]×TB20) · [trên/dưới] TB20 · chu kỳ: […]
## Tham chiếu
(tối đa 2 dòng; không có thì bỏ hẳn mục này)
## Lịch 3 phiên tới
(chỉ sự kiện ảnh hưởng mã theo dõi hoặc toàn thị trường; tối đa 4 dòng)
## Dữ liệu
(1 dòng: "Dữ liệu ổn" hoặc nêu số ✖, dòng tạm, đính chính so với bản trước. Kết thúc bằng: "Phụ lục: file gửi kèm, và cuối ghi chú Bản tin/<yyyy-mm-dd> Bản tin")
```

## Mẫu phụ lục
```
# Phụ lục bản tin [dd/mm]
## Kỹ thuật MBB, TCB (bản chữ chart6.py) và giá so với TB20 của các mã khác
## Thế giới đêm qua – đầy đủ
## Dòng vốn ngoại – bản chữ ap_luc_von_ngoai.py
## Chuỗi truyền dẫn – bản chữ chuoi_truyen_dan.py
## Tin nền tảng mới (mỗi tin một dòng kèm chuỗi tác động)
## Tin doanh nghiệp không đưa lên thân bản tin
## Doanh nghiệp và ngành tham chiếu – đầy đủ (B2, mục 4)
## Độ chính xác dự báo
## Lịch sự kiện 10 ngày tới
## Chưa kiểm chứng (mục · số · nguồn · vì sao)
## Đã thu thập nhưng không dùng (kèm lý do)
## Độ đầy đủ dữ liệu
## Nguồn (kèm cấp 1/2/3)
## Nhật ký chạy (nguyên văn research/nhat-ky-chay.txt)
```
Mọi tin bị bỏ khỏi thân bản tin vẫn phải có mặt ở phụ lục.

## Lưu (mọi file ghi bằng `project_write` với `local_path`, không dán nội dung)

**Mỗi bản tin chỉ tạo MỘT file mới trong dự án:** ghi chú Obsidian, chứa cả thân bản tin và phụ lục. Không tạo `<ngày>-ban-tin.md`, `<ngày>-ban-tin-phu-luc.md`, `gia-bo-sung-*.csv`, file giá hay bất kỳ file theo ngày nào khác. Mọi thứ còn lại là ghi đè file trạng thái đã có.

`C luu` làm phần chuẩn bị (chép `gia_<MÃ>_ctck.csv` về `<W>/du-an/data/<MÃ>.csv`, `VNINDEX.csv`, `VN30.csv` – lịch sử giá duy nhất; `nen_du_lieu.py`; thêm dòng `- Bản tin/<yyyy-mm-dd> Bản tin.md (cập nhật <yyyy-mm-dd>)` vào mục "Đang chờ đồng bộ" của `NHAC-DONG-BO.md`) và in danh sách file **mới hoặc đã đổi** so với lúc agent T tải xong. Danh sách đó thường gồm: ghi chú Obsidian bản tin (file mới duy nhất), các nhật ký CSV, hai file dự báo của MBB và TCB, `data/TOM-TAT.md`, `data/<MÃ>.csv`, `data/VNINDEX.csv`, `data/VN30.csv`, `data/vnd-cong-cu.txt`, file `luu-tru/<tên>.csv` do `nen_du_lieu.py` tạo, `NHAC-DONG-BO.md`. Thiếu file nào trong số này (ví dụ lịch sử giá) nghĩa là bước trước đã lỗi: xem nhật ký.

Không ghi gì khác; **không sửa ghi chú Obsidian sống** (`Mã/`, `Vĩ mô & dòng vốn/`, `00 Tổng quan.md`): phân tích sâu sẽ cập nhật chúng. Bản tin đã lưu không bao giờ bị sửa. Ghi chú bản tin cũ hơn 14 ngày được skill `dong-bo-obsidian` xóa khỏi dự án sau khi đã có trong vault; bản tin sáng không tự xóa file nào.

**Ghi chú Obsidian của bản tin** = phần đầu (`<W>/ghi_chu_dau.md`, ngắn, không bảng) + thân bản tin nguyên văn + phụ lục nguyên văn; `C ghep` ghép thành `<W>/du-an/obsidian/Bản tin/<yyyy-mm-dd> Bản tin.md`, không viết lại.

Phần đầu:
```
---
loai: ban-tin
ngay: <yyyy-mm-dd>
ma: [MBB, TCB, CTG, HPG]
tags: [chung-khoan, ban-tin]
---
# <yyyy-mm-dd> Bản tin (dữ liệu phiên dd/mm)
Về [[00 Tổng quan]] · Bản tin đầy đủ và phụ lục ở cuối ghi chú này
## Điểm chính
(5–8 gạch đầu dòng chép từ thân bản tin; mỗi mã một dòng bắt đầu bằng [[MBB]] / [[TCB]] / [[CTG]] / [[HPG]] gồm giá, % và mốc; tin vĩ mô gắn link ghi chú liên quan: [[Dòng vốn ngoại]] [[Fed & Mỹ]] [[NHNN & lãi suất]] [[Tỷ giá]] [[Trái phiếu]] [[ETF & khu vực]] [[Đầu tư công & FDI]] [[Doanh nghiệp tham chiếu]])

---

```

## Câu trả lời cuối (thông báo điện thoại)
Đúng nguyên văn thân bản tin, cộng (chỉ khi bước 30 hoặc 31 của nhật ký không OK) dòng nhật ký đó, cộng một dòng: "Obsidian: N file chờ đồng bộ – sẽ được chép khi bạn bấm chạy Phân tích sâu (hoặc gõ 'đồng bộ Obsidian' trên máy tính)." Gửi kèm `MBB-6-phien.png`, `TCB-6-phien.png` và `<W>/phu_luc.md` bằng SendUserFile nếu có.
