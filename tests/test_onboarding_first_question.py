from content_factory_bot.handlers.onboarding import _ready_kb


def _button_map(kb) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in kb.inline_keyboard:
        for btn in row:
            if btn.callback_data:
                out[btn.callback_data] = btn.text
    return out


def test_ready_keyboard_has_continue_cancel_help_only() -> None:
    kb = _ready_kb("en")
    mapping = _button_map(kb)
    assert "onb:ready:yes" in mapping
    assert mapping["onb:ready:yes"] == "✅ Continue"
    assert "onb:nav:cancel" in mapping
    assert mapping["onb:nav:cancel"] == "⏸️ Pause"
    assert "onb:nav:help" in mapping
    assert "onb:nav:back" not in mapping
    assert "onb:ready:no" not in mapping
