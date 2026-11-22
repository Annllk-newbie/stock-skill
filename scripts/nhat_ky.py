#!/usr/bin/env python3
"""Nhật ký chạy: mỗi bước của một lần chạy ghi MỘT dòng, để khi lỗi biết ngay lỗi ở đâu và sửa thế nào.

Dòng nhật ký:  HH:MM | TRẠNG THÁI | <bước> | <chi tiết> | Gợi ý: <cách sửa>
Trạng thái: OK · CẢNH BÁO (chạy được nhưng thiếu/◐) · LỖI (bước hỏng, lần chạy vẫn tiếp) · BỎ QUA (cố ý không làm, kèm lý do) · DỪNG (cả lần chạy dừng)

Cách dùng (mặc định file research/nhat-ky-chay.txt, đổi bằng --file):
    python nhat_ky.py bat-dau --tieu-de "Bản tin sáng 2026-11-24" --phien-ban "dc9be80 2026-11-22"
    python nhat_ky.py ghi --buoc "02 VND health" --trang-thai ok --chi-tiet "16 công cụ"
    python nhat_ky.py ghi --buoc "09 Agent B2" --trang-thai loi --chi-tiet "<nguyên văn lỗi>"
    python nhat_ky.py chay --buoc "04 gia_vnd.py" --dung-khi-ma 2 -- python scripts/gia_vnd.py ... > ket-qua.json
    python nhat_ky.py tom-tat            # in tóm tắt: số bước theo trạng thái + mọi dòng không OK

`chay` chạy lệnh sau `--`, chuyển nguyên stdout/stderr của lệnh ra ngoài (nên `> file` vẫn dùng được),
trả về đúng mã thoát của lệnh, và ghi dòng OK hoặc LỖI/DỪNG kèm dòng lỗi cuối và gợi ý sửa.
Không có --chi-tiet/--goi-y khi trạng thái không OK thì gợi ý được tự tra từ bảng lỗi đã biết.
"""
import argparse
import datetime as dt
import os
import re
import subprocess
import sys

MAC_DINH = os.path.join("research", "nhat-ky-chay.txt")
TRANG_THAI = {"ok": "OK", "canh-bao": "CẢNH BÁO", "loi": "LỖI", "bo-qua": "BỎ QUA", "dung": "DỪNG"}

# (mẫu lỗi, gợi ý) – dòng đầu tiên khớp được dùng. Thêm mẫu mới khi gặp lỗi mới.
LOI_CODE = ("LỖI CODE của skill (không phải lỗi dữ liệu): không tự sửa code trong lần chạy; chuyển sang bản ổn định theo "
            "mục 'Khi code mới lỗi' của SKILL.md, rồi gửi dòng này cho Claude để sửa trên GitHub.")

GOI_Y = [
    (r"SyntaxError|IndentationError|NameError|AttributeError|ImportError: cannot import|"
     r"No module named '(?:nhat_ky|common|indicators|cycles|chay|gia_vnd|forecast6|chart6|kiem_dinh)'|"
     r"unrecognized arguments|the following arguments are required|invalid choice|"
     r"can't open file '[^']*research/skill", LOI_CODE),
    (r"ModuleNotFoundError: No module named '([\w.]+)'",
     "Thiếu thư viện {0}: chạy `pip install {0} --break-system-packages` rồi chạy lại bước này."),
    (r"URL_NOT_ON_ALLOWLIST",
     "WebFetch chặn URL gõ tay: WebSearch trước rồi fetch đúng link trả về (trang-web.md)."),
    (r"throttl|429|rate limit|too many requests",
     "Bị giới hạn tần suất: chờ 20 giây rồi gọi lại MỘT lần."),
    (r"timed? ?out|timeout|hết thời gian",
     "Quá thời gian: gọi lại MỘT lần; vẫn lỗi thì ghi LỖI và đi tiếp (giá thì DỪNG)."),
    (r"\"dung\": ?true|chưa có phiên|⊘",
     "Giá có mã ✖/⊘: bù phiên thiếu theo mục 'Giá' của phien-chinh.md rồi chạy lại; vẫn lỗi thì DỪNG."),
    (r"JSONDecodeError|Expecting value|Extra data|Unterminated string",
     "File JSON hỏng hoặc rỗng: mở file đầu vào của bước này (thường là file chép từ kết quả MCP) xem có bị cắt không."),
    (r"Thiếu cột|KeyError",
     "CSV thiếu hoặc sai tên cột: so dòng tiêu đề của file với cột script cần (chạy script với --help)."),
    (r"Không đọc được ngày|does not match format|ValueError: time data",
     "Ngày sai định dạng trong CSV: xem giá trị nêu trong lỗi, sửa về yyyy-mm-dd."),
    (r"CSV rỗng|empty|rỗng",
     "File đầu vào rỗng: kiểm agent T đã tải đủ chưa (dòng JSON `da_luu`) hoặc bước trước có ghi ra file không."),
    (r"No such file|FileNotFoundError|không có file|không tìm thấy|not found",
     "Thiếu file: kiểm đường dẫn trong lệnh và agent T đã tải file đó chưa (dòng JSON `da_luu`)."),
    (r"Permission denied|403|Forbidden",
     "Bị chặn quyền truy cập: trang/thư mục không cho đọc – đổi nguồn (trang-web.md) hoặc kiểm quyền thư mục."),
    (r"Traceback|Error",
     "Lỗi trong script: chạy riêng lệnh này để xem lỗi đầy đủ, rồi gửi dòng nhật ký này cho Claude để sửa trên GitHub."),
]
MAC_DINH_GOI_Y = "Chưa có trong bảng lỗi đã biết: gửi nguyên dòng này cho Claude để tìm nguyên nhân."


def goi_y(van_ban):
    for mau, g in GOI_Y:
        m = re.search(mau, van_ban or "", re.I)
        if m:
            return g.format(*m.groups())
    return MAC_DINH_GOI_Y


def gon(s, n=300):
    s = " ".join((s or "").replace("|", "/").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def ghi_dong(file, buoc, trang_thai, chi_tiet="", goi_y_sua=""):
    """Ghi một dòng. Dùng được từ script khác: from nhat_ky import ghi_dong."""
    tt = TRANG_THAI.get(trang_thai, trang_thai)
    if tt not in TRANG_THAI.values():
        raise ValueError(f"trạng thái không hợp lệ: {trang_thai}")
    if tt not in ("OK", "BỎ QUA") and not goi_y_sua:
        goi_y_sua = goi_y(chi_tiet)
    cot = [dt.datetime.now().strftime("%H:%M"), tt, gon(buoc, 80), gon(chi_tiet)]
    if goi_y_sua:
        cot.append("Gợi ý: " + gon(goi_y_sua, 250))
    d = os.path.dirname(file)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(file, "a", encoding="utf-8") as f:
        f.write(" | ".join(cot).rstrip(" |") + "\n")


def doc_dong(file):
    try:
        with open(file, encoding="utf-8") as f:
            return [l.rstrip("\n") for l in f if re.match(r"^\d\d:\d\d \| ", l)]
    except OSError:
        return []


def tom_tat(file):
    dong = doc_dong(file)
    if not dong:
        return f"Nhật ký chạy: chưa có dòng nào ({file})."
    dem = {}
    for l in dong:
        tt = l.split(" | ")[1]
        dem[tt] = dem.get(tt, 0) + 1
    thu_tu = ["OK", "CẢNH BÁO", "LỖI", "BỎ QUA", "DỪNG"]
    dau = f"Nhật ký chạy: {len(dong)} bước · " + " · ".join(f"{dem[t]} {t}" for t in thu_tu if t in dem)
    xau = [l for l in dong if l.split(" | ")[1] != "OK"]
    return dau + ("\n" + "\n".join("- " + l for l in xau) if xau else "\nMọi bước OK.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", default=MAC_DINH)
    sp = ap.add_subparsers(dest="lenh", required=True)

    b = sp.add_parser("bat-dau", help="tạo nhật ký mới cho một lần chạy (ghi đè file cũ)")
    b.add_argument("--tieu-de", required=True)
    b.add_argument("--phien-ban", default="")

    g = sp.add_parser("ghi", help="ghi một dòng")
    g.add_argument("--buoc", required=True)
    g.add_argument("--trang-thai", required=True, choices=list(TRANG_THAI))
    g.add_argument("--chi-tiet", default="")
    g.add_argument("--goi-y", default="")

    c = sp.add_parser("chay", help="chạy một lệnh và tự ghi kết quả")
    c.add_argument("--buoc", required=True)
    c.add_argument("--dung-khi-ma", type=int, nargs="*", default=[],
                   help="mã thoát nghĩa là DỪNG cả lần chạy (vd gia_vnd.py: 2)")
    c.add_argument("--canh-bao-khi-ma", type=int, nargs="*", default=[])
    c.add_argument("lenh_con", nargs=argparse.REMAINDER)

    sp.add_parser("tom-tat", help="in tóm tắt và các dòng không OK")
    for p in (b, g, c, sp.choices["tom-tat"]):
        p.add_argument("--file", default=argparse.SUPPRESS)
    a = ap.parse_args()

    if a.lenh == "bat-dau":
        d = os.path.dirname(a.file)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(a.file, "w", encoding="utf-8") as f:
            f.write(f"# Nhật ký chạy – {a.tieu_de}" + (f" · code {a.phien_ban}" if a.phien_ban else "")
                    + f" · bắt đầu {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        return 0
    if a.lenh == "ghi":
        ghi_dong(a.file, a.buoc, a.trang_thai, a.chi_tiet, a.goi_y)
        return 0
    if a.lenh == "tom-tat":
        print(tom_tat(a.file))
        return 0

    lenh = a.lenh_con[1:] if a.lenh_con[:1] == ["--"] else a.lenh_con
    if not lenh:
        ap.error("chay: thiếu lệnh sau --")
    try:
        p = subprocess.run(lenh, capture_output=True, text=True)
    except OSError as e:
        ghi_dong(a.file, a.buoc, "loi", f"không chạy được lệnh: {e}")
        print(e, file=sys.stderr)
        return 127
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    if p.returncode == 0:
        ghi_dong(a.file, a.buoc, "ok")
    else:
        cuoi = (p.stderr.strip().splitlines() or p.stdout.strip().splitlines() or ["lỗi không rõ"])[-1]
        # gia_vnd.py báo dừng trên stdout (JSON) – đưa cả stdout vào để tra gợi ý
        tra = p.stderr + "\n" + p.stdout[-2000:]
        tt = "dung" if p.returncode in a.dung_khi_ma else "canh-bao" if p.returncode in a.canh_bao_khi_ma else "loi"
        ghi_dong(a.file, a.buoc, tt, f"mã thoát {p.returncode}: {cuoi}", goi_y(tra))
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
