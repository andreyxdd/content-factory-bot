from content_factory_bot.locale.telegram import ui_lang_from_telegram


def test_russian_codes() -> None:
    for code in ("ru", "RU", "rus", "ru-RU", "ru_BY"):
        assert ui_lang_from_telegram(code) == "ru"


def test_english_fallback() -> None:
    assert ui_lang_from_telegram("en") == "en"
    assert ui_lang_from_telegram("de") == "en"
    assert ui_lang_from_telegram(None) == "en"
    assert ui_lang_from_telegram("") == "en"
