# Phiên chính: điều phối (cả hai chế độ)

Ai đọc: phiên chính, ngay sau SKILL.md, cùng `nguyen-tac.md`, `nhan.md` và file của chế độ (`ban-tin-sang.md` hoặc `phan-tich-sau.md`). Không đọc file nào khác trong `references/`: thẻ việc của agent là để agent tự đọc.

`<S>` = `research/skill` (bản clone kho GitHub) · `<W>` = `research/` · "dự án" = `claude/chung-khoan/` trong Project "Economy and trading".

## Lệnh điều phối `chay.py`
Mọi việc script làm bằng `C` = `python <S>/scripts/chay.py <ban-tin|sau|sau-nhe> <lệnh>`, đúng thứ tự `bat-dau` → `gia` → `tinh` → `ghep` → `luu` (thứ tự đầy đủ kèm các việc không phải script: `C ke-hoach`). Mỗi lệnh tự ghi nhật ký chạy và chỉ in kết quả ngắn: đọc phần in ra, không mở file kết quả. Không gõ tay lệnh của từng script; script nào cần chạy riêng (ví dụ `kiem_dinh.py fdr`, `event_study.py`) thì chạy qua `N chay` (mục "Nhật ký chạy").

## Tiết kiệm token (bắt buộc)
- **Không tự gọi `project_read`:** nội dung file sẽ nằm lại trong ngữ cảnh suốt lần chạy. Giao cho agent T (`the/T.md`). Không gọi `project_info`. Không bao giờ chép tay nội dung file ra đĩa.
- **Mọi file lưu vào dự án dùng `project_write` với `local_path`**, đúng danh sách `C luu` in ra. Không dán nội dung CSV/JSON vào câu trả lời, suy nghĩ hay lời giao việc; xử lý bằng Python, chỉ in vài dòng.
- **Lời giao việc cho agent chỉ vài dòng** (mục "Giao việc"): agent nhận đường dẫn, không nhận nội dung, và trả lời ngắn.
- Không đọc bản tin hay báo cáo cũ bản đầy đủ: trạng thái cần cho lần chạy nằm ở `data/TOM-TAT.md` và `data/MOC-THEO-DOI.md`.

## Phân công mô hình (quy tắc của người dùng)
Mọi việc thu thập và tải dữ liệu dùng Haiku; Sonnet chỉ tổng hợp, phân tích, điều phối; kiểm tra cuối cùng là Opus.
- Phiên chính (Sonnet): điều phối, chạy `chay.py`, gọi VND MCP phần chung, gắn nhãn, lưu, gửi. Không tự đọc web.
- Agent T: Haiku, effort low. Thu thập B2, A2, A3, A4, kiểm chứng A5, agent theo mã (M, M-<MÃ>): Haiku, effort medium.
- Chỉ phân tích sâu: tổng hợp (Sonnet, effort high), kiểm tra chéo (Opus, effort medium, **bắt buộc**), agent O (Sonnet, effort low).

**Số agent mỗi lần chạy (cố định, không tự thêm):**
- Bản tin sáng: **3** = T · B2 · M (một agent theo mã làm cho mọi mã); thêm A5 chỉ khi còn số quan trọng chưa ✔ (tối đa 4).
- Phân tích sâu bản đầy đủ: **12** = T · A2, A3, A4 · agent theo mã · A5 · tổng hợp · kiểm tra chéo · O. Sửa lỗi sau kiểm tra chéo gửi lại cho chính agent tổng hợp (SendMessage), không tạo agent mới.
- Phân tích sâu bản cập nhật: **11** (như trên, bỏ A4).
(Phân tích sâu tính với 4 mã; thêm mã thì thêm một agent theo mã. Bản tin sáng luôn một agent M.) Cuối báo cáo ghi một dòng: mô hình nào đã thu thập, tổng hợp, kiểm tra.

## Giao việc (lời giao việc mẫu; không chép quy tắc vào)
Mọi lời giao việc gồm: tên agent · câu "Đọc <các file dưới> trong `<S>/references/` rồi làm đúng việc của bạn" · tham số chung: phiên cần lấy, ngày lần chạy trước, danh sách mã, `<W>`, đường dẫn `<W>/du-an/data/TOM-TAT.md`.
- **T:** `the/T.md`; thêm chế độ (B/A), `<S>`.
- **B2, A2, A3, A4, A5:** `thu-thap.md`, `trang-web.md`, `nhan.md`, `the/<tên>.md` (A2 thêm mục tham chiếu của `the/B2.md`; thẻ tự ghi). B2 thêm Brent và % từ VND, sự kiện F1/F2 trong lịch 24 giờ qua; A2, A3 thêm mức chạy.
- **M (bản tin sáng, mọi mã):** `thu-thap.md`, `nhan.md`, `agent-ma.md` (mục "Chế độ B"), `the/M-<MÃ>.md` của từng mã; thêm danh sách mã, giá đóng cửa và nhãn VND của từng mã, câu "VND hoạt động (health ok)".
- **M-<MÃ> (phân tích sâu):** `thu-thap.md`, `nhan.md`, `agent-ma.md`, `the/M-<MÃ>.md`; thêm chế độ (A-đầy đủ / A-cập nhật), giá đóng cửa và nhãn VND của mã, câu "VND hoạt động (health ok)".
- **Tổng hợp, kiểm tra chéo, O:** xem `phan-tich-sau.md`.

## VND MCP (nguồn giá duy nhất; phiên chính làm trước khi giao việc)
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

## Giá
- Lịch sử giá khoảng 6 năm lấy từ dự án (`data/<MÃ>.csv`, `data/VNINDEX.csv`, `data/VN30.csv`, agent T tải); VND không có lệnh lấy lịch sử dài. `C gia --phien <phiên> --cong-cu "<tên công cụ mcp__VND__ đã nạp, cách nhau dấu phẩy>"` (sau khi agent T xong) chạy `gia_vnd.py` rồi `kiem_tra_du_lieu.py`: nối phiên mới, tự điều chỉnh lịch sử khi có sự kiện quyền, kiểm tra nội tại, gắn nhãn. Lệnh in `tom_tat`, `chi_so`, `vnd`, mã không ✔ hoặc có `dieu_chinh`, kết quả kiểm tra file giá.
- `kiem_tra` có `loi`: không dùng phiên đó cho dự báo, ghi ở mục "Dữ liệu"; `dong_tam` chỉ được tồn tại ở phiên cuối. Có `dieu_chinh`: đối chiếu `get_company_events` của mã để xác nhận sự kiện quyền, ghi ở mục "Dữ liệu".
- Mã ✔: không agent nào tìm giá mã đó nữa. Mã thoát 2 (`"dung": true`): bù phiên thiếu nếu lý do là `⊘ chưa có phiên` (kiểm `get_trading_calendar` xem còn thiếu phiên nào, gọi `get_stock_price_by_date` cho từng phiên, thêm vào `vnd.json`, chạy lại `C gia`); vẫn mã 2 thì "Khi DỪNG".
- **Mã người dùng hỏi mà không có trong danh sách theo dõi:** giá lấy từ file người dùng gửi, hoặc từ VND (`get_stock_price_by_date` theo ngày) khi chỉ cần vài phiên; không có lịch sử thì báo người dùng, KHÔNG lấy giá trên web. `chay.py` và `forecast6.py` dùng biên độ HOSE ±7%: mã HNX/UPCoM cần `--gioi-han 0.10`/`0.15` khi chạy riêng `forecast6.py`.
- `<W>/gia/gia_<MÃ>_ctck.csv` (cột `date,open,high,low,close,volume`, nghìn đồng, đã điều chỉnh) là file giá cho MỌI script; `C luu` chép về `data/` để thành lịch sử giá duy nhất.

## Gắn nhãn, A5 và ghi nhật ký số liệu (bước 18–19)
Sau khi các agent thu thập xong: gắn nhãn theo `nhan.md` (giá và chỉ số VND đã có nhãn); gom số quan trọng chưa ✔ vào `<W>/can_kiem_chung.md` (mỗi dòng: mục, số, nguồn hiện có) rồi gọi A5 theo chế độ (kết quả ở `<W>/kiem_chung.md`, cập nhật nhãn theo đó). Rồi ghi thêm dòng vào các file nhật ký số liệu (cột ở mục dưới) trong `<W>/du-an/` bằng Python, chỉ thêm dòng:
- `data/von-ngoai.csv`: khối ngoại toàn sàn (VND), Brent, vàng (VND), các cột ở mục "Dòng tiền Việt Nam" của `ket_qua_B2.md` (bản tin) và số Mỹ/Fed của `ket_qua_B2.md`/`ket_qua_A3.md` (DXY, lợi suất, breakeven, VIX, xác suất Fed).
- `data/kiem-chung.csv`: mọi số quan trọng kèm nhãn cuối cùng.
- `data/tham-chieu.csv`: dòng của `tham_chieu_B2.csv` hoặc `tham_chieu_A2.csv` (bỏ dòng trùng).
- `su-kien-nen-tang.csv`: tin F1–F7 mới (từ `ket_qua_A3.md`, `ket_qua_A4.md`; bản tin sáng: tin chung của B2 thuộc nhóm F) kèm chuỗi tác động.
- Sự kiện theo mã (chỉ phân tích sâu): không ghi tay, `C tinh` tự ghép.

## Cột và cách ghi các file nhật ký số liệu (chỉ thêm dòng)
- `data/kiem-chung.csv` (cột `ngay_du_lieu,muc,gia_tri,nhan,nguon_1,nguon_2,cap_cao_nhat,ghi_chu,ngay_kiem`). Số được đính chính thì nêu ở mục "Dữ liệu" của bản kế tiếp.
- `data/von-ngoai.csv`: mỗi lần chạy thêm một dòng cho mỗi phiên còn thiếu, đúng cột ghi ở đầu `ap_luc_von_ngoai.py`, cộng ba cột `lam_phat_ky_vong_5y` (breakeven Mỹ 5 năm, FRED chuỗi `T5YIE`), `vix`, `vang` của `chuoi_truyen_dan.py` (`chay.py tinh` tự thêm cột nếu file cũ chưa có). Khối ngoại ròng HOSE lấy từ VND (`get_foreign_trading` code VNINDEX). Chỉ ghi số ✔; số ◐ ghi kèm nhãn trong cột `nguon`; số ✖ để trống. Ô không lấy được để trống, không chép số cũ sang ngày mới. Số theo tuần (ETF, khu vực) ghi ở ngày công bố. Không sửa số đã có trừ khi có nguồn đính chính (ghi lý do vào `nguon`). Mỗi lần chạy lấy bù khoảng 1 tuần số cũ của DXY, lợi suất Mỹ 10 năm, giá USD Vietcombank và khối ngoại HOSE cho đến khi file đủ 8 tuần.
- `su-kien-nen-tang.csv` (cột `date,nhom,su_kien,tac_dong_du_kien,source_url,reliability,note`; `nhom` là F1–F7); `tac_dong_du_kien` là chuỗi nhân quả ngắn ở cấp thị trường.
- `data/tham-chieu.csv` (cột `ngay,doanh_nghiep,tin,kenh_anh_huong,ma_lien_quan,nhan,nguon`).
- `<MÃ>/su-kien.csv` (cột `date,event,group,source_url,reliability,note`; chỉ phân tích sâu ghép thêm; không cắt; không ghi ngày đáo hạn VN30F vào đây, `chay_sau.py` tự sinh).

## Nhật ký chạy (bắt buộc)
Mỗi bước một dòng trong `<W>/nhat-ky-chay.txt`. `N` = `python <S>/scripts/nhat_ky.py`.
- `chay.py` tự ghi mọi bước script bên trong (01, 04, 05, 20–24, 28, 29): không ghi lại.
- Script chạy riêng: `N chay --buoc "<tên bước>" -- python <S>/scripts/<script>.py …` (chuyển hướng `>` đặt sau cùng như bình thường).
- Việc không phải script (VND MCP, agent, `project_write`, SendUserFile, PushNotification): làm xong thì `N ghi --buoc "<tên bước>" --trang-thai <ok|canh-bao|loi|bo-qua|dung> --chi-tiet "<ngắn; khi lỗi chép NGUYÊN VĂN thông báo lỗi>"`. Agent trả lời đủ file → ok; thiếu mục hoặc có số ⊘ → canh-bao (ghi thiếu gì); lỗi hoặc không ghi ra file → loi. Bước cố ý không làm (A5 khi mọi số đã ✔, A4 ở bản cập nhật) → bo-qua kèm lý do.
- **Tên bước cố định** (giữ nguyên chữ và số; bước không có ở chế độ đó thì bỏ): `01 Tải code GitHub` · `02 VND health và công cụ` · `03 VND lịch, giá, chỉ số, khối ngoại sàn` · `04 gia_vnd.py` · `05 kiem_tra_du_lieu.py` · `06 Agent T` · `07 Đồng bộ và liệt kê vault` · `08 Chấm dự báo kỳ trước` · `09 Agent B2` · `10 Agent M` (bản tin sáng) · `11 Agent A2` · `12 Agent A3` · `13 Agent A4` · `14 Agent M-MBB` · `15 Agent M-TCB` · `16 Agent M-CTG` · `17 Agent M-HPG` · `18 Agent A5` · `19 Gắn nhãn và ghi nhật ký CSV` · `20 ap_luc_von_ngoai.py` · `21 chuoi_truyen_dan.py` · `22 forecast6/chart6 MBB` · `23 forecast6/chart6 TCB` · `24 chay_sau.py` · `25 Agent tổng hợp` · `26 Kiểm tra chéo Opus` · `27 Agent O` · `28 Viết bản tin/báo cáo và phụ lục` · `29 nen_du_lieu.py` · `30 Lưu vào dự án` · `31 Gửi người dùng`. Thêm mã vào danh sách theo dõi thì thêm bước `Agent M-<MÃ>` ngay sau mã cuối.
- `C ghep` đưa nguyên văn nhật ký vào cuối phụ lục/báo cáo và in dòng "Nhật ký: …" khi có bước không OK: thêm dòng đó vào mục "Dữ liệu". Bước 30–31 xảy ra sau khi ghép: lỗi thì đưa dòng đó vào câu trả lời cuối.
- Nhật ký ghi "LỖI CODE của skill" → mục "Khi code mới lỗi" của SKILL.md.

## Dữ liệu trong dự án
Mỗi lần chạy theo lịch là một phiên mới, không nhớ gì, nên trạng thái nằm trong dự án. Không có công cụ Projects thì vẫn làm và ghi ở đầu báo cáo là không so được với lần trước.
- **Đọc đầu mỗi lần chạy:** qua agent T (danh sách cố định ở `the/T.md`).
- **Ghi mỗi lần chạy: đúng MỘT file mới** – ghi chú Obsidian của lần chạy (`obsidian/Bản tin/<yyyy-mm-dd> Bản tin.md` hoặc `obsidian/Báo cáo sâu/<yyyy-mm-dd> Phân tích sâu.md`), chứa cả tóm tắt và toàn văn. Mọi thứ khác là ghi đè file trạng thái đã có. `C luu` in đúng danh sách file mới hoặc đã đổi; không tạo file nào ngoài danh sách đó, không tạo file theo ngày, theo quý hay theo mã. Code skill không nằm trong dự án.
- **Số file không tăng theo thời gian:** vault Obsidian là kho lưu trữ. Skill `dong-bo-obsidian` xóa khỏi dự án các ghi chú bản tin/báo cáo cũ hơn 14 ngày đã có trong vault và chuyển các dòng trong `luu-tru/<tên>.csv` vào vault. Các lần chạy không tự xóa file nào. Ảnh biểu đồ không lưu vào dự án.

## Khi DỪNG (VND lỗi, hoặc `C gia` vẫn mã 2)
Giá và chỉ số chỉ lấy từ VND MCP. Trước khi kết luận VND lỗi: đã nạp công cụ bằng ToolSearch `mcp__VND__`, đã gọi `mcp__VND__health`, đã gọi lại đúng lệnh bị lỗi MỘT lần (gặp "throttled" thì chờ 20 giây). Vẫn lỗi thì **DỪNG cả lần chạy**: không lấy giá từ web, không gọi agent thu thập, không chạy script phân tích, không viết bản tin hay báo cáo, không ghi gì vào dự án. Chỉ làm ba việc:
1. `N ghi --buoc "<bước lỗi>" --trang-thai dung --chi-tiet "<nguyên văn lỗi>"` (`C gia` đã tự ghi nếu lỗi ở đó).
2. Gửi thông báo cho người dùng (lần chạy theo lịch: PushNotification): "Dừng: không lấy được giá từ VND MCP", lệnh đã gọi, nguyên văn lỗi, giờ thử, và nguyên kết quả `N tom-tat`.
3. Trả lời đúng nội dung đó.

## Khi một agent lỗi hoặc hết hạn mức
Chỉ khi lệnh gọi thật sự báo lỗi (không phải phán đoán "không cần"). Không chạy lại cả quy trình; luôn lưu những gì đã thu thập.
- Agent T lỗi, không có công cụ Projects, hoặc `da_luu` rỗng: phiên chính tự gọi `project_read` cho các đường dẫn trong `the/T.md` rồi chạy `python <S>/scripts/du_an.py luu --out <W>/du-an` (không chép tay nội dung). File dự án chưa có (lần đầu) thì bỏ qua và ghi ở mục "Dữ liệu".
- Agent thu thập hoặc agent theo mã lỗi: ghi nhật ký `loi`; mục của agent đó trong "Độ đầy đủ dữ liệu" ghi "không lấy được – agent lỗi"; không tự đi tìm thay.
- A5 lỗi: giữ nhãn ◐.
- Tổng hợp, kiểm tra chéo, agent O lỗi: theo `phan-tich-sau.md`.
- Phiên không có công cụ Agent hoặc thiếu một mô hình: phiên chính tự làm và ghi rõ trong báo cáo.
