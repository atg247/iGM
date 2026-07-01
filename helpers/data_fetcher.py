import requests
from ics import Calendar
import logging

def get_seasons():
    url = "https://tulospalvelu.leijonat.fi/helpers/getseasons"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_levels(season):
    url = "https://tulospalvelu.leijonat.fi/helpers/getlevels"
    payload = {'season': season}
    response = requests.get(url, params=payload)
    response.raise_for_status()
    return response.json()

def get_stat_groups(season, level_id, district_id=0):
    url = "https://tulospalvelu.leijonat.fi/serie/helpers/getsubseries"
    payload = {
        'season': season,
        'levelid': level_id,
        'districtid': district_id
    }
    response = requests.get(url, params=payload)
    response.raise_for_status()
    return [
        {'StatGroupID': item['subSerieId'], 'StatGroupName': item['subSerieName']}
        for item in response.json()
    ]

def get_teams(season, stat_group_id):
    url = "https://tulospalvelu.leijonat.fi/serie/helpers/getsubserie"
    payload = {'season': season, 'subSerieId': stat_group_id, 'teamid': ''}
    response = requests.get(url, params=payload)
    response.raise_for_status()
    return {'Teams': response.json().get('teams', [])}

def hae_kalenteri(calendar_url):
    descriptions = []
    
    # Step 2: Fetch the ICS file
    try:
        response = requests.get(calendar_url)
        response.raise_for_status()  # Raise an error for bad responses
        ics_content = response.text
    except requests.exceptions.RequestException as e:
        return []

    # Step 3: Parse the ICS file
    calendar = Calendar(ics_content)

    logging.debug(f"calendar fetched.")
  
        # Step 4: Extract events into a structured format
    for event in calendar.events:
        # Extract details about each event
        event_name = event.name
        description = event.description if event.description else 'No Description'
        uid = event.uid if event.uid else 'No UID'

        if "Ottelu" in event_name:
            # Append event data to list
            descriptions.append({
                
                "Tapahtuma": event.name,
                "Lisätiedot": description,  # Assuming description contains level information
                "Uid": uid.split('_')[-1]
            })
    logging.debug(f"found {len(descriptions)} events from calendar.")
    
    if descriptions:
        return descriptions
    else:
        return []
