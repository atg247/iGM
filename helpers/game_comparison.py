import re

from fuzzywuzzy import fuzz
from datetime import datetime, timedelta

from logging_config import logger

def parse_sortable_date(date_string):
    """Parse SortableDate string into a date object."""
    try:
        # Remove GMT and parse only the date part
        clean_date = date_string.replace(' GMT', '')  # Remove 'GMT'
        parsed_datetime = datetime.strptime(clean_date, '%a, %d %b %Y %H:%M:%S')  # Correct format
        return parsed_datetime  # Return the complete datetime object
    except ValueError as e:
        raise ValueError(f"Error parsing SortableDate: {date_string}") from e


def compare_games(jopox_games, tulospalvelu_games):
    """Compare games from Jopox and Tulospalvelu.fi datasets."""
    # Initialize logging
        
    results = []

    managed_games = [managed_game for managed_game in tulospalvelu_games if managed_game['Type'] != 'follow']
    logger.info('Comparing games from Tulospalvelu and Jopox')
    logger.info("Total managed games: %d", len(managed_games))
    logger.info("Total Jopox games: %d", len(jopox_games))

    for t_game in managed_games:    
        
        # Parse date from Tulospalvelu game
        try:
            t_game_datetime = parse_sortable_date(t_game['SortableDate'])
        except ValueError:
            logger.error("Invalid SortableDate format for game: %s", t_game)
            results.append({
                'game': t_game,
                'match_status': 'red',
                'reason': f"Invalid date format: {t_game['SortableDate']}",
                'best_match': None,
            })
            continue

        # Extract t_Game details
        date = t_game_datetime.strftime('%Y-%m-%d')

        # Skip games that have already been played before yesterday
        if t_game_datetime < datetime.now() - timedelta(days=1):
            continue

        time = t_game['Time']
        location = t_game['Location'].lower()
        small_area_game = t_game['Small Area Game'] == '1'
        home_team = t_game['Home Team'].lower() 
        away_team = t_game['Away Team'].lower()

        if time == "00:00":
            time = "Not scheduled"

        best_match = None
        best_matches = []
        best_score = 0
        best_reason = ""
        color_score = 0  # Track discrepancies for color scoring
        warning_reason = ""

        for j_game in jopox_games:
            try:
                # Parse the sortable_date field from Jopox game
                j_game_datetime = datetime.strptime(j_game['sortable_date'], '%Y-%m-%d %H:%M')
            except ValueError:
                logger.error("Invalid sortable_date format: %s", j_game['sortable_date'])
                continue

            # Skip games that have already been played before yesterday
            if j_game_datetime < datetime.now() - timedelta(days=1):
                continue

            
            # Extract J_Game details
            j_time = j_game['aika']
            j_location = j_game['paikka'].lower()
            j_team_home = j_game['joukkueet'].split(' - ')[0].lower()
            j_team_away = j_game['joukkueet'].split(' - ')[1].lower()
            
            # Convert times
            try:
                t_game_time = datetime.strptime(time, '%H:%M') if time != "Not scheduled" else None
                j_game_time = datetime.strptime(j_time, '%H:%M')
            except ValueError:
                logger.error("Invalid time format: Tulospalvelu %s vs Jopox %s", time, j_time)
                continue
            

            # Temporary scoring for this Jopox game
            score = 0
            color_score_temp = 0
            reason = ""

            # Date Matching
            if date == j_game_datetime.strftime('%Y-%m-%d'):
                score += 30
            else:
                reason += f"Ottelun päivämäärä on {date}, mutta Jopoxissa se on {j_game_datetime.strftime('%Y-%m-%d')}. "
                color_score_temp += 1

            # Time Matching
            if time == "Not scheduled" and (j_time == "07:00" or j_time == "00:00"):
                score += 30 
                reason += "Ottelun alkamisaika ei ole määritetty Tulospalvelussa. Jopox-aika vastaa oletusta (07:00). "
                color_score_temp += 1

            elif time == "07:00" and j_time == "07:00":
                score += 30
                reason += "Ottelun alkamisaika Tulospalvelussa on 07:00. Jopox-aika vastaa oletusta (07:00). "
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
            if location_match_score > 80:
                score += 30
                
                # find number from string location
                t_location_number = re.findall(r'\d+', location)                
                j_location_number = re.findall(r'\d+', j_location)

                if t_location_number and j_location_number and t_location_number[0] != j_location_number[0]:
                    score -= 15
                    color_score_temp += 1
                    reason += f"Ottelu pelataan paikassa: {location}, mutta Jopoxiin on merkattu: {j_location}. "
                # if t_location has no number and j_location has any number then score -20
                elif not t_location_number and j_location_number:
                    score -= 15
                    color_score_temp += 1                    
                    reason += f"Ottelu pelataan paikassa: {location}, mutta Jopoxiin on merkattu: {j_location}. "
                
            else:
                reason += f"Ottelu pelataan paikassa: {location}, mutta Jopoxiin on merkattu: {j_location}. "
                color_score_temp += 1


            home_team_match_score = fuzz.ratio(j_team_home, home_team)
            if home_team_match_score > 90:
                score += 15
            else:
                reason += f"Kotijoukkueen pitäisi olla {home_team}"
                color_score_temp += 1

            away_team_match_score = fuzz.ratio(j_team_away, away_team)
            if away_team_match_score > 90:
                score += 15

            else:
                reason += f"Vierasjoukkueen pitäisi olla {away_team}"
                color_score_temp += 1

            team_score = home_team_match_score + away_team_match_score 
            if team_score >= 180:
                score += 10

            if 'Lisätiedot' in j_game and j_game['Lisätiedot']:

                if small_area_game:
                    if 'pienpeli' not in j_game['Lisätiedot'].lower() and 'pienpeli' not in j_game['joukkueet'].lower():
                        reason += "Kyseessä on pienpeli, mutta siitä ei ole mainintaa Jopoxissa. "
                        color_score_temp += 1
                    elif 'pienpeli' in j_game['Lisätiedot'].lower() or 'pienpeli' in j_game['joukkueet'].lower():
                        score += 20

                if not small_area_game:
                    if 'Lisätiedot' in j_game and j_game['Lisätiedot']:
                        if 'pienpeli' in j_game['Lisätiedot'].lower() or 'pienpeli' in j_game['joukkueet'].lower() and team_score >= 180:
                            reason+="Kyseessä ei ole pienpeli, vaikka Jopoxissa se on mainittu."
                            score -=20
                        if 'pienpeli' in j_game['Lisätiedot'].lower() or 'pienpeli' in j_game['joukkueet'].lower() and team_score <= 180:
                            reason+="Kyseessä ei ole pienpeli, vaikka Jopoxissa se on mainittu."
                            score -=10

            # Update the best match
            if score > best_score:
                best_score = score
                best_match = j_game
                best_reason = reason
                color_score = color_score_temp

            
                if best_match is None or best_score < 105 :
                    warning_reason = (
                        "En ole varma löysinkö oikean ottelun."
                        "Tarkista Jopoxista, että päivämäärä, joukkueiden nimet ja alkamisaika vastaavat tulospalvelua. "
                        "Esimerkiksi joukkueiden nimien tai pelipaikan lyhentäminen voi aiheuttaa ongelmia. "
                        "Jos ottelun alkamisaikaa ei ole merkitty, käytä Jopoxissa oletusaikaa 07:00. "
                        "Löydän parhaiten ottelun jos Jopoxissa on merkitty alkamisajaksi todellinen ottelun alkamisaika."

                    )

                elif best_match and best_score > 1:
                    warning_reason = None

                best_matches.append({'match': best_match, 'score': best_score, 'reason': reason, 'color_score': color_score, 'warning': warning_reason})
                

        #pick the best match from best_matches and append it to results with color_score, reason and warning_reason
                
        if best_matches:
            best_match = max(best_matches, key=lambda x: x['score'])['match']
            best_score = max(best_matches, key=lambda x: x['score'])['score']
            best_reason = max(best_matches, key=lambda x: x['score'])['reason']
            color_score = max(best_matches, key=lambda x: x['score'])['color_score']
            warning_reason = max(best_matches, key=lambda x: x['score'])['warning']

            # Determine match status
            if color_score == 0 and best_match:
                match_status = 'green'
                best_reason = "Ottelu löytyy Jopoxista. Ei huomioita."
                jopox_games.remove(best_match)
                
            elif color_score > 0 and best_match:
                match_status = 'yellow'
                jopox_games.remove(best_match)
        else:
            match_status = 'red'
            best_reason = "En löytänyt ottelua Jopoxista."


        results.append({
            'game': t_game,
            'match_status': match_status,
            'reason': best_reason.strip(),
            'warning': warning_reason.strip() if warning_reason else None,
            'best_match': best_match,
        })

    return results
