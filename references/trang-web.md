# Trang web: ưu tiên, không dùng, dự phòng

Ai đọc: agent thu thập B1, B2, A2, A3, A4, A5 (agent theo mã chỉ đọc khi trang trong `agent-ma.md` không đủ). Cách lấy trang (WebSearch trước rồi WebFetch link kết quả) ở `thu-thap.md`.

## Trang web ưu tiên
Khảo sát 14/11/2026, chỉ giữ trang tin cậy trung bình đến cao và đọc được. Vẫn tìm thêm ở nguồn khác khi cần. Mỗi số ghi "nguồn + ngày"; số quan trọng phải khớp hai nguồn mới được ✔.

| Trang (tên miền) | Loại nội dung | Tin cậy | Áp dụng cho |
|---|---|---|---|
| hoaphat.com.vn (IR) | BCTC, công bố chính thức | Cao (gốc) | HPG |
| techcombank.com (nhà đầu tư) | BCTC, thông cáo | Cao (gốc) | TCB |
| investor.vietinbank.vn | BCTC, công bố | Cao (gốc) | CTG |
| thongtinthitruong.mbbank.com.vn | Công bố, tin MB | Cao (gốc) | MBB |
| nso.gov.vn (link `?p=` hoặc PDF) | CPI, GDP, sản xuất | Cao (gốc) | Vĩ mô |
| sbv.gov.vn (PDF báo cáo tuần) | Lãi suất liên ngân hàng, tỷ giá trung tâm | Cao (gốc), hay chậm | Vĩ mô, ngân hàng |
| federalreserve.gov | Quyết định, biên bản FOMC | Cao (gốc) | Fed |
| fred.stlouisfed.org (/series, /data/<MÃ CHUỖI>, dùng `offset` để tới số mới) | Lợi suất Mỹ, breakeven, chuỗi lịch sử | Cao | Mỹ |
| 24hmoney.vn (/stock/<MÃ>) | Tin, sự kiện theo mã | Trung bình-cao | Tin doanh nghiệp (không lấy giá hay khối ngoại) |
| stockbiz.vn (/stocks/<MÃ>/trading, nguồn FireAnt) | Tự doanh (tỷ đồng) | Trung bình-cao; tự doanh phiên mới nhất coi là chưa chắc | Chỉ tự doanh |
| cafef.vn (trang sự kiện theo mã, bài tin) | Sự kiện doanh nghiệp, tin | Trung bình-cao (báo lại) | Tin T1, sự kiện quá khứ |
| vneconomy.vn, tinnhanhchungkhoan.vn, baochinhphu.vn, thanhnien.vn, vnbusiness.vn, mekongasean.vn | Tin toàn văn, KQKD | Trung bình-cao (báo lại) | Tin doanh nghiệp, ngành |
| thoibaotaichinhvietnam.vn | Tỷ giá, đấu thầu trái phiếu, ngân sách | Trung bình-cao (báo Bộ Tài chính) | Tỷ giá, trái phiếu |
| vietnamplus.vn, vov.vn, baodauthau.vn | CPI, FDI, đầu tư công | Trung bình-cao (báo lại số chính thức) | Vĩ mô |
| uk.investing.com | S&P 500 có ngày | Trung bình-cao | Mỹ |
| kitco.com | Giá vàng (đối chiếu số VND) | Trung bình-cao | Hàng hóa |
| tradingeconomics.com (/news/..., /commodity/iron-ore) | DXY, quặng sắt | Trung bình | Mỹ, HPG đầu vào |
| etfcentral.com (/fund/VNM) | AUM, dòng vốn ETF VNM có ngày | Trung bình | ETF |

**Không dùng làm số chốt:** hnx.vn, vsd.vn (chặn robot); ssc.gov.vn, congbothongtin.ssc.gov.vn, treasury.gov TextView, CME FedWatch (khung JS, không có số); nhadautu.vn, ndh.vn, ssi.com.vn, vietnamnews.vn (lỗi fetch); finance.vietstock.vn (che số ở tài khoản Free); simplize.vn (chỉ phiên chính dùng để đối chiếu khi `gia_vnd.py` báo điều chỉnh giá); CafeF DuLieu, BSC, TradingView, 24hmoney trang khối ngoại toàn sàn (trống hoặc sai); etfdb, stockanalysis.com (cũ); báo cáo CTCK có dự phóng cũ (không phải kết quả thật); Yahoo Finance cho cổ phiếu Việt Nam; trang không ghi đơn vị phát hành, ngày đăng hay nguồn số liệu; trang tổng hợp bằng AI; diễn đàn.

**Chưa có nguồn đọc được ổn định (ghi "chưa có số liệu", không điền bằng nguồn cũ):** tự doanh theo mã ổn định, lãi suất điều hành, lợi suất trái phiếu VN thứ cấp mới, xác suất FedWatch, VIX (chỉ có khi bài AP/CNBC/Reuters nêu), chỉ số châu Á.

**Nguồn dự phòng nước ngoài** (thứ tự thử: trang Việt Nam trong bảng → trang Việt Nam khác → dưới đây; trang nào hai lần liền không đọc được thì ghi chú để người dùng cập nhật):
- **Tỷ giá trung tâm, liên ngân hàng, tự do:** bản tin "SNAPSHOT-Vietnam dong" của Reuters (tìm "SNAPSHOT Vietnam dong <ngày>"). Giá USD Vietcombank chỉ lấy từ vietcombank.com.vn hoặc báo Việt Nam; không được thì ⊘.
- **Lãi suất liên ngân hàng, điều hành:** Trading Economics, Reuters (cấp 2).
- **Tin doanh nghiệp:** trang IR tiếng Anh của doanh nghiệp (cấp 1), Reuters, Bloomberg, Nikkei Asia; tin MarketScreener phải mở được bài gốc.
- **Tin vĩ mô Việt Nam bằng tiếng Anh:** theinvestor.vn, e.vnexpress.net, en.vietnamplus.vn (cấp 3).
