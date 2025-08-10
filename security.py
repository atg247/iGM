import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

fernet_key = os.getenv('FERNET_KEY')
if not fernet_key:
    raise RuntimeError(
        "FERNET_KEY puuttuu ympäristöstä. Lisää se .env-tiedostoon tai ympäristömuuttujaksi."
    )

cipher_suite = Fernet(fernet_key)
