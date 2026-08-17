"""set_link():n haarat.

Linkin korvaaminen on se kohta, jossa virhe jää pysyväksi: väärä uid ei korjaannu itsestään,
koska vertailu luottaa linkkiin arvauksen sijaan. Siksi jokainen haara testataan erikseen.
"""

from helpers.jopox_links import (
    CONFLICT, KEPT_EXISTING, LINKED, NOT_FOUND, UNCHANGED, set_link)


def test_unlinked_game_gets_the_link(make_game):
    row = make_game('2711751')
    assert set_link(row.game_id, '229648').status == LINKED
    assert row.jopox_uid == '229648'


def test_same_uid_again_is_a_no_op(make_game):
    row = make_game('2711751', jopox_uid='229648')
    assert set_link(row.game_id, '229648').status == UNCHANGED


def test_numeric_game_id_matches_the_string_column(make_game):
    """Tulospalvelu antaa Game ID:n numerona; SQLite sietäisi sen, Postgres ei."""
    row = make_game('2711751')
    assert set_link(int(row.game_id), '229648').status == LINKED
    assert row.jopox_uid == '229648'


def test_existing_link_is_kept_without_a_snapshot(make_game):
    """Ilman tilannekuvaa ei voi tietää onko vanha tapahtuma yhä olemassa - ei kosketa."""
    row = make_game('2711751', jopox_uid='229648')
    assert set_link(row.game_id, '229999').status == KEPT_EXISTING
    assert row.jopox_uid == '229648'


def test_existing_link_is_kept_when_still_in_jopox(make_game):
    row = make_game('2711751', jopox_uid='229648')
    assert set_link(row.game_id, '229999', {'229648'}).status == KEPT_EXISTING
    assert row.jopox_uid == '229648'


def test_stale_link_is_repointed(make_game):
    """Jopox ei anna poistettua uid:tä uudelleen, joten poissaolo todistaa sen poistetuksi."""
    row = make_game('2711751', jopox_uid='229648')
    assert set_link(row.game_id, '229999', {'111111'}).status == LINKED
    assert row.jopox_uid == '229999'


def test_uid_already_used_by_another_game_in_the_same_team(make_game):
    first = make_game('2711751', jopox_uid='229648')
    second = make_game('2711752')
    assert set_link(second.game_id, '229648', {'111111'}).status == CONFLICT
    assert second.jopox_uid is None
    assert first.jopox_uid == '229648'


def test_same_uid_is_allowed_for_another_team(make_game, app):
    """Konfliktivahti on tarkoituksella joukkuekohtainen - dokumentoidaan nykyinen rajaus."""
    from extensions import db
    from models.team import Team

    other = Team(team_id='1368626269', team_name='S-Kiekko Punainen',
                 stat_group='U14 Valkoinen', season='2026', statgroup='8815')
    db.session.add(other)
    db.session.commit()

    make_game('2711751', jopox_uid='229648')
    cross = make_game('2710574', team_obj=other)

    assert set_link(cross.game_id, '229648', {'111111'}).status == LINKED
    assert cross.jopox_uid == '229648'


def test_unknown_game_is_not_found(make_game):
    assert set_link('ei-ole-olemassa', '229648').status == NOT_FOUND


def test_missing_arguments_are_rejected(make_game):
    row = make_game('2711751')
    assert set_link(row.game_id, None).status == NOT_FOUND
    assert set_link(None, '229648').status == NOT_FOUND
    assert row.jopox_uid is None


def test_set_link_does_not_commit(make_game):
    """Kutsuja päättää transaktion rajat; rollbackin pitää perua linkitys."""
    from extensions import db

    row = make_game('2711751')
    set_link(row.game_id, '229648')
    db.session.rollback()
    assert row.jopox_uid is None
