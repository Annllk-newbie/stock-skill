#!/usr/bin/env python3
"""Phát hiện chu kỳ tăng/giảm trong chuỗi giá, kể cả khi chu kỳ thay đổi giữa các năm.

Cách dùng:
    python cycles.py gia.csv                    # ngưỡng đảo chiều tự động
    python cycles.py gia.csv --threshold 6      # coi là đảo chiều khi giá đi ngược >= 6%
    python cycles.py gia.csv --window 3         # ± phiên khi đối chiếu sự kiện với đỉnh/đáy

Đầu ra (JSON):
  - đỉnh/đáy đã xác nhận (ngày, giá, thứ, ngày trong tháng) để đối chiếu với lịch sự kiện
  - độ dài chu kỳ, pha tăng/giảm, biên độ, độ đều đặn – cho toàn bộ dữ liệu VÀ cho từng năm
  - phát hiện thời điểm chu kỳ thay đổi (dài ra/ngắn lại) và xu hướng độ dài chu kỳ theo thời gian
  - dự phóng lần đảo chiều tới, dựa trên giai đoạn gần đây nếu chu kỳ đã thay đổi
  - đỉnh/đáy cao nhất/thấp nhất của từng năm (xem chu kỳ năm có rơi vào cùng thời điểm không)
  - hiệu ứng lịch kèm chỉ số t, và độ nhất quán theo tháng qua các năm

Độ dài dữ liệu nên có: ít nhất 5–6 chu kỳ hoàn chỉnh. Chu kỳ ~1 tháng: 2–3 năm; ~1 quý: 3–5 năm;
theo năm/mùa vụ: 5–10 năm. Nên dùng giá ĐÃ ĐIỀU CHỈNH cổ tức/chia tách.
"""
import argparse
import json
import math
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import add_business_days, load_prices, median, percentile, r  # noqa: E402

WEEKDAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]


# ---------- đỉnh / đáy ----------
def zigzag(closes, th):
    pivots = []
    trend = None
    lo_i = hi_i = ext = 0
    for i in range(1, len(closes)):
        p = closes[i]
        if trend is None:
            if p < closes[lo_i]:
                lo_i = i
            if p > closes[hi_i]:
                hi_i = i
            if p >= closes[lo_i] * (1 + th) and lo_i < i:
                pivots.append(("day", lo_i))
                trend, ext = "up", i
            elif p <= closes[hi_i] * (1 - th) and hi_i < i:
                pivots.append(("dinh", hi_i))
                trend, ext = "down", i
        elif trend == "up":
            if p > closes[ext]:
                ext = i
            elif p <= closes[ext] * (1 - th):
                pivots.append(("dinh", ext))
                trend, ext = "down", i
        else:
            if p < closes[ext]:
                ext = i
            elif p >= closes[ext] * (1 + th):
                pivots.append(("day", ext))
                trend, ext = "up", i
    forming = ("dinh" if trend == "up" else "day", ext) if trend else None
    return pivots, forming


def stats(vals):
    if not vals:
        return None
    m = st.mean(vals)
    sd = st.pstdev(vals) if len(vals) > 1 else 0.0
    return {"so_mau": len(vals), "trung_binh": r(m, 1), "trung_vi": r(median(vals), 1),
            "do_lech_chuan": r(sd, 1), "ngan_nhat": r(min(vals), 1), "dai_nhat": r(max(vals), 1),
            "he_so_bien_thien": r(sd / abs(m), 2) if m else None}


def regularity_label(cv):
    if cv is None:
        return "không đủ dữ liệu"
    if cv < 0.25:
        return "khá đều"
    if cv < 0.5:
        return "đều vừa phải"
    return "không đều"


# ---------- thay đổi chu kỳ theo thời gian ----------
def change_point(cycles, data):
    """cycles: list (start_idx, length) đã sắp theo thời gian. Tìm điểm tách làm hai giai đoạn
    có độ dài chu kỳ trung bình khác nhau rõ nhất (cần >= 3 chu kỳ mỗi bên)."""
    n = len(cycles)
    if n < 6:
        return None
    lens = [c[1] for c in cycles]
    best = None
    for s in range(3, n - 2):
        a, b = lens[:s], lens[s:]
        ma, mb = st.mean(a), st.mean(b)
        va = st.pvariance(a) if len(a) > 1 else 0
        vb = st.pvariance(b) if len(b) > 1 else 0
        se = math.sqrt(va / len(a) + vb / len(b)) or 1e-9
        t = (mb - ma) / se
        if best is None or abs(t) > abs(best[0]):
            best = (t, s, ma, mb)
    t, s, ma, mb = best
    rel = (mb - ma) / ma if ma else 0
    changed = abs(t) >= 3 and abs(rel) >= 0.2
    return {
        "co_thay_doi": changed,
        "ngay_bat_dau_giai_doan_moi": data[cycles[s][0]]["date"].isoformat(),
        "chi_so_phien_bat_dau": cycles[s][0],
        "do_dai_tb_truoc": r(ma, 1), "do_dai_tb_sau": r(mb, 1),
        "thay_doi_pct": r(rel * 100, 0), "chi_so_t": r(t, 1),
        "dien_giai": (("Chu kỳ " + ("DÀI RA" if mb > ma else "NGẮN LẠI") +
                       f" từ khoảng {data[cycles[s][0]]['date'].isoformat()}: hãy tìm xem điều gì thay đổi quanh thời điểm này "
                       "(quy định thị trường, chính sách cổ tức, mảng kinh doanh, nhóm nhà đầu tư chính...).")
                      if changed else "Chưa thấy thay đổi đáng kể về độ dài chu kỳ giữa các giai đoạn."),
    }


def length_trend(cycles, data):
    """Hồi quy độ dài chu kỳ theo thời gian (năm) -> chu kỳ dài thêm/ngắn đi bao nhiêu phiên mỗi năm."""
    if len(cycles) < 5:
        return None
    x = [(data[c[0]]["date"] - data[0]["date"]).days / 365.25 for c in cycles]
    y = [c[1] for c in cycles]
    mx, my = st.mean(x), st.mean(y)
    sxx = sum((a - mx) ** 2 for a in x)
    if sxx == 0:
        return None
    slope = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx
    resid = [b - (my + slope * (a - mx)) for a, b in zip(x, y)]
    se = math.sqrt(sum(e * e for e in resid) / max(1, len(y) - 2) / sxx)
    t = slope / se if se else None
    sig = t is not None and abs(t) >= 2
    return {"phien_moi_nam": r(slope, 1), "chi_so_t": r(t, 1),
            "dien_giai": ("chu kỳ dài dần" if slope > 0 else "chu kỳ ngắn dần") if sig else "không có xu hướng rõ"}


def by_year(pivots, phases, cycles, data):
    out = {}
    years = sorted({d["date"].year for d in data})
    for y in years:
        cy = [c[1] for c in cycles if data[c[0]]["date"].year == y]
        rises = [p for p in phases if p["kind"] == "tang" and data[p["start"]]["date"].year == y]
        falls = [p for p in phases if p["kind"] == "giam" and data[p["start"]]["date"].year == y]
        out[str(y)] = {
            "so_phien_du_lieu": sum(1 for d in data if d["date"].year == y),
            "so_dinh": sum(1 for k, i in pivots if k == "dinh" and data[i]["date"].year == y),
            "so_day": sum(1 for k, i in pivots if k == "day" and data[i]["date"].year == y),
            "do_dai_chu_ky_trung_vi": r(median(cy), 1) if cy else None,
            "do_lech_chuan_chu_ky": r(st.pstdev(cy), 1) if len(cy) > 1 else None,
            "bien_do_tang_trung_vi_pct": r(median([p["amp"] for p in rises])) if rises else None,
            "bien_do_giam_trung_vi_pct": r(median([p["amp"] for p in falls])) if falls else None,
        }
    return out


def yearly_extremes(data):
    """Ngày giá cao nhất/thấp nhất mỗi năm (chỉ năm có >= 200 phiên) – để xem chu kỳ năm có lặp đúng thời điểm."""
    years = {}
    for i, d in enumerate(data):
        years.setdefault(d["date"].year, []).append(i)
    out = []
    for y, idx in sorted(years.items()):
        if len(idx) < 200:
            continue
        hi = max(idx, key=lambda i: data[i]["close"])
        lo = min(idx, key=lambda i: data[i]["close"])
        out.append({"nam": y, "ngay_cao_nhat": data[hi]["date"].isoformat(), "thang_cao_nhat": data[hi]["date"].month,
                    "ngay_thap_nhat": data[lo]["date"].isoformat(), "thang_thap_nhat": data[lo]["date"].month})
    return out


# ---------- tự tương quan ----------
def centered_ma(vals, w):
    half = w // 2
    pref = [0.0]
    for v in vals:
        pref.append(pref[-1] + v)
    return [(pref[min(len(vals), i + half + 1)] - pref[max(0, i - half)]) / (min(len(vals), i + half + 1) - max(0, i - half))
            for i in range(len(vals))]


def autocorr_peaks(closes, min_lag=5):
    n = len(closes)
    logp = [math.log(c) for c in closes]
    w = max(21, min(n // 3, 121))
    if w % 2 == 0:
        w += 1
    trend = centered_ma(logp, w)
    x = [a - b for a, b in zip(logp, trend)]
    mu = sum(x) / n
    x = [v - mu for v in x]
    var = sum(v * v for v in x)
    if var == 0:
        return [], "Giá không biến động."
    max_lag = min(n // 3, w)
    acf = [0.0] * (max_lag + 2)
    for lag in range(1, max_lag + 2):
        acf[lag] = sum(x[i] * x[i + lag] for i in range(n - lag)) / var
    peaks = [{"chu_ky_phien": lag, "tu_tuong_quan": r(acf[lag], 3)}
             for lag in range(max(min_lag, 2), max_lag + 1)
             if acf[lag] > acf[lag - 1] and acf[lag] >= acf[lag + 1] and acf[lag] > 0.1]
    peaks.sort(key=lambda p: -p["tu_tuong_quan"])
    return peaks[:3], (f"Tính trên giá đã loại xu hướng (trung bình trượt {w} phiên), chỉ phát hiện chu kỳ ngắn hơn ~{max_lag} phiên. "
                       "Chu kỳ theo năm/mùa vụ: xem 'dinh_day_tung_nam' và 'theo_thang_qua_cac_nam'.")


# ---------- hiệu ứng lịch ----------
def calendar_effects(data):
    rets = [(data[i]["date"], data[i]["close"] / data[i - 1]["close"] - 1) for i in range(1, len(data))]

    def group(keyf, labels):
        buckets = {}
        for d, ret in rets:
            buckets.setdefault(keyf(d), []).append(ret)
        out = []
        for k in sorted(buckets):
            v = buckets[k]
            m = st.mean(v)
            sd = st.pstdev(v) if len(v) > 1 else 0
            t = m / (sd / math.sqrt(len(v))) if sd > 0 else None
            out.append({"nhom": labels[k], "so_phien": len(v), "loi_nhuan_tb_pct": r(m * 100, 3),
                        "ti_le_phien_tang_pct": r(sum(1 for x in v if x > 0) / len(v) * 100, 1),
                        "chi_so_t": r(t, 2), "co_y_nghia": bool(t is not None and abs(t) >= 2 and len(v) >= 20)})
        return out

    res = {"theo_thu": group(lambda d: d.weekday(), WEEKDAYS),
           "theo_tuan_trong_thang": group(lambda d: min((d.day - 1) // 7 + 1, 4),
                                          {1: "Ngày 1–7", 2: "Ngày 8–14", 3: "Ngày 15–21", 4: "Ngày 22–cuối"})}

    # lợi nhuận từng tháng của từng năm -> tháng nào tăng/giảm nhất quán qua các năm
    month_close = {}
    for d in data:
        month_close[(d["date"].year, d["date"].month)] = d["close"]
    keys = sorted(month_close)
    per_month = {}
    for a, b in zip(keys, keys[1:]):
        per_month.setdefault(b[1], []).append((b[0], (month_close[b] / month_close[a] - 1) * 100))
    if len({y for y, _ in keys}) >= 2:
        res["theo_thang_qua_cac_nam"] = [
            {"thang": m, "so_nam": len(v), "so_nam_tang": sum(1 for _, x in v if x > 0),
             "loi_nhuan_trung_vi_pct": r(median([x for _, x in v])),
             "tung_nam": {str(y): r(x) for y, x in v},
             "nhat_quan": len(v) >= 4 and (sum(1 for _, x in v if x > 0) / len(v) >= 0.8 or sum(1 for _, x in v if x > 0) / len(v) <= 0.2)}
            for m, v in sorted(per_month.items())]
    res["ghi_chu"] = ("'co_y_nghia' = |t| >= 2 và >= 20 phiên. 'nhat_quan' = tháng đó cùng chiều ở >= 80% số năm (cần >= 4 năm). "
                      "Ít năm dữ liệu thì khác biệt theo tháng rất dễ là ngẫu nhiên.")
    return res


def turning_clusters(pivots, data, window):
    counter = {"day": {}, "dinh": {}}
    for kind, i in pivots:
        d = data[i]["date"]
        a = (d.day - 1) // 7 * 7 + 1
        key = f"Ngày {a}–{min(a + 6, 31)}"
        counter[kind][key] = counter[kind].get(key, 0) + 1
    return {"day_theo_khoang_ngay": counter["day"], "dinh_theo_khoang_ngay": counter["dinh"],
            "goi_y": f"Coi sự kiện 'trùng' đỉnh/đáy nếu cách nhau trong ±{window} phiên."}


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path")
    ap.add_argument("--threshold", type=float, help="ngưỡng đảo chiều theo %% (mặc định tự tính)")
    ap.add_argument("--window", type=int, default=3)
    args = ap.parse_args()

    data = load_prices(args.csv_path, min_rows=60)
    closes = [d["close"] for d in data]
    rets = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    daily_sd = st.pstdev(rets)
    if args.threshold:
        th, th_note = args.threshold / 100, "do người dùng chọn"
    else:
        th = max(0.03, 2.5 * daily_sd * math.sqrt(5))
        th_note = "tự tính = max(3%, 2.5 × độ lệch chuẩn ngày × √5); thử ngưỡng khác nếu số đỉnh/đáy quá ít/nhiều"

    pivots, forming = zigzag(closes, th)

    def pv(kind, i, confirmed=True):
        d = data[i]["date"]
        return {"loai": "đỉnh" if kind == "dinh" else "đáy", "ngay": d.isoformat(), "gia": r(closes[i]),
                "thu": WEEKDAYS[d.weekday()], "ngay_trong_thang": d.day, "chi_so_phien": i, "da_xac_nhan": confirmed}

    troughs = [i for k, i in pivots if k == "day"]
    peaks = [i for k, i in pivots if k == "dinh"]
    cycles = sorted([(a, b - a) for a, b in zip(troughs, troughs[1:])] + [(a, b - a) for a, b in zip(peaks, peaks[1:])])
    phases = []
    for (k1, i1), (k2, i2) in zip(pivots, pivots[1:]):
        phases.append({"kind": "tang" if k1 == "day" else "giam", "start": i1, "len": i2 - i1,
                       "amp": (closes[i2] / closes[i1] - 1) * 100})

    full = stats([c[1] for c in cycles])
    cv = full["he_so_bien_thien"] if full else None
    cp = change_point(cycles, data)
    regime_start = cp["chi_so_phien_bat_dau"] if cp and cp["co_thay_doi"] else 0

    def phase_stats(kind, from_idx=0):
        ps = [p for p in phases if p["kind"] == kind and p["start"] >= from_idx]
        return {"do_dai_phien": stats([p["len"] for p in ps]), "bien_do_pct": stats([p["amp"] for p in ps])}

    # vị trí hiện tại & dự phóng
    last_i = len(closes) - 1
    current = projection = None
    if pivots:
        lk, li = pivots[-1]
        kind = "tang" if lk == "day" else "giam"
        elapsed = last_i - li
        current = {"pha_hien_tai": "tăng" if kind == "tang" else "giảm", "tu_diem_dao_chieu_gan_nhat": pv(lk, li),
                   "so_phien_da_qua": elapsed, "bien_do_tu_do_pct": r((closes[-1] / closes[li] - 1) * 100)}
        if forming:
            current["diem_dang_hinh_thanh"] = pv(forming[0], forming[1], confirmed=False)

        same = [p for p in phases if p["kind"] == kind and p["start"] >= regime_start]
        basis = f"giai đoạn mới từ {data[regime_start]['date'].isoformat()}" if regime_start else "toàn bộ dữ liệu"
        if len(same) < 3:  # giai đoạn mới quá ngắn -> dùng 6 pha gần nhất
            same = [p for p in phases if p["kind"] == kind][-6:]
            basis = "6 pha cùng loại gần nhất (giai đoạn mới chưa đủ mẫu)"
        if len(same) >= 2:
            lens = [p["len"] for p in same]
            amps = [p["amp"] for p in same]
            lo, hi = percentile(lens, 25), percentile(lens, 75)
            rlo, rhi = max(0, lo - elapsed), max(0, hi - elapsed)
            current["ty_le_pha_da_qua_pct"] = r(elapsed / median(lens) * 100, 0) if median(lens) else None
            projection = {
                "co_so_du_phong": basis,
                "diem_dao_chieu_tiep_theo": "đỉnh" if kind == "tang" else "đáy",
                "cua_so_phien_tu_hom_nay": [r(rlo, 0), r(rhi, 0)],
                "cua_so_ngay_uoc_tinh": [add_business_days(data[-1]["date"], rlo).isoformat(),
                                         add_business_days(data[-1]["date"], rhi).isoformat()],
                "bien_do_pha_dien_hinh_pct": [r(percentile(amps, 25)), r(median(amps)), r(percentile(amps, 75))],
                "dang_trong_cua_so_dao_chieu": lo <= elapsed <= hi,
                "da_qua_do_dai_dien_hinh": elapsed > hi,
                "ghi_chu": ("Cửa sổ = tứ phân vị 25%–75% độ dài các pha cùng loại (theo 'co_so_du_phong'). "
                            "Ngày ước tính chỉ bỏ cuối tuần, chưa trừ ngày lễ. "
                            "'da_qua_do_dai_dien_hinh' = true nghĩa là pha này dài bất thường: chu kỳ có thể đang thay đổi."),
            }

    span_years = (data[-1]["date"] - data[0]["date"]).days / 365.25
    warnings = [
        "Chu kỳ quá khứ không bảo đảm lặp lại; chu kỳ càng rõ thì càng dễ bị thị trường 'đi trước' làm méo.",
        "Dữ liệu chưa điều chỉnh cổ tức/chia tách tạo đáy giả ở ngày GDKHQ – kiểm tra trước khi diễn giải.",
    ]
    if len(cycles) < 10:  # cycles gồm cả đáy->đáy và đỉnh->đỉnh, ~2 mẫu mỗi vòng
        warnings.append(f"Chỉ có khoảng {len(cycles) // 2} chu kỳ hoàn chỉnh: thống kê kém tin cậy, nên lấy dữ liệu dài hơn.")
    if span_years < 2:
        warnings.append(f"Dữ liệu chỉ ~{span_years:.1f} năm: chưa so sánh được giữa các năm.")

    out = {
        "so_phien": len(data), "tu_ngay": data[0]["date"].isoformat(), "den_ngay": data[-1]["date"].isoformat(),
        "so_nam_du_lieu": r(span_years, 1),
        "nguong_dao_chieu_pct": r(th * 100), "cach_chon_nguong": th_note,
        "dinh_day": [pv(k, i) for k, i in pivots],
        "do_dai_chu_ky_phien": {"toan_bo": full, "muc_do_deu": regularity_label(cv)},
        "thay_doi_chu_ky": cp,
        "xu_huong_do_dai_chu_ky": length_trend(cycles, data),
        "theo_tung_nam": by_year(pivots, phases, cycles, data),
        "pha_tang": phase_stats("tang", regime_start),
        "pha_giam": phase_stats("giam", regime_start),
        "ghi_chu_pha": ("Thống kê pha tính từ " + data[regime_start]["date"].isoformat()) if regime_start else "Thống kê pha trên toàn bộ dữ liệu",
        "chu_ky_troi_theo_tu_tuong_quan": None, "ghi_chu_tu_tuong_quan": None,
        "vi_tri_hien_tai": current,
        "du_phong": projection,
        "dinh_day_tung_nam": yearly_extremes(data),
        "hieu_ung_lich": calendar_effects(data),
        "phan_bo_dao_chieu_theo_lich": turning_clusters(pivots, data, args.window),
        "canh_bao": warnings,
    }
    out["chu_ky_troi_theo_tu_tuong_quan"], out["ghi_chu_tu_tuong_quan"] = autocorr_peaks(closes)
    if regime_start:
        out["do_dai_chu_ky_phien"]["muc_do_deu"] += " (gộp hai giai đoạn – xem 'thay_doi_chu_ky' và 'theo_tung_nam')"
        out["do_dai_chu_ky_phien"]["giai_doan_moi"] = stats([c[1] for c in cycles if c[0] >= regime_start])
        out["ghi_chu_tu_tuong_quan"] += " Chu kỳ đã thay đổi nên số gộp toàn bộ dễ gây nhầm; ưu tiên 'chu_ky_troi_giai_doan_moi'."
        out["chu_ky_troi_giai_doan_moi"] = autocorr_peaks(closes[regime_start:])[0] if last_i - regime_start >= 60 else None
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
