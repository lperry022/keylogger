import os
import getpass
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

KEYFILE_PATH = "../keyfile.txt"  # adjust this path if needed
SALT = b'some_static_salt_value_123'

def get_decryption_key():
    if os.path.exists(KEYFILE_PATH):
        with open(KEYFILE_PATH, "rb") as f:
            return f.read()
    else:
        password = getpass.getpass("Enter decryption password: ").encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=SALT,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password))