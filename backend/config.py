"""Centralised, env-driven configuration. No secrets are hardcoded."""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")


class Settings:
    # Core
    MONGO_URL = os.environ["MONGO_URL"]
    DB_NAME = os.environ["DB_NAME"]
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    # Auth
    JWT_SECRET = os.environ.get("JWT_SECRET", "")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_MINUTES = 15
    REFRESH_TOKEN_DAYS = 7
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
    DEMO_EMAIL = os.environ.get("DEMO_EMAIL", "demo@marketpilot.in")
    DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "Demo1234!")

    # Risk / trade-idea rules (configurable)
    ATR_STOP_MULTIPLIER = 2.0
    ATR_TRAIL_MULTIPLIER = 2.0
    TARGET1_R = 1.0
    TARGET2_R = 2.0

    # Broker / notifications (config-ready only in V1)
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


settings = Settings()
