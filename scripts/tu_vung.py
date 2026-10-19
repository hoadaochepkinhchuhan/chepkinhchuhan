#!/usr/bin/env python3
"""Sao lưu blog 詞彙釋義 Giải Nghĩa Từ Vựng vào thư mục tu-vung/ của website dự phòng.

Mỗi lần chạy:
  1. Kéo toàn bộ bài từ Blogger feed của blog Giải Nghĩa Từ Vựng.
  2. Tách tên Hán, âm Hán Việt, chữ cái đầu; làm sạch nội dung (bỏ hiệu ứng trang trí, mã Word thừa).
  3. Tải ảnh về thư mục anh/ dùng chung với Chép Kinh Chữ Hán.
  4. Sinh trang cho từng mục (tu-vung/bai/*.html), kèm mục trước / mục sau theo thứ tự chữ cái.
  5. Ghi tu-vung/data/tu-vung.js cho trang tra cứu tu-vung/index.html.

Blog không vào được thì giữ nguyên bản đã lưu và không báo lỗi, để phần Chép Kinh vẫn đăng bình thường.

Chạy:  python scripts/tu_vung.py
Thử với dữ liệu mẫu (không cần mạng):  python scripts/tu_vung.py --mau scripts/mau-tu-vung
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cap_nhat as c  # dùng chung các hàm tải, làm sạch, lưu ảnh  # noqa: E402

BLOG = "https://giainghiatuvung.blogspot.com"
TEN_BLOG_HAN = "詞彙釋義"
TEN_BLOG = "Giải Nghĩa Từ Vựng"

THU_MUC = c.GOC / "tu-vung"
THU_MUC_BAI = THU_MUC / "bai"
THU_MUC_DATA = THU_MUC / "data"

# thứ tự chữ cái tiếng Việt cho thanh chữ cái
BANG_CHU = ["A", "Ă", "Â", "B", "C", "D", "Đ", "E", "Ê", "G", "H", "I", "K", "L", "M",
            "N", "O", "Ô", "Ơ", "P", "Q", "R", "S", "T", "U", "Ư", "V", "X", "Y"]


# ---------------------------------------------------------------- nguồn
class Nguon(c.Nguon):
    def feed(self, loai: str, bat_dau: int, so_luong: int) -> dict:
        if self.mau:
            f = self.mau / f"{loai}-{bat_dau}.json"
            return json.loads(f.read_text("utf-8")) if f.exists() else {"feed": {}}
        url = (f"{BLOG}/feeds/{loai}/default?alt=json&max-results={so_luong}"
               f"&start-index={bat_dau}")
        return json.loads(c.tai(url))


# ---------------------------------------------------------------- tách thông tin
RE_TACH = re.compile(r"\s+[-–—]\s+")
RE_THE = re.compile(r"<[^>]+>")


def tach_tieu_de(tieu_de: str) -> tuple[str | None, str]:
    """'羯磨 - Yết-ma' → ('羯磨', 'Yết-ma')."""
    phan = RE_TACH.split(tieu_de.strip(), maxsplit=1)
    if len(phan) == 2 and c.RE_HAN.match(phan[0].strip()):
        return phan[0].strip(), phan[1].strip()
    return None, tieu_de.strip()


def chu_dau(hv: str, nhan: list[str]) -> str:
    for n in nhan:   # blog xếp nhãn theo chữ cái đầu (A, Y…)
        n = n.strip().upper()
        if n in BANG_CHU:
            return n
    for ch in hv:
        if ch.isalpha():
            ch = ch.upper()
            if ch in BANG_CHU:
                return ch
            if ch == "Đ":
                return "Đ"
            goc = c.khong_dau(ch).upper()
            return goc if goc in BANG_CHU else "#"
    return "#"


def van_ban(html_sach: str) -> str:
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>", " ", html_sach)
    s = html.unescape(RE_THE.sub("", s))
    return re.sub(r"\s+", " ", s).strip()


def chuan_tim(s: str) -> str:
    return re.sub(r"\s+", " ", c.khong_dau(s).replace("-", " ")).strip()


def khoa(d: dict):
    chu = d["chu"]
    return (BANG_CHU.index(chu) if chu in BANG_CHU else len(BANG_CHU),
            chuan_tim(d["hv"]), d.get("han") or "")


# ---------------------------------------------------------------- trang
MAU = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{tieu_de_the} · {ten_blog}</title>
<link rel="canonical" href="{goc}">
<link rel="stylesheet" href="../../assets/kieu.css">
<script src="../../assets/do-luong.js"></script>
</head>
<body class="trang-bai">
<header class="dau-trang">
  <a class="ten-site" href="../../index.html"><span lang="zh-Hant">冩漢字佛經</span> Chép Kinh Chữ Hán</a>
  <nav><a href="../../muc-luc.html">Mục lục</a><a href="../index.html">Từ vựng</a></nav>
</header>
<main class="bai">
  <p class="duong-dan"><a href="../index.html">Từ vựng</a> / <a href="../index.html#chu-{chu_url}">{chu}</a></p>
  <h1>{tieu_de_html}</h1>
  <p class="thong-tin">{thong_tin}</p>
  <article class="noi-dung tu-vung-bai">
{noi_dung}
  </article>
  {dieu_huong}
</main>
<footer class="chan-trang">
  <p>Bản lưu dự phòng của blog <span lang="zh-Hant">{ten_blog_han}</span> {ten_blog}, cập nhật {cap_nhat}.</p>
</footer>
</body>
</html>
"""


def nhan_muc(d: dict) -> str:
    han = f'<span class="han" lang="zh-Hant">{html.escape(d["han"])}</span> ' if d.get("han") else ""
    return f'{han}<span class="hv">{html.escape(d["hv"])}</span>'


def dieu_huong(truoc: dict | None, sau: dict | None) -> str:
    if not truoc and not sau:
        return ""
    o = ['<nav class="dieu-huong" aria-label="Mục trước và mục sau">']
    if truoc:
        o.append(f'<a class="truoc" href="{html.escape(Path(truoc["tep"]).name)}">'
                 f'<span class="nhan">Mục trước</span>{nhan_muc(truoc)}</a>')
    else:
        o.append("<span></span>")
    if sau:
        o.append(f'<a class="sau" href="{html.escape(Path(sau["tep"]).name)}">'
                 f'<span class="nhan">Mục sau</span>{nhan_muc(sau)}</a>')
    o.append("</nav>")
    return "".join(o)


# ---------------------------------------------------------------- chính
def xu_ly(nguon: Nguon):
    THU_MUC_BAI.mkdir(parents=True, exist_ok=True)
    THU_MUC_DATA.mkdir(parents=True, exist_ok=True)
    thong_ke = {"anh_moi": 0, "anh_bo_qua": 0}
    doi_anh = c.lam_doi_anh(nguon, thong_ke)
    bay_gio = datetime.now(c.GIO_VN)
    tep_data = THU_MUC_DATA / "tu-vung.json"
    cu = json.loads(tep_data.read_text("utf-8")).get("muc", []) if tep_data.exists() else []

    try:
        bai = c.keo_feed(nguon, "posts")
    except Exception as e:
        print(f"  ! blog Từ Vựng: {e}", file=sys.stderr)
        bai = []
    if not bai:
        print(f"::warning::Không lấy được bài nào từ blog {TEN_BLOG}. Giữ nguyên {len(cu)} mục đã lưu.")
        return
    print(f"{TEN_BLOG}: {len(bai)} bài")

    # link tới bài khác trong blog này → trang lưu; link tới blog Chép Kinh → trang lưu bên đó
    ban_do = {}
    muc_luc_kinh = c.THU_MUC_DATA / "muc-luc.json"
    if muc_luc_kinh.exists():
        for d in json.loads(muc_luc_kinh.read_text("utf-8")).get("muc", []):
            if d.get("goc") and "blogspot.com" in d["goc"]:
                ban_do[c.chuan_hoa_link(d["goc"])] = "../../" + d["tep"]
    tho = []
    for e in bai:
        goc = next((l["href"] for l in e.get("link", []) if l.get("rel") == "alternate"), "")
        id_ = e.get("id", {}).get("$t", "").rsplit("-", 1)[-1]
        tep = c.ten_tep_bai(goc, id_)
        if goc:
            ban_do[c.chuan_hoa_link(goc)] = tep
        tho.append((e, goc, tep))

    danh_sach = []
    for e, goc, tep in tho:
        tieu_de = html.unescape(e.get("title", {}).get("$t", "")).strip() or "(không tiêu đề)"
        nhan = [x["term"] for x in e.get("category", [])]
        p = c.LamSach(doi_anh, ban_do)
        p.feed(e.get("content", {}).get("$t") or e.get("summary", {}).get("$t", ""))
        p.close()
        # trang nằm sâu hơn một cấp so với bai/ của Chép Kinh
        noi_dung = re.sub(r'(src|href)="\.\./anh/', r'\1="../../anh/', p.ket_qua())
        chu_van = van_ban(noi_dung)
        han, hv = tach_tieu_de(tieu_de)
        d = {
            "tieu_de": tieu_de, "han": han, "hv": hv, "chu": chu_dau(hv, nhan), "nhan": nhan,
            "ngay": (e.get("published", {}).get("$t") or "")[:10],
            "tom_tat": chu_van[:160] + ("…" if len(chu_van) > 160 else ""),
            "goc": goc, "tep": f"bai/{tep}",
            "tim": chuan_tim(" ".join([tieu_de, chu_van[:600]])),
        }
        danh_sach.append((d, noi_dung))

    # mục đã lưu mà nay không còn trên blog: giữ lại, ghi chú
    tep_moi = {d["tep"] for d, _ in danh_sach}
    giu = []
    for d in cu:
        if d["tep"] not in tep_moi and (THU_MUC / d["tep"]).exists():
            d["khong_con_tren_blog"] = True
            giu.append(d)

    tat_ca = sorted([d for d, _ in danh_sach] + giu, key=khoa)
    vi_tri = {d["tep"]: i for i, d in enumerate(tat_ca)}
    cap_nhat = bay_gio.strftime("%d/%m/%Y")
    for d, noi_dung in danh_sach:
        i = vi_tri[d["tep"]]
        thong_tin = (f'Đăng ngày {c.ngay_vn(d["ngay"])} · '
                     f'<a href="{html.escape(d["goc"])}" rel="noopener">Xem bài trên blog gốc</a>')
        (THU_MUC / d["tep"]).write_text(MAU.format(
            tieu_de_the=html.escape(d["tieu_de"]), ten_blog=TEN_BLOG, ten_blog_han=TEN_BLOG_HAN,
            goc=html.escape(d["goc"]), chu=html.escape(d["chu"]),
            chu_url=urllib.parse.quote(d["chu"]), tieu_de_html=nhan_muc(d), thong_tin=thong_tin,
            noi_dung=noi_dung, cap_nhat=cap_nhat,
            dieu_huong=dieu_huong(tat_ca[i - 1] if i > 0 else None,
                                  tat_ca[i + 1] if i + 1 < len(tat_ca) else None),
        ), "utf-8")

    goi = {
        "tong": {"cap_nhat": bay_gio.isoformat(timespec="minutes"), "so_muc": len(tat_ca),
                 "bang_chu": BANG_CHU, "blog": BLOG, "dau_moc": c.DAU_MOC.get("posts")},
        "muc": tat_ca,
    }
    tep_data.write_text(json.dumps(goi, ensure_ascii=False, indent=1), "utf-8")
    (THU_MUC_DATA / "tu-vung.js").write_text(
        "window.TU_VUNG=" + json.dumps(goi, ensure_ascii=False, separators=(",", ":")) + ";\n", "utf-8")
    print(f"Xong: {len(tat_ca)} mục từ vựng, ảnh mới {thong_ke['anh_moi']}, "
          f"ảnh bỏ qua vì quá lớn {thong_ke['anh_bo_qua']}.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mau", type=Path, help="thư mục dữ liệu mẫu, không dùng mạng")
    a = ap.parse_args()
    try:
        xu_ly(Nguon(a.mau))
    except Exception as e:  # phần này hỏng thì không được làm hỏng cả lần đăng website
        print(f"::warning::Sao lưu {TEN_BLOG} gặp lỗi, giữ nguyên bản cũ: {e}")
