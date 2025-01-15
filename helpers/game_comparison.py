from fuzzywuzzy import fuzz
from datetime import datetime, timedelta
import logging

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
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        filename="gamecomparison.log",
        filemode='w'
    )

    logger = logging.getLogger(__name__)
    
    results = []
    
    managed_games = [managed_game for managed_game in tulospalvelu_games if managed_game['Type'] != 'follow']
    logger.info("Total managed games: %d", len(managed_games))
    logger.info("Total Jopox games: %d", len(jopox_games))
    
    for t_game in managed_games:
        logger.info("Processing Tulospalvelu game: %s", t_game)
        
        try:
            t_game_date = parse_sortable_date(t_game['SortableDate'])
        except ValueError:
            logger.error("Invalid SortableDate format for game: %s", t_game)
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

        logger.info("Extracted details: date=%s, time=%s, location=%s, teams=%s, small_area_game=%s",
                    date, time, location, teams, small_area_game)

        if time == "00:00":
            time = "Not scheduled"

        best_match = None
        best_score = 0
        best_reason = ""
        color_score = 0  # Track discrepancies for color scoring
        warning_reason = None

        for j_game in jopox_games:
            logger.info("Comparing with Jopox game: %s", j_game)

            try:
                j_game_date = datetime.strptime(j_game['Pvm'], '%Y-%m-%d').date()
            except ValueError:
                logger.error("Invalid Jopox date format: %s", j_game['Pvm'])
                continue

            if date != j_game_date.strftime('%Y-%m-%d'):
                logger.info("Dates do not match: Tulospalvelu %s vs Jopox %s", date, j_game_date)
                continue

            # Extract J_Game details
            j_time = j_game['Aika'].split(' - ')[0]
            j_location = j_game['Paikka'].lower()
            j_teams = j_game['Tapahtuma'].split(":")[-1].lower()

            logger.info("Extracted Jopox details: date=%s, time=%s, location=%s, teams=%s",
                        j_game_date, j_time, j_location, j_teams)

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
            logger.info("Time matching: score=%d, reason=%s", score, reason)

            # Location Matching
            location_match_score = fuzz.partial_ratio(location, j_location)
            if location_match_score > 60:
                score += 30
            else:
                reason += f"Ottelu pelataan paikassa: {location}, mutta Jopoxiin on merkattu: {j_location}. "
                color_score_temp += 1
            logger.info("Location matching: score=%d, match_score=%d, reason=%s", score, location_match_score, reason)

            # Team Matching
            team_match_score = fuzz.partial_ratio(teams, j_teams)
            if team_match_score > 60:
                score += 30
            else:
                reason += f"Team mismatch ({teams} vs {j_teams}). "
                color_score_temp += 1
            logger.info("Team matching: score=%d, match_score=%d, reason=%s", score, team_match_score, reason)

            # Small Area Game Check
            if small_area_game:
                if 'Lisätiedot' in j_game and 'pienpeli' not in j_game['Lisätiedot'].lower():
                    reason += "Kyseessä on pienpeli, mutta siitä ei ole mainintaa Jopoxissa. "
                    color_score_temp += 1

            # Update the best match
            if score > best_score:
                logger.info("New best match found: %s with score %d", j_game, score)
                best_score = score
                best_match = j_game
                best_reason = reason
                color_score = color_score_temp
            
            if best_match is None or color_score > 2:
                warning_reason = (
                    "En ole varma löysinkö oikean ottelun."
                    "Tarkista Jopoxista, että päivämäärä, joukkueiden nimet ja alkamisaika vastaavat tulospalvelua. "
                    "Esimerkiksi joukkueiden nimien tai pelipaikan lyhentäminen voi aiheuttaa ongelmia."
                )

        # Determine match status
        if color_score == 0 and best_match:
            match_status = 'green'
            jopox_games.remove(best_match)
            best_reason = "Ottelu löytyy Jopoxista. Ei huomioita."
            
        elif color_score > 0 and best_match:
            match_status = 'yellow'
        else:
            match_status = 'red'
            best_reason = "En löytänyt ottelua Jopoxista."

        logger.info("Final match status: %s, reason: %s", match_status, best_reason)

        results.append({
            'game': t_game,
            'match_status': match_status,
            'reason': best_reason.strip(),
            'warning': warning_reason.strip() if warning_reason else None,
            'best_match': best_match,
        })

    logger.info("Comparison completed. Total results: %d", len(results))
    return results
