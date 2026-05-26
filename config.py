import pytz

# --- SCRIPT CONFIGURATIE ---
DATUMPRIKKER_URL = "https://datumprikker.nl/YOUR_LINK_HERE"
NAAM = "YOUR_NAME_HERE"
EMAIL = "YOUR_EMAIL_HERE"

# --- CALENDAR CONFIGURATIE ---
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
LOCAL_TZ = pytz.timezone("Europe/Amsterdam")
EXCLUDED_CALENDARS = ['Verjaardagen', 'Feestdagen in Nederland', 'Tasks']




