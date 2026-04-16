"""Fernet-based symmetric encryption service for PHI data at rest."""

from cryptography.fernet import Fernet

from src.core.config import settings


class EncryptionService:
    """Encrypts and decrypts bytes using Fernet symmetric encryption.

    The key is loaded from ENCRYPTION_KEY in the application settings.
    Generate a valid key with:
        python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """

    def __init__(self) -> None:
        self._fernet = Fernet(settings.ENCRYPTION_KEY.encode())

    def encrypt(self, data: bytes) -> bytes:
        """Return the Fernet-encrypted ciphertext of the given bytes."""
        return self._fernet.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        """Return the plaintext bytes decrypted from the given Fernet ciphertext."""
        return self._fernet.decrypt(data)
