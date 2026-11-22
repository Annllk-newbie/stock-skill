# M-HPG – Tập đoàn Hòa Phát – phần riêng của mã

Agent M-HPG đọc file này cùng `agent-ma.md` (phần chung), `thu-thap.md`, `nhan.md`.

- **Cổ đông lớn, nội bộ:** ông Trần Đình Long và gia đình (giao dịch của ông Trần Vũ Minh đang theo dõi).
- **Công ty con, dự án:** Khu liên hợp Dung Quất 1 và 2, nhà máy thép ray Dung Quất, mỏ quặng ở Úc, Hòa Phát Nông nghiệp, điện máy gia dụng, khu công nghiệp.
- **Đầu vào:** quặng sắt (VND `SPOT_IRON_QINGDAO`), than cốc, điện (EVN). **Đầu ra:** xây dựng, bất động sản, đầu tư công (cao tốc, đường sắt tốc độ cao), xuất khẩu; giá HRC (VND `HRC_3MM_EXPORT`), CB240.
- **Ngành riêng:** sản lượng tiêu thụ hàng tháng; giá thép Trung Quốc và xuất khẩu thép Trung Quốc; thuế chống bán phá giá (HRC Trung Quốc vào Việt Nam; EU, Mỹ với thép Việt Nam); dự án lớn dùng thép (phần của HPG trong F5).
- **Hàng hóa VND (bước 1):** `get_change_prices` code `SPOT_IRON_QINGDAO,HRC_3MM_EXPORT`, period `1D` và `1M`. `price = 0` kèm `changePct = -100` là chưa cập nhật → ⊘, ghi `lastUpdated`.
- **So sánh cùng ngành (mã niêm yết):** HSG, NKG, TLH, POM.
- **Câu tìm mẫu:** "Hòa Phát <tháng năm>", "HPG sản lượng thép tháng", "Dung Quất 2", "chống bán phá giá thép <năm>", "giá thép Trung Quốc tuần".
