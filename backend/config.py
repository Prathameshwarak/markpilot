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

    # Market data provider selection: "mock" (default, deterministic) or "kotak" (live).
    MARKET_DATA_PROVIDER = os.environ.get("MARKET_DATA_PROVIDER", "mock").strip().lower()

    # Kotak Neo (read-only). Only the variables required by the CURRENT Kotak Neo API
    # (kotakneoapi v3) auth flow are treated as required:
    #   consumer_key -> totp_login(mobile_number, ucc, totp) -> totp_validate(mpin)
    KOTAK_CONSUMER_KEY = os.environ.get("KOTAK_CONSUMER_KEY", "")
    KOTAK_MOBILE = os.environ.get("KOTAK_MOBILE", "")
    KOTAK_UCC = os.environ.get("KOTAK_UCC", "")
    KOTAK_MPIN = os.environ.get("KOTAK_MPIN", "")
    KOTAK_TOTP_SECRET = os.environ.get("KOTAK_TOTP_SECRET", "")
    KOTAK_ENVIRONMENT = os.environ.get("KOTAK_ENVIRONMENT", "prod").strip().lower()
    # Retained for forward-compat but NOT required by the current auth flow:
    KOTAK_API_KEY = os.environ.get("KOTAK_API_KEY", "")
    KOTAK_API_SECRET = os.environ.get("KOTAK_API_SECRET", "")
    KOTAK_CONSUMER_SECRET = os.environ.get("KOTAK_CONSUMER_SECRET", "")

    # Broker / notifications (config-ready only)
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

    # Cache TTLs (seconds)
    QUOTE_CACHE_TTL = 5
    HISTORICAL_CACHE_TTL = 900
    INSTRUMENT_CACHE_TTL = 86400

    @staticmethod
    def kotak_required_keys() -> list[str]:
        return ["KOTAK_CONSUMER_KEY", "KOTAK_MOBILE", "KOTAK_UCC", "KOTAK_MPIN", "KOTAK_TOTP_SECRET"]

    def kotak_configured(self) -> bool:
        return all(getattr(self, k) for k in self.kotak_required_keys())


settings = Settings()
