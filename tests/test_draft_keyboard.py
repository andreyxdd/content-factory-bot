from content_factory_bot.keyboards.draft import draft_options_keyboard


def test_draft_options_keyboard_single_column() -> None:
    kb = draft_options_keyboard(1, 2, ["One", "Two", "Three"], "en")
    assert len(kb.inline_keyboard) == 4
    for row in kb.inline_keyboard:
        assert len(row) == 1
