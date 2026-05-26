"""OAuth start/callback routes for Instagram and LinkedIn."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from content_factory_bot.api.oauth_signing import verify_oauth_start
from content_factory_bot.config import get_settings
from content_factory_bot.db.models import Creator, ProviderKind
from content_factory_bot.locale.i18n import t
from content_factory_bot.services.telegram_notify import notify_creator

router = APIRouter(prefix="/oauth", tags=["oauth"])


async def _creator_lang(db, uid: int) -> str:
    row = await db.get(Creator, uid)
    return row.primary_language if row else "en"


async def _notify_oauth_result(*, uid: int, provider: str, ok: bool, detail: str = "") -> None:
    if uid <= 0:
        return
    from content_factory_bot.db.session import session_scope

    async with session_scope() as session:
        lang = await _creator_lang(session, uid)
    if ok:
        text = t("providers_oauth_success", lang).format(provider=provider)
    else:
        text = t("providers_oauth_failed", lang).format(provider=provider, error=detail)
    await notify_creator(uid, text)


def _require_public_base() -> str:
    settings = get_settings()
    if not settings.public_base_url.strip():
        raise HTTPException(503, "PUBLIC_BASE_URL is not configured")
    return settings.public_base_url.rstrip("/")


def _verify_start_query(provider: str, uid: int, exp: int, sig: str) -> None:
    settings = get_settings()
    if not settings.oauth_state_secret:
        raise HTTPException(503, "OAUTH_STATE_SECRET is not configured")
    if not verify_oauth_start(
        secret=settings.oauth_state_secret,
        telegram_user_id=uid,
        provider=provider,
        expires=exp,
        sig=sig,
    ):
        raise HTTPException(403, "Invalid or expired link")


@router.get("/instagram/start")
async def instagram_start(
    uid: int = Query(..., description="Telegram user id"),
    exp: int = Query(...),
    sig: str = Query(...),
) -> RedirectResponse:
    _verify_start_query(ProviderKind.INSTAGRAM, uid, exp, sig)
    settings = get_settings()
    if not settings.meta_app_id:
        raise HTTPException(503, "META_APP_ID is not configured")
    base = _require_public_base()
    redirect_uri = f"{base}/oauth/instagram/callback"
    # Phase 4: full Meta OAuth URL; stub redirects to callback doc page
    return RedirectResponse(
        url=(
            "https://www.facebook.com/v21.0/dialog/oauth"
            f"?client_id={settings.meta_app_id}"
            f"&redirect_uri={redirect_uri}"
            "&scope=instagram_basic,instagram_content_publish"
            f"&state={uid}"
        )
    )


@router.get("/instagram/callback")
async def instagram_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> HTMLResponse:
    if error:
        uid = int(state) if state and state.isdigit() else 0
        await _notify_oauth_result(uid=uid, provider=ProviderKind.INSTAGRAM, ok=False, detail=error)
        return HTMLResponse(f"<p>Instagram connect failed: {error}</p>", status_code=400)
    if not code:
        raise HTTPException(400, "Missing code")
    uid = int(state) if state and state.isdigit() else 0
    if uid:
        from content_factory_bot.db.session import session_scope
        from content_factory_bot.services.providers import upsert_provider_connection

        async with session_scope() as db:
            await upsert_provider_connection(
                db,
                telegram_user_id=uid,
                provider=ProviderKind.INSTAGRAM,
                credentials=f"stub:{code[:16]}",
                status="active",
            )
        await _notify_oauth_result(uid=uid, provider=ProviderKind.INSTAGRAM, ok=True)
    return HTMLResponse(
        "<p>Instagram connected. Return to Telegram. Token stored (exchange stub).</p>"
    )


@router.get("/linkedin/start")
async def linkedin_start(
    uid: int = Query(...),
    exp: int = Query(...),
    sig: str = Query(...),
) -> RedirectResponse:
    _verify_start_query(ProviderKind.LINKEDIN, uid, exp, sig)
    settings = get_settings()
    if not settings.linkedin_client_id:
        raise HTTPException(503, "LINKEDIN_CLIENT_ID is not configured")
    base = _require_public_base()
    redirect_uri = f"{base}/oauth/linkedin/callback"
    return RedirectResponse(
        url=(
            "https://www.linkedin.com/oauth/v2/authorization"
            f"?response_type=code&client_id={settings.linkedin_client_id}"
            f"&redirect_uri={redirect_uri}"
            "&scope=w_member_social"
            f"&state={uid}"
        )
    )


@router.get("/linkedin/callback")
async def linkedin_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> HTMLResponse:
    if error:
        uid = int(state) if state and state.isdigit() else 0
        await _notify_oauth_result(uid=uid, provider=ProviderKind.LINKEDIN, ok=False, detail=error)
        return HTMLResponse(f"<p>LinkedIn connect failed: {error}</p>", status_code=400)
    if not code:
        raise HTTPException(400, "Missing code")
    uid = int(state) if state and state.isdigit() else 0
    if uid:
        from content_factory_bot.db.session import session_scope
        from content_factory_bot.services.providers import upsert_provider_connection

        async with session_scope() as db:
            await upsert_provider_connection(
                db,
                telegram_user_id=uid,
                provider=ProviderKind.LINKEDIN,
                credentials=f"stub:{code[:16]}",
                status="active",
            )
        await _notify_oauth_result(uid=uid, provider=ProviderKind.LINKEDIN, ok=True)
    return HTMLResponse(
        "<p>LinkedIn connected. Return to Telegram. Token stored (exchange stub).</p>"
    )
