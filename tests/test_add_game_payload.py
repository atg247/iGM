"""Jopoxiin lähetettävän lomakepayloadin sisältö.

Jopoxilla ei ole APIa eikä testiympäristöä, joten oikea POST korvataan valepäätteellä ja
tarkastetaan mitä olisi lähetetty. Tämä on ainoa tapa saada kiinni kentän sisältövirhe ennen
kuin se on jo tallennettu seuran oikeaan kalenteriin - näin jäi aiemmin huomaamatta kenttä,
jonka arvona luki "None".
"""

import pytest

from helpers.game_templates import GAME_INFO_MESSAGE, render_public_info

PREFIX = 'ctl00$MainContentPlaceHolder$GamesBasicForm$'


class FakeResponse:
    status_code = 200
    text = '<html><body>ok</body></html>'
    url = 'https://hallinta3.jopox.fi/Admin/Hockeypox2020/Games/PrePuff.aspx?gid=999999'


class FakeSession:
    """Nappaa POSTin lähettämättä mitään. Jokainen GET palauttaa saman tyhjän sivun."""

    def __init__(self):
        self.posted = []

    def get(self, url, **kwargs):
        return FakeResponse()

    def post(self, url, data=None, headers=None, **kwargs):
        self.posted.append(data)
        return FakeResponse()


@pytest.fixture
def scraper(ctx, user):
    from helpers.jopox_scraper import JopoxScraper

    s = JopoxScraper(user.id, user.jopox_username, 'salasana')
    s.session = FakeSession()
    s.base_url = 'https://hallinta3.jopox.fi/Admin/Hockeypox2020/'
    s.get_event_validation = lambda r: {
        '__VIEWSTATE': 'v', '__VIEWSTATEGENERATOR': 'g', '__EVENTVALIDATION': 'e'}
    s.get_season_id = lambda r: '606'
    s.get_subsite_id = lambda r: '9702'
    s.homeTeamTextBox = lambda r, team_name: 'Musta'
    s.scrape_jopox_games = lambda: []
    s.ggroup_payload = lambda groups: {}
    return s


def tulospalvelu_game(**kwargs):
    game = {
        'Game ID': '2711751',
        'Team Name': 'S-Kiekko Musta',
        'Home Team': 'S-Kiekko Musta',
        'Away Team': 'JYP Musta',
        'Location': 'Seinäjoki 2',
        'Date': '05.09.2026',
        'Time': '13:30',
        'Small Area Game': '0',
        'LeagueDropdownList': '17324',
    }
    game.update(kwargs)
    return game


def game_data_for(game):
    """Sama muoto kuin routes/api/create_jopox.py rakentaa."""
    return {
        'LeagueDropdownList': game['LeagueDropdownList'],
        'EventDropDownList': '',
        'HomeTeamTextBox': game['Team Name'],
        'GuestTeamTextBox': game['Away Team'],
        'AwayCheckbox': '',
        'GameLocationTextBox': game['Location'],
        'GameDateTextBox': game['Date'],
        'GameStartTimeTextBox': game['Time'],
        'GameDurationTextBox': '120',
        'GameMaxParticipatesTextBox': '',
        'FeedGameDropdown': '0',
        'GameNotificationTextBox': '',
        'SaveGameButton': 'Tallenna',
        'GamePublicInfoTextBox': render_public_info(game, {
            'GameDateTextBox': game['Date'], 'GameStartTimeTextBox': game['Time']}),
        'GameInfoTextBox': GAME_INFO_MESSAGE,
    }


def create(scraper, game):
    scraper.add_game([{'game': game, 'game_data': game_data_for(game)}])
    return scraper.session.posted[-1]


def test_public_info_contains_the_real_game_details(scraper):
    payload = create(scraper, tulospalvelu_game())
    info = payload[PREFIX + 'GamePublicInfoTextBox']

    assert 'S-Kiekko Musta - JYP Musta' in info
    assert 'Seinäjoki 2' in info
    assert 'Ison kentän peli' in info


def test_pienpeli_is_marked_in_the_public_info(scraper):
    payload = create(scraper, tulospalvelu_game(**{'Small Area Game': '1'}))
    assert 'Pienpeli' in payload[PREFIX + 'GamePublicInfoTextBox']


def test_no_field_contains_the_string_None(scraper):
    """Regressio: kentät rakennettiin avaimista, joita kukaan ei asettanut."""
    payload = create(scraper, tulospalvelu_game())
    offenders = [k for k, v in payload.items() if isinstance(v, str) and 'None' in v]
    assert offenders == []


def test_message_field_is_left_empty(scraper):
    """Jopoxin vanha viestikenttä on piilotettu käyttöliittymästä - ei kirjoiteta siihen."""
    payload = create(scraper, tulospalvelu_game())
    assert payload[PREFIX + 'GameInfoTextBox'] == ''


def test_date_time_and_location_are_passed_through(scraper):
    payload = create(scraper, tulospalvelu_game())
    assert payload[PREFIX + 'GameDateTextBox'] == '05.09.2026'
    assert payload[PREFIX + 'GameStartTimeTextBox'] == '13:30'
    assert payload[PREFIX + 'GameLocationTextBox'] == 'Seinäjoki 2'


def test_uid_is_read_from_the_redirect_url(scraper):
    game = tulospalvelu_game()
    results, _ = scraper.add_game([{'game': game, 'game_data': game_data_for(game)}])
    assert results[0]['jopox_uid'] == '999999'
    assert results[0]['status'] == 'ok'
