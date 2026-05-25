from cryptography.fernet import Fernet

from content_factory_bot.services.credentials import decrypt_credentials, encrypt_credentials


def test_roundtrip_with_key() -> None:
    fernet_key = Fernet.generate_key().decode()
    plain = "token-abc-123"
    enc = encrypt_credentials(plain, encryption_key=fernet_key)
    assert enc != plain
    assert decrypt_credentials(enc, encryption_key=fernet_key) == plain


def test_passthrough_without_key() -> None:
    plain = "dev-token"
    assert encrypt_credentials(plain, encryption_key="") == plain
    assert decrypt_credentials(plain, encryption_key="") == plain
