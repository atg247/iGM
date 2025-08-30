# logging_config.py
import logging
import os
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("igm")
logger.setLevel(logging.DEBUG)
logger.propagate = False   # estää viestien duplikaation root-loggereihin

# Formaatti: 2025-08-30 11:30:57 [INFO ] igm:123 — viesti
formatter = logging.Formatter(
    "%(asctime)s - %(module)-13.13s - %(funcName)-13.13s - %(levelname)-5s - %(message)s",
    "%Y-%m-%d %H:%M:%S"
)


# Konsoli
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Devissä myös tiedostoon
if os.getenv("APP_ENV", "dev").lower() != "production" and not os.getenv("DYNO"):
    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler(
        "logs/igm.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
