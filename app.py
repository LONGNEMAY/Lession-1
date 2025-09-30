import os
import flask
import pandas as pd
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow

app = flask.Flask(__name__)
app.secret_key = "secret-key"   # đổi cho an toàn

GOOGLE_CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
REDIRECT_URI = "https://lession-1-4-riiv.onrender.com/oauth2callback"  # đổi thành link Render của bạn

# ========================
# ROUTES
# ========================
@app.route("/")
def index():
    return flask.render_template("index.html")

@app.route("/authorize")
def authorize():
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    flask.session["state"] = state
    return flask.redirect(auth_url)

@app.route("/oauth2callback")
def oauth2callback():
    state = flask.session["state"]
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI,
    )
    flow.fetch_token(authorization_response=flask.request.url)

    creds = flow.credentials
    flask.session["credentials"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }
    return flask.redirect("/")

@app.route("/upload", methods=["POST"])
def upload():
    if "credentials" not in flask.session:
        return flask.redirect("/authorize")

    file = flask.request.files["file"]
    prefix = flask.request.form.get("prefix", "[TKB]")

    # Đọc Excel
    df = pd.read_excel(file)

    creds = Credentials.from_authorized_user_info(flask.session["credentials"], SCOPES)
    service = build("calendar", "v3", credentials=creds)

    for _, row in df.iterrows():
        try:
            # Giả sử THỜI GIAN HỌC dạng: "2025-10-01 08:00-10:00"
            time_range = str(row["THỜI GIAN HỌC"]).split("-")
            start = pd.to_datetime(time_range[0].strip())
            end = pd.to_datetime(time_range[1].strip())

            event = {
                "summary": f"{prefix} {row['TÊN HỌC PHẦN']}",
                "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Ho_Chi_Minh"},
                "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Ho_Chi_Minh"},
            }
            service.events().insert(calendarId="primary", body=event).execute()

        except Exception as e:
            print("❌ Lỗi khi xử lý:", row["THỜI GIAN HỌC"], e)
            continue

    return "✅ Đã tạo sự kiện từ file Excel! <a href='/'>Quay lại</a>"






