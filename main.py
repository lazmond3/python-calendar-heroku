from __future__ import print_function

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from flask import Flask, abort, request, send_from_directory
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (ImageSendMessage, MessageEvent, TextMessage,
                            TextSendMessage)

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_BOT_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_BOT_CHANNEL_SECRET"))

assert os.getenv("RYO_UID")
assert os.getenv("G_SECRET")
assert os.getenv("CALENDAR_ID")

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
JST = timezone(timedelta(hours=+9), "JST")
RYO_UID = os.getenv("RYO_UID")  # ryo の UID

with open("credentials.json", "w") as f:
    f.write(os.getenv("G_SECRET"))

creds = service_account.Credentials.from_service_account_file("credentials.json")


def 時間表示(
    start_dt: Optional[datetime],
    start_date: Optional[datetime.date],
    end_dt: Optional[datetime],
    end_date: Optional[datetime.date],
) -> str:
    now = datetime.now(JST)
    today = datetime(now.year, now.month, now.day, tzinfo=JST).date()

    if start_dt:
        start_date = start_dt.date()
        if today == start_date:
            # return f"【本日】 {start_dt.hour:02}:{start_dt.minute:02} - {end_dt.hour:02}:{end_dt.minute:02}"
            return f" {start_dt.hour:02}:{start_dt.minute:02} - {end_dt.hour:02}:{end_dt.minute:02}"
        elif today + timedelta(days=1) == start_date:
            return f"【明日】 {start_dt.hour:02}:{start_dt.minute:02} - {end_dt.hour:02}:{end_dt.minute:02}"
        else:
            return f"{start_date} {start_dt.hour:02}:{start_dt.minute:02} - {end_dt.hour:02}:{end_dt.minute:02}"
    else:
        if today == start_date:
            # date_result = f"【本日】 "
            pass
        elif today + timedelta(days=1) == start_date:
            date_result = f"【明日】 "

        # if today + timedelta(days=1) != end_date:
        #     date_result += f" - {end_date}"
        return date_result


def calendar_str() -> List[str]:
    service = build("calendar", "v3", credentials=creds)
    # Call the Calendar API
    UTC = timezone(timedelta(hours=0), "UTC")
    now = datetime.now(JST)  # current date and time
    now_today_start_of_day = datetime(now.year, now.month, now.day, tzinfo=JST)
    converted = now_today_start_of_day.astimezone(UTC)

    next_day = converted + timedelta(days=2)

    iso_now = converted.isoformat()
    next_day_max = next_day.isoformat()  # 'Z' indicates UTC time
    print(f"original: {now} -> 2日後:  {iso_now} -> {next_day_max}")
    now = converted.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time

    events_result = (
        service.events()
        .list(
            # calendarId="primary",
            calendarId=os.getenv("CALENDAR_ID"),
            timeMin=iso_now,
            timeMax=next_day_max,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
            timeZone="JST",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
        print("No upcoming events found.")
    result: List[str] = []
    result_明日: List[str] = []
    for event in events:
        print(event)
        start_datetime_str: Optional[str] = event["start"].get("dateTime")
        start_date_str: Optional[str] = event["start"].get("date")
        end_datetime_str: Optional[str] = event["end"].get("dateTime")
        end_date_str: Optional[str] = event["end"].get("date")

        if start_datetime_str:
            start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%dT%H:%M:%S%z")
            end_dt = datetime.strptime(end_datetime_str, "%Y-%m-%dT%H:%M:%S%z")
            start_date = None
            end_date = None
        else:
            start_dt = None
            end_dt = None
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        時間 = 時間表示(start_dt, start_date, end_dt, end_date)
        target_string: str = f"{時間}\n\t{event['summary']}"
        if "【明日】" in 時間:
            result_明日.append(target_string)
        else:
            result.append(target_string)

    for r in result:
        result_明日.append(r)
    return result_明日


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """

    str_ = calendar_str()
    print(str_)

    # creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    # if os.path.exists("token.pickle"):
    #     with open("token.pickle", "rb") as token:
    #         creds = pickle.load(token)
    #         print(creds)
    #     exit(0)
    # If there are no (valid) credentials available, let the user log in.

    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         creds.refresh(Request())
    #     else:
    #         flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    #         creds = flow.run_local_server(port=0)
    #     # Save the credentials for the next run
    #     with open("token.pickle", "wb") as token:
    #         pickle.dump(creds, token)


@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)

    return "OK"


@app.route("/")
def hello():
    str_out = ""
    str_out += "<h2>Hello from Python!</h2>"
    str_out += "<blockquote>"
    str_out += "こんにちは<p />"
    str_out += "</blockquote>"
    str_out += "Aug/07/2017 PM 12:49<br />"
    return str_out


@app.route("/send")
def send():
    result: List[str] = calendar_str()
    now = datetime.now(JST)
    today = datetime(now.year, now.month, now.day, tzinfo=JST).date()
    line_bot_api.push_message(RYO_UID, TextMessage(text=f"今日の日付: {today}"))
    for r in result:
        line_bot_api.push_message(RYO_UID, TextMessage(text=r))
    return ""


# @handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     text = event.message.text
#     user_id = event.source.user_id
#     now_timestamp: int = int(datetime.now().timestamp())

#     print(f"user id: {event.source.user_id}")
#     print(f"time: {now_timestamp}, text: {text}, user_id: {user_id}")

    # line_bot_api.reply_message(
    #     event.reply_token,
    #     TextMessage(text=f"time: {now_timestamp}, text: {text}, user_id: {user_id}"),
    # )


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        main()
    else:
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port)
