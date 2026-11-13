# Chế độ B: Bản tin sáng

Phiên chính đọc file này và PHẦN 1 của `thu-thap.md`. Không đọc file tham chiếu nào khác.

Mục tiêu: đọc xong trong **3 phút trên điện thoại** (thân bản tin **tối đa khoảng 350 từ**, không tính ảnh). Chỉ cung cấp thông tin: không phân tích lại nguyên nhân, không chạy lại kiểm định, không gọi Opus, không đọc vault, không đọc bản tin hay báo cáo cũ. Thứ gì cần lưu để kiểm tra nhưng không cần đọc hằng ngày thì vào **phụ lục**.

## Quy trình

`<W>` = thư mục làm việc `research/`. `<S>` = thư mục skill.

0. Hôm nay là thứ 2 hoặc không phải ngày sau một phiên giao dịch (nghỉ lễ) thì dừng, trả lời một dòng. Bản tin gộp mọi phiên kể từ bản tin hoặc báo cáo sâu trước (thứ 3 gộp phiên thứ 2; thứ 5 gộp thứ 3 và thứ 4).
1. **Song song hai việc:**
   - Phiên chính chạy lệnh lấy giá ở mục "Giá" của SKILL.md, rồi `kiem_tra_du_lieu.py` trên các file `gia_<MÃ>_ctck.csv`.
   - Gọi **agent T (Haiku, effort low) tải trạng thái** với đúng lời giao việc ở mục "Agent T" dưới đây. Không tự gọi `project_read` trong phiên chính (nội dung file sẽ nằm lại trong ngữ cảnh suốt lần chạy).
2. Đọc từ đĩa: `<W>/du-an/data/TOM-TAT.md` và `<W>/du-an/data/MOC-THEO-DOI.md` (mốc theo dõi, lịch sự kiện, vị trí chu kỳ và kết quả kiểm định từ phân tích sâu gần nhất). Không đọc các CSV: xử lý chúng bằng Python, chỉ in vài dòng.
3. Gọi song song **B1, B2, B3** (Haiku, effort medium). Lời giao việc ngắn, theo đầu file `thu-thap.md` (tên agent, câu "đọc thu-thap.md PHẦN 1 và 2", tham số). Không chép quy tắc vào lời giao việc.
4. So hai nguồn của từng số theo "Quy tắc chính xác", gắn nhãn. Chỉ khi còn số quan trọng chưa ✔ mới gọi A5 (tối đa 10 dòng). Ghi thêm dòng vào `kiem-chung.csv`, `von-ngoai.csv`, `su-kien-nen-tang.csv`, `tham-chieu.csv` trong `<W>/du-an/` bằng Python (chỉ thêm dòng), rồi chạy `ap_luc_von_ngoai.py <W>/du-an/data/von-ngoai.csv --chu > <W>/ap_luc.txt`. Giá đóng cửa chưa ✔ là dòng tạm: không dùng để chấm mốc hay vẽ vùng dự báo.
5. MBB và TCB: `forecast6.py <giá> --lich-su <file dự báo của mã> --khong-kiem-chung --he-so <he_so_gian_vung phiên 6 của dự báo gần nhất trong file đó>` rồi `chart6.py <giá> --ma <MÃ> --du-bao <kết quả> --out <W>/<MÃ>-6-phien.png > <W>/<MÃ>-6-phien.txt`. File dự báo: MBB `du-an/MBB/du-bao-6-phien.json`, TCB `du-an/TCB/du-bao-6-phien-dieu-chinh.json` (TCB đã chia cổ tức cổ phiếu 100:50, GDKHQ 29/10/2026; giá từ API đã điều chỉnh). CTG, HPG chỉ cần giá so với TB20, tính từ file giá. Không chạy `cycles.py`: vị trí chu kỳ = vị trí trong `MOC-THEO-DOI.md` cộng số phiên đã qua.
6. Viết **thân bản tin** theo mẫu vào `<W>/ban_tin.md`. **Phụ lục ghép bằng một lệnh** vào `<W>/phu_luc.md` (`cat` các file đã có dưới đúng tiêu đề của mẫu: bản chữ `chart6.py`, `ap_luc.txt`, file kết quả, `danh_muc_*.md`, `nguon_*.md` của B1–B3); phiên chính chỉ tự viết ba mục ngắn "Chưa kiểm chứng", "Đã thu thập nhưng không dùng", "Độ chính xác dự báo".
7. **Lưu** (mục "Lưu" dưới đây), rồi trả lời.

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
- Chỉ dùng số ✔, không gắn nhãn từng số (dòng đầu đã ghi tổng). Số ◐ ghi "[mục] chưa xác nhận"; số ✖ ghi "[mục]: các nguồn mâu thuẫn". Giá đóng cửa của một mã chưa ✔ thì dòng mã đó ghi "giá chưa xác nhận" và bỏ vùng dự báo, mốc.
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
## Tin nền tảng mới (mỗi tin một dòng kèm chuỗi tác động)
## Tin doanh nghiệp không đưa lên thân bản tin
## Doanh nghiệp và ngành tham chiếu – đầy đủ (B3)
## Độ chính xác dự báo
## Lịch sự kiện 10 ngày tới
## Chưa kiểm chứng (mục · số · nguồn · vì sao)
## Đã thu thập nhưng không dùng (kèm lý do)
## Độ đầy đủ dữ liệu
## Nguồn (kèm cấp 1/2/3)
```
Mọi tin bị bỏ khỏi thân bản tin vẫn phải có mặt ở phụ lục.

## Lưu (mọi file ghi bằng `project_write` với `local_path`, không dán nội dung)

**Mỗi bản tin chỉ tạo MỘT file mới trong dự án:** ghi chú Obsidian, chứa cả thân bản tin và phụ lục. Không tạo `<ngày>-ban-tin.md`, `<ngày>-ban-tin-phu-luc.md`, `gia-bo-sung-*.csv`, file giá hay bất kỳ file theo ngày nào khác. Mọi thứ còn lại là ghi đè file trạng thái đã có.

Trước khi lưu: chép `gia_<MÃ>_ctck.csv` thành `<W>/du-an/data/<MÃ>.csv` (chỉ trên đĩa, để script đọc giá cuối), rồi chạy `python scripts/nen_du_lieu.py --thu-muc <W>/du-an --ngay <hôm nay>`.

Ghi vào dự án, dưới `claude/chung-khoan/`:
1. `obsidian/Bản tin/<yyyy-mm-dd> Bản tin.md` (file mới duy nhất, xem dưới).
2. Các file trạng thái đã đổi (ghi đè): `data/kiem-chung.csv`, `data/von-ngoai.csv`, `su-kien-nen-tang.csv`, `data/tham-chieu.csv`, hai file dự báo của MBB và TCB, `data/TOM-TAT.md`, và file `luu-tru/<tên>.csv` nào `nen_du_lieu.py` liệt kê trong `can_ghi_lai_vao_du_an` (mỗi nhật ký chỉ có một file lưu trữ; dòng trong đó chờ được chuyển vào vault khi đồng bộ Obsidian).
3. `NHAC-DONG-BO.md` sau khi thêm MỘT dòng `- Bản tin/<yyyy-mm-dd> Bản tin.md (cập nhật <yyyy-mm-dd>)` vào mục "Đang chờ đồng bộ" bằng một lệnh Python (không viết lại file).

Không ghi gì khác; **không sửa ghi chú Obsidian sống** (`Mã/`, `Vĩ mô & dòng vốn/`, `00 Tổng quan.md`): phân tích sâu sẽ cập nhật chúng. Bản tin đã lưu không bao giờ bị sửa. Ghi chú bản tin cũ hơn 14 ngày được skill `dong-bo-obsidian` xóa khỏi dự án sau khi đã có trong vault; bản tin sáng không tự xóa file nào.

**Ghi chú Obsidian của bản tin** = phần đầu (phiên chính viết vào `<W>/ghi_chu_dau.md`, ngắn, không bảng) + thân bản tin nguyên văn + phụ lục nguyên văn, ghép bằng MỘT lệnh, không viết lại:
`cat <W>/ghi_chu_dau.md <W>/ban_tin.md <W>/phu_luc.md > "<W>/du-an/obsidian/Bản tin/<yyyy-mm-dd> Bản tin.md"`

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
Đúng nguyên văn thân bản tin, cộng một dòng: "Obsidian: N file chờ đồng bộ – sẽ được chép khi bạn bấm chạy Phân tích sâu (hoặc gõ 'đồng bộ Obsidian' trên máy tính)." Gửi kèm `MBB-6-phien.png`, `TCB-6-phien.png` và `<W>/phu_luc.md` bằng SendUserFile nếu có.
