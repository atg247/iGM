"""Yhteiset fixtuurit testeille.

Ympäristömuuttujat asetetaan ennen sovelluksen importtia, koska config.py ja security.py
lukevat ne moduulitasolla. Testit eivät siis koskaan käytä kehityskantaa (instance/) eivätkä
kirjoita kehityslokiin (logs/igm.log), eivätkä ne ota yhteyttä Jopoxiin.
"""

import os
import tempfile

from cryptography.fernet import Fernet

_tmpdir = tempfile.mkdtemp(prefix='igm-tests-')

# Oma kanta testeille, ei instance/hockey_data.db.
os.environ['DATABASE_URL'] = f'sqlite:///{_tmpdir}/test.db'
# security.py vaatii tämän importissa; oma avain, ettei testi riipu kehittäjän .env:stä.
os.environ['FERNET_KEY'] = Fernet.generate_key().decode()
os.environ.setdefault('SECRET_KEY', 'test-secret')
# APP_ENV=production estää logging_configia kirjoittamasta logs/igm.log:iin.
os.environ['APP_ENV'] = 'production'
os.environ.setdefault('LOG_LEVEL', 'WARNING')

import pytest  # noqa: E402

from app import create_app  # noqa: E402
from extensions import db as _db  # noqa: E402
from models.team import Team  # noqa: E402
from models.tgames import TGamesdb  # noqa: E402
from models.user import User  # noqa: E402


@pytest.fixture(scope='session')
def app():
    application = create_app()
    application.config.update(TESTING=True)
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture
def ctx(app):
    """Pyyntökonteksti: JopoxScraper lukee Flask-sessiota jo konstruktorissa."""
    with app.test_request_context():
        yield


@pytest.fixture(autouse=True)
def clean_db(app):
    """Jokainen testi alkaa tyhjästä kannasta."""
    yield
    _db.session.rollback()
    for model in (TGamesdb, User, Team):
        _db.session.query(model).delete()
    _db.session.commit()


@pytest.fixture
def team(app):
    t = Team(team_id='1368626268', team_name='S-Kiekko Musta',
             stat_group='U14 Sininen', season='2026', statgroup='8814')
    _db.session.add(t)
    _db.session.commit()
    return t


@pytest.fixture
def make_game(team):
    """Luo TGamesdb-rivin oletusarvoilla; anna vain se mikä testissä merkitsee."""
    def _make(game_id, jopox_uid=None, team_obj=None, **kwargs):
        from datetime import datetime
        row = TGamesdb(
            game_id=str(game_id),
            team_id=(team_obj or team).id,
            date=kwargs.get('date', '05.09.2026'),
            time=kwargs.get('time', '13:30'),
            home_team=kwargs.get('home_team', 'S-Kiekko Musta'),
            away_team=kwargs.get('away_team', 'JYP'),
            home_goals='0', away_goals='0',
            location=kwargs.get('location', 'Seinäjoki 2'),
            level_name='U14 Sininen', stat_group_name='U14 Sininen',
            small_area_game='0', team_name='S-Kiekko Musta', type='manage',
            sortable_date=kwargs.get('sortable_date', datetime(2026, 9, 5)),
            jopox_uid=jopox_uid,
        )
        _db.session.add(row)
        _db.session.commit()
        return row
    return _make


@pytest.fixture
def user(app):
    u = User(username='testi', email='testi@example.com', password_hash='x',
             jopox_username='testi@example.com')
    _db.session.add(u)
    _db.session.commit()
    return u
