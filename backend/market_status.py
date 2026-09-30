"""NSE market-status service. Timezone-aware (Asia/Kolkata) regardless of server TZ.

Holiday support is stubbed so exchange holidays can be added later without a rewrite.
"""
from __future__ import annotations
from datetime import datetime, time
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

PRE_OPEN_START = time(9, 0)
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)

# Extend with NSE trading holidays (YYYY-MM-DD) later.
HOLIDAYS: set[str] = set()


def market_status(now: datetime | None = None) -> dict:
    now = now.astimezone(IST) if now else datetime.now(IST)
    is_weekend = now.weekday() >= 5
    is_holiday = now.strftime("%Y-%m-%d") in HOLIDAYS
    t = now.time()

    if is_weekend or is_holiday:
        status = "CLOSED"
    elif PRE_OPEN_START <= t < MARKET_OPEN:
        status = "PRE_MARKET"
    elif MARKET_OPEN <= t < MARKET_CLOSE:
        status = "OPEN"
    else:
        status = "CLOSED"

    return {
        "status": status,
        "timezone": "Asia/Kolkata",
        "server_time_ist": now.isoformat(),
        "is_weekend": is_weekend,
        "is_holiday": is_holiday,
    }
