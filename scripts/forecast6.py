#!/usr/bin/env python3
"""Dự báo VÙNG GIÁ cho ~6 phiên liên tiếp tới, kèm kiểm chứng độ chính xác bằng dữ liệu quá khứ.

Cách dùng:
    python forecast6.py gia.csv
    python forecast6.py gia.csv --muc 20.0 21.5             # thêm xác suất chạm các mức giá (hỗ trợ/kháng cự...)
    python forecast6.py gia.csv --lich-su du-bao-6-phien.json   # chấm dự báo cũ + ghi dự báo mới vào lịch sử
    python forecast6.py gia.csv --gioi-han 0.10 --nghi 2027-01-01   # sàn HNX (±10%) và ngày nghỉ lễ

Mô hình (không phụ thuộc thư viện ngoài):
  1. Biến động từng phiên ước lượng bằng EWMA (lambda 0,94) trộn 30% với biến động dài hạn.
  2. Mô phỏng 4.000 đường giá: mỗi phiên lấy ngẫu nhiên một "cú sốc" từ chính lịch sử của mã
     (đã chuẩn hóa theo biến động lúc đó) nên đuôi dày/giảm sâu của mã được giữ lại.
     Biên độ mỗi phiên bị chặn theo biên độ sàn (mặc định HOSE ±7%).
  3. Độ lệch (drift) đặt bằng 0: mô hình KHÔNG đoán hướng, nó đo độ rộng của những gì có thể xảy ra.
     Vì vậy xác suất tăng/giảm quanh 50% là bình thường. Hướng đi do phần phân tích kịch bản đánh giá.
  4. Kiểm chứng (backtest) đi theo thời gian: tại mỗi thời điểm trong quá khứ chỉ dùng dữ liệu đến lúc đó,
     dự báo 6 phiên, rồi xem giá thực tế có nằm trong vùng 50%/80%/95% không. Nếu vùng đo được quá hẹp
     hoặc quá rộng so với thực tế, hệ số giãn vùng được hiệu chỉnh (hiệu chỉnh trên 70% đầu, chấm lại trên 30% sau).
  5. Tùy chọn: tín hiệu "vị trí tương tự" (các ngày giá cùng vị trí trong biên độ 20 phiên và cùng chiều 5 phiên)
     và kiểm tra xem nó có đoán hướng tốt hơn cách đoán theo xu thế phổ biến hay không.

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
from common import load_prices, parse_date  # noqa: E402

LAM = 0.94          # hệ số EWMA
SEED_N = 20         # số phiên đầu dùng khởi tạo EWMA
BLEND_EWMA = 0.7    # trọng số EWMA khi trộn với biến động dài hạn
QS = (2.5, 10, 25, 50, 75, 90, 97.5)


# ---------- tiện ích ----------
def qsorted(sv, p):
    k = (len(sv) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(sv) - 1)
    return sv[f] + (sv[c] - sv[f]) * (k - f)


def rnd(x, nd=2):
    return None if x is None else round(x, nd)


def next_sessions(last_date, n, holidays):
    """n ngày giao dịch kế tiếp: bỏ thứ Bảy, Chủ nhật và các ngày nghỉ được truyền vào."""
    out, d = [], last_date
    while len(out) < n:
        d += dt.timedelta(days=1)
        if d.weekday() < 5 and d not in holidays:
            out.append(d)
    return out


# ---------- mô hình biến động ----------
def ewma_vars(rets):
    """out[j] = phương sai dự báo cho rets[j] chỉ dựa trên rets[:j]; out[len(rets)] = cho phiên kế tiếp."""
    seed = rets[:SEED_N] if len(rets) >= SEED_N else rets
    v = sum(x * x for x in seed) / len(seed)
    out = []
    for x in rets:
        out.append(v)
        v = LAM * v + (1 - LAM) * x * x
    out.append(v)
    return out


class Model:
    def __init__(self, closes, window):
        self.closes = closes
        self.window = window
        self.rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
        self.var = ewma_vars(self.rets)
        self.z = [self.rets[j] / math.sqrt(self.var[j]) if self.var[j] > 0 else 0.0
                  for j in range(len(self.rets))]

    def pool(self, t):
        """Các cú sốc đã chuẩn hóa, chỉ dùng dữ liệu đến phiên t (chỉ số phiên đóng cửa cuối đã biết)."""
        lo = max(SEED_N, t - self.window)
        seg = self.z[lo:t]
        if len(seg) < 60:
            return None
        m = sum(seg) / len(seg)
        sd = math.sqrt(sum((x - m) ** 2 for x in seg) / len(seg)) or 1.0
        return [(x - m) / sd for x in seg]

    def var0(self, t):
        ew = self.var[t]
        seg = self.rets[max(0, t - self.window):t]
        lr = sum(x * x for x in seg) / len(seg)
        return BLEND_EWMA * ew + (1 - BLEND_EWMA) * lr


def simulate(v0, pool, h, paths, lo, hi, rng):
    npool = len(pool)
    cum = [[0.0] * paths for _ in range(h)]
    for p in range(paths):
        v, c = v0, 0.0
        for k in range(h):
            x = math.sqrt(v) * pool[int(rng.random() * npool)]
            x = lo if x < lo else hi if x > hi else x
            c += x
            cum[k][p] = c
            v = LAM * v + (1 - LAM) * x * x
    return cum


def quantile_table(cum):
    """Với mỗi phiên: {phân vị: log(giá/giá gốc)}, và tỷ lệ đường đi có lợi nhuận tích lũy > 0."""
    table, p_up = [], []
    for col in cum:
        sv = sorted(col)
        table.append({q: qsorted(sv, q) for q in QS})
        p_up.append(sum(1 for x in col if x > 0) / len(col))
    return table, p_up


# ---------- tín hiệu "vị trí tương tự" ----------
def build_features(closes):
    n = len(closes)
    pos20, r5 = [None] * n, [None] * n
    for i in range(n):
        if i >= 19:
            seg = closes[i - 19:i + 1]
            lo, hi = min(seg), max(seg)
            pos20[i] = (closes[i] - lo) / (hi - lo) if hi > lo else 0.5
        if i >= 5:
            r5[i] = closes[i] / closes[i - 5] - 1
    return pos20, r5


def analog(closes, feats, t, h):
    """Các ngày i <= t-h có cùng vị trí trong biên độ 20 phiên (±0,2) và cùng chiều 5 phiên với ngày t."""
    pos20, r5 = feats
    if pos20[t] is None or r5[t] is None:
        return None
    sign = 1 if r5[t] >= 0 else -1
    fw = []
    for i in range(20, t - h + 1):
        if pos20[i] is None or r5[i] is None:
            continue
        if abs(pos20[i] - pos20[t]) <= 0.2 and (1 if r5[i] >= 0 else -1) == sign:
            fw.append(closes[i + h] / closes[i] - 1)
    if not fw:
        return {"n": 0}
    sv = sorted(fw)
    return {"n": len(fw), "ti_le_tang": sum(1 for x in fw if x > 0) / len(fw),
            "trung_vi": qsorted(sv, 50), "p10": qsorted(sv, 10), "p90": qsorted(sv, 90)}


# ---------- kiểm chứng ----------
def sk_of(s, k):
    return s[k] if isinstance(s, (list, tuple)) else s


def coverage(records, s, h):
    c = {"50": 0, "80": 0, "95": 0}
    per_k80 = [0] * h
    path_ok = 0
    tot = 0
    for rec in records:
        ok_path = True
        for k in range(h):
            a, q = rec["actual"][k], rec["q"][k]
            sc = sk_of(s, k)
            tot += 1
            if sc * q[25] <= a <= sc * q[75]:
                c["50"] += 1
            in80 = sc * q[10] <= a <= sc * q[90]
            if in80:
                c["80"] += 1
                per_k80[k] += 1
            else:
                ok_path = False
            if sc * q[2.5] <= a <= sc * q[97.5]:
                c["95"] += 1
        path_ok += ok_path
    nrec = len(records)
    return {"vung_50_pct": rnd(c["50"] / tot * 100, 1), "vung_80_pct": rnd(c["80"] / tot * 100, 1),
            "vung_95_pct": rnd(c["95"] / tot * 100, 1),
            "ca_6_phien_deu_trong_vung_80_pct": rnd(path_ok / nrec * 100, 1),
            "vung_80_theo_phien_pct": [rnd(x / nrec * 100, 1) for x in per_k80]}


def calibrate(records, h, target=0.80):
    """Hệ số giãn vùng RIÊNG cho từng phiên k (chu kỳ/đà giá làm vùng các phiên xa cần rộng hơn phiên gần).
    Ràng buộc: không giảm dần theo k, nằm trong [0,7; 2,5]."""
    out = []
    for k in range(h):
        best, best_gap = 1.0, 9
        s = 0.5
        while s <= 2.5001:
            ok = sum(1 for rec in records if s * rec["q"][k][10] <= rec["actual"][k] <= s * rec["q"][k][90])
            gap = abs(ok / len(records) - target)
            if gap < best_gap - 1e-12:
                best, best_gap = s, gap
            s += 0.05
        best = max(0.7, min(2.5, best))
        if out:
            best = max(best, out[-1])
        out.append(round(best, 2))
    return out


def run_backtest(model, closes, h, window, paths, lo, hi, step, rng):
    n = len(closes)
    warmup = SEED_N + 100
    origins = list(range(warmup, n - h, step))
    if len(origins) < 15:
        return None, None
    feats = build_features(closes)
    records = []
    hits_a = hits_b = n_a = 0
    for t in origins:
        pool = model.pool(t)
        if pool is None:
            continue
        cum = simulate(model.var0(t), pool, h, paths, lo, hi, rng)
        table, _ = quantile_table(cum)
        actual = [math.log(closes[t + k] / closes[t]) for k in range(1, h + 1)]
        records.append({"t": t, "q": table, "actual": actual})
        an = analog(closes, feats, t, h)
        if an and an.get("n", 0) >= 30:
            fw = [closes[i + h] / closes[i] - 1 for i in range(20, t - h + 1)]
            base_up = sum(1 for x in fw if x > 0) / len(fw) >= 0.5
            real_up = actual[-1] > 0
            n_a += 1
            hits_a += ((an["trung_vi"] > 0) == real_up)
            hits_b += (base_up == real_up)
    return records, {"so_lan_thu": n_a, "dung_a": hits_a, "dung_b": hits_b}


def backtest_summary(records, ana, h):
    nrec = len(records)
    out = {"so_diem_kiem_chung": nrec,
           "ghi_chu": "Các điểm kiểm chứng cách nhau vài phiên nên chồng lấn nhau; độ tin cậy của tỷ lệ thấp hơn con số mẫu."}
    if nrec < 30:
        out["canh_bao"] = "Dưới 30 điểm kiểm chứng: kết quả chỉ mang tính tham khảo; chưa hiệu chỉnh hệ số giãn vùng."
    out["do_phu_goc"] = coverage(records, 1.0, h)
    out["muc_tieu"] = {"vung_50_pct": 50, "vung_80_pct": 80, "vung_95_pct": 95}
    s_all = [1.0] * h
    if nrec >= 30:
        cut = int(nrec * 0.7)
        s_train = calibrate(records[:cut], h)
        out["hieu_chinh_ngoai_mau"] = {
            "he_so_hoc_tu_70pct_dau": s_train,
            "tren_30pct_sau_khi_chua_hieu_chinh": coverage(records[cut:], 1.0, h),
            "tren_30pct_sau_khi_da_hieu_chinh": coverage(records[cut:], s_train, h),
        }
        s_all = calibrate(records, h)
    out["he_so_gian_vung_ap_dung"] = s_all
    out["do_phu_sau_hieu_chinh"] = coverage(records, s_all, h)
    widths = [(rec["q"][h - 1][90] - rec["q"][h - 1][10]) * s_all[h - 1] * 100 for rec in records]
    out["do_rong_vung_80_phien_cuoi_tb_pct"] = rnd(sum(widths) / len(widths), 2)
    if ana and ana["so_lan_thu"] >= 20:
        a = ana["dung_a"] / ana["so_lan_thu"] * 100
        b = ana["dung_b"] / ana["so_lan_thu"] * 100
        out["tin_hieu_vi_tri_tuong_tu"] = {
            "so_lan_thu": ana["so_lan_thu"], "ti_le_doan_dung_huong_pct": rnd(a, 1),
            "ti_le_dung_neu_luon_doan_theo_xu_the_pho_bien_pct": rnd(b, 1),
            "ket_luan": ("có lợi thế rõ so với đoán theo xu thế phổ biến" if a - b >= 5
                         else "KHÔNG hơn rõ rệt cách đoán theo xu thế phổ biến; coi như không có tín hiệu hướng"),
        }
    elif ana:
        out["tin_hieu_vi_tri_tuong_tu"] = {"so_lan_thu": ana["so_lan_thu"],
                                           "ket_luan": "quá ít lần thử để đánh giá; coi như không có tín hiệu hướng"}
    return out, s_all


# ---------- lịch sử và chấm dự báo cũ ----------
def grade_history(hist, data, h):
    dates = [d["date"].isoformat() for d in data]
    closes = [d["close"] for d in data]
    last_date = dates[-1]
    rows, flags = [], []
    tot = {"50": 0, "80": 0, "95": 0, "n": 0}
    for fc in hist.get("du_bao", []):
        base = fc.get("lam_vao_ngay")
        if base is None or base >= last_date or base not in dates:
            continue
        ib = dates.index(base)
        graded, outs = [], 0
        consec = max_consec = 0
        out95 = False
        for ph in fc["phien"]:
            k = ph["k"]
            if ib + k > len(data) - 1:
                break
            a = closes[ib + k]
            in50 = ph["vung_50"][0] <= a <= ph["vung_50"][1]
            in80 = ph["vung_80"][0] <= a <= ph["vung_80"][1]
            in95 = ph["vung_95"][0] <= a <= ph["vung_95"][1]
            tot["n"] += 1
            tot["50"] += in50
            tot["80"] += in80
            tot["95"] += in95
            consec = 0 if in80 else consec + 1
            max_consec = max(max_consec, consec)
            out95 = out95 or (not in95)
            outs += (not in80)
            graded.append({"phien": k, "ngay_thuc_te": dates[ib + k], "gia_thuc_te": rnd(a),
                           "trung_vi_du_bao": ph["trung_vi"],
                           "lech_so_voi_trung_vi_pct": rnd((a / ph["trung_vi"] - 1) * 100, 2),
                           "trong_vung_80": bool(in80)})
        if not graded:
            continue
        done = len(graded) >= len(fc["phien"])
        rows.append({"du_bao_lap_ngay": base, "so_phien_da_co_gia": len(graded),
                     "da_xong": done, "phien": graded})
        if not done:
            if max_consec >= 2:
                flags.append(f"Giá đóng cửa ra ngoài vùng 80% của dự báo lập ngày {base} ở {max_consec} phiên liên tiếp")
            if out95:
                flags.append(f"Có phiên đóng cửa ra ngoài vùng 95% của dự báo lập ngày {base}")
    summary = None
    if tot["n"]:
        summary = {"so_phien_da_cham": tot["n"],
                   "trong_vung_50_pct": rnd(tot["50"] / tot["n"] * 100, 1),
                   "trong_vung_80_pct": rnd(tot["80"] / tot["n"] * 100, 1),
                   "trong_vung_95_pct": rnd(tot["95"] / tot["n"] * 100, 1),
                   "muc_tieu": "50 / 80 / 95",
                   "nhan_xet": ("số phiên đã chấm còn ít, chưa kết luận được" if tot["n"] < 30 else
                                "vùng dự báo đang khớp thực tế" if abs(tot["80"] / tot["n"] * 100 - 80) <= 10 else
                                "vùng dự báo đang LỆCH so với thực tế; cần xem lại hệ số giãn vùng")}
    return rows, summary, flags


def load_history(path):
    if path and os.path.exists(path) and os.path.getsize(path) > 2:
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            print(f"[cảnh báo] không đọc được {path}, bắt đầu lịch sử mới", file=sys.stderr)
    return {"du_bao": []}


# ---------- chương trình chính ----------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path")
    ap.add_argument("--phien", type=int, default=6, help="số phiên dự báo (mặc định 6)")
    ap.add_argument("--so-duong", type=int, default=4000, help="số đường giá mô phỏng")
    ap.add_argument("--gioi-han", type=float, default=0.07, help="biên độ giá tối đa một phiên (HOSE 0.07, HNX 0.10, UPCoM 0.15)")
    ap.add_argument("--cua-so", type=int, default=500, help="số phiên lịch sử dùng để lấy cú sốc")
    ap.add_argument("--muc", type=float, nargs="*", default=[], help="các mức giá cần tính xác suất chạm (cùng đơn vị với CSV)")
    ap.add_argument("--nghi", nargs="*", default=[], help="ngày nghỉ lễ sắp tới (yyyy-mm-dd), không có phiên giao dịch")
    ap.add_argument("--lich-su", help="file JSON lịch sử dự báo: chấm các dự báo cũ rồi ghi thêm dự báo mới")
    ap.add_argument("--khong-ghi", action="store_true", help="chấm lịch sử nhưng không ghi dự báo mới vào file")
    ap.add_argument("--khong-kiem-chung", action="store_true", help="bỏ qua backtest (nhanh hơn, không hiệu chỉnh)")
    ap.add_argument("--he-so", type=float, help="ép hệ số giãn vùng thay vì tự hiệu chỉnh")
    ap.add_argument("--buoc", type=int, default=2, help="khoảng cách (phiên) giữa các điểm backtest")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--hom-nay", help="ngày hôm nay yyyy-mm-dd (để cảnh báo dữ liệu cũ)")
    args = ap.parse_args()

    h = args.phien
    data = load_prices(args.csv_path, min_rows=SEED_N + 80)
    closes = [d["close"] for d in data]
    n = len(closes)
    t = n - 1
    last_date = data[-1]["date"]
    rng = random.Random(args.seed)
    lo, hi = math.log(1 - args.gioi_han), math.log(1 + args.gioi_han)
    holidays = {parse_date(x) for x in args.nghi}

    model = Model(closes, args.cua_so)
    pool = model.pool(t)
    if pool is None:
        sys.exit("Không đủ dữ liệu để lấy cú sốc lịch sử (cần tối thiểu ~80 phiên).")

    # 1) kiểm chứng
    bt_out, s = None, [1.0] * h
    if not args.khong_kiem_chung:
        recs, ana = run_backtest(model, closes, h, args.cua_so, min(1500, args.so_duong), lo, hi, args.buoc, rng)
        if recs and len(recs) >= 15:
            bt_out, s = backtest_summary(recs, ana, h)
        else:
            bt_out = {"canh_bao": "Dữ liệu quá ngắn để kiểm chứng (cần ~140+ phiên); dùng hệ số giãn vùng 1,0 và coi vùng là chưa kiểm chứng."}
    if args.he_so:
        s = [args.he_so] * h

    # 2) dự báo
    cum = simulate(model.var0(t), pool, h, args.so_duong, lo, hi, rng)
    price0 = closes[t]
    table, p_up = quantile_table(cum)
    sess_dates = next_sessions(last_date, h, holidays)

    def px(logv, k):
        return price0 * math.exp(s[k] * logv)

    phien = []
    for k in range(h):
        q = table[k]
        phien.append({
            "k": k + 1, "ngay": sess_dates[k].isoformat(), "trung_vi": rnd(px(q[50], k)),
            "vung_50": [rnd(px(q[25], k)), rnd(px(q[75], k))],
            "vung_80": [rnd(px(q[10], k)), rnd(px(q[90], k))],
            "vung_95": [rnd(px(q[2.5], k)), rnd(px(q[97.5], k))],
            "thay_doi_trung_vi_pct": rnd((px(q[50], k) / price0 - 1) * 100, 2),
            "xac_suat_cao_hon_gia_hien_tai_pct": rnd(p_up[k] * 100, 1),
        })

    def prob_any(cond):
        paths = len(cum[0])
        return sum(1 for p in range(paths) if any(cond(s[k] * cum[k][p]) for k in range(h))) / paths * 100

    xs = {}
    for pct in (3, 5):
        xs[f"it_nhat_1_phien_dong_cua_thap_hon_gia_hien_tai_{pct}pct"] = rnd(prob_any(lambda x, pct=pct: x <= math.log(1 - pct / 100)), 1)
        xs[f"it_nhat_1_phien_dong_cua_cao_hon_gia_hien_tai_{pct}pct"] = rnd(prob_any(lambda x, pct=pct: x >= math.log(1 + pct / 100)), 1)
    xs["dong_cua_phien_cuoi_cao_hon_gia_hien_tai"] = rnd(p_up[-1] * 100, 1)
    muc_out = []
    for lv in args.muc:
        if lv <= 0:
            continue
        L = math.log(lv / price0)
        if L >= 0:
            pr = prob_any(lambda x, L=L: x >= L)
            muc_out.append({"muc": lv, "huong": "phía trên giá hiện tại", "xac_suat_it_nhat_1_phien_dong_cua_toi_muc_pct": rnd(pr, 1)})
        else:
            pr = prob_any(lambda x, L=L: x <= L)
            muc_out.append({"muc": lv, "huong": "phía dưới giá hiện tại", "xac_suat_it_nhat_1_phien_dong_cua_toi_muc_pct": rnd(pr, 1)})

    # 3) vị trí tương tự (hiện tại)
    feats = build_features(closes)
    an_now = analog(closes, feats, t, h)
    an_out = None
    if an_now and an_now.get("n", 0) > 0:
        an_out = {"so_mau": an_now["n"], "ti_le_tang_sau_6_phien_pct": rnd(an_now["ti_le_tang"] * 100, 1),
                  "loi_nhuan_trung_vi_pct": rnd(an_now["trung_vi"] * 100, 2),
                  "p10_pct": rnd(an_now["p10"] * 100, 2), "p90_pct": rnd(an_now["p90"] * 100, 2),
                  "mo_ta": "các ngày trước đây giá ở cùng vị trí trong biên độ 20 phiên (±0,2) và cùng chiều thay đổi 5 phiên",
                  "chi_dung_khi": "mẫu ≥ 30 VÀ kết luận backtest nói tín hiệu này hơn đoán theo xu thế phổ biến"}
        if an_now["n"] < 30:
            an_out["canh_bao"] = "dưới 30 mẫu: bỏ qua"

    # 4) vị trí biến động hiện tại
    sig_now = math.sqrt(model.var0(t))
    last_ret = model.rets[-1]
    sig_pred_last = math.sqrt(model.var[t - 1])
    shock = abs(last_ret) / sig_pred_last if sig_pred_last > 0 else 0

    # 5) lịch sử, chấm dự báo cũ
    graded, grade_sum, flags = None, None, []
    hist_path = args.lich_su
    hist = load_history(hist_path) if hist_path else {"du_bao": []}
    if hist_path:
        graded, grade_sum, flags = grade_history(hist, data, h)
    if shock >= 2.5:
        flags.append(f"Phiên cuối biến động bất thường: {rnd(last_ret * 100, 2)}% (gấp {rnd(shock, 1)} lần mức dao động dự kiến)")

    today = parse_date(args.hom_nay) if args.hom_nay else dt.date.today()
    warn = []
    missing = sum(1 for i in range(1, (today - last_date).days)
                  if (last_date + dt.timedelta(days=i)).weekday() < 5 and (last_date + dt.timedelta(days=i)) not in holidays)
    if missing >= 1:
        warn.append(f"Dữ liệu giá dừng ở {last_date.isoformat()}, thiếu khoảng {missing} phiên gần nhất so với hôm nay "
                    f"({today.isoformat()}). Các phiên đầu của dự báo có thể đã diễn ra; lấy thêm giá rồi chạy lại để vùng dự báo bắt đầu đúng chỗ.")
    if max(s) > 1.25:
        warn.append(f"Hệ số giãn vùng theo phiên {s}: backtest cho thấy mô hình gốc quá hẹp với mã này "
                    "(thường do giá có đà/chu kỳ kéo dài nhiều phiên), vùng đã được nới rộng.")
    if min(s) < 0.85:
        warn.append(f"Hệ số giãn vùng theo phiên {s}: backtest cho thấy mô hình gốc quá rộng với mã này, vùng đã được thu hẹp.")
    warn.append("Ngày giao dịch chỉ loại trừ thứ Bảy, Chủ nhật và các ngày --nghi; kiểm tra lịch nghỉ lễ thực tế.")
    warn.append("Xác suất chạm mức giá tính theo GIÁ ĐÓNG CỬA; trong phiên giá có thể chạm sớm hơn.")

    first, last = phien[0], phien[-1]
    tom_tat = [
        f"Giá đóng cửa {last_date.isoformat()}: {rnd(price0)}. Dao động 1 phiên dự kiến ≈ {rnd(sig_now * 100, 2)}%.",
        f"Phiên {last['k']} ({last['ngay']}): trung vị {last['trung_vi']}, vùng 50% {last['vung_50'][0]}–{last['vung_50'][1]}, "
        f"vùng 80% {last['vung_80'][0]}–{last['vung_80'][1]}.",
        f"Xác suất đóng cửa phiên {last['k']} cao hơn hiện tại: {last['xac_suat_cao_hon_gia_hien_tai_pct']}% (mô hình không đoán hướng, ≈50% là bình thường).",
        f"Xác suất có ít nhất 1 phiên đóng cửa thấp hơn hiện tại 3%: {xs['it_nhat_1_phien_dong_cua_thap_hon_gia_hien_tai_3pct']}%; "
        f"5%: {xs['it_nhat_1_phien_dong_cua_thap_hon_gia_hien_tai_5pct']}%.",
    ]

    entry = {"lam_vao_ngay": last_date.isoformat(), "gia_goc": rnd(price0), "he_so_gian_vung": s,
             "phien": [{"k": p["k"], "ngay": p["ngay"], "trung_vi": p["trung_vi"], "vung_50": p["vung_50"],
                        "vung_80": p["vung_80"], "vung_95": p["vung_95"]} for p in phien]}
    saved = None
    if hist_path and not args.khong_ghi:
        keep = [x for x in hist.get("du_bao", []) if x.get("lam_vao_ngay") != entry["lam_vao_ngay"]]
        keep.append(entry)
        keep.sort(key=lambda x: x["lam_vao_ngay"])
        hist["du_bao"] = keep[-12:]
        with open(hist_path, "w", encoding="utf-8") as f:
            json.dump(hist, f, ensure_ascii=False)
        saved = hist_path

    out = {
        "ngay_cuoi_du_lieu": last_date.isoformat(), "gia_dong_cua": rnd(price0), "so_phien_du_lieu": n,
        "so_phien_du_bao": h, "gioi_han_bien_do_phien": args.gioi_han,
        "bien_dong": {"dao_dong_1_phien_du_kien_pct": rnd(sig_now * 100, 2),
                      "he_so_gian_vung_theo_phien": s},
        "du_bao_tung_phien": phien,
        "xac_suat": xs,
        "xac_suat_cham_muc_gia": muc_out,
        "vi_tri_tuong_tu": an_out,
        "tom_tat": tom_tat,
        "kiem_chung_qua_khu": bt_out,
        "cham_du_bao_truoc": {"tong_hop": grade_sum, "chi_tiet": graded} if hist_path else None,
        "da_ghi_lich_su": saved,
        "canh_bao": warn,
        "phuong_phap": "Mô phỏng lọc theo biến động (EWMA 0,94 trộn dài hạn), cú sốc lấy từ lịch sử của mã, "
                       "drift = 0, chặn biên độ sàn. Vùng = phân vị 25–75 / 10–90 / 2,5–97,5 của các đường mô phỏng, "
                       "nhân hệ số giãn vùng đã hiệu chỉnh bằng backtest.",
        "luu_y": "Đây là vùng giá khả dĩ theo thống kê quá khứ, không phải lời hứa và không phải khuyến nghị mua/bán. "
                 "Tin tức bất ngờ, đợt rung lắc cả thị trường hay thay đổi quy định có thể đưa giá ra ngoài mọi vùng.",
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
