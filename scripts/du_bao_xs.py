#!/usr/bin/env python3
"""Dự báo XÁC SUẤT có chấm điểm: giá sau h phiên cao hơn hôm nay không, và vùng giá 80%.

Thay cho "kịch bản chính" do model tự viết (không đo được). Mọi con số ở đây do script tính,
được kiểm chứng trên dữ liệu quá khứ theo đúng trình tự thời gian, và được chấm điểm khi đến hạn.

Cách dùng:
    python du_bao_xs.py --gia MBB=gia_MBB.csv TCB=gia_TCB.csv CTG=gia_CTG.csv HPG=gia_HPG.csv \
        --chi-so gia_VNINDEX.csv --ky-han 5 20 --lich-su du-an/data/du-bao-xs.json --ra du_bao_xs.json

Cách làm (không thư viện ngoài):
  1. Tín hiệu: mỗi tín hiệu là một con số tính từ giá đến hôm nay (đà 5/20/60 phiên, RSI14, vị trí
     trong biên độ 60 phiên, khoảng cách tới SMA50, độ biến động 20 phiên; có --chi-so thì thêm đà và
     xu hướng VN-Index và sức mạnh so với VN-Index).
  2. Mức cơ sở: tỷ lệ số lần giá tăng sau h phiên trong quá khứ (không dùng tín hiệu nào).
     Một tín hiệu: chia quá khứ thành 5 nhóm theo giá trị tín hiệu, xác suất = tỷ lệ tăng của nhóm có
     giá trị giống hôm nay, kéo về mức cơ sở khi nhóm ít mẫu.
  3. Kiểm chứng đi theo thời gian, mỗi h phiên một điểm (không chồng lấn): tại mỗi điểm chỉ dùng các
     mẫu đã biết kết quả. Gộp mọi mã để có nhiều mẫu hơn.
     - 60% điểm đầu (giai đoạn CHỌN): giữ tín hiệu nào có điểm Brier tốt hơn mức cơ sở.
     - 40% điểm sau (giai đoạn THI, chưa nhìn khi chọn): chấm tổ hợp các tín hiệu đã giữ.
     Kết luận "co_loi_the" chỉ khi tổ hợp thắng mức cơ sở ở giai đoạn THI với xác suất bootstrap ≥ 90%.
     Không thì xác suất công bố = mức cơ sở, và nói rõ là không có tín hiệu nào thắng.
  4. Vùng 80%: lợi nhuận h phiên chia cho biến động EWMA lúc dự báo; lấy phân vị 10% và 90% của 500
     mẫu gần nhất đã biết kết quả (tự hiệu chỉnh nên độ phủ thật bám sát 80%).
  5. --lich-su: chấm các dự báo đã đến hạn (đúng/sai, Brier, có trong vùng 80% không) rồi ghi dự báo mới.

Đây là thống kê từ quá khứ; không phải lời hứa về tương lai và không phải khuyến nghị mua/bán.
"""
import argparse
import datetime as dt
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_prices  # noqa: E402

LAM = 0.94
SO_NHOM = 5          # số nhóm khi chia một tín hiệu
CO_RUT = 40          # độ kéo về mức cơ sở (mẫu ảo)
MIN_TRAIN = 250      # số mẫu tối thiểu đã biết kết quả trước khi bắt đầu chấm
CUA_SO_VUNG = 500    # số mẫu gần nhất dùng cho vùng 80%
TL_CHON = 0.6        # tỷ lệ điểm dành cho giai đoạn chọn tín hiệu
NGUONG_TIN = 0.90    # xác suất bootstrap tối thiểu để nói "có lợi thế"
KHOI = 8             # độ dài khối bootstrap (số điểm)


# ---------- tín hiệu ----------
def ewma_sigma(closes):
    """sig[t] = độ lệch chuẩn lợi nhuận 1 phiên dự kiến cho phiên t+1, chỉ dùng dữ liệu đến t."""
    n = len(closes)
    sig = [None] * n
    rets = [0.0] + [math.log(closes[i] / closes[i - 1]) for i in range(1, n)]
    if n < 22:
        return sig
    v = sum(r * r for r in rets[1:21]) / 20
    for t in range(1, n):
        v = LAM * v + (1 - LAM) * rets[t] * rets[t]
        if t >= 20:
            sig[t] = math.sqrt(v)
    return sig


def rsi14(closes):
    n = len(closes)
    out = [None] * n
    if n < 16:
        return out
    g = l = 0.0
    for i in range(1, 15):
        d = closes[i] - closes[i - 1]
        g += max(d, 0)
        l += max(-d, 0)
    g, l = g / 14, l / 14
    for i in range(15, n):
        d = closes[i] - closes[i - 1]
        g = (g * 13 + max(d, 0)) / 14
        l = (l * 13 + max(-d, 0)) / 14
        out[i] = 100.0 if l == 0 else 100 - 100 / (1 + g / l)
    return out


def tin_hieu_gia(closes):
    """dict tên -> list giá trị theo phiên (None khi chưa đủ dữ liệu)."""
    n = len(closes)
    lg = [math.log(c) for c in closes]
    f = {k: [None] * n for k in ("da_5", "da_20", "da_60", "rsi14", "vi_tri_60", "cach_sma50", "bien_dong_20")}
    r = rsi14(closes)
    for t in range(n):
        if t >= 5:
            f["da_5"][t] = lg[t] - lg[t - 5]
        if t >= 20:
            f["da_20"][t] = lg[t] - lg[t - 20]
            rets = [lg[i] - lg[i - 1] for i in range(t - 19, t + 1)]
            m = sum(rets) / 20
            f["bien_dong_20"][t] = math.sqrt(sum((x - m) ** 2 for x in rets) / 19)
        if t >= 49:
            f["cach_sma50"][t] = lg[t] - math.log(sum(closes[t - 49:t + 1]) / 50)
        if t >= 59:
            seg = closes[t - 59:t + 1]
            lo, hi = min(seg), max(seg)
            f["vi_tri_60"][t] = (closes[t] - lo) / (hi - lo) if hi > lo else 0.5
        if t >= 60:
            f["da_60"][t] = lg[t] - lg[t - 60]
        f["rsi14"][t] = r[t]
    return f


# ---------- dữ liệu ----------
def doc_ma(path):
    data = load_prices(path, min_rows=MIN_TRAIN)
    return [d["date"] for d in data], [d["close"] for d in data]


def tao_mau(ma, dates, closes, h, idx_map=None):
    """Mỗi mẫu: ngày dự báo, ngày biết kết quả, tín hiệu, kết quả tăng (1/0), lợi nhuận chuẩn hóa."""
    f = tin_hieu_gia(closes)
    sig = ewma_sigma(closes)
    if idx_map:
        for k in ("vni_da_20", "vni_cach_sma50", "manh_hon_vni_20"):
            f[k] = [None] * len(closes)
        for t, d in enumerate(dates):
            iv = idx_map.get(d)
            if iv is None:
                continue
            f["vni_da_20"][t] = iv.get("da_20")
            f["vni_cach_sma50"][t] = iv.get("cach_sma50")
            if iv.get("da_20") is not None and f["da_20"][t] is not None:
                f["manh_hon_vni_20"][t] = f["da_20"][t] - iv["da_20"]
    mau = []
    for t in range(len(closes)):
        if sig[t] is None:
            continue
        x = {k: v[t] for k, v in f.items()}
        m = {"ma": ma, "t": t, "ngay": dates[t], "gia": closes[t], "x": x, "sig": sig[t]}
        if t + h < len(closes):
            r = math.log(closes[t + h] / closes[t])
            m.update({"ngay_kq": dates[t + h], "y": 1 if r > 0 else 0, "z": r / (sig[t] * math.sqrt(h))})
        mau.append(m)
    return mau, list(f.keys())


def chi_so_map(path):
    dates, closes = doc_ma(path)
    f = tin_hieu_gia(closes)
    return {d: {"da_20": f["da_20"][t], "cach_sma50": f["cach_sma50"][t]} for t, d in enumerate(dates)}


# ---------- mô hình ----------
def ti_le(train):
    n = len(train)
    return (sum(m["y"] for m in train) + 1) / (n + 2) if n else 0.5


def bien_nhom(vals):
    sv = sorted(vals)
    return [sv[int(len(sv) * i / SO_NHOM)] for i in range(1, SO_NHOM)]


def nhom_cua(v, bien):
    for i, b in enumerate(bien):
        if v < b:
            return i
    return len(bien)


class MoHinh:
    """Học từ các mẫu đã biết kết quả: mức cơ sở + bảng tỷ lệ tăng theo nhóm cho từng tín hiệu."""

    def __init__(self, train, ten_tin_hieu):
        self.base = ti_le(train)
        self.bang = {}
        for k in ten_tin_hieu:
            pts = [(m["x"][k], m["y"]) for m in train if m["x"].get(k) is not None]
            if len(pts) < 100:
                continue
            bien = bien_nhom([v for v, _ in pts])
            dem = [[0, 0] for _ in range(SO_NHOM)]
            for v, y in pts:
                g = nhom_cua(v, bien)
                dem[g][0] += y
                dem[g][1] += 1
            base_k = sum(y for _, y in pts) / len(pts)
            p = [(a + CO_RUT * base_k) / (b + CO_RUT) for a, b in dem]
            self.bang[k] = (bien, p, base_k, [b for _, b in dem])

    def p_tin_hieu(self, m, k):
        v = m["x"].get(k)
        if v is None or k not in self.bang:
            return self.base
        bien, p, base_k, _ = self.bang[k]
        # dịch theo chênh lệch của nhóm so với mức cơ sở của chính tín hiệu
        return min(0.99, max(0.01, self.base + p[nhom_cua(v, bien)] - base_k))

    def p_to_hop(self, m, giu):
        if not giu:
            return self.base
        lb = logit(self.base)
        s = sum(logit(self.p_tin_hieu(m, k)) - lb for k in giu) / len(giu)
        return 1 / (1 + math.exp(-(lb + s)))


def logit(p):
    p = min(0.99, max(0.01, p))
    return math.log(p / (1 - p))


def phan_vi(vals, q):
    sv = sorted(vals)
    k = (len(sv) - 1) * q
    f = int(k)
    c = min(f + 1, len(sv) - 1)
    return sv[f] + (sv[c] - sv[f]) * (k - f)


def vung80(train_z, sig, gia, h):
    zs = train_z[-CUA_SO_VUNG:]
    if len(zs) < 100:
        return None
    s = sig * math.sqrt(h)
    return [gia * math.exp(phan_vi(zs, 0.10) * s), gia * math.exp(phan_vi(zs, 0.90) * s)]


# ---------- kiểm chứng ----------
def kiem_chung(mau_all, ten, h, rng):
    """Đi theo thời gian, mỗi h phiên một điểm; trả về các dòng chấm điểm."""
    ngay_diem = sorted({m["ngay"] for m in mau_all if "y" in m})
    co_kq = sorted((m for m in mau_all if "y" in m), key=lambda m: m["ngay_kq"])
    dong, j, train, cache_mh = [], 0, [], None
    lan_hoc = 0
    for i in range(0, len(ngay_diem), h):
        d = ngay_diem[i]
        while j < len(co_kq) and co_kq[j]["ngay_kq"] <= d:
            train.append(co_kq[j])
            j += 1
        if len(train) < MIN_TRAIN:
            continue
        # học lại mỗi ~20 phiên cho nhanh
        if cache_mh is None or lan_hoc % max(1, 20 // h) == 0:
            cache_mh = MoHinh(train, ten)
        lan_hoc += 1
        z_train = [m["z"] for m in train]
        for m in mau_all:
            if m["ngay"] != d or "y" not in m:
                continue
            v = vung80(z_train, m["sig"], m["gia"], h)
            gia_kq = m["gia"] * math.exp(m["z"] * m["sig"] * math.sqrt(h))
            dong.append({"ngay": d, "ma": m["ma"], "y": m["y"], "base": cache_mh.base,
                         "p": {k: cache_mh.p_tin_hieu(m, k) for k in ten},
                         "mh": cache_mh, "m": m,
                         "trong_vung": None if v is None else (v[0] <= gia_kq <= v[1])})
    return dong


def brier(ps, ys):
    return sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ys)


def bootstrap_thang(d_base, d_mh, rng, so_lan=2000):
    """Xác suất (theo bootstrap khối) để Brier của mô hình nhỏ hơn mức cơ sở."""
    n = len(d_base)
    if n < 2 * KHOI:
        return None
    thang = 0
    for _ in range(so_lan):
        s = 0.0
        cnt = 0
        while cnt < n:
            a = rng.randrange(0, n - KHOI + 1)
            for i in range(a, a + KHOI):
                s += d_base[i] - d_mh[i]
            cnt += KHOI
        thang += s > 0
    return thang / so_lan


def danh_gia(dong, ten, rng):
    cut = int(len(dong) * TL_CHON)
    chon, thi = dong[:cut], dong[cut:]
    if len(chon) < 30 or len(thi) < 20:
        return {"ket_luan": "chua_du_du_lieu", "so_diem": len(dong)}
    ys_c = [r["y"] for r in chon]
    b_base_c = brier([r["base"] for r in chon], ys_c)
    tung = {}
    for k in ten:
        b = brier([r["p"][k] for r in chon], ys_c)
        tung[k] = round(1 - b / b_base_c, 4)
    giu = [k for k, s in sorted(tung.items(), key=lambda kv: -kv[1]) if s > 0]
    ys_t = [r["y"] for r in thi]
    pb = [r["base"] for r in thi]
    pm = [r["mh"].p_to_hop(r["m"], giu) for r in thi]
    b_base_t, b_mh_t = brier(pb, ys_t), brier(pm, ys_t)
    d_b = [(p - y) ** 2 for p, y in zip(pb, ys_t)]
    d_m = [(p - y) ** 2 for p, y in zip(pm, ys_t)]
    xs = bootstrap_thang(d_b, d_m, rng) if giu else None
    if giu and xs is not None and xs >= NGUONG_TIN and b_mh_t < b_base_t:
        kl = "co_loi_the"
    elif giu and b_mh_t < b_base_t:
        kl = "chua_chac"
    else:
        kl = "khong"
    dung_huong = sum(1 for p, y in zip(pm, ys_t) if (p > 0.5) == (y == 1)) / len(ys_t)
    dung_co_so = sum(1 for p, y in zip(pb, ys_t) if (p > 0.5) == (y == 1)) / len(ys_t)
    vung = [r["trong_vung"] for r in dong if r["trong_vung"] is not None]
    return {
        "ket_luan": kl,
        "so_diem_chon": len(chon), "so_diem_thi": len(thi),
        "giai_doan_thi": [thi[0]["ngay"].isoformat(), thi[-1]["ngay"].isoformat()],
        "diem_tung_tin_hieu_giai_doan_chon": tung,
        "tin_hieu_giu": giu,
        "brier_co_so_thi": round(b_base_t, 4), "brier_to_hop_thi": round(b_mh_t, 4),
        "diem_ky_nang_thi": round(1 - b_mh_t / b_base_t, 4),
        "xac_suat_bootstrap_thang": None if xs is None else round(xs, 3),
        "ty_le_dung_huong_thi": round(dung_huong, 3),
        "ty_le_dung_huong_co_so_thi": round(dung_co_so, 3),
        "do_phu_vung_80_pct": round(100 * sum(vung) / len(vung), 1) if vung else None,
        "so_diem_vung": len(vung),
    }


# ---------- lịch sử ----------
def cham_lich_su(hist, gia_theo_ma, hom_nay):
    ket_qua = []
    for fc in hist.get("du_bao", []):
        if fc.get("da_cham"):
            continue
        dates, closes = gia_theo_ma.get(fc["ma"], (None, None))
        if not dates:
            continue
        try:
            i0 = dates.index(dt.date.fromisoformat(fc["ngay"]))
        except ValueError:
            continue
        if i0 + fc["h"] >= len(closes):
            continue
        g = closes[i0 + fc["h"]]
        y = 1 if g > fc["gia"] else 0
        fc.update({"da_cham": True, "gia_kq": g, "ngay_kq": dates[i0 + fc["h"]].isoformat(), "y": y,
                   "brier": round((fc["p_tang"] - y) ** 2, 4),
                   "brier_co_so": round((fc["p_co_so"] - y) ** 2, 4),
                   "trong_vung_80": None if not fc.get("vung_80") else fc["vung_80"][0] <= g <= fc["vung_80"][1]})
        ket_qua.append(fc)
    da = [f for f in hist.get("du_bao", []) if f.get("da_cham")]
    tong = None
    if da:
        v = [f["trong_vung_80"] for f in da if f.get("trong_vung_80") is not None]
        tong = {"so_du_bao_da_cham": len(da),
                "brier_trung_binh": round(sum(f["brier"] for f in da) / len(da), 4),
                "brier_co_so_trung_binh": round(sum(f["brier_co_so"] for f in da) / len(da), 4),
                "do_phu_vung_80_pct": round(100 * sum(v) / len(v), 1) if v else None,
                "nhan_xet": "dưới 30 dự báo đã chấm: chưa kết luận được" if len(da) < 30 else
                            ("tốt hơn mức cơ sở" if sum(f["brier"] for f in da) < sum(f["brier_co_so"] for f in da)
                             else "KHÔNG tốt hơn mức cơ sở")}
    return ket_qua, tong


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gia", nargs="+", required=True, help="MÃ=đường_dẫn_csv (nhiều mã được gộp để học)")
    ap.add_argument("--chi-so", help="CSV giá VN-Index (thêm tín hiệu thị trường)")
    ap.add_argument("--ky-han", type=int, nargs="+", default=[5, 20])
    ap.add_argument("--lich-su", help="JSON lịch sử dự báo: chấm cái đến hạn rồi ghi dự báo mới")
    ap.add_argument("--khong-ghi", action="store_true", help="chấm lịch sử nhưng không ghi dự báo mới")
    ap.add_argument("--ra", help="ghi kết quả JSON ra file (mặc định in ra màn hình)")
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    rng = random.Random(a.seed)

    gia = {}
    for s in a.gia:
        if "=" not in s:
            sys.exit(f"--gia cần dạng MÃ=file.csv, nhận {s!r}")
        ma, p = s.split("=", 1)
        gia[ma.upper()] = doc_ma(p)
    idx = chi_so_map(a.chi_so) if a.chi_so else None

    out = {"ngay_du_lieu": {m: d[-1].isoformat() for m, (d, _) in gia.items()}, "ky_han": {}}
    moi = []
    for h in a.ky_han:
        mau_all, ten = [], None
        for ma, (dates, closes) in gia.items():
            mau, ten = tao_mau(ma, dates, closes, h, idx)
            mau_all.extend(mau)
        dong = kiem_chung(mau_all, ten, h, rng)
        dg = danh_gia(dong, ten, rng)
        train = [m for m in mau_all if "y" in m]
        mh = MoHinh(train, ten)
        z_train = [m["z"] for m in sorted(train, key=lambda m: m["ngay_kq"])]
        giu = dg.get("tin_hieu_giu", []) if dg["ket_luan"] == "co_loi_the" else []
        hom_nay = {}
        for ma, (dates, closes) in gia.items():
            cur = [m for m in mau_all if m["ma"] == ma][-1]
            base = mh.base
            p = mh.p_to_hop(cur, giu)
            v = vung80(z_train, cur["sig"], cur["gia"], h)
            hom_nay[ma] = {"ngay": cur["ngay"].isoformat(), "gia": cur["gia"],
                           "xac_suat_tang_pct": round(100 * p, 1),
                           "xac_suat_co_so_pct": round(100 * base, 1),
                           "dung_tin_hieu": bool(giu),
                           "vung_80": None if v is None else [round(v[0], 2), round(v[1], 2)]}
            moi.append({"ma": ma, "ngay": cur["ngay"].isoformat(), "h": h, "gia": cur["gia"],
                        "p_tang": round(p, 4), "p_co_so": round(base, 4), "tin_hieu": giu,
                        "vung_80": None if v is None else [round(v[0], 2), round(v[1], 2)]})
        out["ky_han"][str(h)] = {"kiem_chung": dg, "hom_nay": hom_nay}

    if a.lich_su:
        hist = {"du_bao": []}
        if os.path.exists(a.lich_su) and os.path.getsize(a.lich_su) > 2:
            with open(a.lich_su, encoding="utf-8") as f:
                hist = json.load(f)
        vua_cham, tong = cham_lich_su(hist, gia, None)
        out["lich_su"] = {"vua_cham": vua_cham, "tong": tong}
        if not a.khong_ghi:
            co = {(f["ma"], f["ngay"], f["h"]) for f in hist["du_bao"]}
            hist["du_bao"].extend(f for f in moi if (f["ma"], f["ngay"], f["h"]) not in co)
        with open(a.lich_su, "w", encoding="utf-8") as f:
            json.dump(hist, f, ensure_ascii=False, indent=1)

    out["cach_doc"] = ("xac_suat_tang_pct: khả năng giá đóng cửa sau h phiên cao hơn hôm nay. "
                       "Khi kiem_chung.ket_luan khác 'co_loi_the' thì con số này CHÍNH LÀ mức cơ sở: "
                       "không tín hiệu nào đoán hướng tốt hơn tỷ lệ tăng trong quá khứ. "
                       "vung_80: khoảng giá mà khoảng 8/10 lần giá sau h phiên rơi vào.")
    s = json.dumps(out, ensure_ascii=False, indent=1, default=str)
    if a.ra:
        with open(a.ra, "w", encoding="utf-8") as f:
            f.write(s)
    print(tom_tat(out))


def tom_tat(out):
    dong = []
    for h, v in out["ky_han"].items():
        k = v["kiem_chung"]
        if k["ket_luan"] == "chua_du_du_lieu":
            dong.append(f"{h} phiên: chưa đủ dữ liệu để kiểm chứng ({k['so_diem']} điểm)")
            continue
        kl = {"co_loi_the": "CÓ lợi thế", "chua_chac": "nhỉnh hơn nhưng chưa chắc", "khong": "KHÔNG thắng"}[k["ket_luan"]]
        dong.append(f"{h} phiên: tín hiệu {kl} so với mức cơ sở (điểm kỹ năng {k['diem_ky_nang_thi']:+.3f}, "
                    f"bootstrap {k['xac_suat_bootstrap_thang']}, {k['so_diem_thi']} điểm thi; "
                    f"đúng hướng {100*k['ty_le_dung_huong_thi']:.0f}% vs cơ sở {100*k['ty_le_dung_huong_co_so_thi']:.0f}%); "
                    f"vùng 80% phủ {k['do_phu_vung_80_pct']}%; giữ: {', '.join(k['tin_hieu_giu']) or 'không'}")
        for ma, x in v["hom_nay"].items():
            dong.append(f"  {ma}: P(tăng sau {h} phiên) {x['xac_suat_tang_pct']}% "
                        f"(cơ sở {x['xac_suat_co_so_pct']}%), vùng 80% {x['vung_80']}")
    t = out.get("lich_su", {}).get("tong")
    if t:
        dong.append(f"Lịch sử: {t['so_du_bao_da_cham']} dự báo đã chấm, Brier {t['brier_trung_binh']} "
                    f"vs cơ sở {t['brier_co_so_trung_binh']}, vùng 80% phủ {t['do_phu_vung_80_pct']}% ({t['nhan_xet']})")
    return "\n".join(dong)


if __name__ == "__main__":
    main()
