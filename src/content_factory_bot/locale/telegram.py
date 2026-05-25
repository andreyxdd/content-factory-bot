"""Map Telegram client language to bot UI locale (v1: en | ru only)."""


def ui_lang_from_telegram(language_code: str | None) -> str:
    """Russian UI for `ru` / `rus` / `ru-*`; English for everything else."""
    if not language_code:
        return "en"
    code = language_code.strip().lower().replace("_", "-")
    if code == "ru" or code == "rus" or code.startswith("ru-"):
        return "ru"
    return "en"
