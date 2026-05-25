from contextlib import asynccontextmanager

from fastapi import FastAPI

from content_factory_bot.api.oauth import router as oauth_router
from content_factory_bot.config import get_settings
from content_factory_bot.db.session import create_tables, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db(settings.database_url)
    await create_tables()
    yield


app = FastAPI(title="Content Factory API", lifespan=lifespan)
app.include_router(oauth_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
