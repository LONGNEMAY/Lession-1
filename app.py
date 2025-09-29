# -*- coding: utf-8 -*-
"""
Created on Mon Sep 29 14:35:40 2025

@author: ACER
"""

# app.py
import streamlit as st
import tempfile
from pathlib import Path
import os

# map đơn vị
UNIT_TO_MINUTES = {"phút": 1, "giờ": 60, "ngày": 1440}
REMIND_METHODS = {"popup": "popup", "email": "email"}

st.set_page_config(page_title="Lên lịch thời khóa biểu tự động")

st.title("📅 Lên lịch thời khóa biểu tự động")

# upload file
uploaded_file = st.file_uploader("File Excel TKB (.xls, .xlsx)", type=["xls", "xlsx"])

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    notify_value = st.number_input("Nhắc trước", min_value=0, value=10, step=1)
with col2:
    unit = st.selectbox("Đơn vị", list(UNIT_TO_MINUTES.keys()))
with col3:
    method = st.selectbox("Phương thức", list(REMIND_METHODS.keys()))

prefix = st.text_input("Tiền tố sự kiện", value="[TKB]")

st.write("---")
st.write("ℹ️ Để tạo sự kiện Calendar cần cấu hình Google API (credentials).")

# helper: lưu file upload tạm
def save_uploaded_file(uploaded_file):
    suffix = Path(uploaded_file.name).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_file.read())
    tmp.flush()
    tmp.close()
    return tmp.name

# import các hàm hiện có (nếu bạn đã có read_excel.py và google_calendar.py)
try:
    from read_excel import doc_tkb
    from google_calendar import dang_nhap_google, tao_su_kien, xoa_su_kien_tkb
    HAS_MODULES = True
except Exception as e:
    HAS_MODULES = False
    MODULE_ERROR = str(e)

def len_lich(file_excel_path, remind_minutes, remind_method, prefix):
    events = doc_tkb(file_excel_path)
    service = dang_nhap_google()
    reminders = [{"method": remind_method, "minutes": remind_minutes}]
    created = 0
    for e in events:
        if not (e.get("gio_bd") and e.get("gio_kt") and e.get("thu")):
            continue
        tao_su_kien(
            service=service,
            mon=e.get("mon"), phong=e.get("phong"), giang_vien=e.get("giang_vien"),
            start_date=e.get("ngay_bat_dau"), end_date=e.get("ngay_ket_thuc"),
            weekday=e.get("thu"), start_time=e.get("gio_bd"), end_time=e.get("gio_kt"),
            reminders=reminders, prefix=prefix
        )
        created += 1
    return created

def xoa_lich(prefix):
    service = dang_nhap_google()
    xoa_su_kien_tkb(service, prefix=prefix)

# Buttons
col_a, col_b, col_c = st.columns(3)
with col_a:
    if st.button("📌 Lên sự kiện"):
        if not uploaded_file:
            st.warning("Hãy chọn file Excel trước.")
        elif not HAS_MODULES:
            st.error("Thiếu module cần thiết: " + MODULE_ERROR)
        else:
            path = save_uploaded_file(uploaded_file)
            remind_minutes = int(notify_value) * UNIT_TO_MINUTES.get(unit, 1)
            remind_method = REMIND_METHODS.get(method, "popup")
            try:
                with st.spinner("Đang tạo sự kiện..."):
                    created = len_lich(path, remind_minutes, remind_method, prefix.strip() or "[TKB]")
                st.success(f"Hoàn tất — đã tạo ~{created} sự kiện.")
            except Exception as ex:
                st.error("Lỗi khi tạo sự kiện: " + str(ex))

with col_b:
    if st.button("🗑 Xóa sự kiện"):
        if not HAS_MODULES:
            st.error("Thiếu module cần thiết: " + MODULE_ERROR)
        else:
            try:
                with st.spinner("Đang xóa..."):
                    xoa_lich(prefix.strip() or "[TKB]")
                st.success("Đã xóa sự kiện có prefix: " + (prefix.strip() or "[TKB]"))
            except Exception as ex:
                st.error("Lỗi khi xóa sự kiện: " + str(ex))

with col_c:
    if st.button("🔑 Đăng nhập Google khác"):
        if os.path.exists("token.json"):
            os.remove("token.json")
            st.success("✅ Token đã được xoá. Lần tới sẽ hỏi đăng nhập Google mới.")
        else:
            st.info("⚠️ Hiện chưa có token nào được lưu.")
