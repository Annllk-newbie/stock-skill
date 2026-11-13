#!/usr/bin/env python3
"""Chạy MỘT LỆNH toàn bộ script tính toán của phân tích sâu cho mọi mã (thay cho ~35 lệnh rời).

Cách dùng (phiên chính, sau khi đã có giá, trạng thái từ dự án và đã gộp sự kiện mới vào <du-an>/<MÃ>/su-kien.csv):
    python scripts/chay_sau.py MBB TCB CTG HPG --gia-dir research/gia --du-an research/du-an --out research \
        --bieu-do MBB TCB [--nghi 2026-11-20 ...] [--kich-ban MBB=3:2 TCB=1:4] [--nhe]

Với mỗi mã, ghi vào <out>/<MÃ>/: cycles.json, kiem_dinh_chu_ky.json (+ .txt), risk.json, indicators.json,
kiem_dinh_su_kien.json (+ .txt; sự kiện = <MÃ>/su-kien.csv + luu-tru/su-kien-ma.csv + ngày đáo hạn VN30F sinh theo quy tắc); mã có biểu đồ thêm du_bao_6_phien.json, kiem_dinh_du_bao.json (+ .txt),
<MÃ>-6-phien.png, bieu_do_6_phien.txt. Lịch sử dự báo (<du-an>/<MÃ>/du-bao-6-phien[-dieu-chinh].json) được ghi thêm tại chỗ.
Toàn thị trường: <out>/ap_luc_von_ngoai.json và ap_luc.txt (nếu có <du-an>/data/von-ngoai.csv).
--nhe: bản giữa tuần – không chạy lại kiểm định chu kỳ và sự kiện (dùng kết quả lần trước nếu còn trên đĩa).

In ra bản tóm tắt ngắn (cũng ghi <out>/tom_tat_script.md) và ghi <out>/moc_nhap.md: phần SỐ của data/MOC-THEO-DOI.md
đã điền sẵn từ kết quả script; phiên chính chỉ thêm mốc "không còn đúng" và lịch sự kiện lấy từ báo cáo.
Script lỗi ở bước nào thì ghi "LỖI" kèm thông báo ở bước đó và chạy tiếp các bước còn lại.
"""
import argparse
import csv
import datetime as dt
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COT_SK = ["date", "event", "group", "source_url", "reliability", "note"]


def _doc_csv(path):
    if not os.path.isfile(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def _ngay_dau_cuoi(gia):
    ds = [r.get("date", "")[:10] for r in _doc_csv(gia)]
    ds = sorted(d for d in ds if len(d) == 10)
    return (dt.date.fromisoformat(ds[0]), dt.date.fromisoformat(ds[-1])) if ds else (None, None)


def su_kien_day_du(du_an, ma, gia, out):
    """Ghép file sự kiện cho kiểm định: <MÃ>/su-kien.csv + dòng của mã trong luu-tru/su-kien-ma.csv
    + ngày đáo hạn VN30F sinh theo quy tắc (thứ 5 tuần thứ ba mỗi tháng) trên cả khoảng giá.
    Ngày đáo hạn KHÔNG lưu trong dự án nữa (sinh lại mỗi lần chạy). Trả về (đường dẫn, số dòng) hoặc (None, 0)."""
    rows = _doc_csv(os.path.join(du_an, ma, "su-kien.csv"))
    rows += [r for r in _doc_csv(os.path.join(du_an, "luu-tru", "su-kien-ma.csv")) if r.get("ma", "").upper() == ma.upper()]
    for r in rows:
        r.setdefault("date", r.get("ngay", ""))
        r.setdefault("group", r.get("nhom", "") or "khong_nhom")
    co = {(r.get("date", "")[:10], r.get("group", "")) for r in rows}
    d0, d1 = _ngay_dau_cuoi(gia)
    if d0:
        y, m = d0.year, d0.month
        het = d1 + dt.timedelta(days=45)
        while dt.date(y, m, 1) <= het:
            t = dt.date(y, m, 1)
            t += dt.timedelta(days=(3 - t.weekday()) % 7 + 14)  # thứ 5 tuần thứ ba
            if d0 <= t <= het and (t.isoformat(), "dao_han_phai_sinh") not in co:
                rows.append({"date": t.isoformat(), "event": f"Đáo hạn hợp đồng tương lai VN30 (quy tắc thứ 5 tuần thứ ba, {m:02d}/{y})",
                             "group": "dao_han_phai_sinh", "source_url": "https://www.hnx.vn", "reliability": "vua",
                             "note": "ma=ALL. Sinh theo quy tắc lúc chạy, chưa đối chiếu lịch HNX; không điều chỉnh khi trùng ngày nghỉ."})
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    rows = [r for r in rows if r.get("date")]
    if not rows:
        return None, 0
    rows.sort(key=lambda r: r["date"])
    p = os.path.join(out, "su_kien_day_du.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COT_SK, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return p, len(rows)


def chay(args, out_json=None, out_txt=None):
    """Chạy một script. Đầu ra dạng '<chữ>...{json}' được tách: chữ -> out_txt, JSON -> out_json. Trả về (dict|None, lỗi|None)."""
    p = subprocess.run([sys.executable] + args, capture_output=True, text=True)
    if p.returncode != 0:
        return None, (p.stderr.strip().splitlines() or ["lỗi không rõ"])[-1][:300]
    s = p.stdout
    lines = s.split("\n")
    i = next((k for k, l in enumerate(lines) if l.startswith("{") or l.startswith("[")), None)
    d = None
    if i is not None:
        try:
            d = json.loads("\n".join(lines[i:]))
        except ValueError:
            d = None
    chu = "\n".join(lines[:i]).strip() if d is not None else s.strip()
    if d is not None and not chu:
        chu = p.stderr.strip()  # một số script in bản chữ ra stderr
    if out_json and d is not None:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    if out_txt and chu:
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write(chu + "\n")
    return d, None


def doc_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ma", nargs="+")
    ap.add_argument("--gia-dir", required=True)
    ap.add_argument("--du-an", required=True, help="thư mục trạng thái tải từ dự án (cấu trúc như claude/chung-khoan/)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--bieu-do", nargs="*", default=["MBB", "TCB"], help="mã có dự báo 6 phiên và biểu đồ")
    ap.add_argument("--nghi", nargs="*", default=[])
    ap.add_argument("--kich-ban", nargs="*", default=[], help="MÃ=đúng:sai (số lần kịch bản chính đã chấm)")
    ap.add_argument("--nhe", action="store_true", help="giữa tuần: không chạy lại kiểm định chu kỳ và sự kiện")
    a = ap.parse_args()
    kb = dict(x.split("=", 1) for x in a.kich_ban)
    V = os.path.join(a.gia_dir, "gia_VNINDEX_ctck.csv")
    S = lambda n: os.path.join(HERE, n)
    L, moc = [], []

    for ma in a.ma:
        G = os.path.join(a.gia_dir, f"gia_{ma}_ctck.csv")
        W = os.path.join(a.out, ma)
        os.makedirs(W, exist_ok=True)
        o = lambda n: os.path.join(W, n)
        if not os.path.isfile(G):
            L.append(f"## {ma}\n- LỖI: không có file giá {G}")
            continue
        loi = []

        def buoc(ten, args, js=None, txt=None):
            d, e = chay(args, js, txt)
            if e:
                loi.append(f"{ten}: {e}")
            return d

        cyc = buoc("cycles", [S("cycles.py"), G], o("cycles.json"))
        ind = buoc("indicators", [S("indicators.py"), G], o("indicators.json"))
        buoc("risk", [S("risk.py"), G], o("risk.json"))
        if a.nhe and os.path.isfile(o("kiem_dinh_chu_ky.json")):
            kc = doc_json(o("kiem_dinh_chu_ky.json"))
        else:
            cmd = [S("kiem_dinh.py"), "chu-ky", G, "--chu"] + (["--benchmark", V] if os.path.isfile(V) else [])
            kc = buoc("kiểm định chu kỳ", cmd, o("kiem_dinh_chu_ky.json"), o("kiem_dinh_chu_ky.txt"))
        sk, so_sk = (None, 0) if a.nhe else su_kien_day_du(a.du_an, ma, G, W)
        ks = None
        if sk:
            ks = buoc("kiểm định sự kiện", [S("kiem_dinh.py"), "su-kien", G, "--su-kien", sk, "--window", "3", "--chu"],
                      o("kiem_dinh_su_kien.json"), o("kiem_dinh_su_kien.txt"))

        fc = kd = None
        if ma in a.bieu_do:
            ls = next((p for p in (os.path.join(a.du_an, ma, "du-bao-6-phien-dieu-chinh.json"),
                                   os.path.join(a.du_an, ma, "du-bao-6-phien.json")) if os.path.isfile(p)),
                      os.path.join(a.du_an, ma, "du-bao-6-phien.json"))
            os.makedirs(os.path.dirname(ls), exist_ok=True)
            muc = []
            if ind:
                hk = ind.get("ho_tro_khang_cu") or {}
                muc = [str(x[0]["muc"]) for x in (hk.get("ho_tro_gan_nhat"), hk.get("khang_cu_gan_nhat")) if x]
            cmd = [S("forecast6.py"), G, "--lich-su", ls] + (["--muc"] + muc if muc else []) + (["--nghi"] + a.nghi if a.nghi else [])
            fc = buoc("forecast6", cmd, o("du_bao_6_phien.json"))
            cmd = [S("kiem_dinh.py"), "du-bao", G, "--lich-su", ls, "--tin-hieu", o("du_bao_6_phien.json"), "--chu"]
            if ma in kb:
                cmd += ["--kich-ban"] + kb[ma].split(":")
            kd = buoc("kiểm định dự báo", cmd, o("kiem_dinh_du_bao.json"), o("kiem_dinh_du_bao.txt"))
            buoc("chart6", [S("chart6.py"), G, "--ma", ma, "--du-bao", o("du_bao_6_phien.json"),
                            "--out", os.path.join(a.out, f"{ma}-6-phien.png")], None, o("bieu_do_6_phien.txt"))

        # ---- tóm tắt và mốc ----
        gia = (ind or {}).get("gia_dong_cua")
        ngay = (ind or {}).get("ngay_cuoi")
        d = [f"## {ma}", f"- Giá đóng cửa {ngay}: {gia}"]
        m = [f"### {ma}", f"- Giá đóng cửa {ngay}: {gia}"]
        if fc and fc.get("du_bao_tung_phien"):
            p = fc["du_bao_tung_phien"]
            v = f"- Vùng 80%: phiên 1 ({p[0]['ngay']}) {p[0]['vung_80'][0]}–{p[0]['vung_80'][1]} → phiên {p[-1]['k']} ({p[-1]['ngay']}) {p[-1]['vung_80'][0]}–{p[-1]['vung_80'][1]}"
            d.append(v)
            m.append(v)
            hs = (fc.get("bien_dong") or {}).get("he_so_gian_vung_theo_phien")
            if hs:
                d.append(f"- Hệ số giãn vùng phiên cuối: {hs[-1]}")
        if cyc:
            vt = cyc.get("vi_tri_hien_tai") or {}
            dp = cyc.get("du_phong") or {}
            tu = vt.get("tu_diem_dao_chieu_gan_nhat") or {}
            v = f"- Chu kỳ: pha {vt.get('pha_hien_tai')}, phiên thứ {vt.get('so_phien_da_qua')} từ {tu.get('loai')} {tu.get('ngay')} ({tu.get('gia')})"
            d.append(v)
            m.append(v)
            d.append(f"- Cửa sổ đảo chiều dự phóng (chỉ dùng khi kiểm định cho phép): {dp.get('cua_so_ngay_uoc_tinh')} · đã quá độ dài điển hình: {dp.get('da_qua_do_dai_dien_hinh')}")
        if kc:
            dd = kc.get("do_deu") or {}
            dpz = kc.get("dong_pha_voi_chi_so") or {}
            v = f"- Kiểm định chu kỳ: {kc.get('muc')} (p = {dd.get('p')}); đồng pha với VN-Index p = {dpz.get('p')}"
            d.append(v)
            m.append(v)
            if kc.get("muc") == "khong_khac_ngau_nhien":
                m.append("- Cửa sổ đảo chiều: không nêu (chu kỳ không khác ngẫu nhiên)")
            else:
                m.append(f"- Cửa sổ đảo chiều dự phóng: {(cyc or {}).get('du_phong', {}).get('cua_so_ngay_uoc_tinh')}")
        if ks is not None:
            d.append(f"- Kiểm định sự kiện: xem kiem_dinh_su_kien.txt ({so_sk} sự kiện, gồm lưu trữ và ngày đáo hạn VN30F sinh theo quy tắc)")
        if ma in a.bieu_do:
            d.append("- Độ chính xác dự báo: xem kiem_dinh_du_bao.txt (chỉ nêu tỷ lệ khi ≥ 10 dự báo độc lập)")
            m.append("- Độ chính xác dự báo: (điền từ kiem_dinh_du_bao.txt: số dự báo độc lập; chưa đủ 10 thì ghi 'chưa đủ để đánh giá')")
        m.append("- Mức giá đóng cửa làm kịch bản chính không còn đúng: (điền từ mục 8 của báo cáo)")
        for e in loi:
            d.append(f"- LỖI {e}")
        L.append("\n".join(d))
        moc.append("\n".join(m))

    vn = os.path.join(a.du_an, "data", "von-ngoai.csv")
    if os.path.isfile(vn):
        d1, e1 = chay([S("ap_luc_von_ngoai.py"), vn], os.path.join(a.out, "ap_luc_von_ngoai.json"))
        _, e2 = chay([S("ap_luc_von_ngoai.py"), vn, "--chu"], None, os.path.join(a.out, "ap_luc.txt"))
        L.append("## Dòng vốn ngoại\n- " + (f"LỖI {e1 or e2}" if (e1 or e2) else "xem ap_luc.txt và ap_luc_von_ngoai.json"))

    tt = "# Tóm tắt kết quả script\n\n" + "\n\n".join(L) + "\n"
    with open(os.path.join(a.out, "tom_tat_script.md"), "w", encoding="utf-8") as f:
        f.write(tt)
    with open(os.path.join(a.out, "moc_nhap.md"), "w", encoding="utf-8") as f:
        f.write("# Mốc theo dõi – trạng thái từ phân tích sâu gần nhất\n\nNgày phân tích: (điền) · dữ liệu đến phiên: (điền)\n\n"
                + "\n\n".join(moc)
                + "\n\n### Toàn thị trường\n- Điểm áp lực khối ngoại: (điền từ ap_luc.txt)\n- Lịch sự kiện 10 ngày tới: (điền từ báo cáo)\n")
    print(tt)


if __name__ == "__main__":
    main()
