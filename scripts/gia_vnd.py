#!/usr/bin/env python3
"""Giá cổ phiếu và chỉ số chỉ từ VND MCP (thay lay_gia_cty_ck.py, bỏ KBS và Vietcap từ 22/11/2026).

VND MCP không có lệnh lấy lịch sử dài, nên lịch sử 6 năm lấy từ bản lưu trong dự án
(data/<MÃ>.csv, data/VNINDEX.csv, data/VN30.csv – agent T tải về), rồi nối các phiên mới
mà phiên chính đã gọi từ VND và ghi vào một file JSON gọn (xem --vnd).

Cách dùng:
    python gia_vnd.py MBB TCB CTG HPG --phien 2026-11-20 --lich-su-dir <W>/du-an/data \
        --vnd <W>/gia/vnd.json --out-dir <W>/gia \
        [--cong-cu "<tên công cụ VND, cách nhau dấu phẩy>" --cong-cu-cu <W>/du-an/data/vnd-cong-cu.txt] \
        > <W>/gia/ket-qua.json

File --vnd (phiên chính ghi, chỉ chép các trường dưới đây từ kết quả VND, không thêm gì):
{
  "health": "ok",
  "co_phieu": {"2026-11-20": [{"code": "MBB", "adOpen": 18.5, "adHigh": 18.55, "adLow": 18.25,
                               "adClose": 18.25, "nmVolume": 13428478, "basicPrice": 18.7,
                               "ceilingPrice": 20, "floorPrice": 17.4}, ...]},
  "chi_so": {"VNINDEX": {"2026-11-20": {"open": 1671.25, "high": 1689.18, "low": 1666.41,
                         "close": 1688.79, "change": -0.83, "pctChange": -0.049,
                         "accumulatedVol": 736616872, "accumulatedVal": 15932987132530}},
             "VN30": {...}},
  "thong_bao": ["mọi câu thông báo/cảnh báo/cập nhật hệ thống VND trả về, nguyên văn"]
}
get_stock_price_by_date: nhiều mã một lần, đọc theo trường code. get_vnmarket_prices: MỖI chỉ số
một lần gọi (kết quả không có trường mã).

Kết quả: gia_<MÃ>_ctck.csv, gia_VNINDEX_ctck.csv, gia_VN30_ctck.csv trong --out-dir (giữ tên cũ để
các script khác không phải đổi; cột date,open,high,low,close,volume, nghìn đồng, đã điều chỉnh)
và JSON ra stdout (cấu trúc như lay_gia_cty_ck.py: tom_tat, ma, chi_so, thêm dieu_chinh, vnd).

Nhãn: VND là dữ liệu sàn qua công ty chứng khoán. Theo quyết định của người dùng (22/11/2026),
số giá/chỉ số VND qua được kiểm tra nội tại là ✔ (một nguồn cấp cao). Không qua thì ✖ và ghi lý do.
Điều chỉnh giá: nếu giá tham chiếu (basicPrice) của phiên mới khác giá đóng cửa phiên trước trong
lịch sử, coi là có sự kiện quyền (chia cổ tức, phát hành) và nhân toàn bộ lịch sử trước đó theo tỷ lệ
basicPrice / đóng cửa trước, khối lượng chia theo tỷ lệ đó. Ghi rõ vào dieu_chinh.
"""
import argparse
import csv
import json
import os
import sys

COT = ["date", "open", "high", "low", "close", "volume"]
TU_THONG_BAO = ("message", "notice", "warning", "deprecat", "update", "maintenance", "thong_bao")


def doc(p):
    if not os.path.exists(p):
        return []
    with open(p, newline="", encoding="utf-8") as f:
        rows = []
        for r in csv.DictReader(f):
            try:
                rows.append({"date": r["date"][:10], "open": float(r["open"]), "high": float(r["high"]),
                             "low": float(r["low"]), "close": float(r["close"]), "volume": float(r["volume"] or 0)})
            except (KeyError, ValueError):
                continue
    rows.sort(key=lambda r: r["date"])
    return rows


def ghi(p, rows):
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COT)
        for r in rows:
            w.writerow([r["date"]] + [round(r[k], 4) for k in COT[1:5]] + [int(round(r["volume"]))])


def kiem_noi_tai(o, h, l, c, tran=None, san=None):
    loi = []
    if not (l <= min(o, c) + 1e-9 and h >= max(o, c) - 1e-9):
        loi.append("thấp/cao không bao mở/đóng")
    if tran is not None and san is not None and not (san - 1e-9 <= c <= tran + 1e-9):
        loi.append(f"đóng cửa {c} ngoài biên độ sàn {san}–trần {tran}")
    return loi


def tim_thong_bao(obj, out, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if any(t in k.lower() for t in TU_THONG_BAO) and isinstance(v, (str, list)) and v:
                out.append(f"{path}{k}: {v}")
            tim_thong_bao(v, out, f"{path}{k}.")
    elif isinstance(obj, list):
        for x in obj:
            tim_thong_bao(x, out, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ma", nargs="+")
    ap.add_argument("--phien", required=True, help="phiên gần nhất đã đóng cửa (yyyy-mm-dd)")
    ap.add_argument("--lich-su-dir", required=True)
    ap.add_argument("--vnd", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--cong-cu", default=None)
    ap.add_argument("--cong-cu-cu", default=None)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    vnd = json.load(open(a.vnd, encoding="utf-8"))
    kq = {"phien": a.phien, "nguon": "VND MCP (một nguồn cấp cao; KBS và Vietcap đã bỏ từ 22/11/2026)",
          "ma": {}, "chi_so": {}, "vnd": {"health": vnd.get("health"), "thong_bao": list(vnd.get("thong_bao", []))}}
    tim_thong_bao({k: v for k, v in vnd.items() if k != "thong_bao"}, kq["vnd"]["thong_bao"])

    # Danh sách công cụ VND: so với lần trước để phát hiện cập nhật hệ thống
    if a.cong_cu is not None:
        moi = sorted({x.strip() for x in a.cong_cu.split(",") if x.strip()})
        cu = []
        if a.cong_cu_cu and os.path.exists(a.cong_cu_cu):
            cu = sorted({x.strip() for x in open(a.cong_cu_cu, encoding="utf-8") if x.strip()})
        kq["vnd"]["cong_cu"] = {"so_luong": len(moi), "them": sorted(set(moi) - set(cu)) if cu else [],
                                "bo": sorted(set(cu) - set(moi)) if cu else [],
                                "ghi_chu": "lần đầu ghi danh sách" if not cu else ""}
        if a.cong_cu_cu:
            with open(a.cong_cu_cu, "w", encoding="utf-8") as f:
                f.write("\n".join(moi) + "\n")

    ngay_cp = sorted(vnd.get("co_phieu", {}))
    tom = []
    for ma in a.ma:
        lich = doc(os.path.join(a.lich_su_dir, f"{ma}.csv"))
        muc = {"nhan": "✔", "nguon": "VND MCP", "canh_bao": [], "dieu_chinh": [], "phien_them": []}
        if not lich:
            muc["canh_bao"].append(f"không có lịch sử data/{ma}.csv")
        for d in ngay_cp:
            dong = next((x for x in vnd["co_phieu"][d] if x.get("code", "").upper() == ma), None)
            if dong is None:
                muc["canh_bao"].append(f"{d}: VND không trả dòng của {ma}")
                continue
            o, h, l, c = (float(dong[k]) for k in ("adOpen", "adHigh", "adLow", "adClose"))
            v = float(dong.get("nmVolume") or 0)
            loi = kiem_noi_tai(o, h, l, c, dong.get("ceilingPrice"), dong.get("floorPrice"))
            truoc = [r for r in lich if r["date"] < d]
            cung = [r for r in lich if r["date"] == d]
            if cung:
                r0 = cung[0]
                if abs(r0["close"] - c) > 1e-6:
                    muc["canh_bao"].append(f"{d}: lịch sử ghi {r0['close']} khác VND {c} – thay bằng VND")
                lich = [r for r in lich if r["date"] != d]
            if truoc and dong.get("basicPrice") is not None:
                tc, dc = float(dong["basicPrice"]), truoc[-1]["close"]
                if abs(tc - dc) > 0.0051:
                    ty = tc / dc
                    for r in lich:
                        if r["date"] < d:
                            for k in ("open", "high", "low", "close"):
                                r[k] *= ty
                            r["volume"] /= ty
                    muc["dieu_chinh"].append({"ngay": d, "tham_chieu": tc, "dong_cua_truoc": dc, "ty_le": round(ty, 6),
                                              "ghi_chu": "giá tham chiếu khác đóng cửa phiên trước: đã điều chỉnh toàn bộ lịch sử trước ngày này (kiểm sự kiện quyền bằng get_company_events)"})
            lich.append({"date": d, "open": o, "high": h, "low": l, "close": c, "volume": v})
            lich.sort(key=lambda r: r["date"])
            muc["phien_them"].append(d)
            if loi:
                muc["nhan"] = "✖"
                muc["canh_bao"].append(f"{d}: " + "; ".join(loi))
        # liên tục: phiên đầu tiên mới phải ngay sau phiên cuối lịch sử (phiên chính tự kiểm bằng lịch VND)
        cuoi = lich[-1] if lich else None
        if not cuoi or cuoi["date"] != a.phien:
            muc["nhan"] = "⊘"
            muc["canh_bao"].append(f"chưa có phiên {a.phien}")
        else:
            muc["phien_can_lay"] = {k: cuoi[k] for k in COT[1:]}
        p = os.path.join(a.out_dir, f"gia_{ma}_ctck.csv")
        ghi(p, lich)
        muc["file"] = p
        muc["so_phien"] = len(lich)
        kq["ma"][ma] = muc
        tom.append(f"{ma} {muc['nhan']}")
    kq["tom_tat"] = " · ".join(tom)

    for cs, theo_ngay in vnd.get("chi_so", {}).items():
        lich = doc(os.path.join(a.lich_su_dir, f"{cs}.csv"))
        canh = []
        for d in sorted(theo_ngay):
            x = theo_ngay[d]
            lich = [r for r in lich if r["date"] != d]
            lich.append({"date": d, "open": float(x["open"]), "high": float(x["high"]), "low": float(x["low"]),
                         "close": float(x["close"]), "volume": float(x.get("accumulatedVol") or 0)})
            lich.sort(key=lambda r: r["date"])
        cuoi = lich[-1] if lich else None
        if not cuoi or cuoi["date"] != a.phien:
            kq["chi_so"][cs] = {"nhan": "⊘", "ghi_chu": f"chưa có phiên {a.phien}"}
            continue
        x = theo_ngay.get(a.phien, {})
        truoc = lich[-2] if len(lich) > 1 else None
        nhan = "✔"
        if truoc and x.get("change") is not None and abs((cuoi["close"] - truoc["close"]) - float(x["change"])) > 0.011:
            nhan = "✖"
            canh.append(f"thay đổi VND {x['change']} khác đóng cửa trừ phiên trước {round(cuoi['close'] - truoc['close'], 2)} (lịch sử có thể thiếu phiên)")
        canh += kiem_noi_tai(cuoi["open"], cuoi["high"], cuoi["low"], cuoi["close"])
        if canh and nhan == "✔":
            nhan = "✖"
        p = os.path.join(a.out_dir, f"gia_{cs}_ctck.csv")
        ghi(p, lich)
        kq["chi_so"][cs] = {"nhan": nhan, "nguon": "VND MCP", "dong_cua": cuoi["close"],
                            "phien_truoc": {"ngay": truoc["date"], "dong_cua": truoc["close"]} if truoc else None,
                            "thay_doi_diem": x.get("change"), "thay_doi_pct": x.get("pctChange"),
                            "cao": cuoi["high"], "thap": cuoi["low"], "khoi_luong_cp": int(cuoi["volume"]),
                            "gia_tri_ty_dong_gom_thoa_thuan": round(float(x["accumulatedVal"]) / 1e9, 1) if x.get("accumulatedVal") else None,
                            "canh_bao": canh, "file": p}
    json.dump(kq, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
