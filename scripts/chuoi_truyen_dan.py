#!/usr/bin/env python3
"""CHUỖI TRUYỀN DẪN vĩ mô: cú sốc bên ngoài (dầu, Fed, USD) đã truyền tới đâu trên đường vào chứng khoán Việt Nam.

Đọc von-ngoai.csv (cùng file với ap_luc_von_ngoai.py) và file giá VN-Index, in từng mắt xích:
số mới nhất, ngày của số, thay đổi so với số liền trước và so với khoảng 5 phiên trước, có vượt ngưỡng
"đáng kể" hay không; rồi nêu lực nào đang thắng trên lợi suất Mỹ và mắt xích nào KHÔNG chuyển động dù
mắt xích trước đã chuyển động ("chỗ đứt"). Chỉ là quan sát cơ học trên số đã thu thập: không kết luận
nguyên nhân, không dự báo, không phải khuyến nghị mua/bán.

Cách dùng:
    python chuoi_truyen_dan.py von-ngoai.csv --vnindex gia_VNINDEX_ctck.csv            # in JSON
    python chuoi_truyen_dan.py von-ngoai.csv --vnindex gia_VNINDEX_ctck.csv --chu      # bản chữ cho bản tin/báo cáo
    python chuoi_truyen_dan.py von-ngoai.csv --them-cot    # thêm 3 cột mới vào file cũ (chạy một lần, không đổi số đã có)

Dùng các cột đã có của von-ngoai.csv (brent, ust10y, ust2y, dxy, fed_xs_tang, usd_vnd_nh_ban,
lien_nh_qua_dem, omo_rong_ty, kn_rong_hose_ty) và 3 cột thêm (ô trống = không lấy được, KHÔNG điền đoán):
    lam_phat_ky_vong_5y   breakeven lạm phát Mỹ 5 năm (%), FRED chuỗi T5YIE
    vix                   chỉ số VIX (đóng cửa phiên Mỹ đêm trước)
    vang                  giá vàng giao ngay (USD/ounce)
"""
import argparse
import csv
import datetime as dt
import io
import json
import sys

COT_MOI = ["lam_phat_ky_vong_5y", "vix", "vang"]

# (khóa, tên, cột, kiểu thay đổi, ngưỡng đáng kể, đơn vị hiển thị)
#   kiểu "pct": % thay đổi · "bp": điểm cơ bản (cột tính bằng %) · "diem": điểm phần trăm · "abs": giá trị tuyệt đối
MAT_XICH = [
    ("brent", "Dầu Brent", "brent", "pct", 2.0, "USD/thùng"),
    ("lam_phat", "Kỳ vọng lạm phát Mỹ 5 năm", "lam_phat_ky_vong_5y", "bp", 5.0, "%"),
    ("fed", "Xác suất Fed tăng kỳ tới", "fed_xs_tang", "diem", 10.0, "%"),
    ("ust2y", "Lợi suất Mỹ 2 năm", "ust2y", "bp", 5.0, "%"),
    ("ust10y", "Lợi suất Mỹ 10 năm", "ust10y", "bp", 5.0, "%"),
    ("dxy", "DXY", "dxy", "pct", 0.5, "điểm"),
    ("vix", "VIX", "vix", "pct", 10.0, "điểm"),
    ("vang", "Vàng", "vang", "pct", 1.0, "USD/ounce"),
    ("usd_vnd", "Giá bán USD Vietcombank", "usd_vnd_nh_ban", "pct", 0.2, "đồng"),
    ("qua_dem", "Liên ngân hàng qua đêm", "lien_nh_qua_dem", "diem", 0.5, "%"),
    ("omo", "NHNN bơm(+)/hút(−) ròng", "omo_rong_ty", "abs", 5000.0, "tỷ đồng"),
    ("khoi_ngoai", "Khối ngoại ròng HOSE", "kn_rong_hose_ty", "abs", 500.0, "tỷ đồng"),
]
NHOM = [
    ("1. Cú sốc và kỳ vọng lạm phát", ["brent", "lam_phat"]),
    ("2. Fed, lợi suất và USD", ["fed", "ust2y", "ust10y", "dxy"]),
    ("3. Né rủi ro", ["vix", "vang"]),
    ("4. Việt Nam: tỷ giá và thanh khoản VND", ["usd_vnd", "qua_dem", "omo"]),
    ("5. Dòng vốn và kết quả", ["khoi_ngoai", "vnindex"]),
]
# Cặp (mắt xích trước, mắt xích sau, cùng chiều?) dùng để tìm chỗ đứt
CAP = [
    ("brent", "lam_phat", True),
    ("lam_phat", "ust2y", True),
    ("dxy", "usd_vnd", True),
    ("dxy", "khoi_ngoai", False),
    ("khoi_ngoai", "vnindex", True),
]
SO_CU_NGAY = 5  # số mới nhất cũ hơn chừng này ngày so với dòng cuối thì coi là "số cũ"


def num(v):
    v = (v or "").strip().replace(",", "")
    if v in ("", "-", "null", "None", "NA"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def doc_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        try:
            d = dt.date.fromisoformat((r.get("date") or "").strip()[:10])
        except ValueError:
            continue
        out.append((d, r))
    out.sort(key=lambda x: x[0])
    return out


def chuoi(rows, cot):
    """Danh sách (ngày, giá trị) của các ô không trống, cũ -> mới; trùng ngày thì giữ số sau."""
    d = {}
    for ngay, r in rows:
        v = num(r.get(cot))
        if v is not None:
            d[ngay] = v
    return sorted(d.items())


def doi(kieu, moi, cu):
    if moi is None or cu is None:
        return None
    if kieu == "pct":
        return None if cu == 0 else (moi / cu - 1) * 100
    if kieu == "bp":
        return (moi - cu) * 100
    return moi - cu


def do_mat_xich(khoa, ten, s, kieu, nguong, don_vi, ngay_cuoi):
    if not s:
        return {"khoa": khoa, "ten": ten, "co_so": False}
    ngay, moi = s[-1]
    truoc = s[-2] if len(s) >= 2 else None
    tuan = s[-6] if len(s) >= 6 else None
    if kieu == "abs":
        # dòng tiền: bản thân con số đã là thay đổi trong ngày; "đáng kể" khi tổng 5 số gần nhất
        # vượt 3 lần ngưỡng (chiều theo tổng), hoặc riêng số mới nhất vượt ngưỡng
        d1 = moi
        tong5 = sum(v for _, v in s[-5:])
        if abs(tong5) >= 3 * nguong:
            dong, chieu = True, (1 if tong5 > 0 else -1)
        elif abs(moi) >= nguong:
            dong, chieu = True, (1 if moi > 0 else -1)
        else:
            dong, chieu = False, 0
        rec = {"tong_5_so_gan_nhat": round(tong5, 2), "so_so_trong_tong": min(5, len(s))}
    else:
        d1 = doi(kieu, moi, truoc[1]) if truoc else None
        d5 = doi(kieu, moi, tuan[1]) if tuan else None
        # xét thay đổi qua 5 số gần nhất nếu có (cú sốc thường mất vài phiên để truyền), không thì số liền trước
        xet = d5 if d5 is not None else d1
        dong = xet is not None and abs(xet) >= nguong
        chieu = (1 if xet > 0 else -1) if dong else 0
        rec = {"doi_5_so": None if d5 is None else round(d5, 2), "ngay_so_5": tuan[0].isoformat() if tuan else None}
    rec.update({
        "khoa": khoa, "ten": ten, "co_so": True, "gia_tri": moi, "ngay": ngay.isoformat(), "don_vi": don_vi,
        "kieu": kieu, "nguong": nguong,
        "doi_lien_truoc": None if d1 is None else round(d1, 2),
        "ngay_lien_truoc": truoc[0].isoformat() if truoc else None,
        "dang_ke": bool(dong), "chieu": chieu,
        "so_cu": (ngay_cuoi - ngay).days > SO_CU_NGAY if ngay_cuoi else False,
    })
    return rec


def doc_vnindex(path):
    if not path:
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        r = {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
        try:
            out.append((dt.date.fromisoformat(r["date"][:10]), float(r["close"].replace(",", ""))))
        except (KeyError, ValueError):
            continue
    return sorted(out)


def phan_tich(rows, vnindex):
    ngay_cuoi = rows[-1][0] if rows else None
    if vnindex and (ngay_cuoi is None or vnindex[-1][0] > ngay_cuoi):
        ngay_cuoi = vnindex[-1][0]
    mx = {}
    for khoa, ten, cot, kieu, nguong, dv in MAT_XICH:
        mx[khoa] = do_mat_xich(khoa, ten, chuoi(rows, cot), kieu, nguong, dv, ngay_cuoi)
    mx["vnindex"] = do_mat_xich("vnindex", "VN-Index", vnindex, "pct", 1.0, "điểm", ngay_cuoi)

    def c(k):  # chiều của mắt xích nếu có số mới và đáng kể
        m = mx[k]
        return m["chieu"] if m.get("co_so") and not m.get("so_cu") and m.get("dang_ke") else 0

    def co(k):
        m = mx[k]
        return m.get("co_so") and not m.get("so_cu")

    # Lực nào đang thắng trên lợi suất Mỹ 10 năm
    lp = c("brent") > 0 or c("lam_phat") > 0
    ne = c("vix") > 0 or c("vang") > 0
    if not co("ust10y"):
        luc = "chưa có số lợi suất Mỹ 10 năm mới nên chưa đọc được"
    elif c("ust10y") > 0 and lp and not ne:
        luc = "lợi suất tăng cùng dầu/kỳ vọng lạm phát: lực lạm phát đang thắng"
    elif c("ust10y") < 0 and ne:
        luc = "lợi suất giảm trong khi VIX/vàng tăng: lực né rủi ro đang thắng"
    elif c("ust10y") > 0 and ne:
        luc = "lợi suất tăng dù VIX/vàng tăng: lực lạm phát hoặc kỳ vọng Fed lấn át né rủi ro"
    elif c("ust10y") < 0 and lp:
        luc = "lợi suất giảm dù dầu/kỳ vọng lạm phát tăng: thị trường lo tăng trưởng hơn lo lạm phát"
    elif c("ust10y") == 0 and (lp or ne):
        luc = "lợi suất chưa phản ứng (hai lực đang triệt tiêu nhau hoặc cú sốc chưa đủ lớn)"
    elif c("ust10y") != 0:
        luc = ("lợi suất " + ("tăng" if c("ust10y") > 0 else "giảm")
               + " nhưng không đi cùng dầu, kỳ vọng lạm phát hay né rủi ro: lý do nằm ở kỳ vọng Fed hoặc số liệu Mỹ (xem F1)")
    else:
        luc = "không có lực nào nổi bật"

    # Chỗ đứt: mắt xích trước đáng kể mà mắt xích sau không động hoặc động ngược chiều kỳ vọng
    dut, noi, chua = [], [], []
    for a, b, cung in CAP:
        if c(a) == 0:
            continue
        if not co(b):
            chua.append(f"{mx[a]['ten']} → {mx[b]['ten']}")
            continue
        ky_vong = c(a) if cung else -c(a)
        if c(b) == 0:
            dut.append({"tu": mx[a]["ten"], "den": mx[b]["ten"], "kieu": "khong_phan_ung",
                        "mo_ta": f"{mx[a]['ten']} đã chuyển động nhưng {mx[b]['ten']} chưa phản ứng"})
        elif c(b) != ky_vong:
            dut.append({"tu": mx[a]["ten"], "den": mx[b]["ten"], "kieu": "nguoc_chieu",
                        "mo_ta": f"{mx[b]['ten']} đi ngược chiều thường thấy sau khi {mx[a]['ten']} chuyển động"})
        else:
            noi.append(f"{mx[a]['ten']} → {mx[b]['ten']}")

    ngoai = [k for k in ("brent", "lam_phat", "fed", "ust2y", "ust10y", "dxy", "vix", "vang") if c(k) != 0]
    thieu = [mx[k]["ten"] for k in mx if not mx[k].get("co_so")]
    cu = [f"{mx[k]['ten']} ({mx[k]['ngay']})" for k in mx if mx[k].get("co_so") and mx[k].get("so_cu")]
    return {
        "ngay_du_lieu_cuoi": ngay_cuoi.isoformat() if ngay_cuoi else None,
        "mat_xich": mx,
        "du_so_quoc_te": sum(1 for k in ("brent", "ust10y", "dxy") if co(k)) >= 2,
        "co_cu_soc_ben_ngoai": bool(ngoai),
        "mat_xich_ben_ngoai_dang_ke": [mx[k]["ten"] for k in ngoai],
        "luc_tren_loi_suat_my": luc,
        "da_truyen": noi,
        "cho_dut": dut,
        "chua_doi_chieu_duoc": chua,
        "chua_co_so": thieu,
        "so_cu": cu,
        "luu_y": "Quan sát cơ học trên số đã thu thập; nhãn ✔/◐ của từng số xem kiem-chung.csv và cột nguon. "
                 "Loại cú sốc dầu (cung hay cầu) và lý do của chỗ đứt chỉ được ghi khi có tin có nguồn. "
                 "Không phải tín hiệu mua/bán.",
    }


def so(v):
    if v is None:
        return "?"
    s = f"{v:,.2f}".rstrip("0").rstrip(".")
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def dm(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.day:02d}/{d.month:02d}"


def cau(m):
    if not m.get("co_so"):
        return f"- {m['ten']}: chưa có số liệu"
    dv = {"pct": "%", "bp": " điểm cơ bản", "diem": " điểm %", "abs": ""}[m["kieu"]]
    s = f"- {m['ten']}: {so(m['gia_tri'])} {m['don_vi']} ({dm(m['ngay'])})"
    if m["kieu"] == "abs":
        s += f"; tổng {m['so_so_trong_tong']} số gần nhất {so(m['tong_5_so_gan_nhat'])}"
    else:
        if m["doi_lien_truoc"] is not None:
            s += f"; {'+' if m['doi_lien_truoc'] > 0 else ''}{so(m['doi_lien_truoc'])}{dv} so với {dm(m['ngay_lien_truoc'])}"
        if m.get("doi_5_so") is not None:
            s += f"; {'+' if m['doi_5_so'] > 0 else ''}{so(m['doi_5_so'])}{dv} so với {dm(m['ngay_so_5'])}"
    if m.get("so_cu"):
        s += " · SỐ CŨ, không dùng để đọc chuỗi"
    elif m["dang_ke"]:
        s += " · ĐÁNG KỂ " + ("↑" if m["chieu"] > 0 else "↓")
    else:
        s += " · yên"
    return s


def ban_chu(kq):
    L = [f"Chuỗi truyền dẫn – dữ liệu đến {kq['ngay_du_lieu_cuoi']}"]
    for ten, ds in NHOM:
        L.append(ten)
        L += [cau(kq["mat_xich"][k]) for k in ds]
    L.append("Đọc chuỗi")
    if not kq["du_so_quoc_te"]:
        L.append("- Chưa đủ số quốc tế mới để đọc chuỗi (xem danh sách thiếu bên dưới); không kết luận \"không có cú sốc\".")
    elif not kq["co_cu_soc_ben_ngoai"]:
        L.append("- Không có cú sốc mới từ bên ngoài (không mắt xích quốc tế nào vượt ngưỡng).")
    else:
        L.append("- Mắt xích quốc tế đang chuyển động: " + ", ".join(kq["mat_xich_ben_ngoai_dang_ke"]) + ".")
    L.append("- Lợi suất Mỹ: " + kq["luc_tren_loi_suat_my"] + ".")
    if kq["da_truyen"]:
        L.append("- Đã truyền: " + "; ".join(kq["da_truyen"]) + ".")
    for d in kq["cho_dut"]:
        L.append("- Chỗ đứt: " + d["mo_ta"] + ".")
    if kq["chua_doi_chieu_duoc"]:
        L.append("- Chưa đối chiếu được (mắt xích sau thiếu số mới): " + "; ".join(kq["chua_doi_chieu_duoc"]) + ".")
    if kq["co_cu_soc_ben_ngoai"] and not kq["cho_dut"]:
        L.append("- Chưa thấy chỗ đứt trong các cặp có số.")
    if kq["chua_co_so"]:
        L.append("- Chưa có số liệu: " + ", ".join(kq["chua_co_so"]) + ".")
    if kq["so_cu"]:
        L.append("- Số cũ: " + ", ".join(kq["so_cu"]) + ".")
    L.append("- " + kq["luu_y"])
    return "\n".join(L)


def them_cot(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(io.StringIO(f.read())))
    if not rows:
        sys.exit("File rỗng.")
    h = rows[0]
    thieu = [c for c in COT_MOI if c not in h]
    if not thieu:
        print(json.dumps({"da_them": [], "ghi_chu": "file đã đủ cột"}, ensure_ascii=False))
        return
    n = len(h)
    vi_tri = h.index("nguon") if "nguon" in h else n  # chèn trước cột nguon để nguon vẫn là cột cuối
    moi = []
    for i, r in enumerate(rows):
        r = r + [""] * (n - len(r))
        moi.append(r[:vi_tri] + (thieu if i == 0 else [""] * len(thieu)) + r[vi_tri:])
    with open(path, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(moi)
    print(json.dumps({"da_them": thieu, "so_dong": len(moi) - 1}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("csv", help="von-ngoai.csv")
    p.add_argument("--vnindex", help="file giá VN-Index (cột date, close)")
    p.add_argument("--chu", action="store_true", help="in bản chữ thay vì JSON")
    p.add_argument("--them-cot", action="store_true", help="thêm các cột mới còn thiếu vào file rồi thoát")
    a = p.parse_args()
    if a.them_cot:
        them_cot(a.csv)
        return
    kq = phan_tich(doc_csv(a.csv), doc_vnindex(a.vnindex))
    print(ban_chu(kq) if a.chu else json.dumps(kq, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
