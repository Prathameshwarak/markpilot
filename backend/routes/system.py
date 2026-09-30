from fastapi import APIRouter, Depends
from auth import get_current_user
from brokers.kotak_neo import KotakNeoAdapter
from config import settings
import services

router = APIRouter(prefix="/api", tags=["system", "settings"])

_broker = KotakNeoAdapter()


@router.get("/system/status")
async def system_status():
    return {
        "status": "ok",
        "version": "0.1.0",
        "data_provider": "mock",
        "market_data_stale": False,
        "broker": _broker.health_check(),
        "telegram": {"configured": bool(settings.TELEGRAM_BOT_TOKEN), "enabled": False},
        "regime": services.current_regime()["regime"],
        "universe_size": len(services.EQUITIES),
        "modules": {"fno": "coming_soon", "equity": "active", "monitoring": "active"},
    }


@router.get("/settings")
async def get_settings(user: dict = Depends(get_current_user)):
    from db import db
    doc = await db.user_settings.find_one({"user_id": str(user["_id"])})
    if not doc:
        return {"max_risk_pct": 1.5, "stop_buffer_pct": 0.5, "max_open_positions": 5,
                "telegram_enabled": False, "telegram_chat_id": "", "in_app_notifications": True,
                "persona": "Swing Trader"}
    doc.pop("_id", None)
    doc.pop("user_id", None)
    return doc


@router.put("/settings")
async def update_settings(body: dict, user: dict = Depends(get_current_user)):
    from db import db
    from models import SettingsIn
    clean = SettingsIn(**body).model_dump()
    await db.user_settings.update_one({"user_id": str(user["_id"])}, {"$set": clean}, upsert=True)
    return clean
