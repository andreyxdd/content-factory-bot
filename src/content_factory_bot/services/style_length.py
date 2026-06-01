"""Map Style Card length band to soft character ranges."""

from __future__ import annotations

import re


def length_band_from_style_card(style_card: str) -> str:
    text = style_card.lower()
    if "ru" in text or "корот" in text or "short" in text:
        if "длин" in text or "long" in text:
            pass
        elif "корот" in text or "short" in text:
            return "short"
    if re.search(r"\bдлинн", text) or re.search(r"\blong\b", text):
        return "long"
    if re.search(r"\bсредн", text) or re.search(r"\bmedium\b", text):
        return "medium"
    if re.search(r"\bкорот", text) or re.search(r"\bshort\b", text):
        return "short"
    return "medium"


def char_range_for_band(band: str) -> tuple[int, int]:
    bands = {
        "short": (400, 900),
        "medium": (900, 1800),
        "long": (1800, 3500),
    }
    return bands.get(band, bands["medium"])
