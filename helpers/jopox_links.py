"""Tulospalvelu-ottelun ja Jopox-tapahtuman välisen linkin hallinta.

Linkki (TGamesdb.jopox_uid) on se, joka pitää ottelut pareina ilman että vertailun tarvitsee
arvata paria uudelleen joka kerta. Sääntö siitä, milloin linkin saa asettaa tai korvata, on
tässä yhdessä paikassa, koska sitä tarvitaan useammasta kohdasta - luonnista, muokkauksesta ja
myöhemmin käyttäjän tekemästä manuaalisesta linkityksestä. Jos sääntö haarautuisi, eri polut
alkaisivat kohdella vanhentuneita ja ristiriitaisia linkkejä eri tavoin.

set_link() ei committaa: kutsuja päättää transaktion rajat.
"""

from collections import namedtuple

from logging_config import logger
from models.tgames import TGamesdb

# Linkki asetettiin (rivi oli linkitön tai vanha linkki oli varmistetusti vanhentunut).
LINKED = "linked"
# Rivillä oli jo tämä sama uid.
UNCHANGED = "unchanged"
# Rivillä oli eri uid, joka on tai voi olla yhä voimassa - ei korvattu.
KEPT_EXISTING = "kept_existing"
# Uid on jo linkitetty saman joukkueen toiseen otteluun.
CONFLICT = "conflict"
# Ottelua ei löytynyt kannasta, tai argumentit puuttuivat.
NOT_FOUND = "not_found"

LinkResult = namedtuple("LinkResult", "status row")


def set_link(game_id, jopox_uid, known_uids_before=None):
    """Asettaa ottelun jopox_uid:n turvallisesti ja palauttaa LinkResult(status, row).

    known_uids_before on tilannekuva Jopoxin uid:istä ennen toimenpidettä. Sen avulla
    erotetaan kovapoistettu linkki yhä voimassa olevasta: koska Jopox ei koskaan palauta
    käyttöön kerran poistettua uid:tä, poissaolo tilannekuvasta tarkoittaa että vanha
    tapahtuma on poistettu ja linkin saa osoittaa uudelleen. None tarkoittaa ettei
    tilannekuvaa ole - silloin vanhaa linkkiä ei korvata, koska varmuutta ei ole.

    Ei committaa.
    """
    if not game_id or not jopox_uid:
        return LinkResult(NOT_FOUND, None)

    # game_id on kannassa merkkijono mutta tulee Tulospalvelusta numerona. SQLite täsmäisi
    # silti tyyppiaffiniteetin ansiosta, Postgres ei - normalisoidaan aina.
    game_id = str(game_id)
    jopox_uid = str(jopox_uid)

    row = TGamesdb.query.filter_by(game_id=game_id).first()
    if not row:
        logger.info("set_link: game_id %s ei löytynyt tgames-taulusta", game_id)
        return LinkResult(NOT_FOUND, None)

    if row.jopox_uid == jopox_uid:
        return LinkResult(UNCHANGED, row)

    if row.jopox_uid:
        if known_uids_before is None or row.jopox_uid in known_uids_before:
            logger.info(
                "set_link: game_id %s on jo linkitetty uid:hen %s (voimassa tai varmistamaton) "
                "- ei korvata uudella uid:llä %s",
                game_id,
                row.jopox_uid,
                jopox_uid,
            )
            return LinkResult(KEPT_EXISTING, row)

        logger.info(
            "set_link: vanhentunut uid %s -> %s ottelulle %s", row.jopox_uid, jopox_uid, game_id
        )

    conflict = TGamesdb.query.filter(
        TGamesdb.jopox_uid == jopox_uid,
        TGamesdb.team_id == row.team_id,
        TGamesdb.game_id != row.game_id,
    ).first()
    if conflict:
        logger.warning(
            "set_link: uid %s on jo linkitetty ottelulle %s - ei linkitetä ottelulle %s",
            jopox_uid,
            conflict.game_id,
            game_id,
        )
        return LinkResult(CONFLICT, row)

    row.jopox_uid = jopox_uid
    logger.info("set_link: ottelu %s linkitetty uid:hen %s", game_id, jopox_uid)
    return LinkResult(LINKED, row)
