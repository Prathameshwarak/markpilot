"""Kotak Neo READ-ONLY broker adapter (Milestone 2).

Uses the current Kotak Neo Python SDK (`neo_api_client`, distributed as `kotakneoapi` v3):
    NeoAPI(consumer_key, environment) -> totp_login(mobile_number, ucc, totp) -> totp_validate(mpin)

Market data (quotes / historical_data) only needs the consumer key in this SDK version, so
the TOTP session is used for the Settings connection test but is not a prerequisite for data.

Hard rules enforced here:
- Credentials come ONLY from server-side env vars. Never logged, never returned to the client.
- READ-ONLY: place_order / modify_order / cancel_order are NEVER called. They exist in the
  SDK but this adapter deliberately does not expose or invoke them.
- The SDK is imported lazily so the app starts and runs on mock data without credentials.
"""
from __future__ import annotations
import logging
from datetime import date, datetime, timedelta, timezone

from config import settings
from brokers.base import BrokerAdapter
from brokers import instruments

logger = logging.getLogger("marketpilot.kotak")

# Read-only allow-list. Order-mutating SDK methods are intentionally excluded and must
# never be added here.
READ_ONLY_METHODS = {
    "authenticate", "health_check", "get_quote", "get_historical_data",
    "get_instrument", "subscribe_market_data", "unsubscribe_market_data",
}


# App interval names -> SDK interval codes (kotakneoapi 3.x).
_INTERVALS = {"day": "D", "daily": "D", "1d": "D", "week": "W", "weekly": "W"}


def _num(d: dict, *keys, default=None):
    for k in keys:
        v = d.get(k)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                return v
    return default


class KotakAPIError(RuntimeError):
    """Raised when the Kotak SDK returns an error payload instead of raising."""


def _sanitize(msg) -> str:
    """Strip any configured secret values from a message before it is stored/logged."""
    text = str(msg)[:300]
    for k in ("KOTAK_CONSUMER_KEY", "KOTAK_MOBILE", "KOTAK_UCC", "KOTAK_MPIN", "KOTAK_TOTP_SECRET",
              "KOTAK_API_KEY", "KOTAK_API_SECRET", "KOTAK_CONSUMER_SECRET"):
        v = getattr(settings, k, "")
        if v and len(str(v)) >= 3:
            text = text.replace(str(v), "***")
    return text


def sdk_error(resp) -> str | None:
    """Return a sanitized error message if `resp` is an SDK error payload, else None.

    The SDK reports many failures as dicts rather than exceptions, e.g.
    {"error": [{"code": "400", "message": "..."}]}, {"Error": "...", "Exception": "..."},
    or {"stat": "Not_Ok", "emsg": "..."}.
    """
    if resp is None:
        return "Empty response from Kotak"
    if not isinstance(resp, dict):
        return None
    err = resp.get("error") or resp.get("Error") or resp.get("errors")
    if err:
        if isinstance(err, list) and err and isinstance(err[0], dict):
            first = err[0]
            code = first.get("code")
            m = first.get("message") or first.get("msg") or str(first)
            return _sanitize(f"{m} (code {code})" if code else m)
        return _sanitize(err)
    stat = str(resp.get("stat") or resp.get("status") or "").lower()
    if stat in ("not_ok", "error", "failed", "failure"):
        return _sanitize(resp.get("emsg") or resp.get("message") or "Kotak returned an error status")
    if "Exception" in resp and "data" not in resp:
        return _sanitize(resp.get("Exception"))
    return None


def _check(resp, op: str):
    err = sdk_error(resp)
    if err:
        raise KotakAPIError(f"{op} failed: {err}")
    return resp


class KotakNeoAdapter(BrokerAdapter):
    def __init__(self):
        self._client = None          # data client (consumer key only) or authenticated client
        self._connected = False      # True only after a verified TOTP+MPIN session
        self._status = "NOT_CONFIGURED" if not settings.kotak_configured() else "DISCONNECTED"
        self._last_connection: str | None = None
        self._last_error: str | None = None
        self._last_data_received: str | None = None

    # ---- configuration ----
    @property
    def configured(self) -> bool:
        return settings.kotak_configured()

    @property
    def data_configured(self) -> bool:
        return settings.kotak_data_configured()

    def required_env(self) -> list[str]:
        return settings.kotak_required_keys()

    def _record_error(self, msg: str):
        self._last_error = _sanitize(msg)

    def _new_client(self):
        import neo_api_client  # lazy import; keeps app light if SDK absent
        return neo_api_client.NeoAPI(
            consumer_key=settings.KOTAK_CONSUMER_KEY, environment=settings.KOTAK_ENVIRONMENT,
            timeout=15.0,  # hard timeout so a stalled call can't pin a FastAPI thread
        )

    def _data_client(self):
        """Client for read-only market data. The installed SDK (kotakneoapi 3.x) serves
        quotes() and historical_data() with the consumer key alone, so a TOTP/MPIN session
        is NOT required here. An authenticated client is reused if one exists."""
        if self._client is not None:
            return self._client
        if not self.data_configured:
            raise RuntimeError("Kotak Neo session not established (KOTAK_CONSUMER_KEY not configured)")
        try:
            self._client = self._new_client()
        except ImportError as e:
            raise RuntimeError("Kotak SDK is not available on the server") from e
        return self._client

    # ---- auth ----
    def authenticate(self) -> dict:
        """Establish a read-only TOTP session (used by Settings -> Test Connection).
        Reports CONNECTED only when the SDK responses themselves indicate success."""
        if not self.configured:
            self._status = "NOT_CONFIGURED"
            return self._status_payload("Kotak Neo credentials are not configured.")
        try:
            import neo_api_client  # noqa: F401
            import pyotp
        except Exception as e:  # SDK not importable
            self._status = "ERROR"
            self._record_error("Kotak SDK unavailable")
            logger.error("Kotak SDK import failed: %s", type(e).__name__)
            return self._status_payload("Kotak SDK is not available on the server.")

        try:
            totp = pyotp.TOTP(settings.KOTAK_TOTP_SECRET).now()
            client = self._new_client()
            _check(client.totp_login(mobile_number=settings.KOTAK_MOBILE, ucc=settings.KOTAK_UCC, totp=totp),
                   "TOTP login")
            _check(client.totp_validate(mpin=settings.KOTAK_MPIN), "MPIN validation")
            self._client = client
            self._connected = True
            self._status = "CONNECTED"
            self._last_error = None
            self._last_connection = datetime.now(timezone.utc).isoformat()
            logger.info("Kotak Neo authenticated (read-only session established).")
            return self._status_payload("Connected to Kotak Neo (read-only).")
        except Exception as e:
            # Never log credential values; only the exception type + sanitized message.
            self._connected = False
            self._status = "AUTH_FAILED" if isinstance(e, KotakAPIError) else self._classify_error(e)
            self._record_error(f"{type(e).__name__}: {e}")
            logger.error("Kotak Neo authentication failed: %s", self._last_error)
            return self._status_payload("Kotak Neo authentication failed. Check credentials/TOTP.")

    @staticmethod
    def _classify_error(e: Exception) -> str:
        name = type(e).__name__.lower()
        if "auth" in name or "validation" in name or "authorization" in name:
            return "AUTH_FAILED"
        if "timeout" in name:
            return "TIMEOUT"
        if "network" in name or "connection" in name:
            return "DISCONNECTED"
        if "ratelimit" in name:
            return "RATE_LIMITED"
        return "ERROR"

    # ---- health ----
    def _status_payload(self, message: str) -> dict:
        return {
            "connected": self._connected,
            "status": self._status,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def health_check(self) -> dict:
        return {
            "broker": "kotak_neo",
            "configured": self.configured,
            "connected": self._connected,
            "status": self._status,
            "order_execution": "disabled",  # never enabled — read-only product
            "last_connection": self._last_connection,
            "last_error": self._last_error,
            "market_data_mode": "consumer_key" if self.data_configured else "unavailable",
            "last_data_received": self._last_data_received,
            "required_env": self.required_env(),
        }

    # ---- instruments ----
    def get_instrument(self, symbol: str) -> dict | None:
        inst = instruments.get_instrument(symbol)
        return inst.to_dict() if inst else None

    # ---- quotes ----
    def get_quote(self, symbol: str) -> dict:
        client = self._data_client()
        inst = instruments.get_instrument(symbol)
        if not inst or not inst.broker_instrument_token:
            raise ValueError(f"Unknown instrument: {symbol}")
        try:
            resp = _check(client.quotes(
                instrument_tokens=[{"instrument_token": inst.broker_instrument_token,
                                    "exchange_segment": inst.exchange}],
                quote_type="all",
            ), f"quotes({symbol})")
        except Exception as e:
            self._record_error(f"{type(e).__name__}: {e}")
            raise
        quote = self._normalize_quote(resp, inst)
        self._last_data_received = quote["timestamp"]
        return quote

    def _normalize_quote(self, resp: dict, inst) -> dict:
        rows = resp.get("data") if isinstance(resp, dict) else None
        row = rows[0] if isinstance(rows, list) and rows else (resp if isinstance(resp, dict) else {})
        ltp = _num(row, "last_traded_price", "ltp", "last_price")
        prev_close = _num(row, "prev_close_price", "close_price", "close", "cls")
        change_pct = None
        if ltp is not None and prev_close:
            change_pct = round((ltp / prev_close - 1) * 100, 2)
        return {
            "symbol": inst.symbol,
            "exchange": inst.exchange,
            "ltp": ltp,
            "open": _num(row, "open_price", "open", "op"),
            "high": _num(row, "high_price", "high", "hp"),
            "low": _num(row, "low_price", "low", "lp"),
            "close": prev_close,
            "volume": _num(row, "volume", "vol_traded", "v"),
            "change_pct": change_pct,
            "timestamp": row.get("last_traded_time") or datetime.now(timezone.utc).isoformat(),
            "source": "kotak",
            "is_live": True,
        }

    # ---- historical ----
    def get_historical_data(self, symbol: str, interval: str = "day", days: int = 120,
                            start: str | None = None, end: str | None = None) -> list[dict]:
        """Daily (or other interval) candles. `symbol` may be a stock in the universe or an
        index name known to instruments.index_token (e.g. "NIFTY")."""
        client = self._data_client()
        neosymbol = instruments.neosymbol(symbol)
        if not neosymbol:
            raise ValueError(f"Unknown instrument: {symbol}")
        to_d = date.fromisoformat(end) if end else date.today()
        # Calendar span: ~1.6x trading days covers weekends/holidays.
        from_d = date.fromisoformat(start) if start else to_d - timedelta(days=int(days * 1.6) + 10)
        try:
            resp = _check(client.historical_data(
                neosymbol=neosymbol,
                interval=_INTERVALS.get(interval, interval),
                from_date=from_d.isoformat(),
                to_date=to_d.isoformat(),
            ), f"historical_data({symbol})")
        except Exception as e:
            self._record_error(f"{type(e).__name__}: {e}")
            raise
        candles = self._normalize_candles(resp)
        if candles:
            self._last_data_received = candles[-1]["timestamp"]
        return candles

    @staticmethod
    def _normalize_candles(resp) -> list[dict]:
        rows = resp.get("data") if isinstance(resp, dict) else resp
        out: list[dict] = []
        if not isinstance(rows, list):
            return out
        for r in rows:
            if isinstance(r, (list, tuple)) and len(r) >= 6:
                ts, o, h, l, c, v = r[0], r[1], r[2], r[3], r[4], r[5]
            elif isinstance(r, dict):
                ts = r.get("timestamp") or r.get("time") or r.get("date")
                o, h, l, c = r.get("open"), r.get("high"), r.get("low"), r.get("close")
                v = r.get("volume")
            else:
                continue
            try:
                out.append({"timestamp": str(ts), "open": float(o), "high": float(h),
                            "low": float(l), "close": float(c), "volume": float(v)})
            except (TypeError, ValueError):
                continue
        return out

    # ---- market-data streaming (architecture only; no alerting in this milestone) ----
    def subscribe_market_data(self, symbols: list[str]) -> dict:
        tokens = []
        for s in symbols:
            inst = instruments.get_instrument(s)
            if inst and inst.broker_instrument_token:
                tokens.append({"exchange_segment": inst.exchange,
                               "instrument_token": inst.broker_instrument_token})
        return {"status": "subscribed" if self._connected else "not_connected",
                "count": len(tokens), "tokens": tokens}

    def unsubscribe_market_data(self, symbols: list[str]) -> dict:
        return {"status": "unsubscribed", "count": len(symbols)}
