import requests
from ics import Calendar
import pandas as pd
import datetime

def get_levels(season):
    url = "https://tulospalvelu.leijonat.fi/helpers/getLevels.php"
    payload = {'season': season}
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()

def get_stat_groups(season, level_id, district_id=0):
    url = "https://tulospalvelu.leijonat.fi/serie/helpers/getStatGroups.php"
    payload = {
        'season': season,
        'levelid': level_id,
        'districtid': district_id
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()

def get_teams(season, stat_group_id):
    url = "https://tulospalvelu.leijonat.fi/serie/helpers/getStatGroup.php"
    payload = {'season': season, 'stgid': stat_group_id}
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()

def get_jopox_events():
    pass#<----------Alla jopox-haun runko
    url = "https://s-kiekko-app.jopox.fi/www/ajax/calendar.aspx/LoadMoreEvents"
    cookies = {
        'ASP.NET_SessionId': '-------',   # Replace with your actual ASP.NET_SessionId value
        '_utma': '-------',                         # Replace with your actual _utma value
        '_utmz': '------',                         # Replace with your actual _utmz value
        '_fbp': '------',                           # Replace with your actual _fbp value
        'jpx_team_select': '8787',     # Replace with your actual jpx_team_select value
        'jpxapp': '---------'
       }
    headers = { 
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Referer': 'https://s-kiekko-app.jopox.fi/home/club/8787?web=1',   # Adjust referer if needed, to the page where the request originates from
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    payload = {'subsite':8787, 'fromDate': '30.10.2024 00:00', 'clientType': 1 }
    response = requests.post(url, data=payload, cookies=cookies,  headers=headers)
    response.raise_for_status()
    return response.json

def hae_kalenteri(team_id):
    events_data = []
    print("jopox_team_id------------------>:", team_id)
    ics_url = f'https://ics.jopox.fi/hockeypox/calendar/ical.php?ics=true&e=t&cal=U122013_{team_id}'  # Replace with the actual ICS URL

    # Step 2: Fetch the ICS file
    try:
        response = requests.get(ics_url)
        response.raise_for_status()  # Raise an error for bad responses
        ics_content = response.text
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch ICS file: {e}")
        return []

    # Step 3: Parse the ICS file
    calendar = Calendar(ics_content)

        # Step 4: Extract events into a structured format
    for event in calendar.events:
        # Extract details about each event
        event_name = event.name
        start_date = event.begin.format('YYYY-MM-DD') if event.begin else 'Unknown Start date'
        start_time = event.begin.format('HH:mm') if event.begin else 'Unknown Start time'
        end_time = event.end.format('HH:mm') if event.end else 'Unknown End'
        location = event.location if event.location else 'Unknown Location'
        description = event.description if event.description else 'No Description'
        uid = event.uid if event.uid else 'No UID'

        if "Ottelu" in event_name:
            # Append event data to list
            events_data.append({
                
                "Pvm": start_date,
                "SortableDate": start_date,  # Date in sortable format (YYYY-MM-DD)
                "Tapahtuma": event.name,
                "Aika": f"{start_time} - {end_time}",
                "Paikka": location,
                "Lisätiedot": description,  # Assuming description contains level information
                "Uid": uid.split('_')[-1]
            })

    if events_data:
        return events_data
    else:
        print("No events found in the ICS file.")
        return []
