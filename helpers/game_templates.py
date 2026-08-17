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

# Oletusteksti GameInfoTextBox-kentälle. Eri sisältö kuin ennakkoinfossa: mukana päivä ja
# kellonaika. Kenttä on toistaiseksi oma templaattinsa, koska ei ole varmistettu missä se
# Jopoxin käyttöliittymässä näkyy - jos se osoittautuu turhaksi, sen voi jättää tyhjäksi
# ilman että ennakkoinfoon tarvitsee koskea.
# TODO: logiikka sille tarvitaanko toimitsijoita, huomioiden pienpelit.
DEFAULT_GAME_INFO = """
                Ottelu {date} klo {time}<br>
                {home_team} - {away_team}<br>
                {location}<br>
                <br>
                {pienpeli}<br>
                <br>
                Kokoontuminen tuntia ennen ottelun alkua.<br>
                <br>
                Joukkue:
                <br>
                """


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


def render_game_texts(game, game_data=None, public_info_template=None, game_info_template=None):
    """Palauttaa (ennakkoinfo, game_info) valmiiksi renderöitynä.

    Templaatit ovat valinnaisia, jotta kutsuja voi myöhemmin syöttää käyttäjän omat versiot;
    ilman niitä käytetään oletuksia.
    """
    values = build_placeholders(game, game_data)

    return (
        render_template(
            public_info_template if public_info_template is not None else DEFAULT_PUBLIC_INFO,
            values,
        ),
        render_template(
            game_info_template if game_info_template is not None else DEFAULT_GAME_INFO,
            values,
        ),
    )
