#!/usr/bin/env python3
"""Lưu file của dự án ra đĩa ĐÚNG TỪNG BYTE mà không phải chép tay nội dung (không tốn token đầu ra).

Công cụ Projects (project_read) trả nội dung file vào cuộc trò chuyện. Script này đọc lại chính
các kết quả đó trong nhật ký phiên (~/.claude/projects/**/*.jsonl, kể cả của agent con) và ghi ra đĩa.

Cách dùng (ngay SAU khi đã gọi project_read cho các file cần, trong cùng phiên hoặc cùng agent):
    python du_an.py luu --out research/du-an [--skill-dir <SKILL_DIR>] [--can <đường dẫn dự án> ...]
        Ghi mỗi file vào <out>/<đường dẫn sau "claude/chung-khoan/">.
        File của skill (claude/chung-khoan/skill/references/*, claude/chung-khoan/scripts/*) được ghi thẳng
        vào <SKILL_DIR>/references|scripts nếu có --skill-dir và thư mục đó ghi được; không thì vào <out>/skill/.
        --can: liệt kê các đường dẫn bắt buộc phải có; thiếu thì báo trong "thieu".
    python du_an.py phien-ban --skill-dir <SKILL_DIR> --md <out>/skill/PHIEN-BAN.md --che-do sang|sau
        In danh sách file trong dự án MỚI HƠN gói skill đang cài (hoặc chưa có trên đĩa) mà chế độ này cần.
        Danh sách rỗng = không phải tải gì.
In ra một dòng JSON. Không gọi mạng, không sửa file nào ngoài thư mục đích.
"""
import argparse
import glob
import json
import os
import re
import sys
import time

GOC = "claude/chung-khoan/"


def _van_ban(c):
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "".join(b.get("text", "") for b in c if isinstance(b, dict))
    return ""


def _giai_ma(s):
    """Trả về dict kết quả project_read, hoặc None."""
    s = s.strip()
    m = re.search(r"Full output saved to:\s*(\S+)", s)
    if "<persisted-output>" in s and m and os.path.isfile(m.group(1)):
        with open(m.group(1), encoding="utf-8") as f:
            s = f.read().strip()
    i = s.find("{")
    if i < 0:
        return None
    try:
        o, _ = json.JSONDecoder().raw_decode(s[i:])
    except ValueError:
        return None
    return o if isinstance(o, dict) else None


def quet(gio=12):
    """{đường dẫn dự án: (thời điểm, dict kết quả)} – lấy kết quả mới nhất của mỗi đường dẫn."""
    goc = os.path.expanduser("~/.claude/projects")
    moc = time.time() - gio * 3600
    files = [p for p in glob.glob(os.path.join(goc, "**", "*.jsonl"), recursive=True) if os.path.getmtime(p) >= moc]
    files.sort(key=os.path.getmtime)
    kq, thu_tu = {}, 0
    for p in files:
        cho = {}
        try:
            f = open(p, encoding="utf-8", errors="replace")
        except OSError:
            continue
        with f:
            for line in f:
                if "project_read" not in line and "tool_result" not in line:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                c = (o.get("message") or {}).get("content")
                if not isinstance(c, list):
                    continue
                for b in c:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_use" and (b.get("input") or {}).get("method") == "project_read":
                        cho[b.get("id")] = b["input"].get("path")
                    elif b.get("type") == "tool_result" and b.get("tool_use_id") in cho:
                        d = _giai_ma(_van_ban(b.get("content")))
                        path = cho[b["tool_use_id"]]
                        if d and not b.get("is_error"):
                            thu_tu += 1
                            kq[d.get("path") or path] = (thu_tu, d)
    return kq


def noi_dung(d):
    """Nội dung file (str) từ kết quả project_read; file lớn được trả bằng đường dẫn tạm."""
    if isinstance(d.get("content"), str):
        return d["content"]
    for k, v in d.items():
        if k != "path" and isinstance(v, str) and len(v) < 500 and os.path.isfile(v):
            with open(v, encoding="utf-8") as f:
                return f.read()
    return None


def dich(path, out, skill_dir):
    rel = path[len(GOC):] if path.startswith(GOC) else path.replace("/", "_")
    if skill_dir and os.access(skill_dir, os.W_OK):
        if rel.startswith("skill/references/"):
            return os.path.join(skill_dir, rel[len("skill/"):])
        if rel.startswith("scripts/"):
            return os.path.join(skill_dir, rel)
    elif rel.startswith("scripts/"):
        return os.path.join(out, "skill", rel)
    return os.path.join(out, rel)


def cmd_luu(a):
    kq = quet(a.gio)
    da, loi = [], []
    for path, (_, d) in sorted(kq.items(), key=lambda x: x[1][0]):
        nd = noi_dung(d)
        if nd is None:
            loi.append(path)
            continue
        to = dich(path, a.out, a.skill_dir)
        os.makedirs(os.path.dirname(to) or ".", exist_ok=True)
        with open(to, "w", encoding="utf-8", newline="") as f:
            f.write(nd)
        da.append({"du_an": path, "dia": to, "ky_tu": len(nd)})
    co = {x["du_an"] for x in da}
    thieu = [p for p in a.can if p not in co]
    print(json.dumps({"da_luu": da, "khong_doc_duoc": loi, "thieu": thieu,
                      "ghi_chu": "thieu/khong_doc_duoc: gọi lại project_read cho các đường dẫn đó rồi chạy lại; vẫn thiếu thì ghi tay."},
                     ensure_ascii=False))
    return 1 if thieu else 0


def cmd_phien_ban(a):
    goi = "2026-11-01"
    p = os.path.join(a.skill_dir, "PHIEN-BAN.txt")
    if os.path.isfile(p):
        m = re.search(r"\d{4}-\d{2}-\d{2}", open(p, encoding="utf-8").read())
        if m:
            goi = m.group(0)
    can = []
    if os.path.isfile(a.md):
        for line in open(a.md, encoding="utf-8"):
            ph = [x.strip() for x in line.lstrip("- ").split("·")]
            if len(ph) < 4 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", ph[1]):
                continue
            trong_skill, ngay, du_an, che_do = ph[0], ph[1], ph[2], ph[3]
            if a.che_do not in che_do:
                continue
            tren_dia = os.path.isfile(os.path.join(a.skill_dir, trong_skill)) or \
                (a.out and os.path.isfile(os.path.join(a.out, "skill", trong_skill)))
            if ngay > goi or not tren_dia:
                can.append(du_an)
    print(json.dumps({"ngay_dong_goi": goi, "can_tai": can}, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="lenh", required=True)
    s = sub.add_parser("luu")
    s.add_argument("--out", required=True)
    s.add_argument("--skill-dir")
    s.add_argument("--can", nargs="*", default=[])
    s.add_argument("--gio", type=float, default=12, help="chỉ đọc nhật ký phiên sửa trong N giờ gần đây")
    s.set_defaults(f=cmd_luu)
    s = sub.add_parser("phien-ban")
    s.add_argument("--skill-dir", required=True)
    s.add_argument("--md", required=True)
    s.add_argument("--che-do", required=True, choices=["sang", "sau"])
    s.add_argument("--out")
    s.set_defaults(f=cmd_phien_ban)
    a = ap.parse_args()
    sys.exit(a.f(a))


if __name__ == "__main__":
    main()
