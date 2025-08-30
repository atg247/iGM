# logging_config.py
import logging
import os
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("igm")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s:%(lineno)d — %(message)s",
    "%Y-%m-%d %H:%M:%S"
)

# Konsoliin
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Dev-ympäristössä myös tiedostoon
if os.getenv("APP_ENV", "dev") != "production" and not os.getenv("DYNO"):
    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler(
        "logs/igm.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

logger.debug("Logger initialized")