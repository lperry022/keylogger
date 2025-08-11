import os, base64
from typing import Optional
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

KEY_FILE = "secret.key"
SALT_FILE = "salt.bin"
SALT_SIZE = 16

def _load_or_create_salt() -> bytes:
    if os.path.exists(SALT_FILE):
        return open(SALT_FILE, "rb").read()
    salt = os.urandom(SALT_SIZE)
    with open(SALT_FILE, "wb") as f:
        f.write(salt)
    return salt

def _derive_key(password: bytes, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
    return base64.urlsafe_b64encode(kdf.derive(password))

def load_or_create_key(password: Optional[str] = None) -> bytes:
    """
    If KEY_FILE exists, read it. Otherwise derive from `password` (or LOG_ENCRYPTION_PASSWORD env)
    and save it to KEY_FILE.
    """
    if os.path.exists(KEY_FILE):
        return open(KEY_FILE, "rb").read()

    pwd = (password or os.getenv("LOG_ENCRYPTION_PASSWORD") or "").encode()
    if not pwd:
        raise ValueError("No password provided to create key (set in GUI or LOG_ENCRYPTION_PASSWORD).")

    salt = _load_or_create_salt()
    key = _derive_key(pwd, salt)
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key

# internal cached Fernet
_F = None

def set_password_for_new_key(password: str) -> None:
    """Create key file from password if it doesn't exist yet."""
    global _F
    if not os.path.exists(KEY_FILE):
        key = load_or_create_key(password)
        _F = Fernet(key)  # cache for immediate use

def _ensure_fernet() -> Fernet:
    global _F
    if _F is None:
        # load existing key (no password needed once file exists)
        if not os.path.exists(KEY_FILE):
            raise RuntimeError("Key file not found. Provide a password in the GUI and click 'Init Key'.")
        _F = Fernet(open(KEY_FILE, "rb").read())
    return _F

def encrypt_line(text: str) -> bytes:
    return _ensure_fernet().encrypt(text.encode())

def decrypt_line(token: bytes) -> str:
    return _ensure_fernet().decrypt(token).decode()
