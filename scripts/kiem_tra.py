#!/usr/bin/env python3
"""Kiểm tra nhanh: hai blog có gì mới so với bản đã lưu không.

Chạy mỗi 5 phút. Chỉ đọc mốc "cập nhật lần cuối" trong feed của mỗi blog (rất nhẹ),
so với mốc đã ghi trong lần sao lưu trước. Có khác thì báo cho bước cập nhật đầy đủ chạy.

Ghi kết quả ra GITHUB_OUTPUT:  co_moi=true | false
Đặt biến môi trường LUON_CHAY=true để bỏ qua kiểm tra (chạy tay, lịch hằng ngày, sửa file).
"""

import json
import os
import urllib.request
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
BLOG = [
    ("Chép Kinh Chữ Hán", "https://hoadaochepkinhchuhan.blogspot.com", GOC / "data" / "muc-luc.json"),
    ("Giải Nghĩa Từ Vựng", "https://giainghiatuvung.blogspot.com", GOC / "tu-vung" / "data" / "tu-vung.json"),
]


def moc_tren_blog(goc: str) -> str | None:
    url = f"{goc}/feeds/posts/default?alt=json&max-results=1"
    req = urllib.request.Request(url, headers={"User-Agent": "ChepKinhChuHan-backup/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return (json.load(r).get("feed", {}).get("updated") or {}).get("$t")


def moc_da_luu(tep: Path) -> str | None:
    try:
        return (json.loads(tep.read_text("utf-8")).get("tong") or {}).get("dau_moc")
    except Exception:
        return None


def main() -> bool:
    if os.environ.get("LUON_CHAY", "").lower() == "true":
        print("Chạy cập nhật đầy đủ (chạy tay, lịch hằng ngày hoặc vừa sửa file).")
        return True
    co_moi = False
    for ten, goc, tep in BLOG:
        try:
            moi = moc_tren_blog(goc)
        except Exception as e:
            print(f"{ten}: không đọc được blog ({e}), bỏ qua lần này.")
            continue
        cu = moc_da_luu(tep)
        if moi and moi != cu:
            print(f"{ten}: có thay đổi ({cu} → {moi}).")
            co_moi = True
        else:
            print(f"{ten}: không có gì mới.")
    return co_moi


if __name__ == "__main__":
    kq = main()
    ra = os.environ.get("GITHUB_OUTPUT")
    if ra:
        with open(ra, "a", encoding="utf-8") as f:
            f.write(f"co_moi={'true' if kq else 'false'}\n")
    print(f"co_moi={'true' if kq else 'false'}")
