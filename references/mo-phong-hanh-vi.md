# Mô phỏng hành vi nhà đầu tư (agent kiểu A và C)

File này do phiên chính đọc khi chạy chế độ **M – Mô phỏng hành vi** hoặc khi phân tích sâu dùng mục "Hành vi đám đông". Script: `scripts/mo_phong_hanh_vi.py` (cần `numpy`).

## Ba kiểu agent

- **A – Đám đông toàn thị trường:** bộ máy chạy trên VN-Index, cho ra đường đi VN-Index theo từng kịch bản.
- **C – Phản ứng theo từng mã:** cùng bộ máy, chạy riêng cho từng mã trong `<DANH_SÁCH_MÃ>` (mục 1.1 của SKILL.md), nhận đường đi VN-Index của A làm đầu vào (nhỏ lẻ nhìn VN-Index để quyết định).
- **B – Bản sao hành vi của người dùng:** CHƯA LÀM. Khi người dùng gửi lịch sử lệnh xuất từ VNDirect sẽ thêm. Tham số `--ho-so-ca-nhan` hiện chỉ báo lỗi.

## Nhóm nhà đầu tư trong mô hình

| Nhóm | Vốn mỗi agent | Hành vi |
|---|---|---|
| Nhỏ lẻ (600 agent/lần chạy) | 100–200 triệu | bầy đàn (Lux–Marchesi), đuổi nhịp 5 phiên, nhìn VN-Index, bán sớm khi lãi/gồng khi lỗ (Shefrin–Statman, Odean 1998), ngại thua lỗ λ (Kahneman–Tversky): biến động cao thì đòi tín hiệu mạnh hơn mới mua, sau khi cắt lỗ thì "sợ" không mua lại khoảng 2λ phiên; 30% dùng margin (bán giải chấp khi lỗ 12%), còn lại cắt lỗ ở mức 8–25% |
| Lớn (30 agent) | 5–10 tỷ | neo giá trị theo EMA 120 phiên, ít bầy đàn (0,3 lần nhỏ lẻ), cắt lỗ có kỷ luật ở −10% |
| Khối ngoại | số thật | dòng ròng theo mã từ VND MCP; tương lai lấy mẫu khối 5 phiên từ 120 phiên gần nhất |

Luật thị trường: biên độ HOSE ±7%, bước giá HOSE, lô 100, T+2 (mua phiên này, phiên sau chưa bán được), phí 0,15% mỗi chiều, thuế bán 0,1%. Tỷ trọng giá trị giao dịch của nhỏ lẻ mặc định 0,70 (`--ty-trong-nho-le`); khối ngoại lấy tỷ trọng thật; phần còn lại là nhà đầu tư lớn.

## Dữ liệu đầu vào

Script KHÔNG tự lấy dữ liệu.
- Giá: file `research/gia/gia_<MÃ>_ctck.csv` và `gia_VNINDEX_ctck.csv` của `lay_gia_cty_ck.py` (dùng được ngay, cột `value` thiếu thì script ước = giá × khối lượng). Không chạy được script giá thì tạo file cùng khuôn từ VND MCP `get_stock_price_by_date` (adOpen/adHigh/adLow/adClose, nmVolume, nmValue) và `get_vnmarket_prices` (mỗi lần gọi một chỉ số); giao cho agent Haiku, tối đa 4 lệnh gọi song song, gặp "throttled" thì chờ 20 giây.
- Khối ngoại: `research/gia/khoi_ngoai.csv`, cột `date,code,buyVal,sellVal,netVal` (đồng), từ VND `get_foreign_trading` (một lần gọi mỗi mã, size ≥ số phiên, sort asc).
- Cần ≥ 200 phiên liên tục có khối ngoại (tốt nhất 1–2 năm). Ít hơn 140 phiên thì script dừng.

## Hai bước

Trước khi chạy: `mkdir -p research/mo-phong && cp research/du-an/data/mo-phong/ts_*.json research/mo-phong/ 2>/dev/null` (tham số đã hiệu chỉnh ở lần trước, agent T tải về). Không có file `ts_<MÃ>.json` thì phải chạy bước 1 cho mã đó.

**1. Hiệu chỉnh (chỉ ở phân tích sâu, hoặc khi người dùng yêu cầu; khoảng 1–2 phút mỗi mã, cả VN-Index + 4 mã khoảng 3–4 phút khi chạy 2 tiến trình song song):**
```bash
G=research/gia; S=research/skill/scripts; O=research/mo-phong; mkdir -p $O
python $S/mo_phong_hanh_vi.py hieu-chinh --ma VNINDEX --gia $G/gia_VNINDEX_ctck.csv --khoi-ngoai $G/khoi_ngoai.csv --out $O/ts_VNINDEX.json --im
for M in <DANH_SÁCH_MÃ>; do
  python $S/mo_phong_hanh_vi.py hieu-chinh --ma $M --gia $G/gia_${M}_ctck.csv --thi-truong $G/gia_VNINDEX_ctck.csv \
     --khoi-ngoai $G/khoi_ngoai.csv --out $O/ts_$M.json --im
done
```
Thử 150 bộ tham số × 8 lần chạy (cùng một lượt tính, mọi bộ dùng chung số ngẫu nhiên nên so sánh công bằng), rồi tinh chỉnh 35 bộ × 16 lần và 21 bộ × 24 lần, so 6 "dấu vân tay" của giá thật (độ biến động, đuôi dày, tự tương quan, cụm biến động, tương quan thanh khoản–biến động, tương quan khối ngoại–giá). Kiểm tra ngoài mẫu ở **hai mốc** (hiệu chỉnh 60% đầu → chấm 20% kế tiếp; hiệu chỉnh 80% đầu → chấm 20% cuối), mỗi mốc so với **mô hình rỗng** (không có hành vi). Cạnh nhau hai lệnh `hieu-chinh` là đủ cho 2 lõi CPU; nhiều hơn chỉ xếp hàng. Lưu `ts_<MÃ>.json` vào dự án ở `claude/chung-khoan/data/mo-phong/ts_<MÃ>.json` (ghi đè) để các lần chạy sau không phải hiệu chỉnh lại.

**2. Kịch bản (mỗi lần chạy; khoảng 1 phút mỗi mã với 2000 lần chạy):**
```bash
python $S/mo_phong_hanh_vi.py kich-ban --ma $M --gia $G/gia_${M}_ctck.csv --thi-truong $G/gia_VNINDEX_ctck.csv \
   --khoi-ngoai $G/khoi_ngoai.csv --tham-so $O/ts_$M.json --tham-so-thi-truong $O/ts_VNINDEX.json \
   --phien 6 --so-lan 2000 --out $O/kb_$M.json --chu > $O/kb_$M.txt
```
Sáu kịch bản: `co_so`, `tin_tot`, `tin_xau` (tin riêng của mã), `khoi_ngoai_ban`, `khoi_ngoai_mua`, `thi_truong_hoang_loan` (A chạy với cú sốc tâm lý toàn thị trường, C nhận đường đi đó). Mỗi kịch bản cho: vùng giá từng phiên, xác suất cao hơn giá hiện tại, xác suất chạm trần/sàn, dòng tiền ròng ước của nhỏ lẻ/lớn/ngoại (tỷ đồng), tâm lý đám đông, tỷ lệ nhỏ lẻ cắt lỗ, PGR/PLR (Odean). Mục `hien_tai`: tâm lý đám đông lúc này, tỷ lệ nhỏ lẻ đang lãi/lỗ trên 10% (ước từ hồ sơ khối lượng 60 phiên), giá vốn trung vị.

## Cách đưa vào báo cáo (quy tắc)

- Mục **"Hành vi đám đông (mô phỏng)"** đặt sau mục dự báo 6 phiên. Mỗi mã 3–5 gạch đầu dòng chép từ `kb_<MÃ>.txt`: trạng thái hiện tại; kịch bản cơ sở; hai kịch bản lệch nhau nhiều nhất; ai đang là bên mua/bán chính.
- **Luôn ghi kết quả kiểm tra ngoài mẫu** dạng "đạt x/2 mốc" (`kiem_tra_ngoai_mau.so_moc_dat`). Chỉ 2/2 mới được viết "mô hình hành vi khớp tốt hơn ngẫu nhiên". 1/2 hoặc 0/2 thì ghi rõ: "chưa ổn định / chưa giải thích giá tốt hơn ngẫu nhiên ở mã này – chỉ đọc như minh họa cơ chế". Không được bỏ dòng này.
- Dòng "⚠ biến động mô phỏng bằng … lần mức bình thường" có trong `kb_<MÃ>.txt` thì chép nguyên ý: vùng giá và xác suất chạm sàn của mã đó là kịch bản căng thẳng chưa kiểm chứng, không được viết như xác suất thật.
- Tham số có `khoang_tot` rộng (vd λ từ 1,2 đến 3,3) nghĩa là dữ liệu giá không xác định được tham số đó: ghi "chưa xác định được", không diễn giải như sự thật về tâm lý nhà đầu tư.
- Dòng tiền theo nhóm, tỷ lệ đang lãi/lỗ, PGR/PLR là **ước lượng của mô hình**, không phải số liệu thật: không gắn nhãn ✔, ghi "(mô phỏng)". Số khối ngoại đầu vào thì là số thật từ VND.
- Vùng giá của mô phỏng hành vi KHÔNG thay thế `forecast6.py` (đã có kiểm chứng riêng). Hai bên lệch nhau nhiều thì nêu cả hai và nói mô hình nào đã được kiểm chứng lâu hơn.
- Không dùng kết quả để đưa lệnh mua/bán.

## Giới hạn cần nói với người dùng
Mô hình rút gọn: một nhịp quyết định mỗi phiên, không có sổ lệnh trong phiên, không có tự doanh, không có tin tức thật ngoài kịch bản. Nó cho biết **cơ chế hành vi nào phù hợp với cách giá đã chạy** và **đám đông có thể phản ứng thế nào** trong từng kịch bản, không cho biết điều gì chắc chắn sẽ xảy ra.
