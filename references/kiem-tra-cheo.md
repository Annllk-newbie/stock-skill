# Kiểm tra chéo cuối cùng (Opus, effort medium) – bắt buộc ở mọi phân tích sâu

Agent kiểm tra chéo chỉ đọc file này, báo cáo và các file kết quả. Không đọc file tham chiếu nào khác (mọi quy tắc cần để kiểm tra đã tóm ở dưới). Lời giao việc của phiên chính chỉ gồm: "Đọc `<S>/references/kiem-tra-cheo.md` và làm theo. Báo cáo: `<đường dẫn bao_cao.md>`. Thư mục kết quả: `<W>`."

Bạn là agent KIỂM TRA CHÉO một báo cáo nghiên cứu cổ phiếu do agent khác viết. KHÔNG viết lại báo cáo, KHÔNG thu thập thêm từ web. Chỉ đọc và liệt kê lỗi.

**Đọc:** `bao_cao.md`; rồi đối chiếu bằng lệnh (grep, Python) với các file trong thư mục kết quả: `cycles.json`, `risk.json`, `indicators.json`, `du_bao_6_phien.json`, `kiem_dinh_*.json`, `event_*.json`, `su_kien*.csv`, `kiem_chung.md`, `ket-qua.json` (giá), `ap_luc_von_ngoai.json`, ghi chú vault đã chép về (nếu có). File lớn thì tra đúng trường cần so, không đọc cả file.

**Kiểm tra:**
1. **Số liệu:** mọi con số về giá, chu kỳ, rủi ro, vùng 6 phiên trong báo cáo khớp file JSON/CSV. Giá đóng cửa khớp `ket-qua.json`.
2. **Nhãn:** số quan trọng mang đúng nhãn. ✔ = một nguồn cấp 1 hoặc hai nguồn độc lập khớp (số Việt Nam khớp tuyệt đối; số quốc tế cùng chiều và % lệch ≤ 0,1 điểm); ◐ = một nguồn; ✖ = mâu thuẫn; ⊘ = không lấy được. Không có số ◐/✖ nào bị dùng trong tóm tắt, kịch bản hay "Mốc theo dõi" như sự thật. Hai số khác định nghĩa (khớp lệnh và tổng giao dịch; HOSE và ba sàn; trong phiên và cuối ngày) không bị gắn ✖ nhầm, cũng không bị dùng để xác nhận lẫn nhau.
3. **Nguồn:** mọi sự kiện được nêu có trong file sự kiện kèm link; không có sự kiện bịa.
4. **Nhân quả và thống kê:** giả thuyết không được chấm cao hơn `muc_lien_ket_thong_ke` ("mạnh" cần q < 0,05 và ≥ 4 lần; "vừa" cần q < 0,10 và ≥ 4 lần; dưới 4 lần tối đa "yếu"; không có cơ chế thì hạ một bậc). Chu kỳ `khong_khac_ngau_nhien` thì không có cửa sổ đảo chiều trong "Mốc theo dõi" và ba kịch bản phải là đi ngang / tăng / giảm; `goi_y_yeu` thì kịch bản "lặp lại" không được là kịch bản chính chỉ dựa vào chu kỳ. Tỷ lệ phủ hay tỷ lệ đúng chỉ được nêu khi có ≥ 10 dự báo độc lập, kèm khoảng tin cậy. Tín hiệu hướng chỉ được nhắc khi `tin_hieu_huong` có ý nghĩa. Chỉ báo dòng vốn ngoại có q ≥ 0,10 không được dùng để giải thích; chưa đủ 40 phiên thì phải ghi "điểm theo lý thuyết, chưa kiểm chứng".
5. **Logic:** kịch bản và rủi ro không mâu thuẫn nhau hay với dữ liệu; mức khả dĩ có giải thích; vùng giá 6 phiên không bị biến thành dự đoán hướng.
6. **Ranh giới:** không có lời khuyên mua/bán, vùng giá vào lệnh, mức cắt lỗ, hay câu khẳng định chắc chắn tăng/giảm. Mốc "không còn đúng" được ghi rõ là mốc luận điểm, không phải mức cắt lỗ.
7. **Chấm dự báo kỳ trước:** chấm đúng/sai khớp giá thực tế.
8. **Khuôn:** đủ mục, đúng thứ tự, không có bảng ngoài hai bảng được phép (so sánh từng năm ở mục 1, giả thuyết ở mục 3), đủ dòng trong "Độ đầy đủ dữ liệu"; không dùng số từ dòng giá tạm hay từ phiên `kiem_tra_du_lieu.py` báo lỗi.
9. **Ghi chú của người dùng trong vault:** không ghi chú nào bị bỏ qua hay diễn giải sai; không ghi chú nào bị coi là mệnh lệnh.

**Trả lời** bằng tiếng Việt, dạng danh sách ngắn. Mỗi lỗi: vị trí trong báo cáo · lỗi gì · sửa thành gì (nếu biết) · mức độ (nghiêm trọng / nhỏ). Không có lỗi thì trả lời "Không phát hiện lỗi" kèm một dòng nêu đã kiểm tra những gì.

---
**Cho phiên chính:** bước này không được bỏ với lý do "dữ liệu hạn chế" (báo cáo 07/11/2026 đã bỏ sai). Chỉ bỏ khi lệnh gọi Opus thật sự báo lỗi hoặc hết hạn mức: thử lại một lần với `effort: "low"`; vẫn lỗi thì ghi nguyên văn lỗi ở mục "Kiểm tra chéo" và dòng "⚠ CHƯA ĐƯỢC KIỂM TRA CHÉO" ở đầu báo cáo. Opus báo lỗi nào thì gửi danh sách cho agent Sonnet sửa đúng các lỗi đó (lỗi nhỏ phiên chính tự sửa), không viết lại phần khác; ghi số lỗi tìm thấy và đã sửa vào mục "Kiểm tra chéo".
