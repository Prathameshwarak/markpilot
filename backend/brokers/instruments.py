"""Internal instrument model + broker-agnostic mapping layer.

The research engine uses the internal `symbol` only. Broker-specific identifiers
(exchange segment, instrument token) live here and are translated by the broker adapter,
so additional brokers can be added later without touching the engine.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict

from data.universe import UNIVERSE


@dataclass
class Instrument:
    symbol: str
    exchange: str
    trading_symbol: str
    broker_symbol: str
    broker_instrument_token: str | None
    company_name: str
    sector: str

    def to_dict(self) -> dict:
        return asdict(self)


# Best-effort NSE cash-segment tokens for the initial universe. Real Kotak tokens are
# resolved at runtime from the scrip master via KotakNeoAdapter.get_instrument(); these
# static values are a fallback/seed and are clearly broker-agnostic placeholders.
_NSE_TOKENS = {
    "RELIANCE": "2885", "TCS": "11536", "HDFCBANK": "1333", "INFY": "1594",
    "ICICIBANK": "4963", "SBIN": "3045", "BHARTIARTL": "10604", "ITC": "1660",
    "LT": "11483", "HINDUNILVR": "1394", "TATAMOTORS": "3456", "AXISBANK": "5900",
}

# Kotak addresses indices by NAME (official SDK docs: WsToken("nse_cm", "Nifty 50")).
# The first entry is preferred; later entries are fallbacks tried in order until one
# returns data. The working identifier is remembered for the process.
_INDEX_IDS = {
    "NIFTY": [("nse_cm", "Nifty 50"), ("nse_cm", "26000")],
    "NIFTY 50": [("nse_cm", "Nifty 50"), ("nse_cm", "26000")],
}
_INDEX_RESOLVED: dict[str, tuple[str, str]] = {}


def get_instrument(symbol: str) -> Instrument | None:
    symbol = symbol.upper()
    meta = UNIVERSE.get(symbol)
    if not meta:
        return None
    return Instrument(
        symbol=symbol,
        exchange="nse_cm",
        trading_symbol=f"{symbol}-EQ",
        broker_symbol=symbol,
        broker_instrument_token=_NSE_TOKENS.get(symbol),
        company_name=meta["name"],
        sector=meta["sector"],
    )


def index_token(index: str = "NIFTY") -> tuple[str, str] | None:
    key = index.upper()
    if key in _INDEX_RESOLVED:
        return _INDEX_RESOLVED[key]
    ids = _INDEX_IDS.get(key)
    return ids[0] if ids else None


def remember_index_neosymbol(index: str, neosym: str) -> None:
    seg, _, tok = neosym.partition("|")
    _INDEX_RESOLVED[index.upper()] = (seg, tok)


def neosymbol_candidates(symbol: str) -> list[str]:
    """All neosymbols to try for `symbol` (indices may have several; stocks have one)."""
    key = symbol.upper()
    if key in _INDEX_IDS:
        first = index_token(key)
        ids = [first] + [i for i in _INDEX_IDS[key] if i != first]
        return [f"{s}|{t}" for s, t in ids]
    ns = neosymbol(symbol)
    return [ns] if ns else []


def neosymbol(symbol: str) -> str | None:
    """Kotak SDK `neosymbol` ("{exchange_segment}|{instrument_token}") for a stock in the
    universe or a configured index (indices are NOT part of UNIVERSE)."""
    idx = index_token(symbol)
    if idx:
        return f"{idx[0]}|{idx[1]}"
    inst = get_instrument(symbol)
    if inst and inst.broker_instrument_token:
        return f"{inst.exchange}|{inst.broker_instrument_token}"
    return None


def all_instruments() -> list[Instrument]:
    return [get_instrument(s) for s in UNIVERSE]
