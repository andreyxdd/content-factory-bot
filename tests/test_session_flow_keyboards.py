from content_factory_bot.keyboards.session_flow import finalize_keyboard, setup_keyboard


def test_setup_keyboard_has_three_rows() -> None:
    kb = setup_keyboard("en", research=True, cover=False)
    assert len(kb.inline_keyboard) == 3


def test_finalize_keyboard_save_first() -> None:
    kb = finalize_keyboard(1, "en")
    assert "fin:save" in kb.inline_keyboard[0][0].callback_data
