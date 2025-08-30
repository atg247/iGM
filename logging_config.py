import logging
import os
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("igm")

if not logger.handlers:

    log_level = os.getenv(
        "LOG_LEVEL",
        "INFO" if os.getenv("APP_ENV", "dev").lower() == "production" or os.getenv("DYNO") else "DEBUG"
    ).upper()
    logger.setLevel(log_level)
    logger.propagate = False

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

is_prod = os.getenv("APP_ENV", "dev").lower() == "production" or os.getenv("DYNO")

logging.getLogger("werkzeug").setLevel("WARNING" if is_prod else "INFO")
logging.getLogger("sqlalchemy.engine").setLevel("WARNING" if is_prod else "INFO")