"""MarketPilot backend entrypoint."""
from config import settings  # loads .env first
from scheduler import run_scheduler

import asyncio
import logging
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from db import client, create_indexes
from auth import router as auth_router, seed_users
from routes.equities import router as equities_router
from routes.monitoring import router as monitoring_router
from routes.alerts import router as alerts_router
from routes.system import router as system_router
from routes.notifications import router as notifications_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("marketpilot")

app = FastAPI(title="MarketPilot API", version="0.3.0")
_scheduler_stop = None
_scheduler_task = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(equities_router)
app.include_router(monitoring_router)
app.include_router(alerts_router)
app.include_router(system_router)
app.include_router(notifications_router)


@app.get("/api/health")
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "marketpilot"}


@app.on_event("startup")
async def on_startup():
    global _scheduler_stop, _scheduler_task
    await create_indexes()
    await seed_users()
    _scheduler_stop = asyncio.Event()
    _scheduler_task = asyncio.create_task(run_scheduler(_scheduler_stop))
    logger.info("MarketPilot backend started (universe + ideas cached; refresh scheduler enabled).")


@app.on_event("shutdown")
async def on_shutdown():
    global _scheduler_stop, _scheduler_task
    if _scheduler_stop is not None:
        _scheduler_stop.set()
    if _scheduler_task is not None:
        try:
            await asyncio.wait_for(_scheduler_task, timeout=5)
        except Exception:
            _scheduler_task.cancel()
    client.close()
