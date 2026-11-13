#!/usr/bin/env python3
"""Kiểm định thống kê: tách tín hiệu thật khỏi trùng hợp ngẫu nhiên.

Bốn lệnh con, mỗi lệnh trả JSON (thêm --chu để in thêm 2–4 dòng kết luận dán thẳng vào báo cáo):

  chu-ky   Chu kỳ đo được có đều hơn giá đi ngẫu nhiên không?
           python kiem_dinh.py chu-ky gia.csv [--threshold 6] [--benchmark vnindex.csv] [--n 400]
  su-kien  Mỗi nhóm sự kiện có trùng đỉnh/đáy nhiều hơn tình cờ không? (hoán vị + sửa lỗi so sánh nhiều lần)
           python kiem_dinh.py su-kien gia.csv --su-kien su-kien.csv [--window 3] [--n 2000]
  du-bao   Vùng 80% có thật sự phủ ~80% không, tính trên các dự báo KHÔNG chồng lấn; kịch bản có hơn đoán bừa không?
           python kiem_dinh.py du-bao gia.csv --lich-su du-bao-6-phien.json [--kich-ban 5 3] [--tin-hieu du_bao_6_phien.json]
  fdr      Sửa lỗi so sánh nhiều lần (Benjamini–Hochberg) cho một loạt giá trị p, hoặc cho các hệ số
           tương quan mà ap_luc_von_ngoai.py báo (dạng tuong_quan:so_diem).
           python kiem_dinh.py fdr DXY=0.03 loi_suat_my=0.20 ETF=0.04
           python kiem_dinh.py fdr DXY=-0.35:60 ETF=-0.12:60 ty_gia=0.05:60

Vì sao cần: giá đi ngẫu nhiên cũng tạo ra "chu kỳ" trông rất thật; thử 10 loại sự kiện thì trung bình
1 loại "trùng" đỉnh/đáy chỉ do may; và dự báo lập mỗi ngày cho 6 phiên tới chồng lấn nhau nên 30 phiên
chấm thực chất chỉ là khoảng 5 lần thử độc lập.
"""
import argparse
import csv
import json
import math
import os
import random
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_prices, parse_date, percentile, r  # noqa: E402
from cycles import zigzag  # noqa: E402


# ---------- công cụ thống kê ----------
def p_value(count_extreme, n):
    """p theo hoán vị, cộng 1 để không bao giờ báo p = 0."""
    return (count_extreme + 1) / (n + 1)


def bh(pvals):
    """Benjamini–Hochberg. Nhận dict tên -> p, trả dict tên -> q."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    q, prev = {}, 1.0
    for rank in range(m, 0, -1):
        name, p = items[rank - 1]
        prev = min(prev, p * m / rank)
        q[name] = min(1.0, prev)
    return q


def binom_pmf(k, n, p):
    return math.comb(n, k) * p ** k * (1 - p) ** (n - k)


def binom_two_sided(k, n, p):
    """Kiểm định nhị thức chính xác hai phía."""
    if n == 0:
        return None
    pk = binom_pmf(k, n, p)
    return min(1.0, sum(binom_pmf(i, n, p) for i in range(n + 1) if binom_pmf(i, n, p) <= pk * (1 + 1e-9)))


def binom_greater(k, n, p):
    """P(X >= k) – một phía, dùng khi hỏi 'có hơn mức cơ sở không'."""
    if n == 0:
        return None
    return min(1.0, sum(binom_pmf(i, n, p) for i in range(k, n + 1)))


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return [r(max(0, c - h) * 100, 1), r(min(1, c + h) * 100, 1)]


def default_threshold(closes):
    rets = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    return max(0.03, 2.5 * st.pstdev(rets) * math.sqrt(5))  # giống cycles.py


def cycle_lengths(pivots):
    tr = [i for k, i in pivots if k == "day"]
    pk = [i for k, i in pivots if k == "dinh"]
    return [b - a for a, b in zip(tr, tr[1:])] + [b - a for a, b in zip(pk, pk[1:])]


def cv(vals):
    if len(vals) < 4:
        return None
    m = st.mean(vals)
    return st.pstdev(vals) / m if m else None


def window_hits(pivots):
    """Đi tiến theo thời gian: mỗi pha, lấy tứ phân vị 25–75% độ dài 12 pha cùng loại trước đó làm 'cửa sổ',
    xem pha đó có kết thúc trong cửa sổ không. Trả (số trúng, số thử)."""
    phases = [(k1, i2 - i1) for (k1, i1), (_, i2) in zip(pivots, pivots[1:])]
    hits = tries = 0
    for j, (kind, ln) in enumerate(phases):
        prev = [l for k, l in phases[:j] if k == kind][-12:]
        if len(prev) < 6:
            continue
        lo, hi = percentile(prev, 25), percentile(prev, 75)
        tries += 1
        hits += lo <= ln <= hi
    return hits, tries


def block_bootstrap(rets, rng, mean_block=10):
    """Bootstrap khối dừng (Politis–Romano): giữ cụm biến động và quán tính ngắn hạn,
    nhưng phá mọi nhịp lặp dài hơn vài tuần. Đây là 'thị trường không có chu kỳ' để so sánh."""
    n = len(rets)
    out, i = [], rng.randrange(n)
    pnew = 1 / mean_block
    while len(out) < n:
        out.append(rets[i])
        i = rng.randrange(n) if rng.random() < pnew else (i + 1) % n
    return out


def rebuild(c0, rets):
    px = [c0]
    for x in rets:
        px.append(px[-1] * math.exp(x))
    return px


# ---------- 1. chu kỳ ----------
def cmd_chu_ky(a):
    data = load_prices(a.csv_path, min_rows=120)
    closes = [d["close"] for d in data]
    th = a.threshold / 100 if a.threshold else default_threshold(closes)
    lr = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    piv, _ = zigzag(closes, th)
    lens = cycle_lengths(piv)
    obs_cv, obs_n = cv(lens), len(piv)
    obs_hit = window_hits(piv)
    rng = random.Random(a.seed)

    sur_cv, sur_n, sur_hit_rate = [], [], []
    for _ in range(a.n):
        px = rebuild(closes[0], block_bootstrap(lr, rng, a.block))
        p2, _ = zigzag(px, th)
        c2 = cv(cycle_lengths(p2))
        if c2 is not None:
            sur_cv.append(c2)
        sur_n.append(len(p2))
        h, t = window_hits(p2)
        if t:
            sur_hit_rate.append(h / t)

    out = {"so_phien": len(data), "nguong_dao_chieu_pct": r(th * 100), "so_dinh_day": obs_n,
           "so_mau_ngau_nhien": a.n, "do_dai_khoi_bootstrap_tb": a.block}
    if obs_cv is None or len(sur_cv) < 50:
        out["ket_luan"] = "không đủ đỉnh/đáy để kiểm định (cần ≥ 4 chu kỳ)"
        out["muc"] = "khong_du_mau"
    else:
        p = p_value(sum(c <= obs_cv for c in sur_cv), len(sur_cv))
        out["do_deu"] = {
            "he_so_bien_thien_thuc": r(obs_cv, 3),
            "he_so_bien_thien_ngau_nhien_trung_vi": r(percentile(sur_cv, 50), 3),
            "khoang_90pct_ngau_nhien": [r(percentile(sur_cv, 5), 3), r(percentile(sur_cv, 95), 3)],
            "p": r(p, 4),
            "giai_thich": "p = tỷ lệ chuỗi ngẫu nhiên (cùng biến động, không có chu kỳ) có độ dài chu kỳ đều bằng hoặc hơn chuỗi thật.",
        }
        out["muc"] = "co_co_so" if p < 0.05 else "goi_y_yeu" if p < 0.2 else "khong_khac_ngau_nhien"
        out["ket_luan"] = {
            "co_co_so": "Chu kỳ đều hơn hẳn giá đi ngẫu nhiên: có cơ sở để dùng cửa sổ đảo chiều.",
            "goi_y_yeu": "Chu kỳ chỉ đều hơn ngẫu nhiên một chút: dùng cửa sổ đảo chiều như gợi ý, không làm căn cứ chính.",
            "khong_khac_ngau_nhien": ("Chu kỳ KHÔNG đều hơn giá đi ngẫu nhiên: nhịp lên xuống quan sát được là đặc tính "
                                      "chung của mọi chuỗi giá. Không dùng cửa sổ đảo chiều để dự báo thời điểm."),
        }[out["muc"]]
    out["so_dinh_day_ngau_nhien_trung_vi"] = r(percentile(sur_n, 50), 0)
    if obs_hit[1]:
        out["cua_so_dao_chieu"] = {
            "ty_le_trung_thuc_pct": r(obs_hit[0] / obs_hit[1] * 100, 1), "so_lan_thu": obs_hit[1],
            "ty_le_trung_tren_chuoi_ngau_nhien_pct": r(percentile(sur_hit_rate, 50) * 100, 1) if sur_hit_rate else None,
            "giai_thich": ("Cửa sổ 25–75% trúng khoảng một nửa số lần ngay cả trên chuỗi ngẫu nhiên. "
                           "Chỉ khi tỷ lệ thực cao hơn rõ con số ngẫu nhiên thì cửa sổ mới mang thông tin."),
        }
    if a.benchmark:
        out["dong_pha_voi_chi_so"] = benchmark_sync(data, piv, a.benchmark, th, a.window, rng)
    if a.chu:
        print_chu_ky(out)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


def benchmark_sync(data, piv, bench_path, th, w, rng, n=2000):
    bdata = load_prices(bench_path, min_rows=60)
    bmap = {d["date"]: d["close"] for d in bdata}
    idx = [i for i, d in enumerate(data) if d["date"] in bmap]
    if len(idx) < 120:
        return {"ket_luan": "chỉ số trùng ngày với cổ phiếu quá ít để so"}
    pos = {i: j for j, i in enumerate(idx)}
    bclose = [bmap[data[i]["date"]] for i in idx]
    bth = max(0.02, default_threshold(bclose))
    bp, _ = zigzag(bclose, bth)
    bset = [j for _, j in bp]
    sp = [pos[i] for _, i in piv if i in pos]
    L = len(idx)

    def matched(points):
        return sum(any(abs(s - b) <= w for b in bset) for s in points)

    obs = matched(sp)
    perm = []
    for _ in range(n):
        off = rng.randrange(L)
        perm.append(matched([(s + off) % L for s in sp]))
    p = p_value(sum(x >= obs for x in perm), n)
    exp = st.mean(perm)
    return {"dinh_day_trung_voi_chi_so": obs, "tren_tong": len(sp), "ky_vong_neu_ngau_nhien": r(exp, 1),
            "p": r(p, 4),
            "ket_luan": ("Phần lớn đỉnh/đáy đi cùng chỉ số: nguyên nhân nhiều khả năng ở cấp thị trường, không riêng mã này."
                         if p < 0.05 and obs > 1.5 * exp else
                         "Đỉnh/đáy không trùng chỉ số nhiều hơn tình cờ: cần tìm nguyên nhân riêng của mã.")}


def print_chu_ky(o):
    print("# Kết luận kiểm định chu kỳ", file=sys.stderr)
    dd = o.get("do_deu")
    if dd:
        print(f"- Độ đều chu kỳ: hệ số biến thiên {dd['he_so_bien_thien_thuc']} so với {dd['he_so_bien_thien_ngau_nhien_trung_vi']} "
              f"của chuỗi ngẫu nhiên (p = {dd['p']}). {o['ket_luan']}", file=sys.stderr)
    else:
        print(f"- {o['ket_luan']}", file=sys.stderr)
    cs = o.get("cua_so_dao_chieu")
    if cs:
        print(f"- Cửa sổ đảo chiều trúng {cs['ty_le_trung_thuc_pct']}% ({cs['so_lan_thu']} lần), "
              f"chuỗi ngẫu nhiên trúng {cs['ty_le_trung_tren_chuoi_ngau_nhien_pct']}%.", file=sys.stderr)
    bs = o.get("dong_pha_voi_chi_so")
    if bs and "p" in bs:
        print(f"- {bs['dinh_day_trung_voi_chi_so']}/{bs['tren_tong']} đỉnh/đáy trùng chỉ số (tình cờ ~{bs['ky_vong_neu_ngau_nhien']}, "
              f"p = {bs['p']}). {bs['ket_luan']}", file=sys.stderr)


# ---------- 2. sự kiện ----------
def read_events(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            ds = row.get("date") or row.get("ngay")
            grp = row.get("group") or row.get("nhom") or "khong_nhom"
            if not ds:
                continue
            try:
                rows.append((parse_date(ds), grp))
            except ValueError:
                continue
    return rows


def cmd_su_kien(a):
    data = load_prices(a.csv_path, min_rows=120)
    closes = [d["close"] for d in data]
    dates = [d["date"] for d in data]
    th = a.threshold / 100 if a.threshold else default_threshold(closes)
    piv, _ = zigzag(closes, th)
    pidx = [i for _, i in piv]
    pkind = {i: k for k, i in piv}
    L = len(data)
    w = a.window

    def to_idx(d):
        for i, x in enumerate(dates):
            if x >= d:
                return i
        return None

    groups = {}
    for d, g in read_events(a.su_kien):
        if dates[0] <= d <= dates[-1]:
            i = to_idx(d)
            if i is not None:
                groups.setdefault(g, set()).add(i)

    def hits(ev):
        return sum(any(-w <= p - e <= w for p in pidx) for e in ev)

    def hits_before(ev):  # đỉnh/đáy xảy ra cùng phiên hoặc SAU sự kiện (sự kiện có thể là nguyên nhân)
        return sum(any(0 <= p - e <= w for p in pidx) for e in ev)

    # khoảng cách tới đỉnh/đáy gần nhất của từng phiên (giới hạn 15 phiên để vài sự kiện xa không lấn át)
    dist = [min(15, min(abs(i - p) for p in pidx)) if pidx else 15 for i in range(L)]

    def mean_dist(ev):
        return sum(dist[e] for e in ev) / len(ev)

    rng = random.Random(a.seed)
    res, pvals = {}, {}
    for g, evs in groups.items():
        ev = sorted(evs)
        obs = hits(ev)
        obs_d = mean_dist(ev)
        perm, perm_d = [], []
        for _ in range(a.n):
            off = rng.randrange(L)
            sh = [(e + off) % L for e in ev]  # dịch cả nhóm: giữ khoảng cách giữa các lần (vd. hằng tháng)
            perm.append(hits(sh))
            perm_d.append(mean_dist(sh))
        # thống kê chính: khoảng cách trung bình tới đỉnh/đáy gần nhất (nhạy hơn đếm trùng khi đỉnh/đáy dày)
        p = p_value(sum(x <= obs_d for x in perm_d), a.n)
        exp = st.mean(perm)
        covered = sum(any(abs(pp - e) <= w for e in ev) for pp in pidx)
        loai = {"dinh": 0, "day": 0}
        for e in ev:
            for pp in pidx:
                if abs(pp - e) <= w:
                    loai[pkind[pp]] += 1
                    break
        res[g] = {"so_lan_su_kien": len(ev), "so_lan_trung": obs, "ky_vong_neu_tinh_co": r(exp, 2),
                  "he_so_nang": r(obs / exp, 2) if exp else None,
                  "trung_ma_dinh_day_den_sau": hits_before(ev),
                  "trung_dinh": loai["dinh"], "trung_day": loai["day"],
                  "do_trung_pct": r(obs / len(ev) * 100, 1),
                  "do_bao_phu_pct": r(covered / len(pidx) * 100, 1) if pidx else None,
                  "khoang_cach_tb_toi_dinh_day_phien": r(obs_d, 2),
                  "khoang_cach_tb_neu_tinh_co_phien": r(st.mean(perm_d), 2),
                  "p": r(p, 4)}
        pvals[g] = p
    qs = bh(pvals) if pvals else {}
    for g, v in res.items():
        v["q_sau_sua_nhieu_lan"] = r(qs[g], 4)
        n, q = v["so_lan_su_kien"], qs[g]
        if v["p"] > 0.5:
            v["muc_lien_ket_thong_ke"] = "khong_lien_quan"
        elif n >= 4 and q < 0.05:
            v["muc_lien_ket_thong_ke"] = "manh"
        elif n >= 4 and q < 0.10:
            v["muc_lien_ket_thong_ke"] = "vua"
        else:
            v["muc_lien_ket_thong_ke"] = "yeu"
        if n < 4:
            v["ghi_chu"] = "Dưới 4 lần: không đủ mẫu để khác tình cờ, tối đa 'yếu' dù trùng hết."
    out = {"nguong_dao_chieu_pct": r(th * 100), "cua_so_phien": w, "so_dinh_day": len(pidx),
           "ty_le_phien_nam_trong_cua_so_quanh_dinh_day_pct": r(
               sum(any(abs(i - p) <= w for p in pidx) for i in range(L)) / L * 100, 1),
           "so_nhom_da_thu": len(res),
           "giai_thich": ("p: xác suất trùng nhiều như vậy nếu dịch cả nhóm sự kiện sang thời điểm ngẫu nhiên. "
                          "q: p đã sửa vì thử nhiều nhóm cùng lúc (Benjamini–Hochberg). Kiểm định dựa trên "
                          "khoảng cách trung bình tới đỉnh/đáy gần nhất. 'Mạnh' cần q < 0,05 và ≥ 4 lần; 'vừa' q < 0,10. Mức thống kê là trần: thiếu cơ chế giải thích thì hạ thêm."),
           "nhom": dict(sorted(res.items(), key=lambda kv: kv[1]["p"]))}
    if a.chu:
        print("# Kết luận kiểm định sự kiện", file=sys.stderr)
        print(f"- {out['ty_le_phien_nam_trong_cua_so_quanh_dinh_day_pct']}% số phiên nằm sát một đỉnh/đáy (±{w} phiên): "
              f"đây là mức trùng do tình cờ.", file=sys.stderr)
        for g, v in out["nhom"].items():
            print(f"- {g}: trùng {v['so_lan_trung']}/{v['so_lan_su_kien']} (tình cờ ~{v['ky_vong_neu_tinh_co']}), "
                  f"q = {v['q_sau_sua_nhieu_lan']} → {v['muc_lien_ket_thong_ke']}", file=sys.stderr)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


# ---------- 3. dự báo ----------
def cmd_du_bao(a):
    out = {}
    if a.lich_su:
        data = load_prices(a.csv_path, min_rows=10)
        dates = [d["date"].isoformat() for d in data]
        closes = [d["close"] for d in data]
        with open(a.lich_su, encoding="utf-8") as f:
            hist = json.load(f)
        done = []
        for fc in hist.get("du_bao", []):
            base = fc.get("lam_vao_ngay")
            if base not in dates:
                continue
            ib = dates.index(base)
            ph = fc["phien"]
            h = max(p["k"] for p in ph)
            if ib + h > len(data) - 1:
                continue
            res = [(p["k"], p["vung_80"][0] <= closes[ib + p["k"]] <= p["vung_80"][1]) for p in ph]
            done.append((ib, h, base, res))
        all_n = sum(len(x[3]) for x in done)
        all_k = sum(sum(v for _, v in x[3]) for x in done)
        # chọn các dự báo không chồng lấn: lần sau lập sau khi lần trước đã hết 6 phiên
        indep, last_end = [], -1
        for ib, h, base, res in sorted(done):
            if ib >= last_end:
                indep.append((base, res))
                last_end = ib + h
        k_last = sum(dict(res)[max(dict(res))] for _, res in indep)
        n_ind = len(indep)
        cov = {"so_du_bao_da_het_han": len(done),
               "so_phien_da_cham_moi_du_bao": all_n,
               "ty_le_trong_vung_80_moi_phien_pct": r(all_k / all_n * 100, 1) if all_n else None,
               "so_du_bao_doc_lap": n_ind,
               "ngay_lap_du_bao_doc_lap": [b for b, _ in indep],
               "trong_vung_80_o_phien_cuoi_doc_lap": k_last,
               "ty_le_doc_lap_pct": r(k_last / n_ind * 100, 1) if n_ind else None,
               "khoang_tin_cay_95pct": wilson(k_last, n_ind),
               "p_so_voi_80pct": r(binom_two_sided(k_last, n_ind, 0.8), 4) if n_ind else None}
        if n_ind < 10:
            cov["ket_luan"] = (f"Mới có {n_ind} dự báo độc lập (cần ≥ 10, nên ≥ 20): chưa nói được vùng 80% đúng hay sai. "
                               "Không nêu tỷ lệ phủ như một kết quả.")
        else:
            lo, hi = cov["khoang_tin_cay_95pct"]
            cov["ket_luan"] = ("Vùng 80% đang QUÁ HẸP: giá ra ngoài nhiều hơn mức cho phép." if hi < 80 else
                               "Vùng 80% đang quá rộng: có thể thu hẹp." if lo > 80 else
                               "Tỷ lệ phủ phù hợp 80% trong sai số thống kê.")
        out["vung_80"] = cov
    if a.kich_ban:
        dung, sai = a.kich_ban
        n = dung + sai
        base = a.co_so
        p = binom_greater(dung, n, base) if n else None
        out["kich_ban"] = {"dung": dung, "sai": sai, "ty_le_dung_pct": r(dung / n * 100, 1) if n else None,
                           "muc_co_so_pct": r(base * 100, 1), "khoang_tin_cay_95pct": wilson(dung, n),
                           "p_hon_co_so": r(p, 4) if p is not None else None,
                           "ket_luan": ("chưa đủ 10 lần chấm để kết luận" if n < 10 else
                                        "kịch bản chính đúng nhiều hơn đoán bừa một cách có ý nghĩa" if p < 0.05 else
                                        "kịch bản chính CHƯA hơn đoán bừa giữa ba kịch bản; nói rõ trong báo cáo")}
    if a.tin_hieu:
        with open(a.tin_hieu, encoding="utf-8") as f:
            fc = json.load(f)
        s = (fc.get("kiem_chung_qua_khu") or {}).get("tin_hieu_vi_tri_tuong_tu") or {}
        n = s.get("so_lan_thu")
        if n and "ti_le_doan_dung_huong_pct" in s:
            k = round(s["ti_le_doan_dung_huong_pct"] / 100 * n)
            b = s["ti_le_dung_neu_luon_doan_theo_xu_the_pho_bien_pct"] / 100
            step = a.buoc
            n_eff = max(1, round(n * step / 6)) if step < 6 else n
            k_eff = round(k * n_eff / n)
            p = binom_greater(k_eff, n_eff, b)
            out["tin_hieu_huong"] = {"so_lan_thu": n, "so_lan_hieu_dung_sau_tru_chong_lan": n_eff,
                                     "dung_pct": s["ti_le_doan_dung_huong_pct"], "co_so_pct": r(b * 100, 1),
                                     "p": r(p, 4),
                                     "ket_luan": ("có lợi thế có ý nghĩa so với đoán theo xu thế phổ biến" if p < 0.05 else
                                                  "KHÔNG hơn có ý nghĩa cách đoán theo xu thế phổ biến: không nhắc tín hiệu hướng")}
    if a.chu:
        print("# Kết luận kiểm định dự báo", file=sys.stderr)
        for key, v in out.items():
            print(f"- {key}: {v.get('ket_luan')}", file=sys.stderr)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


# ---------- 4. fdr ----------
def corr_p(rho, n_eff):
    """p hai phía của hệ số tương quan, dùng biến đổi Fisher trên số điểm hiệu dụng."""
    if n_eff < 5 or abs(rho) >= 1:
        return 1.0 if n_eff < 5 else 0.0
    z = math.atanh(rho) * math.sqrt(n_eff - 3)
    return math.erfc(abs(z) / math.sqrt(2))


def cmd_fdr(a):
    pv, note = {}, {}
    for item in a.cap:
        name, val = item.rsplit("=", 1)
        if ":" in val:  # dạng tương quan:số_điểm từ ap_luc_von_ngoai.py
            rho, n = val.split(":")
            n_eff = int(n) / a.chong_lan
            pv[name] = corr_p(float(rho), n_eff)
            note[name] = f"tương quan {rho} trên {n} điểm ≈ {n_eff:.0f} điểm độc lập"
        else:
            pv[name] = float(val)
    q = bh(pv)
    out = {name: {"p": r(pv[name], 4), "q": r(q[name], 4), "ghi_chu": note.get(name), "con_y_nghia_q_duoi_0_05": q[name] < 0.05,
                  "con_y_nghia_q_duoi_0_10": q[name] < 0.10} for name in sorted(pv, key=pv.get)}
    json.dump({"so_kiem_dinh": len(pv), "ket_qua": out,
               "giai_thich": "Chỉ báo có q ≥ 0,10 coi như chưa chứng minh được tác dụng; không dùng để giải thích."},
              sys.stdout, ensure_ascii=False, indent=2)
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="lenh", required=True)

    c = sub.add_parser("chu-ky")
    c.add_argument("csv_path")
    c.add_argument("--threshold", type=float, help="ngưỡng đảo chiều %% (để trống = như cycles.py)")
    c.add_argument("--benchmark", help="CSV chỉ số chung (VN-Index) để xem chu kỳ có đi theo thị trường không")
    c.add_argument("--window", type=int, default=3)
    c.add_argument("--n", type=int, default=400, help="số chuỗi ngẫu nhiên")
    c.add_argument("--block", type=int, default=10, help="độ dài khối bootstrap trung bình (phiên)")
    c.add_argument("--seed", type=int, default=7)
    c.add_argument("--chu", action="store_true")
    c.set_defaults(fn=cmd_chu_ky)

    s = sub.add_parser("su-kien")
    s.add_argument("csv_path")
    s.add_argument("--su-kien", required=True, help="CSV cột date và group (hoặc ngay, nhom)")
    s.add_argument("--threshold", type=float)
    s.add_argument("--window", type=int, default=3)
    s.add_argument("--n", type=int, default=2000)
    s.add_argument("--seed", type=int, default=7)
    s.add_argument("--chu", action="store_true")
    s.set_defaults(fn=cmd_su_kien)

    d = sub.add_parser("du-bao")
    d.add_argument("csv_path")
    d.add_argument("--lich-su", help="du-bao-6-phien.json")
    d.add_argument("--kich-ban", type=int, nargs=2, metavar=("DUNG", "SAI"),
                   help="số lần kịch bản chính đúng / sai từ nhat-ky-du-bao.md (bỏ 'Chưa rõ')")
    d.add_argument("--co-so", type=float, default=1 / 3, help="tỷ lệ đúng nếu đoán bừa (mặc định 1/3: ba kịch bản)")
    d.add_argument("--tin-hieu", help="du_bao_6_phien.json mới nhất, để kiểm định tín hiệu 'vị trí tương tự'")
    d.add_argument("--buoc", type=int, default=2, help="số phiên giữa hai điểm kiểm chứng trong forecast6.py")
    d.add_argument("--chu", action="store_true")
    d.set_defaults(fn=cmd_du_bao)

    f = sub.add_parser("fdr")
    f.add_argument("cap", nargs="+", help="ten=p, hoặc ten=tuong_quan:so_diem (lấy từ phần kiểm chứng của ap_luc_von_ngoai.py)")
    f.add_argument("--chong-lan", type=float, default=5,
                   help="chia số điểm cho số này vì cửa sổ 5 phiên tương lai chồng lấn (mặc định 5)")
    f.set_defaults(fn=cmd_fdr)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
