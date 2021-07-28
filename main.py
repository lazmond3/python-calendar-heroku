from __future__ import print_function

import os
import pickle
from datetime import datetime, timedelta, timezone
from typing import Optional

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
JST = timezone(timedelta(hours=+9), "JST")

with open("credentials.json", "w") as f:
    assert os.getenv("G_SECRET")
    f.write(os.getenv("G_SECRET"))


def 時間表示(dt: Optional[datetime], date: Optional[datetime.date]) -> str:
    now = datetime.now(JST)
    today = datetime(now.year, now.month, now.day, tzinfo=JST).date()

    if dt:
        date = dt.date()
        if today == date:
            return f"【本日】 {today} {dt.hour:02}:{dt.minute:02} から -- "
        else:
            return f"【明日】 {today + timedelta(days=1)} {dt.hour:02}:{dt.minute:02} から --"
    else:
        if today == date:
            return f"【本日】 {today}  -- "
        else:
            return f"【明日】 {today}  -- "

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

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


    print("Getting the upcoming 10 events")
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=iso_now,
            timeMax=next_day_max,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
            timeZone="JST"
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
        print("No upcoming events found.")
    for event in events:
        # start = event["start"].get("dateTime", event["start"].get("date"))
        # start = event["start"].get("dateTime", event["start"].get("date")) # if 文みたいなものか
        start_datetime = event["start"].get("dateTime")
        start_date = event["start"].get("date")
        # print(f"{start_datetime}, {start_date}")

        if start_datetime:
            sdt_obj_parsed = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M:%S%z')
        else:
            sdt_obj_parsed = None
            start_date2 = datetime.strptime(start_date, "%Y-%m-%d").date()
        # print(f"{start_datetime}, {start_date}, {sdt_obj_parsed}")
        時間 = 時間表示(sdt_obj_parsed, start_date2)

        print(f"{時間} {event['summary']}")

        # print(start, event["summary"], event["description"], type(start), type(event["summary"]))
        # print(start_date, start, event["summary"], type(start), type(event["summary"]))


if __name__ == "__main__":
    main()
