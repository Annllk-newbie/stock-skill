#!/usr/bin/env python3
"""Đo rủi ro giá nếu mua ở mức giá hiện tại (hoặc mức giá dự định).

Cách dùng:
    python risk.py gia.csv
    python risk.py gia.csv --horizons 5 20 60     # các khung nắm giữ (phiên)
    python risk.py gia.csv --entry 25300          # giá dự định mua thay vì giá đóng cửa cuối

Đầu ra (JSON), cho từng khung nắm giữ:
  - phân phối lợi nhuận lịch sử sau h phiên (tỷ lệ có lãi, trung vị, kịch bản xấu 10%/5%, tệ nhất)
  - mức sụt sâu nhất TRONG lúc nắm giữ (max adverse excursion): giá từng xuống thấp hơn giá mua bao nhiêu
  - cùng các số đó nhưng chỉ tính những ngày giá ở vị trí tương tự trong biên độ 60 phiên (gần đỉnh/gần đáy)
Thêm: độ biến động năm hóa, mức sụt giảm lớn nhất lịch sử, khoảng cách tới đỉnh/đáy 52 tuần và 60 phiên,
thanh khoản (giá trị giao dịch trung bình).

Đây là thống kê quá khứ, không phải xác suất tương lai.
"""
import argparse
import json
import math
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_prices, median, percentile, r  # noqa: E402


def range_pos(closes, i, n=60):
    seg = closes[max(0, i - n + 1): i + 1]
    lo, hi = min(seg), max(seg)
    return (closes[i] - lo) / (hi - lo) if hi > lo else 0.5


def forward_stats(data, idxs, h):
    rets, mae = [], []
    for i in idxs:
        if i + h >= len(data):
            continue
        entry = data[i]["close"]
        rets.append((data[i + h]["close"] / entry - 1) * 100)
        low = min(d["low"] for d in data[i + 1: i + h + 1])
        mae.append((low / entry - 1) * 100)
    if len(rets) < 10:
        return {"so_mau": len(rets), "ghi_chu": "quá ít mẫu để thống kê"}
    return {
        "so_mau": len(rets),
        "ti_le_co_lai_pct": r(sum(1 for x in rets if x > 0) / len(rets) * 100, 1),
        "loi_nhuan_trung_vi_pct": r(median(rets)),
        "kich_ban_xau_10pct": r(percentile(rets, 10)),
        "kich_ban_xau_5pct": r(percentile(rets, 5)),
        "te_nhat_pct": r(min(rets)),
        "tot_nhat_pct": r(max(rets)),
        "sut_sau_nhat_trong_luc_giu": {
            "trung_vi_pct": r(median(mae)),
            "xau_10pct": r(percentile(mae, 10)),
            "te_nhat_pct": r(min(mae)),
        },
    }


def max_drawdown(closes):
    peak = closes[0]
    mdd = 0
    peak_i = trough_i = best_peak_i = 0
    for i, c in enumerate(closes):
        if c > peak:
            peak, peak_i = c, i
        dd = c / peak - 1
        if dd < mdd:
            mdd, trough_i, best_peak_i = dd, i, peak_i
    return mdd * 100, best_peak_i, trough_i


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path")
    ap.add_argument("--horizons", type=int, nargs="+", default=[5, 20, 60])
    ap.add_argument("--entry", type=float, help="giá dự định mua (mặc định: giá đóng cửa cuối)")
    args = ap.parse_args()

    data = load_prices(args.csv_path, min_rows=80)
    closes = [d["close"] for d in data]
    last = len(data) - 1
    entry = args.entry or closes[-1]

    rets = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    vol_ann = st.pstdev(rets) * math.sqrt(252) * 100

    cur_pos = range_pos(closes, last)
    all_idx = list(range(60, len(data)))
    similar = [i for i in all_idx if abs(range_pos(closes, i) - cur_pos) <= 0.1]

    horizons = {}
    for h in args.horizons:
        horizons[f"{h}_phien"] = {"moi_ngay": forward_stats(data, all_idx, h),
                                 "ngay_co_vi_tri_tuong_tu": forward_stats(data, similar, h)}

    mdd, p_i, t_i = max_drawdown(closes)
    win52 = data[-252:]
    hi52 = max(d["high"] for d in win52)
    lo52 = min(d["low"] for d in win52)
    win60 = data[-60:]
    hi60 = max(d["high"] for d in win60)
    lo60 = min(d["low"] for d in win60)

    liq = None
    vols = [d["volume"] for d in data[-20:] if d["volume"] is not None]
    if len(vols) >= 10:
        val = [d["volume"] * d["close"] for d in data[-20:] if d["volume"] is not None]
        liq = {"khoi_luong_tb_20_phien": r(st.mean(vols), 0), "gia_tri_gd_tb_20_phien": r(st.mean(val), 0),
               "ghi_chu": "Giá trị giao dịch thấp nghĩa là khó bán nhanh khi cần, và giá dễ bị một nhóm nhỏ chi phối."}

    out = {
        "ngay_cuoi": data[-1]["date"].isoformat(),
        "gia_mua_gia_dinh": r(entry),
        "vi_tri_trong_bien_do_60_phien": r(cur_pos, 2),
        "vi_tri_dien_giai": ("gần đỉnh biên độ" if cur_pos > 0.8 else "gần đáy biên độ" if cur_pos < 0.2 else "giữa biên độ"),
        "do_bien_dong_nam_hoa_pct": r(vol_ann, 1),
        "dao_dong_1_phien_dien_hinh_pct": r(st.pstdev(rets) * 100, 2),
        "sut_giam_lon_nhat_lich_su": {"pct": r(mdd), "tu_ngay": data[p_i]["date"].isoformat(),
                                      "den_ngay": data[t_i]["date"].isoformat()},
        "khoang_cach": {
            "toi_dinh_52_tuan_pct": r((hi52 / entry - 1) * 100), "toi_day_52_tuan_pct": r((lo52 / entry - 1) * 100),
            "toi_dinh_60_phien_pct": r((hi60 / entry - 1) * 100), "toi_day_60_phien_pct": r((lo60 / entry - 1) * 100),
        },
        "theo_khung_nam_giu": horizons,
        "thanh_khoan": liq,
        "ghi_chu": ("Số âm ở 'kịch bản xấu' và 'sụt sâu nhất' là mức lỗ tạm thời/thực tế từng xảy ra khi mua ở những thời điểm tương tự. "
                    "'ngay_co_vi_tri_tuong_tu' = các ngày giá nằm cùng vùng (±10%) trong biên độ 60 phiên như hôm nay. "
                    "Mẫu chồng lấn nhau nên số mẫu thực sự độc lập ít hơn con số hiển thị."),
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
