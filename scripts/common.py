"""Hàm dùng chung: đọc CSV giá, xử lý ngày tháng."""
import csv
import datetime as dt
import sys

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y%m%d", "%Y-%m-%d %H:%M:%S")


def parse_date(s):
    s = s.strip()
    for fmt in DATE_FORMATS:
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Không đọc được ngày: {s!r}")


def load_prices(path, min_rows=15):
    """Đọc CSV có các cột date, open, high, low, close, volume (không phân biệt hoa thường).
    Trả về list dict đã sắp xếp cũ -> mới. Cột open/volume có thể thiếu."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("File CSV rỗng.")
    rows = [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in rows]
    for col in ("date", "close"):
        if col not in rows[0]:
            sys.exit(f"Thiếu cột bắt buộc: {col}")

    def num(r, k):
        v = r.get(k, "").replace(",", "")
        if v in ("", "null", "None", "-"):
            return None
        return float(v)

    data = []
    for r in rows:
        try:
            d = parse_date(r["date"])
            c = num(r, "close")
        except ValueError:
            continue
        if c is None:
            continue
        h = num(r, "high")
        l = num(r, "low")
        o = num(r, "open")
        data.append({"date": d, "open": o if o is not None else c,
                     "high": h if h is not None else c, "low": l if l is not None else c,
                     "close": c, "volume": num(r, "volume")})
    data.sort(key=lambda x: x["date"])
    if len(data) < min_rows:
        sys.exit(f"Chỉ có {len(data)} dòng hợp lệ, cần tối thiểu {min_rows}.")
    return data


def add_business_days(d, n):
    """Cộng n ngày làm việc (bỏ thứ Bảy, Chủ nhật; KHÔNG trừ ngày lễ)."""
    step = 1 if n >= 0 else -1
    left = abs(int(round(n)))
    while left > 0:
        d += dt.timedelta(days=step)
        if d.weekday() < 5:
            left -= 1
    return d


def r(x, nd=2):
    return None if x is None else round(x, nd)


def percentile(vals, p):
    if not vals:
        return None
    s = sorted(vals)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def median(vals):
    return percentile(vals, 50)
