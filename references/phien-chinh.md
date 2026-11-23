# Phiên chính (file duy nhất phiên chính đọc, cùng `nguyen-tac.md`)

## Phiên chính: điều phối (cả hai chế độ)

Ai đọc: phiên chính, ngay sau SKILL.md, cùng `nguyen-tac.md`. File này gồm phần chung (dưới đây) và hai mục theo chế độ: "Chế độ B: Bản tin sáng" và "Chế độ A: Phân tích sâu". Không đọc `thu-thap.md` hay `tong-hop.md`: đó là việc của agent.

`<S>` = `research/skill` (bản clone kho GitHub) · `<W>` = `research/` · "dự án" = `claude/chung-khoan/` trong Project "Economy and trading".

### Lệnh điều phối `chay.py`
Mọi việc script làm bằng `C` = `python <S>/scripts/chay.py <ban-tin|sau|sau-nhe> <lệnh>`, đúng thứ tự `bat-dau` → `gia` → `tinh` → `ghep` → `luu` (thứ tự đầy đủ kèm các việc không phải script: `C ke-hoach`). Mỗi lệnh tự ghi nhật ký chạy và chỉ in kết quả ngắn: đọc phần in ra, không mở file kết quả. Không gõ tay lệnh của từng script; script nào cần chạy riêng (ví dụ `kiem_dinh.py fdr`, `event_study.py`) thì chạy qua `N chay` (mục "Nhật ký chạy").

### Tiết kiệm token (bắt buộc)
- **Không tự gọi `project_read`:** nội dung file sẽ nằm lại trong ngữ cảnh suốt lần chạy. Giao cho agent T (mục "Thẻ T" của `thu-thap.md`). Không gọi `project_info`. Không bao giờ chép tay nội dung file ra đĩa.
- **Mọi file lưu vào dự án dùng `project_write` với `local_path`**, đúng danh sách `C luu` in ra. Không dán nội dung CSV/JSON vào câu trả lời, suy nghĩ hay lời giao việc; xử lý bằng Python, chỉ in vài dòng.
- **Lời giao việc cho agent chỉ vài dòng** (mục "Giao việc"): agent nhận đường dẫn, không nhận nội dung, và trả lời ngắn.
- Không đọc bản tin hay báo cáo cũ bản đầy đủ: trạng thái cần cho lần chạy nằm ở `data/TOM-TAT.md` và `data/MOC-THEO-DOI.md`.

### Phân công mô hình (quy tắc của người dùng)
Mọi việc thu thập và tải dữ liệu dùng Haiku; Sonnet chỉ tổng hợp, phân tích, điều phối; kiểm tra cuối cùng là Opus.
- Phiên chính (Sonnet): điều phối, chạy `chay.py`, gọi VND MCP phần chung, gắn nhãn, lưu, gửi. Không tự đọc web.
- Agent T: Haiku, effort low. Thu thập B, A-chung, A-ma và kiểm chứng A5: Haiku, effort medium.
- Chỉ phân tích sâu: tổng hợp (Sonnet, effort high), kiểm tra chéo (Opus, effort medium, **bắt buộc**), agent O (Sonnet, effort low).

**Số agent mỗi lần chạy (cố định, không tự thêm):**
- Bản tin sáng: **2** = T · B (một agent thu thập làm cả tin chung lẫn từng mã); thêm A5 chỉ khi còn số quan trọng chưa ✔ (tối đa 3).
- Phân tích sâu (cả hai mức): **7** = T · A-chung (lịch, vĩ mô, quốc tế, tin nền tảng) · A-ma (mọi mã) · A5 · tổng hợp · kiểm tra chéo · O. Sửa lỗi sau kiểm tra chéo gửi lại cho chính agent tổng hợp (SendMessage), không tạo agent mới.
Thêm mã vào danh sách theo dõi không thêm agent: A-ma và B làm lần lượt mọi mã. Cuối báo cáo ghi một dòng: mô hình nào đã thu thập, tổng hợp, kiểm tra.

### Giao việc (lời giao việc mẫu; không chép quy tắc vào)
Mọi lời giao việc gồm: tên agent · câu "Đọc `<S>/references/nguyen-tac.md` và `<S>/references/thu-thap.md` rồi làm đúng các thẻ ghi dưới đây" · tham số chung: phiên cần lấy, ngày lần chạy trước, danh sách mã, `<W>`, đường dẫn `<W>/du-an/data/TOM-TAT.md`.
- **T:** mục "Thẻ T"; thêm chế độ (B/A), `<S>`.
- **B (bản tin sáng):** mục "Thẻ B2" rồi mục "Agent theo mã" (chế độ B) cho từng mã; thêm Brent và % từ VND, sự kiện F1/F2 trong lịch 24 giờ qua, giá đóng cửa và nhãn VND của từng mã, câu "VND hoạt động (health ok)".
- **A-chung (phân tích sâu):** lần lượt mục "Thẻ A2", "Thẻ A3" và (chỉ bản đầy đủ) "Thẻ A4"; thêm mức chạy.
- **A-ma (phân tích sâu):** mục "Agent theo mã" (chế độ A-đầy đủ / A-cập nhật) cho từng mã; thêm giá đóng cửa và nhãn VND của từng mã, câu "VND hoạt động (health ok)".
- **A5:** mục "Thẻ A5".
- **Tổng hợp, kiểm tra chéo, O:** xem mục "Chế độ A".

### VND MCP (nguồn giá duy nhất; phiên chính làm trước khi giao việc)
1. ToolSearch với đúng từ khóa `mcp__VND__` (max_results 40) để nạp công cụ; KHÔNG dùng từ khóa khác. Gọi `mcp__VND__health`.
2. Ghi lại mọi **thông báo của VND** (cảnh báo, bảo trì, cập nhật phần mềm/hệ thống, công cụ đổi tên hoặc ngừng – trong kết quả health, kết quả từng lệnh, hoặc mô tả công cụ), chép nguyên văn vào trường `thong_bao` của `<W>/gia/vnd.json`; `C gia --cong-cu` so danh sách công cụ với `data/vnd-cong-cu.txt` và báo công cụ mới/bị bỏ. Có thông báo hoặc công cụ đổi thì đưa một dòng lên đầu bản tin/báo cáo ("VND cập nhật hệ thống: …") và ghi đủ ở mục "Dữ liệu".
3. Gọi MỘT lượt, rồi chép đúng các trường cần (xem đầu `<S>/scripts/gia_vnd.py`) vào `<W>/gia/vnd.json`, không chép thêm gì:
   - `get_trading_calendar` (date = ngày mai, size 1): phiên gần nhất đã đóng cửa; trước 15:05 không dùng phiên hôm nay.
   - `get_stock_price_by_date`: mọi mã một lần gọi cho MỖI phiên còn thiếu kể từ phiên cuối của bản lưu. `adClose/adOpen/adHigh/adLow` nghìn đồng, đã điều chỉnh; `nmVolume` cp. Đọc theo trường `code`, không theo thứ tự dòng.
   - `get_vnmarket_prices`: **MỖI CHỈ SỐ một lần gọi** (VNINDEX, VN30), mỗi phiên thiếu: kết quả không có trường mã và thứ tự dòng không theo thứ tự yêu cầu. `accumulatedVal` = tổng giá trị gồm thỏa thuận (đồng).
   - `get_foreign_trading` (code `VNINDEX`, size ≥ số phiên): khối ngoại toàn sàn, `netVal` đồng → chia 1e9 ra tỷ; tổng sàn lấy dòng VNINDEX, không cộng từng mã. Ghi vào `data/von-ngoai.csv` (cột `kn_rong_hose_ty`).
   - `get_change_prices` (Brent `GEN1ST_BRENT_OIL`, vàng `SPOT_GOLDS`; period 1D/1W/1M): `price = 0` kèm `changePct = -100` nghĩa là chưa cập nhật → ⊘, KHÔNG phải giảm 100%; kiểm `lastUpdated`.
   - Khi cần giải thích nhịp VN-Index: `get_positive_foreign_net_value`, `get_industry_classification`, `get_vnindex_leaderlarger`.
4. Phần theo từng mã (khối ngoại theo mã, định giá, sự kiện công bố, ban lãnh đạo, hàng hóa riêng) do agent theo mã gọi. Agent thu thập khác không gọi VND. Mọi số từ VND ghi nguồn "VND MCP + ngày giao dịch".
5. Chỉ khi health hoặc lệnh gọi lại một lần vẫn lỗi mới coi là VND lỗi → mục "Khi DỪNG". Không bao giờ ghi "không phản hồi" khi chưa gọi.

### Giá
- Lịch sử giá khoảng 6 năm lấy từ dự án (`data/<MÃ>.csv`, `data/VNINDEX.csv`, `data/VN30.csv`, agent T tải); VND không có lệnh lấy lịch sử dài. `C gia --phien <phiên> --cong-cu "<tên công cụ mcp__VND__ đã nạp, cách nhau dấu phẩy>"` (sau khi agent T xong) chạy `gia_vnd.py` rồi `kiem_tra_du_lieu.py`: nối phiên mới, tự điều chỉnh lịch sử khi có sự kiện quyền, kiểm tra nội tại, gắn nhãn. Lệnh in `tom_tat`, `chi_so`, `vnd`, mã không ✔ hoặc có `dieu_chinh`, kết quả kiểm tra file giá.
- `kiem_tra` có `loi`: không dùng phiên đó cho dự báo, ghi ở mục "Dữ liệu"; `dong_tam` chỉ được tồn tại ở phiên cuối. Có `dieu_chinh`: đối chiếu `get_company_events` của mã để xác nhận sự kiện quyền, ghi ở mục "Dữ liệu".
- Mã ✔: không agent nào tìm giá mã đó nữa. Mã thoát 2 (`"dung": true`): bù phiên thiếu nếu lý do là `⊘ chưa có phiên` (kiểm `get_trading_calendar` xem còn thiếu phiên nào, gọi `get_stock_price_by_date` cho từng phiên, thêm vào `vnd.json`, chạy lại `C gia`); vẫn mã 2 thì "Khi DỪNG".
- **Mã người dùng hỏi mà không có trong danh sách theo dõi:** giá lấy từ file người dùng gửi, hoặc từ VND (`get_stock_price_by_date` theo ngày) khi chỉ cần vài phiên; không có lịch sử thì báo người dùng, KHÔNG lấy giá trên web. `chay.py` và `forecast6.py` dùng biên độ HOSE ±7%: mã HNX/UPCoM cần `--gioi-han 0.10`/`0.15` khi chạy riêng `forecast6.py`.
- `<W>/gia/gia_<MÃ>_ctck.csv` (cột `date,open,high,low,close,volume`, nghìn đồng, đã điều chỉnh) là file giá cho MỌI script; `C luu` chép về `data/` để thành lịch sử giá duy nhất.

### Gắn nhãn, A5 và ghi nhật ký số liệu (bước 18–19)
Sau khi các agent thu thập xong: gắn nhãn theo `nguyen-tac.md` (mục "Nhãn") (giá và chỉ số VND đã có nhãn); gom số quan trọng chưa ✔ vào `<W>/can_kiem_chung.md` (mỗi dòng: mục, số, nguồn hiện có) rồi gọi A5 theo chế độ (kết quả ở `<W>/kiem_chung.md`, cập nhật nhãn theo đó). Rồi ghi thêm dòng vào các file nhật ký số liệu (cột ở mục dưới) trong `<W>/du-an/` bằng Python, chỉ thêm dòng:
- `data/von-ngoai.csv`: khối ngoại toàn sàn (VND), Brent, vàng (VND), các cột ở mục "Dòng tiền Việt Nam" của `ket_qua_B2.md` (bản tin) và số Mỹ/Fed của `ket_qua_B2.md`/`ket_qua_A3.md` (DXY, lợi suất, breakeven, VIX, xác suất Fed).
- `data/kiem-chung.csv`: mọi số quan trọng kèm nhãn cuối cùng.
- `data/tham-chieu.csv`: dòng của `tham_chieu_B2.csv` hoặc `tham_chieu_A2.csv` (bỏ dòng trùng).
- `su-kien-nen-tang.csv`: tin F1–F7 mới (từ `ket_qua_A3.md`, `ket_qua_A4.md`; bản tin sáng: tin chung của B2 thuộc nhóm F) kèm chuỗi tác động.
- Sự kiện theo mã (chỉ phân tích sâu): không ghi tay, `C tinh` tự ghép.

### Cột và cách ghi các file nhật ký số liệu (chỉ thêm dòng)
- `data/kiem-chung.csv` (cột `ngay_du_lieu,muc,gia_tri,nhan,nguon_1,nguon_2,cap_cao_nhat,ghi_chu,ngay_kiem`). Số được đính chính thì nêu ở mục "Dữ liệu" của bản kế tiếp.
- `data/von-ngoai.csv`: mỗi lần chạy thêm một dòng cho mỗi phiên còn thiếu, đúng cột ghi ở đầu `ap_luc_von_ngoai.py`, cộng ba cột `lam_phat_ky_vong_5y` (breakeven Mỹ 5 năm, FRED chuỗi `T5YIE`), `vix`, `vang` của `chuoi_truyen_dan.py` (`chay.py tinh` tự thêm cột nếu file cũ chưa có). Khối ngoại ròng HOSE lấy từ VND (`get_foreign_trading` code VNINDEX). Chỉ ghi số ✔; số ◐ ghi kèm nhãn trong cột `nguon`; số ✖ để trống. Ô không lấy được để trống, không chép số cũ sang ngày mới. Số theo tuần (ETF, khu vực) ghi ở ngày công bố. Không sửa số đã có trừ khi có nguồn đính chính (ghi lý do vào `nguon`). Mỗi lần chạy lấy bù khoảng 1 tuần số cũ của DXY, lợi suất Mỹ 10 năm, giá USD Vietcombank và khối ngoại HOSE cho đến khi file đủ 8 tuần.
- `su-kien-nen-tang.csv` (cột `date,nhom,su_kien,tac_dong_du_kien,source_url,reliability,note`; `nhom` là F1–F7); `tac_dong_du_kien` là chuỗi nhân quả ngắn ở cấp thị trường.
- `data/tham-chieu.csv` (cột `ngay,doanh_nghiep,tin,kenh_anh_huong,ma_lien_quan,nhan,nguon`).
- `<MÃ>/su-kien.csv` (cột `date,event,group,source_url,reliability,note`; chỉ phân tích sâu ghép thêm; không cắt; không ghi ngày đáo hạn VN30F vào đây, `chay_sau.py` tự sinh).

### Dự báo xác suất (`du_bao_xs.py`, cả hai chế độ; `C tinh` tự chạy)
Thay cho "kịch bản chính" tự viết. Với mỗi mã và kỳ hạn 5, 20 phiên: xác suất giá đóng cửa sau h phiên cao hơn hôm nay, mức cơ sở (tỷ lệ tăng trong quá khứ) và vùng 80%. Script tự kiểm chứng trên toàn bộ lịch sử giá (gộp mọi mã, chọn tín hiệu ở 60% đầu, chấm ở 40% sau chưa nhìn thấy) và tự chấm các dự báo cũ trong `data/du-bao-xs.json`.
- Kết luận `CÓ lợi thế`: được nêu xác suất kèm tên tín hiệu đã giữ. Kết luận khác: xác suất công bố CHÍNH LÀ mức cơ sở; luôn ghi kèm "chưa có tín hiệu nào đoán hướng tốt hơn tỷ lệ tăng trong quá khứ".
- Độ chính xác thật (Brier so với mức cơ sở, độ phủ vùng 80%) chỉ được nêu như kết luận khi đã có ≥ 30 dự báo đã chấm; ít hơn thì ghi "chưa đủ để đánh giá".
- Không biến xác suất thành lời khuyên mua/bán; không tự sửa con số của script.

### Nhật ký chạy (bắt buộc)
Mỗi bước một dòng trong `<W>/nhat-ky-chay.txt`. `N` = `python <S>/scripts/nhat_ky.py`.
- `chay.py` tự ghi mọi bước script bên trong (01, 04, 05, 20–24, 28, 29): không ghi lại.
- Script chạy riêng: `N chay --buoc "<tên bước>" -- python <S>/scripts/<script>.py …` (chuyển hướng `>` đặt sau cùng như bình thường).
- Việc không phải script (VND MCP, agent, `project_write`, SendUserFile, PushNotification): làm xong thì `N ghi --buoc "<tên bước>" --trang-thai <ok|canh-bao|loi|bo-qua|dung> --chi-tiet "<ngắn; khi lỗi chép NGUYÊN VĂN thông báo lỗi>"`. Agent trả lời đủ file → ok; thiếu mục hoặc có số ⊘ → canh-bao (ghi thiếu gì); lỗi hoặc không ghi ra file → loi. Bước cố ý không làm (A5 khi mọi số đã ✔, A4 ở bản cập nhật) → bo-qua kèm lý do.
- **Tên bước cố định** (giữ nguyên chữ và số; bước không có ở chế độ đó thì bỏ): `01 Tải code GitHub` · `02 VND health và công cụ` · `03 VND lịch, giá, chỉ số, khối ngoại sàn` · `04 gia_vnd.py` · `05 kiem_tra_du_lieu.py` · `06 Agent T` · `07 Đồng bộ và liệt kê vault` · `08 Chấm dự báo kỳ trước` · `09 Agent B` (bản tin sáng) · `11 Agent A-chung` · `14 Agent A-ma` · `18 Agent A5` · `19 Gắn nhãn và ghi nhật ký CSV` · `20 ap_luc_von_ngoai.py` · `21 chuoi_truyen_dan.py` · `22 forecast6/chart6 MBB` · `23 forecast6/chart6 TCB` · `24 chay_sau.py` · `25a du_bao_xs.py` · `25 Agent tổng hợp` · `26 Kiểm tra chéo Opus` · `27 Agent O` · `28 Viết bản tin/báo cáo và phụ lục` · `29 nen_du_lieu.py` · `30 Lưu vào dự án` · `31 Gửi người dùng`.
- `C ghep` đưa nguyên văn nhật ký vào cuối phụ lục/báo cáo và in dòng "Nhật ký: …" khi có bước không OK: thêm dòng đó vào mục "Dữ liệu". Bước 30–31 xảy ra sau khi ghép: lỗi thì đưa dòng đó vào câu trả lời cuối.
- Nhật ký ghi "LỖI CODE của skill" → mục "Khi code mới lỗi" của SKILL.md.

### Dữ liệu trong dự án
Mỗi lần chạy theo lịch là một phiên mới, không nhớ gì, nên trạng thái nằm trong dự án. Không có công cụ Projects thì vẫn làm và ghi ở đầu báo cáo là không so được với lần trước.
- **Đọc đầu mỗi lần chạy:** qua agent T (danh sách cố định ở mục "Thẻ T" của `thu-thap.md`).
- **Ghi mỗi lần chạy: đúng MỘT file mới** – ghi chú Obsidian của lần chạy (`obsidian/Bản tin/<yyyy-mm-dd> Bản tin.md` hoặc `obsidian/Báo cáo sâu/<yyyy-mm-dd> Phân tích sâu.md`), chứa cả tóm tắt và toàn văn. Mọi thứ khác là ghi đè file trạng thái đã có. `C luu` in đúng danh sách file mới hoặc đã đổi; không tạo file nào ngoài danh sách đó, không tạo file theo ngày, theo quý hay theo mã. Code skill không nằm trong dự án.
- **Số file không tăng theo thời gian:** vault Obsidian là kho lưu trữ. Skill `dong-bo-obsidian` xóa khỏi dự án các ghi chú bản tin/báo cáo cũ hơn 14 ngày đã có trong vault và chuyển các dòng trong `luu-tru/<tên>.csv` vào vault. Các lần chạy không tự xóa file nào. Ảnh biểu đồ không lưu vào dự án.

### Khi DỪNG (VND lỗi, hoặc `C gia` vẫn mã 2)
Giá và chỉ số chỉ lấy từ VND MCP. Trước khi kết luận VND lỗi: đã nạp công cụ bằng ToolSearch `mcp__VND__`, đã gọi `mcp__VND__health`, đã gọi lại đúng lệnh bị lỗi MỘT lần (gặp "throttled" thì chờ 20 giây). Vẫn lỗi thì **DỪNG cả lần chạy**: không lấy giá từ web, không gọi agent thu thập, không chạy script phân tích, không viết bản tin hay báo cáo, không ghi gì vào dự án. Chỉ làm ba việc:
1. `N ghi --buoc "<bước lỗi>" --trang-thai dung --chi-tiet "<nguyên văn lỗi>"` (`C gia` đã tự ghi nếu lỗi ở đó).
2. Gửi thông báo cho người dùng (lần chạy theo lịch: PushNotification): "Dừng: không lấy được giá từ VND MCP", lệnh đã gọi, nguyên văn lỗi, giờ thử, và nguyên kết quả `N tom-tat`.
3. Trả lời đúng nội dung đó.

### Khi một agent lỗi hoặc hết hạn mức
Chỉ khi lệnh gọi thật sự báo lỗi (không phải phán đoán "không cần"). Không chạy lại cả quy trình; luôn lưu những gì đã thu thập.
- Agent T lỗi, không có công cụ Projects, hoặc `da_luu` rỗng: phiên chính tự gọi `project_read` cho các đường dẫn trong mục "Thẻ T" của `thu-thap.md` rồi chạy `python <S>/scripts/du_an.py luu --out <W>/du-an` (không chép tay nội dung). File dự án chưa có (lần đầu) thì bỏ qua và ghi ở mục "Dữ liệu".
- Agent thu thập hoặc agent theo mã lỗi: ghi nhật ký `loi`; mục của agent đó trong "Độ đầy đủ dữ liệu" ghi "không lấy được – agent lỗi"; không tự đi tìm thay.
- A5 lỗi: giữ nhãn ◐.
- Tổng hợp, kiểm tra chéo, agent O lỗi: theo `phien-chinh.md` (mục "Chế độ A").
- Phiên không có công cụ Agent hoặc thiếu một mô hình: phiên chính tự làm và ghi rõ trong báo cáo.

## Chế độ B: Bản tin sáng

Mục tiêu: **một màn hình điện thoại** (thân bản tin tối đa khoảng **150 từ**, 6–9 dòng ngắn, không tính ảnh). Chỉ cung cấp thông tin: không phân tích lại nguyên nhân, không chạy lại kiểm định, không gọi Sonnet agent hay Opus, không đọc vault, không đọc bản tin hay báo cáo cũ. Mọi thứ còn lại (kỹ thuật, chuỗi truyền dẫn, tham chiếu, kiểm chứng…) nằm ở **phụ lục**, không mất đi đâu.

### Quy trình (`C` = `python <S>/scripts/chay.py ban-tin`)

0. Hôm nay là thứ 2 hoặc không phải ngày sau một phiên giao dịch (nghỉ lễ) thì dừng, trả lời một dòng. Bản tin chạy sáng thứ 3, 4, 5, 6 và gộp mọi phiên kể từ bản tin hoặc báo cáo sâu trước (thứ 3 gộp phiên thứ 2; ngày nào lỡ chạy thì bản kế tiếp gộp bù).
1. `C bat-dau --ma <DANH_SÁCH_MÃ> --bieu-do <các mã có biểu đồ>` (ngay sau khi clone code).
2. **Song song:** gọi agent T (chế độ B); trong lúc đó gọi VND theo mục "VND MCP" và ghi `<W>/gia/vnd.json`.
3. Agent T xong: `C gia --phien <phiên gần nhất đã đóng cửa> --cong-cu "<tên các công cụ mcp__VND__ đã nạp>"`. Mã thoát 2 → bù phiên thiếu hoặc DỪNG theo mục "Khi DỪNG".
4. Đọc từ đĩa: `<W>/du-an/data/TOM-TAT.md` và `<W>/du-an/data/MOC-THEO-DOI.md`. Không đọc các CSV: xử lý bằng Python, chỉ in vài dòng.
5. Gọi **agent B** (agent thu thập duy nhất, làm cả tin chung lẫn từng mã; lời giao việc ở mục "Giao việc"). Agent B ghi `ket_qua_B2.md`, `tham_chieu_B2.csv` và `ma/<MÃ>.md` của từng mã. Tin "T1" lấy từ mục "Tin doanh nghiệp", "Sự kiện công bố", "Hệ sinh thái" của `<W>/ma/<MÃ>.md`.
6. Gắn nhãn và ghi nhật ký số liệu (mục "Gắn nhãn, A5 và ghi nhật ký số liệu"); chỉ khi còn số quan trọng chưa ✔ mới gọi A5 (tối đa 10 dòng), không thì ghi nhật ký BỎ QUA.
7. `C tinh [--nghi yyyy-mm-dd …]`: điểm áp lực khối ngoại, chuỗi truyền dẫn, dự báo 6 phiên và biểu đồ các mã có biểu đồ, giá so với TB20 của các mã còn lại (`<W>/tb20.txt`), và **dự báo xác suất** của mọi mã (`<W>/du_bao_xs.txt`, xem mục "Dự báo xác suất"). Không chạy `cycles.py`.
8. Viết **thân bản tin** theo mẫu vào `<W>/ban_tin.md`, phần đầu ghi chú vào `<W>/ghi_chu_dau.md`, và các mục tự viết của phụ lục vào `<W>/phu_luc_tu_viet.md` dưới đúng tiêu đề mẫu: luôn có `## Chưa kiểm chứng`, `## Đã thu thập nhưng không dùng`, `## Tin nền tảng mới`, `## Lịch sự kiện 10 ngày tới` (lấy từ `MOC-THEO-DOI.md` cộng sự kiện mới của agent B), và `## Từng mã – đầy đủ` (mỗi mã: giá, %, KL so với TB20, vùng 80% phiên 6, chu kỳ theo `MOC-THEO-DOI.md`, mốc, tin T1). Rồi `C ghep`. Lệnh in dòng "Nhật ký: …" thì thêm dòng đó vào dòng "Dữ liệu" của `ban_tin.md` và chạy lại `C ghep`.
9. `C luu`, rồi `project_write` (với `local_path`) **đúng từng dòng** danh sách nó in ra, không thêm không bớt; ghi nhật ký bước 30; trả lời (bước 31).

### Quy tắc lọc cho thân bản tin
- Chỉ đưa vào điều **khác hôm qua** hoặc **cần chú ý hôm nay**: mốc bị chạm, giá ra ngoài vùng 80%, khối lượng ≥ 1,5 lần TB20, giá thay đổi ≥ 2 lần độ lệch chuẩn ngày, tin T1 của mã theo dõi, chỗ đứt mới của chuỗi truyền dẫn so với `MOC-THEO-DOI.md`, tin nền tảng làm đổi điểm áp lực khối ngoại, sự kiện trong 3 phiên tới. Còn lại để phụ lục.
- Chỉ dùng số ✔, không gắn nhãn từng số (dòng đầu đã ghi tổng). Số ◐ ghi "[mục] chưa xác nhận"; số ✖ ghi "[mục]: các nguồn mâu thuẫn".
- Mỗi mã đúng **một dòng**: giá và %; thêm tối đa một ý (tin T1, ngoài vùng 80%, mốc bị chạm, KL ≥ 1,5 lần TB20) khi có. Chu kỳ, kỹ thuật, TB20 để ở phụ lục.
- Dòng **Xác suất** chép từ `du_bao_xs.txt` (kỳ hạn 5 phiên). Khi kết luận kiểm chứng KHÁC "CÓ lợi thế": ghi đúng "(chưa có tín hiệu nào đoán hướng tốt hơn tỷ lệ tăng trong quá khứ)". Không tự diễn giải con số thành nên mua/bán.
- Không bảng, không biểu đồ chữ, không lặp số đã có trong ảnh `chart6.py`.

### Mẫu thân bản tin (giữ đúng thứ tự và tên dòng mọi ngày; tối đa ~150 từ)
```
# Bản tin [thứ dd/mm] · x ✔ · y ◐ · z ✖ · w ⊘
**Đáng chú ý:** [1–2 câu, quan trọng nhất trước; không có thì "Không có thay đổi lớn so với hôm qua"]
**Thị trường:** VN-Index [điểm] ([%]) · khối ngoại HOSE [ròng] tỷ · áp lực bán [x/100] · thế giới: [biến động đáng kể hoặc "yên ắng"]
- MBB [giá] ([%])[ · một ý nếu có]
- TCB [giá] ([%])[ · một ý nếu có]
- CTG [giá] ([%])[ · một ý nếu có]
- HPG [giá] ([%])[ · một ý nếu có]
**Xác suất tăng sau 5 phiên:** MBB [a]% · TCB [b]% · CTG [c]% · HPG [d]% [ghi chú khi không có tín hiệu]
**Lịch 3 phiên:** [tối đa 2 sự kiện; không có thì bỏ dòng]
**Dữ liệu:** [ổn / vấn đề ngắn] · Phụ lục: file gửi kèm và cuối ghi chú Bản tin/<yyyy-mm-dd> Bản tin
```
Thế giới chỉ nêu biến động đáng kể (S&P 500/Nasdaq ≥ 1%, lợi suất Mỹ 10 năm ≥ 5 điểm cơ bản, DXY ≥ 0,5%, dầu ≥ 2%, châu Á ≥ 1,5%). Điểm áp lực thêm "chưa kiểm chứng" khi chưa đủ 40 phiên.

### Mẫu phụ lục (`C ghep` dựng; tự điền các mục có file sẵn)
```
# Phụ lục bản tin [dd/mm]
## Từng mã – đầy đủ                                                           ← phu_luc_tu_viet.md
## Kỹ thuật MBB, TCB (bản chữ chart6.py) và giá so với TB20 của các mã khác   ← <MÃ>-6-phien.txt, tb20.txt
## Dự báo xác suất (du_bao_xs.py)                                             ← du_bao_xs.txt
## Thế giới đêm qua – đầy đủ                                                  ← các mục còn lại của ket_qua_B2.md
## Dòng vốn ngoại – bản chữ ap_luc_von_ngoai.py                               ← ap_luc.txt, mục "Dòng tiền Việt Nam" của ket_qua_B2.md
## Chuỗi truyền dẫn – bản chữ chuoi_truyen_dan.py                             ← chuoi.txt
## Tin nền tảng mới (mỗi tin một dòng kèm chuỗi tác động)                     ← phu_luc_tu_viet.md
## Tin doanh nghiệp không đưa lên thân bản tin                                ← ma/<MÃ>.md
## Doanh nghiệp và ngành tham chiếu – đầy đủ (B2, mục 4)                      ← tham_chieu_B2.csv
## Độ chính xác dự báo                                                        ← forecast6 + lịch sử du_bao_xs
## Lịch sự kiện 10 ngày tới                                                   ← phu_luc_tu_viet.md
## Chưa kiểm chứng (mục · số · nguồn · vì sao)                                ← kiem_chung.md + phu_luc_tu_viet.md
## Đã thu thập nhưng không dùng (kèm lý do)                                   ← phu_luc_tu_viet.md
## Độ đầy đủ dữ liệu                                                          ← danh_muc_*.md
## Nguồn (kèm cấp 1/2/3)                                                      ← nguon_*.md
## Nhật ký chạy (nguyên văn research/nhat-ky-chay.txt)                        ← nhat-ky-chay.txt
```
Mọi tin bị bỏ khỏi thân bản tin vẫn phải có mặt ở phụ lục.

### Lưu
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

### Câu trả lời cuối (thông báo điện thoại)
Đúng nguyên văn thân bản tin (một màn hình), cộng (chỉ khi bước 30 hoặc 31 của nhật ký không OK) dòng nhật ký đó, cộng một dòng: "Obsidian: N file chờ đồng bộ – sẽ được chép khi bạn bấm chạy Phân tích sâu (hoặc gõ 'đồng bộ Obsidian' trên máy tính)." Gửi kèm `MBB-6-phien.png`, `TCB-6-phien.png` và `<W>/phu_luc.md` bằng SendUserFile nếu có.

## Chế độ A: Phân tích sâu – phiên chính

Phiên chính đọc file này sau `phien-chinh.md`, `nguyen-tac.md`, `nguyen-tac.md` (mục "Nhãn"). Không đọc `tong-hop.md` hay thẻ việc của agent, không tự đọc nội dung ghi chú, CSV hay JSON: việc đó thuộc về agent và script.

### Hai mức chạy (xác định theo ngày giờ Việt Nam lúc bấm chạy)
- **Bản đầy đủ (`sau`) – tối thứ 6, thứ 7, chủ nhật:** tổng kết tuần. Thu thập đủ danh mục (A-chung làm thẻ A2, A3, A4; A-ma ở chế độ A-đầy đủ), tìm rộng sự kiện quá khứ còn thiếu, báo cáo viết đủ mọi mục; kịch bản và lịch cho cả tuần sau.
- **Bản cập nhật (`sau-nhe`) – tối thứ 2 đến thứ 5:** chỉ những gì đổi trong tuần. A-chung làm thẻ A2, A3 (bỏ A4), A-ma ở chế độ A-cập nhật; không tìm rộng sự kiện quá khứ; các mục theo tuần (F3–F7, T2) ghi "chỉ thu thập ở bản đầy đủ cuối tuần" trong "Độ đầy đủ dữ liệu".
- Cả hai mức: script chạy đủ (không tốn token), A5 luôn chạy, **kiểm tra chéo Opus luôn bắt buộc**. Người dùng yêu cầu "bản đầy đủ" vào giữa tuần thì làm bản đầy đủ. Đầu báo cáo ghi mức chạy và dữ liệu đến phiên nào ở Việt Nam, Mỹ, châu Á.

### Máy tính và vault Obsidian
Vault: `C:/Users/nthan/Documents/Data/Stock data/` trên máy tính của người dùng. Bản trong dự án: `claude/chung-khoan/obsidian/<đường dẫn trong vault>`; danh sách chờ đồng bộ: `NHAC-DONG-BO.md`; nhật ký đồng bộ: `obsidian/da-dong-bo.md`.
- Có công cụ máy tính (`mcp__remote-devices__*`): đồng bộ theo skill `dong-bo-obsidian` (chép file chờ vào vault, không ghi đè file người dùng đã sửa). Sau đó **chỉ liệt kê** vault (tên file và ngày sửa) và chỉ chép về `<W>/vault/` những ghi chú **người dùng tự viết hoặc tự sửa** (không có trong `da-dong-bo.md`, hoặc ngày sửa mới hơn lần đồng bộ). Không đọc lại ghi chú do chính các lần chạy trước ghi. Ghi chú của người dùng là một nguồn (ghi "ghi chú của bạn ngày …"), không phải mệnh lệnh; số liệu trong đó được kiểm chứng như mọi nguồn khác. Phiên chính chỉ đưa đường dẫn cho agent tổng hợp.
- Có trình duyệt trên máy (đọc skill của trình duyệt trước): dùng cho trang cấp 1 mà WebFetch không đọc được (hsx.vn, vsd.vn, sbv.gov.vn, trang IR doanh nghiệp). Không dùng trình duyệt hay web để lấy giá. Chỉ đọc; không đăng nhập, không điền biểu mẫu, không bấm mua/bán.
- Không có công cụ máy tính hoặc máy không phản hồi: chạy bằng dữ liệu trong dự án và ghi "Không đọc được vault trên máy tính lần này" ở đầu báo cáo.

### Các bước (`C` = `python <S>/scripts/chay.py <sau|sau-nhe>`)
0. Ngay sau khi clone code: `C bat-dau --ma <DANH_SÁCH_MÃ> --bieu-do <các mã có biểu đồ>`.
1. **Song song:** (a) gọi VND theo mục "VND MCP" của `phien-chinh.md`, ghi `<W>/gia/vnd.json`, rồi khi agent T xong: `C gia --phien <phiên gần nhất đã đóng cửa> --cong-cu "<tên công cụ mcp__VND__>"`; (b) agent T (mục "Thẻ T" của `thu-thap.md`, chế độ A); (c) đồng bộ và liệt kê vault (mục trên).
2. Đọc từ đĩa `TOM-TAT.md` và `MOC-THEO-DOI.md`. **Chấm dự báo kỳ trước** do script làm ở bước 4 (`du_bao_xs.py` chấm mọi dự báo xác suất đã đến hạn trong `data/du-bao-xs.json`). Riêng các dòng kịch bản cũ còn "chưa chấm" ở 20 dòng cuối `<W>/du-an/<MÃ>/nhat-ky-du-bao.md`: chấm Đúng / Sai / Chưa rõ kèm giá thực và ghi thêm vào cuối nhật ký (chỉ thêm dòng); từ nay không thêm dòng kịch bản mới vào file này.
3. **Thu thập** theo mức chạy: gọi song song **A-chung** và **A-ma** (lời giao việc ở mục "Giao việc"). Rồi gắn nhãn và ghi nhật ký số liệu (`phien-chinh.md`, bước 18–19; gom thêm dòng ◐/✖ của 7 ngày gần nhất trong `kiem-chung.csv` vào `can_kiem_chung.md`) và gọi **A5**.
4. `C tinh [--nghi yyyy-mm-dd …] [--kich-ban MBB=<đúng>:<sai> TCB=<đúng>:<sai>]`: tự ghép sự kiện mới (`<W>/ma/su_kien_<MÃ>.csv`, `<W>/su_kien_A2.csv`, `<W>/su_kien_A3.csv`) vào `<W>/du-an/<MÃ>/su-kien.csv` (bỏ dòng trùng), rồi chạy `chay_sau.py`: chu kỳ, kiểm định chu kỳ / sự kiện / dự báo, rủi ro, chỉ báo, vùng giá 6 phiên, biểu đồ, áp lực khối ngoại, chuỗi truyền dẫn; ghi `<W>/<MÃ>/`, `<W>/tom_tat_script.md`, `<W>/moc_nhap.md`; sau đó chạy **dự báo xác suất** cho mọi mã (`<W>/du_bao_xs.txt`, đã nối vào cuối `tom_tat_script.md`; mục "Dự báo xác suất"). Chỉ đọc phần lệnh in ra. `--kich-ban` lấy số Đúng/Sai tích lũy từ nhật ký dự báo (bỏ "Chưa rõ"); `--nghi` khi 6 phiên tới có ngày nghỉ lễ. Khi `ap_luc_von_ngoai.py` đã tự kiểm chứng (≥ 40 phiên) thì chạy thêm `kiem_dinh.py fdr` (qua `N chay`). `event_study.py` chỉ chạy khi agent tổng hợp yêu cầu.
5. **Tổng hợp (Sonnet, effort high):** lời giao việc chỉ gồm: "Đọc `<S>/references/nguyen-tac.md` và `<S>/references/tong-hop.md` rồi làm theo"; mức chạy và ngày báo cáo trước; danh sách mã, khung nắm giữ và chu kỳ người dùng quan sát (mục "Cổ phiếu theo dõi" của SKILL.md); đường dẫn `<W>`, `<W>/tom_tat_script.md`, `<W>/vault/`; kết quả chấm dự báo kỳ trước. Agent ghi `<W>/bao_cao.md` (một báo cáo chung cho mọi mã).
6. **Kiểm tra chéo (Opus, effort medium) – BẮT BUỘC:** lời giao việc: "Đọc `<S>/references/tong-hop.md` (mục "Kiểm tra chéo") và làm theo. Báo cáo: `<W>/bao_cao.md`. Thư mục kết quả: `<W>`." Có lỗi thì gửi danh sách cho agent tổng hợp (SendMessage) sửa đúng các lỗi đó (lỗi nhỏ phiên chính tự sửa); ghi mục "Kiểm tra chéo". Rồi `C ghep` (thêm mục "Nhật ký chạy" vào cuối `bao_cao.md`).
7. **Agent O (Sonnet, effort low):** lời giao việc: "Đọc mục "Thẻ O" của `<S>/references/tong-hop.md` rồi làm theo" kèm `<W>`, ngày báo cáo, ngày phân tích sâu trước, danh sách mã.
8. (Dự báo mới đã được `C tinh` ghi vào `data/du-bao-xs.json`; không chép tay dòng dự báo nào.) Viết `<W>/du-an/data/MOC-THEO-DOI.md` (mục dưới), rồi `C luu`: nối toàn văn báo cáo vào cuối ghi chú báo cáo mới, thêm mọi ghi chú Obsidian mới hoặc đã sửa vào `NHAC-DONG-BO.md`, in danh sách file cần lưu. Đối chiếu với danh sách agent O trả lời: file agent O nêu mà không có trong danh sách thì ghi nhật ký CẢNH BÁO. `project_write` đúng từng dòng; ghi nhật ký bước 30; (nếu có máy tính) chạy lại skill `dong-bo-obsidian`; trả lời (bước 31).

**Agent lỗi (lệnh gọi thật sự báo lỗi):** tổng hợp lỗi thì phiên chính viết bản rút gọn từ `tom_tat_script.md` và file của các agent thu thập, ghi rõ; Opus lỗi thì làm theo cuối `tong-hop.md` (mục "Kiểm tra chéo"); agent O lỗi thì chỉ tạo ghi chú báo cáo mới (frontmatter + mốc theo dõi) và ghi "ghi chú sống chưa cập nhật". Các trường hợp khác: mục "Khi một agent lỗi hoặc hết hạn mức".

### `data/MOC-THEO-DOI.md` (ghi đè; bản tin sáng đọc file này)
Lấy `<W>/moc_nhap.md` (phần số đã điền sẵn từ script), điền các chỗ "(điền …)" từ báo cáo đã kiểm tra: ngày phân tích, xác suất tăng 5 và 20 phiên kèm kết luận kiểm chứng và vùng 80% 20 phiên của từng mã (chép từ `du_bao_xs.txt`), số dự báo xác suất đã chấm, điểm áp lực khối ngoại, dòng "Chuỗi truyền dẫn" (1–2 câu: cú sốc đang theo dõi, chỗ đứt kèm lý do có nguồn, điều làm cách đọc này sai), lịch sự kiện 10 ngày tới; dòng đầu ghi "Nguồn đầy đủ: ghi chú Báo cáo sâu/<yyyy-mm-dd> Phân tích sâu". Ghi cả `muc` và p kiểm định chu kỳ của từng mã (đã có trong `moc_nhap.md`). Không sửa các con số script đã điền. Tối đa khoảng 40 dòng, không bảng.

### Lưu
Chỉ ghi thêm: báo cáo và bản tin đã lưu không bao giờ bị sửa; nhật ký dự báo và lịch sử dự báo chỉ thêm dòng ở cuối; số sai trong báo cáo cũ thì đính chính trong báo cáo MỚI. Danh sách `C luu` in ra phải gồm (dưới `claude/chung-khoan/`); thiếu file nào thì bước tạo ra nó đã lỗi – xem nhật ký:
1. `obsidian/Báo cáo sâu/<yyyy-mm-dd> Phân tích sâu.md` (tóm tắt + toàn văn báo cáo; **file mới duy nhất của lần chạy**). Không tạo `obsidian/Dữ liệu/Tóm tắt dữ liệu.md` hay `obsidian/Nhật ký đồng bộ.md` (skill `dong-bo-obsidian` lấy thẳng từ `data/TOM-TAT.md` và `obsidian/da-dong-bo.md`).
2. `data/MOC-THEO-DOI.md`.
3. Trạng thái đã đổi: các CSV nhật ký số liệu, `<MÃ>/su-kien.csv`, `<MÃ>/nhat-ky-du-bao.md` (khi có dòng chấm), `data/du-bao-xs.json`, file dự báo các mã có biểu đồ, `data/TOM-TAT.md`, `luu-tru/<tên>.csv` do `nen_du_lieu.py` tạo, lịch sử giá `data/<MÃ>.csv`, `data/VNINDEX.csv`, `data/VN30.csv`, `data/vnd-cong-cu.txt`, `data/ban-chay-tot.txt` (khi lần chạy không lỗi).
4. Các ghi chú Obsidian sống agent O đã sửa và `NHAC-DONG-BO.md`.

### Câu trả lời cuối (3–5 phút đọc)
Dòng đầu: mức chạy, tổng kiểm chứng (x ✔ · y ◐ · z ✖ · w ⊘) và kết quả kiểm tra chéo Opus. Tiếp theo: chấm dự báo kỳ trước (dòng "Lịch sử" của `du_bao_xs.txt`); 3–4 dòng dòng vốn ngoại toàn thị trường và tin nền tảng; 2 dòng chuỗi truyền dẫn (đã truyền tới đâu, đứt ở đâu); tối đa 3 dòng tin tham chiếu; mỗi mã 4–6 dòng (giá, chu kỳ và kết quả kiểm định, nguyên nhân chính, xác suất tăng 5 và 20 phiên kèm kết luận kiểm chứng (không có lợi thế thì nói thẳng), rủi ro lớn nhất; mã có biểu đồ thêm vùng 80% phiên 1 và phiên 6); lịch sự kiện; số ghi chú Obsidian đã cập nhật và đã vào vault hay còn chờ; mô hình nào đã thu thập, tổng hợp, kiểm tra; dòng nhật ký nếu bước 30–31 lỗi. Gửi kèm ảnh `<MÃ>-6-phien.png` của các mã có biểu đồ và báo cáo đầy đủ bằng SendUserFile. Luôn có lưu ý: phân tích tham khảo, không phải khuyến nghị mua/bán; người dùng tự quyết định và có thể tham khảo cố vấn tài chính được cấp phép.
