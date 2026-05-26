import datetime
import os.path
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import SCOPES, LOCAL_TZ, EXCLUDED_CALENDARS

def get_calendar_events():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
        except Exception:
            # Refresh token is likely expired or invalid, request a new one
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    # Haal events op van nu tot 2 maanden vooruit
    # Gebruik timezone-aware now in plaats van utcnow() (deprecated)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    all_events = []
    
    # Haal alle kalenders op
    calendars_result = service.calendarList().list().execute()
    calendars = calendars_result.get('items', [])
    
    for calendar in calendars:
        cal_name = calendar.get('summary', '')
        if cal_name in EXCLUDED_CALENDARS:
            continue
            
        try:
            events_result = service.events().list(
                calendarId=calendar['id'], 
                timeMin=now,
                singleEvents=True, 
                orderBy='startTime'
            ).execute()
            all_events.extend(events_result.get('items', []))
        except Exception as e:
            print(f"Kon events voor kalender '{cal_name}' niet ophalen: {e}")

    return all_events

def check_conflict(prikker_start, prikker_end, events):
    """
    Vergelijkt het tijdslot van Datumprikker met je Google Calendar events.
    """
    for event in events:
        # Negeer evenementen die de hele dag duren (deze hebben een 'date' veld i.p.v. 'dateTime')
        if 'date' in event['start']:
            continue

        # Google geeft 'date' voor hele dag of 'dateTime' voor specifieke tijden
        ev_start_str = event['start'].get('dateTime', event['start'].get('date'))
        ev_end_str = event['end'].get('dateTime', event['end'].get('date'))

        # Parse ISO naar datetime objecten
        ev_start = datetime.datetime.fromisoformat(ev_start_str.replace('Z', '+00:00'))
        if ev_start.tzinfo is None:
            ev_start = LOCAL_TZ.localize(ev_start)
            
        ev_end = datetime.datetime.fromisoformat(ev_end_str.replace('Z', '+00:00'))
        if ev_end.tzinfo is None:
            ev_end = LOCAL_TZ.localize(ev_end)

        # Check overlap: (StartA < EndB) AND (EndA > StartB)
        if (prikker_start < ev_end) and (prikker_end > ev_start):
            return True # Er is een conflict
    return False
