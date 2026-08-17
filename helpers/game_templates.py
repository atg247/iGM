"""Jopoxiin kirjoitettavien vapaiden tekstikenttien rakentaminen.

Tekstit rakennettiin aiemmin f-stringeinä suoraan JopoxScraper.add_game():n payload-dictissä,
jolloin kutsuja ei voinut vaikuttaa niihin lainkaan. Sisältöpäätökset asuvat nyt täällä ja
scraper vain postittaa sen mitä sille annetaan.

Templaatit ovat tavallisia merkkijonoja, joissa on {placeholder}-kenttiä. Ne on tarkoitettu
myöhemmin käyttäjän itsensä muokattaviksi, joten renderöinti ei saa kaatua siihen että
templaatissa on tuntematon tai kirjoitusvirheellinen placeholder.
"""

from collections import defaultdict

from logging_config import logger

# Käytettävissä olevat placeholderit. Tämä lista on myös se, joka näytetään käyttäjälle
# asetusnäkymässä, joten pidä se ajan tasalla build_placeholders():n kanssa.
PLACEHOLDERS = (
    'home_team',
    'away_team',
    'location',
    'date',
    'time',
    'pienpeli',
    'team_name',
    'level',
)

# Oletusteksti näkyvälle ennakkoinfolle (GamePublicInfoTextBox). Sisennykset ja tyhjät rivit
# ovat tarkoituksellisia: teksti menee Jopoxiin sellaisenaan ja tämä vastaa sitä mitä
# sovellus on tähän asti kirjoittanut.
# TODO: logiikka sille tarvitaanko toimitsijoita, huomioiden pienpelit.
DEFAULT_PUBLIC_INFO = """
                {home_team} - {away_team}<br>
                {pienpeli}<br>
                <br>
                {location}<br>
                <br>
                <br>
                Kokoontuminen tuntia ennen ottelun alkua.<br>
                <br>
                Joukkue:
                <br>
                """

# GameInfoTextBox jätetään tarkoituksella tyhjäksi.
#
# Kenttä on Jopoxin vanha viestitoiminto: sen label on "Viesti (näkyy tapahtuman
# osallistujille Jopox pukukopissa ilmoituksena sekä Jopox+ sovelluksessa notifikaationa)".
# Jopox on kuitenkin poistanut sen käyttöliittymästä - textarea on kahden sisäkkäisen
# display:none -paneelin (NotificationPanel, GameNotificationPanel) sisällä, eikä
# ottelulomakkeella näy kuin Ennakkoinfo. Siksi kenttään aiemmin kirjoitettu teksti ei ole
# näkynyt eikä lähettänyt ilmoituksia kenellekään.
#
# Lähetetään silti tyhjänä mukana, koska selainkin postittaa piilotetun kentän ja poisjättö
# voisi kaataa ASP.NET-postbackin. Älä täytä tätä: näkyvä teksti kuuluu ennakkoinfoon.
GAME_INFO_MESSAGE = ''


def build_placeholders(game, game_data=None):
    """Kokoaa placeholder-arvot Tulospalvelu-ottelusta ja luontilomakkeen datasta.

    Päivä ja kellonaika luetaan game_data:sta, koska ne on siellä jo muotoiltu samaan asuun
    kuin mitä Jopoxin lomakkeelle lähetetään. Muut kentät tulevat suoraan ottelusta.
    """
    game = game or {}
    game_data = game_data or {}

    return {
        'home_team': game.get('Home Team', ''),
        'away_team': game.get('Away Team', ''),
        'location': game.get('Location', ''),
        'date': game_data.get('GameDateTextBox', '') or game.get('Date', ''),
        'time': game_data.get('GameStartTimeTextBox', '') or game.get('Time', ''),
        'pienpeli': 'Pienpeli' if game.get('Small Area Game') == '1' else 'Ison kentän peli',
        'team_name': game.get('Team Name', ''),
        'level': game.get('Level Name', ''),
    }


def render_template(template, values):
    """Täyttää templaatin placeholderit. Tuntematon placeholder korvautuu tyhjällä.

    defaultdict siksi, ettei käyttäjän kirjoitusvirhe templaatissa kaada ottelun luontia -
    yksi tyhjä kohta tekstissä on parempi kuin epäonnistunut luonti. Muotoiluvirhe (esim.
    pariton aaltosulje) ei ole korjattavissa oletuksella, joten silloin palautetaan templaatti
    sellaisenaan ja asia lokitetaan.
    """
    if not template:
        return ''

    try:
        return template.format_map(defaultdict(str, values))
    except (ValueError, IndexError) as e:
        logger.error(
            "render_template(): virheellinen templaatti (%s) - lähetetään sellaisenaan", e
        )
        return template


def render_public_info(game, game_data=None, template=None):
    """Renderöi ottelun ennakkoinfon (GamePublicInfoTextBox).

    Templaatti on valinnainen, jotta kutsuja voi myöhemmin syöttää käyttäjän oman version;
    ilman sitä käytetään oletusta.

    Huom: viestikentälle (GameInfoTextBox) ei ole vastaavaa funktiota tarkoituksella - ks.
    GAME_INFO_MESSAGE.
    """
    values = build_placeholders(game, game_data)

    return render_template(
        template if template is not None else DEFAULT_PUBLIC_INFO,
        values,
    )
