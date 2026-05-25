from content_factory_bot.config import Settings


def test_parsed_allowlist() -> None:
    s = Settings(
        BOT_TOKEN="x",
        ALLOWLIST_TELEGRAM_IDS="1, 2 ,3",
    )
    assert s.parsed_allowlist() == frozenset({1, 2, 3})
