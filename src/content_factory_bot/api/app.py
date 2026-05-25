from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from content_factory_bot.api.health import run_health_checks
from content_factory_bot.api.oauth import router as oauth_router
from content_factory_bot.config import get_settings
from content_factory_bot.db.schema import ensure_schema
from content_factory_bot.db.session import get_engine, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db(settings.database_url)
    await ensure_schema()
    yield


app = FastAPI(title="Content Factory API", lifespan=lifespan)
app.include_router(oauth_router)


@app.get("/health")
async def health() -> JSONResponse:
    settings = get_settings()
    report = await run_health_checks(settings, get_engine())
    return JSONResponse(content=report.as_dict(), status_code=report.http_status)
