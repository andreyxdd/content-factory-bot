"""Download Telegram file bytes via Bot API."""

from aiogram import Bot


async def download_file_bytes(bot: Bot, file_id: str) -> bytes:
    file = await bot.get_file(file_id)
    if not file.file_path:
        raise ValueError("Telegram file has no path")
    buf = await bot.download_file(file.file_path)
    if hasattr(buf, "read"):
        return buf.read()
    return bytes(buf)
