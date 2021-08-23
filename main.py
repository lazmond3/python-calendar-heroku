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
from linebot.models import ImageSendMessage, MessageEvent, TextMessage, TextSendMessage

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
    date_result = ""
    if start_dt:
        start_date = start_dt.date()
        if today == start_date:
            # return f"【本日】 {start_dt.hour:02}:{start_dt.minute:02} - {end_dt.hour:02}:{end_dt.minute:02}"
            return f" {start_dt.hour:02}:{start_dt.minute:02} - {end_dt.hour:02}:{end_dt.minute:02}\n"
        elif today + timedelta(days=1) == start_date:
            return f"【明日】 {start_dt.hour:02}:{start_dt.minute:02} - {end_dt.hour:02}:{end_dt.minute:02}\n"
        else:
            return f"{start_date} {start_dt.hour:02}:{start_dt.minute:02} - {end_dt.hour:02}:{end_dt.minute:02}\n"
    else:
        if today == start_date:
            # date_result = f"【本日】 "
            pass
        elif today + timedelta(days=1) == start_date:
            date_result = f"【明日】 \n"

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
        if len(時間) != 0:
            target_string: str = f"{時間}\t{event['summary']}"
        else:
            target_string: str = f"{event['summary']}"
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

def lambda_handler(a1, a2):
    result: List[str] = calendar_str()
    now = datetime.now(JST)
    today = datetime(now.year, now.month, now.day, tzinfo=JST).date()
    line_bot_api.push_message(RYO_UID, TextMessage(text=f"今日の日付: {today}"))
    for r in result:
        line_bot_api.push_message(RYO_UID, TextMessage(text=r))


@app.route("/send")
def send():
    result: List[str] = calendar_str()
    now = datetime.now(JST)
    today = datetime(now.year, now.month, now.day, tzinfo=JST).date()
    line_bot_api.push_message(RYO_UID, TextMessage(text=f"今日の日付: {today}"))
    for r in result:
        line_bot_api.push_message(RYO_UID, TextMessage(text=r))
    return ""


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        main()
    else:
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port)
