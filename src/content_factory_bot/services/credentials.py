"""Encrypt provider tokens at rest (Fernet when key configured)."""

import logging

logger = logging.getLogger(__name__)


def encrypt_credentials(plain: str, *, encryption_key: str) -> str:
    if not encryption_key.strip():
        return plain
    from cryptography.fernet import Fernet

    f = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
    return f.encrypt(plain.encode()).decode()


def decrypt_credentials(stored: str, *, encryption_key: str) -> str:
    if not encryption_key.strip():
        return stored
    from cryptography.fernet import Fernet

    f = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
    try:
        return f.decrypt(stored.encode()).decode()
    except Exception:
        logger.warning("credential decrypt failed; returning as-is")
        return stored
