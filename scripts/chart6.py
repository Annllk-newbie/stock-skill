#!/usr/bin/env python3
"""Biểu đồ kỹ thuật 6 PHIÊN GẦN NHẤT, có chú thích ngay trên hình, kèm vùng dự báo 6 phiên tới.

Thay cho bảng số: mọi biến động đáng chú ý được đánh số ①②③ trên nến và giải thích bằng lời ở khung dưới.

Cách dùng:
    python chart6.py gia.csv --ma TCB --du-bao du_bao_6_phien.json --out tcb.png
    python chart6.py gia.csv --ma TCB --du-bao du_bao_6_phien.json --chu     # chỉ in bản chữ (cho thông báo)

Đọc hình:
  - Trục dọc: giá (nghìn đồng/cổ phiếu). Trục ngang: ngày giao dịch (T2..T6 và ngày/tháng).
  - Mỗi nến = 1 phiên. Xanh, rỗng = đóng cửa cao hơn mở cửa; đỏ, đặc = thấp hơn.
    Số đậm trên nến = % thay đổi so với phiên trước và giá đóng cửa. Số nhỏ xám ở hai đầu bóng nến = giá cao nhất / thấp nhất phiên.
  - Đường xanh dương = trung bình 20 phiên (TB20); đường cam = TB50. Nét đứt xám = hỗ trợ/kháng cự.
  - Vùng tím bên phải = 6 phiên tới: mỗi thanh là vùng giá có khả năng khoảng 80%, chấm = mức giữa (trung vị).
    Vùng này đo độ rộng dao động, KHÔNG đoán hướng.
Quy ước màu thị trường Việt Nam: xanh = tăng, đỏ = giảm.
"""
import argparse
import datetime as dt
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_prices  # noqa: E402

try:
    from indicators import support_resistance  # noqa: E402
except Exception:  # pragma: no cover
    support_resistance = None

C = dict(surface="#fcfcfb", ink="#151515", ink2="#4a4946", muted="#8a8984", grid="#e6e5df", axis="#c3c2b7",
         up="#0a8a0a", down="#d83b3a", sma20="#2a78d6", sma50="#e0782f", fc="#6a55d9", sr="#7d7c76",
         note_bg="#f3f2ee")
THU = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
SO = "①②③④⑤⑥⑦⑧⑨"


def vn(x, nd=2):
    return f"{x:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x):
    s = vn(abs(x) * 100, 1)
    return ("+" if x > 0 else "−" if x < 0 else "±") + s + "%"


def sma(vals, n, i):
    if i + 1 < n:
        return None
    return sum(vals[i - n + 1:i + 1]) / n


def ema_list(vals, n):
    k = 2 / (n + 1)
    out, e = [], vals[0]
    for v in vals:
        e = v * k + e * (1 - k)
        out.append(e)
    return out


def rsi_at(closes, n=14):
    if len(closes) <= n:
        return None
    g = [max(closes[i] - closes[i - 1], 0) for i in range(1, len(closes))]
    l = [max(closes[i - 1] - closes[i], 0) for i in range(1, len(closes))]
    ag, al = sum(g[:n]) / n, sum(l[:n]) / n
    for i in range(n, len(g)):
        ag = (ag * (n - 1) + g[i]) / n
        al = (al * (n - 1) + l[i]) / n
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def is_placeholder(data, i):
    d = data[i]
    flat = d["open"] == d["high"] == d["low"] == d["close"]
    same_vol = i > 0 and d["volume"] and d["volume"] == data[i - 1]["volume"]
    return flat and (same_vol or not d["volume"])


def analyse(data, n_show=6):
    closes = [d["close"] for d in data]
    vols = [d["volume"] or 0 for d in data]
    N = len(data)
    idx = list(range(max(1, N - n_show), N))
    rows = []
    for i in idx:
        d = data[i]
        prev = closes[i - 1]
        v20 = sma(vols, 20, i - 1) if i >= 20 else (sum(vols[:i]) / i if i else None)
        hi20 = max(d2["high"] for d2 in data[max(0, i - 20):i]) if i else None
        lo20 = min(d2["low"] for d2 in data[max(0, i - 20):i]) if i else None
        rows.append(dict(i=i, d=d, chg=d["close"] / prev - 1, gap=d["open"] / prev - 1, v20=v20,
                         vr=(d["volume"] / v20) if (v20 and d["volume"]) else None,
                         hi20=hi20, lo20=lo20, tam=is_placeholder(data, i),
                         sma20=sma(closes, 20, i), sma50=sma(closes, 50, i)))
    # ---- chú thích biến động ----
    notes = []
    real = [r for r in rows if not r["tam"]]
    if real:
        up = max(real, key=lambda r: r["chg"])
        dn = min(real, key=lambda r: r["chg"])
        if up["chg"] > 0.005:
            notes.append((up["i"], f"Tăng mạnh nhất trong 6 phiên ({pct(up['chg'])})" +
                          (f", khối lượng gấp {vn(up['vr'], 1)} lần trung bình 20 phiên → lực mua lớn" if up["vr"] and up["vr"] >= 1.3 else "")))
        if dn["chg"] < -0.005:
            notes.append((dn["i"], f"Giảm mạnh nhất trong 6 phiên ({pct(dn['chg'])})" +
                          (f", khối lượng gấp {vn(dn['vr'], 1)} lần trung bình → lực bán lớn" if dn["vr"] and dn["vr"] >= 1.3 else "")))
    for r in real:
        d = r["d"]
        if r["hi20"] and d["close"] > r["hi20"]:
            notes.append((r["i"], f"Đóng cửa {vn(d['close'])} vượt mức cao nhất 20 phiên trước đó ({vn(r['hi20'])})"))
        if r["lo20"] and d["close"] < r["lo20"]:
            notes.append((r["i"], f"Đóng cửa {vn(d['close'])} thủng mức thấp nhất 20 phiên trước đó ({vn(r['lo20'])})"))
        if r["vr"] and r["vr"] >= 1.5 and r["i"] not in (n[0] for n in notes):
            notes.append((r["i"], f"Khối lượng đột biến: {vn(d['volume'] / 1e6, 1)} triệu cp, gấp {vn(r['vr'], 1)} lần trung bình"))
        if abs(r["gap"]) >= 0.015:
            notes.append((r["i"], f"Mở cửa {'tăng' if r['gap'] > 0 else 'giảm'} vọt {pct(r['gap'])} so với giá đóng cửa trước"))
        rng_ = d["high"] - d["low"]
        if rng_ > 0:
            upper = (d["high"] - max(d["open"], d["close"])) / rng_
            lower = (min(d["open"], d["close"]) - d["low"]) / rng_
            if upper >= 0.6:
                notes.append((r["i"], f"Bóng trên dài: lên {vn(d['high'])} rồi bị bán xuống → bên bán chặn ở vùng cao"))
            elif lower >= 0.6:
                notes.append((r["i"], f"Bóng dưới dài: xuống {vn(d['low'])} rồi được mua lên → bên mua đỡ ở vùng thấp"))
        if r["sma20"] and r["i"] > 0:
            p_prev = data[r["i"] - 1]["close"]
            s_prev = sma(closes, 20, r["i"] - 1)
            if s_prev and p_prev < s_prev <= d["close"] or (s_prev and p_prev < s_prev and d["close"] >= r["sma20"]):
                notes.append((r["i"], f"Giá cắt LÊN đường TB20 ({vn(r['sma20'])})"))
            elif s_prev and p_prev > s_prev and d["close"] < r["sma20"]:
                notes.append((r["i"], f"Giá cắt XUỐNG đường TB20 ({vn(r['sma20'])})"))
    for r in rows:
        if r["tam"]:
            notes.append((r["i"], "Dữ liệu TẠM: mới có giá đóng cửa, chưa có giá mở/cao/thấp và khối lượng thật (nến gạch chéo)"))
    # bỏ trùng, giữ thứ tự thời gian, tối đa 7
    seen, uniq = set(), []
    for i, t in sorted(notes, key=lambda x: x[0]):
        if (i, t) not in seen:
            seen.add((i, t))
            uniq.append((i, t))
    uniq = uniq[:7]

    # ---- tóm tắt kỹ thuật bằng lời ----
    last = rows[-1]
    base_i = last["i"] if not last["tam"] else last["i"]
    c = closes[base_i]
    s20, s50 = sma(closes, 20, base_i), sma(closes, 50, base_i)
    tom = []
    first_close = closes[rows[0]["i"] - 1]
    tom.append(f"6 phiên: {vn(first_close)} → {vn(c)} ({pct(c / first_close - 1)}); "
               f"thấp nhất {vn(min(r['d']['low'] for r in rows))}, cao nhất {vn(max(r['d']['high'] for r in rows))}.")
    if s20:
        if s50:
            if c > s20 > s50:
                tr = "giá trên TB20 và TB20 trên TB50 → xu hướng TĂNG ngắn hạn"
            elif c < s20 < s50:
                tr = "giá dưới TB20 và TB20 dưới TB50 → xu hướng GIẢM ngắn hạn"
            else:
                tr = "giá và hai đường trung bình đan xen → chưa có xu hướng rõ (đi ngang)"
            tom.append(f"Xu hướng: TB20 {vn(s20)}, TB50 {vn(s50)}; {tr}.")
        else:
            tom.append(f"Xu hướng: giá {'trên' if c > s20 else 'dưới'} TB20 ({vn(s20)}); chưa đủ 50 phiên để có TB50.")
    rv = rsi_at(closes[:base_i + 1])
    if rv is not None:
        if rv >= 70:
            m = "vùng QUÁ MUA (trên 70): đã tăng nóng, dễ có nhịp điều chỉnh"
        elif rv <= 30:
            m = "vùng QUÁ BÁN (dưới 30): đã giảm sâu, dễ có nhịp hồi"
        elif rv >= 55:
            m = "nghiêng về bên mua"
        elif rv <= 45:
            m = "nghiêng về bên bán"
        else:
            m = "trung tính"
        tom.append(f"RSI14 = {vn(rv, 0)} → {m}.")
    if len(closes) >= 35:
        cl = closes[:base_i + 1]
        line = [a - b for a, b in zip(ema_list(cl, 12), ema_list(cl, 26))]
        sig = ema_list(line, 9)
        hist = [a - b for a, b in zip(line, sig)]
        cross = None
        for k in range(len(hist) - 6, len(hist)):
            if k > 0 and hist[k - 1] < 0 <= hist[k]:
                cross = ("cắt LÊN đường tín hiệu", k)
            elif k > 0 and hist[k - 1] > 0 >= hist[k]:
                cross = ("cắt XUỐNG đường tín hiệu", k)
        txt = f"MACD {'trên' if hist[-1] >= 0 else 'dưới'} đường tín hiệu → đà {'tăng' if hist[-1] >= 0 else 'giảm'}"
        if cross:
            txt += f"; vừa {cross[0]} ngày {data[cross[1]]['date'].strftime('%d/%m')}"
        txt += ", " + ("đà đang mạnh lên" if abs(hist[-1]) > abs(hist[-2]) else "đà đang yếu đi") + "."
        tom.append(txt)
    if any(r["tam"] for r in rows):
        tom.append("Lưu ý: phiên cuối là dữ liệu tạm; chỉ báo tính trên giá đóng cửa tạm đó.")
    return rows, uniq, tom


def text_out(ma, rows, notes, tom, fc):
    ph = (fc or {}).get("du_bao_tung_phien", [])
    out = [f"{ma} – 6 phiên gần nhất:"]
    out.append("  " + " · ".join(f"{r['d']['date'].strftime('%d/%m')} {vn(r['d']['close'])} ({pct(r['chg'])}){'*' if r['tam'] else ''}"
                                 for r in rows))
    out += ["  " + t for t in tom]
    for k, (i, t) in enumerate(notes):
        out.append(f"  {SO[k]} {next(r for r in rows if r['i'] == i)['d']['date'].strftime('%d/%m')}: {t}")
    if ph:
        a, b = ph[0], ph[-1]
        out.append(f"  6 phiên tới (vùng 80%, không đoán hướng): {a['ngay'][8:]}/{a['ngay'][5:7]} {vn(a['vung_80'][0])}–{vn(a['vung_80'][1])}"
                   f" → {b['ngay'][8:]}/{b['ngay'][5:7]} {vn(b['vung_80'][0])}–{vn(b['vung_80'][1])}; mức giữa ~{vn(b['trung_vi'])}")
    if any(r["tam"] for r in rows):
        out.append("  (*) dữ liệu tạm")
    return "\n".join(out)


def draw(data, ma, rows, notes, tom, fc, out, dpi):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from matplotlib.ticker import FuncFormatter

    ph = (fc or {}).get("du_bao_tung_phien", [])
    nR, nF = len(rows), len(ph)
    GAP = 0.9
    xr = list(range(nR))
    xf = [nR - 1 + GAP + k for k in range(1, nF + 1)]
    xmax = xf[-1] if nF else nR - 1

    fig = plt.figure(figsize=(12, 11), facecolor=C["surface"])
    gs = fig.add_gridspec(3, 1, height_ratios=[5.2, 1.5, 3.4], hspace=0.14,
                          left=0.085, right=0.88, top=0.895, bottom=0.03)
    ax = fig.add_subplot(gs[0])
    axv = fig.add_subplot(gs[1], sharex=ax)
    axn = fig.add_subplot(gs[2])
    axn.axis("off")

    for a in (ax, axv):
        a.set_facecolor(C["surface"])
        a.grid(True, axis="y", color=C["grid"], lw=0.7)
        a.set_axisbelow(True)
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
        a.spines["left"].set_color(C["axis"])
        a.spines["bottom"].set_color(C["axis"])
        a.tick_params(colors=C["ink2"], labelsize=9, length=3)
        if nF:
            a.axvspan(nR - 1 + GAP / 2 + 0.05, xmax + 0.6, color=C["fc"], alpha=0.06, lw=0)

    lows = [r["d"]["low"] for r in rows] + ([p["vung_80"][0] for p in ph] if nF else [])
    highs = [r["d"]["high"] for r in rows] + ([p["vung_80"][1] for p in ph] if nF else [])
    ymin, ymax = min(lows), max(highs)
    span = ymax - ymin or 1
    ylo, yhi = ymin - span * 0.22, ymax + span * 0.30

    # hỗ trợ / kháng cự
    if support_resistance:
        try:
            sr = support_resistance(data, lookback=min(120, len(data)))
            lv = [(z["level"], "Kháng cự") for z in sr.get("resistances_nearest_first", [])[:1]] + \
                 [(z["level"], "Hỗ trợ") for z in sr.get("supports_nearest_first", [])[:1]]
            for v, tag in lv:
                if ylo < v < yhi:
                    ax.axhline(v, color=C["sr"], lw=1, ls=(0, (6, 4)), zorder=1)
                    ax.text(xmax + 0.75, v, f"{tag}\n{vn(v)}", color=C["sr"], fontsize=8.5, va="center", ha="left")
        except Exception:
            pass

    # đường trung bình
    for key, col, lab in (("sma20", C["sma20"], "TB20"), ("sma50", C["sma50"], "TB50")):
        ys = [r[key] for r in rows]
        if all(y is not None for y in ys):
            ax.plot(xr, ys, color=col, lw=2, zorder=2, alpha=0.9)
            ax.text(-0.75, ys[0], f"{lab} {vn(ys[0])}", color=col, fontsize=8.5, ha="right", va="center", fontweight="bold")

    # nến + chú thích
    note_idx = {}
    for k, (i, _) in enumerate(notes):
        note_idx.setdefault(i, []).append(SO[k])
    for x, r in zip(xr, rows):
        d = r["d"]
        upc = r["chg"] >= 0
        col = C["up"] if r["chg"] >= 0 else C["down"]
        ax.vlines(x, d["low"], d["high"], color=col, lw=1.6, zorder=3)
        body = max(abs(d["close"] - d["open"]), span * 0.006)
        ax.add_patch(Rectangle((x - 0.28, min(d["open"], d["close"])), 0.56, body,
                               facecolor=C["surface"] if upc else col, edgecolor=col, lw=1.6, zorder=4,
                               hatch="///" if r["tam"] else None))
        ax.text(x + 0.31, d["high"], vn(d["high"]), color=C["muted"], fontsize=7.5, va="center", ha="left")
        ax.text(x + 0.31, d["low"], vn(d["low"]), color=C["muted"], fontsize=7.5, va="center", ha="left")
        ax.text(x, d["high"] + span * 0.05, f"{pct(r['chg'])}\n{vn(d['close'])}", color=col, fontsize=10,
                fontweight="bold", ha="center", va="bottom", linespacing=1.15)
        if r["tam"]:
            ax.text(x, d["low"] - span * 0.04, "dữ liệu\ntạm", color=C["muted"], fontsize=8, ha="center", va="top", style="italic")
        if r["i"] in note_idx:
            ax.text(x, d["high"] + span * 0.205, " ".join(note_idx[r["i"]]), color=C["ink"], fontsize=13,
                    ha="center", va="bottom")

    # dự báo
    if nF:
        last_c = rows[-1]["d"]["close"]
        ax.plot([xr[-1], xf[0]], [last_c, ph[0]["trung_vi"]], color=C["fc"], lw=1, ls=":", zorder=2)
        for x, p in zip(xf, ph):
            lo, hi = p["vung_80"]
            ax.add_patch(Rectangle((x - 0.22, lo), 0.44, hi - lo, facecolor=C["fc"], alpha=0.22, lw=0, zorder=2))
            ax.plot(x, p["trung_vi"], "o", color=C["fc"], ms=5, zorder=3)
        ax.plot(xf, [p["trung_vi"] for p in ph], color=C["fc"], lw=1.4, zorder=3)
        for k in (0, nF - 1):
            p, x = ph[k], xf[k]
            ax.text(x, p["vung_80"][1] + span * 0.015, vn(p["vung_80"][1]), color=C["fc"], fontsize=8.5, ha="center", va="bottom")
            ax.text(x, p["vung_80"][0] - span * 0.015, vn(p["vung_80"][0]), color=C["fc"], fontsize=8.5, ha="center", va="top")
        ax.text((xf[0] + xf[-1]) / 2, yhi - span * 0.03, "6 PHIÊN TỚI\nthanh tím = vùng giá có khả năng ~80%\n(đo độ rộng dao động, không đoán hướng)",
                color=C["fc"], fontsize=8.5, ha="center", va="top", linespacing=1.3)
    ax.text((xr[0] + xr[-1]) / 2, yhi - span * 0.03, "6 PHIÊN VỪA QUA", color=C["ink2"], fontsize=9,
            ha="center", va="top", fontweight="bold")

    ax.set_ylim(ylo, yhi)
    ax.set_xlim(-1.5, xmax + 0.6)
    ax.set_ylabel("Giá (nghìn đồng / cổ phiếu)", color=C["ink2"], fontsize=10)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: vn(v)))
    plt.setp(ax.get_xticklabels(), visible=False)

    # khối lượng
    vols = [(r["d"]["volume"] or 0) / 1e6 for r in rows]
    vcol = [C["up"] if r["chg"] >= 0 else C["down"] for r in rows]
    bars = axv.bar(xr, vols, color=vcol, width=0.56, alpha=0.8)
    for b, r in zip(bars, rows):
        if r["tam"]:
            b.set_hatch("///")
            b.set_alpha(0.35)
    vmax = max(vols) if vols else 1
    for x, v, r in zip(xr, vols, rows):
        axv.text(x, v + vmax * 0.04, ("?" if r["tam"] else vn(v, 1)), ha="center", va="bottom", fontsize=8.5, color=C["ink2"])
    v20 = rows[-1]["v20"]
    if v20:
        axv.axhline(v20 / 1e6, color=C["ink2"], lw=1, ls=(0, (4, 3)))
        axv.text(xr[-1] + 0.45, v20 / 1e6, f"TB 20 phiên\n{vn(v20 / 1e6, 1)} tr", fontsize=8, color=C["ink2"], va="center")
    axv.set_ylim(0, vmax * 1.35)
    axv.set_ylabel("Khối lượng\n(triệu cổ phiếu)", color=C["ink2"], fontsize=9)
    axv.yaxis.set_major_formatter(FuncFormatter(lambda v, _: vn(v, 0)))

    ticks = xr + xf
    labs = [f"{THU[r['d']['date'].weekday()]}\n{r['d']['date'].strftime('%d/%m')}" for r in rows]
    for p in ph:
        dd = dt.date.fromisoformat(p["ngay"])
        labs.append(f"{THU[dd.weekday()]}\n{dd.strftime('%d/%m')}")
    axv.set_xticks(ticks)
    axv.set_xticklabels(labs, fontsize=9)
    for t in axv.get_xticklabels()[nR:]:
        t.set_color(C["fc"])
    axv.set_xlabel("Ngày giao dịch", color=C["ink2"], fontsize=9.5)

    # khung chú thích
    axn.add_patch(Rectangle((0, 0), 1, 1, transform=axn.transAxes, facecolor=C["note_bg"], edgecolor=C["grid"], lw=0.8))
    axn.text(0.015, 0.95, "Tóm tắt kỹ thuật", fontsize=10.5, fontweight="bold", color=C["ink"], va="top", transform=axn.transAxes)
    y = 0.86
    import textwrap
    for t in tom:
        for j, ln in enumerate(textwrap.wrap(t, 60)):
            axn.text(0.015, y, ("• " if j == 0 else "  ") + ln, fontsize=8.8, color=C["ink2"], va="top", transform=axn.transAxes)
            y -= 0.068
    axn.text(0.5, 0.95, "Các biến động được đánh số trên hình", fontsize=10.5, fontweight="bold", color=C["ink"], va="top",
             transform=axn.transAxes)
    y = 0.86
    for k, (i, t) in enumerate(notes):
        day = next(r for r in rows if r["i"] == i)["d"]["date"].strftime("%d/%m")
        for j, ln in enumerate(textwrap.wrap(f"{day}: {t}", 66)):
            axn.text(0.5, y, (SO[k] + " " if j == 0 else "    ") + ln, fontsize=8.8, color=C["ink2"], va="top", transform=axn.transAxes)
            y -= 0.068
    if not notes:
        axn.text(0.5, 0.80, "Không có biến động nổi bật trong 6 phiên.", fontsize=8.8, color=C["ink2"], va="top", transform=axn.transAxes)

    last = rows[-1]["d"]
    fig.text(0.085, 0.962, f"{ma} – biểu đồ kỹ thuật 6 phiên gần nhất · đóng cửa {vn(last['close'])} ngày {last['date'].strftime('%d/%m/%Y')}",
             fontsize=14, fontweight="bold", color=C["ink"])
    fig.text(0.085, 0.94, "Nến xanh rỗng = giá tăng so với phiên trước, nến đỏ đặc = giảm. Số đậm trên nến: % thay đổi và giá đóng cửa. "
             "Số xám nhỏ: giá cao/thấp nhất phiên.", fontsize=9, color=C["ink2"])
    fig.text(0.085, 0.924, "Đường xanh dương = trung bình 20 phiên (TB20), cam = TB50, nét đứt = hỗ trợ/kháng cự. "
             "Thống kê tham khảo, không phải khuyến nghị mua/bán.", fontsize=9, color=C["ink2"])
    fig.savefig(out, dpi=dpi, facecolor=C["surface"])
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path")
    ap.add_argument("--ma", default="Cổ phiếu")
    ap.add_argument("--du-bao", help="file JSON của forecast6.py")
    ap.add_argument("--out", default="bieu-do-6-phien.png")
    ap.add_argument("--phien", type=int, default=6)
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--chu", action="store_true", help="chỉ in bản chữ")
    args = ap.parse_args()
    data = load_prices(args.csv_path, min_rows=args.phien + 2)
    fc = None
    if args.du_bao:
        try:
            with open(args.du_bao, encoding="utf-8") as f:
                fc = json.load(f)
        except (OSError, ValueError) as e:
            print(f"[cảnh báo] không đọc được {args.du_bao}: {e}", file=sys.stderr)
    rows, notes, tom = analyse(data, args.phien)
    if not args.chu:
        try:
            draw(data, args.ma, rows, notes, tom, fc, args.out, args.dpi)
            print(args.out)
        except ImportError:
            print("[cảnh báo] thiếu matplotlib (pip install matplotlib --break-system-packages); chỉ in bản chữ.", file=sys.stderr)
    print(text_out(args.ma, rows, notes, tom, fc))


if __name__ == "__main__":
    main()
