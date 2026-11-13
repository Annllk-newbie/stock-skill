# Kỹ thuật và nguyên nhân chu kỳ

Chỉ agent tổng hợp (Sonnet) và agent thu thập A2/A3 đọc file này, và chỉ đọc mục đang cần (tìm tiêu đề bằng Grep rồi Read đúng đoạn). Phiên chính không đọc. Hai phần: **Phần A – Nguyên nhân có thể tạo chu kỳ giá** (mục 1–10) và **Phần B – Diễn giải phân tích kỹ thuật** (mục 1–11).

---

# PHẦN A – Danh mục nguyên nhân có thể tạo chu kỳ giá

Đọc file này ở bước tìm lý do cho chu kỳ. Mục tiêu là có một danh sách kiểm tra đủ rộng để không bỏ sót nguyên nhân, rồi dùng phương pháp ở mục cuối để chấm điểm từng giả thuyết bằng dữ liệu.

## Mục lục
1. Nguyên tắc tìm nguyên nhân
2. Lỗi dữ liệu tạo ra chu kỳ giả
3. Cấu trúc thị trường (lịch cố định)
4. Sự kiện doanh nghiệp
5. Dòng tiền và nhà đầu tư
6. Ngành, hàng hóa và mùa vụ
7. Vĩ mô và chính sách
8. Tâm lý, tin đồn và giao dịch bất thường
9. Thị trường khác (Mỹ, quốc tế)
10. Cách liên kết sự kiện với đỉnh/đáy và chấm điểm

## 1. Nguyên tắc tìm nguyên nhân

- **Độ dài chu kỳ là manh mối đầu tiên.** Một chu kỳ ~20–22 phiên gợi ý thứ gì đó lặp lại hằng tháng; ~60–65 phiên gợi ý theo quý; ~250 phiên là theo năm; chu kỳ vài phiên thường đến từ cơ chế thanh toán hoặc giao dịch ngắn hạn. Đi tìm sự kiện có cùng nhịp lặp.
- **Ngày đảo chiều là manh mối thứ hai.** Nếu đáy hay rơi vào tuần thứ 3 của tháng, hoặc đỉnh hay xuất hiện ngay trước ngày công bố kết quả kinh doanh, hãy tìm sự kiện có lịch tương ứng.
- **Thường có nhiều nguyên nhân chồng lên nhau.** Một nhịp tăng có thể do kỳ vọng lợi nhuận quý cộng thêm dòng tiền ETF. Liệt kê tất cả giả thuyết có điểm, không cần chọn một.
- **Trùng thời điểm chưa phải là nguyên nhân.** Sự kiện chỉ được coi là nguyên nhân khi có cơ chế hợp lý (nó thay đổi cung hoặc cầu cổ phiếu như thế nào) VÀ lặp lại đủ nhiều lần.
- **"Không tìm được lý do" là một kết quả hợp lệ.** Nói thẳng ra còn tốt hơn gán một nguyên nhân yếu.

## 2. Lỗi dữ liệu tạo ra chu kỳ giả

Kiểm tra trước tiên, vì nếu chu kỳ là do dữ liệu thì mọi phân tích sau đều vô nghĩa.

- **Giá chưa điều chỉnh** cổ tức tiền mặt, cổ tức bằng cổ phiếu, phát hành quyền mua: tại ngày giao dịch không hưởng quyền (GDKHQ), giá tham chiếu bị điều chỉnh giảm, trông như một cú sập. Nếu công ty trả cổ tức đều đặn, điều này tạo ra "chu kỳ" giả. So sánh ngày đáy với lịch chốt quyền.
- **Thiếu phiên, trùng phiên, sai múi giờ** trong file tải về.
- **Biên độ trần/sàn** làm giá bị "cắt" và kéo dài nhịp sang phiên sau.

## 3. Cấu trúc thị trường (lịch cố định)

Các mục dưới đây là lịch phổ biến ở thị trường Việt Nam; quy định có thể đã thay đổi, nên luôn tra lịch cụ thể của kỳ đang xét trên trang của sở giao dịch hoặc quỹ.

| Sự kiện | Nhịp lặp | Cơ chế tác động | Nơi tra cứu |
|---|---|---|---|
| Đáo hạn hợp đồng tương lai VN30 (thường thứ Năm tuần thứ 3 của tháng) | Hằng tháng | Các vị thế phái sinh lớn có thể kéo cổ phiếu trụ cột trong rổ VN30 quanh ngày đáo hạn | hnx.vn, các công ty chứng khoán |
| Cơ cấu danh mục ETF ngoại (FTSE Vietnam, MarketVector/VNM) | Theo quý (thường tháng 3, 6, 9, 12) | Quỹ phải mua/bán một lượng lớn vào phiên cơ cấu; giá thường chạy trước ngày công bố | Tin của các công ty chứng khoán, cafef, vietstock |
| Cơ cấu rổ VN30, VNDiamond, VNFinLead và các ETF nội | Theo quý hoặc nửa năm | Như trên, tác động mạnh với mã bị thêm/loại | hsx.vn |
| Chu kỳ thanh toán (cổ phiếu về tài khoản sau T+2) | Vài phiên | Áp lực chốt lời khi hàng về sau một nhịp tăng nóng | Quy định hiện hành của sở/VSD |
| Kỳ xem xét nâng hạng thị trường (FTSE Russell, MSCI) | Nửa năm/năm | Kỳ vọng dòng vốn ngoại lên toàn thị trường | Thông báo của FTSE Russell, MSCI |
| Mã vào/ra danh sách không được giao dịch ký quỹ | Theo quý (theo BCTC) | Mất margin khiến bên mua giảm, có thể gây bán giải chấp | hsx.vn, hnx.vn |

## 4. Sự kiện doanh nghiệp

| Sự kiện | Nhịp lặp | Cơ chế | Nơi tra cứu |
|---|---|---|---|
| Công bố BCTC quý / kết quả kinh doanh | Theo quý (vài tuần sau khi hết quý) | Giá tăng theo kỳ vọng trước ngày công bố, chốt lời khi tin ra ("mua tin đồn, bán sự thật") | Trang quan hệ cổ đông của công ty, hsx/hnx |
| Ước tính kết quả kinh doanh, số liệu tháng (bán lẻ, sản lượng điện, thép...) | Hằng tháng | Thông tin sớm làm thay đổi kỳ vọng | Công ty, báo ngành |
| Đại hội cổ đông (thường tháng 3–5), kế hoạch lợi nhuận | Hằng năm | Kế hoạch cao/thấp hơn kỳ vọng | Tài liệu ĐHCĐ |
| Chốt quyền cổ tức, phát hành thêm | Theo năm/nửa năm | Mua để hưởng quyền trước GDKHQ, bán sau đó; xem thêm mục 2 | vsd.vn, thông báo công ty |
| Cổ phiếu ESOP/phát hành riêng lẻ hết hạn chế chuyển nhượng | Không đều | Nguồn cung mới đổ ra thị trường | Thông báo phát hành |
| Giao dịch nội bộ, cổ đông lớn, mua cổ phiếu quỹ | Không đều | Báo hiệu quan điểm của người nắm thông tin; tạo cung/cầu trực tiếp | Công bố thông tin giao dịch |

## 5. Dòng tiền và nhà đầu tư

- **Khối ngoại mua/bán ròng** theo mã và toàn thị trường; thường có chu kỳ theo tỷ giá và dòng vốn toàn cầu.
- **Tự doanh công ty chứng khoán** (thường có số liệu hằng ngày).
- **Dư nợ ký quỹ** toàn thị trường (theo quý): dư nợ cao làm giá dễ sập theo chuỗi khi giảm mạnh.
- **Room ngoại** đầy/trống: mã hết room có thể giao dịch theo nhịp khác.
- **Thanh khoản**: mã thanh khoản thấp dễ bị một vài lệnh lớn tạo ra dao động có nhịp.

## 6. Ngành, hàng hóa và mùa vụ

Ghép cổ phiếu với biến số ngành dẫn dắt lợi nhuận, rồi so chu kỳ của biến đó với chu kỳ giá:

- Thép ↔ giá quặng sắt, thép cuộn; Dầu khí ↔ giá dầu Brent; Phân bón/hóa chất ↔ giá urê; Cao su ↔ giá cao su; Thủy sản, dệt may ↔ đơn hàng xuất khẩu, tỷ giá, mùa đặt hàng.
- Điện: thủy điện mạnh mùa mưa, nhiệt điện mạnh mùa khô; Bán lẻ, tiêu dùng: cao điểm trước Tết; Hàng không, du lịch: cao điểm hè và lễ.
- Ngân hàng ↔ hạn mức tín dụng, lãi suất liên ngân hàng; Bất động sản ↔ chính sách tín dụng, pháp lý dự án, lãi suất.
- Hiệu ứng cuối quý/cuối năm (quỹ "làm đẹp" danh mục), tháng trước Tết.

## 7. Vĩ mô và chính sách

- Lãi suất điều hành và động thái thanh khoản của Ngân hàng Nhà nước (sbv.gov.vn); lãi suất liên ngân hàng.
- Tỷ giá USD/VND; chỉ số DXY.
- Họp chính sách của Fed (FOMC, 8 lần/năm) và số liệu lạm phát Mỹ.
- Số liệu thống kê trong nước: CPI, PMI (đầu tháng), GDP quý (gso.gov.vn).
- Thay đổi chính sách thuế, quy định ngành, đầu tư công.
- Diễn biến chỉ số chung (VN-Index) và các thị trường lớn trong khu vực: nếu cổ phiếu chỉ đang đi theo nhịp của cả thị trường thì nguyên nhân nằm ở cấp thị trường, không phải doanh nghiệp. Hãy luôn so chu kỳ cổ phiếu với chu kỳ VN-Index.

## 8. Tâm lý, tin đồn và giao dịch bất thường

- Diễn đàn, nhóm mạng xã hội, báo cáo khuyến nghị của công ty chứng khoán (khuyến nghị mới thường gây phản ứng ngắn hạn).
- **Tết âm lịch:** ngày lệch tới gần một tháng giữa các năm (cuối tháng 1 đến giữa tháng 2), nên hiệu ứng trước/sau Tết (rút tiền tiêu Tết, nghỉ dài ngày, dòng tiền quay lại sau Tết) trông như chu kỳ năm "không đều" nếu so theo lịch dương.
- **Chu kỳ không đi kèm tin tức**, khối lượng đột biến mà không có thông tin, thanh khoản thấp, tỷ lệ cổ phiếu tự do chuyển nhượng nhỏ, có thể là dấu hiệu của dòng tiền đầu cơ có tổ chức. Chỉ nêu điều này như một khả năng kèm các dấu hiệu quan sát được; không kết luận hay buộc tội ai. Với người mua, đây là một rủi ro lớn vì chu kỳ kiểu này có thể dừng đột ngột.

## 9. Thị trường khác (Mỹ, quốc tế)

Nếu cổ phiếu niêm yết ở nước ngoài: đáo hạn quyền chọn (thứ Sáu tuần thứ 3 của tháng, kỳ lớn vào tháng cuối quý), mùa báo cáo lợi nhuận, cơ cấu chỉ số (S&P, Russell vào tháng 6), FOMC, số liệu việc làm (thứ Sáu đầu tháng), CPI, giai đoạn mua lại cổ phiếu bị hạn chế quanh ngày công bố lợi nhuận.

## 10. Cách liên kết sự kiện với đỉnh/đáy và chấm điểm

1. **Lập dòng thời gian sự kiện** trong cùng khoảng thời gian với dữ liệu giá: ngày, sự kiện, nhóm (mục 3–8), nguồn. Chỉ ghi sự kiện tìm được bằng chứng.
2. **Đối chiếu** với danh sách `dinh_day` từ `cycles.py`. Một sự kiện được coi là "trùng" nếu cách đỉnh/đáy không quá ±3 phiên (hoặc giá trị `--window` đã dùng). Lưu ý chiều thời gian: sự kiện xảy ra **trước** đảo chiều mới có thể là nguyên nhân; sự kiện đã biết trước lịch (ví dụ ngày công bố KQKD) có thể tác động từ trước đó vài phiên do kỳ vọng.
3. **Đếm cả hai chiều cho từng loại sự kiện:**
   - Bao nhiêu lần sự kiện xảy ra thì có đảo chiều đi kèm (độ trúng)?
   - Bao nhiêu đỉnh/đáy có sự kiện đó đi kèm (độ bao phủ)?
   Ví dụ: "Đáo hạn phái sinh xảy ra 12 lần, 8 lần trùng với đáy (67%); nó giải thích 8/14 đáy (57%)."
   Với sự kiện có ngày thay đổi mỗi năm (Tết âm lịch, ngày công bố KQKD, ngày GDKHQ, ngày cơ cấu ETF), chạy thêm `scripts/event_study.py` với danh sách ngày thật của từng lần. Kết quả "nhất quán" (cùng chiều ≥ 75% số lần, từ 4 sự kiện trở lên) là bằng chứng mạnh. `phien_day_thuong_gap` và `phien_dinh_thuong_gap` cho biết giá thường tạo đáy/đỉnh trước hay sau sự kiện bao nhiêu phiên.
4. **So với ngẫu nhiên:** nếu cửa sổ ±3 phiên quanh sự kiện chiếm khoảng 30% số phiên trong tháng, thì trùng 30% là chuyện tình cờ. Chỉ khi tỷ lệ trùng vượt rõ mức này mới đáng kể.
5. **Chấm mức độ liên kết:**
   - **Mạnh:** có cơ chế rõ, lặp lại ≥ 4 lần, độ trúng cao hơn hẳn mức ngẫu nhiên, cùng nhịp với chu kỳ giá.
   - **Vừa:** có cơ chế, trùng vài lần nhưng chưa đủ mẫu hoặc có ngoại lệ.
   - **Yếu:** chỉ trùng 1–2 lần, hoặc có trùng nhưng không có cơ chế giải thích.
   - **Không liên quan:** đã kiểm tra, không trùng.
6. **Viết chuỗi nhân quả** cho các giả thuyết mạnh/vừa theo dạng:
   `Sự kiện → cơ chế (ai mua/bán, vì sao) → tác động lên cung/cầu → kết quả trên giá (thường cách sự kiện bao nhiêu phiên)`.
7. **Dùng để dự báo:** tra lịch các sự kiện mạnh/vừa sắp tới và đặt chúng cạnh cửa sổ đảo chiều dự phóng. Nếu cả hai trùng nhau, kịch bản đảo chiều đáng tin hơn; nếu lệch, nói rõ là có mâu thuẫn.

---

# PHẦN B – Hướng dẫn diễn giải phân tích kỹ thuật

Đọc file này khi cần giải thích kết quả từ `scripts/indicators.py`, hoặc khi các tín hiệu mâu thuẫn nhau.

## Mục lục
1. Nguyên tắc chung
2. Xu hướng (SMA/EMA)
3. Động lượng (RSI, MACD)
4. Biến động (Bollinger, ATR)
5. Khối lượng
6. Hỗ trợ và kháng cự
7. Mô hình giá thường gặp
8. Kết hợp tín hiệu và xử lý mâu thuẫn
9. Đo rủi ro giá
10. Đọc biểu đồ (khối `doc_bieu_do` và ảnh `chart.py`)
11. Dự báo vùng giá 6 phiên (`forecast6.py`): cách đọc và giới hạn

## 1. Nguyên tắc chung

Mỗi chỉ báo chỉ là một cách nhìn lên cùng một dòng giá, nên chúng thường nói những điều gần giống nhau. Ba chỉ báo cùng báo tăng không phải ba bằng chứng độc lập; thường chúng chỉ phản ánh cùng một đợt giá tăng. Vì thế, ưu tiên kết hợp các nhóm khác nhau: xu hướng, động lượng, khối lượng, và cấu trúc giá (hỗ trợ/kháng cự). Khi cả bốn nhóm cùng hướng, tín hiệu tin cậy hơn.

Xác định xu hướng chính trước, rồi mới đọc chỉ báo ngắn hạn. Tín hiệu "quá mua" trong xu hướng tăng mạnh thường chỉ là giá đi tiếp, còn trong thị trường đi ngang mới hay đi kèm đảo chiều.

## 2. Xu hướng (SMA/EMA)

- Giá trên SMA50 và SMA200, SMA50 trên SMA200: xu hướng tăng bền. Ngược lại là xu hướng giảm.
- Giá cắt xuống dưới SMA20 trong xu hướng tăng thường là nhịp điều chỉnh ngắn; cắt xuống dưới SMA50 kèm khối lượng lớn nghiêm trọng hơn.
- SMA50 cắt lên SMA200 ("golden cross") và cắt xuống ("death cross") là tín hiệu chậm: xuất hiện khi giá đã đi một đoạn, nên dùng để xác nhận xu hướng hơn là để báo sớm.
- EMA phản ứng nhanh hơn SMA nên hợp khung ngắn; SMA phẳng hơn nên hợp khung dài.
- Các đường SMA dốc lên thì làm hỗ trợ động, dốc xuống thì làm kháng cự động.

## 3. Động lượng

**RSI(14)**
- Trên 70: giá tăng nhanh, dễ chững hoặc nghỉ; dưới 30: giá giảm nhanh, dễ hồi kỹ thuật. Đây không phải lệnh bán hay mua; trong xu hướng mạnh RSI có thể ở vùng cực trị nhiều tuần.
- Phân kỳ có giá trị hơn mức tuyệt đối: giá lập đỉnh mới nhưng RSI đỉnh thấp hơn (phân kỳ âm) báo hiệu lực tăng yếu dần; ngược lại với phân kỳ dương ở đáy. Script không tự phát hiện phân kỳ; cần so sánh với chuỗi giá khi thấy cần.
- Trong xu hướng tăng, RSI thường dao động 40–80 và vùng 40–50 hay là điểm hồi; trong xu hướng giảm, 20–60.

**MACD (12, 26, 9)**
- MACD cắt lên signal: động lượng cải thiện; cắt xuống: suy yếu. Cắt xảy ra dưới đường 0 có độ tin cậy thấp hơn trong xu hướng giảm, và ngược lại.
- Histogram thu hẹp trong khi giá vẫn tăng là dấu hiệu đà tăng đang chậm lại, thường đi trước tín hiệu cắt.

## 4. Biến động

**Bollinger (20, 2)**
- Giá chạm dải trên trong xu hướng tăng mạnh thường là "đi dọc dải" chứ chưa phải đảo chiều.
- Dải co hẹp (bandwidth thấp so với lịch sử) thường đi trước một nhịp bứt phá, nhưng không cho biết hướng; chờ giá thoát khỏi dải kèm khối lượng.
- %B > 1 hoặc < 0 nghĩa là giá nằm ngoài dải.

**ATR(14)**
- Đo biên độ dao động trung bình một phiên. Cho biết một nhịp giảm bao nhiêu là "dao động bình thường" và bao nhiêu là bất thường với cổ phiếu này.
- ATR/giá (%) cao nghĩa là cổ phiếu biến động mạnh, nên giảm quy mô vị thế.

## 5. Khối lượng

- Giá bứt phá khỏi kháng cự kèm khối lượng cao hơn trung bình 20 phiên (tỷ lệ > 1.3–1.5) đáng tin hơn bứt phá khối lượng thấp.
- Giá tăng nhưng khối lượng giảm dần: lực mua cạn dần.
- Phiên giảm mạnh với khối lượng đột biến có thể là bán tháo hoặc dấu hiệu cạn cung; cần xem phiên kế tiếp để phân biệt.
- Tỷ lệ khối lượng thấp bất thường quanh ngày lễ hoặc cổ phiếu thanh khoản kém thì không nên suy diễn nhiều.

## 6. Hỗ trợ và kháng cự

- Vùng càng được chạm nhiều lần và càng gần đây thì càng đáng chú ý. Script cung cấp số lần chạm để so sánh.
- Coi chúng là **vùng**, không phải một con số: biên độ vài phần trăm quanh mốc.
- Khi kháng cự bị phá vỡ thật sự, nó thường trở thành hỗ trợ (và ngược lại); kiểm tra bằng việc giá quay lại thử vùng đó mà không thủng.
- Mốc tròn (ví dụ 50.000, 100) và đỉnh/đáy lịch sử hay có phản ứng tâm lý.

## 7. Mô hình giá thường gặp

Chỉ nêu mô hình khi thấy rõ trong dữ liệu hoặc ảnh biểu đồ, và nói mức độ chắc chắn.

- **Vai-đầu-vai / vai-đầu-vai ngược**: đảo chiều; xác nhận khi giá thủng/vượt đường cổ.
- **Hai đỉnh / hai đáy**: đảo chiều; xác nhận khi phá vùng giữa hai đỉnh/đáy.
- **Cờ, tam giác, nêm**: tiếp diễn hoặc đảo chiều tùy hướng phá vỡ; chờ phá vỡ kèm khối lượng.
- **Tích lũy đi ngang (hộp giá)**: biên trên và dưới là kháng cự/hỗ trợ; thoát hộp cho hướng đi tiếp, cần đề phòng phá vỡ giả.

Mô hình nến đơn lẻ (búa, nhấn chìm, doji) chỉ có ý nghĩa tại vùng hỗ trợ/kháng cự và cần phiên sau xác nhận.

## 8. Kết hợp tín hiệu và xử lý mâu thuẫn

Khi tín hiệu mâu thuẫn (ví dụ giá trên SMA200 nhưng MACD cắt xuống):

1. Xác định khung thời gian của người dùng. Tín hiệu dài hạn tăng, ngắn hạn giảm nghĩa là có thể đang điều chỉnh trong xu hướng tăng; người giữ dài hạn và người lướt sóng sẽ kết luận khác nhau.
2. Cho trọng số lớn hơn cho tín hiệu thuộc khung lớn hơn.
3. Xem khối lượng để phân xử: tín hiệu giảm kèm khối lượng cao đáng lo hơn tín hiệu giảm khối lượng thấp.
4. Nếu vẫn không phân xử được, nói thẳng là tín hiệu hỗn hợp và đưa kịch bản "đi ngang" lên mức khả dĩ cao hơn thay vì ép ra một hướng.
5. Đối chiếu với tin tức: một sự kiện sắp tới (công bố lợi nhuận, cổ tức) có thể làm mọi mô hình kỹ thuật mất hiệu lực ngắn hạn.

## 9. Đo rủi ro giá

Skill không đưa vùng mua/bán; phần này giúp diễn giải mức rủi ro.

- **ATR và độ biến động năm hóa** cho biết một phiên/một năm giá thường dao động bao nhiêu. Biến động cao nghĩa là cùng một số tiền bỏ vào, mức lỗ tạm thời có thể lớn hơn nhiều.
- **Khoảng cách tới hỗ trợ gần nhất và đáy 60 phiên** là mức giảm "bình thường" có thể xảy ra mà chưa phá cấu trúc; nếu thủng các mức này, rủi ro chuyển sang mức cao hơn.
- **Mức sụt sâu nhất trong lúc nắm giữ** (từ `risk.py`) quan trọng hơn lợi nhuận cuối kỳ: nhiều người buộc phải bán ở đáy vì không chịu nổi mức sụt tạm thời.
- **Vị trí trong biên độ 60 phiên:** mua khi giá gần đỉnh biên độ của một cổ phiếu có chu kỳ thường có rủi ro sụt tạm thời cao hơn; so số liệu nhóm "ngày có vị trí tương tự" với nhóm "mọi ngày" để thấy chênh lệch.
- **Thanh khoản thấp** làm mọi con số trên kém tin cậy hơn, vì giá có thể nhảy cóc.
- Nhắc người dùng rằng mức lỗ thật phụ thuộc vào số tiền họ bỏ vào, và đó là quyết định theo hoàn cảnh tài chính của họ, không phải theo biểu đồ.

## 10. Đọc biểu đồ (khối `doc_bieu_do` và ảnh `chart.py`)

`indicators.py` có khối `doc_bieu_do` mô tả những gì mắt người đọc trên biểu đồ. Mọi mục trong đó chỉ để **mô tả**; không mục nào đủ để dự báo riêng lẻ. Viết phần "Đọc biểu đồ" trong báo cáo (5–8 dòng) theo thứ tự sau, và ở mỗi dòng nêu con số từ file chứ không viết cảm tính:

1. **Xu hướng:** giá so với SMA20/50/200 và độ dốc của chúng (mục 2).
2. **Động lượng:** RSI, MACD, và `phan_ky_rsi` nếu có. Phân kỳ chỉ là cảnh báo sớm, hay sai khi xu hướng mạnh; chờ giá xác nhận.
3. **Biến động:** `nen_bollinger`. "Nén chặt" (độ rộng thấp nhất khoảng 20% lịch sử gần) thường đi trước một nhịp biến động lớn nhưng không cho biết hướng; "giãn rộng" nghĩa là biến động đã xảy ra và có thể đang nguội đi.
4. **Khối lượng và giá:** `khoi_luong_va_gia`. Phiên giảm kèm khối lượng từ 1,5 lần trung bình là áp lực bán rõ hơn phiên giảm khối lượng thấp; ngược lại với phiên tăng.
5. **Nến và chuỗi phiên:** `nen_phien_cuoi`, `chuoi_phien`, `gap_5_phien`. Bóng dài hoặc nến nhấn chìm chỉ có ý nghĩa tại vùng hỗ trợ/kháng cự (mục 7). Khoảng trống giá thường được giá quay lại "lấp"; nêu mức của nó như một vùng để theo dõi.
6. **Cấu trúc:** hỗ trợ/kháng cự gần nhất và số lần chạm; vị trí giá trong biên độ 20 và 60 phiên.
7. **Ghép với chu kỳ:** pha hiện tại và cửa sổ đảo chiều từ `cycles.py`. Nếu biểu đồ và chu kỳ cùng nói một điều, nêu rõ; nếu mâu thuẫn, nêu rõ và nói mình ưu tiên khung nào theo mục 8.

Ảnh biểu đồ (`chart.py`) dùng cho người đọc. Cách đọc ảnh: nến **rỗng = tăng, đặc = giảm**; đường xanh dương là SMA20, cam là SMA50; vùng nhạt quanh giá là dải Bollinger; ▲▼ là đáy/đỉnh chu kỳ do zigzag tìm; "KC/HT" là kháng cự/hỗ trợ ước lượng; vùng tím bên phải là dự báo 6 phiên.

## 11. Dự báo vùng giá 6 phiên (`forecast6.py`): cách đọc và giới hạn

**Nó là gì.** Một vùng giá khả dĩ cho từng phiên trong 6 phiên giao dịch tới, tính bằng mô phỏng từ chính lịch sử biến động của mã. Nó trả lời "giá có thể dao động trong khoảng nào" và "xác suất chạm một mức nào đó là bao nhiêu". Nó **không đoán hướng**: độ lệch đặt bằng 0, nên xác suất tăng/giảm quanh 50% là bình thường, không phải tín hiệu trung lập có chủ ý của người phân tích.

**Ba vùng.** Vùng 50% (giá thực tế nên rơi vào đó khoảng một nửa số lần), vùng 80% và vùng 95%. Giá đóng cửa ra ngoài vùng 80% khoảng 1 lần trong 5 phiên là bình thường. Ra ngoài vùng 95% là hiếm và là lý do để xem lại kịch bản.

**Độ tin cậy của chính vùng này.** Script tự kiểm chứng bằng dữ liệu quá khứ (`kiem_chung_qua_khu`): tại mỗi thời điểm cũ chỉ dùng dữ liệu đến lúc đó, dự báo 6 phiên rồi so với giá thực.
- `do_phu_goc` gần 50/80/95 nghĩa là mô hình khớp mã này. Thấp hơn nhiều (ví dụ vùng 80% chỉ phủ 50%) nghĩa là giá của mã này hay đi một mạch nhiều phiên (có đà hoặc có chu kỳ), vùng gốc quá hẹp. Script nới vùng bằng `he_so_gian_vung_theo_phien` (riêng từng phiên) và chấm lại trên 30% dữ liệu sau cùng, chưa dùng để hiệu chỉnh (`hieu_chinh_ngoai_mau`). Số ngoài mẫu mới là số đáng tin.
- Dưới 30 điểm kiểm chứng hoặc dữ liệu ngắn: coi vùng là chưa kiểm chứng và nói thẳng điều đó.
- Các điểm kiểm chứng chồng lấn nhau, nên sai số của tỷ lệ phủ lớn hơn con số mẫu gợi ý.

**Tín hiệu vị trí tương tự** (`vi_tri_tuong_tu`) cho biết những ngày trước đây có cùng vị trí trong biên độ 20 phiên và cùng chiều 5 phiên thì 6 phiên sau giá đi thế nào. Chỉ dùng khi mẫu từ 30 trở lên **và** `tin_hieu_vi_tri_tuong_tu.ket_luan` trong phần kiểm chứng nói nó hơn cách đoán theo xu thế phổ biến. Trên hầu hết cổ phiếu, kết luận sẽ là "không hơn", khi đó bỏ qua nó. Đừng đưa nó vào báo cáo như một lý do tăng/giảm.

**Chấm dự báo cũ** (`cham_du_bao_truoc`, cần file `--lich-su`): mỗi lần chạy, script chấm các dự báo lập trước đó theo giá thực, và cộng dồn tỷ lệ giá nằm trong vùng 50/80/95.

**Giới hạn cần nói rõ khi báo cáo cho người dùng:**
- Không tính tin tức bất ngờ, nhịp rung lắc cả thị trường, hay thay đổi quy định; các sự kiện đó có thể đưa giá ra ngoài mọi vùng.
- Ngày nghỉ lễ chỉ được loại trừ nếu truyền `--nghi`; kiểm tra lịch thực tế.
- Xác suất chạm mức giá tính theo giá đóng cửa; giá trong phiên có thể chạm sớm hơn.
- Biên độ sàn (HOSE ±7%) đã được chặn mỗi phiên; mã trên HNX hay UPCoM dùng `--gioi-han 0.10` hoặc `0.15`.
- Hướng đi (tăng hay giảm) do phần phân tích nguyên nhân và kịch bản đánh giá, không do script này.
