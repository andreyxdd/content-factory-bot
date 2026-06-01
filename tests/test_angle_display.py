from content_factory_bot.services.draft import AngleOption


def test_angle_display_block_uses_html_without_separators() -> None:
    angle = AngleOption(
        id="A",
        format="story",
        hook="A hook line.",
        preview="Preview body text.",
    )
    text = angle.display_block("en")
    assert "─" not in text
    assert "═" not in text
    assert "HOOK:" not in text
    assert "<b>Angle A · story</b>" in text
    assert "<b>A hook line.</b>" in text
    assert "Preview body text." in text


def test_angle_display_block_russian_heading() -> None:
    angle = AngleOption(
        id="B",
        format="conflict",
        hook="Хук.",
        preview="Текст.",
    )
    text = angle.display_block("ru")
    assert "<b>Угол B · conflict</b>" in text
