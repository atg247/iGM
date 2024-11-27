from fuzzywuzzy import fuzz
from datetime import datetime

import re

def parse_sortable_date(date_string):
    """Parse SortableDate string into a date object."""
    try:
        # Remove GMT and parse only the date part
        clean_date = date_string.replace(' GMT', '')
        parsed_datetime = datetime.strptime(clean_date, '%a, %d %b %Y %H:%M:%S')
        return parsed_datetime.date()  # Return only the date part
    except ValueError as e:
        raise ValueError(f"Error parsing SortableDate: {date_string}") from e


def compare_games(jopox_games, tulospalvelu_games):
    """Compare games from Jopox and Tulospalvelu.fi datasets."""
    results = []

    for t_game in tulospalvelu_games:
        # Parse SortableDate into a date object
        try:
            t_game_date = parse_sortable_date(t_game['SortableDate'])

        except ValueError as e:
            results.append({
                'game': t_game,
                'match_status': 'red',
                'reason': f"Invalid date format: {t_game['SortableDate']}"
            })
            continue

        # Format date for comparison
        date = t_game_date.strftime('%Y-%m-%d')
        time = t_game['Time']
        location = t_game['Location'].split()[0].lower()  # Only use the town name
        small_area_game = t_game['Small Area Game'] == '1'
        teams = f"{t_game['Home Team']} - {t_game['Away Team']}".lower()

        match_status = None
        reason = ""
        print("t_game:", date, time, location, small_area_game, teams)
       
       
        for j_game in jopox_games:
            # Parse Jopox 'Pvm' into a date object
            try:
                j_game_date = datetime.strptime(j_game['Pvm'], '%Y-%m-%d').date()
            except ValueError as e:
                reason = f"Invalid date format in Jopox data: {j_game['Pvm']}"
                match_status = 'red'
                break

            if date != j_game_date.strftime('%Y-%m-%d'):
                continue  # Dates must match
            j_time = j_game['Aika'].split(' - ')[0] #
            j_location = j_game['Paikka'].split()[0].lower()
            j_teams = j_game['Tapahtuma'].split()[0].lower()
            print("J_game:", j_game_date, j_time, j_location, j_teams)
            # Check match conditions
            time_match = time == j_time
            location_match = location in j_location
            team_match = fuzz.partial_ratio(teams, j_teams) > 80  # Fuzzy match for team names

            # Handle small area game
            if small_area_game and 'pienpeli' not in j_game['Lisätiedot'].lower():
                match_status = 'yellow'
                reason = "Kyseessä on pienpeli, mutta siitä ei ole mainintaa Jopoxissa."
                continue

            # Determine match level
            if time_match and location_match and team_match:
                match_status = 'green'
                break
            else:
                if not time_match:
                    reason += f"Ottelun oikea alkamisaika on klo: {time}, mutta Jopoxissa se on klo {j_time}). "
                if not location_match:
                    reason += f"Ottelu pelataan paikassa: {location}, mutta Jopoxiin on merkattu: {j_location}). "
                if not team_match:
                    reason += f"Team mismatch ({teams} vs {j_teams}). "
                match_status = 'yellow'

        if not match_status:
            match_status = 'red'
            reason = "Game not found in Jopox."

        results.append({
            'game': t_game,
            'match_status': match_status,
            'reason': reason,
        })

    return results