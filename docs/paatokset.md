# Päätökset

Ratkaisuja, joiden perustelu ei näy koodista ja jotka on kallista selvittää uudelleen. Uusin
ylimpänä. Lisää tänne rivi, kun päätät jotain, mikä yllättäisi seuraavan lukijan — erityisesti
jos syy löytyi Jopoxin käyttäytymisestä eikä omasta koodista.

Muoto: mitä päätettiin, miksi, ja mikä muuttuisi jos päätöstä muutetaan.

---

## 2026-08-17 · Jopoxin viestikenttä jätetään tyhjäksi

`GameInfoTextBox` täytettiin ottelun tiedoilla. Kentän oma label Jopoxin lomakkeella on
*"Viesti (näkyy tapahtuman osallistujille Jopox pukukopissa ilmoituksena sekä Jopox+
sovelluksessa notifikaationa)"* — eli se ei ole infokenttä vaan joukkueelle lähtevä ilmoitus.

Jopox on kuitenkin poistanut sen käyttöliittymästä: textarea on kahden sisäkkäisen
`display: none` -paneelin (`NotificationPanel`, `GameNotificationPanel`) sisällä, eikä
ottelulomakkeella näy kuin Ennakkoinfo. Sinne aiemmin kirjoitettu teksti ei siis ole näkynyt
kenellekään eikä lähettänyt ilmoituksia.

Kenttä lähetetään silti mukana tyhjänä, koska selainkin postittaa piilotetun kentän ja
poisjättö voisi kaataa ASP.NET-postbackin.

**Jos muutat:** varmista ensin Jopoxista, onko toiminto palautettu käyttöön. Massaluonti
lähettäisi yhden ilmoituksen per ottelu.

## 2026-08-17 · Linkitetty pari varataan ennen fuzzy-täsmäytystä

`TGamesdb.jopox_uid` on tieto, ei arvaus. Jos linkki haetaan samassa silmukassa, joka kuluttaa
Jopox-rivejä, listalla aiempi linkitön ottelu ehtii viedä juuri sen rivin, joka kuuluu
myöhemmälle linkitetylle ottelulle — ja loki näyttää tältä erottamattomasti samalta kuin
aidosti Jopoxista poistettu tapahtuma.

**Jos muutat:** `tests/test_game_comparison.py::test_linked_pair_is_reserved_before_fuzzy_round`
kaatuu.

## 2026-08-17 · Tapahtuma menee parhaalle osumalle, ei ensimmäiselle

Täsmäytys eteni ottelu kerrallaan ja jokainen otti parhaan vapaan rivin omalla vuorollaan,
jolloin listajärjestys ratkaisi. Oikealla datalla 30 pisteen osuma vei tapahtuman ottelulta,
jonka osuma samaan tapahtumaan oli 150 pistettä.

Tämä ei ollut vain kosmeettista: väärin paritetun rivin "Päivitä Jopox" olisi kirjoittanut
yhden ottelun tiedot toisen ottelun päälle Jopoxissa.

**Jos muutat:** pisteytys (`score_candidate`) ja jako ovat eri asioita — pisteytystä voi
säätää koskematta jakojärjestykseen.

## 2026-08-17 · Muokkaus tallentaa linkin vain varmasta parista

`update_jopox` saa uid:n modalista, mutta modalin pari tulee fuzzy-täsmäytyksestä eikä
käyttäjän valinnasta. Epävarma osuma voi osoittaa saman päivän toiseen otteluun, ja väärä
linkki lukitsisi virheen pysyväksi, koska vertailu luottaa jatkossa linkkiin.

Frontend lähettää `pairing_confident`, joka on tosi vain vihreälle osumalle ilman varoitusta.

**Jos muutat:** oikea ratkaisu on antaa käyttäjän vahvistaa tai vaihtaa pari (tiekartan C2),
jolloin ehto voi perustua nimenomaiseen valintaan arvion sijaan.

## 2026-08-17 · Konfliktivahti on joukkuekohtainen

`set_link` estää saman `jopox_uid`:n linkittämisen kahdelle ottelulle **saman joukkueen**
sisällä, mutta sallii sen eri joukkueille. Tämä on nykyinen käyttäytyminen, ei vahinko — mutta
sitä ei ole varsinaisesti perusteltu.

**Jos muutat:** päätös tarvitaan ennen kuin `(team_id, jopox_uid)` -uniikki-indeksi lisätään.
Testi `test_same_uid_is_allowed_for_another_team` dokumentoi nykytilan ja kaatuu muutoksesta.

## 2026-08-17 · `game_id` normalisoidaan merkkijonoksi joka rajapinnalla

Tulospalvelu lähettää `Game ID`:n JSON-numerona, `tgames.game_id` on varchar. SQLite täsmää
numeron merkkijonosarakkeeseen tyyppiaffiniteetin ansiosta, joten virhe ei näy paikallisesti —
Postgresissa vertailu käyttäytyy toisin.

Tämä ehti aiheuttaa yhden bugin: linkkihaku löysi rivit kannasta, mutta niiden avaimet olivat
merkkijonoja ja haku tehtiin numerolla, jolloin yksikään linkki ei osunut.

**Jos muutat:** älä. Normalisoi molemmat päät.

## 2026-08-17 · Jopox-kirjoitukset testataan valepäätteellä

Jopoxilla ei ole APIa eikä testiympäristöä, ja jokainen luonti syntyy seuran oikeaan
kalenteriin. `tests/test_add_game_payload.py` vaihtaa `JopoxScraper.session`-olion tilalle
kaksoisolennon, joka nappaa POSTin lähettämättä sitä, ja tarkastaa lomakekentät.

Tämä on ainoa tapa saada kiinni kentän sisältövirhe etukäteen. Ilman sitä jäi huomaamatta
kenttä, jonka arvona luki kirjaimellisesti `None` neljässätoista luodussa ottelussa.
