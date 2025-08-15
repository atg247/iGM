import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename="comparison.log",
    encoding='utf-8',
    filemode='w',
    format='%(asctime)s - %(module)-13.13s - %(funcName)-13.13s - %(levelname)-5s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
