"""Vertailun täsmäytyslogiikka.

Puhtaita testejä: ei kantaa eikä verkkoa. Painopiste on niissä tilanteissa, joissa sama
päivä tuottaa useita ehdokkaita - juuri siellä väärä pari on aiemmin syntynyt.
"""

from helpers.game_comparison import compare_games


def t_game(
    game_id,
    home="K-Laser Punainen",
    away="S-Kiekko Musta",
    time="13:30",
    location="Seinäjoki 2",
    date="Sat, 26 Sep 2026 00:00:00 GMT",
):
    return {
        "Game ID": game_id,
        "Type": "manage",
        "SortableDate": date,
        "Time": time,
        "Location": location,
        "Small Area Game": "0",
        "Home Team": home,
        "Away Team": away,
    }


def j_game(
    uid,
    home="K-Laser Punainen",
    away="S-Kiekko Musta",
    aika="13:30",
    paikka="Seinäjoki 2",
    pvm="2026-09-26",
):
    return {
        "uid": uid,
        "sortable_date": f"{pvm} {aika}",
        "aika": aika,
        "paikka": paikka,
        "joukkueet": f"{home} - {away}",
    }


def pairs(results):
    return {r["game"]["Game ID"]: (r["best_match"] or {}).get("uid") for r in results}


def test_identical_games_keep_distinct_pairs():
    """Kaksi samanlaista ottelua samana päivänä eivät saa jakaa samaa Jopox-riviä."""
    results = compare_games(
        [j_game("228450"), j_game("228451")],
        [t_game("A"), t_game("B")],
    )
    got = pairs(results)
    assert got["A"] != got["B"]
    assert set(got.values()) == {"228450", "228451"}


def test_stored_link_beats_fuzzy_match():
    """Linkki ratkaisee parin, vaikka fuzzy päätyisi toiseen järjestykseen."""
    results = compare_games(
        [j_game("228450"), j_game("228451")],
        [t_game("A"), t_game("B")],
        {"A": "228451", "B": "228450"},
    )
    assert pairs(results) == {"A": "228451", "B": "228450"}
    assert all(r["warning"] is None for r in results)


def test_linked_pair_is_reserved_before_fuzzy_round():
    """Linkitön ottelu ei saa napata riviä, joka kuuluu linkillä toiselle ottelulle.

    Regressio: linkki haettiin aiemmin samassa silmukassa, joka kulutti Jopox-rivejä, joten
    listalla aiempi ottelu ehti viedä rivin ennen linkin vuoroa.
    """
    results = compare_games([j_game("228450")], [t_game("A"), t_game("B")], {"B": "228450"})
    got = pairs(results)
    assert got["B"] == "228450"
    assert got["A"] is None


def test_event_goes_to_best_scoring_game_not_the_first_one():
    """Sama päivä, kaksi ottelua: tapahtuma kuuluu sille, jonka tiedot täsmäävät.

    Regressio: aiemmin listalla ensimmäinen ottelu vei rivin heikoillakin pisteillä.
    """
    huono = t_game(
        "huono",
        home="Sport Punainen",
        away="S-Kiekko Musta",
        time="07:00",
        location="Vaasa hh 2",
        date="Sat, 05 Sep 2026 00:00:00 GMT",
    )
    hyva = t_game(
        "hyva",
        home="S-Kiekko Punainen",
        away="Diskos Punainen",
        time="13:30",
        location="Seinäjoki 2",
        date="Sat, 05 Sep 2026 00:00:00 GMT",
    )
    tapahtuma = j_game("229659", home="S-Kiekko Punainen", away="Diskos Punainen", pvm="2026-09-05")

    got = pairs(compare_games([tapahtuma], [huono, hyva]))
    assert got["hyva"] == "229659"
    assert got["huono"] is None


def test_stale_link_falls_back_to_fuzzy():
    """Jopoxista poistettu uid ei saa jättää ottelua ilman paria."""
    got = pairs(compare_games([j_game("228450")], [t_game("A")], {"A": "999999"}))
    assert got["A"] == "228450"


def test_linked_pair_still_reports_discrepancies():
    """Linkki ohittaa arvaamisen muttei sisällön tarkistusta."""
    results = compare_games(
        [j_game("228450", aika="15:30")],
        [t_game("A", time="13:30")],
        {"A": "228450"},
    )
    assert results[0]["match_status"] == "yellow"
    assert "13:30" in results[0]["reason"]
    assert results[0]["best_match"]["uid"] == "228450"


def test_matching_game_is_green():
    results = compare_games([j_game("228450")], [t_game("A")], {"A": "228450"})
    assert results[0]["match_status"] == "green"


def test_game_missing_from_jopox_is_red():
    results = compare_games([], [t_game("A")])
    assert results[0]["match_status"] == "red"
    assert results[0]["best_match"] is None


def test_followed_games_are_not_compared():
    followed = dict(t_game("A"), Type="follow")
    assert compare_games([j_game("228450")], [followed]) == []


def test_game_id_may_arrive_as_a_number():
    """Tulospalvelu lähettää Game ID:n numerona, linkkikartan avaimet ovat merkkijonoja."""
    results = compare_games([j_game("228450")], [t_game(2711764)], {"2711764": "228450"})
    assert results[0]["best_match"]["uid"] == "228450"
    assert results[0]["warning"] is None
