#!/usr/bin/env python3
"""MỘT LỆNH ĐIỀU PHỐI cho mỗi chặng của một lần chạy: thứ tự bước, tham số, file vào/ra và nhật ký đều cố định ở đây.

Phiên chính chỉ còn tự làm các việc không phải script (gọi VND MCP, gọi agent, viết lời văn, project_write, gửi);
mọi việc script nằm trong 5 lệnh dưới đây, chạy đúng thứ tự. Mỗi lệnh tự ghi nhật ký chạy (nhat_ky.py) và in
kết quả NGẮN; chỉ đọc phần in ra, không mở file kết quả trừ khi cần.

Chế độ: ban-tin (bản tin sáng) · sau (phân tích sâu bản đầy đủ) · sau-nhe (phân tích sâu bản cập nhật giữa tuần)

    python research/skill/scripts/chay.py <chế độ> bat-dau --ma MBB TCB CTG HPG [--bieu-do MBB TCB] [--ngay yyyy-mm-dd]
        → tạo nhật ký, ghi bước 01, in kế hoạch các bước của chế độ (ke-hoach)
    python research/skill/scripts/chay.py <chế độ> gia --phien yyyy-mm-dd --cong-cu "<tên công cụ mcp__VND__, cách nhau dấu phẩy>"
        → (sau khi agent T đã tải dự án và <W>/gia/vnd.json đã ghi) bước 04 gia_vnd.py, 05 kiem_tra_du_lieu.py.
          Mã thoát 2 = DỪNG cả lần chạy (mục "Khi DỪNG" của phien-chinh.md).
    python research/skill/scripts/chay.py <chế độ> tinh [--nghi yyyy-mm-dd …] [--kich-ban MBB=3:2 …]
        → (sau khi gắn nhãn và ghi nhật ký CSV) ban-tin: bước 20–23 (+ TB20 các mã không có biểu đồ);
          sau/sau-nhe: ghép sự kiện mới (ma/su_kien_<MÃ>.csv, su_kien_A2.csv, su_kien_A3.csv) vào
          du-an/<MÃ>/su-kien.csv rồi bước 24 chay_sau.py.
    python research/skill/scripts/chay.py <chế độ> ghep
        → ban-tin: ghép <W>/phu_luc.md theo đúng mẫu phụ lục rồi ghép ghi chú Obsidian bản tin (cần <W>/ghi_chu_dau.md,
          <W>/ban_tin.md; phiên chính viết các mục tự viết vào <W>/phu_luc_tu_viet.md dưới đúng tiêu đề mẫu).
          sau/sau-nhe: thêm mục "Nhật ký chạy" vào cuối <W>/bao_cao.md (sau kiểm tra chéo, trước agent O).
    python research/skill/scripts/chay.py <chế độ> luu
        → bước 29: chép giá về <W>/du-an/data, nen_du_lieu.py; sau: nối báo cáo vào ghi chú báo cáo sâu;
          thêm ghi chú mới/đã sửa vào NHAC-DONG-BO.md; in DANH SÁCH file cần project_write (local_path → đường dẫn dự án),
          tính bằng so nội dung với lúc agent T vừa tải xong – chỉ file mới hoặc đã đổi.
    python research/skill/scripts/chay.py <chế độ> ke-hoach   → in lại danh sách bước

<W> = research/ (đổi bằng --w). Trạng thái giữa các lệnh: <W>/chay-trang-thai.json.
"""
import argparse
import csv
import datetime as dt
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from nhat_ky import ghi_dong, goi_y, tom_tat  # noqa: E402

DU_AN_GOC = "claude/chung-khoan"
VN = dt.timezone(dt.timedelta(hours=7))
LICH_SU_DU_BAO = ("du-bao-6-phien-dieu-chinh.json", "du-bao-6-phien.json")

# Kế hoạch: (số bước, chế độ áp dụng, ai làm). "chay.py X" = lệnh của file này; còn lại phiên chính tự làm và tự ghi nhật ký.
KE_HOACH = [
    ("01 Tải code GitHub", "BA", "git clone (mục 0 SKILL.md) rồi `chay.py <chế độ> bat-dau`"),
    ("02 VND health và công cụ", "BA", "phiên chính: ToolSearch `mcp__VND__`, `mcp__VND__health`; ghi nhật ký"),
    ("06 Agent T", "BA", "agent Haiku: nguyen-tac.md + thu-thap.md (Thẻ T), song song với 02–03; ghi nhật ký"),
    ("03 VND lịch, giá, chỉ số, khối ngoại sàn", "BA", "phiên chính: gọi VND theo mục 'VND MCP' của phien-chinh.md, ghi <W>/gia/vnd.json; ghi nhật ký"),
    ("04–05 Giá", "BA", "`chay.py <chế độ> gia --phien … --cong-cu …` (mã thoát 2 → DỪNG)"),
    ("07 Đồng bộ và liệt kê vault", "A", "skill dong-bo-obsidian; ghi nhật ký"),
    ("08 Chấm dự báo kỳ trước", "A", "script chấm ở bước 25a; phiên chính chỉ chấm nốt dòng kịch bản cũ trong nhat-ky-du-bao.md; ghi nhật ký"),
    ("09 Agent B", "B", "MỘT agent Haiku: nguyen-tac.md + thu-thap.md (Thẻ B2 rồi Agent theo mã cho mọi mã); ghi nhật ký"),
    ("11 Agent A-chung", "A", "agent Haiku: nguyen-tac.md + thu-thap.md (Thẻ A2, A3, A4 – A4 chỉ bản đầy đủ); song song với 14"),
    ("14 Agent A-ma", "A", "MỘT agent Haiku: nguyen-tac.md + thu-thap.md (Agent theo mã, chế độ A, cho mọi mã); ghi nhật ký"),
    ("18 Agent A5", "BA", "phiên chính gắn nhãn, gom số chưa ✔ vào can_kiem_chung.md; agent Haiku: nguyen-tac.md + thu-thap.md (Thẻ A5). A: luôn; B: chỉ khi còn số chưa ✔ (không thì BỎ QUA)"),
    ("19 Gắn nhãn và ghi nhật ký CSV", "BA", "phiên chính, Python (phien-chinh.md, mục bước 18–19); ghi nhật ký"),
    ("20–25a Tính toán", "BA", "`chay.py <chế độ> tinh` (kể cả du_bao_xs.py; --nghi nếu có)"),
    ("25 Agent tổng hợp", "A", "agent Sonnet: nguyen-tac.md + tong-hop.md → <W>/bao_cao.md"),
    ("26 Kiểm tra chéo Opus", "A", "agent Opus: tong-hop.md (mục Kiểm tra chéo cuối cùng)"),
    ("28 Ghép", "BA", "B: viết <W>/ghi_chu_dau.md, <W>/ban_tin.md, <W>/phu_luc_tu_viet.md rồi `chay.py ban-tin ghep`; A: `chay.py sau ghep`"),
    ("27 Agent O", "A", "agent Sonnet: tong-hop.md (Thẻ O), sau khi ghép nhật ký vào báo cáo"),
    ("29 Nén và chuẩn bị lưu", "BA", "`chay.py <chế độ> luu` (A: sau agent O; viết MOC-THEO-DOI.md trước lệnh này)"),
    ("30 Lưu vào dự án", "BA", "phiên chính: project_write từng dòng `luu` in ra; ghi nhật ký (file lỗi ghi đường dẫn)"),
    ("31 Gửi người dùng", "BA", "PushNotification / câu trả lời cuối + SendUserFile ảnh; ghi nhật ký"),
]

MAU_PHU_LUC = [
    "Từng mã – đầy đủ",
    "Kỹ thuật MBB, TCB (bản chữ chart6.py) và giá so với TB20 của các mã khác",
    "Dự báo xác suất (du_bao_xs.py)",
    "Thế giới đêm qua – đầy đủ",
    "Dòng vốn ngoại – bản chữ ap_luc_von_ngoai.py",
    "Chuỗi truyền dẫn – bản chữ chuoi_truyen_dan.py",
    "Tin nền tảng mới (mỗi tin một dòng kèm chuỗi tác động)",
    "Tin doanh nghiệp không đưa lên thân bản tin",
    "Doanh nghiệp và ngành tham chiếu – đầy đủ (B2, mục 4)",
    "Độ chính xác dự báo",
    "Lịch sự kiện 10 ngày tới",
    "Chưa kiểm chứng (mục · số · nguồn · vì sao)",
    "Đã thu thập nhưng không dùng (kèm lý do)",
    "Độ đầy đủ dữ liệu",
    "Nguồn (kèm cấp 1/2/3)",
    "Nhật ký chạy (nguyên văn research/nhat-ky-chay.txt)",
]
LICH_SU_XS = "du-bao-xs.json"
KY_HAN_XS = ["5", "20"]


# ---------- tiện ích ----------
class Ctx:
    def __init__(self, a):
        self.a = a
        self.W = a.w
        self.NK = os.path.join(self.W, "nhat-ky-chay.txt")
        self.TT = os.path.join(self.W, "chay-trang-thai.json")
        self.DA = os.path.join(self.W, "du-an")
        self.GIA = os.path.join(self.W, "gia")

    def p(self, *x):
        return os.path.join(self.W, *x)

    def tt(self):
        try:
            with open(self.TT, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            sys.exit(f"Chưa có {self.TT}: chạy `chay.py {self.a.che_do} bat-dau --ma …` trước.")

    def luu_tt(self, d):
        os.makedirs(self.W, exist_ok=True)
        with open(self.TT, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)

    def ghi(self, buoc, trang_thai, chi_tiet="", goi_y_sua=""):
        ghi_dong(self.NK, buoc, trang_thai, chi_tiet, goi_y_sua)


def chay_lenh(cx, buoc, args, out=None, dung_khi_ma=(), canh_bao_khi_ma=(), ghi_ok=True):
    """Chạy một script con, ghi nhật ký. Trả về (mã thoát, stdout)."""
    p = subprocess.run([sys.executable] + args, capture_output=True, text=True)
    if out:
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(p.stdout)
    if p.returncode == 0:
        if ghi_ok:
            cx.ghi(buoc, "ok")
    else:
        cuoi = (p.stderr.strip().splitlines() or p.stdout.strip().splitlines() or ["lỗi không rõ"])[-1]
        tt = "dung" if p.returncode in dung_khi_ma else "canh-bao" if p.returncode in canh_bao_khi_ma else "loi"
        cx.ghi(buoc, tt, f"mã thoát {p.returncode}: {cuoi}", goi_y(p.stderr + "\n" + p.stdout[-2000:]))
    return p.returncode, p.stdout


def doc_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def doc_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def bam(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for k in iter(lambda: f.read(1 << 16), b""):
            h.update(k)
    return h.hexdigest()


def anh_chup(goc):
    out = {}
    for d, _, fs in os.walk(goc):
        for n in fs:
            fp = os.path.join(d, n)
            out[os.path.relpath(fp, goc).replace(os.sep, "/")] = bam(fp)
    return out


def file_lich_su(cx, ma):
    return next((p for p in (os.path.join(cx.DA, ma, n) for n in LICH_SU_DU_BAO) if os.path.isfile(p)), None)


# ---------- lệnh ----------
def cmd_ke_hoach(cx, che_do=None):
    che_do = che_do or cx.a.che_do
    k = "B" if che_do == "ban-tin" else "A"
    print(f"Kế hoạch {che_do} (đúng thứ tự; tên bước trong nhật ký theo mục \"Nhật ký chạy\" của phien-chinh.md):")
    for ten, ap, ai in KE_HOACH:
        if k in ap:
            print(f"- {ten}: {ai}")
    return 0


def cmd_bat_dau(cx):
    a = cx.a
    ngay = a.ngay or dt.datetime.now(VN).date().isoformat()
    try:
        pb = subprocess.run(["git", "-C", SKILL, "log", "-1", "--format=%h %cs"], capture_output=True, text=True).stdout.strip()
    except OSError:
        pb = ""
    tieu_de = {"ban-tin": "Bản tin sáng", "sau": "Phân tích sâu đầy đủ", "sau-nhe": "Phân tích sâu cập nhật"}[a.che_do]
    os.makedirs(cx.W, exist_ok=True)
    with open(cx.NK, "w", encoding="utf-8") as f:
        f.write(f"# Nhật ký chạy – {tieu_de} {ngay}" + (f" · code {pb}" if pb else "")
                + f" · bắt đầu {dt.datetime.now(VN).strftime('%Y-%m-%d %H:%M')}\n")
    cx.ghi("01 Tải code GitHub", "ok", pb)
    cx.luu_tt({"che_do": a.che_do, "ngay": ngay, "ma": a.ma, "bieu_do": a.bieu_do, "phien_ban": pb})
    return cmd_ke_hoach(cx)


def cmd_gia(cx):
    a, t = cx.a, cx.tt()
    thieu = [f for f in [os.path.join(cx.DA, "data", f"{m}.csv") for m in t["ma"] + ["VNINDEX", "VN30"]]
             + [os.path.join(cx.GIA, "vnd.json")] if not os.path.isfile(f)]
    if thieu:
        cx.ghi("04 gia_vnd.py", "dung", "thiếu file đầu vào: " + ", ".join(thieu),
               "Lịch sử giá do agent T tải (bước 06), vnd.json do phiên chính ghi (bước 03): làm xong hai bước đó rồi chạy lại lệnh gia.")
        print(json.dumps({"dung": True, "ly_do_dung": ["thiếu file đầu vào"], "thieu": thieu}, ensure_ascii=False))
        return 2
    t["anh_chup_du_an"] = anh_chup(cx.DA)  # trạng thái ngay sau agent T, để lệnh luu biết file nào đã đổi
    cx.luu_tt(t)
    args = [os.path.join(HERE, "gia_vnd.py")] + t["ma"] + ["--phien", a.phien, "--lich-su-dir", os.path.join(cx.DA, "data"),
                                                         "--vnd", os.path.join(cx.GIA, "vnd.json"), "--out-dir", cx.GIA]
    if a.cong_cu is not None:
        args += ["--cong-cu", a.cong_cu, "--cong-cu-cu", os.path.join(cx.DA, "data", "vnd-cong-cu.txt")]
    ma_thoat, _ = chay_lenh(cx, "04 gia_vnd.py", args, out=os.path.join(cx.GIA, "ket-qua.json"), dung_khi_ma=(2,))
    kq = doc_json(os.path.join(cx.GIA, "ket-qua.json")) or {}
    cs = {c: (f"{v.get('nhan')} {v.get('dong_cua')} ({v.get('thay_doi_pct')}%), GTGD {v.get('gia_tri_ty_dong_gom_thoa_thuan')} tỷ"
              + (f" – {'; '.join(v['canh_bao'])}" if v.get("canh_bao") else "") if v.get("nhan") == "✔" else v)
          for c, v in (kq.get("chi_so") or {}).items()}
    gon = {"dung": ma_thoat != 0, "tom_tat": kq.get("tom_tat"), "chi_so": cs, "vnd": kq.get("vnd"),
           "ma_can_xem": {m: v for m, v in (kq.get("ma") or {}).items() if v.get("nhan") != "✔" or v.get("dieu_chinh")}}
    if kq.get("ly_do_dung"):
        gon["ly_do_dung"] = kq["ly_do_dung"]
    if ma_thoat != 0:
        print(json.dumps(gon, ensure_ascii=False, indent=1))
        return 2
    files = [f"{m}={os.path.join(cx.GIA, f'gia_{m}_ctck.csv')}" for m in t["ma"]]
    mt, out = chay_lenh(cx, "05 kiem_tra_du_lieu.py", [os.path.join(HERE, "kiem_tra_du_lieu.py")] + files,
                        out=os.path.join(cx.GIA, "kiem-tra.json"), canh_bao_khi_ma=(1,))
    kt = doc_json(os.path.join(cx.GIA, "kiem-tra.json")) or {}
    gon["kiem_tra"] = {k: kt.get(k) for k in ("loi", "dong_tam") if kt.get(k)} or "sạch"
    print(json.dumps(gon, ensure_ascii=False))
    return 0


def tb20(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = [x for x in csv.DictReader(f) if x.get("close")]
    if len(r) < 20:
        return None
    c = [float(x["close"]) for x in r[-20:]]
    tb = sum(c) / 20
    return r[-1]["date"], c[-1], tb, (c[-1] / tb - 1) * 100


COT_SK = ["date", "event", "group", "source_url", "reliability", "note"]


def ghep_su_kien(cx, t):
    """Phân tích sâu: thêm sự kiện mới của agent theo mã (ma/su_kien_<MÃ>.csv) và sự kiện chung
    (su_kien_A2.csv, su_kien_A3.csv – toàn thị trường, áp cho mọi mã) vào du-an/<MÃ>/su-kien.csv, bỏ dòng trùng."""
    chung = []
    for n in ("su_kien_A2.csv", "su_kien_A3.csv"):
        chung += doc_sk(cx.p(n))
    tong, loi = 0, []
    for ma in t["ma"]:
        moi = doc_sk(cx.p("ma", f"su_kien_{ma}.csv")) + chung
        f = os.path.join(cx.DA, ma, "su-kien.csv")
        cu = doc_sk(f)
        co = {(r.get("date", ""), r.get("event", "").strip().lower()) for r in cu}
        them = []
        for r in moi:
            k = (r.get("date", ""), r.get("event", "").strip().lower())
            if r.get("date") and r.get("event") and k not in co:
                co.add(k)
                them.append(r)
        if not them:
            continue
        try:
            os.makedirs(os.path.dirname(f), exist_ok=True)
            moi_file = not os.path.isfile(f) or os.path.getsize(f) == 0
            cot = COT_SK
            if not moi_file:
                with open(f, newline="", encoding="utf-8-sig") as fi:
                    cot = [c.strip() for c in (next(csv.reader(fi), None) or COT_SK)]
                with open(f, "rb") as fi:
                    fi.seek(-1, 2)
                    thieu_xuong_dong = fi.read(1) not in (b"\n", b"\r")
                if thieu_xuong_dong:
                    with open(f, "a", encoding="utf-8") as fo:
                        fo.write("\n")
            with open(f, "a", newline="", encoding="utf-8") as fo:
                w = csv.DictWriter(fo, fieldnames=cot, extrasaction="ignore", restval="")
                if moi_file:
                    w.writeheader()
                w.writerows(them)
            tong += len(them)
        except OSError as e:
            loi.append(f"{ma}: {e}")
    if loi:
        cx.ghi("24 chay_sau.py · ghép sự kiện", "loi", "; ".join(loi))
    else:
        cx.ghi("24 chay_sau.py · ghép sự kiện", "ok", f"thêm {tong} dòng sự kiện")


def doc_sk(path):
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            return [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]
    except OSError:
        return []


def du_bao_xs(cx, t):
    """Bước 25a: xác suất tăng 5/20 phiên + vùng 80% cho mọi mã, tự chấm dự báo cũ trong data/du-bao-xs.json."""
    gia = [f"{m}={os.path.join(cx.GIA, f'gia_{m}_ctck.csv')}" for m in t["ma"]
           if os.path.isfile(os.path.join(cx.GIA, f"gia_{m}_ctck.csv"))]
    if not gia:
        cx.ghi("25a du_bao_xs.py", "loi", "không có file giá gia_<MÃ>_ctck.csv nào")
        return 1
    args = [os.path.join(HERE, "du_bao_xs.py"), "--gia"] + gia + ["--ky-han"] + KY_HAN_XS + [
        "--lich-su", os.path.join(cx.DA, "data", LICH_SU_XS), "--ra", cx.p("du_bao_xs.json")]
    vni = os.path.join(cx.GIA, "gia_VNINDEX_ctck.csv")
    if os.path.isfile(vni):
        args += ["--chi-so", vni]
    mt, _ = chay_lenh(cx, "25a du_bao_xs.py", args, out=cx.p("du_bao_xs.txt"))
    return mt


def cmd_tinh(cx):
    a, t = cx.a, cx.tt()
    vn = os.path.join(cx.DA, "data", "von-ngoai.csv")
    vni = os.path.join(cx.GIA, "gia_VNINDEX_ctck.csv")
    if t["che_do"] != "ban-tin":
        ghep_su_kien(cx, t)
        args = [os.path.join(HERE, "chay_sau.py")] + t["ma"] + ["--gia-dir", cx.GIA, "--du-an", cx.DA, "--out", cx.W,
                                                              "--bieu-do"] + t["bieu_do"] + ["--nhat-ky", cx.NK]
        if a.nghi:
            args += ["--nghi"] + a.nghi
        if a.kich_ban:
            args += ["--kich-ban"] + a.kich_ban
        if t["che_do"] == "sau-nhe":
            args.append("--nhe")
        mt, _ = chay_lenh(cx, "24 chay_sau.py", args)
        mx = du_bao_xs(cx, t)
        if mx == 0 and os.path.isfile(cx.p("tom_tat_script.md")):
            with open(cx.p("tom_tat_script.md"), "a", encoding="utf-8") as f:
                f.write("\n\n## Dự báo xác suất (du_bao_xs.py)\n" + (doc_file(cx.p("du_bao_xs.txt")) or "") + "\n")
        print(f"Xong. Đọc {cx.p('tom_tat_script.md')} (dòng LỖI cũng có trong nhật ký)." if mt == 0 else "chay_sau.py lỗi: xem nhật ký.")
        return mt

    # bản tin sáng
    if os.path.isfile(vn):
        with open(vn, encoding="utf-8") as f:
            dau = f.readline()
        if "vix" not in dau.split(","):
            chay_lenh(cx, "21 chuoi_truyen_dan.py (thêm cột)", [os.path.join(HERE, "chuoi_truyen_dan.py"), vn, "--them-cot"])
        chay_lenh(cx, "20 ap_luc_von_ngoai.py", [os.path.join(HERE, "ap_luc_von_ngoai.py"), vn, "--chu"], out=cx.p("ap_luc.txt"))
        chay_lenh(cx, "21 chuoi_truyen_dan.py", [os.path.join(HERE, "chuoi_truyen_dan.py"), vn, "--vnindex", vni, "--chu"],
                  out=cx.p("chuoi.txt"))
    else:
        cx.ghi("20 ap_luc_von_ngoai.py", "loi", f"không có file {vn}")
    for i, ma in enumerate(t["bieu_do"]):
        buoc = f"{22 + i} forecast6/chart6 {ma}"
        G = os.path.join(cx.GIA, f"gia_{ma}_ctck.csv")
        os.makedirs(cx.p(ma), exist_ok=True)
        args = [os.path.join(HERE, "forecast6.py"), G]
        ls = file_lich_su(cx, ma)
        if ls:
            args += ["--lich-su", ls]
            cu = (doc_json(ls) or {}).get("du_bao") or []
            hs = cu[-1].get("he_so_gian_vung") if cu else None
            hs = hs[5] if isinstance(hs, list) and len(hs) >= 6 else hs[-1] if isinstance(hs, list) and hs else hs
            if isinstance(hs, (int, float)):
                args += ["--khong-kiem-chung", "--he-so", str(hs)]
        else:
            ls = os.path.join(cx.DA, ma, LICH_SU_DU_BAO[1])
            os.makedirs(os.path.dirname(ls), exist_ok=True)
            args += ["--lich-su", ls]
            cx.ghi(buoc, "canh-bao", f"chưa có lịch sử dự báo của {ma}: tạo mới {ls}, chạy có kiểm chứng (chậm hơn)",
                   "Bình thường ở lần đầu. Các lần sau vẫn báo thì agent T chưa tải file du-bao-6-phien*.json của mã này.")
        if a.nghi:
            args += ["--nghi"] + a.nghi
        fj = cx.p(ma, "du_bao_6_phien.json")
        mt, _ = chay_lenh(cx, buoc + " · forecast6", args, out=fj, ghi_ok=False)
        if mt != 0:
            continue
        mt, _ = chay_lenh(cx, buoc + " · chart6", [os.path.join(HERE, "chart6.py"), G, "--ma", ma, "--du-bao", fj,
                                                   "--out", cx.p(f"{ma}-6-phien.png")], out=cx.p(f"{ma}-6-phien.txt"), ghi_ok=False)
        if mt == 0:
            cx.ghi(buoc, "ok")
    dong = []
    for ma in t["ma"]:
        if ma in t["bieu_do"]:
            continue
        r = tb20(os.path.join(cx.GIA, f"gia_{ma}_ctck.csv"))
        dong.append(f"- {ma}: không đủ 20 phiên" if not r else
                    f"- {ma} ({r[0]}): đóng cửa {r[1]:g}, TB20 {r[2]:.2f}, {'trên' if r[3] >= 0 else 'dưới'} TB20 {abs(r[3]):.1f}%")
    with open(cx.p("tb20.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(dong) + "\n")
    du_bao_xs(cx, t)
    print("Xong. Kết quả: " + ", ".join(
        [cx.p("ap_luc.txt"), cx.p("chuoi.txt"), cx.p("tb20.txt"), cx.p("du_bao_xs.txt")] + [cx.p(f"{m}-6-phien.txt") for m in t["bieu_do"]]
        + [cx.p(f"{m}-6-phien.png") for m in t["bieu_do"]]))
    print(tom_tat(cx.NK).splitlines()[0])
    return 0


def doc_muc(path):
    """Tách file markdown theo tiêu đề '## …' → {tiêu đề: nội dung}."""
    s = doc_file(path) or ""
    out, cur = {}, None
    for l in s.splitlines():
        if l.startswith("## "):
            cur = l[3:].strip()
            out[cur] = []
        elif cur is not None:
            out[cur].append(l)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def khop_muc(muc_tu_viet, tieu_de):
    """Tiêu đề phiên chính viết có thể ngắn hơn mẫu: khớp theo phần trước dấu '(' hoặc '–'."""
    goc = tieu_de.split("(")[0].split("–")[0].strip().lower()
    return [v for k, v in muc_tu_viet.items() if k.split("(")[0].split("–")[0].strip().lower() == goc]


def ghep_phu_luc(cx, t):
    W = cx.p
    tv = doc_muc(W("phu_luc_tu_viet.md"))
    M = {t.split(" (")[0].split(" –")[0]: t for t in MAU_PHU_LUC}
    tu_dong = {
        M["Kỹ thuật MBB, TCB"]: [W(f"{m}-6-phien.txt") for m in t["bieu_do"]] + [W("tb20.txt")],
        M["Dự báo xác suất"]: [W("du_bao_xs.txt")],
        M["Thế giới đêm qua"]: [("tru", W("ket_qua_B2.md"), "Dòng tiền Việt Nam")],
        M["Dòng vốn ngoại"]: [W("ap_luc.txt"), ("muc", W("ket_qua_B2.md"), "Dòng tiền Việt Nam")],
        M["Chuỗi truyền dẫn"]: [W("chuoi.txt")],
        M["Tin doanh nghiệp không đưa lên thân bản tin"]: [W("ma", f"{m}.md") for m in t["ma"]],
        M["Doanh nghiệp và ngành tham chiếu"]: [W("tham_chieu_B2.csv")],
        M["Chưa kiểm chứng"]: [W("kiem_chung.md")],
        M["Độ đầy đủ dữ liệu"]: sorted(glob.glob(W("danh_muc_*.md"))),
        M["Nguồn"]: sorted(glob.glob(W("nguon_*.md"))),
    }
    phan = [f"# Phụ lục bản tin {dt.date.fromisoformat(t['ngay']).strftime('%d/%m')}"]
    for td in MAU_PHU_LUC:
        noi = []
        if td.startswith("Nhật ký chạy"):
            noi.append(doc_file(cx.NK) or "")
        for f in tu_dong.get(td, []):
            if isinstance(f, tuple):  # (muc|tru, file, tiêu đề): chỉ lấy / bỏ đúng một mục ## của file
                kieu, f, ten = f
                muc = doc_muc(f)
                c = (muc.get(ten) if kieu == "muc" else
                     "\n\n".join(f"## {k}\n{v}" for k, v in muc.items() if k != ten) or None) if muc else None
                if kieu == "tru" and not muc:
                    c = doc_file(f)
            else:
                c = doc_file(f)
            if c:
                c = "\n".join("###" + l.lstrip("#") if l.startswith("#") else l for l in c.splitlines())
                noi.append(c if len(tu_dong[td]) == 1 else f"### {os.path.basename(f)}\n{c}")
        if td == "Độ chính xác dự báo":
            xs = (doc_json(W("du_bao_xs.json")) or {}).get("lich_su", {}).get("tong")
            if xs:
                noi.append("- du_bao_xs.py (mọi mã): " + json.dumps(xs, ensure_ascii=False))
            for m in t["bieu_do"]:
                d = (doc_json(W(m, "du_bao_6_phien.json")) or {}).get("cham_du_bao_truoc") or {}
                if d.get("tong_hop"):
                    noi.append(f"- {m} (forecast6.py): " + json.dumps(d["tong_hop"], ensure_ascii=False))
        noi += khop_muc(tv, td)
        phan.append(f"## {td}\n" + ("\n\n".join(x for x in noi if x) or "(không có)"))
    with open(W("phu_luc.md"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(phan) + "\n")


def cmd_ghep(cx):
    t = cx.tt()
    if t["che_do"] != "ban-tin":
        bc = cx.p("bao_cao.md")
        if not os.path.isfile(bc):
            cx.ghi("28 Viết bản tin/báo cáo và phụ lục", "loi", f"chưa có {bc}", "Agent tổng hợp (bước 25) chưa ghi báo cáo.")
            return 1
        s = doc_file(bc)
        if "## Nhật ký chạy" not in s:
            with open(bc, "a", encoding="utf-8") as f:
                f.write("\n\n## Nhật ký chạy (nguyên văn research/nhat-ky-chay.txt)\n" + (doc_file(cx.NK) or "") + "\n")
        cx.ghi("28 Viết bản tin/báo cáo và phụ lục", "ok", "đã thêm Nhật ký chạy vào bao_cao.md")
        print(f"Xong: {bc}. Tiếp theo: agent O.")
        return 0
    thieu_viet = [f for f in (cx.p("ghi_chu_dau.md"), cx.p("ban_tin.md")) if not os.path.isfile(f)]
    if thieu_viet:
        cx.ghi("28 Viết bản tin/báo cáo và phụ lục", "loi", "chưa có " + ", ".join(thieu_viet),
               "Phiên chính viết ghi_chu_dau.md và ban_tin.md theo mẫu ở mục Chế độ B của phien-chinh.md trước khi ghép.")
        return 1
    # ghi trước dòng nhật ký của bước 28 để phụ lục chứa cả dòng đó
    thieu = [f for f in (cx.p("ket_qua_B2.md"),) + tuple(cx.p("ma", f"{m}.md") for m in t["ma"])
             if not os.path.isfile(f)]
    if os.path.isfile(cx.p("ket_qua_B2.md")) and "Dòng tiền Việt Nam" not in doc_muc(cx.p("ket_qua_B2.md")):
        thieu.append(cx.p("ket_qua_B2.md") + " (thiếu mục '## Dòng tiền Việt Nam')")
    cx.ghi("28 Viết bản tin/báo cáo và phụ lục", "canh-bao" if thieu else "ok",
           ("thiếu file agent: " + ", ".join(os.path.basename(f) for f in thieu)) if thieu else "",
           "Agent chưa ghi đúng tên file hoặc tên mục kết quả (ket_qua_B2.md, ma/<MÃ>.md): mục đó trong phụ lục ghi (không có)." if thieu else "")
    ghep_phu_luc(cx, t)
    note = os.path.join(cx.DA, "obsidian", "Bản tin", f"{t['ngay']} Bản tin.md")
    os.makedirs(os.path.dirname(note), exist_ok=True)
    with open(note, "w", encoding="utf-8") as f:
        for p in (cx.p("ghi_chu_dau.md"), cx.p("ban_tin.md"), cx.p("phu_luc.md")):
            f.write(doc_file(p) + "\n\n")
    print(f"Xong: {cx.p('phu_luc.md')} và ghi chú {note}")
    tt = tom_tat(cx.NK)
    if "Mọi bước OK" not in tt:
        print("Thêm dòng này vào mục 'Dữ liệu' của thân bản tin TRƯỚC KHI gửi (ghi chú đã ghép; sửa ban_tin.md thì chạy lại ghep):")
        print("Nhật ký: " + tt.splitlines()[0].replace("Nhật ký chạy: ", "") + " – chi tiết ở phụ lục")
    return 0


def them_dong_bo(cx, ngay, duong_dan):
    f = os.path.join(cx.DA, "NHAC-DONG-BO.md")
    s = doc_file(f)
    if s is None or "## Đang chờ đồng bộ" not in s:
        cx.ghi("29 nen_du_lieu.py", "canh-bao", f"không có {f} hoặc thiếu mục 'Đang chờ đồng bộ' – chưa thêm danh sách chờ")
        return False
    dau, sau = s.split("## Đang chờ đồng bộ", 1)
    than, _, con_lai = sau.partition("\n## ")
    dong = [l for l in than.strip().splitlines() if l.strip() and l.strip() != "(không có)"]
    co = {l.split(" (cập nhật")[0] for l in dong}
    for p in duong_dan:
        if f"- {p}" not in co:
            dong.append(f"- {p} (cập nhật {ngay})")
    moi = dau + "## Đang chờ đồng bộ\n" + "\n".join(dong) + "\n" + ("\n## " + con_lai if con_lai else "")
    with open(f, "w", encoding="utf-8") as fo:
        fo.write(moi)
    return True


def cmd_luu(cx):
    t = cx.tt()
    for m in t["ma"] + ["VNINDEX", "VN30"]:
        src = os.path.join(cx.GIA, f"gia_{m}_ctck.csv")
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(cx.DA, "data", f"{m}.csv"))
        else:
            cx.ghi("29 nen_du_lieu.py", "loi", f"không có {src} để chép về lịch sử giá")
    if t["che_do"] != "ban-tin":
        bc, notes = cx.p("bao_cao.md"), glob.glob(os.path.join(cx.DA, "obsidian", "Báo cáo sâu", f"{t['ngay']} Phân tích sâu.md"))
        if notes and os.path.isfile(bc) and "## 0. Chấm dự báo" not in (doc_file(notes[0]) or ""):
            with open(notes[0], "a", encoding="utf-8") as f:
                f.write("\n---\n\n" + doc_file(bc) + "\n")
        elif not notes:
            cx.ghi("29 nen_du_lieu.py", "loi", "không có ghi chú Báo cáo sâu của hôm nay", "Agent O (bước 27) chưa tạo ghi chú báo cáo.")
    mt, out = chay_lenh(cx, "29 nen_du_lieu.py", [os.path.join(HERE, "nen_du_lieu.py"), "--thu-muc", cx.DA, "--ngay", t["ngay"]],
                        out=cx.p("nen.json"))
    cu = t.get("anh_chup_du_an") or {}
    moi = anh_chup(cx.DA)
    doi = sorted(k for k, h in moi.items() if cu.get(k) != h and k != "NHAC-DONG-BO.md")
    obs = [k[len("obsidian/"):] for k in doi if k.startswith("obsidian/") and k != "obsidian/da-dong-bo.md"]
    if obs and them_dong_bo(cx, t["ngay"], obs):
        doi.append("NHAC-DONG-BO.md")
    if not cu:
        cx.ghi("29 nen_du_lieu.py", "canh-bao", "không có ảnh chụp dự án lúc bắt đầu (lệnh gia chưa chạy?) – liệt kê MỌI file")
    # Bản chạy tốt: lần chạy không có dòng LỖI/DỪNG nào → ghi lại commit để có thể dời nhánh on-dinh tới đó
    dong = [l.split(" | ")[1] for l in open(cx.NK, encoding="utf-8") if l[:2].isdigit()] if os.path.isfile(cx.NK) else []
    if dong and not {"LỖI", "DỪNG"} & set(dong) and t.get("phien_ban"):
        f = os.path.join(cx.DA, "data", "ban-chay-tot.txt")
        cu_dong = [l for l in (doc_file(f) or "").splitlines() if l.strip() and not l.startswith("#")]
        cu_dong.append(f"{t['phien_ban']} · {t['ngay']} · {t['che_do']}")
        with open(f, "w", encoding="utf-8") as fo:
            fo.write("# Commit của skill đã chạy trọn không lỗi (mới nhất ở cuối). Claude dời nhánh on-dinh tới dòng cuối khi sửa kho (README).\n"
                     + "\n".join(cu_dong[-10:]) + "\n")
        if "data/ban-chay-tot.txt" not in doi:
            doi.append("data/ban-chay-tot.txt")
    ds = [{"local_path": os.path.abspath(os.path.join(cx.DA, k)), "path": f"{DU_AN_GOC}/{k}"} for k in doi]
    with open(cx.p("can-luu.json"), "w", encoding="utf-8") as f:
        json.dump(ds, f, ensure_ascii=False, indent=1)
    print(f"Cần project_write {len(ds)} file (danh sách cũng ở {cx.p('can-luu.json')}); mỗi file: path=…, local_path=…")
    for d in ds:
        print(f"- {d['path']}  ←  {d['local_path']}")
    return mt


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("che_do", choices=["ban-tin", "sau", "sau-nhe"])
    ap.add_argument("--w", default="research", help="thư mục làm việc (mặc định research)")
    sp = ap.add_subparsers(dest="lenh", required=True)
    b = sp.add_parser("bat-dau")
    b.add_argument("--ma", nargs="+", required=True)
    b.add_argument("--bieu-do", nargs="*", default=["MBB", "TCB"])
    b.add_argument("--ngay")
    g = sp.add_parser("gia")
    g.add_argument("--phien", required=True)
    g.add_argument("--cong-cu")
    ti = sp.add_parser("tinh")
    ti.add_argument("--nghi", nargs="*", default=[])
    ti.add_argument("--kich-ban", nargs="*", default=[])
    for n in ("ghep", "luu", "ke-hoach"):
        sp.add_parser(n)
    a = ap.parse_args()
    cx = Ctx(a)
    f = {"bat-dau": cmd_bat_dau, "gia": cmd_gia, "tinh": cmd_tinh, "ghep": cmd_ghep, "luu": cmd_luu,
         "ke-hoach": cmd_ke_hoach}[a.lenh]
    try:
        return f(cx)
    except BrokenPipeError:
        raise
    except Exception as e:  # lỗi của chính chay.py: ghi nhật ký để biết đây là lỗi code
        import traceback
        tb = traceback.format_exc()
        try:
            ghi_dong(cx.NK, f"chay.py {a.lenh}", "loi", f"{type(e).__name__}: {e}", goi_y(tb))
        except Exception:
            pass
        raise


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # đầu ra bị cắt (vd. `| head`): không phải lỗi của skill
        try:
            sys.stdout = open(os.devnull, "w")
        except OSError:
            pass
        sys.exit(0)
