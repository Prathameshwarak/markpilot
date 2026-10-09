"""Notification preferences + Telegram test. The bot token is server-side only and is
never returned by any endpoint.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends

from auth import get_current_user
from config import settings
from db import db
from models import NotificationSettingsIn
from telegram import send_telegram_message

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

_NOTIF_KEYS = ["telegram_enabled", "telegram_chat_id", "alert_entry", "alert_stop",
               "alert_target", "alert_trailing", "alert_regime", "daily_summary"]


def _defaults() -> dict:
    d = NotificationSettingsIn().model_dump()
    return d


@router.get("/settings")
async def get_notification_settings(user: dict = Depends(get_current_user)):
    doc = await db.user_settings.find_one({"user_id": str(user["_id"])}) or {}
    out = _defaults()
    for k in _NOTIF_KEYS:
        if k in doc:
            out[k] = doc[k]
    # Server-side capability flag — the token itself is NEVER exposed.
    out["telegram_bot_configured"] = settings.telegram_configured()
    return out


@router.put("/settings")
async def update_notification_settings(body: NotificationSettingsIn, user: dict = Depends(get_current_user)):
    clean = body.model_dump()
    await db.user_settings.update_one({"user_id": str(user["_id"])}, {"$set": clean}, upsert=True)
    clean["telegram_bot_configured"] = settings.telegram_configured()
    return clean


@router.post("/telegram/test")
async def test_telegram(body: dict = None, user: dict = Depends(get_current_user)):
    body = body or {}
    chat_id = body.get("telegram_chat_id")
    if not chat_id:
        doc = await db.user_settings.find_one({"user_id": str(user["_id"])}) or {}
        chat_id = doc.get("telegram_chat_id", "")
    result = await send_telegram_message(chat_id, "✅ MarketPilot test notification. Alerts are wired up.")
    return result
