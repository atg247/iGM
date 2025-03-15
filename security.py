import os

from cryptography.fernet import Fernet

fernet_key = os.getenv('FERNET_KEY')
cipher_suite = Fernet(fernet_key)
