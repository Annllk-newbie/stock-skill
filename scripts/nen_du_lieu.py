#!/usr/bin/env python3
"""Nén dữ liệu tích lũy và tạo bản tóm tắt ngắn để các lần chạy KHÔNG phải đọc lại cả file CSV.

Cách dùng (chạy CUỐI mỗi lần chạy, sau khi đã ghi thêm dòng mới):
    python nen_du_lieu.py --thu-muc <thư mục chứa file đã tải về> --ngay 2026-11-08 \
        [--giu kiem-chung.csv=30 tham-chieu.csv=30 su-kien-nen-tang.csv=60 von-ngoai.csv=120]

Thư mục làm việc nên có cấu trúc giống dự án claude/chung-khoan/:
    data/MBB.csv, data/TCB.csv, data/CTG.csv, data/HPG.csv   (giá – KHÔNG cắt, script phân tích cần đủ 5 năm)
    data/von-ngoai.csv, data/kiem-chung.csv, data/tham-chieu.csv, su-kien-nen-tang.csv
                                                               (nhật ký – cắt theo số ngày giữ lại)
    <MÃ>/su-kien.csv                                           (KHÔNG cắt: kiểm định sự kiện cần đủ lịch sử)
    ap_luc_von_ngoai.json                                       (nếu có, để lấy điểm hiện tại)

Việc script làm:
 1. Với mỗi file nhật ký: giữ trong file chính các dòng trong N ngày gần nhất; dòng cũ hơn được
    CHUYỂN (không xóa) sang MỘT file luu-tru/<tên>.csv cho mỗi nhật ký (ghi thêm, không trùng dòng).
    Không tạo file theo quý: số file trong dự án không tăng theo thời gian.
    Dòng ◐/✖ còn mở trong kiem-chung.csv luôn được giữ lại dù cũ.
 2. Ghi data/TOM-TAT.md (khoảng 40–60 dòng): giá đóng cửa gần nhất 4 mã, điểm áp lực khối ngoại,
    các số ◐/✖ còn mở, tin tham chiếu và tin nền tảng mới nhất, số dòng mỗi file, file lưu trữ.
    Mọi lần chạy đọc file này TRƯỚC; chỉ mở CSV gốc bằng script khi thật sự cần chi tiết.
In ra JSON ngắn: các file đã nén, số dòng chuyển sang lưu trữ, đường dẫn các file cần ghi lại vào dự án.
"""
import argparse
import csv
import datetime as dt
import io
import json
import os
import sys

MA = ["MBB", "TCB", "CTG", "HPG"]
MAC_DINH = {
    "data/kiem-chung.csv": 30,
    "data/tham-chieu.csv": 30,
    "su-kien-nen-tang.csv": 60,
    "data/von-ngoai.csv": 120,  # cần >= 8 tuần và >= 40 phiên để tự kiểm chứng
}
COT_NGAY = ("date", "ngay", "ngay_du_lieu", "ngay_kiem")


def doc(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        txt = f.read()
    rows = list(csv.reader(io.StringIO(txt)))
    if not rows:
        return [], []
    return rows[0], [r for r in rows[1:] if any(c.strip() for c in r)]


def ghi(path, header, rows):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def parse_ngay(s):
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return dt.datetime.strptime(s[:10], fmt).date()
        except ValueError:
            pass
    return None


def chi_so_ngay(header):
    low = [h.strip().lower() for h in header]
    for c in COT_NGAY:
        if c in low:
            return low.index(c)
    return 0


def con_mo(header, row):
    low = [h.strip().lower() for h in header]
    if "nhan" not in low:
        return False
    return row[low.index("nhan")].strip() in ("◐", "✖")


def nen_file(goc, rel, so_ngay, hom_nay):
    path = os.path.join(goc, rel)
    if not os.path.exists(path):
        return None
    header, rows = doc(path)
    if not header:
        return None
    i = chi_so_ngay(header)
    moc = hom_nay - dt.timedelta(days=so_ngay)
    giu, cu = [], []
    for r in rows:
        d = parse_ngay(r[i] if i < len(r) else "")
        if d is None or d >= moc or (rel.endswith("kiem-chung.csv") and con_mo(header, r) and d >= hom_nay - dt.timedelta(days=90)):
            giu.append(r)
        else:
            cu.append((d, r))
    ghi_luu = []
    if cu:
        # MỘT file lưu trữ cho mỗi nhật ký (không chia theo quý). File này phải được agent T tải về trước
        # (nếu đã có trong dự án) để dòng cũ không bị ghi đè; xem danh sách tải trong ban-tin-sang.md.
        ten = os.path.basename(rel).rsplit(".", 1)[0]
        luu_rel = "luu-tru/" + ten + ".csv"
        luu = os.path.join(goc, luu_rel)
        old = []
        if os.path.exists(luu):
            _, old = doc(luu)
        seen = {tuple(x) for x in old}
        ghi(luu, header, old + [r for _, r in sorted(cu, key=lambda x: x[0]) if tuple(r) not in seen])
        ghi_luu.append(luu_rel)
        ghi(path, header, giu)
    return {"file": rel, "giu": len(giu), "chuyen_luu_tru": len(cu), "luu_tru": ghi_luu}


def gia_cuoi(goc, ma):
    p = os.path.join(goc, "data", f"{ma}.csv")
    if not os.path.exists(p):
        return None
    h, rows = doc(p)
    if not rows:
        return None
    low = [x.lower() for x in h]
    r = rows[-1]
    get = lambda k: r[low.index(k)] if k in low and low.index(k) < len(r) else ""
    tam = all(get(k) == get("close") for k in ("open", "high", "low")) and not get("volume")
    return f"{ma}: {get('close')} ({get('date')}){' – dòng tạm' if tam else ''} · {len(rows)} phiên trong file"


def tom_tat(goc, hom_nay, ket_qua):
    L = [f"# Tóm tắt dữ liệu – cập nhật {hom_nay.isoformat()}", "",
         "Đọc file này trước. Chỉ mở CSV gốc bằng script khi cần chi tiết; không dán nội dung CSV vào báo cáo.", "",
         "## Giá đóng cửa gần nhất (nghìn đồng; TCB đã quy đổi sau 29/10/2026)"]
    for m in MA:
        g = gia_cuoi(goc, m)
        L.append(f"- {g}" if g else f"- {m}: không có file giá")
    L += ["", "## Dòng vốn ngoại"]
    pj = os.path.join(goc, "ap_luc_von_ngoai.json")
    if os.path.exists(pj):
        try:
            j = json.load(open(pj, encoding="utf-8"))
            diem = j.get("diem") or j.get("diem_ap_luc")
            muc = j.get("muc") or j.get("muc_do")
            L.append(f"- Điểm áp lực: {diem} ({muc}); độ phủ {j.get('do_phu', '?')}; kiểm chứng: {j.get('kiem_chung', {}).get('trang_thai', 'chưa') if isinstance(j.get('kiem_chung'), dict) else j.get('kiem_chung', 'chưa')}")
        except Exception as e:  # noqa: BLE001
            L.append(f"- Không đọc được ap_luc_von_ngoai.json ({e})")
    vp = os.path.join(goc, "data", "von-ngoai.csv")
    if os.path.exists(vp):
        h, rows = doc(vp)
        low = [x.lower() for x in h]
        k = low.index("kn_rong_hose_ty") if "kn_rong_hose_ty" in low else None
        co = sorted((r for r in rows if k is not None and k < len(r) and r[k].strip()), key=lambda r: r[0])
        for r in co[-5:]:
            L.append(f"- {r[0]}: khối ngoại HOSE {r[k].strip()} tỷ")
        if not co:
            L.append("- Chưa có số khối ngoại HOSE")
    L += ["", "## Số còn ◐/✖ (chưa kiểm chứng xong)"]
    kp = os.path.join(goc, "data", "kiem-chung.csv")
    if os.path.exists(kp):
        h, rows = doc(kp)
        # dòng mới nhất cho mỗi (ngày, mục)
        last = {}
        for r in rows:
            last[(r[0], r[1] if len(r) > 1 else "")] = r
        mo = [r for r in last.values() if con_mo(h, r)]
        for r in mo[-12:]:
            L.append(f"- {r[0]} · {r[1]} = {r[2] if len(r) > 2 else ''} {r[3] if len(r) > 3 else ''}")
        if not mo:
            L.append("- Không có")
    for rel, tieu_de, n in (("data/tham-chieu.csv", "Tin doanh nghiệp tham chiếu mới nhất", 6),
                            ("su-kien-nen-tang.csv", "Tin nền tảng mới nhất", 6)):
        L += ["", f"## {tieu_de}"]
        p = os.path.join(goc, rel)
        if os.path.exists(p):
            h, rows = doc(p)
            for r in rows[-n:]:
                L.append("- " + " · ".join(c.strip()[:140] for c in r[:4] if c.strip()))
        else:
            L.append("- Chưa có file")
    L += ["", "## Nén lần này"]
    for k in ket_qua:
        if k:
            L.append(f"- {k['file']}: giữ {k['giu']} dòng, chuyển {k['chuyen_luu_tru']} dòng sang lưu trữ {', '.join(k['luu_tru']) or ''}".rstrip())
    out = os.path.join(goc, "data", "TOM-TAT.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return "data/TOM-TAT.md"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--thu-muc", required=True)
    ap.add_argument("--ngay", default=dt.date.today().isoformat())
    ap.add_argument("--giu", nargs="*", default=[], help="tên_file=số_ngày (ghi đè mặc định)")
    a = ap.parse_args()
    hom_nay = parse_ngay(a.ngay)
    cfg = dict(MAC_DINH)
    for s in a.giu:
        k, v = s.split("=", 1)
        for key in list(cfg):
            if key.endswith(k):
                cfg[key] = int(v)
    kq = [nen_file(a.thu_muc, rel, n, hom_nay) for rel, n in cfg.items()]
    tt = tom_tat(a.thu_muc, hom_nay, kq)
    can_ghi = [k["file"] for k in kq if k and k["chuyen_luu_tru"]] + sorted({x for k in kq if k for x in k["luu_tru"]}) + [tt]
    print(json.dumps({"ket_qua": [k for k in kq if k], "can_ghi_lai_vao_du_an": can_ghi}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    sys.exit(main())
