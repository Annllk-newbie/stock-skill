#!/usr/bin/env python3
"""Vẽ biểu đồ phân tích: nến, SMA20/50, Bollinger, hỗ trợ/kháng cự, đỉnh/đáy chu kỳ, khối lượng, RSI, MACD,
và vùng dự báo 6 phiên tới (nếu có file kết quả của forecast6.py).

Cách dùng:
    python forecast6.py gia.csv > du_bao.json
    python chart.py gia.csv --du-bao du_bao.json --ma HPG --out hpg.png
    python chart.py gia.csv --chi-chu --du-bao du_bao.json     # chỉ in biểu đồ chữ (cho thông báo điện thoại)

Tùy chọn: --phien 100 (số phiên hiển thị), --toi (nền tối), --khong-chu-ky (ẩn đỉnh/đáy zigzag), --nguong 6 (ngưỡng zigzag %).
Quy ước màu theo thị trường Việt Nam: xanh = tăng, đỏ = giảm. Nến tăng để RỖNG, nến giảm TÔ ĐẶC,
nên vẫn đọc được hướng khi không phân biệt màu.
Nếu không có matplotlib, script tự chuyển sang biểu đồ chữ.
"""
import argparse
import json
import math
import os
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_prices  # noqa: E402
from indicators import ema_series, support_resistance  # noqa: E402
from cycles import zigzag  # noqa: E402

THEMES = {
    "sang": dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#898781", grid="#e1e0d9", axis="#c3c2b7",
                 up="#008300", down="#e34948", s1="#2a78d6", s2="#eb6834", fc="#6250d6", band="#2a78d6"),
    "toi": dict(surface="#1a1a19", ink="#f0efec", ink2="#c3c2b7", muted="#898781", grid="#2c2c2a", axis="#383835",
                up="#0ca30c", down="#e66767", s1="#3987e5", s2="#d95926", fc="#9085e9", band="#3987e5"),
}


# ---------- chỉ báo dạng chuỗi ----------
def sma_series(vals, n):
    out = [None] * len(vals)
    s = 0.0
    for i, v in enumerate(vals):
        s += v
        if i >= n:
            s -= vals[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def bollinger_series(vals, n=20, k=2):
    mid, up, lo = [None] * len(vals), [None] * len(vals), [None] * len(vals)
    for i in range(n - 1, len(vals)):
        w = vals[i - n + 1:i + 1]
        m = sum(w) / n
        sd = math.sqrt(sum((x - m) ** 2 for x in w) / n)
        mid[i], up[i], lo[i] = m, m + k * sd, m - k * sd
    return mid, up, lo


def rsi_series(closes, n=14):
    out = [None] * len(closes)
    if len(closes) <= n:
        return out
    g = [max(closes[i] - closes[i - 1], 0) for i in range(1, len(closes))]
    l = [max(closes[i - 1] - closes[i], 0) for i in range(1, len(closes))]
    ag, al = sum(g[:n]) / n, sum(l[:n]) / n
    out[n] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    for i in range(n, len(g)):
        ag = (ag * (n - 1) + g[i]) / n
        al = (al * (n - 1) + l[i]) / n
        out[i + 1] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def macd_series(closes):
    ef, es = ema_series(closes, 12), ema_series(closes, 26)
    line = [a - b for a, b in zip(ef, es)]
    sig = ema_series(line, 9)
    return line, sig, [a - b for a, b in zip(line, sig)]


# ---------- biểu đồ chữ ----------
def sparkline(vals):
    bars = "▁▂▃▄▅▆▇█"
    lo, hi = min(vals), max(vals)
    if hi == lo:
        return bars[3] * len(vals)
    return "".join(bars[min(7, int((v - lo) / (hi - lo) * 7.999))] for v in vals)


def text_chart(data, fc, ma, n=30):
    closes = [d["close"] for d in data]
    seg = closes[-n:]
    lines = [f"{ma or 'Giá'} {n} phiên gần nhất: {sparkline(seg)}",
             f"  thấp {min(seg):g} · cao {max(seg):g} · đóng cửa {seg[-1]:g} ({data[-1]['date'].isoformat()})"]
    if fc:
        ph = fc.get("du_bao_tung_phien", [])
        if ph:
            lines.append("Dự báo vùng 80% các phiên tới:")
            for p in ph:
                lines.append(f"  P{p['k']} {p['ngay'][5:]}: {p['vung_80'][0]:g} – {p['vung_80'][1]:g} (trung vị {p['trung_vi']:g})")
    return "\n".join(lines)


# ---------- biểu đồ ảnh ----------
def draw(data, fc, args):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    T = THEMES["toi" if args.toi else "sang"]
    n_all = len(data)
    closes_all = [d["close"] for d in data]
    w = min(args.phien, n_all)
    off = n_all - w
    seg = data[off:]
    o = [d["open"] for d in seg]
    h = [d["high"] for d in seg]
    lo = [d["low"] for d in seg]
    c = [d["close"] for d in seg]
    vol = [d["volume"] or 0 for d in seg]
    x = list(range(w))

    sma20 = sma_series(closes_all, 20)[off:]
    sma50 = sma_series(closes_all, 50)[off:]
    bm, bu, bl = [s[off:] for s in bollinger_series(closes_all)]
    rsi = rsi_series(closes_all)[off:]
    mline, msig, mhist = [s[off:] for s in macd_series(closes_all)]
    sr = support_resistance(data, lookback=min(120, n_all))

    ph = (fc or {}).get("du_bao_tung_phien", [])
    nf = len(ph)
    xmax = w - 1 + nf

    fig = plt.figure(figsize=(10, 9.2), facecolor=T["surface"])
    gs = fig.add_gridspec(4, 1, height_ratios=[5, 1.3, 1.4, 1.4], hspace=0.08, left=0.075, right=0.86, top=0.875, bottom=0.07)
    axp = fig.add_subplot(gs[0])
    axv = fig.add_subplot(gs[1], sharex=axp)
    axr = fig.add_subplot(gs[2], sharex=axp)
    axm = fig.add_subplot(gs[3], sharex=axp)
    axes = [axp, axv, axr, axm]

    for ax in axes:
        ax.set_facecolor(T["surface"])
        ax.grid(True, axis="y", color=T["grid"], lw=0.6)
        ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.spines["bottom"].set_color(T["axis"])
        ax.tick_params(colors=T["muted"], labelsize=8, length=0)
        if nf:
            ax.axvspan(w - 0.5, xmax + 0.5, color=T["fc"], alpha=0.05, lw=0)
    for ax in axes[:-1]:
        plt.setp(ax.get_xticklabels(), visible=False)

    # --- giá ---
    axp.fill_between(x, [v if v is not None else float("nan") for v in bl],
                     [v if v is not None else float("nan") for v in bu], color=T["band"], alpha=0.08, lw=0, label="Bollinger 20")
    for i in x:
        up = c[i] >= o[i]
        col = T["up"] if up else T["down"]
        axp.vlines(i, lo[i], h[i], color=col, lw=0.9, zorder=3)
        body = max(abs(c[i] - o[i]), (max(h) - min(lo)) * 0.0015)
        axp.add_patch(Rectangle((i - 0.32, min(o[i], c[i])), 0.64, body,
                                facecolor=T["surface"] if up else col, edgecolor=col, lw=0.9, zorder=4))
    axp.plot(x, [v if v is not None else float("nan") for v in sma20], color=T["s1"], lw=1.6, label="SMA20", zorder=5)
    axp.plot(x, [v if v is not None else float("nan") for v in sma50], color=T["s2"], lw=1.6, label="SMA50", zorder=5)

    # hỗ trợ / kháng cự
    levels = [(z["level"], "KC") for z in sr["resistances_nearest_first"][:2]] + \
             [(z["level"], "HT") for z in sr["supports_nearest_first"][:2]]
    for lv, tag in levels:
        axp.axhline(lv, color=T["muted"], lw=0.9, ls=(0, (5, 4)), zorder=2)
        axp.text(-0.7, lv, f"{tag} {lv:.2f}", color=T["ink2"], fontsize=7, va="bottom", ha="left")

    # đỉnh/đáy chu kỳ
    if not args.khong_chu_ky and n_all >= 60:
        rets = [closes_all[i] / closes_all[i - 1] - 1 for i in range(1, n_all)]
        th = args.nguong / 100 if args.nguong else max(0.03, 2.5 * st.pstdev(rets) * math.sqrt(5))
        pivots, _ = zigzag(closes_all, th)
        for kind, i in pivots:
            j = i - off
            if 0 <= j < w:
                if kind == "dinh":
                    axp.plot(j, h[j] * 1.004, marker="v", color=T["ink2"], ms=6, ls="none", zorder=6)
                else:
                    axp.plot(j, lo[j] * 0.996, marker="^", color=T["ink2"], ms=6, ls="none", zorder=6)

    # vùng dự báo
    if nf:
        xs = [w - 1] + [w - 1 + p["k"] for p in ph]
        base = c[-1]
        med = [base] + [p["trung_vi"] for p in ph]
        for key, alpha in (("vung_80", 0.14), ("vung_50", 0.26)):
            lo_b = [base] + [p[key][0] for p in ph]
            hi_b = [base] + [p[key][1] for p in ph]
            axp.fill_between(xs, lo_b, hi_b, color=T["fc"], alpha=alpha, lw=0, zorder=2)
        axp.plot(xs, med, color=T["fc"], lw=2, zorder=5, label="Dự báo: trung vị")
        axp.plot([], [], color=T["fc"], lw=8, alpha=0.26, label="Vùng 50%")
        axp.plot([], [], color=T["fc"], lw=8, alpha=0.14, label="Vùng 80%")
        last = ph[-1]
        axp.text(xmax + 0.9, last["vung_80"][1], f"{last['vung_80'][1]:g}", color=T["ink2"], fontsize=8, va="center")
        axp.text(xmax + 0.9, last["trung_vi"], f"{last['trung_vi']:g}", color=T["fc"], fontsize=8.5, va="center", fontweight="bold")
        axp.text(xmax + 0.9, last["vung_80"][0], f"{last['vung_80'][0]:g}", color=T["ink2"], fontsize=8, va="center")
    axp.text(w - 1 + 0.8, c[-1], f"{c[-1]:g}", color=T["ink"], fontsize=8.5, va="center", fontweight="bold") if not nf else None

    ymin = min(lo + [p["vung_95"][0] for p in ph]) if nf else min(lo)
    ymax = max(h + [p["vung_95"][1] for p in ph]) if nf else max(h)
    pad = (ymax - ymin) * 0.06
    axp.set_ylim(ymin - pad, ymax + pad)
    axp.set_xlim(-1, xmax + 1.5)
    axp.yaxis.tick_right()
    axp.legend(loc="lower left", bbox_to_anchor=(0, 1.005), fontsize=7.5, ncol=7, frameon=False,
               labelcolor=T["ink2"], handlelength=1.6, columnspacing=1.1, borderaxespad=0)
    if nf:
        axp.text((w - 0.5 + xmax + 0.5) / 2, ymax + pad * 0.55, f"{nf} phiên tới", color=T["fc"], fontsize=7.5,
                 ha="center", va="center")

    # --- khối lượng ---
    vcol = [T["up"] if c[i] >= o[i] else T["down"] for i in x]
    axv.bar(x, vol, color=vcol, width=0.7, alpha=0.75)
    v20 = sma_series([d["volume"] or 0 for d in data], 20)[off:]
    axv.plot(x, [v if v is not None else float("nan") for v in v20], color=T["ink2"], lw=1.1)
    axv.set_ylabel("KL", color=T["muted"], fontsize=8)
    axv.yaxis.tick_right()
    axv.yaxis.set_major_formatter(lambda v, _: f"{v / 1e6:.0f}M")

    # --- RSI ---
    axr.axhspan(30, 70, color=T["grid"], alpha=0.35, lw=0)
    axr.plot(x, [v if v is not None else float("nan") for v in rsi], color=T["s1"], lw=1.4)
    axr.axhline(70, color=T["muted"], lw=0.7, ls=(0, (4, 3)))
    axr.axhline(30, color=T["muted"], lw=0.7, ls=(0, (4, 3)))
    axr.set_ylim(0, 100)
    axr.set_yticks([30, 50, 70])
    axr.set_ylabel("RSI14", color=T["muted"], fontsize=8)
    axr.yaxis.tick_right()

    # --- MACD ---
    mcol = [T["up"] if v >= 0 else T["down"] for v in mhist]
    axm.bar(x, mhist, color=mcol, width=0.7, alpha=0.55)
    axm.plot(x, mline, color=T["s1"], lw=1.3)
    axm.plot(x, msig, color=T["s2"], lw=1.3)
    axm.axhline(0, color=T["axis"], lw=0.8)
    axm.set_ylabel("MACD", color=T["muted"], fontsize=8)
    axm.yaxis.tick_right()

    # --- trục ngày ---
    allx = list(range(xmax + 1))
    lab_dates = [d["date"] for d in seg] + [__import__("datetime").date.fromisoformat(p["ngay"]) for p in ph]
    step = max(1, len(allx) // 8)
    ticks = [t for t in range(0, w, step) if (not nf or t < w - 1 - step * 0.4)]
    if nf:
        ticks += [w - 1, xmax]
    axm.set_xticks(ticks)
    axm.set_xticklabels([lab_dates[i].strftime("%d/%m") for i in ticks], fontsize=8, color=T["muted"])

    # --- tiêu đề ---
    name = args.ma or "Cổ phiếu"
    fig.text(0.075, 0.962, f"{name} · giá đóng cửa {c[-1]:g} ({data[-1]['date'].strftime('%d/%m/%Y')})",
             color=T["ink"], fontsize=13, fontweight="bold", ha="left")
    sub = "Nến rỗng = tăng, nến đặc = giảm · ▲▼ = đáy/đỉnh chu kỳ · KC/HT = kháng cự/hỗ trợ ước lượng"
    if nf:
        l = ph[-1]
        sub = (f"Dự báo {nf} phiên (tới {l['ngay'][8:]}/{l['ngay'][5:7]}): trung vị {l['trung_vi']:g}, "
               f"vùng 80% {l['vung_80'][0]:g}–{l['vung_80'][1]:g}")
    fig.text(0.075, 0.936, sub, color=T["ink2"], fontsize=9, ha="left")
    fig.text(0.075, 0.012, "Thống kê từ dữ liệu quá khứ, không phải khuyến nghị mua/bán. Vùng dự báo không đoán hướng.",
             color=T["muted"], fontsize=7.5, ha="left")

    fig.savefig(args.out, dpi=args.dpi, facecolor=T["surface"])
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path")
    ap.add_argument("--out", default="bieu-do.png")
    ap.add_argument("--du-bao", help="file JSON do forecast6.py tạo ra")
    ap.add_argument("--ma", help="mã cổ phiếu, hiện ở tiêu đề")
    ap.add_argument("--phien", type=int, default=100, help="số phiên quá khứ hiển thị")
    ap.add_argument("--nguong", type=float, help="ngưỡng zigzag %% (mặc định tự tính như cycles.py)")
    ap.add_argument("--khong-chu-ky", action="store_true")
    ap.add_argument("--toi", action="store_true", help="nền tối")
    ap.add_argument("--dpi", type=int, default=140)
    ap.add_argument("--chi-chu", action="store_true", help="chỉ in biểu đồ chữ, không vẽ ảnh")
    args = ap.parse_args()

    data = load_prices(args.csv_path, min_rows=30)
    fc = None
    if args.du_bao:
        try:
            with open(args.du_bao, encoding="utf-8") as f:
                fc = json.load(f)
        except (OSError, ValueError) as e:
            print(f"[cảnh báo] không đọc được {args.du_bao}: {e}", file=sys.stderr)

    if args.chi_chu:
        print(text_chart(data, fc, args.ma))
        return
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        print("[cảnh báo] không có matplotlib (pip install matplotlib --break-system-packages); in biểu đồ chữ thay thế.", file=sys.stderr)
        print(text_chart(data, fc, args.ma))
        return
    draw(data, fc, args)
    print(args.out)
    print(text_chart(data, fc, args.ma))


if __name__ == "__main__":
    main()
