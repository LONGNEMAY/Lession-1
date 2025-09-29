# google_calendar.py
from __future__ import print_function
import datetime
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Quyền truy cập Calendar
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def dang_nhap_google():
    """Đăng nhập Google Calendar, tạo service"""
    creds = None
    # Nếu đã có token.json thì load
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # Nếu chưa có hoặc token hết hạn
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Yêu cầu đăng nhập lại bằng credentials.json
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            # Nếu chạy local không mở được browser thì dùng run_console()
            creds = flow.run_console()

        # Lưu token mới
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    return service

def tao_su_kien(service, mon, phong, giang_vien,
                 start_date, end_date, weekday,
                 start_time, end_time, reminders, prefix="[TKB]"):
    """Tạo sự kiện lịch học trên Google Calendar"""

    # Mapping thứ (Mon, Tue, ...) sang số
    weekday_map = {
        "2": "MO", "3": "TU", "4": "WE", "5": "TH", "6": "FR", "7": "SA", "CN": "SU"
    }
    byday = weekday_map.get(str(weekday), "MO")

    event = {
        "summary": f"{prefix} {mon}",
        "location": phong if phong else "",
        "description": giang_vien if giang_vien else "",
        "start": {
            "dateTime": f"{start_date}T{start_time}:00",
            "timeZone": "Asia/Ho_Chi_Minh",
        },
        "end": {
            "dateTime": f"{start_date}T{end_time}:00",
            "timeZone": "Asia/Ho_Chi_Minh",
        },
        "recurrence": [
            f"RRULE:FREQ=WEEKLY;BYDAY={byday};UNTIL={end_date.replace('-', '')}T235900Z"
        ],
        "reminders": {
            "useDefault": False,
            "overrides": reminders,
        },
    }

    service.events().insert(calendarId="primary", body=event).execute()

def xoa_su_kien_tkb(service, prefix="[TKB]"):
    """Xóa toàn bộ sự kiện có prefix nhất định"""
    events_result = service.events().list(
        calendarId="primary", maxResults=2500, singleEvents=True
    ).execute()
    events = events_result.get("items", [])

    for event in events:
        if event.get("summary", "").startswith(prefix):
            service.events().delete(calendarId="primary", eventId=event["id"]).execute()


