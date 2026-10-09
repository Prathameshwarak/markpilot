"""Background refresh scheduler for MarketPilot market data."""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from config import settings
import market_status
import services

logger = logging.getLogger("marketpilot.scheduler")
IST = ZoneInfo("Asia/Kolkata")

async def run_scheduler(stop: asyncio.Event) -> None:
    last_history_refresh = 0.0
    last_retry = 0.0
    loop = asyncio.get_running_loop()
    logger.info("Market data refresh scheduler started (quote interval=%ss).", settings.MARKET_DATA_REFRESH_SECONDS)
    while not stop.is_set():
        now = datetime.now(IST)
        status = market_status.market_status(now)
        import time
        monotonic = time.monotonic()
        try:
            if status["status"] == "OPEN":
                if services.DATA_SOURCE == "kotak":
                    await asyncio.to_thread(services.refresh_live_quotes)
                    if monotonic - last_history_refresh >= settings.HISTORY_REFRESH_SECONDS:
                        # rebuild clears provider caches and recalculates daily indicators;
                        # do this much less often than quote polling.
                        await asyncio.to_thread(services.rebuild)
                        last_history_refresh = monotonic
                elif monotonic - last_retry >= settings.LIVE_RETRY_SECONDS:
                    await asyncio.to_thread(services.rebuild)
                    last_retry = monotonic
            elif services.DATA_SOURCE == "kotak" and not status.get("is_weekend") and not status.get("is_holiday") and now.hour >= 15 and last_history_refresh == 0:
                await asyncio.to_thread(services.rebuild)
                last_history_refresh = monotonic
        except Exception:
            logger.exception("Market data scheduler iteration failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=settings.MARKET_DATA_REFRESH_SECONDS)
        except asyncio.TimeoutError:
            pass
    logger.info("Market data refresh scheduler stopped.")
