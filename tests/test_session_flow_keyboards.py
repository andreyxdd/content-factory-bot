from content_factory_bot.keyboards.session_flow import finalize_keyboard, setup_keyboard


def test_setup_keyboard_has_start_row() -> None:
    kb = setup_keyboard("en", research=True, cover=False)
    assert kb.inline_keyboard[-1][0].callback_data == "cs:start"
    assert any(
        btn.callback_data == "cs:setup:instructions"
        for row in kb.inline_keyboard
        for btn in row
    )


def test_setup_keyboard_clear_when_instructions_set() -> None:
    kb = setup_keyboard("en", research=True, cover=False, has_instructions=True)
    instruction_row = next(
        row
        for row in kb.inline_keyboard
        if any(btn.callback_data == "cs:setup:instructions" for btn in row)
    )
    assert len(instruction_row) == 2
    assert instruction_row[0].callback_data == "cs:setup:instructions"
    assert instruction_row[1].callback_data == "cs:setup:clear_instructions"


def test_finalize_keyboard_save_first() -> None:
    kb = finalize_keyboard(1, "en")
    assert "fin:save" in kb.inline_keyboard[0][0].callback_data
