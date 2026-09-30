from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from db import db
from auth import get_current_user
from models import JournalEntryIn

router = APIRouter(prefix="/api", tags=["alerts", "journal"])


@router.get("/alerts")
async def list_alerts(user: dict = Depends(get_current_user)):
    docs = await db.alerts.find({"user_id": str(user["_id"])}).sort("timestamp", -1).to_list(100)
    for d in docs:
        d["id"] = str(d.pop("_id"))
        d.pop("user_id", None)
    return {"count": len(docs), "alerts": docs}


@router.post("/alerts/{alert_id}/read")
async def mark_read(alert_id: str, user: dict = Depends(get_current_user)):
    from bson import ObjectId
    await db.alerts.update_one({"_id": ObjectId(alert_id), "user_id": str(user["_id"])}, {"$set": {"read": True}})
    return {"message": "ok"}


@router.get("/journal")
async def list_journal(user: dict = Depends(get_current_user)):
    docs = await db.journal_entries.find({"user_id": str(user["_id"])}).sort("created_at", -1).to_list(200)
    for d in docs:
        d["id"] = str(d.pop("_id"))
        d.pop("user_id", None)
    wins = sum(1 for d in docs if d.get("outcome") == "win")
    closed = [d for d in docs if d.get("outcome") in ("win", "loss")]
    pnl = sum(((d.get("exit_price") or 0) - d["entry_price"]) * d.get("quantity", 1)
              * (1 if d.get("direction", "bullish") == "bullish" else -1) for d in closed)
    metrics = {
        "total": len(docs),
        "win_rate": round(wins / len(closed) * 100, 1) if closed else 0,
        "total_pnl": round(pnl, 2),
        "closed": len(closed),
    }
    return {"metrics": metrics, "entries": docs}


@router.post("/journal")
async def add_journal(body: JournalEntryIn, user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    doc = body.model_dump()
    doc.update({"user_id": str(user["_id"]), "created_at": now})
    res = await db.journal_entries.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    doc.pop("_id", None)
    doc.pop("user_id", None)
    return doc
