"""MarketPilot backend entrypoint."""
from config import settings  # loads .env first

import logging
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from db import client, create_indexes
from auth import router as auth_router, seed_users
from routes.equities import router as equities_router
from routes.monitoring import router as monitoring_router
from routes.alerts import router as alerts_router
from routes.system import router as system_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("marketpilot")

app = FastAPI(title="MarketPilot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list({settings.FRONTEND_URL, "http://localhost:3000"}),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(equities_router)
app.include_router(monitoring_router)
app.include_router(alerts_router)
app.include_router(system_router)


@app.get("/api/health")
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "marketpilot"}


@app.on_event("startup")
async def on_startup():
    await create_indexes()
    await seed_users()
    logger.info("MarketPilot backend started (universe + ideas cached).")


@app.on_event("shutdown")
async def on_shutdown():
    client.close()
