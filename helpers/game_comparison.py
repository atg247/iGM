from fuzzywuzzy import fuzz
from datetime import datetime, timedelta

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
        try:
            t_game_date = parse_sortable_date(t_game['SortableDate'])
        except ValueError:
            results.append({
                'game': t_game,
                'match_status': 'red',
                'reason': f"Invalid date format: {t_game['SortableDate']}",
                'best_match': None,
            })
            continue

        # Extract T_Game details
        date = t_game_date.strftime('%Y-%m-%d')
        time = t_game['Time']
        location = t_game['Location'].lower()
        small_area_game = t_game['Small Area Game'] == '1'
        teams = f"{t_game['Home Team']} - {t_game['Away Team']}".lower()

        #print T-game details in different rows
        print("-------\nTULOSPALVELU:", date,"\n", time,"\n", location,"\n", teams,"\n", small_area_game)

        if time == "00:00":
            time = "Not scheduled"

        best_match = None
        best_score = 0
        best_reason = ""
        color_score = 0  # Track discrepancies for color scoring

        #print("T_Game:", date, time, location, teams, small_area_game)

        for j_game in jopox_games:
            try:
                j_game_date = datetime.strptime(j_game['Pvm'], '%Y-%m-%d').date()
            except ValueError:
                continue

            if date != j_game_date.strftime('%Y-%m-%d'):
                continue

            # Extract J_Game details
            j_time = j_game['Aika'].split(' - ')[0]
            j_location = j_game['Paikka'].lower()
            j_teams = j_game['Tapahtuma'].split(":")[-1].lower()

            print("-------\nJopox:", "\n",j_game_date, "\n", j_time, "\n", j_location, "\n", j_teams)

            # Convert times
            try:
                t_game_time = datetime.strptime(time, '%H:%M') if time != "Not scheduled" else None
                j_game_time = datetime.strptime(j_time, '%H:%M')
            except ValueError:
                continue

            # Temporary scoring for this Jopox game
            score = 0
            color_score_temp = 0
            reason = ""

            # Time Matching
            if time == "Not scheduled" and j_time == "07:00":
                score += 30
                reason += "Ottelun alkamisaika ei ole määritetty Tulospalvelussa. Jopox-aika vastaa oletusta (07:00). "
                color_score_temp += 1
            elif t_game_time and t_game_time.time() == j_game_time.time():  # Exact match
                score += 50

            elif t_game_time and (t_game_time - timedelta(hours=1)).time() == j_game_time.time():  # Arrival time
                score += 30
                reason += "Jopoxiin merkitty alkamisaika on tuntia aikaisemmin kuin Tulospalvelussa. "
                color_score_temp += 1
            else:
                reason += f"Ottelun oikea alkamisaika on klo: {time}, mutta Jopoxissa se on klo {j_time}. "
                color_score_temp += 1

            # Location Matching
            location_match_score = fuzz.partial_ratio(location, j_location)
            if location_match_score > 60:
                score += 30
            else:
                reason += f"Ottelu pelataan paikassa: {location}, mutta Jopoxiin on merkattu: {j_location}. "
                color_score_temp += 1

            # Team Matching
            team_match_score = fuzz.partial_ratio(teams, j_teams)
            if team_match_score > 60:
                score += 30
            else:
                reason += f"Team mismatch ({teams} vs {j_teams}). "
                color_score_temp += 1

            # Small Area Game Check
            if small_area_game:
                if 'Lisätiedot' in j_game and 'pienpeli' not in j_game['Lisätiedot'].lower():
                    reason += "Kyseessä on pienpeli, mutta siitä ei ole mainintaa Jopoxissa. "
                    color_score_temp += 1

            #print(f"Temporary Color Score for {t_game['Game ID']}: {color_score_temp}")
            #print(f"Reason for {t_game['Game ID']}: {reason}")

            # Update the best match
            if score > best_score:
                best_score = score
                best_match = j_game
                best_reason = reason
                color_score = color_score_temp  # Update main color_score with temp

        print("Best Match:", best_match, best_score)

        # Determine match status
        if color_score == 0 and best_match:
            match_status = 'green'
            jopox_games.remove(best_match)
        elif color_score > 0 and best_match:
            match_status = 'yellow'
        else:
            match_status = 'red'
            best_reason = "Game not found in Jopox."

        results.append({
            'game': t_game,
            'match_status': match_status,
            'reason': best_reason.strip(),
            'best_match': best_match,
        })

    return results
