"""Server-side Telegram sender. TELEGRAM_BOT_TOKEN never leaves the backend and is
never logged. Missing token degrades gracefully (no crash).
"""
from __future__ import annotations
import logging
import httpx

from config import settings

logger = logging.getLogger("marketpilot.telegram")

NOT_CONFIGURED_MSG = "Telegram bot is not configured on this server."


async def send_telegram_message(chat_id: str, text: str) -> dict:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return {"sent": False, "configured": False, "message": NOT_CONFIGURED_MSG}
    if not chat_id:
        return {"sent": False, "configured": True, "message": "No Telegram Chat ID set."}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )
        if resp.status_code == 200 and resp.json().get("ok"):
            return {"sent": True, "configured": True, "message": "Test notification sent to Telegram."}
        return {"sent": False, "configured": True,
                "message": "Telegram rejected the request. Check the Chat ID."}
    except Exception as e:  # never log the token
        logger.error("Telegram send failed: %s", type(e).__name__)
        return {"sent": False, "configured": True, "message": "Could not reach Telegram."}
