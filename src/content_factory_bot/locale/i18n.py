import json
from functools import lru_cache
from pathlib import Path

SUPPORTED = frozenset({"en", "ru"})
_DEFAULT = "en"
_LOCALE_DIR = Path(__file__).parent


@lru_cache
def _load(lang: str) -> dict[str, str]:
    path = _LOCALE_DIR / f"{lang}.json"
    if not path.exists():
        path = _LOCALE_DIR / f"{_DEFAULT}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_language(lang: str | None) -> str:
    if lang and lang.lower() in SUPPORTED:
        return lang.lower()
    return _DEFAULT


def t(key: str, lang: str | None) -> str:
    data = _load(normalize_language(lang))
    return data.get(key, _load(_DEFAULT).get(key, key))
