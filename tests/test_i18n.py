from content_factory_bot.locale.i18n import normalize_language, t


def test_normalize_language() -> None:
    assert normalize_language("ru") == "ru"
    assert normalize_language("EN") == "en"
    assert normalize_language("de") == "en"


def test_translate() -> None:
    assert "Welcome" in t("welcome", "en")
    assert "Добро" in t("welcome", "ru")
