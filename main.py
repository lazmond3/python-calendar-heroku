from __future__ import print_function

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from flask import Flask, request, abort, send_from_directory
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

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


def 時間表示(dt: Optional[datetime], date: Optional[datetime.date]) -> str:
    now = datetime.now(JST)
    today = datetime(now.year, now.month, now.day, tzinfo=JST).date()

    if dt:
        date = dt.date()
        if today == date:
            return f"【本日】 {today} {dt.hour:02}:{dt.minute:02}  -- "
        else:
            return f"【明日】 {today + timedelta(days=1)} {dt.hour:02}:{dt.minute:02}  -- "
    else:
        if today == date:
            return f"【本日】 {today}        -- "
        else:
            return f"【明日】 {today}        -- "


def calendar_str() -> str:
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
    for event in events:
        start_datetime = event["start"].get("dateTime")
        start_date = event["start"].get("date")

        if start_datetime:
            sdt_obj_parsed = datetime.strptime(start_datetime, "%Y-%m-%dT%H:%M:%S%z")
        else:
            sdt_obj_parsed = None
            start_date2 = datetime.strptime(start_date, "%Y-%m-%d").date()
        時間 = 時間表示(sdt_obj_parsed, start_date2)

        # print()
        result.append(f"{時間} {event['summary']}")
    return "\n".join(result)

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
    result:str = calendar_str()
    line_bot_api.push_message(RYO_UID, TextMessage(text=result))
    return result

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    user_id = event.source.user_id
    now_timestamp: int = int(datetime.now().timestamp())

    print(f"user id: {event.source.user_id}")
    print(f"time: {now_timestamp}, text: {text}, user_id: {user_id}")

    line_bot_api.reply_message(
        event.reply_token, TextMessage(text=f"time: {now_timestamp}, text: {text}, user_id: {user_id}")
    )
    


# if __name__ == "__main__":
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)