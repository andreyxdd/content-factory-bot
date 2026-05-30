from content_factory_bot.handlers.onboarding import _confirm_edit_fork_kb, _edit_field_kb
from content_factory_bot.services.onboarding_engine import S2_KEYS, S4_KEYS, editable_fields_for_confirm


def _callback_data_set(markup) -> set[str]:
    out: set[str] = set()
    for row in markup.inline_keyboard:
        for btn in row:
            if btn.callback_data:
                out.add(btn.callback_data)
    return out


def test_editable_fields_for_s2_confirm_excludes_future_sections() -> None:
    keys = {field.key for field in editable_fields_for_confirm("s2_confirm")}
    assert keys == set(S2_KEYS)
    assert "s4_beliefs" not in keys
    assert "s5_reader_phrase" not in keys


def test_editable_fields_for_s4_confirm_excludes_s5() -> None:
    keys = {field.key for field in editable_fields_for_confirm("s4_confirm")}
    assert keys == set(S2_KEYS + S4_KEYS)
    assert "s5_reader_phrase" not in keys


def test_edit_field_kb_s2_confirm_shows_only_s2_callbacks() -> None:
    callbacks = _callback_data_set(_edit_field_kb("en", "s2_confirm"))
    assert "onb:edit:s2_about" in callbacks
    assert "onb:edit:s2_goals" in callbacks
    assert "onb:edit:s4_beliefs" not in callbacks
    assert "onb:edit:s5_voice_betrayal" not in callbacks
    assert "onb:nav:back" in callbacks


def test_confirm_edit_fork_kb_s2_has_expected_actions() -> None:
    callbacks = _callback_data_set(_confirm_edit_fork_kb("s2_confirm", "en"))
    assert "onb:s2_confirm:edit_fields" in callbacks
    assert "onb:s2_confirm:continue_questions" in callbacks
    assert "onb:edit:s2_about" not in callbacks
