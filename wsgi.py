from logging_config import logger  # aktivoi logitus heti
logger.info("WSGI bootstrap starting...")

try:
    from app import create_app
    app = create_app()
    logger.info("Flask app created.")
except Exception:
    logger.exception("Fatal error during app initialization")
    raise