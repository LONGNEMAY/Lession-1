import os
import datetime as dt
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ----------------------------------------
# Phạm vi quyền (Google Calendar)
# ----------------------------------------
SCOPES = ['https://www.googleapis.com/auth/calendar']

# ----------------------------------------
# Đăng nhập Google và tạo service
# ----------------------------------------
def dang_nhap_google():
    """
    Đăng nhập Google bằng OAuth2, trả về đối tượng service để thao tác Calendar.
    Yêu cầu có file credentials.json trong cùng thư mục.
    """
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES).run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    print("✅ Đăng nhập Google thành công!")
    return build('calendar', 'v3', credentials=creds)

# ----------------------------------------
# Tìm ngày đầu tiên khớp với thứ học
# ----------------------------------------
def tim_ngay_bat_dau(start_date, google_weekday):
    current = start_date
    while current.weekday() != google_weekday:
        current += dt.timedelta(days=1)
    return current

# ----------------------------------------
# Hàm tạo sự kiện lặp hàng tuần
# ----------------------------------------
def tao_su_kien(service, mon, phong, giang_vien,
                start_date, end_date, weekday, start_time, end_time,
                reminders=None, prefix="[TKB]"):
    """
    Tạo sự kiện lặp hàng tuần trên Google Calendar.
    """
    start_date = dt.datetime.strptime(start_date.strip(), "%d/%m/%Y").date()
    end_date = dt.datetime.strptime(end_date.strip(), "%d/%m/%Y").date()

    # Google Calendar: 0=Thứ 2 ... 6=Chủ Nhật
    google_weekday = (weekday - 2) % 7
    current = tim_ngay_bat_dau(start_date, google_weekday)

    start_dt = dt.datetime.combine(current, dt.datetime.strptime(start_time, "%H:%M").time())
    end_dt = dt.datetime.combine(current, dt.datetime.strptime(end_time, "%H:%M").time())

    event = {
        'summary': f"{prefix} {mon}",
        'location': phong,
        'description': f"Giảng viên: {giang_vien}",
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Asia/Ho_Chi_Minh'},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Asia/Ho_Chi_Minh'},
        'recurrence': [f"RRULE:FREQ=WEEKLY;UNTIL={end_date.strftime('%Y%m%d')}T235959Z"],
        'reminders': {'useDefault': False, 'overrides': reminders or []}
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"📅 Đã tạo sự kiện: {event['summary']} ({event.get('id')})")
    return event.get('id')

# ----------------------------------------
# Hàm xóa toàn bộ sự kiện TKB (theo prefix)
# ----------------------------------------
def xoa_su_kien_tkb(service, prefix="[TKB]"):
    """
    Xóa toàn bộ sự kiện có prefix trong Google Calendar.
    """
    events_result = service.events().list(
        calendarId='primary',
        q=prefix,  # Lọc theo từ khóa ngay tại đây
        singleEvents=True,
        orderBy='startTime',
        maxResults=2500
    ).execute()
    events = events_result.get('items', [])
    count = 0
    if not events:
        print(f"ℹ️ Không tìm thấy sự kiện nào có prefix '{prefix}' để xóa.")
        return 0
    for event in events:
        if event.get('summary', '').startswith(prefix):
            service.events().delete(calendarId='primary', eventId=event['id']).execute()
            count += 1
    print(f"🗑️ Đã xóa {count} sự kiện có prefix '{prefix}'.")
    return count