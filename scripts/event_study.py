#!/usr/bin/env python3
"""So diễn biến giá quanh một loại sự kiện lặp lại qua nhiều năm (nghiên cứu sự kiện).

Dùng khi chu kỳ có vẻ lệch thời điểm giữa các năm: rất có thể nguyên nhân là một sự kiện mà ngày
của nó thay đổi mỗi năm (Tết âm lịch, ngày công bố KQKD, ngày chốt quyền, ngày cơ cấu ETF...).
Thay vì so theo lịch dương, ta "căn" giá theo ngày sự kiện rồi xem phản ứng có lặp lại không.

Cách dùng:
    python event_study.py gia.csv --dates 2022-02-01 2023-01-22 2024-02-10 2025-01-29
    python event_study.py gia.csv --dates-file tet.txt --before 15 --after 10
    python event_study.py gia.csv --dates-file kqkd.txt --benchmark vnindex.csv   # trừ biến động thị trường chung

File ngày: mỗi dòng một ngày, có thể kèm nhãn sau dấu phẩy, ví dụ "2024-02-10,Tết Giáp Thìn".
Nếu ngày sự kiện không phải ngày giao dịch, dùng phiên giao dịch đầu tiên sau đó làm phiên 0.

Đầu ra (JSON):
  - từng sự kiện: biến động giá trước sự kiện (phiên -before đến -1) và sau sự kiện (phiên 0 đến +after)
  - trung bình/trung vị lợi nhuận tích lũy theo từng phiên tương đối, tỷ lệ số lần dương
  - phiên tương đối mà giá thường thấp nhất/cao nhất -> cho biết đỉnh/đáy thường xuất hiện trước/sau sự kiện bao lâu
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_prices, median, parse_date, r  # noqa: E402


def read_dates(args):
    items = []
    for s in args.dates or []:
        items.append((parse_date(s), s))
    if args.dates_file:
        with open(args.dates_file, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(",", 1)
                items.append((parse_date(parts[0]), parts[1].strip() if len(parts) > 1 else parts[0]))
    if not items:
        sys.exit("Cần --dates hoặc --dates-file.")
    return sorted(items)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path")
    ap.add_argument("--dates", nargs="+")
    ap.add_argument("--dates-file")
    ap.add_argument("--before", type=int, default=10)
    ap.add_argument("--after", type=int, default=10)
    ap.add_argument("--benchmark", help="CSV giá chỉ số chung để tính biến động vượt trội so với thị trường")
    args = ap.parse_args()

    data = load_prices(args.csv_path, min_rows=30)
    dates = [d["date"] for d in data]
    bench = None
    if args.benchmark:
        b = load_prices(args.benchmark, min_rows=30)
        bench = {d["date"]: d["close"] for d in b}

    def idx_on_or_after(day):
        for i, d in enumerate(dates):
            if d >= day:
                return i
        return None

    offsets = list(range(-args.before, args.after + 1))
    paths, events, skipped = [], [], []
    for day, label in read_dates(args):
        i = idx_on_or_after(day)
        if i is None or i - args.before - 1 < 0 or i + args.after >= len(data):
            skipped.append({"ngay": day.isoformat(), "nhan": label, "ly_do": "không đủ dữ liệu quanh ngày này"})
            continue
        base_i = i - args.before - 1  # phiên mốc ngay trước cửa sổ
        base = data[base_i]["close"]

        def ret(j):
            x = data[j]["close"] / base - 1
            if bench is not None:
                b0, b1 = bench.get(data[base_i]["date"]), bench.get(data[j]["date"])
                if b0 and b1:
                    x -= b1 / b0 - 1
            return x * 100

        path = [ret(i + o) for o in offsets]
        paths.append(path)
        pre = path[args.before - 1] if args.before > 0 else 0.0  # tới phiên -1
        post = path[-1] - pre
        lo_o = offsets[min(range(len(path)), key=lambda k: path[k])]
        hi_o = offsets[max(range(len(path)), key=lambda k: path[k])]
        events.append({"ngay_su_kien": day.isoformat(), "nhan": label, "phien_0": data[i]["date"].isoformat(),
                       "bien_dong_truoc_pct": r(pre), "bien_dong_sau_pct": r(post),
                       "phien_thap_nhat": lo_o, "phien_cao_nhat": hi_o})

    if len(paths) < 2:
        sys.exit("Cần ít nhất 2 sự kiện có đủ dữ liệu xung quanh.")

    profile = []
    for k, o in enumerate(offsets):
        col = [p[k] for p in paths]
        profile.append({"phien": o, "tb_pct": r(sum(col) / len(col)), "trung_vi_pct": r(median(col)),
                        "ti_le_duong_pct": r(sum(1 for x in col if x > 0) / len(col) * 100, 0)})

    pre_vals = [e["bien_dong_truoc_pct"] for e in events]
    post_vals = [e["bien_dong_sau_pct"] for e in events]
    n = len(events)

    def consistency(vals):
        up = sum(1 for v in vals if v > 0)
        return {"so_lan_tang": up, "so_lan_giam": n - up, "trung_vi_pct": r(median(vals)),
                "nhat_quan": n >= 4 and (up / n >= 0.75 or up / n <= 0.25)}

    out = {
        "so_su_kien": n, "cua_so": [-args.before, args.after],
        "so_voi_thi_truong": bench is not None,
        "truoc_su_kien": consistency(pre_vals),
        "sau_su_kien": consistency(post_vals),
        "phien_day_thuong_gap": median([e["phien_thap_nhat"] for e in events]),
        "phien_dinh_thuong_gap": median([e["phien_cao_nhat"] for e in events]),
        "tung_su_kien": events,
        "duong_trung_binh": profile,
        "bo_qua": skipped,
        "ghi_chu": ("Lợi nhuận tích lũy tính từ phiên ngay trước cửa sổ. 'nhat_quan' = cùng chiều ở >= 75% số lần (cần >= 4 sự kiện). "
                    "Dưới 4–5 sự kiện thì chỉ nên coi là gợi ý. Nếu có --benchmark, số liệu là phần vượt trội so với chỉ số."),
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
