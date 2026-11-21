import json
import os
from cryptography.fernet import Fernet
from config import ENCRYPTION_KEY

STORAGE_FILE = "credentials.json"


class CredentialStore:
    """Encrypted on-disk store for user credentials.

    Passwords are encrypted at rest with Fernet (AES-128 in CBC mode with
    HMAC authentication). The encryption key must be provided via the
    ENCRYPTION_KEY environment variable.
    """

    def __init__(self):
        if not ENCRYPTION_KEY:
            raise ValueError("ENCRYPTION_KEY environment variable is required")
        key = ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY
        self.cipher = Fernet(key)
        self._data = {}
        self._load()

    def _load(self):
        if os.path.exists(STORAGE_FILE):
            with open(STORAGE_FILE, "r") as f:
                raw = json.load(f)
            self._data = {int(k): v for k, v in raw.items()}

    def _save(self):
        raw = {str(k): v for k, v in self._data.items()}
        with open(STORAGE_FILE, "w") as f:
            json.dump(raw, f)

    def save_credential(self, user_id: int, service: str, email: str, password: str):
        if user_id not in self._data:
            self._data[user_id] = {}
        encrypted_pw = self.cipher.encrypt(password.encode()).decode()
        self._data[user_id][service] = {
            "email": email,
            "password": encrypted_pw,
        }
        self._save()

    def get_credentials(self, user_id: int) -> dict:
        """Return {service: (email, password)} with passwords decrypted."""
        if user_id not in self._data:
            return {}
        result = {}
        for service, info in self._data[user_id].items():
            password = self.cipher.decrypt(info["password"].encode()).decode()
            result[service] = (info["email"], password)
        return result

    def remove_credential(self, user_id: int, service: str) -> bool:
        if user_id in self._data and service in self._data[user_id]:
            del self._data[user_id][service]
            self._save()
            return True
        return False
