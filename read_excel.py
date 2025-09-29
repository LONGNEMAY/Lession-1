import pandas as pd 
import re
from tiet_gio import quy_doi_tiet


# ---------------- HÀM TÁCH Ô NHIỀU THỨ THÀNH NHIỀU DÒNG ----------------
def tach_thu(text):
    """Tách nội dung thành nhiều đoạn theo từng 'Thứ'."""
    if not isinstance(text, str) or not text.strip():
        return []
    # Tách bằng regex: mỗi "Thứ X" là một đoạn
    return re.split(r"(?=Thứ \d+)", text, flags=re.IGNORECASE)


# ---------------- HÀM PARSE MỘT ĐOẠN (SAU KHI TÁCH) ----------------
def parse_doan(part, ngay_bat_dau, ngay_ket_thuc):
    part = part.strip()
    if not part.lower().startswith("thứ"):
        return None

    # Thứ
    thu = int(m.group(1)) if (m := re.search(r"Thứ (\d+)", part, re.I)) else None

    # Tiết + quy đổi giờ
    if (m := re.search(r"Tiết\s*(\d+)\s*-\s*(\d+)", part, re.I)):
        tiet_bd, tiet_kt = map(int, m.groups())
        gio_bd, gio_kt = quy_doi_tiet(tiet_bd, tiet_kt)
    else:
        tiet_bd = tiet_kt = gio_bd = gio_kt = None

    # Phòng + Giảng viên
    phong = giang_vien = ""
    if "," in part:
        left, giang_vien = map(str.strip, part.rsplit(",", 1))

        # chỉ lấy phòng nếu có ')' phía trước và dữ liệu sau đó không rỗng
        if ")" in left:
            sau_ngoac = left.split(")")[-1].strip()
            if sau_ngoac:
                phong = sau_ngoac

    return dict(
        ngay_bat_dau=ngay_bat_dau,
        ngay_ket_thuc=ngay_ket_thuc,
        thu=thu,
        tiet_bd=tiet_bd,
        tiet_kt=tiet_kt,
        gio_bd=gio_bd or "",
        gio_kt=gio_kt or "",
        phong=phong,
        giang_vien=giang_vien
    )


# ---------------- HÀM PARSE NGUYÊN Ô ----------------
def parse_thoigian_hoc(text):
    if not isinstance(text, str) or not text.strip():
        return []

    # Lấy ngày bắt đầu - kết thúc
    m = re.search(r"(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})", text)
    if not m:
        return []
    ngay_bat_dau, ngay_ket_thuc = m.groups()

    # Tách thành nhiều đoạn theo Thứ
    parts = tach_thu(text)

    results = []
    for part in parts:
        r = parse_doan(part, ngay_bat_dau, ngay_ket_thuc)
        if r:
            results.append(r)
    return results


# ---------------- HÀM ĐỌC FILE EXCEL ----------------
def doc_tkb(file_path, start_row=5):
    print(f"Đang đọc file: {file_path}")
    df = pd.read_excel(file_path, header=None)

    events = []
    for _, row in df.iloc[start_row:].iterrows():
        if pd.isna(row[0]):  # cột A rỗng => kết thúc
            break

        mon = str(row[4]).strip() if len(row) > 2 else ""    # cột C
        thoigian = str(row[6]).strip() if len(row) > 6 else ""  # cột G
        if mon.lower() in ["", "nan"] or thoigian.lower() in ["", "nan"]:
            continue

        for tg in parse_thoigian_hoc(thoigian):
            events.append({"mon": mon, **tg})

    return events


# ---------------- CHẠY RIÊNG LẺ ----------------
"""if __name__ == "__main__":
    file_path = "TKB_6251100167 - copy.xls"   # đổi tên file cho đúng
    ds_su_kien = doc_tkb(file_path, start_row=5)

    print("===== DANH SÁCH SỰ KIỆN =====")
    for e in ds_su_kien:
        print(e)"""

if __name__ == "__main__":
    ds_su_kien = doc_tkb(".")
    print("===== DANH SÁCH MÔN HỌC =====")
    for e in ds_su_kien:
        print(e)