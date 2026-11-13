#!/usr/bin/env python3
"""Lấy giá ngày từ API của hai công ty chứng khoán (KBS và Vietcap), so hai nguồn với nhau và với file giá đã lưu.

Cách dùng:
    python lay_gia_cty_ck.py MBB TCB CTG HPG --phien 2026-11-06 --out-dir research/gia_ctck \
        --doi-chieu MBB=MBB.csv TCB=TCB.csv CTG=CTG.csv HPG=HPG.csv
    python lay_gia_cty_ck.py MBB --phien 2026-11-06 --nguon kbs        # chỉ một nguồn
    python lay_gia_cty_ck.py MBB --tu-file kbs=kbs.json vci=vci.json   # JSON gốc đã lấy qua trình duyệt
    python lay_gia_cty_ck.py MBB --tu-file kbs=kbs.csv vci=vci.csv     # dạng gọn: MÃ,ngày,mở,cao,thấp,đóng,KL (đồng)

Nguồn (không công bố chính thức, có thể đổi bất cứ lúc nào):
  kbs  GET  https://kbbuddywts.kbsec.com.vn/iis-server/investment/stocks/<MÃ>/data_day?sdate=dd-mm-yyyy&edate=dd-mm-yyyy
            -> {"symbol":..,"data_day":[{"t":"yyyy-mm-dd 07:00","o","h","l","c","v"},...]}
  vci  POST https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart
            body {"timeFrame":"ONE_DAY","symbols":["<MÃ>"],"to":<unix giây>,"countBack":<n>} (MỖI LẦN MỘT MÃ)
            -> [{"symbol":..,"o":[..],"h":[..],"l":[..],"c":[..],"v":[..],"t":["<unix giây>",..]}]
  Giá trả theo đồng; script đổi sang nghìn đồng như file giá đã lưu.

Đầu ra: JSON in ra màn hình; mỗi mã có
  - nguon.<kbs|vci>: lấy được không, lỗi, số phiên, kiểm tra nội tại, đối chiếu với file đã lưu
  - phien_can_lay: giá của phiên --phien theo từng nguồn, và 'nhan':
        ✔  hai nguồn đều khớp file đã lưu (≥ 5 phiên) và khớp nhau tuyệt đối ở phiên cần lấy
        ◐  chỉ một nguồn dùng được
        ✖  hai nguồn khác nhau ở phiên cần lấy (không chọn số nào)
        ⊘  không nguồn nào dùng được
  - <out-dir>/gia_<MÃ>_ctck.csv: date,open,high,low,close,volume (nghìn đồng) của nguồn tốt nhất, chỉ khi nhãn ✔ hoặc ◐.
Quy tắc an toàn:
  - Phiên của ngày hôm nay (giờ Việt Nam) trước 15:05 là phiên đang giao dịch: bỏ, không bao giờ coi là giá đóng cửa.
  - Không đoán: thiếu trường thì báo lỗi cấu trúc; không có phiên cần lấy thì không dùng phiên khác thay thế.
  - Đối chiếu file đã lưu chỉ dùng 10 phiên gần nhất trùng ngày (giá quá khứ có thể khác vì điều chỉnh cổ tức).
    Lệch theo một tỷ lệ gần như không đổi -> ghi 'lech_do_dieu_chinh', nguồn vẫn dùng được cho phiên mới.
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request

KBS = os.environ.get("KBS_API", "https://kbbuddywts.kbsec.com.vn/iis-server/investment/stocks/{ma}/data_day")
VCI = os.environ.get("VCI_API", "https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart")
TOL = 0.001          # nghìn đồng
CUA_SO = 10          # số phiên gần nhất dùng để đối chiếu với file đã lưu
TOI_THIEU = 5
VN = dt.timezone(dt.timedelta(hours=7))
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
       "Accept": "application/json"}
TOL_CU = 0.03        # nghìn đồng: sai khác do làm tròn giá điều chỉnh ở các phiên cũ giữa hai nguồn


def http(url, data=None, retries=1):
    last = None
    for k in range(retries + 1):
        try:
            h = dict(HDR)
            if data is not None:
                h["Content-Type"] = "application/json"
                if "vietcap" in url:
                    h["Origin"] = h["Referer"] = "https://trading.vietcap.com.vn"
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8")), None
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
        except urllib.error.URLError as e:
            last = f"không kết nối được: {e.reason}"
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None, "trả về không phải JSON (trang chặn hoặc đổi cấu trúc)"
        except Exception as e:  # noqa: BLE001
            last = f"lỗi: {e}"
        time.sleep(2)
    return None, last


def fetch_kbs(ma, tu, den):
    url = KBS.format(ma=ma) + f"?sdate={tu:%d-%m-%Y}&edate={den:%d-%m-%Y}"
    return http(url)


def fetch_vci(ma, tu, den, n=None):
    to = int(dt.datetime.combine(den + dt.timedelta(days=1), dt.time(), VN).timestamp())
    n = n or (den - tu).days + 5
    body = json.dumps({"timeFrame": "ONE_DAY", "symbols": [ma], "to": to, "countBack": n}).encode()
    return http(VCI, data=body)


def parse_kbs(ma, raw):
    if not isinstance(raw, dict) or not isinstance(raw.get("data_day"), list):
        return None, "không có trường 'data_day': cấu trúc đã đổi"
    if str(raw.get("symbol", ma)).upper() != ma:
        return None, f"mã trả về {raw.get('symbol')} ≠ {ma}"
    rows = []
    for x in raw["data_day"]:
        if not all(k in x for k in ("t", "o", "h", "l", "c", "v")):
            return None, "thiếu trường o/h/l/c/v/t: cấu trúc đã đổi"
        rows.append((str(x["t"])[:10], x["o"], x["h"], x["l"], x["c"], x["v"]))
    return rows, None


def parse_vci(ma, raw):
    if not isinstance(raw, list):
        return None, "không phải danh sách: cấu trúc đã đổi"
    hit = [x for x in raw if str(x.get("symbol", "")).upper() == ma]
    if not hit:
        return None, "không có dữ liệu cho mã (gọi mỗi lần một mã)"
    x = hit[0]
    if not all(k in x for k in ("t", "o", "h", "l", "c", "v")):
        return None, "thiếu trường o/h/l/c/v/t: cấu trúc đã đổi"
    n = len(x["t"])
    if any(len(x[k]) != n for k in ("o", "h", "l", "c", "v")):
        return None, "độ dài các mảng không bằng nhau"
    rows = []
    for i in range(n):
        d = dt.datetime.fromtimestamp(int(x["t"][i]), VN).date().isoformat()
        rows.append((d, x["o"][i], x["h"][i], x["l"][i], x["c"][i], x["v"][i]))
    return rows, None


def clean(rows, now):
    """Đổi đơn vị, bỏ phiên đang giao dịch, kiểm tra nội tại. Trả (dòng tốt, dòng bị loại)."""
    hom_nay = now.date().isoformat()
    dang_gd = now.time() < dt.time(15, 5)
    good, bad, seen = [], [], set()
    for d, o, h, l, c, v in rows:
        if d in seen:
            bad.append(f"{d}: trùng ngày")
            continue
        seen.add(d)
        if d > hom_nay or (d == hom_nay and dang_gd):
            bad.append(f"{d}: phiên chưa kết thúc, bỏ")
            continue
        try:
            o, h, l, c = (float(z) / 1000 for z in (o, h, l, c))
        except (TypeError, ValueError):
            bad.append(f"{d}: giá không phải số")
            continue
        if not (l - TOL <= min(o, c) and max(o, c) <= h + TOL) or min(o, h, l, c) <= 0:
            bad.append(f"{d}: cao/thấp không hợp lệ (mở {o}, cao {h}, thấp {l}, đóng {c})")
            continue
        good.append({"date": d, "open": round(o, 3), "high": round(h, 3), "low": round(l, 3),
                     "close": round(c, 3), "volume": v})
    good.sort(key=lambda r: r["date"])
    # biên độ ±7% so với đóng cửa phiên trước (HOSE)
    ok = []
    for i, r in enumerate(good):
        if i and i >= len(good) - 30 and abs(r["close"] / good[i - 1]["close"] - 1) > 0.0701:
            bad.append(f"{r['date']}: đóng cửa lệch {r['close'] / good[i - 1]['close'] - 1:+.2%} so với phiên trước, "
                       "vượt ±7% (kiểm tra chia cổ tức)")
            continue
        ok.append(r)
    return ok, bad


def load_saved(path, ma=None):
    """File giá đã lưu: một mã (date,...,close) hoặc file chung nhiều mã có cột 'ma'."""
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            r = {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
            if ma and r.get("ma") and r["ma"].upper() != ma:
                continue
            try:
                out[r["date"][:10]] = float(r["close"].replace(",", ""))
            except (KeyError, ValueError):
                continue
    return out


def doi_chieu(rows, saved, phien):
    both = [r for r in rows if r["date"] in saved and r["date"] != phien][-CUA_SO:]
    if len(both) < TOI_THIEU:
        return {"so_phien": len(both), "dung_duoc": False, "ghi_chu": f"chưa đủ {TOI_THIEU} phiên trùng với file đã lưu"}
    # file đã lưu ghi 2 chữ số thập phân (nghìn đồng); giá đã điều chỉnh của nguồn có thể lẻ hơn -> làm tròn trước khi so
    lech = [r for r in both if abs(round(r["close"], 2) - saved[r["date"]]) > TOL]
    if not lech:
        return {"so_phien": len(both), "dung_duoc": True, "ghi_chu": "khớp tuyệt đối"}
    # lệch chỉ ở các phiên cũ, theo một tỷ lệ gần như không đổi -> do điều chỉnh giá
    # Điều kiện: lệch là MỘT ĐOẠN LIỀN các phiên cũ nhất (mọi phiên trước mốc đều lệch, mọi phiên sau đều khớp),
    # ít nhất 2 phiên, cùng một tỷ lệ, và ít nhất 3 phiên gần nhất khớp tuyệt đối.
    ratios = [round(r["close"], 2) / saved[r["date"]] for r in lech]
    k = len(lech)
    lien = [r["date"] for r in both[:k]] == [r["date"] for r in lech]
    deu = max(ratios) - min(ratios) < 0.002
    if lien and k >= 2 and deu and len(both) - k >= 3:
        return {"so_phien": len(both), "dung_duoc": True, "lech_do_dieu_chinh": True,
                "phien_lech": [r["date"] for r in lech], "ty_le": round(sum(ratios) / len(ratios), 5),
                "ghi_chu": "phiên cũ lệch theo một tỷ lệ (nguồn và file đã lưu điều chỉnh khác nhau); các phiên gần nhất khớp"}
    return {"so_phien": len(both), "dung_duoc": False,
            "phien_lech": [{"ngay": r["date"], "nguon": round(r["close"], 2), "file_luu": saved[r["date"]]} for r in lech[:5]],
            "ghi_chu": "CÓ PHIÊN LỆCH: không dùng nguồn này cho mã này lần chạy này"}


def khop_cheo(r1, r2, phien, n=5):
    """So giá đóng cửa của n phiên ngay trước phiên cần lấy giữa hai nguồn (cho phép lệch làm tròn TOL_CU)."""
    d2 = {r["date"]: r["close"] for r in r2}
    chung = [r for r in r1 if r["date"] in d2 and r["date"] < phien][-n:]
    lech = [r["date"] for r in chung if abs(r["close"] - d2[r["date"]]) > TOL_CU]
    return len(chung), lech


def chi_so(phien, now, lich_su=0, out_dir="."):
    """VN-Index và VN30 của phiên từ Vietcap (MỘT nguồn cấp 2 -> nhãn ◐; cần thêm một nguồn nữa để thành ✔)."""
    den = dt.date.fromisoformat(phien)
    out = {}
    for ten in ("VNINDEX", "VN30"):
        raw, err = fetch_vci(ten, den - dt.timedelta(days=12), den, lich_su + 10 if lich_su else None)
        if err or not isinstance(raw, list) or not raw or "accumulatedValue" not in raw[0]:
            out[ten] = {"nhan": "⊘", "loi": err or "cấu trúc đã đổi"}
            continue
        x = raw[0]
        ds = [dt.datetime.fromtimestamp(int(t), VN).date().isoformat() for t in x["t"]]
        if phien not in ds or (phien == now.date().isoformat() and now.time() < dt.time(15, 5)):
            out[ten] = {"nhan": "⊘", "loi": f"chưa có phiên {phien} (hoặc phiên chưa kết thúc)"}
            continue
        i = ds.index(phien)
        if i == 0:
            out[ten] = {"nhan": "⊘", "loi": "không có phiên trước để tính thay đổi"}
            continue
        c, p = x["c"][i], x["c"][i - 1]
        out[ten] = {"nhan": "◐", "nguon": "Vietcap (cấp 2, một nguồn)", "dong_cua": round(c, 2),
                    "phien_truoc": {"ngay": ds[i - 1], "dong_cua": round(p, 2)},
                    "thay_doi_diem": round(c - p, 2), "thay_doi_pct": round((c / p - 1) * 100, 2),
                    "cao": round(x["h"][i], 2), "thap": round(x["l"][i], 2),
                    "khoi_luong_cp": x["v"][i],
                    "gia_tri_ty_dong_gom_thoa_thuan": round(x["accumulatedValue"][i] / 1000, 1)}
        if lich_su:
            path = os.path.join(out_dir, f"gia_{ten}_ctck.csv")
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["date", "open", "high", "low", "close", "volume"])
                for j in range(i + 1):
                    w.writerow([ds[j]] + [round(x[k][j], 2) for k in "ohlc"] + [x["v"][j]])
            out[ten]["file"] = path
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ma", nargs="+")
    ap.add_argument("--phien", required=True, help="phiên cần lấy yyyy-mm-dd")
    ap.add_argument("--nguon", nargs="+", default=["kbs", "vci"], choices=["kbs", "vci"])
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--doi-chieu", nargs="*", default=[], help="MÃ=file_gia_da_luu.csv")
    ap.add_argument("--tu-file", nargs="*", default=[],
                    help="nguon=file.json (JSON gốc đã lấy qua trình duyệt; có thể chứa nhiều mã: {MÃ: json gốc})")
    ap.add_argument("--lich-su", type=int, default=0,
                    help="số phiên lịch sử cần lấy (vd 540 cho bản tin, 1500 cho phân tích sâu). Khi có, file "
                         "gia_<MÃ>_ctck.csv chứa đủ lịch sử: giá đã điều chỉnh của Vietcap (làm tròn 2 số, khớp file "
                         "giá của dự án), khối lượng của KBS nếu có.")
    ap.add_argument("--chi-so", action="store_true", help="lấy thêm VN-Index, VN30 của phiên từ Vietcap (nhãn ◐)")
    ap.add_argument("--bay-gio", help="(chạy thử) giờ Việt Nam yyyy-mm-ddTHH:MM")
    a = ap.parse_args()

    now = dt.datetime.fromisoformat(a.bay_gio).replace(tzinfo=VN) if a.bay_gio else dt.datetime.now(VN)
    phien = a.phien
    den = dt.date.fromisoformat(phien)
    tu = den - dt.timedelta(days=max(30, int(a.lich_su * 1.55)))
    saved_paths = dict(x.split("=", 1) for x in a.doi_chieu)
    files = {}
    for x in a.tu_file:
        k, p = x.split("=", 1)
        with open(p, encoding="utf-8") as f:
            if p.endswith(".csv"):
                # định dạng gọn: mỗi dòng "MÃ,yyyy-mm-dd,mở,cao,thấp,đóng,khối lượng" (giá theo ĐỒNG, như API trả)
                gon = {}
                for line in f:
                    parts = [x.strip() for x in line.strip().split(",")]
                    if len(parts) != 7 or not parts[1][:4].isdigit():
                        continue
                    gon.setdefault(parts[0].upper(), []).append(tuple([parts[1]] + parts[2:]))
                files[k] = {"__gon__": gon}
            else:
                files[k] = json.load(f)
    os.makedirs(a.out_dir, exist_ok=True)
    report = {"phien": phien, "luc_chay": now.isoformat(timespec="minutes"), "ma": {}}

    for ma in [m.upper() for m in a.ma]:
        saved = load_saved(saved_paths[ma], ma) if ma in saved_paths else {}
        info = {"nguon": {}}
        dung = {}
        for src in a.nguon:
            gon = files.get(src, {}).get("__gon__") if isinstance(files.get(src), dict) else None
            if gon is not None:
                raw, err = None, (None if ma in gon else "file gọn không có mã này")
            elif src in files:
                raw = files[src].get(ma, files[src]) if isinstance(files[src], dict) and ma in files[src] else files[src]
                err = None
            else:
                raw, err = fetch_kbs(ma, tu, den) if src == "kbs" else fetch_vci(ma, tu, den, a.lich_su + 10 if a.lich_su else None)
            if err:
                info["nguon"][src] = {"lay_duoc": False, "loi": err}
                continue
            if gon is not None:
                rows, err = gon[ma], None
            else:
                rows, err = (parse_kbs if src == "kbs" else parse_vci)(ma, raw)
            if err:
                info["nguon"][src] = {"lay_duoc": False, "loi": err}
                continue
            rows, bad = clean(rows, now)
            hit = next((r for r in rows if r["date"] == phien), None)
            dc = doi_chieu(rows, saved, phien) if saved else {
                "dung_duoc": True, "ghi_chu": "không có file đã lưu để đối chiếu; chỉ dựa vào so hai nguồn với nhau"}
            info["nguon"][src] = {"lay_duoc": True, "so_phien": len(rows), "dong_bi_loai": bad,
                                  "co_phien_can_lay": hit is not None, "doi_chieu": dc}
            if hit and dc["dung_duoc"]:
                dung[src] = (hit, rows)
        # nhãn cho phiên cần lấy
        if len(dung) == 2:
            (h1, _), (h2, _) = dung["kbs"], dung["vci"]
            khop = all(abs(h1[k] - h2[k]) <= TOL for k in ("open", "high", "low", "close"))
            n_cheo, lech_cheo = khop_cheo(dung["kbs"][1], dung["vci"][1], phien)
            info["so_hai_nguon"] = {"phien_can_lay_khop": khop, "so_phien_truoc_da_so": n_cheo, "phien_truoc_lech": lech_cheo}
            nhan = "✔" if khop and n_cheo >= 3 and not lech_cheo else "✖"
        elif len(dung) == 1:
            nhan = "◐"
        else:
            nhan = "⊘"
        info["phien_can_lay"] = {"nhan": nhan, **{s: {k: v for k, v in h.items() if k != "date"} for s, (h, _) in dung.items()}}
        if nhan == "✖":
            info["phien_can_lay"]["ghi_chu"] = "hai nguồn khác nhau: không chọn số nào, ghi cả hai vào phụ lục"
        if nhan in ("✔", "◐"):
            if a.lich_su and "vci" in dung:
                # lịch sử: giá điều chỉnh của Vietcap (làm tròn 2 số như file dự án), khối lượng KBS nếu có
                kl = {r["date"]: r["volume"] for r in dung["kbs"][1]} if "kbs" in dung else {}
                out_rows = [{**{k: (round(v, 2) if k != "date" else v) for k, v in r.items() if k != "volume"},
                             "volume": kl.get(r["date"], r["volume"])} for r in dung["vci"][1] if r["date"] <= phien]
            else:
                out_rows = [r for r in dung["kbs" if "kbs" in dung else "vci"][1] if r["date"] <= phien]
            path = os.path.join(a.out_dir, f"gia_{ma}_ctck.csv")
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["date", "open", "high", "low", "close", "volume"])
                w.writeheader()
                w.writerows(out_rows)
            info["file"] = path
            info["so_phien_trong_file"] = len(out_rows)
        report["ma"][ma] = info

    if a.chi_so:
        report["chi_so"] = chi_so(phien, now, a.lich_su, a.out_dir)
    nhan = {m: v["phien_can_lay"]["nhan"] for m, v in report["ma"].items()}
    report["tom_tat"] = " · ".join(f"{m} {n}" for m, n in nhan.items())
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()
    sys.exit(0 if any(n in ("✔", "◐") for n in nhan.values()) else 2)


if __name__ == "__main__":
    main()
