from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from auth import get_current_user
from brokers.registry import get_kotak_adapter
from config import settings
import services

router = APIRouter(prefix="/api", tags=["system", "settings"])


async def _db_status() -> str:
    try:
        from db import db
        await db.command("ping")
        return "CONNECTED"
    except Exception:
        return "ERROR"


def _market_data_status() -> str:
    ds = services.DATA_SOURCE
    if ds == "kotak":
        return "KOTAK"
    if ds == "mock":
        return "MOCK"
    return "ERROR"


@router.get("/system/status")
async def system_status():
    broker = get_kotak_adapter().health_check()
    ps = services.provider_status()
    return {
        "status": "ok",
        "application": "HEALTHY",
        "version": "0.2.0",
        "database": await _db_status(),
        "market_data": _market_data_status(),
        "data_source": ps["data_source"],
        "data_quality": ps["data_quality"],
        "last_market_data_timestamp": ps["last_market_data_timestamp"],
        "market_data_error": ps["last_error"],
        "failed_symbols": ps["failed_symbols"],
        "market_data_stale": ps["data_source"] == "mock",
        "kotak": broker["status"],
        "broker": broker,
        "scheduler": "READY",
        "telegram": {"configured": bool(settings.TELEGRAM_BOT_TOKEN), "enabled": False},
        "regime": services.current_regime()["regime"],
        "universe_size": len(services.EQUITIES),
        "modules": {"fno": "coming_soon", "equity": "active", "monitoring": "active"},
    }


@router.get("/broker/kotak/status")
async def kotak_status(user: dict = Depends(get_current_user)):
    # Sanitized health only — never returns credentials or tokens.
    return get_kotak_adapter().health_check()


@router.get("/broker/kotak/market-data-check")
async def kotak_market_data_check(user: dict = Depends(get_current_user)):
    """Read-only validation: one NIFTY history call + one quote using the consumer key.
    Returns sanitized facts only (no credentials, tokens or session ids)."""
    return await run_in_threadpool(get_kotak_adapter().validate_market_data)


@router.post("/broker/kotak/test-connection")
async def kotak_test_connection(user: dict = Depends(get_current_user)):
    adapter = get_kotak_adapter()
    result = await run_in_threadpool(adapter.authenticate)
    # Only rebuild market data when the session was genuinely verified (authenticate()
    # now checks the SDK response payloads, not just the absence of exceptions).
    market = None
    if result.get("connected") and result.get("status") == "CONNECTED":
        market = await run_in_threadpool(services.rebuild)
    # Only the sanitized fields are returned to the client.
    return {
        "connected": result.get("connected", False),
        "status": result.get("status"),
        "message": result.get("message"),
        "timestamp": result.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "market_data": market,
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
