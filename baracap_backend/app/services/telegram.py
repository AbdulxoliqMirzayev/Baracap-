from __future__ import annotations

import requests

from app.config import settings


class TelegramNotConfiguredError(RuntimeError):
    pass


def send_telegram_message(text: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        raise TelegramNotConfiguredError("Telegram bot token yoki chat id sozlanmagan")

    response = requests.post(
        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=12,
    )
    response.raise_for_status()
    return True
