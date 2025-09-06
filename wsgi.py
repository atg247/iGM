import os, sys
# Ensure local module imports resolve to files in this directory first
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from logging_config import logger  # aktivoi logitus heti
logger.info("WSGI bootstrap starting...")

try:
    from app import create_app
    app = create_app()
    logger.info("Flask app created.")
except Exception:
    logger.exception("Fatal error during app initialization")
    raise
