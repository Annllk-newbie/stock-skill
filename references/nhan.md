# Nhãn và quy tắc chính xác

Ai đọc: phiên chính, mọi agent thu thập (kể cả agent theo mã, A5) và agent tổng hợp. Cột và cách ghi các file nhật ký số liệu ở `phien-chinh.md`. Người dùng đã thấy bản tin dùng số chưa kiểm chứng như số thật, và có tin bị bỏ qua không nói lý do: file này chặn hai lỗi đó.

## Cấp nguồn
- **Cấp 1 – chính thống:** hsx.vn, hnx.vn, vsd.vn, sbv.gov.vn, nso.gov.vn, mof.gov.vn, baochinhphu.vn, chinhphu.vn, trang quan hệ nhà đầu tư của chính doanh nghiệp (mbbank.com.vn, techcombank.com, vietinbank.vn, hoaphat.com.vn), BCTC gốc; quốc tế: federalreserve.gov, bls.gov, bea.gov, treasury.gov, ngân hàng trung ương khác, MSCI, FTSE Russell.
- **Cấp 2 – hãng tin và dữ liệu quốc tế:** Reuters, Bloomberg, AP, AFP, Financial Times, Wall Street Journal, Nikkei Asia, CNBC, MarketWatch, Yonhap, SCMP; dữ liệu: Yahoo Finance (chỉ số liệu Mỹ, không dùng cho cổ phiếu Việt Nam), Investing.com, Trading Economics, MarketScreener (để đối chiếu, không dùng một mình).
- **Cấp 3 – báo trong nước và trang tổng hợp:** Vietstock, CafeF, Tin nhanh chứng khoán, VnEconomy, Người Quan Sát, Thời báo Tài chính, Thời báo Ngân hàng, index.vn, Simplize, cophieu68; báo tiếng Anh của Việt Nam (The Investor, Vietnam News, Bizhub, VnExpress International, Vietnam Plus).
- **VND MCP** (dữ liệu sàn qua công ty chứng khoán): giá, chỉ số, khối ngoại (toàn sàn và theo mã) và sự kiện quyền là ✔ khi qua kiểm tra nội tại của `gia_vnd.py` (thấp ≤ mở/đóng ≤ cao, đóng cửa trong biên độ sàn–trần, thay đổi chỉ số bằng đóng cửa trừ phiên trước); không qua thì ✖ kèm lý do. Định giá (P/E, P/B, ROE) và hàng hóa từ VND mang ◐ trừ khi khớp một nguồn khác.

## Nhãn cho từng số quan trọng
Số quan trọng: giá đóng cửa các mã, VN-Index/VN30, thanh khoản, khối ngoại toàn sàn, mọi số F1–F7, KQKD, ngày GDKHQ/chốt quyền, số Mỹ/châu Á.
- ✔ **đã kiểm chứng:** một nguồn cấp 1, hoặc hai nguồn độc lập (không cùng chép một bài, không cùng nhà cung cấp dữ liệu) cho cùng con số của cùng ngày, khớp theo "Quy tắc chính xác".
- ◐ **một nguồn:** chỉ một nguồn cấp 2/3. Không dùng làm mốc chấm kịch bản hay dòng giá chính thức.
- ✖ **mâu thuẫn:** các nguồn ghi khác nhau. Ghi cả hai số và nguồn, không chọn một số để tính.
- ⊘ **không lấy được:** nêu lý do (trang bị chặn, chưa có bài, sai năm). Không bỏ dòng.

Thân bản tin và phần kết luận của báo cáo chỉ dùng số ✔; số ◐ chỉ nhắc kèm "chưa xác nhận"; số ✖ chỉ ghi "các nguồn mâu thuẫn"; con số cụ thể của ◐/✖ kèm nguồn nằm ở phụ lục hoặc mục "Chưa kiểm chứng".

## Quy tắc chính xác
- **Đúng ngày:** nguồn phải ghi rõ ngày của phiên. "Hôm nay", "mới nhất" hay trang không có ngày đều không được chấp nhận. Trang tổng hợp hay trả bản lưu cũ, nên phải thấy đúng dòng của phiên cần lấy. So theo ngày của PHIÊN, không theo ngày đăng bài.
- **Đúng mã và đúng sàn:** tiêu đề trang phải có tên mã và sàn (HOSE).
- **Số Việt Nam khớp tuyệt đối mới là ✔:** giá cổ phiếu khớp đúng bước giá; VN-Index và VN30 lệch không quá 0,01 điểm; khối ngoại và thanh khoản lệch không quá 1 tỷ đồng hoặc 1%, lấy mức lớn hơn; tỷ giá khớp đúng số. Lệch hơn là ✖.
- **Số quốc tế (V2, F1):** khớp (✔) khi hai nguồn cùng chiều và % thay đổi lệch không quá 0,1 điểm phần trăm; lợi suất lệch không quá 2 điểm cơ bản; dầu và DXY lệch không quá 0,5%. Mức điểm ghi theo nguồn cấp cao hơn. Ngược chiều hoặc lệch hơn là ✖. Hai bài cùng chép một hãng tin chỉ là một nguồn.
- **Khác định nghĩa KHÔNG phải mâu thuẫn:** trước khi gắn ✖, kiểm tra hai số có cùng định nghĩa không; khác thì ghi thành hai dòng riêng, mỗi dòng mang nhãn của chính nó. Các cặp hay nhầm:
  - Thanh khoản: *tổng giá trị giao dịch HOSE gồm thỏa thuận* (chỉ tiêu mặc định, cùng định nghĩa với `accumulatedVal` của VND trong `chi_so`) khác *giá trị khớp lệnh*; HOSE khác *ba sàn*.
  - Khối ngoại và tự doanh: *ròng trên HOSE* (mặc định, ghi vào `von-ngoai.csv`) khác *ròng ba sàn/toàn thị trường*; bài không nêu phạm vi thì ghi "phạm vi không nêu" và chỉ dùng để xác nhận khi khớp một số đã rõ phạm vi.
  - Số trong phiên khác số cuối ngày (giá USD ngân hàng, tỷ giá tự do, chỉ số giữa phiên): ghi giờ của số, dùng số muộn nhất trong ngày.
- **Kiểm tra nội tại:** thấp ≤ mở, đóng ≤ cao; đóng cửa trong biên độ ±7% so với tham chiếu; điểm thay đổi của VN-Index bằng điểm hôm nay trừ điểm phiên trước, và khớp % thay đổi. Sai là ✖ dù hai nguồn khớp nhau.
- **Đơn vị:** trang nước ngoài ghi giá theo đồng (19.250), file giá ghi nghìn đồng (19,25); khối ngoại có thể ghi bằng USD. Đổi đơn vị trước khi so; không tự quy đổi USD sang đồng để tạo nguồn thứ hai.
- **Khối lượng** khác nhau giữa các nguồn do cách tính, không dùng để đối chiếu và không vì thế mà gắn ✖ cho giá. Khối lượng lịch sử trước 22/11/2026 là của Vietcap, từ đó là khớp lệnh của VND (`nmVolume`): không dùng để đối chiếu.
- **Giá đã điều chỉnh:** sau chia cổ tức bằng cổ phiếu, chỉ so giá của phiên mới; giá phiên trước lệch đúng bằng tỷ lệ chia thì ghi chú "nguồn chưa/đã điều chỉnh", không gắn ✖.
- **Không suy ra số:** không tính giá đóng cửa từ % thay đổi, không tính số này từ số khác rồi coi là đã lấy được.

**Không bỏ qua im lặng:** tin agent tìm thấy mà không dùng (trùng, ngoài danh mục, sai năm, nguồn đáng ngờ) được liệt kê một dòng ở "Đã thu thập nhưng không dùng" kèm lý do.
