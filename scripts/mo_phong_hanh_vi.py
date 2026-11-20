#!/usr/bin/env python3
"""Mô phỏng HÀNH VI mua bán của nhiều nhóm nhà đầu tư (agent-based model) + Monte Carlo.

Kiểu A – đám đông toàn thị trường: chạy trên VN-Index.
Kiểu C – phản ứng theo từng mã (MBB, TCB, HPG, CTG...): cùng bộ máy, nhận đường đi VN-Index từ kiểu A.
Kiểu B – bản sao hành vi của chính người dùng: CHƯA làm (chỗ cắm sẵn ở `--ho-so-ca-nhan`, báo lỗi rõ).

Ba nhóm agent
  • Nhỏ lẻ (mặc định 600 agent/lần chạy, vốn 100–200 triệu đồng): bầy đàn (Lux–Marchesi), đuổi xu hướng,
    hiệu ứng bán sớm/gồng lỗ (Shefrin–Statman), ngại thua lỗ (Kahneman–Tversky): sau khi cắt lỗ thì
    "sợ" không mua lại một thời gian, và đòi tín hiệu mạnh hơn mới mua khi biến động cao. Có người dùng margin
    (bị bán giải chấp khi lỗ sâu). Chịu luật T+2 (cổ phiếu mua phiên trước chưa bán được) và lô 100.
  • Lớn (mặc định 30 agent, vốn 5–10 tỷ): neo theo "giá trị" (EMA 120 phiên), mua khi giá thấp hơn, bán khi cao hơn;
    ít bầy đàn, cắt lỗ có kỷ luật.
  • Khối ngoại: dòng tiền ngoại sinh lấy từ số thật (VND MCP), khi mô phỏng tương lai thì lấy mẫu khối từ số gần đây.
Mỗi agent đại diện cho nhiều nhà đầu tư giống nó: trọng số được chỉnh để tỷ trọng giá trị giao dịch của từng nhóm
khớp với `--ty-trong-nho-le` và tỷ trọng thật của khối ngoại.

Giá: lợi suất = kappa × (cầu ròng / giá trị giao dịch bình quân) + nhiễu thông tin; chặn biên độ (HOSE ±7%),
làm tròn bước giá HOSE.

Hiệu chỉnh ("chạy nhiều lần để tối ưu"): phương pháp mô-men mô phỏng (method of simulated moments).
Thử nhiều bộ tham số hành vi, mỗi bộ chạy nhiều lần, so 6 "dấu vân tay" của chuỗi giá thật (độ biến động, đuôi dày,
tự tương quan lợi suất, cụm biến động, tương quan |lợi suất|–thanh khoản, tương quan lợi suất–khối ngoại),
chọn bộ gần nhất, rồi tinh chỉnh quanh các bộ tốt nhất. Kiểm tra NGOÀI MẪU: hiệu chỉnh trên 70% đầu, chấm trên 30% sau,
so với mô hình rỗng không có hành vi (chỉ nhiễu + tác động giá). Mô hình hành vi không thắng mô hình rỗng thì phải nói rõ.

Cách dùng
  python mo_phong_hanh_vi.py hieu-chinh --ma VNINDEX --gia gia_VNINDEX_vnd.csv --khoi-ngoai khoi_ngoai.csv --out ts_VNINDEX.json
  python mo_phong_hanh_vi.py hieu-chinh --ma MBB --gia gia_MBB_vnd.csv --thi-truong gia_VNINDEX_vnd.csv \
        --khoi-ngoai khoi_ngoai.csv --out ts_MBB.json
  python mo_phong_hanh_vi.py kich-ban --ma MBB --gia ... --thi-truong ... --khoi-ngoai ... --tham-so ts_MBB.json \
        --tham-so-thi-truong ts_VNINDEX.json --phien 6 --so-lan 2000 --out kb_MBB.json --chu

File giá: cột date,open,high,low,close,volume[,value] (nghìn đồng; value đồng – thiếu thì ước = close×1000×volume).
File khối ngoại: date[,code],netVal[,buyVal,sellVal] (đồng).
Đây là mô hình để HIỂU hành vi và lập kịch bản, không phải dự báo chắc chắn, không phải khuyến nghị mua/bán.
"""
import argparse
import csv
import datetime as dt
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_prices  # noqa: E402

PHIEN_BAN = "1.0"
BURN = 60            # số phiên "nạp lịch sử" (giá ép theo thật) trước khi để giá tự do
FEE = 0.0015         # phí giao dịch mỗi chiều (ước, VNDirect khoảng 0,15–0,35%)
TAX_SELL = 0.001     # thuế bán 0,1%
LAM_REF = 2.25       # hệ số ngại thua lỗ tham chiếu (Tversky & Kahneman 1992)
NU = 0.3             # tốc độ cập nhật tâm lý đám đông
THETA0 = 0.9         # ngưỡng tín hiệu để hành động

# (tên, thấp, cao, ý nghĩa)
PARAMS = [
    ("bay_dan", 0.0, 1.8, "mức bầy đàn của nhỏ lẻ (>1: dễ tự khuếch đại thành hưng phấn/hoảng loạn)"),
    ("xu_huong", 0.0, 1.5, "mức đuổi theo nhịp tăng/giảm 5 phiên"),
    ("theo_thi_truong", 0.0, 1.5, "mức nhỏ lẻ nhìn VN-Index để quyết định"),
    ("ngai_lo", 1.0, 3.5, "hệ số ngại thua lỗ λ (lý thuyết ≈ 2,25)"),
    ("ban_som", 0.0, 2.0, "hiệu ứng bán sớm khi lãi / gồng khi lỗ"),
    ("neo_gia_tri", 0.0, 2.0, "mức nhà đầu tư lớn mua khi rẻ, bán khi đắt so với EMA120"),
    ("kappa", 0.001, 0.12, "tác động giá của 1 đơn vị cầu ròng (theo giá trị GD bình quân)"),
    ("nhieu", 0.002, 0.025, "nhiễu thông tin không thuộc hành vi (độ lệch chuẩn lợi suất/phiên)"),
]
NAMES = [p[0] for p in PARAMS]
NULL_FIXED = {"bay_dan": 0.0, "xu_huong": 0.0, "theo_thi_truong": 0.0, "ngai_lo": 1.0, "ban_som": 0.0, "neo_gia_tri": 0.0}
MOMENTS = ["do_bien_dong", "duoi_day", "tu_tuong_quan", "cum_bien_dong", "thanh_khoan_bien_dong", "khoi_ngoai_gia"]


# ---------------- dữ liệu ----------------
def load_series(path):
    rows = load_prices(path, min_rows=BURN + 40)
    with open(path, newline="", encoding="utf-8-sig") as f:
        raw = {(r.get("date") or "").strip(): r for r in csv.DictReader(f)}
    out = []
    for r in rows:
        v = None
        rr = raw.get(r["date"].isoformat())
        if rr and (rr.get("value") or "").strip() not in ("", "None", "null"):
            v = float(rr["value"])
        if v is None:
            v = r["close"] * 1000 * (r["volume"] or 0)
        out.append((r["date"], r["close"], v))
    return out


def load_foreign(path, code):
    if not path:
        return {}
    res = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if "code" in r and r["code"] and r["code"].strip().upper() != code.upper():
                continue
            try:
                d = dt.date.fromisoformat(r["date"].strip()[:10])
                nv = float(r["netVal"])
            except (KeyError, ValueError):
                continue
            g = None
            try:
                g = (float(r["buyVal"]) + float(r["sellVal"])) / 2
            except (KeyError, ValueError, TypeError):
                pass
            res[d] = (nv, g)
    return res


def build(args):
    """Ghép giá mã, VN-Index, khối ngoại theo ngày. Trả dict mảng numpy."""
    s = load_series(args.gia)
    # chỉ dùng đoạn liên tục cuối cùng: khoảng trống > 12 ngày lịch (dài hơn Tết) làm sai lợi suất
    cut = 0
    for j in range(1, len(s)):
        if (s[j][0] - s[j - 1][0]).days > 12:
            cut = j
    if cut:
        print(f"⚠ {args.ma}: dữ liệu giá đứt quãng trước {s[cut][0]}, chỉ dùng từ ngày đó ({len(s) - cut} phiên).",
              file=sys.stderr)
        s = s[cut:]
    dates = [d for d, _, _ in s]
    price = np.array([p for _, p, _ in s])
    value = np.array([v for _, _, v in s])
    is_index = args.ma.upper() in ("VNINDEX", "VN30", "HNX", "UPCOM")
    mret = np.zeros(len(dates))
    have_m = False
    if args.thi_truong and not is_index:
        m = {d: p for d, p, _ in load_series(args.thi_truong)}
        mp = np.array([m.get(d, np.nan) for d in dates])
        mp = np.where(np.isnan(mp), np.nan, mp)
        # điền trống bằng giá trước
        for i in range(1, len(mp)):
            if np.isnan(mp[i]):
                mp[i] = mp[i - 1]
        mret[1:] = np.nan_to_num(mp[1:] / mp[:-1] - 1)
        have_m = True
    fx = load_foreign(args.khoi_ngoai, args.ma)
    fnet = np.array([fx.get(d, (0.0, None))[0] for d in dates])
    fgross = np.array([fx.get(d, (0.0, None))[1] or 0.0 for d in dates])
    n_f = sum(1 for d in dates if d in fx)
    # các phiên đầu thiếu khối ngoại: chỉ dùng đoạn có khối ngoại nếu đủ dài
    ret = np.zeros(len(dates))
    ret[1:] = price[1:] / price[:-1] - 1
    return {"dates": dates, "price": price, "value": value, "ret": ret, "mret": mret, "have_m": have_m,
            "fnet": fnet, "fgross": fgross, "n_foreign": n_f, "is_index": is_index,
            "limit": args.bien_do, "ma": args.ma.upper()}


# ---------------- bước giá HOSE ----------------
def tick_round(p, is_index):
    if is_index:
        return p
    t = np.where(p < 10, 0.01, np.where(p < 50, 0.05, 0.1))
    return np.round(p / t) * t


# ---------------- mô-men ----------------
def acf(x, k):
    x = x - x.mean(axis=-1, keepdims=True)
    den = (x * x).sum(axis=-1)
    num = (x[..., k:] * x[..., :-k]).sum(axis=-1)
    return num / np.where(den == 0, 1, den)


def corr(a, b):
    a = a - a.mean(axis=-1, keepdims=True)
    b = b - b.mean(axis=-1, keepdims=True)
    den = np.sqrt((a * a).sum(axis=-1) * (b * b).sum(axis=-1))
    return (a * b).sum(axis=-1) / np.where(den == 0, 1, den)


def moments(r, v, f):
    """r, v, f: (..., T). Trả (..., 6)."""
    sd = r.std(axis=-1)
    z = (r - r.mean(axis=-1, keepdims=True)) / np.where(sd == 0, 1, sd)[..., None]
    kurt = (z ** 4).mean(axis=-1) - 3
    a1 = acf(r, 1)
    ab = np.abs(r)
    clus = np.mean([acf(ab, k) for k in range(1, 6)], axis=0)
    cv = corr(ab, v)
    cf = corr(r, f) if np.any(f) else np.zeros_like(sd)
    return np.stack([sd * 100, np.minimum(kurt, 30), a1, clus, cv, cf], axis=-1)


def real_moments(r, v, f, n_boot=300, block=10, seed=7):
    m = moments(r, v, f)
    rng = np.random.default_rng(seed)
    T = len(r)
    bs = []
    for _ in range(n_boot):
        idx = np.concatenate([np.arange(s, s + block) for s in rng.integers(0, T - block, T // block + 1)])[:T]
        bs.append(moments(r[idx], v[idx], f[idx]))
    se = np.array(bs).std(axis=0)
    se = np.maximum(se, np.array([0.05, 0.3, 0.03, 0.03, 0.04, 0.04]))
    return m, se


# ---------------- bộ máy mô phỏng ----------------
class Pop:
    """Trạng thái agent cho M lần chạy song song."""

    def __init__(self, rng, M, nr, nl, p0, profile):
        self.M, self.nr, self.nl = M, nr, nl
        n = nr + nl
        self.is_r = np.zeros(n, bool)
        self.is_r[:nr] = True
        cap = np.concatenate([rng.uniform(100e6, 200e6, (M, nr)), rng.uniform(5e9, 10e9, (M, nl))], axis=1)
        frac = np.concatenate([rng.uniform(0.2, 0.8, (M, nr)), rng.uniform(0.3, 0.7, (M, nl))], axis=1)
        self.shares = np.floor(cap * frac / (p0 * 1000) / 100) * 100
        self.cash = cap - self.shares * p0 * 1000
        # giá vốn lấy mẫu theo phân bố khối lượng các phiên trước (hồ sơ khối lượng)
        pp, ww = profile
        self.cost = rng.choice(pp, size=(M, n), p=ww / ww.sum())
        self.lock = np.zeros((M, n))
        self.cool = np.zeros((M, n))
        self.L = np.where(rng.random((M, n)) < 0.3, 0.12, rng.uniform(0.08, 0.25, (M, n)))  # 30% dùng margin
        self.L[:, nr:] = 0.10


def run(theta, D, start, n_forced, n_free, M, rng, nr=600, nl=30, scen=None, mpaths=None, share_r=0.70,
        record_agents=False):
    """Chạy M lần song song.
    start: chỉ số phiên đầu tiên của đoạn ép giá; n_forced phiên ép giá thật, rồi n_free phiên giá tự do.
    Trong đoạn tự do: nếu n_free vượt dữ liệu (tương lai) thì khối ngoại và VN-Index lấy theo scen/mpaths.
    Trả dict: ret (M,n_free), val (M,n_free), các luồng tiền theo nhóm, chỉ báo hành vi."""
    th = dict(zip(NAMES, theta)) if not isinstance(theta, dict) else theta
    h, wt, bm = th["bay_dan"], th["xu_huong"], th["theo_thi_truong"]
    lam, dsp, phi = th["ngai_lo"], th["ban_som"], th["neo_gia_tri"]
    kap, sn = th["kappa"], th["nhieu"]
    P, R, V, MR, FN, FG = D["price"], D["ret"], D["value"], D["mret"], D["fnet"], D["fgross"]
    Tdat = len(P)
    is_index, lim = D["is_index"], D["limit"]
    sig = max(np.std(R[max(1, start - 250):start + n_forced]), 0.004)
    sig_m = max(np.std(MR[max(1, start - 250):start + n_forced]), 0.003) if D["have_m"] else 1.0
    lo = max(0, start - 60)
    prof = (P[lo:start + 1], np.maximum(V[lo:start + 1], 1.0))
    pop = Pop(rng, M, nr, nl, P[start], prof)
    vbar = V[max(0, start + n_forced - 60):start + n_forced].mean()
    fshare = min(0.4, FG[max(0, start + n_forced - 120):start + n_forced].mean() / vbar) if vbar > 0 else 0.0
    share_l = max(0.05, 1 - share_r - fshare)
    isr = pop.is_r

    hist = np.tile(P[max(0, start - 20):start + 1], (M, 1))   # lịch sử giá (M, ≤21)
    ema = np.full(M, P[max(0, start - 120):start + 1].mean())
    x = np.zeros(M)
    g_r = np.zeros(M)
    g_l = np.zeros(M)
    wr = wl = None
    T = n_forced + n_free
    out = {k: np.zeros((M, n_free)) for k in ("ret", "val", "net_r", "net_l", "net_f", "x", "capit", "chot_lai",
                                                "gong_lo")}
    news = np.zeros(n_free) if scen is None else scen.get("news", np.zeros(n_free))
    fund = 0.0 if scen is None else scen.get("fund", 0.0)
    for t in range(T):
        i = start + t + 1                   # phiên đang mô phỏng
        free = t >= n_forced
        k = t - n_forced
        p_prev = hist[:, -1]
        # đầu vào ngoại sinh
        if i < Tdat and (mpaths is None or not free):
            mret_t = np.full(M, MR[i])
            f_t = np.full(M, FN[i])
        else:
            mret_t = mpaths[:, k] if mpaths is not None else np.zeros(M)
            f_t = scen["foreign"][:, k] if scen is not None and "foreign" in scen else np.zeros(M)
        # ---- tâm lý đám đông (Lux–Marchesi rút gọn) ----
        z5 = (p_prev / hist[:, max(0, hist.shape[1] - 6)] - 1) / (sig * math.sqrt(5))
        zm = mret_t / sig_m if D["have_m"] else 0.0
        nw = news[k] if free else 0.0
        x = (1 - NU) * x + NU * np.tanh(h * x + wt * z5 + bm * zm + nw) + 0.08 * rng.standard_normal(M)
        x = np.clip(x, -1, 1)
        vr = (np.std(np.diff(hist[:, -6:], axis=1) / hist[:, -6:-1], axis=1) / sig) if hist.shape[1] >= 6 else np.ones(M)
        # ---- quyết định từng agent ----
        held = pop.shares > 0
        g = np.where(held, p_prev[:, None] / pop.cost - 1, 0.0)
        gs = g / (sig * math.sqrt(5))
        disp = np.where(g > 0, -dsp * np.minimum(gs, 3), dsp * (lam / LAM_REF) * np.minimum(-gs, 2)) * held
        eta = rng.standard_normal(pop.shares.shape)
        sig_r = x[:, None] + 0.6 * eta + disp
        gap = (ema * (1 + fund if free else 1) - p_prev) / p_prev / (sig * math.sqrt(20))
        sig_l = phi * gap[:, None] + 0.3 * h * x[:, None] + 0.5 * eta + 0.3 * disp
        s = np.where(isr[None, :], sig_r, sig_l)
        th_b = THETA0 * (1 + 0.5 * (lam - 1) * np.maximum(0, vr - 1))[:, None]
        th_b = np.where(isr[None, :], th_b, 0.7)
        th_s = np.where(isr[None, :], THETA0, 0.7)
        sellable = np.maximum(pop.shares - pop.lock, 0)
        lot_cost = p_prev[:, None] * 1000 * 100
        buy = (s > th_b) & (pop.cool <= 0) & (pop.cash >= lot_cost)
        sell = (s < -th_s) & (sellable > 0)
        capit = (g < -pop.L) & (sellable > 0)
        frac_b = np.where(isr[None, :], rng.uniform(0.3, 0.7, s.shape), 0.2)
        frac_s = np.where(isr[None, :], rng.uniform(0.5, 1.0, s.shape), 0.25)
        q_b = np.where(buy, np.floor(pop.cash * frac_b / lot_cost) * 100, 0)
        q_s = np.where(sell, np.ceil(sellable * frac_s / 100) * 100, 0)
        q_s = np.where(capit, np.where(isr[None, :], sellable, np.ceil(sellable * 0.5 / 100) * 100), q_s)
        q_s = np.minimum(q_s, sellable)
        q_b = np.where(q_s > 0, 0, q_b)
        bv = q_b * p_prev[:, None] * 1000
        sv = q_s * p_prev[:, None] * 1000
        gross_r = ((bv + sv) * isr).sum(1) / 2
        gross_l = ((bv + sv) * ~isr).sum(1) / 2
        net_r = ((bv - sv) * isr).sum(1)
        net_l = ((bv - sv) * ~isr).sum(1)
        # ---- giá ----
        if not free:
            p_new = np.full(M, P[i])
            g_r += gross_r
            g_l += gross_l
            if t == n_forced - 1:
                wr = share_r * vbar / np.maximum(g_r / n_forced, 1.0)
                wl = share_l * vbar / np.maximum(g_l / n_forced, 1.0)
        else:
            dem = wr * net_r + wl * net_l + f_t
            r_t = kap * dem / vbar + sn * rng.standard_normal(M)
            r_t = np.clip(r_t, -lim, lim)
            p_new = tick_round(p_prev * (1 + r_t), is_index)
            if not is_index:  # giữ trong biên độ sau khi làm tròn
                ceil_ = np.floor(p_prev * (1 + lim) / np.where(p_prev < 10, 0.01, np.where(p_prev < 50, 0.05, 0.1)) + 1e-9) \
                    * np.where(p_prev < 10, 0.01, np.where(p_prev < 50, 0.05, 0.1))
                flo_ = np.ceil(p_prev * (1 - lim) / np.where(p_prev < 10, 0.01, np.where(p_prev < 50, 0.05, 0.1)) - 1e-9) \
                    * np.where(p_prev < 10, 0.01, np.where(p_prev < 50, 0.05, 0.1))
                p_new = np.clip(p_new, flo_, ceil_)
            out["ret"][:, k] = p_new / p_prev - 1
            out["val"][:, k] = (wr * gross_r + wl * gross_l + np.abs(f_t) + (FG[i] if i < Tdat else fshare * vbar)) / vbar
            out["net_r"][:, k] = wr * net_r
            out["net_l"][:, k] = wl * net_l
            out["net_f"][:, k] = f_t
            out["x"][:, k] = x
            nr_ = max(nr, 1)
            out["capit"][:, k] = (capit & isr[None, :]).sum(1) / nr_
            # Odean (1998): PGR = lãi đã chốt / (lãi đã chốt + lãi trên giấy); PLR tương tự cho lỗ
            rg = ((q_s > 0) & (g > 0) & isr[None, :]).sum(1)
            pg = ((q_s == 0) & (g > 0) & held & isr[None, :]).sum(1)
            rl = ((q_s > 0) & (g < 0) & isr[None, :]).sum(1)
            pl = ((q_s == 0) & (g < 0) & held & isr[None, :]).sum(1)
            out["chot_lai"][:, k] = rg / np.maximum(rg + pg, 1)
            out["gong_lo"][:, k] = rl / np.maximum(rl + pl, 1)
        # ---- khớp lệnh và sổ sách ----
        pn = p_new[:, None] * 1000
        pop.cash += q_s * pn * (1 - FEE - TAX_SELL) - q_b * pn * (1 + FEE)
        newsh = pop.shares + q_b - q_s
        pop.cost = np.where(q_b > 0, (pop.cost * pop.shares + q_b * p_new[:, None]) / np.maximum(pop.shares + q_b, 1), pop.cost)
        pop.cost = np.where(newsh <= 0, p_new[:, None], pop.cost)
        pop.shares = newsh
        pop.lock = q_b                                  # T+2: mua phiên này, phiên sau chưa bán được
        pop.cool = np.where(capit & isr[None, :], np.round(2 * lam), pop.cool - 1)
        hist = np.concatenate([hist[:, 1:] if hist.shape[1] >= 21 else hist, p_new[:, None]], axis=1)
        ema = ema + (p_new - ema) * (2 / 121)
    out["wr"], out["wl"], out["share_l"], out["fshare"] = wr, wl, share_l, fshare
    if record_agents:
        held = pop.shares > 0
        out["agents"] = pop
    return out


# ---------------- hiệu chỉnh ----------------
def loss_of(theta, D, start, n_free, target, se, M, seed):
    rng = np.random.default_rng(seed)       # cùng hạt giống cho mọi ứng viên (common random numbers)
    o = run(theta, D, start, BURN, n_free, M, rng)
    i0 = start + BURN + 1
    f = D["fnet"][i0:i0 + n_free] / max(D["value"][i0 - 60:i0].mean(), 1)
    ms = moments(o["ret"], o["val"], np.tile(f, (M, 1)))
    mm = ms.mean(axis=0)
    return float((((mm - target) / se) ** 2).sum()), mm


def lhs(rng, n, fixed=None):
    lo = np.array([p[1] for p in PARAMS])
    hi = np.array([p[2] for p in PARAMS])
    u = (rng.permuted(np.tile(np.arange(n), (len(PARAMS), 1)), axis=1).T + rng.random((n, len(PARAMS)))) / n
    th = lo + u * (hi - lo)
    if fixed:
        for kname, v in fixed.items():
            th[:, NAMES.index(kname)] = v
    return th


def calibrate(D, start, n_free, n_cand, M, seed, fixed=None, log=None):
    i0 = start + BURN + 1
    r = D["ret"][i0:i0 + n_free]
    v = D["value"][i0:i0 + n_free] / D["value"][i0 - 60:i0].mean()
    f = D["fnet"][i0:i0 + n_free] / D["value"][i0 - 60:i0].mean()
    target, se = real_moments(r, v, f)
    rng = np.random.default_rng(seed)
    cands = lhs(rng, n_cand, fixed)
    res = []
    for j, th in enumerate(cands):
        L, mm = loss_of(th, D, start, n_free, target, se, M, seed + 1)
        res.append((L, th, mm))
        if log and (j + 1) % 20 == 0:
            log(f"  vòng 1: {j + 1}/{n_cand}")
    res.sort(key=lambda z: z[0])
    # độ xác định của từng tham số: khoảng của 10% bộ tốt nhất vòng 1 (cùng số lần chạy, phủ đều không gian)
    top = np.array([z[1] for z in res[:max(3, len(res) // 10)]])
    # độ nhạy: tương quan hạng (Spearman) giữa giá trị tham số và độ lệch trên mọi ứng viên vòng 1
    Ls = np.argsort(np.argsort([z[0] for z in res]))
    TH = np.array([z[1] for z in res])
    sens = []
    for j in range(len(PARAMS)):
        rk = np.argsort(np.argsort(TH[:, j]))
        sens.append(0.0 if np.std(rk) == 0 else float(np.corrcoef(rk, Ls)[0, 1]))
    lo = np.array([p[1] for p in PARAMS])
    hi = np.array([p[2] for p in PARAMS])
    best = res
    # vòng 2, 3: tinh chỉnh quanh các bộ tốt nhất, bước nhỏ dần, chạy nhiều lần hơn
    n_ref = 0
    for keep, step, mult, sd in ((5, 0.08, 2, 2), (3, 0.03, 3, 3)):
        refined = []
        for _, th0, _ in best[:keep]:
            refined.append(th0)
            for _ in range(6):
                th = np.clip(th0 + rng.normal(0, step, len(PARAMS)) * (hi - lo), lo, hi)
                if fixed:
                    for kname, val in fixed.items():
                        th[NAMES.index(kname)] = val
                refined.append(th)
        best = []
        for th in refined:
            L, mm = loss_of(th, D, start, n_free, target, se, M * mult, seed + sd)
            best.append((L, th, mm))
        best.sort(key=lambda z: z[0])
        n_ref += len(refined) * M * mult
    res2 = best
    return {"best": res2[0][1], "loss": res2[0][0], "sim_moments": res2[0][2], "target": target, "se": se,
            "top_lo": top.min(axis=0), "top_hi": top.max(axis=0), "do_nhay": sens, "n_runs": n_cand * M + n_ref}


def cmd_calibrate(args):
    D = build(args)
    T = len(D["price"])
    log = (lambda s: print(s, file=sys.stderr)) if not args.im else None
    # chỉ dùng đoạn có khối ngoại (nếu có file khối ngoại)
    start = 0
    if args.khoi_ngoai:
        nz = np.nonzero(D["fnet"])[0]
        if len(nz):
            start = max(0, nz[0] - 1)
    n_all = T - start - BURN - 1
    if n_all < 80:
        sys.exit(f"Dữ liệu quá ngắn: còn {n_all} phiên sau {BURN} phiên nạp, cần ≥ 80.")
    n_tr = int(n_all * 0.7)
    n_te = n_all - n_tr
    log and log(f"[{D['ma']}] hiệu chỉnh trên {n_tr} phiên, kiểm tra ngoài mẫu {n_te} phiên")
    seed = args.seed + sum(ord(c) * 31 ** i for i, c in enumerate(D["ma"])) % 10007
    fx = None if D["have_m"] else {"theo_thi_truong": 0.0}
    cal_tr = calibrate(D, start, n_tr, args.ung_vien, args.lan, seed, fixed=fx, log=log)
    null_tr = calibrate(D, start, n_tr, max(20, args.ung_vien // 4), args.lan, seed, fixed=NULL_FIXED)
    # chấm ngoài mẫu: nạp lịch sử tới hết đoạn hiệu chỉnh rồi để giá tự do trên đoạn kiểm tra
    st2 = start + n_tr
    i0 = st2 + BURN + 1
    r = D["ret"][i0:i0 + n_te]
    v = D["value"][i0:i0 + n_te] / D["value"][i0 - 60:i0].mean()
    f = D["fnet"][i0:i0 + n_te] / D["value"][i0 - 60:i0].mean()
    tgt, se = real_moments(r, v, f)
    L_beh, _ = loss_of(cal_tr["best"], D, st2, n_te, tgt, se, args.lan * 3, seed + 9)
    L_null, _ = loss_of(null_tr["best"], D, st2, n_te, tgt, se, args.lan * 3, seed + 9)
    # hiệu chỉnh lại trên toàn bộ để dùng cho kịch bản
    log and log(f"[{D['ma']}] hiệu chỉnh lại trên toàn bộ {n_all} phiên")
    cal = calibrate(D, start, n_all, args.ung_vien, args.lan, seed + 100, fixed=fx, log=log)
    out = {
        "ma": D["ma"], "phien_ban": PHIEN_BAN, "tao_luc": dt.datetime.now().isoformat(timespec="seconds"),
        "du_lieu": {"tu": D["dates"][start].isoformat(), "den": D["dates"][-1].isoformat(), "so_phien": T - start,
                    "co_khoi_ngoai": D["n_foreign"], "co_vnindex": D["have_m"]},
        "tham_so": {k: round(float(v), 4) for k, v in zip(NAMES, cal["best"])},
        "khoang_tot": {k: [round(float(a), 3), round(float(b), 3)] for k, a, b in zip(NAMES, cal["top_lo"], cal["top_hi"])},
        # chưa xác định = độ lệch gần như không đổi khi tham số đổi (|Spearman| < 0,15) VÀ 10% bộ tốt nhất trải rộng
        "chua_xac_dinh": [k for k, a, b, p, r in zip(NAMES, cal["top_lo"], cal["top_hi"], PARAMS, cal["do_nhay"])
                          if (b - a) > 0.4 * (p[2] - p[1]) and abs(r) < 0.15 and not (fx and k in fx)],
        "do_nhay": {k: round(r, 2) for k, r in zip(NAMES, cal["do_nhay"])},
        "y_nghia": {p[0]: p[3] for p in PARAMS},
        "mo_men_that": dict(zip(MOMENTS, np.round(cal["target"], 3).tolist())),
        "mo_men_mo_phong": dict(zip(MOMENTS, np.round(cal["sim_moments"], 3).tolist())),
        "sai_so_chuan": dict(zip(MOMENTS, np.round(cal["se"], 3).tolist())),
        "do_khop": round(cal["loss"], 2),
        "kiem_tra_ngoai_mau": {"phien_hieu_chinh": n_tr, "phien_kiem_tra": n_te,
                               "loss_mo_hinh_hanh_vi": round(L_beh, 2), "loss_mo_hinh_rong": round(L_null, 2),
                               "hanh_vi_tot_hon": bool(L_beh < L_null)},
        "so_lan_chay_hieu_chinh": int(cal["n_runs"] + cal_tr["n_runs"] + null_tr["n_runs"]),
        "ty_trong_nho_le": args.ty_trong_nho_le,
    }
    with open(args.out, "w", encoding="utf-8") as fo:
        json.dump(out, fo, ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("ma", "tham_so", "do_khop", "kiem_tra_ngoai_mau")}, ensure_ascii=False))


# ---------------- kịch bản tương lai ----------------
def scenarios(D, M, n, rng):
    fn = D["fnet"][-120:]
    fn = fn[fn != 0] if np.any(fn) else np.zeros(1)
    def boot():
        idx = rng.integers(0, max(1, len(fn) - 5), M)
        return np.stack([fn[np.minimum(idx + j, len(fn) - 1)] for j in range(n)], axis=1)
    decay = 0.5 ** np.arange(n)
    q10, q90 = np.percentile(fn, 10), np.percentile(fn, 90)
    return {
        "co_so": {"mo_ta": "không có tin lớn; khối ngoại như 120 phiên gần đây", "foreign": boot()},
        "tin_tot": {"mo_ta": "tin tốt riêng của mã (KQKD vượt kỳ vọng, cổ tức...): tâm lý +1 giảm dần, giá trị neo +3%",
                    "foreign": boot(), "news": 1.0 * decay, "fund": 0.03},
        "tin_xau": {"mo_ta": "tin xấu riêng của mã (nợ xấu tăng, KQKD hụt...): tâm lý −1 giảm dần, giá trị neo −3%",
                    "foreign": boot(), "news": -1.0 * decay, "fund": -0.03},
        "khoi_ngoai_ban": {"mo_ta": f"khối ngoại bán ròng mạnh mỗi phiên (mức 10% xấu nhất 120 phiên ≈ {q10 / 1e9:.0f} tỷ)",
                           "foreign": np.full((M, n), min(q10, 0.0))},
        "khoi_ngoai_mua": {"mo_ta": f"khối ngoại mua ròng mạnh mỗi phiên (mức 10% tốt nhất ≈ {q90 / 1e9:.0f} tỷ)",
                           "foreign": np.full((M, n), max(q90, 0.0))},
        "thi_truong_hoang_loan": {"mo_ta": "VN-Index hoảng loạn (tâm lý toàn thị trường −1,5 phiên đầu, khối ngoại bán)",
                                  "foreign": np.full((M, n), min(q10, 0.0)), "news": np.r_[-1.5, -0.75, np.zeros(n - 2)][:n],
                                  "chi_thi_truong": True},
    }


def load_theta(path):
    with open(path, encoding="utf-8") as f:
        j = json.load(f)
    return j, j["tham_so"]


def cmd_scen(args):
    if args.ho_so_ca_nhan:
        sys.exit("Kiểu B (bản sao hành vi cá nhân) chưa làm: cần lịch sử lệnh xuất từ VNDirect. Bỏ --ho-so-ca-nhan.")
    D = build(args)
    meta, th = load_theta(args.tham_so)
    M, n = args.so_lan, args.phien
    rng = np.random.default_rng(args.seed)
    T = len(D["price"])
    start = T - 1 - BURN
    sc = scenarios(D, M, n, rng)
    # đường đi VN-Index cho từng kịch bản (kiểu A)
    mp = {}
    if args.tham_so_thi_truong and args.thi_truong and not D["is_index"]:
        aargs = argparse.Namespace(**{**vars(args), "ma": "VNINDEX", "gia": args.thi_truong, "thi_truong": None})
        DA = build(aargs)
        _, thA = load_theta(args.tham_so_thi_truong)
        TA = len(DA["price"])
        scA = scenarios(DA, M, n, np.random.default_rng(args.seed + 5))
        for name in sc:
            sA = scA["thi_truong_hoang_loan"] if sc[name].get("chi_thi_truong") else scA["co_so"]
            oA = run(thA, DA, TA - 1 - BURN, BURN, n, M, np.random.default_rng(args.seed + 11), scen=sA)
            mp[name] = oA["ret"]
    elif D["have_m"]:
        mr = D["mret"][-250:]
        for name in sc:
            idx = rng.integers(0, len(mr) - n, M)
            base = np.stack([mr[idx + j] for j in range(n)], axis=1)
            if sc[name].get("chi_thi_truong"):
                base[:, 0] += -0.04
                base[:, 1] += -0.02
            mp[name] = base
    p_last = D["price"][-1]
    res = {"ma": D["ma"], "phien_cuoi": D["dates"][-1].isoformat(), "gia_cuoi": float(p_last),
           "so_lan_chay": M, "so_phien": n, "tham_so": th, "kiem_tra_ngoai_mau": meta.get("kiem_tra_ngoai_mau"),
           "chua_xac_dinh": meta.get("chua_xac_dinh", []), "hieu_chinh_luc": meta.get("tao_luc"),
           "kich_ban": {}}
    # trạng thái hiện tại: chạy nạp lịch sử 60 phiên với số lần nhỏ để đọc tâm lý và lãi/lỗ của nhỏ lẻ
    o0 = run(th, D, start, BURN, 1, 400, np.random.default_rng(args.seed + 3), scen=sc["co_so"] | {
        "foreign": sc["co_so"]["foreign"][:400, :1]}, mpaths=(mp["co_so"][:400, :1] if mp else None), record_agents=True)
    pop = o0["agents"]
    held = pop.shares[:, :pop.nr] > 0
    gnow = p_last / pop.cost[:, :pop.nr] - 1
    res["hien_tai"] = {
        "tam_ly_dam_dong": round(float(o0["x"][:, 0].mean()), 3),
        "ty_le_nho_le_dang_lai": round(float(((gnow > 0) & held).sum() / max(held.sum(), 1)), 3),
        "ty_le_nho_le_lo_tren_10pct": round(float(((gnow < -0.10) & held).sum() / max(held.sum(), 1)), 3),
        "gia_von_trung_vi_nho_le": round(float(np.median(pop.cost[:, :pop.nr][held])), 2),
        "ema120": round(float(D["price"][-120:].mean()), 2),
    }
    for name, s in sc.items():
        o = run(th, D, start, BURN, n, M, np.random.default_rng(args.seed + 21), scen=s, mpaths=mp.get(name))
        path = p_last * np.cumprod(1 + o["ret"], axis=1)
        qs = np.percentile(path, [2.5, 10, 25, 50, 75, 90, 97.5], axis=0)
        lim = D["limit"] - 0.006          # trừ một bước giá: giá trần/sàn đã làm tròn xuống bước giá
        sd_ratio = float(o["ret"].std() / max(D["ret"][-120:].std(), 1e-6))
        res["kich_ban"][name] = {
            "mo_ta": s["mo_ta"],
            "bien_dong_so_voi_thuc": round(sd_ratio, 2),
            "vung_gia": {f"phien_{j + 1}": [round(float(q), 2) for q in qs[:, j]] for j in range(n)},
            "xs_tang_sau_n_phien": round(float((path[:, -1] > p_last).mean()), 3),
            "xs_cham_tran": round(float((o["ret"] >= lim).any(axis=1).mean()), 3),
            "xs_cham_san": round(float((o["ret"] <= -lim).any(axis=1).mean()), 3),
            "rong_nho_le_ty_moi_phien": [round(float(v) / 1e9, 1) for v in o["net_r"].mean(0)],
            "rong_lon_ty_moi_phien": [round(float(v) / 1e9, 1) for v in o["net_l"].mean(0)],
            "rong_ngoai_ty_moi_phien": [round(float(v) / 1e9, 1) for v in o["net_f"].mean(0)],
            "tam_ly": [round(float(v), 2) for v in o["x"].mean(0)],
            "nho_le_cat_lo_pct": [round(100 * float(v), 1) for v in o["capit"].mean(0)],
            "PGR_pct": [round(100 * float(v), 1) for v in o["chot_lai"].mean(0)],
            "PLR_pct": [round(100 * float(v), 1) for v in o["gong_lo"].mean(0)],
        }
    with open(args.out, "w", encoding="utf-8") as fo:
        json.dump(res, fo, ensure_ascii=False, indent=1)
    if args.chu:
        print(text(res))
    else:
        print(json.dumps({"ma": res["ma"], "hien_tai": res["hien_tai"]}, ensure_ascii=False))


def text(res):
    L = []
    hn = res["hien_tai"]
    L.append(f"Mô phỏng hành vi {res['ma']} – {res['so_lan_chay']} lần chạy × {res['so_phien']} phiên, từ giá "
             f"{res['gia_cuoi']} (phiên {res['phien_cuoi']}). Mô hình để hiểu hành vi, không phải dự báo chắc chắn.")
    k = res.get("kiem_tra_ngoai_mau") or {}
    if k:
        L.append("- Kiểm tra ngoài mẫu: mô hình hành vi " + ("KHỚP TỐT HƠN" if k.get("hanh_vi_tot_hon") else "KHÔNG tốt hơn")
                 + f" mô hình rỗng (điểm lệch {k['loss_mo_hinh_hanh_vi']} so với {k['loss_mo_hinh_rong']}; càng nhỏ càng khớp).")
    t = res["tham_so"]
    L.append(f"- Hành vi hiệu chỉnh: bầy đàn {t['bay_dan']:.2f} · đuổi xu hướng {t['xu_huong']:.2f} · nhìn VN-Index "
             f"{t['theo_thi_truong']:.2f} · ngại lỗ λ {t['ngai_lo']:.2f} · bán sớm {t['ban_som']:.2f} · NĐT lớn neo giá trị {t['neo_gia_tri']:.2f}"
             + (f" (chưa xác định được từ dữ liệu giá: {', '.join(res['chua_xac_dinh'])})." if res.get("chua_xac_dinh") else "."))
    L.append(f"- Hiện tại (ước từ hồ sơ khối lượng 60 phiên): tâm lý đám đông {hn['tam_ly_dam_dong']:+.2f} (−1 sợ hãi … +1 hưng phấn); "
             f"{hn['ty_le_nho_le_dang_lai'] * 100:.0f}% nhỏ lẻ đang lãi, {hn['ty_le_nho_le_lo_tren_10pct'] * 100:.0f}% lỗ trên 10%; "
             f"giá vốn trung vị nhỏ lẻ {hn['gia_von_trung_vi_nho_le']}, EMA120 {hn['ema120']}.")
    r0 = res["kich_ban"]["co_so"]["bien_dong_so_voi_thuc"]
    if r0 > 1.3 or r0 < 0.7:
        L.append(f"- ⚠ Ở kịch bản cơ sở, biến động mỗi phiên của mô phỏng bằng {r0:.1f} lần thực tế 120 phiên gần đây: "
                 + ("vùng giá dưới đây RỘNG hơn thực tế, đọc như kịch bản căng thẳng." if r0 > 1.3 else "vùng giá dưới đây HẸP hơn thực tế."))
    for name, s in res["kich_ban"].items():
        n = res["so_phien"]
        v = s["vung_gia"][f"phien_{n}"]
        L.append(f"- Kịch bản {name} ({s['mo_ta']}): phiên {n} vùng 80% {v[1]}–{v[5]}, trung vị {v[3]}; "
                 f"xác suất cao hơn giá hiện tại {s['xs_tang_sau_n_phien'] * 100:.0f}%; chạm trần {s['xs_cham_tran'] * 100:.0f}%, "
                 f"chạm sàn {s['xs_cham_san'] * 100:.0f}%. Ròng phiên 1: nhỏ lẻ {s['rong_nho_le_ty_moi_phien'][0]:+.0f} tỷ, "
                 f"lớn {s['rong_lon_ty_moi_phien'][0]:+.0f} tỷ, ngoại {s['rong_ngoai_ty_moi_phien'][0]:+.0f} tỷ; "
                 f"nhỏ lẻ cắt lỗ {max(s['nho_le_cat_lo_pct']):.1f}%/phiên lúc cao nhất; hiệu ứng bán sớm: "
                 f"{np.mean(s['PGR_pct']):.1f}% người đang lãi chốt lời mỗi phiên so với {np.mean(s['PLR_pct']):.1f}% người đang lỗ chịu bán.")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("hieu-chinh", "kich-ban"):
        p = sub.add_parser(name)
        p.add_argument("--ma", required=True)
        p.add_argument("--gia", required=True)
        p.add_argument("--thi-truong")
        p.add_argument("--khoi-ngoai")
        p.add_argument("--bien-do", type=float, default=0.07, help="biên độ sàn (HOSE 0.07, HNX 0.10, UPCoM 0.15)")
        p.add_argument("--ty-trong-nho-le", type=float, default=0.70,
                       help="tỷ trọng giá trị giao dịch của nhóm nhỏ lẻ (mặc định 0,70; còn lại là NĐT lớn + khối ngoại)")
        p.add_argument("--seed", type=int, default=2026)
        p.add_argument("--out", required=True)
        p.add_argument("--im", action="store_true", help="không in tiến độ")
    pc = sub.choices["hieu-chinh"]
    pc.add_argument("--ung-vien", type=int, default=150, help="số bộ tham số thử ở vòng 1")
    pc.add_argument("--lan", type=int, default=8, help="số lần chạy mỗi bộ tham số ở vòng 1 (vòng 2 gấp 3)")
    ps = sub.choices["kich-ban"]
    ps.add_argument("--tham-so", required=True)
    ps.add_argument("--tham-so-thi-truong")
    ps.add_argument("--phien", type=int, default=6)
    ps.add_argument("--so-lan", type=int, default=2000)
    ps.add_argument("--chu", action="store_true")
    ps.add_argument("--ho-so-ca-nhan", help="(kiểu B, chưa làm) file lịch sử lệnh của người dùng")
    a = ap.parse_args()
    (cmd_calibrate if a.cmd == "hieu-chinh" else cmd_scen)(a)


if __name__ == "__main__":
    main()
