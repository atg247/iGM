import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Yksi nimetty juuriloggari sovellukselle
logger = logging.getLogger("igm")

if not logger.handlers:
    # Prod: INFO; Dev: DEBUG (ellei LOG_LEVEL override)
    is_prod = bool(os.getenv("DYNO")) or os.getenv("APP_ENV", "dev").lower() == "production"
    log_level = os.getenv("LOG_LEVEL", "INFO" if is_prod else "DEBUG").upper()

    logger.setLevel(log_level)
    logger.propagate = False  # ei duplikaatteja rootin kautta

    # Yhtenäinen formaatti
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(module)-13.13s - %(funcName)-13.13s - %(levelname)-5s - %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    # Konsoli (Heroku lukee stdout/stderr)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)   # varmistetaan, että handler ei nosta tasoa
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Devissä myös tiedostoon (Herokussa FS on efemeerinen, joten ei siellä)
    if not is_prod:
        os.makedirs("logs", exist_ok=True)
        file_handler = RotatingFileHandler(
            "logs/igm.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Hiljennä kolmansien osapuolten melu (prodissa tiukemmin)
    logging.getLogger("werkzeug").setLevel(logging.WARNING if is_prod else logging.INFO)
    logging.getLogger("gunicorn.error").setLevel(logging.INFO)     # virheloki, pidä näkyvissä
    logging.getLogger("gunicorn.access").setLevel(logging.ERROR)   # access-logi pois näkyvistä
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING if is_prod else logging.INFO)

# logging_config.py (lisäys loppuun)
_root = logging.getLogger()
if not _root.handlers:
    # ohjataan kaikki juuritasolta vähintään ERRORit ulos (varmistus)
    import sys
    _h = logging.StreamHandler(sys.stderr)
    _h.setLevel(logging.ERROR)
    _h.setFormatter(logging.Formatter("%(asctime)s - ROOT - %(levelname)s - %(message)s"))
    _root.addHandler(_h)
