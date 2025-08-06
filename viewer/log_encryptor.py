import os
import getpass
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode
from datetime import datetime

# Constants
LOG_DIR = "logs"
KEYFILE_PATH = "keyfile.txt"
SALT = b'some_static_salt_value_123'  # Must be 16+ bytes. Replace with your own unique salt!

# Ensure logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Get password securely
def get_password():
    password = os.getenv("LOG_ENCRYPTION_PASSWORD")
    if not password:
        password = getpass.getpass("Enter encryption password: ")
    return password.encode()

# Generate or load key
def load_or_generate_key(password: bytes):
    if os.path.exists(KEYFILE_PATH):
        with open(KEYFILE_PATH, "rb") as f:
            key = f.read()
    else:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=SALT,
            iterations=100000,
            backend=default_backend()
        )
        key = urlsafe_b64encode(kdf.derive(password))
        with open(KEYFILE_PATH, "wb") as f:
            f.write(key)
    return key

# Encrypt log data
def encrypt_log(data: bytes):
    password = get_password()
    key = load_or_generate_key(password)
    f = Fernet(key)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{LOG_DIR}/{date_str}.log"
    encrypted_data = f.encrypt(data)

    with open(filename, "ab") as file:
        file.write(encrypted_data + b'\n')
