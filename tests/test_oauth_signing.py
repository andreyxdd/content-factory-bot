import time

from content_factory_bot.api.oauth_signing import build_start_url, verify_oauth_start


def test_build_and_verify_start_url() -> None:
    secret = "test-secret"
    url = build_start_url(
        public_base_url="https://example.com",
        secret=secret,
        telegram_user_id=42,
        provider="instagram",
    )
    assert url.startswith("https://example.com/oauth/instagram/start?")
    assert "uid=42" in url


def test_verify_rejects_expired() -> None:
    secret = "test-secret"
    exp = int(time.time()) - 10
    import hashlib
    import hmac as hmac_mod

    payload = f"42:instagram:{exp}"
    sig = hmac_mod.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    assert (
        verify_oauth_start(
            secret=secret,
            telegram_user_id=42,
            provider="instagram",
            expires=exp,
            sig=sig,
        )
        is False
    )
