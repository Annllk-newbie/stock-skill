# Chuỗi truyền dẫn vĩ mô (nút thắt quan sát)

Ai đọc: **agent tổng hợp (Sonnet) của phân tích sâu**. Phiên chính và bản tin sáng không đọc file này: bản tin sáng chỉ chép từ `chuoi.txt` theo quy tắc ghi trong `ban-tin-sang.md`.

Câu hỏi cần trả lời mỗi lần chạy: **cú sốc bên ngoài (dầu, Trung Đông, Fed, USD) đã truyền tới mắt xích nào trên đường vào cổ phiếu Việt Nam, và đứt ở đâu.** Sơ đồ quen thuộc "dầu → lạm phát → Fed → lãi suất → USD → lợi suất → thanh khoản → dòng vốn → chứng khoán" đúng hướng nhưng không phải domino; phần dưới là cách đọc nó bằng số.

## Mắt xích và nguồn số (đều đã có sẵn, không gọi thêm agent)

`chuoi_truyen_dan.py` đọc `data/von-ngoai.csv` và file giá VN-Index, in `<W>/chuoi.txt` (bản chữ) và `<W>/chuoi_truyen_dan.json`: từng mắt xích có số mới nhất, ngày, thay đổi, cờ ĐÁNG KỂ ↑/↓ hoặc "yên", rồi phần "Đọc chuỗi" (lực trên lợi suất Mỹ, cặp đã truyền, chỗ đứt, số thiếu, số cũ).

1. Cú sốc và kỳ vọng lạm phát: Brent (≥ 2%), breakeven Mỹ 5 năm (≥ 5 điểm cơ bản).
2. Fed, lợi suất, USD: xác suất Fed kỳ tới (≥ 10 điểm %), lợi suất Mỹ 2 và 10 năm (≥ 5 điểm cơ bản), DXY (≥ 0,5%).
3. Né rủi ro: VIX (≥ 10%), vàng (≥ 1%).
4. Việt Nam: giá bán USD Vietcombank (≥ 0,2%), liên ngân hàng qua đêm (≥ 0,5 điểm %), NHNN bơm/hút ròng.
5. Dòng vốn và kết quả: khối ngoại ròng HOSE, VN-Index (≥ 1%); từng mã lấy ở `tom_tat_script.md`.

Ngưỡng tính trên thay đổi qua 5 số gần nhất (không có thì số liền trước). Số của script mang nhãn của số gốc (✔/◐ trong `kiem-chung.csv` và cột `nguon`): số ◐ chỉ nhắc kèm "chưa xác nhận", mắt xích trống ghi "chưa có số liệu", **không suy ra từ mắt xích bên cạnh**.

## Sáu quy tắc đọc

1. **Không tuần tự.** Thị trường định giá kỳ vọng: lợi suất, USD và cổ phiếu có thể phản ứng cùng một phiên, trước cả CPI và Fed. Ghi mắt xích nào đã động, mắt xích nào chưa; không viết "A dẫn tới B" chỉ vì B đứng sau A trong sơ đồ.
2. **Phân loại cú sốc dầu.** Sốc cung (chiến tranh, OPEC cắt giảm) vừa đẩy lạm phát vừa kéo tăng trưởng xuống; dầu tăng vì cầu mạnh thường đi cùng cổ phiếu tăng. Chỉ gắn loại khi có tin có nguồn nêu nguyên nhân; không có thì ghi "chưa rõ loại cú sốc" và viết cả hai nhánh.
3. **Sốc cung không đồng nghĩa Fed tăng lãi suất.** Fed nhìn lạm phát lõi và kỳ vọng lạm phát. Dầu tăng mà breakeven 5 năm đứng yên là chuỗi đứt ngay mắt xích thứ hai.
4. **Hai lực ngược chiều trên lợi suất Mỹ:** lạm phát đẩy lên, né rủi ro kéo xuống. Dùng dòng "Lợi suất Mỹ" của script; không tự chọn lực.
5. **Đoạn Việt Nam có hai van.** NHNN (bán dự trữ, hút/bơm, tỷ giá trung tâm) có thể chặn DXY truyền vào USD/VND. Thanh khoản và margin của nhà đầu tư cá nhân thường quyết định VN-Index nhiều hơn khối ngoại: khối ngoại bán mà chỉ số không giảm là một chỗ đứt, không phải nghịch lý. Không quy biến động chỉ cho dòng vốn ngoại.
6. **Độ trễ và vòng ngược.** Dầu ngấm vào CPI khoảng 1–3 tháng, Fed phản ứng theo kỳ họp, cổ phiếu đi trước. Cổ phiếu giảm sâu làm điều kiện tài chính thắt lại, Fed có thể mềm giọng: mắt xích cuối tác động ngược lên mắt xích đầu.

**Chỗ đứt là thông tin quan trọng nhất.** Mỗi chỗ đứt script nêu: tìm trong file thu thập (V1, F1, F2, tham chiếu) một tin giải thích; có thì dẫn nguồn, không thì ghi "chưa rõ lý do". Trùng thời điểm chưa phải nguyên nhân (nguyên tắc chung của skill vẫn áp dụng).

## Kênh trực tiếp tới mã theo dõi (không qua Fed)

- **HPG:** than, điện, vận tải, quặng sắt (tin Petrolimex, EVN, TKV ở `tham-chieu.csv`; T2 thép).
- **MBB, TCB, CTG:** liên ngân hàng và lãi suất huy động (chi phí vốn), tỷ giá (dư nợ ngoại tệ của khách hàng), lợi suất trái phiếu (danh mục đầu tư), sức khỏe khách hàng vay chịu chi phí năng lượng.
Chỉ ghi kênh nào có tin hoặc số trong kỳ; không liệt kê cho đủ.

## Viết gì

Mục **"Chuỗi truyền dẫn"** của báo cáo (nằm trong "Toàn thị trường"), 6–10 dòng, viết thành câu, không bảng:
- Một dòng cho mỗi nhóm 1–5: số, nhãn, chiều; nhóm không có gì động thì gộp "yên".
- Cú sốc đang theo dõi và loại của nó (hoặc "Không có cú sốc mới từ bên ngoài" / "Chưa đủ số liệu để đọc chuỗi" theo đúng dòng script in, rồi dừng ở đó, không viết thêm).
- Lực đang thắng trên lợi suất Mỹ; đoạn đã truyền; từng chỗ đứt kèm lý do có nguồn hoặc "chưa rõ lý do".
- Kênh trực tiếp tới mã theo dõi nếu có.
- **Điều làm cách đọc này sai:** một điều kiện đo được (ví dụ "breakeven 5 năm tăng quá 10 điểm cơ bản trong tuần", "giá bán USD Vietcombank vượt mức cao nhất tháng").
- So với báo cáo sâu trước: chuỗi đã truyền thêm hay lùi lại mắt xích nào.

Chuỗi này bổ sung, không thay thế điểm áp lực khối ngoại của `ap_luc_von_ngoai.py`: không cộng hai thứ thành một điểm, không dùng chuỗi để dự báo hướng VN-Index hay từng mã. Ba kịch bản dòng vốn ngoại 1–2 tuần tới lấy "dấu hiệu xác nhận" từ chính các mắt xích ở đây. Đây là bức tranh rủi ro, không phải tín hiệu mua/bán.
