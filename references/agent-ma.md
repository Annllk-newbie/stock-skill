# Agent theo mã (M-<MÃ>) – phần chung

Ở phân tích sâu, mỗi mã theo dõi có MỘT agent riêng (Haiku, effort medium); ở bản tin sáng một agent `M` làm cho mọi mã (mục cuối) lo mọi thứ của mã đó: số liệu VND MCP theo mã, tin doanh nghiệp, hệ sinh thái (công ty con, cổ đông lớn, đối tác chiến lược, khách hàng lớn) và phần ngành gắn trực tiếp với mã. Đọc file này, `thu-thap.md`, `nhan.md` và phần riêng của mã `the/M-<MÃ>.md`. Phiên chính đưa: chế độ (B / A-đầy đủ / A-cập nhật) · phiên cần lấy và ngày lần chạy trước · giá đóng cửa và nhãn VND của mã (chế độ B: của mọi mã) · "VND hoạt động (health ok)" · `<W>` · đường dẫn `TOM-TAT.md`.

Agent theo mã làm: T1 (tin doanh nghiệp; nguồn: trang ưu tiên → hsx.vn, vsd.vn), sự kiện quá khứ **riêng của mã**, F3 (lãi suất của ngân hàng đó; nguồn: trang ngân hàng → CafeF, VnEconomy), và phần của mã trong T2, F4, F5. B2, A2, A3, A4 không làm các phần này.

**1. Số liệu VND MCP (làm trước; nạp công cụ bằng ToolSearch với đúng từ khóa `mcp__VND__`).** Gọi `mcp__VND__health`; chỉ khi health hoặc lệnh gọi lại một lần vẫn báo lỗi mới ghi "VND MCP lỗi: <nguyên văn>" và bỏ qua bước này. Không ghi "không phản hồi" khi chưa gọi.
- Giá: phiên chính đã lấy, KHÔNG gọi lại.
- `get_foreign_trading` (code = mã, 5 phiên tới phiên cần lấy, size 10): mỗi phiên `netVal`/1e9 = tỷ đồng ròng, `netVol`; phiên cuối thêm `currentRoom`.
- `get_latest_ratios` (filter `ratioCode:PRICE_TO_EARNINGS,PRICE_TO_BOOK,ROAE_TR_AVG5Q,MARKETCAP`, where `code:<MÃ>`, order `reportDate`, fields `code,ratioCode,reportDate,value`). Ghi kèm `reportDate`.
- `get_company_events` (code = mã): chỉ ghi sự kiện có `disclosureDate` sau lần chạy trước, hoặc `effectiveDate`/`expiredDate` trong 15 ngày tới.
- Chỉ A-đầy đủ: `get_ratios` (q `code:<MÃ>~ratioCode:PRICE_TO_EARNINGS,PRICE_TO_BOOK~reportDate:gte:<1 năm trước>`, sort `reportDate:asc`, size 300) → P/E, P/B nhỏ nhất / trung vị / lớn nhất 1 năm; `get_company_personnel` (size 30) → chỉ dòng có `updatedDate` hoặc `effectiveDate` trong 30 ngày qua (bỏ dòng trùng tên cũ).
- Mã của hệ sinh thái có niêm yết (phần riêng của mã): `get_stock_price_by_date` gộp một lần gọi, ghi % thay đổi; chỉ đưa vào "Hệ sinh thái" khi |%| ≥ 3 hoặc có tin.
- Hàng hóa riêng của mã (nếu phần riêng có ghi): `get_change_prices`; `price = 0` kèm `changePct = -100` là chưa cập nhật → ⊘, ghi `lastUpdated`.

**2. Tin trên web** (theo cách lấy trang ở `thu-thap.md`). Trang: trang IR của mã (bảng ở `trang-web.md` nếu cần), cafef.vn (trang sự kiện theo mã), 24hmoney.vn/stock/<MÃ>, vneconomy.vn, tinnhanhchungkhoan.vn; nguồn khác hay nguồn dự phòng thì đọc `trang-web.md`. Chỉ tin đăng sau lần chạy trước. Tối đa: chế độ B 6 tin, A-cập nhật 8 tin, A-đầy đủ 12 tin. Thứ tự ưu tiên: (a) tin của chính doanh nghiệp; (b) tin của hệ sinh thái có kênh ảnh hưởng rõ tới mã; (c) phần ngành riêng của mã. Mỗi tin: ngày · tin (1 câu) · nhóm (a/b/c) · kênh ảnh hưởng (với b, c) · nhãn · nguồn 1 · nguồn 2.

**3. Sự kiện quá khứ (chỉ A-đầy đủ):** đọc mục "Tìm rộng sự kiện quá khứ" của `the/A2.md` và làm cho mã của mình. VND `get_company_events` là nguồn chính cho cổ tức, GDKHQ, niêm yết bổ sung; cafef để đối chiếu.

**Ghi vào `<W>/ma/`:**
- `<MÃ>.md` đúng các mục, đúng thứ tự, mục không có gì ghi "không có tin mới" hoặc "không lấy được – lý do": `## Số VND` · `## Khối ngoại 5 phiên` · `## Định giá` · `## Sự kiện công bố` · `## Tin doanh nghiệp` · `## Hệ sinh thái` · `## Ngành riêng của mã` · `## Ban lãnh đạo` (chỉ A-đầy đủ) · `## Đã thu thập nhưng không dùng`.
- `su_kien_<MÃ>.csv` (cột `date,event,group,source_url,reliability,note`; `group` theo loại nguyên nhân ở mục "Tìm rộng sự kiện quá khứ" của `the/A2.md`: `kqkd`, `co_tuc`, `gdkhq`, `phat_hanh`, `co_dong_lon`, `doi_tac`, `cong_ty_con`, `nganh`, `tin_don`…). Mọi tin và sự kiện có ngày đều vào file này, kể cả tin không kèm biến động giá.
- `danh_muc_M-<MÃ>.md`, `nguon_M-<MÃ>.md` (ở `<W>/`, như các agent thu thập khác).

**Hệ sinh thái là danh sách khởi đầu**, có thể đã cũ. Thấy tin cho biết quan hệ đã đổi (thoái vốn, đổi đối tác, cổ đông mới vượt 5%) thì ghi vào "Hệ sinh thái" với nhãn và nguồn, kèm dòng "Đề nghị cập nhật danh sách hệ sinh thái: …". Không tự sửa file hướng dẫn.

**Chế độ B (bản tin sáng): MỘT agent `M` làm cho mọi mã.** Đọc file này, `thu-thap.md`, `nhan.md` một lần, rồi thẻ `the/M-<MÃ>.md` của từng mã. Gọi `mcp__VND__health` một lần; các lệnh VND gộp nhiều mã được thì gộp (`get_stock_price_by_date` của hệ sinh thái mọi mã một lần gọi). Làm lần lượt từng mã theo đúng thứ tự danh sách, mỗi mã tối đa 6 tin; ghi `<W>/ma/<MÃ>.md` và `<W>/ma/su_kien_<MÃ>.csv` cho từng mã như trên, còn `danh_muc_M.md`, `nguon_M.md` là một file chung (mỗi dòng bắt đầu bằng mã). Một mã gặp lỗi thì ghi lỗi trong `<MÃ>.md` của mã đó và làm tiếp mã sau. Trả lời cuối: mỗi mã một dòng (số tin, mục thiếu). Phân tích sâu vẫn một agent cho mỗi mã (`M-<MÃ>`).

**Thêm mã mới vào danh sách theo dõi:** tạo `the/M-<MÃ>.md` theo mẫu các mã có sẵn; mã chưa có file riêng thì agent chỉ làm phần chung.
