import uvicorn


def run() -> None:
    uvicorn.run(
        "content_factory_bot.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
