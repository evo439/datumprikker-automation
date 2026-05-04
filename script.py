import update_dependencies
update_dependencies.update_dependencies()

import datetime
import os.path
import pytz # Belangrijk voor tijdzones
import parser
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- CONFIGURATIE ---
DATUMPRIKKER_URL = "https://datumprikker.nl/YOUR_LINK_HERE"
NAAM = "YOUR_NAME_HERE"
EMAIL = "YOUR_EMAIL_HERE"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
LOCAL_TZ = pytz.timezone("Europe/Amsterdam")
EXCLUDED_CALENDARS = ['Verjaardagen', 'Feestdagen in Nederland', 'Tasks']

def get_calendar_events():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
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

def run_agent():
    events = get_calendar_events()
    
    # Desktop setting
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)
    
    try:
        driver.get(DATUMPRIKKER_URL)

        # 1. Cookies (Desktop selector)
        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button")))
            cookie_btn.click()
        except:
            pass
        

        # 2. Start invullen
        start_btn = wait.until(EC.element_to_be_clickable((By.ID, "nav_next")))
        start_btn.click()

        #2.5 Taal op NL zetten
        try:
            menu_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".toggle-popupmenu")))
            menu_btn.click()

            language_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".select_language a")))
            language_btn.click()

            nederlands_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='?hl=nl']")))
            nederlands_btn.click()
        except Exception as e:
            print(f"Taal switch overgeslagen: {e}")

        time.sleep(1)

        # 3. Grid uitlezen en vergelijken
        # Datumprikker gebruikt vaak een tabel of grid voor de opties
        rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".eventdate")))

        for row in rows:
            try:
                # Hier moet je de parsing aanpassen aan het exacte Datumprikker format
                # Voorbeeld: "maandag 12 mei 2026 14:00 - 15:00"
                date_text = row.find_element(By.CSS_SELECTOR, ".date").text
                
                # Parse de datumtekst naar start en eind datetime objecten
                start_dt, end_dt = parser.parse_dutch_datumprikker_date(date_text)
                
                # Voorzie de tijden van de juiste tijdzone (nodig voor check_conflict)
                prikker_start = LOCAL_TZ.localize(start_dt)
                prikker_end = LOCAL_TZ.localize(end_dt)
                
                # Check op conflicten met Google Calendar
                bezet = check_conflict(prikker_start, prikker_end, events)
                
                if bezet:
                    element = row.find_element(By.CSS_SELECTOR, "li.no")
                    driver.execute_script("arguments[0].click();", element)
                else:
                    element = row.find_element(By.CSS_SELECTOR, "li.yes")
                    driver.execute_script("arguments[0].click();", element)
            except Exception as e:
                print(f"Fout bij verwerken van rij: {e}")
                continue

        # 4. Navigatie & Persoonsgegevens
        next_btn = driver.find_element(By.ID, "nav_next")
        next_btn.click()

        naam_veld = wait.until(EC.visibility_of_element_located((By.ID, "eventname")))
        naam_veld.send_keys(NAAM)
        
        email_veld = driver.find_element(By.ID, "eventemail")
        email_veld.send_keys(EMAIL)

        # 5. Volgende (naar overzichtspagina)
        final_next = driver.find_element(By.ID, "nav_next")
        final_next.click()

        print("Agent is klaar met invullen. Controleer de pagina.")

    finally:
        input("Klaar? Druk op Enter...")
        driver.quit()

if __name__ == "__main__":
    run_agent()
