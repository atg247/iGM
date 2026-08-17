# iGM — Ottelunhaku

Flask-sovellus jääkiekkojoukkueen otteluohjelman pitämiseen ajan tasalla. Hakee joukkueen
virallisen ohjelman **Tulospalvelu.fi**:stä, lukee saman joukkueen kalenterin **Jopoxista**,
vertaa niitä ja kertoo mitkä ottelut puuttuvat Jopoxista tai ovat siellä väärin — ja kirjoittaa
korjaukset takaisin Jopoxiin.

Jopoxilla ei ole julkista rajapintaa, joten sitä käytetään kirjautumalla sisään ja täyttämällä
sen hallintalomakkeita ohjelmallisesti.

## Käyttöönotto

Python 3.12, riippuvuudet virtuaaliympäristöön.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # tuotantoon riittää requirements.txt
pre-commit install                    # kerran per työasema
```

Luo `.env`-tiedosto (ei versionhallinnassa). Vähintään nämä tarvitaan:

| Muuttuja | Merkitys |
|---|---|
| `SECRET_KEY` | Flaskin istuntojen allekirjoitus |
| `FERNET_KEY` | Jopox-salasanojen salaus levylle; sovellus ei käynnisty ilman |
| `DATABASE_URL` | Postgres tuotannossa; ilman tätä käytetään paikallista SQLiteä |
| `EMAIL_USERNAME`, `EMAIL_PASSWORD` | Salasanan palautusviestit |

## Ajaminen

```bash
flask run --debug
```

Sovellus nousee osoitteeseen http://127.0.0.1:5001 (`FLASK_RUN_PORT` tulee `.env`:stä).

**Käytä `--debug`-lippua.** Ilman sitä palvelin ei lataa koodimuutoksia, ja muutos näyttää
siltä kuin se ei toimisi.

## Testit ja tarkistukset

```bash
pytest          # ei koske kehityskantaan eikä ota yhteyttä Jopoxiin
ruff check .
```

Molemmat ajetaan myös CI:ssä jokaisella pushilla.

## Tietokanta

Migraatiot Flask-Migratella. Skeeman muutoksen jälkeen:

```bash
flask --app wsgi db migrate -m "kuvaus"
flask --app wsgi db upgrade
```

Tuotannossa `db upgrade` on ajettava erikseen — se ei tapahdu deployn yhteydessä itsestään.

## Lisää

- `CLAUDE.md` — arkkitehtuuri ja moduulien vastuut
- `docs/paatokset.md` — miksi tietyt ratkaisut ovat niin kuin ovat
