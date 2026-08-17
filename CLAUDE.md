# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this app does

iGM ("Ottelunhaku") is a Flask web app for Finnish youth hockey team managers. It:

1. Fetches a team's official game schedule from **Tulospalvelu.fi** (leijonat.fi results service API).
2. Scrapes/manages the same team's calendar in **Jopox** (a Finnish sports-club management platform), which has no public API — `JopoxScraper` mixes a documented JSON API (`myapi.jopox.fi`) with legacy ASP.NET WebForms scraping (`__VIEWSTATE`/`__EVENTVALIDATION` postbacks via BeautifulSoup).
3. Compares the two datasets with fuzzy matching (team names, times, locations) to flag games that are missing or wrong in Jopox, then lets the manager push corrections back into Jopox from the UI.

Much of the domain vocabulary in code, logs, and templates is Finnish (e.g. `joukkueet` = teams, `paikka` = location, `aika` = time, `ottelu` = game).

## Commands

Python env is managed with a `.venv` (Python 3.12, see `.python-version`).

```bash
# install deps
pip install -r requirements.txt

# run the dev server (reads FLASK_APP=wsgi from .flaskenv)
python app.py                 # http://localhost:5000, debug via DEBUG=True env var
# or
flask --app wsgi run

# database migrations (Flask-Migrate/Alembic)
flask --app wsgi db migrate -m "message"
flask --app wsgi db upgrade

# production-style run (as used by Procfile)
gunicorn wsgi:app --config gunicorn.conf.py

# tests and lint (dev deps: pip install -r requirements-dev.txt)
pytest
ruff check .
pre-commit install       # once per machine; runs ruff + whitespace checks on commit
```

Tests live in `tests/` and are configured in `pyproject.toml`. They never touch the
development database, `logs/igm.log` or Jopox: `tests/conftest.py` points `DATABASE_URL` at a
temporary file and sets `APP_ENV=production` before the app is imported. Jopox interaction is
tested by swapping a fake session into `JopoxScraper` and inspecting the form payload that
would have been posted — Jopox has no API and no test environment, so this is the only way to
check what gets written before it lands in a real club calendar.

Ruff runs with a deliberately narrow rule set (`E`, `F`, `I`, `W`) that is kept at zero.
`ruff format` has **not** been applied to the codebase yet, so it is disabled in
`.pre-commit-config.yaml`; enabling it needs a one-off reformat commit first.

The `package.json`/`vue` dependencies are present but there is no active Vue build in use; frontend behavior lives in plain `static/js/*.js` and Jinja templates.

## Configuration / secrets

Config is environment-driven via `.env` (loaded with `python-dotenv`) and read in `config.py`, `security.py`, `logging_config.py`. Required/used env vars:

- `DATABASE_URL` — Postgres URL in prod (Heroku `postgres://` is rewritten to `postgresql://`); falls back to local SQLite at `instance/hockey_data.db` if unset.
- `SECRET_KEY` — Flask session signing.
- `FERNET_KEY` — required at import time by `security.py`; used to encrypt/decrypt each user's stored Jopox password (`User.jopox_password`). App raises `RuntimeError` at startup if missing.
- `COOKIE_SECURE` — toggles `REMEMBER_COOKIE_SECURE` (True on Heroku, False locally).
- `EMAIL_USERNAME` / `EMAIL_PASSWORD` — Gmail SMTP for Flask-Mail (password reset emails).
- `LOG_LEVEL`, `APP_ENV`, `DYNO` — logging verbosity/target; `DYNO` presence implies running on Heroku (prod).
- `PORT`, `DEBUG` — used by the `if __name__ == '__main__'` dev entrypoint in `app.py`.

## Architecture

**App factory**: `app.py` builds the app via `create_app()`, initializes extensions (`extensions/__init__.py`: `db`, `bcrypt`, `mail`, `session`, `login_manager`) and registers four blueprints. `wsgi.py` is the real entrypoint used by gunicorn/Heroku — it wraps `create_app()` with logging and re-raises on failure so boot errors are visible in logs.

**Blueprints** (`routes/`):
- `routes/route.py` (`routes_bp`) — top-level pages (`/`, `/dashboard`, `/schedule`, `/simulator`).
- `routes/auth/` (`auth_bp`) — login/register/logout/password reset, one file per route, aggregated via `routes/auth/__init__.py`.
- `routes/dashboard/` (`dashboard_bp`) — team management: save/clear Jopox credentials, select managed Jopox team, add/remove followed & managed teams.
- `routes/api/` (`api_bp`, prefix `/api`) — the core data-fetch/compare/write workflow: `get_all_schedules`, `get_tulospalvelu_games`, `get_jopox_games`, `compare`, `update_jopox`, `create_jopox`, `check_level`, `jopox_status`. `routes/api/__init__.py` registers a blueprint-wide `errorhandler(Exception)` that converts any exception to a JSON `{status, message}` response.

Each route submodule does `from . import <blueprint>` and attaches routes by decorating; the package `__init__.py` files import `*` from every submodule purely for route registration side effects.

**Models** (`models/`, SQLAlchemy via `db` from `extensions`):
- `User` — app account, plus encrypted Jopox credentials (`jopox_username`, `jopox_password` as Fernet-encrypted bytes) and cached Jopox team info (`jopox_team_id`, `jopox_calendar_url`, ...).
- `Team` — a Tulospalvelu team, keyed by `(team_id, stat_group)` unique constraint, not by `team_id` alone (a team can appear in multiple stat groups/series).
- `UserTeam` — many-to-many join between `User` and `Team` with a `relationship_type` of `'manage'` or `'follow'` — this distinction drives most business logic (only "managed" teams get write-backs to Jopox; "followed" teams are read-only schedule tracking).
- `TGamesdb` (`tgames` table) — cached snapshot of fetched Tulospalvelu games per team, FK to `Team.id` with cascade delete.

**Helpers** (`helpers/`) — the domain logic, kept out of routes:
- `data_fetcher.py` — thin wrappers around Tulospalvelu.fi lookup endpoints (seasons/levels/stat groups/teams) plus `hae_kalenteri` for parsing a Jopox-exported ICS calendar.
- `game_fetcher.py` (`GameFetcher`) — fetches a team's games from Tulospalvelu and normalizes them into a pandas DataFrame. Note `Time` defaults empty `GameTime` to `'07:00'` — this sentinel means "not scheduled yet" and is checked for explicitly downstream.
- `game_comparison.py` (`compare_games`) — the matching core. Scores a Tulospalvelu game against a Jopox game with `score_candidate()`: `fuzzywuzzy` on team names/location, date/time proximity (exact time, or exactly 1 hour earlier = "arrival time" convention), and a `pienpeli` (small-area game) check. Produces per-game `match_status` of `green`/`yellow`/`red` with a Finnish `reason`. Runs in three passes, and the order matters:
  1. games with a stored `jopox_uid` claim their event out of the pool — a link is a fact, not a guess, so it must not have to compete;
  2. every remaining game/event pair is scored and assigned **best score first**, not in list order;
  3. results are emitted in the original order.

  Both rules exist because of real mispairings: matching in list order let a game scoring 30 take an event that another game scored 150 on, and looking up links inside the consuming loop let an earlier game steal a linked event. Mutates its `jopox_games` input list (`.remove()`) for claimed pairs, so callers must not reuse that list.
- `game_templates.py` — the free-text fields written into Jopox. Owns `DEFAULT_PUBLIC_INFO` and the `{placeholder}` rendering; the scraper makes no content decisions. `GAME_INFO_MESSAGE` is deliberately empty — see the decision log.
- `jopox_links.py` (`set_link`) — the single rule for when a `TGamesdb.jopox_uid` may be set or replaced, returning `linked` / `unchanged` / `kept_existing` / `conflict` / `not_found`. Used by creation, update and (later) manual linking, so the rule cannot drift between paths. Does not commit.
- `jopox_scraper.py` (`JopoxScraper`) — all Jopox interaction. Persists scraping session state (cookies, VIEWSTATE, tokens) into the Flask session keyed by `user_id` (`save_session_to_flask`/`load_session_from_flask`) so a login doesn't need to be repeated on every request; call `ensure_logged_in()`/`access_admin()` before scraping/write operations. Also owns league/level creation (`create_league`, `define_league`) and game create/modify (`add_game`, `modify_game`) against Jopox's admin UI.
- `update_jopox_credentials.py` — decrypts the current user's stored Jopox password with `security.cipher_suite` and refreshes cached `jopox_team_id`/`jopox_calendar_url` via a fresh `JopoxScraper` login.

**Typical request flow** for the main use case: dashboard lists managed/followed teams (`UserTeam.relationship_type`) → `/api/schedules` fetches+caches Tulospalvelu games per team into `TGamesdb` → frontend also fetches the user's Jopox games (scraped) → `/api/compare` fuzzy-matches the two → mismatches shown to the user → `/api/update_jopox` writes corrections back into Jopox via `JopoxScraper`.

**Logging**: a single named logger `"igm"` configured in `logging_config.py` (import `logger` from there, not `logging.getLogger` directly). Logs to stdout always; also to `logs/igm.log` (rotating) when not running on Heroku. Level is `INFO` in prod, `DEBUG` in dev unless `LOG_LEVEL` overrides.

**Security**: passwords hashed with `flask-bcrypt`; each user's Jopox password is separately encrypted at rest with Fernet (`security.cipher_suite`, key from `FERNET_KEY`) since it must be decrypted later to log into Jopox on the user's behalf — this is different from the one-way `User.password_hash`.
