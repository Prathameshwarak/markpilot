"""Pydantic models. ObjectId is mapped to a string id via BaseDocument."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Annotated, Any, Literal
from pydantic import BaseModel, Field, BeforeValidator, EmailStr, ConfigDict
from bson import ObjectId


def _to_str_id(v: Any) -> Any:
    if isinstance(v, ObjectId):
        return str(v)
    return v


PyObjectId = Annotated[str, BeforeValidator(_to_str_id)]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BaseDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    @classmethod
    def from_mongo(cls, doc: dict):
        if not doc:
            return None
        return cls(**doc)

    def to_mongo(self) -> dict:
        data = self.model_dump(by_alias=True, exclude_none=True)
        data.pop("_id", None)
        return data


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=80)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


# ---------- Domain (request/response payloads) ----------
class MonitorEventOut(BaseModel):
    type: str
    message: str
    timestamp: str
    old_stop: Optional[float] = None
    new_stop: Optional[float] = None
    reason: Optional[str] = None
    price: Optional[float] = None


class JournalEntryIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    setup: str = Field(default="Swing")
    direction: Literal["bullish", "bearish"] = "bullish"
    entry_price: float = Field(gt=0)
    exit_price: Optional[float] = Field(default=None, gt=0)
    quantity: int = Field(default=1, ge=1)
    entry_date: Optional[str] = None
    exit_date: Optional[str] = None
    outcome: Literal["win", "loss", "open"] = "open"
    notes: Optional[str] = ""


class SettingsIn(BaseModel):
    max_risk_pct: float = Field(default=1.5, ge=0.1, le=10)
    stop_buffer_pct: float = Field(default=0.5, ge=0, le=10)
    max_open_positions: int = Field(default=5, ge=1, le=50)
    telegram_enabled: bool = False
    telegram_chat_id: Optional[str] = ""
    in_app_notifications: bool = True
    persona: str = Field(default="Swing Trader")
