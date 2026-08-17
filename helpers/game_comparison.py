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


def find_linked_game(jopox_games, jopox_links, t_game):
    """Etsii ottelulle luontivaiheessa tallennetun Jopox-parin jopox_uid:n perusteella.

    Palauttaa None jos linkkiä ei ole tai linkitettyä tapahtumaa ei enää löydy Jopoxista
    (esim. se on poistettu siellä käsin) - tällöin kutsuja putoaa fuzzy-täsmäytykseen.
    """
    if not jopox_links:
        return None

    # Avain merkkijonoksi: Tulospalvelu antaa Game ID:n numerona, kanta merkkijonona.
    game_id = t_game.get('Game ID')
    uid = jopox_links.get(str(game_id)) if game_id is not None else None
    if not uid:
        return None

    for j_game in jopox_games:
        if (j_game or {}).get('uid') == uid:
            return j_game

    logger.info(
        "Game ID %s on linkitetty jopox_uid:hen %s, mutta sitä ei löytynyt Jopoxista - "
        "käytetään fuzzy-täsmäytystä", t_game.get('Game ID'), uid
    )
    return None


def score_candidate(t_fields, j_game):
    """Pisteyttää yhden Jopox-ottelun Tulospalvelu-ottelua vasten.

    Palauttaa (score, reason, color_score) tai None jos ottelua ei voi arvioida
    (kelvoton päivämäärä/aika tai ottelu on jo pelattu). color_score kertoo
    löydettyjen poikkeamien määrän ja ratkaisee vihreä/keltainen-tilan.
    """
    date = t_fields['date']
    t_time = t_fields['time']
    location = t_fields['location']
    small_area_game = t_fields['small_area_game']
    home_team = t_fields['home_team']
    away_team = t_fields['away_team']

    try:
        # Parse the sortable_date field from Jopox game
        j_game_datetime = datetime.strptime(j_game['sortable_date'], '%Y-%m-%d %H:%M')
    except ValueError:
        logger.error("Invalid sortable_date format: %s", j_game['sortable_date'])
        return None

    # Skip games that have already been played before yesterday
    if j_game_datetime < datetime.now() - timedelta(days=1):
        return None

    # Extract J_Game details
    j_time = j_game['aika']
    j_location = j_game['paikka'].lower()
    j_team_home = j_game['joukkueet'].split(' - ')[0].lower()
    j_team_away = j_game['joukkueet'].split(' - ')[1].lower()

    # Convert times
    try:
        t_game_time = datetime.strptime(t_time, '%H:%M') if t_time != "Not scheduled" else None
        j_game_time = datetime.strptime(j_time, '%H:%M')
    except ValueError:
        logger.error("Invalid time format: Tulospalvelu %s vs Jopox %s", t_time, j_time)
        return None

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
    if t_time == "Not scheduled" and (j_time == "07:00" or j_time == "00:00"):
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
        reason += f"Ottelun oikea alkamisaika on klo: {t_time}, mutta Jopoxissa se on klo {j_time}. "
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

    return score, reason, color_score_temp


def compare_games(jopox_games, tulospalvelu_games, jopox_links=None):
    """Compare games from Jopox and Tulospalvelu.fi datasets.

    jopox_links on valinnainen {game_id: jopox_uid} -kartta luontivaiheessa tallennetuista
    pareista. Linkitetyt ottelut tunnistetaan suoraan uid:n perusteella, jolloin paria ei
    tarvitse arvata uudelleen - fuzzy-täsmäytys jää vain linkittämättömille otteluille.
    """
    # Initialize logging

    results = []

    managed_games = [managed_game for managed_game in tulospalvelu_games if managed_game['Type'] != 'follow']
    logger.info('Comparing games from Tulospalvelu and Jopox')
    logger.info("Total managed games: %d", len(managed_games))
    logger.info("Total Jopox games: %d", len(jopox_games))
    logger.info("Known jopox_uid links: %d", len(jopox_links or {}))

    # Esikäsittely: päivämäärän jäsennys ja kelpoisuus kerran per ottelu, jotta linkit
    # voidaan varata ennen fuzzy-kierrosta ilman että logiikka on kahdessa paikassa.
    entries = []
    for t_game in managed_games:
        try:
            t_game_datetime = parse_sortable_date(t_game['SortableDate'])
        except ValueError:
            logger.error("Invalid SortableDate format for game: %s", t_game)
            entries.append({'t_game': t_game, 'state': 'invalid_date'})
            continue

        # Skip games that have already been played before yesterday
        if t_game_datetime < datetime.now() - timedelta(days=1):
            entries.append({'t_game': t_game, 'state': 'past'})
            continue

        # Defensive: Tulospalvelu's raw time is "HH:MM:SS"; strptime below expects "HH:MM".
        time = (t_game['Time'] or '')[:5]
        if time in ("07:00", "00:00"):
            time = "Not scheduled"

        entries.append({
            't_game': t_game,
            'state': 'ok',
            't_fields': {
                'date': t_game_datetime.strftime('%Y-%m-%d'),
                'time': time,
                'location': t_game['Location'].lower(),
                'small_area_game': t_game['Small Area Game'] == '1',
                'home_team': t_game['Home Team'].lower(),
                'away_team': t_game['Away Team'].lower(),
            },
        })

    # Ensimmäinen kierros: varataan linkitetyt parit pois yhteisestä joukosta. Tämä on tehtävä
    # ennen fuzzyä, koska muuten aiempi linkittämätön ottelu voi napata juuri sen Jopox-rivin,
    # joka kuuluu myöhemmälle linkitetylle ottelulle - ja linkin koko idea on, ettei paria
    # tarvitse enää kilpailuttaa.
    linked_hits = 0
    for entry in entries:
        if entry['state'] != 'ok':
            continue

        linked_match = find_linked_game(jopox_games, jopox_links, entry['t_game'])
        scored_link = score_candidate(entry['t_fields'], linked_match) if linked_match else None
        if scored_link is None:
            continue

        entry['claim'] = (linked_match, scored_link)
        jopox_games.remove(linked_match)
        linked_hits += 1
        logger.debug(
            "Game ID %s täsmätty linkillä jopox_uid %s (color_score=%d)",
            entry['t_game'].get('Game ID'), linked_match.get('uid'), scored_link[2]
        )

    # Toinen kierros: fuzzy-täsmäytys lopuille. Kaikki ottelu-Jopox-parit pisteytetään ensin,
    # ja vasta sitten jaetaan parhaasta alkaen. Aiemmin jokainen ottelu nappasi parhaan vapaan
    # rivin omalla vuorollaan, jolloin listalla aiempi ottelu saattoi viedä rivin 30 pisteellä
    # vaikka myöhemmällä ottelulla olisi ollut siihen 150 pisteen osuma.
    candidates = []
    for idx, entry in enumerate(entries):
        if entry['state'] != 'ok' or 'claim' in entry:
            continue
        for j_game in jopox_games:
            scored = score_candidate(entry['t_fields'], j_game)
            if scored is None:
                continue
            score, reason, color_score = scored
            candidates.append((score, idx, j_game, reason, color_score))

    # Paras ensin. idx tasapelin ratkaisijana, jotta tulos on toistettava.
    candidates.sort(key=lambda c: (-c[0], c[1]))

    taken_entries = set()
    taken_uids = set()
    for score, idx, j_game, reason, color_score in candidates:
        if idx in taken_entries or id(j_game) in taken_uids:
            continue
        entries[idx]['match'] = (j_game, score, reason, color_score)
        taken_entries.add(idx)
        taken_uids.add(id(j_game))

    # Kolmas kierros: tulokset alkuperäisessä järjestyksessä.
    for entry in entries:
        t_game = entry['t_game']

        if entry['state'] == 'invalid_date':
            results.append({
                'game': t_game,
                'match_status': 'red',
                'reason': f"Invalid date format: {t_game['SortableDate']}",
                'best_match': None,
            })
            continue

        if entry['state'] == 'past':
            continue

        # Linkitetty pari on varattu ensimmäisellä kierroksella. Sisältö on pisteytetty
        # normaalisti, jotta päivämäärä-, aika- ja paikkapoikkeamat raportoidaan kuten ennen -
        # vain parin arvaaminen jää pois, eikä epävarmuusvaroitusta tarvita.
        claim = entry.get('claim')
        if claim is not None:
            best_match, (best_score, best_reason, color_score) = claim
            warning_reason = None
        elif 'match' in entry:
            best_match, best_score, best_reason, color_score = entry['match']
            warning_reason = None if best_score >= 105 else (
                "En ole varma löysinkö oikean ottelun."
                "Tarkista Jopoxista, että päivämäärä, joukkueiden nimet ja alkamisaika vastaavat tulospalvelua. "
                "Esimerkiksi joukkueiden nimien tai pelipaikan lyhentäminen voi aiheuttaa ongelmia. "
                "Jos ottelun alkamisaikaa ei ole merkitty, käytä Jopoxissa oletusaikaa 07:00. "
                "Löydän parhaiten ottelun jos Jopoxissa on merkitty alkamisajaksi todellinen ottelun alkamisaika."
            )
        else:
            results.append({
                'game': t_game,
                'match_status': 'red',
                'reason': "En löytänyt ottelua Jopoxista.",
                'warning': None,
                'best_match': None,
            })
            continue

        if color_score == 0:
            match_status = 'green'
            best_reason = "Ottelu löytyy Jopoxista. Ei huomioita."
        else:
            match_status = 'yellow'

        results.append({
            'game': t_game,
            'match_status': match_status,
            'reason': best_reason.strip(),
            'warning': warning_reason.strip() if warning_reason else None,
            'best_match': best_match,
        })

    logger.info("Matched via stored jopox_uid link: %d/%d", linked_hits, len(managed_games))

    return results
