#!/usr/bin/env python3
"""Tính chỉ báo kỹ thuật từ file CSV giá cổ phiếu.

Cách dùng:
    python indicators.py gia.csv            # in JSON ra màn hình
    python indicators.py gia.csv --pretty   # JSON thụt lề, dễ đọc

CSV cần các cột (không phân biệt hoa thường): date, open, high, low, close, volume.
Cột volume có thể thiếu; khi đó các phần liên quan đến khối lượng bị bỏ qua.
Dữ liệu có thể xếp cũ -> mới hoặc mới -> cũ, script tự sắp xếp theo ngày.
Cần ít nhất ~30 phiên để các chỉ báo có ý nghĩa; 200+ phiên để có SMA200.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_prices  # noqa: E402


def load(path):
    data = load_prices(path, min_rows=15)
    for d in data:
        d["date"] = d["date"].isoformat()
    return data


def sma(vals, n):
    if len(vals) < n:
        return None
    return sum(vals[-n:]) / n


def ema_series(vals, n):
    k = 2 / (n + 1)
    out = [vals[0]]
    for v in vals[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def rsi(closes, n=14):
    if len(closes) <= n:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_g = sum(gains[:n]) / n
    avg_l = sum(losses[:n]) / n
    for i in range(n, len(gains)):
        avg_g = (avg_g * (n - 1) + gains[i]) / n
        avg_l = (avg_l * (n - 1) + losses[i]) / n
    if avg_l == 0:
        return 100.0
    return 100 - 100 / (1 + avg_g / avg_l)


def macd(closes, fast=12, slow=26, signal=9):
    if len(closes) < slow + signal:
        return None
    ef, es = ema_series(closes, fast), ema_series(closes, slow)
    line = [a - b for a, b in zip(ef, es)]
    sig = ema_series(line, signal)
    hist = [a - b for a, b in zip(line, sig)]
    return {"macd": line[-1], "signal": sig[-1], "histogram": hist[-1],
            "histogram_prev": hist[-2], "macd_prev": line[-2], "signal_prev": sig[-2]}


def bollinger(closes, n=20, k=2):
    if len(closes) < n:
        return None
    w = closes[-n:]
    m = sum(w) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in w) / n)
    upper, lower = m + k * sd, m - k * sd
    last = closes[-1]
    pct_b = (last - lower) / (upper - lower) if upper != lower else None
    return {"middle": m, "upper": upper, "lower": lower,
            "percent_b": pct_b, "bandwidth_pct": (upper - lower) / m * 100}


def atr(data, n=14):
    if len(data) <= n:
        return None
    trs = []
    for i in range(1, len(data)):
        h, l, pc = data[i]["high"], data[i]["low"], data[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    a = sum(trs[:n]) / n
    for t in trs[n:]:
        a = (a * (n - 1) + t) / n
    return a


def support_resistance(data, window=5, lookback=120, tol=0.015):
    """Tìm đỉnh/đáy cục bộ trong `lookback` phiên gần nhất, gom các mốc gần nhau (trong tol%)
    thành vùng; vùng có nhiều lần chạm hơn thì mạnh hơn."""
    seg = data[-lookback:]
    pivots_hi, pivots_lo = [], []
    for i in range(window, len(seg) - window):
        hi = seg[i]["high"]
        lo = seg[i]["low"]
        if all(hi >= seg[j]["high"] for j in range(i - window, i + window + 1)):
            pivots_hi.append(hi)
        if all(lo <= seg[j]["low"] for j in range(i - window, i + window + 1)):
            pivots_lo.append(lo)

    def cluster(levels):
        levels = sorted(levels)
        groups = []
        for lv in levels:
            if groups and abs(lv - groups[-1][-1]) / groups[-1][-1] <= tol:
                groups[-1].append(lv)
            else:
                groups.append([lv])
        return [{"level": sum(g) / len(g), "touches": len(g)} for g in groups]

    price = data[-1]["close"]
    zones = cluster(pivots_hi + pivots_lo)
    supports = sorted([z for z in zones if z["level"] < price], key=lambda z: -z["level"])[:3]
    resistances = sorted([z for z in zones if z["level"] > price], key=lambda z: z["level"])[:3]
    return {"supports_nearest_first": supports, "resistances_nearest_first": resistances,
            "recent_high": max(d["high"] for d in seg), "recent_low": min(d["low"] for d in seg)}


def volume_info(data):
    vols = [d["volume"] for d in data if d["volume"] is not None]
    if len(vols) < 20 or data[-1]["volume"] is None:
        return None
    avg20 = sum(vols[-20:]) / 20
    return {"last": data[-1]["volume"], "avg20": avg20,
            "ratio_vs_avg20": data[-1]["volume"] / avg20 if avg20 else None}


def r(x, nd=2):
    if x is None:
        return None
    return round(x, nd)


def candle_info(data):
    """Mô tả nến phiên cuối bằng tỷ lệ thân/bóng. Chỉ mang tính mô tả, độ tin cậy dự báo của từng mẫu nến thấp."""
    d = data[-1]
    rng = d["high"] - d["low"]
    if rng <= 0:
        return {"mo_ta": "nến phẳng (không biên độ)"}
    body = abs(d["close"] - d["open"])
    up_sh = d["high"] - max(d["open"], d["close"])
    lo_sh = min(d["open"], d["close"]) - d["low"]
    kind = "tăng" if d["close"] > d["open"] else "giảm" if d["close"] < d["open"] else "đứng"
    notes = []
    if body / rng < 0.1:
        notes.append("thân rất nhỏ (do dự)")
    if lo_sh / rng > 0.55 and body / rng < 0.35:
        notes.append("bóng dưới dài (có lực đỡ giá trong phiên)")
    if up_sh / rng > 0.55 and body / rng < 0.35:
        notes.append("bóng trên dài (bị bán ra khi lên cao)")
    if len(data) >= 2:
        p = data[-2]
        if (d["close"] > d["open"] and p["close"] < p["open"] and d["close"] >= p["open"] and d["open"] <= p["close"]):
            notes.append("nến tăng bao trùm thân nến giảm trước")
        if (d["close"] < d["open"] and p["close"] > p["open"] and d["open"] >= p["close"] and d["close"] <= p["open"]):
            notes.append("nến giảm bao trùm thân nến tăng trước")
    return {"loai": kind, "than_pct_bien_do": r(body / rng * 100, 0), "bong_tren_pct_bien_do": r(up_sh / rng * 100, 0),
            "bong_duoi_pct_bien_do": r(lo_sh / rng * 100, 0), "ghi_chu": notes,
            "luu_y": "mẫu nến chỉ để mô tả; không dùng riêng lẻ để dự báo"}


def streak_info(closes):
    n = 0
    sign = 0
    for i in range(len(closes) - 1, 0, -1):
        d = closes[i] - closes[i - 1]
        sg = 1 if d > 0 else -1 if d < 0 else 0
        if sg == 0 or (sign != 0 and sg != sign):
            break
        sign = sg
        n += 1
    return {"huong": "tăng" if sign > 0 else "giảm" if sign < 0 else "đứng", "so_phien_lien_tiep": n}


def gap_info(data, look=5):
    """Khoảng trống giá (mở cửa vượt khỏi vùng giá phiên trước) trong `look` phiên gần nhất."""
    out = []
    for i in range(max(1, len(data) - look), len(data)):
        p, d = data[i - 1], data[i]
        if d["low"] > p["high"]:
            out.append({"ngay": d["date"], "loai": "gap tăng", "tu": r(p["high"]), "den": r(d["low"])})
        elif d["high"] < p["low"]:
            out.append({"ngay": d["date"], "loai": "gap giảm", "tu": r(p["low"]), "den": r(d["high"])})
    return out


def bollinger_squeeze(closes, n=20, look=120):
    """Độ rộng dải Bollinger hiện tại nằm ở phân vị nào trong `look` phiên (thấp = giá đang nén, thường đi trước biến động lớn)."""
    if len(closes) < n + 30:
        return None
    widths = []
    for i in range(n - 1, len(closes)):
        w = closes[i - n + 1:i + 1]
        m = sum(w) / n
        sd = math.sqrt(sum((x - m) ** 2 for x in w) / n)
        widths.append(4 * sd / m)
    hist = widths[-look:]
    cur = widths[-1]
    pct = sum(1 for x in hist if x <= cur) / len(hist) * 100
    return {"do_rong_hien_tai_pct": r(cur * 100), "phan_vi_trong_lich_su_pct": r(pct, 0),
            "nhan": "nén chặt (độ rộng thấp nhất 20% lịch sử gần)" if pct <= 20 else
                    "giãn rộng (cao nhất 20%)" if pct >= 80 else "bình thường",
            "luu_y": "nén chặt cho biết biến động lớn có thể sắp tới, không cho biết hướng"}


def rsi_divergence(closes, look=30, n=14):
    """So sánh hai đáy/đỉnh gần nhất trong `look` phiên: giá tạo đáy thấp hơn nhưng RSI tạo đáy cao hơn (phân kỳ dương), và ngược lại."""
    if len(closes) < look + n + 5:
        return None
    rs = []
    for end in range(len(closes) - look, len(closes) + 1):
        rs.append(rsi(closes[:end], n))
    seg = closes[-look:]
    r_seg = rs[-look:] if len(rs) >= look else None
    if not r_seg or any(v is None for v in r_seg):
        return None
    w = 3

    def pivots(kind):
        idx = []
        for i in range(w, look - w):
            win = seg[i - w:i + w + 1]
            if (kind == "lo" and seg[i] == min(win)) or (kind == "hi" and seg[i] == max(win)):
                idx.append(i)
        return idx[-2:]

    out = {"phan_ky": None}
    lows, highs = pivots("lo"), pivots("hi")
    if len(lows) == 2 and seg[lows[1]] < seg[lows[0]] and r_seg[lows[1]] > r_seg[lows[0]]:
        out["phan_ky"] = "dương: giá tạo đáy thấp hơn nhưng RSI tạo đáy cao hơn (đà giảm yếu dần)"
    elif len(highs) == 2 and seg[highs[1]] > seg[highs[0]] and r_seg[highs[1]] < r_seg[highs[0]]:
        out["phan_ky"] = "âm: giá tạo đỉnh cao hơn nhưng RSI tạo đỉnh thấp hơn (đà tăng yếu dần)"
    out["luu_y"] = "phân kỳ thường báo sớm và hay sai nếu xu hướng mạnh; cần chờ giá xác nhận"
    return out


def volume_price(data):
    """Quan hệ khối lượng và giá của 5 phiên gần nhất so với trung bình 20 phiên."""
    vols = [d["volume"] for d in data if d["volume"] is not None]
    if len(vols) < 25:
        return None
    avg20 = sum(vols[-25:-5]) / 20
    rows = []
    for d, pd in zip(data[-5:], data[-6:-1]):
        if d["volume"] is None or avg20 <= 0:
            continue
        rows.append({"ngay": d["date"], "thay_doi_pct": r((d["close"] / pd["close"] - 1) * 100),
                     "khoi_luong_so_voi_tb20": r(d["volume"] / avg20)})
    heavy_down = [x for x in rows if x["thay_doi_pct"] < 0 and x["khoi_luong_so_voi_tb20"] >= 1.5]
    heavy_up = [x for x in rows if x["thay_doi_pct"] > 0 and x["khoi_luong_so_voi_tb20"] >= 1.5]
    note = []
    if heavy_down:
        note.append("có phiên giảm kèm khối lượng lớn (áp lực bán rõ)")
    if heavy_up:
        note.append("có phiên tăng kèm khối lượng lớn (lực mua rõ)")
    return {"5_phien": rows, "nhan_xet": note or ["không có phiên nào khối lượng vượt 1,5 lần trung bình"]}


def trend_summary(close, s20, s50, s200):
    notes = []
    if s20 and s50:
        notes.append("SMA20 trên SMA50 (động lượng ngắn hạn tốt hơn trung hạn)" if s20 > s50
                     else "SMA20 dưới SMA50 (động lượng ngắn hạn yếu hơn trung hạn)")
    if s50 and s200:
        notes.append("SMA50 trên SMA200 (cấu trúc dài hạn tăng)" if s50 > s200
                     else "SMA50 dưới SMA200 (cấu trúc dài hạn giảm)")
    for name, v in (("SMA20", s20), ("SMA50", s50), ("SMA200", s200)):
        if v:
            notes.append(f"Giá {'trên' if close > v else 'dưới'} {name}")
    return notes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path")
    ap.add_argument("--pretty", action="store_true", help="in JSON thụt lề")
    args = ap.parse_args()

    data = load(args.csv_path)
    closes = [d["close"] for d in data]
    last = data[-1]
    prev = data[-2]

    s20, s50, s200 = sma(closes, 20), sma(closes, 50), sma(closes, 200)
    e12 = ema_series(closes, 12)[-1]
    e26 = ema_series(closes, 26)[-1]
    rs = rsi(closes)
    mc = macd(closes)
    bb = bollinger(closes)
    a = atr(data)
    sr = support_resistance(data)
    vol = volume_info(data)

    out = {
        "so_phien": len(data),
        "ngay_cuoi": last["date"],
        "gia_dong_cua": r(last["close"]),
        "thay_doi_phien_cuoi_pct": r((last["close"] / prev["close"] - 1) * 100),
        "thay_doi_5_phien_pct": r((closes[-1] / closes[-6] - 1) * 100) if len(closes) > 5 else None,
        "thay_doi_20_phien_pct": r((closes[-1] / closes[-21] - 1) * 100) if len(closes) > 20 else None,
        "sma": {"sma20": r(s20), "sma50": r(s50), "sma200": r(s200)},
        "ema": {"ema12": r(e12), "ema26": r(e26)},
        "xu_huong": trend_summary(last["close"], s20, s50, s200),
        "rsi14": r(rs),
        "rsi_nhan": None if rs is None else ("quá mua (>70)" if rs > 70 else "quá bán (<30)" if rs < 30 else "trung tính (30-70)"),
        "macd": None if mc is None else {
            "macd": r(mc["macd"], 4), "signal": r(mc["signal"], 4), "histogram": r(mc["histogram"], 4),
            "tin_hieu": ("MACD vừa cắt lên signal" if mc["macd_prev"] <= mc["signal_prev"] and mc["macd"] > mc["signal"]
                         else "MACD vừa cắt xuống signal" if mc["macd_prev"] >= mc["signal_prev"] and mc["macd"] < mc["signal"]
                         else "MACD trên signal" if mc["macd"] > mc["signal"] else "MACD dưới signal"),
            "histogram_dang": "mở rộng" if abs(mc["histogram"]) > abs(mc["histogram_prev"]) else "thu hẹp",
        },
        "bollinger20": None if bb is None else {k: r(v, 3) for k, v in bb.items()},
        "atr14": r(a),
        "atr14_pct_gia": r(a / last["close"] * 100) if a else None,
        "khoi_luong": None if vol is None else {k: r(v, 2) for k, v in vol.items()},
        "ho_tro_khang_cu": {
            "ho_tro_gan_nhat": [{"muc": r(z["level"]), "so_lan_cham": z["touches"]} for z in sr["supports_nearest_first"]],
            "khang_cu_gan_nhat": [{"muc": r(z["level"]), "so_lan_cham": z["touches"]} for z in sr["resistances_nearest_first"]],
            "dinh_gan_day": r(sr["recent_high"]),
            "day_gan_day": r(sr["recent_low"]),
        },
        "doc_bieu_do": {
            "nen_phien_cuoi": candle_info(data),
            "chuoi_phien": streak_info(closes),
            "gap_5_phien": gap_info(data),
            "nen_bollinger": bollinger_squeeze(closes),
            "phan_ky_rsi": rsi_divergence(closes),
            "khoi_luong_va_gia": volume_price(data),
        },
        "ghi_chu": "Chỉ báo tính từ dữ liệu quá khứ; không đảm bảo kết quả tương lai. "
                   "Hỗ trợ/kháng cự là vùng ước lượng từ đỉnh/đáy cục bộ, cần đối chiếu với biểu đồ.",
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    print()


if __name__ == "__main__":
    main()
