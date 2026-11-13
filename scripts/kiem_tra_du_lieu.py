#!/usr/bin/env python3
"""Kiểm tra file giá TRƯỚC khi phân tích, để các lần chạy dùng cùng một bộ dữ liệu sạch.

Cách dùng:
    python kiem_tra_du_lieu.py MBB=data/MBB.csv TCB=data/TCB.csv CTG=data/CTG.csv HPG=data/HPG.csv SSI=data/SSI.csv \
        --tham-chieu MBB=19.90 HPG=21.15 --bien-do 0.07

Kiểm tra từng mã:
  - ngày trùng, ngày không theo thứ tự, ngày cuối tuần;
  - cao < max(mở, đóng) hoặc thấp > min(mở, đóng);
  - thay đổi vượt biên độ sàn (HOSE ±7%; có thể do chia cổ tức/chia tách – cần xác minh);
  - dòng TẠM: mở = cao = thấp = đóng và khối lượng trống hoặc chép y phiên trước;
  - khoảng trống quá 5 ngày làm việc;
  - giá đóng cửa phiên cuối so với giá tham chiếu tra trên sàn/Vietstock (nếu truyền --tham-chieu).
Kiểm tra chéo giữa các mã:
  - hai mã có cùng giá đóng cửa và cùng khối lượng trong một ngày, hoặc giá phiên cuối của mã này
    khớp với dãy giá của mã kia → nghi bị ĐẢO NHÃN mã khi thu thập.
Kết quả: JSON {"loi": [...], "canh_bao": [...], "dong_tam": [...]} ; mã thoát 1 nếu có lỗi.
"""
import argparse
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_prices  # noqa: E402


def bdays(a, b):
    n, d = 0, a
    while d < b:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="MÃ=đường_dẫn.csv")
    ap.add_argument("--tham-chieu", nargs="*", default=[], help="MÃ=giá đóng cửa phiên cuối tra từ nguồn thứ hai")
    ap.add_argument("--bien-do", type=float, default=0.07)
    ap.add_argument("--so-phien-cuoi", type=int, default=30, help="chỉ kiểm tra chi tiết N phiên cuối (lỗi cấu trúc vẫn kiểm cả file)")
    args = ap.parse_args()

    loi, cb, tam = [], [], []
    series = {}
    for spec in args.files:
        ma, path = spec.split("=", 1)
        ma = ma.upper()
        with open(path, encoding="utf-8-sig") as f:
            raw_dates = [ln.split(",")[0].strip() for ln in f.read().splitlines()[1:] if ln.strip()]
        if len(raw_dates) != len(set(raw_dates)):
            dups = sorted({d for d in raw_dates if raw_dates.count(d) > 1})
            loi.append(f"{ma}: ngày bị trùng {dups[:5]}")
        if raw_dates != sorted(raw_dates):
            cb.append(f"{ma}: các dòng không theo thứ tự ngày (script tự sắp xếp, nhưng nên ghi lại file đã sắp xếp)")
        data = load_prices(path, min_rows=2)
        series[ma] = data
        start = max(1, len(data) - args.so_phien_cuoi)
        for i, d in enumerate(data):
            ds = d["date"].isoformat()
            if d["date"].weekday() >= 5:
                loi.append(f"{ma} {ds}: ngày cuối tuần")
            if d["high"] < max(d["open"], d["close"]) - 1e-9 or d["low"] > min(d["open"], d["close"]) + 1e-9:
                loi.append(f"{ma} {ds}: cao/thấp mâu thuẫn với mở/đóng (O {d['open']} H {d['high']} L {d['low']} C {d['close']})")
            if i == 0:
                continue
            p = data[i - 1]
            chg = d["close"] / p["close"] - 1
            if abs(chg) > args.bien_do + 0.003:
                (loi if i >= start else cb).append(
                    f"{ma} {ds}: thay đổi {chg * 100:+.1f}% vượt biên độ ±{args.bien_do * 100:.0f}% – sai dữ liệu hoặc ngày chia cổ tức/chia tách, cần xác minh")
            g = bdays(p["date"], d["date"])
            if g > 5:
                cb.append(f"{ma}: khoảng trống {g} ngày làm việc giữa {p['date']} và {ds} (nghỉ lễ dài hay thiếu dữ liệu?)")
            flat = d["open"] == d["high"] == d["low"] == d["close"]
            if flat and (not d["volume"] or d["volume"] == p["volume"]):
                tam.append(f"{ma} {ds}")
        if args.tham_chieu:
            pass
    for spec in args.tham_chieu:
        ma, v = spec.split("=", 1)
        ma = ma.upper()
        if ma in series:
            last = series[ma][-1]
            if abs(last["close"] - float(v)) > 0.005 * float(v):
                loi.append(f"{ma}: đóng cửa phiên cuối {last['close']} ({last['date']}) khác giá tra từ nguồn thứ hai {v}")
    # chéo giữa các mã
    mas = list(series)
    for a_i, a in enumerate(mas):
        da = {d["date"]: d for d in series[a][-args.so_phien_cuoi:]}
        for b in mas[a_i + 1:]:
            db = {d["date"]: d for d in series[b][-args.so_phien_cuoi:]}
            for day in sorted(set(da) & set(db)):
                x, y = da[day], db[day]
                if x["close"] == y["close"] and x["volume"] and x["volume"] == y["volume"]:
                    loi.append(f"{a}/{b} {day}: cùng giá đóng cửa và khối lượng – nghi chép nhầm mã")
            # dò đảo nhãn: phiên cuối của a nằm gần dãy b hơn dãy a
            la, lb = series[a][-1], series[b][-1]
            if la["date"] == lb["date"] and len(series[a]) > 6 and len(series[b]) > 6:
                pa, pb = series[a][-2]["close"], series[b][-2]["close"]
                ja, jb = abs(la["close"] / pa - 1), abs(lb["close"] / pb - 1)
                xa, xb = abs(la["close"] / pb - 1), abs(lb["close"] / pa - 1)
                if xa < 0.02 and xb < 0.02 and (ja > 0.04 or jb > 0.04):
                    loi.append(f"{a}/{b} {la['date']}: giá phiên cuối của hai mã có vẻ bị ĐẢO NHÃN – kiểm tra lại nguồn")
    out = {"loi": loi, "canh_bao": cb, "dong_tam": tam,
           "ket_luan": "OK" if not loi else f"{len(loi)} lỗi – sửa hoặc ghi rõ trong báo cáo trước khi phân tích"}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if loi else 0)


if __name__ == "__main__":
    main()
