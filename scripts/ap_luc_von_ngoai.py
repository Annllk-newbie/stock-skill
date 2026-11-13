#!/usr/bin/env python3
"""Điểm ÁP LỰC BÁN của khối ngoại trên TOÀN THỊ TRƯỜNG Việt Nam (không theo từng mã).

Đọc file chuỗi số liệu tích lũy hằng ngày (von-ngoai.csv), chấm từng chỉ báo nền tảng,
cộng thành điểm 0–100 và (khi đủ dữ liệu) kiểm chứng chỉ báo nào thực sự đi trước khối ngoại bán ròng.

Cách dùng:
    python ap_luc_von_ngoai.py von-ngoai.csv                # in JSON
    python ap_luc_von_ngoai.py von-ngoai.csv --chu          # in bản chữ cho báo cáo

Cột của von-ngoai.csv (ô trống = không lấy được; KHÔNG điền đoán):
    date                    yyyy-mm-dd (ngày giao dịch ở Việt Nam)
    kn_rong_hose_ty         khối ngoại mua(+)/bán(−) ròng khớp lệnh + thỏa thuận trên HOSE, tỷ đồng
    kn_ghi_chu_giao_dich_lon  giao dịch lớn đơn lẻ làm méo số (vd "ACB -469 thỏa thuận"); để trống nếu không có
    dxy                     chỉ số USD (đóng cửa phiên Mỹ đêm trước)
    ust10y, ust2y           lợi suất trái phiếu Mỹ 10 năm, 2 năm (%)
    fed_xs_tang             xác suất thị trường định giá Fed TĂNG ở kỳ họp kế tiếp (%); nếu thị trường định giá GIẢM thì ghi số âm
    usd_vnd_trung_tam       tỷ giá trung tâm NHNN
    usd_vnd_nh_ban          giá bán USD của Vietcombank
    usd_vnd_tu_do_ban       giá bán USD tự do
    lien_nh_qua_dem         lãi suất VND liên ngân hàng qua đêm (%)
    omo_rong_ty             NHNN bơm(+)/hút(−) ròng qua OMO và tín phiếu trong ngày, tỷ đồng
    etf_tuan_ty             tổng dòng tiền các ETF vào cổ phiếu Việt Nam trong TUẦN (tỷ đồng, + vào / − rút); ghi ở ngày công bố
    khu_vuc_tuan_trieu_usd  khối ngoại ròng tuần ở châu Á mới nổi (MIDF/Reuters: Hàn, Đài, Ấn, Thái, Indo, Phi, Malay), triệu USD; ghi ở ngày công bố
    brent                   giá dầu Brent (USD/thùng)
    nguon                   ghi chú nguồn ngắn

Điểm là quy tắc theo lý thuyết (xem RULES) cho tới khi phần kiểm chứng có đủ ≥40 phiên.
Không phải khuyến nghị mua/bán.
"""
import argparse
import csv
import datetime as dt
import json
import math
import sys

COLS = ["kn_rong_hose_ty", "dxy", "ust10y", "ust2y", "fed_xs_tang", "usd_vnd_trung_tam", "usd_vnd_nh_ban",
        "usd_vnd_tu_do_ban", "lien_nh_qua_dem", "omo_rong_ty", "etf_tuan_ty", "khu_vuc_tuan_trieu_usd", "brent"]


def num(v):
    v = (v or "").strip().replace(",", "")
    if v in ("", "-", "null", "None", "NA"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def load(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        try:
            d = dt.date.fromisoformat(r["date"].strip())
        except (KeyError, ValueError):
            continue
        rec = {"date": d, "ghi_chu": (r.get("kn_ghi_chu_giao_dich_lon") or "").strip(), "nguon": (r.get("nguon") or "").strip()}
        for c in COLS:
            rec[c] = num(r.get(c))
        out.append(rec)
    out.sort(key=lambda x: x["date"])
    # gộp trùng ngày: giữ giá trị không trống mới nhất
    merged = {}
    for r in out:
        m = merged.setdefault(r["date"], {"date": r["date"], "ghi_chu": "", "nguon": ""})
        for k, v in r.items():
            if k == "date":
                continue
            if v not in (None, ""):
                m[k] = v
    res = [merged[k] for k in sorted(merged)]
    for r in res:
        for c in COLS:
            r.setdefault(c, None)
    return res


def last_val(rows, col, before_idx=None, max_age_days=10):
    """giá trị gần nhất (không trống) của cột, tính tới hàng before_idx; bỏ nếu quá cũ."""
    end = len(rows) - 1 if before_idx is None else before_idx
    ref = rows[end]["date"]
    for i in range(end, -1, -1):
        v = rows[i][col]
        if v is not None:
            if (ref - rows[i]["date"]).days > max_age_days:
                return None, None
            return v, rows[i]["date"]
    return None, None


def val_n_ago(rows, col, n_days, end=None):
    """giá trị gần nhất cách ngày cuối khoảng n_days ngày lịch (±4 ngày)."""
    end = len(rows) - 1 if end is None else end
    target = rows[end]["date"] - dt.timedelta(days=n_days)
    best = None
    for i in range(end, -1, -1):
        r = rows[i]
        if r[col] is None:
            continue
        if r["date"] <= target + dt.timedelta(days=4):
            if abs((r["date"] - target).days) <= 6:
                best = (r[col], r["date"])
            break
    return best if best else (None, None)


def clamp(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


def fmt(x, nd=2):
    if x is None:
        return "không có"
    return f"{x:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# (tên, trọng số, hàm(rows, end) -> (điểm -1..+1 hoặc None, mô tả))
def r_dxy(rows, e):
    a, da = last_val(rows, "dxy", e)
    b, _ = val_n_ago(rows, "dxy", 28, e)
    if a is None or b is None:
        return None, "DXY: chưa đủ số (cần số hiện tại và ~4 tuần trước)"
    ch = (a / b - 1) * 100
    return clamp(ch / 2.0), f"DXY {fmt(a)} ({'+' if ch >= 0 else ''}{fmt(ch, 1)}% trong ~4 tuần): USD mạnh lên → tiền rút khỏi thị trường mới nổi" if ch > 0 else f"DXY {fmt(a)} ({fmt(ch, 1)}% trong ~4 tuần): USD yếu đi → giảm áp lực"


def r_ust(rows, e):
    a, _ = last_val(rows, "ust10y", e)
    b, _ = val_n_ago(rows, "ust10y", 28, e)
    if a is None:
        return None, "Lợi suất Mỹ 10 năm: không có số"
    level = clamp((a - 4.25) / 1.0)          # trên ~4,25% bắt đầu là áp lực, ~5,25% là tối đa
    if b is None:
        return level * 0.7, f"Lợi suất Mỹ 10 năm {fmt(a, 3)}% (chưa có số 4 tuần trước để đo xu hướng)"
    chg_bp = (a - b) * 100
    sc = clamp(0.6 * level + 0.4 * clamp(chg_bp / 30))
    return sc, f"Lợi suất Mỹ 10 năm {fmt(a, 3)}% ({'+' if chg_bp >= 0 else ''}{fmt(chg_bp, 0)} điểm cơ bản trong ~4 tuần)"


def r_fed(rows, e):
    a, d = last_val(rows, "fed_xs_tang", e, max_age_days=21)
    if a is None:
        return None, "Kỳ vọng Fed: không có số"
    sc = clamp(a / 80.0)
    if a >= 0:
        return sc, f"Thị trường định giá {fmt(a, 0)}% khả năng Fed TĂNG lãi suất kỳ họp tới → USD và lợi suất Mỹ có lực đỡ"
    return sc, f"Thị trường định giá {fmt(-a, 0)}% khả năng Fed GIẢM lãi suất → hỗ trợ dòng vốn vào thị trường mới nổi"


def r_fx_gap(rows, e):
    tf, _ = last_val(rows, "usd_vnd_tu_do_ban", e)
    nh, _ = last_val(rows, "usd_vnd_nh_ban", e)
    if tf is None or nh is None:
        return None, "Chênh USD tự do – ngân hàng: thiếu số"
    gap = tf - nh
    sc = clamp((gap - 150) / 350)             # dưới ~150 đồng là bình thường, ~500 là căng
    return sc, f"USD tự do bán {fmt(tf, 0)} so với Vietcombank {fmt(nh, 0)}: chênh {fmt(gap, 0)} đồng → " + \
        ("thị trường kỳ vọng VND yếu đi" if gap > 250 else "chưa căng")


def r_fx_trend(rows, e):
    a, _ = last_val(rows, "usd_vnd_nh_ban", e)
    b, _ = val_n_ago(rows, "usd_vnd_nh_ban", 28, e)
    if a is None or b is None:
        return None, "Xu hướng tỷ giá ngân hàng: chưa đủ số"
    ch = (a / b - 1) * 100
    return clamp(ch / 0.8), f"Giá bán USD ngân hàng {'+' if ch >= 0 else ''}{fmt(ch, 2)}% trong ~4 tuần (VND {'mất giá' if ch > 0 else 'lên giá'})"


def r_liquidity(rows, e):
    a, _ = last_val(rows, "lien_nh_qua_dem", e)
    omo = [rows[i]["omo_rong_ty"] for i in range(max(0, e - 4), e + 1) if rows[i]["omo_rong_ty"] is not None]
    if a is None and not omo:
        return None, "Thanh khoản VND: không có số"
    sc = 0.0
    parts = []
    if a is not None:
        sc += clamp((a - 4.0) / 2.0) * 0.6
        parts.append(f"lãi suất qua đêm {fmt(a, 2)}%")
    if omo:
        s = sum(omo)
        sc += clamp(-s / 20000) * 0.4
        parts.append(f"NHNN {'hút' if s < 0 else 'bơm'} ròng {fmt(abs(s), 0)} tỷ trong {len(omo)} phiên gần nhất")
    return clamp(sc), "Thanh khoản VND: " + ", ".join(parts) + " (hút ròng/lãi suất cao = NHNN giữ tỷ giá, tiền trong nước căng hơn)"


def r_etf(rows, e):
    a, d = last_val(rows, "etf_tuan_ty", e, max_age_days=14)
    if a is None:
        return None, "Dòng tiền ETF tuần: không có số"
    return clamp(-a / 1500), f"ETF tuần gần nhất ({d.strftime('%d/%m')}): {'rút' if a < 0 else 'nạp'} ròng {fmt(abs(a), 0)} tỷ đồng"


def r_region(rows, e):
    a, d = last_val(rows, "khu_vuc_tuan_trieu_usd", e, max_age_days=14)
    if a is None:
        return None, "Khối ngoại châu Á mới nổi: không có số"
    return clamp(-a / 3000), f"Khối ngoại châu Á mới nổi tuần gần nhất ({d.strftime('%d/%m')}): {'bán' if a < 0 else 'mua'} ròng {fmt(abs(a), 0)} triệu USD → " + \
        ("rút vốn diện rộng, không riêng Việt Nam" if a < 0 else "khu vực đang hút vốn")


def r_momentum(rows, e):
    vals = [(rows[i]["kn_rong_hose_ty"], rows[i]["ghi_chu"]) for i in range(max(0, e - 9), e + 1) if rows[i]["kn_rong_hose_ty"] is not None]
    if len(vals) < 3:
        return None, "Đà khối ngoại: chưa đủ 3 phiên"
    s5 = sum(v for v, _ in vals[-5:])
    s10 = sum(v for v, _ in vals)
    neg = sum(1 for v, _ in vals[-5:] if v < 0)
    big = [g for _, g in vals[-5:] if g]
    sc = clamp(-s5 / 4000) * 0.7 + clamp((neg - 2.5) / 2.5) * 0.3
    txt = f"Khối ngoại HOSE: {fmt(s5, 0)} tỷ trong {min(5, len(vals))} phiên có số gần nhất ({neg} phiên bán ròng)"
    if len(vals) > 5:
        txt += f", {fmt(s10, 0)} tỷ trong {len(vals)} phiên"
    if big:
        txt += f"; có giao dịch lớn đơn lẻ: {'; '.join(big)} (làm méo số, không phải bán tháo diện rộng)"
        sc *= 0.7
    return clamp(sc), txt


RULES = [
    ("Đồng USD (DXY)", 0.14, r_dxy, "dxy"),
    ("Lợi suất Mỹ", 0.14, r_ust, "ust10y"),
    ("Kỳ vọng Fed", 0.10, r_fed, "fed_xs_tang"),
    ("Chênh tỷ giá tự do – ngân hàng", 0.14, r_fx_gap, "usd_vnd_tu_do_ban"),
    ("Xu hướng tỷ giá ngân hàng", 0.10, r_fx_trend, "usd_vnd_nh_ban"),
    ("Thanh khoản VND", 0.08, r_liquidity, "lien_nh_qua_dem"),
    ("Dòng tiền ETF", 0.12, r_etf, "etf_tuan_ty"),
    ("Khối ngoại châu Á", 0.10, r_region, "khu_vuc_tuan_trieu_usd"),
    ("Đà bán của chính khối ngoại", 0.08, r_momentum, "kn_rong_hose_ty"),
]


def score_at(rows, e):
    items, tot, wsum = [], 0.0, 0.0
    for name, w, fn, _ in RULES:
        sc, txt = fn(rows, e)
        items.append({"chi_bao": name, "trong_so": w, "diem": None if sc is None else round(sc, 2), "mo_ta": txt})
        if sc is not None:
            tot += w * sc
            wsum += w
    if wsum == 0:
        return None, items, 0
    s = 50 + 50 * tot / wsum
    return round(s), items, round(wsum / sum(w for _, w, _, _ in RULES) * 100)


def level(s):
    if s is None:
        return "chưa tính được"
    if s >= 65:
        return "CAO"
    if s >= 45:
        return "VỪA"
    return "THẤP"


def corr(x, y):
    n = len(x)
    if n < 8:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    if sx == 0 or sy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def verify(rows, horizon=5, min_rows=40):
    """Điểm từng chỉ báo hôm nay có đi trước tổng khối ngoại ròng N phiên SAU đó không (tương quan âm = đúng hướng)."""
    kn = [r["kn_rong_hose_ty"] for r in rows]
    if sum(1 for v in kn if v is not None) < min_rows:
        return {"trang_thai": f"Chưa đủ dữ liệu: cần ≥{min_rows} phiên có số khối ngoại, hiện có {sum(1 for v in kn if v is not None)}. "
                              "Điểm hiện tại là quy tắc theo lý thuyết, chưa được kiểm chứng."}
    out = {"trang_thai": "ok", "chan_troi_phien": horizon, "chi_bao": []}
    fut = []
    for e in range(len(rows) - horizon):
        nxt = [kn[j] for j in range(e + 1, e + 1 + horizon) if kn[j] is not None]
        fut.append(sum(nxt) if len(nxt) >= horizon - 1 else None)
    tot_x, tot_y = [], []
    for name, w, fn, _ in RULES:
        xs, ys = [], []
        for e in range(len(fut)):
            if fut[e] is None:
                continue
            sc, _ = fn(rows, e)
            if sc is not None:
                xs.append(sc)
                ys.append(fut[e])
        c = corr(xs, ys)
        out["chi_bao"].append({"chi_bao": name, "so_diem": len(xs), "tuong_quan": None if c is None else round(c, 2),
                               "nhan_xet": "chưa đủ điểm" if c is None else
                               ("đi trước khá rõ (điểm cao → sau đó bán ròng)" if c <= -0.3 else
                                "có tín hiệu yếu" if c <= -0.1 else
                                "không thấy tác dụng" if c < 0.1 else "ngược chiều lý thuyết, cần xem lại")})
    for e in range(len(fut)):
        if fut[e] is None:
            continue
        s, _, _ = score_at(rows, e)
        if s is not None:
            tot_x.append(s)
            tot_y.append(fut[e])
    c = corr(tot_x, tot_y)
    out["diem_tong"] = {"so_diem": len(tot_x), "tuong_quan": None if c is None else round(c, 2)}
    return out


def text(res):
    L = [f"Áp lực bán của khối ngoại (toàn thị trường), ngày {res['ngay']}: {res['diem'] if res['diem'] is not None else '—'}/100 – {res['muc']}"
         f" (dựa trên {res['do_phu_pct']}% trọng số có dữ liệu)"]
    if res["do_phu_pct"] < 60:
        L.append("  ⚠ Độ tin cậy thấp: thiếu nhiều chỉ báo, điểm có thể lệch nhiều khi bổ sung số.")
    if res.get("thay_doi"):
        L.append(f"  So với {res['thay_doi']['ngay']}: {res['thay_doi']['diem']}/100")
    keys = sorted([i for i in res["chi_bao"] if i["diem"] is not None], key=lambda i: -i["diem"] * i["trong_so"])
    L.append("  Đang đẩy áp lực LÊN:")
    up = [i for i in keys if i["diem"] > 0.15]
    L += [f"   - {i['mo_ta']}" for i in up] or ["   - không có"]
    L.append("  Đang GIẢM áp lực:")
    dn = [i for i in reversed(keys) if i["diem"] < -0.15]
    L += [f"   - {i['mo_ta']}" for i in dn] or ["   - không có"]
    miss = [i["chi_bao"] for i in res["chi_bao"] if i["diem"] is None]
    if miss:
        L.append("  Thiếu dữ liệu: " + ", ".join(miss))
    L.append("  Kiểm chứng: " + (res["kiem_chung"]["trang_thai"] if res["kiem_chung"]["trang_thai"] != "ok" else
                                 f"điểm tổng tương quan {res['kiem_chung']['diem_tong']['tuong_quan']} với khối ngoại ròng 5 phiên sau "
                                 f"({res['kiem_chung']['diem_tong']['so_diem']} điểm; âm = đúng hướng)"))
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path")
    ap.add_argument("--chu", action="store_true")
    ap.add_argument("--chan-troi", type=int, default=5)
    args = ap.parse_args()
    rows = load(args.csv_path)
    if not rows:
        sys.exit("File rỗng.")
    e = len(rows) - 1
    s, items, cov = score_at(rows, e)
    res = {"ngay": rows[e]["date"].isoformat(), "diem": s, "muc": level(s), "do_phu_pct": cov, "chi_bao": items,
           "kiem_chung": verify(rows, args.chan_troi),
           "ghi_chu": "Quy tắc theo lý thuyết cho tới khi kiểm chứng đủ dữ liệu. Không phải khuyến nghị mua/bán."}
    for back in range(5, 0, -1):
        if e - back >= 0:
            s2, _, _ = score_at(rows, e - back)
            if s2 is not None:
                res["thay_doi"] = {"ngay": rows[e - back]["date"].isoformat(), "diem": s2}
                break
    if args.chu:
        print(text(res))
    else:
        print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
