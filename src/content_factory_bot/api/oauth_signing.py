import hashlib
import hmac
import time
from urllib.parse import urlencode


def _sign_payload(secret: str, telegram_user_id: int, provider: str, expires: int) -> str:
    payload = f"{telegram_user_id}:{provider}:{expires}"
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def verify_oauth_start(
    *,
    secret: str,
    telegram_user_id: int,
    provider: str,
    expires: int,
    sig: str,
) -> bool:
    if int(time.time()) > expires:
        return False
    expected = _sign_payload(secret, telegram_user_id, provider, expires)
    return hmac.compare_digest(expected, sig)


def build_start_url(
    *,
    public_base_url: str,
    secret: str,
    telegram_user_id: int,
    provider: str,
    ttl_seconds: int = 900,
) -> str:
    if not secret:
        raise ValueError("OAUTH_STATE_SECRET is required for OAuth start links")
    base = public_base_url.rstrip("/")
    expires = int(time.time()) + ttl_seconds
    sig = _sign_payload(secret, telegram_user_id, provider, expires)
    qs = urlencode({"uid": telegram_user_id, "exp": expires, "sig": sig})
    return f"{base}/oauth/{provider}/start?{qs}"
