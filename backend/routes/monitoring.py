from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from bson import ObjectId

import services
from db import db
from auth import get_current_user
from engine.monitoring import evaluate

router = APIRouter(prefix="/api", tags=["ideas", "monitoring"])


@router.get("/trade-ideas")
async def trade_ideas():
    ideas = sorted(services.IDEAS.values(), key=lambda i: i["score"], reverse=True)
    return {"count": len(ideas), "ideas": ideas}


@router.get("/trade-ideas/{idea_id}")
async def trade_idea(idea_id: str):
    idea = services.IDEAS.get(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Trade idea not found")
    return idea


def _public_session(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    doc.pop("user_id", None)
    return doc


@router.post("/trade-ideas/{idea_id}/monitor")
async def monitor_idea(idea_id: str, user: dict = Depends(get_current_user)):
    idea = services.IDEAS.get(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Trade idea not found")
    existing = await db.monitoring_sessions.find_one(
        {"user_id": str(user["_id"]), "idea_id": idea_id, "status": {"$nin": ["CLOSED", "STOP_LOSS_HIT", "T2_HIT"]}})
    if existing:
        raise HTTPException(status_code=400, detail="Already monitoring this idea")
    now = datetime.now(timezone.utc).isoformat()
    session = {
        "user_id": str(user["_id"]), "idea_id": idea_id, "symbol": idea["symbol"],
        "company": idea["company"], "direction": idea["direction"], "entry": idea["entry"],
        "original_stop": idea["stop_loss"], "current_stop": idea["stop_loss"],
        "target1": idea["target1"], "target2": idea["target2"], "atr": idea["atr"],
        "score": idea["score"], "status": "MONITORING", "created_at": now, "last_updated": now,
        "events": [{"type": "MONITORING_STARTED", "message": f"Started monitoring {idea['symbol']}",
                    "timestamp": now}],
    }
    res = await db.monitoring_sessions.insert_one(session)
    session["_id"] = res.inserted_id
    await db.alerts.insert_one({
        "user_id": str(user["_id"]), "type": "MONITORING_STARTED", "symbol": idea["symbol"],
        "message": f"You are now monitoring {idea['symbol']}", "timestamp": now, "read": False,
    })
    return _public_session(session)


@router.get("/monitoring")
async def list_monitoring(user: dict = Depends(get_current_user)):
    docs = await db.monitoring_sessions.find({"user_id": str(user["_id"])}).sort("created_at", -1).to_list(200)
    return {"count": len(docs), "sessions": [_public_session(d) for d in docs]}


@router.get("/monitoring/{session_id}")
async def get_monitoring(session_id: str, user: dict = Depends(get_current_user)):
    doc = await db.monitoring_sessions.find_one({"_id": ObjectId(session_id), "user_id": str(user["_id"])})
    if not doc:
        raise HTTPException(status_code=404, detail="Monitoring session not found")
    return _public_session(doc)


@router.post("/monitoring/{session_id}/refresh")
async def refresh_monitoring(session_id: str, user: dict = Depends(get_current_user)):
    """Re-evaluate a session against the latest (mock) quote and record any events."""
    doc = await db.monitoring_sessions.find_one({"_id": ObjectId(session_id), "user_id": str(user["_id"])})
    if not doc:
        raise HTTPException(status_code=404, detail="Monitoring session not found")
    eq = services.EQUITIES.get(doc["symbol"])
    price = eq["price"] if eq else doc["entry"]
    result = evaluate(doc["direction"], doc["entry"], doc["current_stop"], doc["target1"],
                      doc["target2"], doc["status"], price, doc.get("atr") or price * 0.02)
    now = datetime.now(timezone.utc).isoformat()
    if result["events"]:
        await db.monitoring_sessions.update_one(
            {"_id": doc["_id"]},
            {"$set": {"status": result["status"], "current_stop": result["current_stop"], "last_updated": now},
             "$push": {"events": {"$each": result["events"]}}})
        for ev in result["events"]:
            await db.alerts.insert_one({"user_id": str(user["_id"]), "type": ev["type"],
                                        "symbol": doc["symbol"], "message": ev["message"],
                                        "timestamp": ev["timestamp"], "read": False})
    updated = await db.monitoring_sessions.find_one({"_id": doc["_id"]})
    return {"current_price": price, "new_events": result["events"], "session": _public_session(updated)}


@router.post("/monitoring/{session_id}/close")
async def close_monitoring(session_id: str, user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    res = await db.monitoring_sessions.update_one(
        {"_id": ObjectId(session_id), "user_id": str(user["_id"])},
        {"$set": {"status": "CLOSED", "last_updated": now},
         "$push": {"events": {"type": "CLOSED", "message": "Monitoring closed by user", "timestamp": now}}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Monitoring session not found")
    return {"message": "Monitoring closed", "status": "CLOSED"}
