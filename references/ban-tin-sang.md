# Chế độ B: Bản tin sáng

Phiên chính đọc file này sau `phien-chinh.md`, `nguyen-tac.md`, `nhan.md`. Không đọc file tham chiếu nào khác.

Mục tiêu: đọc xong trong **3 phút trên điện thoại** (thân bản tin **tối đa khoảng 380 từ**, không tính ảnh). Chỉ cung cấp thông tin: không phân tích lại nguyên nhân, không chạy lại kiểm định, không gọi Sonnet agent hay Opus, không đọc vault, không đọc bản tin hay báo cáo cũ. Thứ gì cần lưu để kiểm tra nhưng không cần đọc hằng ngày thì vào **phụ lục**.

## Quy trình (`C` = `python <S>/scripts/chay.py ban-tin`)

0. Hôm nay là thứ 2 hoặc không phải ngày sau một phiên giao dịch (nghỉ lễ) thì dừng, trả lời một dòng. Bản tin gộp mọi phiên kể từ bản tin hoặc báo cáo sâu trước (thứ 3 gộp phiên thứ 2; thứ 5 gộp thứ 3 và thứ 4).
1. `C bat-dau --ma <DANH_SÁCH_MÃ> --bieu-do <các mã có biểu đồ>` (ngay sau khi clone code).
2. **Song song:** gọi agent T (`the/T.md`, chế độ B); trong lúc đó gọi VND theo mục "VND MCP" của `phien-chinh.md` và ghi `<W>/gia/vnd.json`.
3. Agent T xong: `C gia --phien <phiên gần nhất đã đóng cửa> --cong-cu "<tên các công cụ mcp__VND__ đã nạp>"`. Mã thoát 2 → bù phiên thiếu hoặc DỪNG theo `phien-chinh.md`.
4. Đọc từ đĩa: `<W>/du-an/data/TOM-TAT.md` và `<W>/du-an/data/MOC-THEO-DOI.md`. Không đọc các CSV: xử lý bằng Python, chỉ in vài dòng.
5. Gọi song song **B1, B2** và **một agent theo mã cho mỗi mã** (lời giao việc ở `phien-chinh.md`). Tin "T1" của bản tin lấy từ mục "Tin doanh nghiệp", "Sự kiện công bố", "Hệ sinh thái" của `<W>/ma/<MÃ>.md`.
6. Gắn nhãn và ghi nhật ký số liệu (`phien-chinh.md`, bước 18–19); chỉ khi còn số quan trọng chưa ✔ mới gọi A5 (tối đa 10 dòng), không thì ghi nhật ký BỎ QUA.
7. `C tinh [--nghi yyyy-mm-dd …]`: điểm áp lực khối ngoại, chuỗi truyền dẫn, dự báo 6 phiên và biểu đồ các mã có biểu đồ, giá so với TB20 của các mã còn lại (`<W>/tb20.txt`). Không chạy `cycles.py`: vị trí chu kỳ = vị trí trong `MOC-THEO-DOI.md` cộng số phiên đã qua.
8. Viết **thân bản tin** theo mẫu vào `<W>/ban_tin.md`, phần đầu ghi chú vào `<W>/ghi_chu_dau.md`, và các mục tự viết của phụ lục vào `<W>/phu_luc_tu_viet.md` dưới đúng tiêu đề mẫu: luôn có `## Chưa kiểm chứng`, `## Đã thu thập nhưng không dùng`, `## Độ chính xác dự báo`, `## Tin nền tảng mới`, `## Lịch sự kiện 10 ngày tới` (lấy từ `MOC-THEO-DOI.md` cộng sự kiện mới của B2). Rồi `C ghep`: ghép `<W>/phu_luc.md` đúng mẫu phụ lục (mục thiếu ghi "(không có)") và ghi chú Obsidian bản tin. Lệnh in dòng "Nhật ký: …" thì thêm dòng đó vào mục "Dữ liệu" của `ban_tin.md` và chạy lại `C ghep`.
9. `C luu`, rồi `project_write` (với `local_path`) **đúng từng dòng** danh sách nó in ra, không thêm không bớt; ghi nhật ký bước 30; trả lời (bước 31).

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

## Mẫu phụ lục (`C ghep` dựng; tự điền các mục có file sẵn)
```
# Phụ lục bản tin [dd/mm]
## Kỹ thuật MBB, TCB (bản chữ chart6.py) và giá so với TB20 của các mã khác   ← <MÃ>-6-phien.txt, tb20.txt
## Thế giới đêm qua – đầy đủ                                                  ← ket_qua_B2.md
## Dòng vốn ngoại – bản chữ ap_luc_von_ngoai.py                               ← ap_luc.txt, ket_qua_B1.md
## Chuỗi truyền dẫn – bản chữ chuoi_truyen_dan.py                             ← chuoi.txt
## Tin nền tảng mới (mỗi tin một dòng kèm chuỗi tác động)                     ← phu_luc_tu_viet.md
## Tin doanh nghiệp không đưa lên thân bản tin                                ← ma/<MÃ>.md
## Doanh nghiệp và ngành tham chiếu – đầy đủ (B2, mục 4)                      ← tham_chieu_B2.csv
## Độ chính xác dự báo                                                        ← forecast6 + phu_luc_tu_viet.md
## Lịch sự kiện 10 ngày tới                                                   ← phu_luc_tu_viet.md
## Chưa kiểm chứng (mục · số · nguồn · vì sao)                                ← kiem_chung.md + phu_luc_tu_viet.md
## Đã thu thập nhưng không dùng (kèm lý do)                                   ← phu_luc_tu_viet.md
## Độ đầy đủ dữ liệu                                                          ← danh_muc_*.md
## Nguồn (kèm cấp 1/2/3)                                                      ← nguon_*.md
## Nhật ký chạy (nguyên văn research/nhat-ky-chay.txt)                        ← nhat-ky-chay.txt
```
Mọi tin bị bỏ khỏi thân bản tin vẫn phải có mặt ở phụ lục.

## Lưu
`C luu` chép giá về lịch sử, chạy `nen_du_lieu.py`, thêm `- Bản tin/<yyyy-mm-dd> Bản tin.md (cập nhật <yyyy-mm-dd>)` vào mục "Đang chờ đồng bộ" của `NHAC-DONG-BO.md`, và in danh sách file mới hoặc đã đổi so với lúc agent T tải xong. Danh sách thường gồm: ghi chú Obsidian bản tin (file mới duy nhất), các nhật ký CSV, file dự báo các mã có biểu đồ, `data/TOM-TAT.md`, `data/<MÃ>.csv`, `data/VNINDEX.csv`, `data/VN30.csv`, `data/vnd-cong-cu.txt`, `data/ban-chay-tot.txt` (khi lần chạy không lỗi), file `luu-tru/<tên>.csv` do `nen_du_lieu.py` tạo, `NHAC-DONG-BO.md`. Thiếu file nào trong số này (ví dụ lịch sử giá) nghĩa là bước trước đã lỗi: xem nhật ký.

**Không sửa ghi chú Obsidian sống** (`Mã/`, `Vĩ mô & dòng vốn/`, `00 Tổng quan.md`): phân tích sâu sẽ cập nhật chúng. Bản tin đã lưu không bao giờ bị sửa.

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
