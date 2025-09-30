# -*- coding: utf-8 -*-
"""
Created on Mon Sep 29 14:35:40 2025

@author: ACER
"""
import os
import flask
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
import pathlib

# Thông tin app
app = flask.Flask(__name__)
app.secret_key = "your_secret_key"  # đổi thành chuỗi ngẫu nhiên

# Đường dẫn file credentials.json (OAuth Web Client từ Google Cloud)
GOOGLE_CLIENT_SECRETS_FILE = "credentials.json"

# Phạm vi quyền cần cấp
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# URL callback sau khi login thành công
REDIRECT_URI = "http://localhost:5000/oauth2callback"
# Khi deploy Render thì đổi thành:
# REDIRECT_URI = "https://ten-app.onrender.com/oauth2callback"

@app.route("/")
def index():
    if "credentials" not in flask.session:
        return '<a href="/authorize">Đăng nhập Google</a>'
    creds = Credentials.from_authorized_user_info(flask.session["credentials"], SCOPES)

    try:
        service = build("calendar", "v3", credentials=creds)
        # Lấy danh sách 5 sự kiện sắp tới
        events_result = service.events().list(
            calendarId="primary", maxResults=5, singleEvents=True,
            orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])
        html = "<h3>Sự kiện sắp tới:</h3><ul>"
        for event in events:
            html += f"<li>{event.get('summary')} - {event['start'].get('dateTime')}</li>"
        html += "</ul><br><a href='/create'>➕ Tạo sự kiện demo</a>"
        return html
    except Exception as e:
        return f"Lỗi API: {str(e)}<br><a href='/authorize'>Đăng nhập lại</a>"

@app.route("/authorize")
def authorize():
    flow = Flow.from_client_secrets_file(
        GOOGLE_CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    flask.session["state"] = state
    return flask.redirect(authorization_url)

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
        "scopes": creds.scopes,
    }
    return flask.redirect("/")

@app.route("/create")
def create_event():
    if "credentials" not in flask.session:
        return flask.redirect("/authorize")

    creds = Credentials.from_authorized_user_info(flask.session["credentials"], SCOPES)
    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": "[Demo] Lịch test",
        "start": {"dateTime": "2025-10-01T10:00:00+07:00"},
        "end": {"dateTime": "2025-10-01T11:00:00+07:00"},
    }
    service.events().insert(calendarId="primary", body=event).execute()

    return "✅ Đã tạo sự kiện demo! <a href='/'>Quay lại</a>"

if __name__ == "__main__":
    app.run("0.0.0.0", 5000, debug=True)

