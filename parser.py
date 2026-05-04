import datetime
import re

def parse_dutch_datumprikker_date(date_str):
    """
    Converteert een Datumprikker string naar een start- en eind-datetime object.
    Input format voorbeeld: "ma 12 mei 10:00 - 11:00" of "maandag 12 mei 2026 14:00"
    """
    
    # Mappings voor Nederlandse termen
    maanden = {
        'jan': 1, 'januari': 1,
        'feb': 2, 'februari': 2,
        'mrt': 3, 'maart': 3,
        'apr': 4, 'april': 4,
        'mei': 5,
        'jun': 6, 'juni': 6,
        'jul': 7, 'juli': 7,
        'aug': 8, 'augustus': 8,
        'sep': 9, 'september': 9,
        'okt': 10, 'oktober': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12
    }

    # Opschonen van de string
    date_str = date_str.lower().strip().replace(',', ' ')
    
    # Regex om de onderdelen te extraheren
    # Zoekt naar: [dagnaam] [dagnummer] [maandnaam] [optioneel jaar] [tijdstip]
    pattern = r'(?P<dagnum>\d{1,2})\s+(?P<maand>\w+)\s*(?P<jaar>\d{4})?\s+(?P<start>\d{1,2}:\d{2})\s*(?:-\s*(?P<eind>\d{1,2}:\d{2}))?'
    
    match = re.search(pattern, date_str)
    if not match:
        raise ValueError(f"Kon datum format niet herkennen: {date_str}")

    day = int(match.group('dagnum'))
    month_str = match.group('maand')
    month = maanden.get(month_str)
    
    if not month:
        raise ValueError(f"Onbekende maand: {month_str}")

    # Bepaal het jaar: als niet in de tekst, neem huidige jaar.
    # Als de maand al geweest is, ga uit van volgend jaar.
    now = datetime.datetime.now()
    if match.group('jaar'):
        year = int(match.group('jaar'))
    else:
        year = now.year
        if month < now.month:
            year += 1

    # Starttijd parsen
    start_time_str = match.group('start')
    start_dt = datetime.datetime.strptime(f"{year}-{month}-{day} {start_time_str}", "%Y-%m-%d %H:%M")

    # Eindtijd parsen (indien aanwezig, anders default 1 uur later)
    if match.group('eind'):
        end_time_str = match.group('eind')
        end_dt = datetime.datetime.strptime(f"{year}-{month}-{day} {end_time_str}", "%Y-%m-%d %H:%M")
    else:
        end_dt = start_dt + datetime.timedelta(hours=1)

    return start_dt, end_dt
