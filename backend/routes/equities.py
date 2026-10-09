from fastapi import APIRouter, HTTPException
import services

router = APIRouter(prefix="/api", tags=["research"])


@router.get("/market/overview")
async def market_overview():
    return services.market_overview()


@router.get("/equities")
async def equities():
    return {"count": len(services.EQUITIES), "equities": services.list_equities()}


@router.get("/equities/{symbol}")
async def equity_detail(symbol: str):
    eq = services.EQUITIES.get(symbol.upper())
    if not eq:
        raise HTTPException(status_code=404, detail="Equity not found")
    return {k: v for k, v in eq.items() if k != "candles"}


@router.get("/equities/{symbol}/research")
async def equity_research(symbol: str):
    eq = services.EQUITIES.get(symbol.upper())
    if not eq:
        raise HTTPException(status_code=404, detail="Equity not found")
    c = eq["candles"]
    chart = [{"i": i, "close": c["close"][i], "volume": c["volume"][i]}
             for i in range(max(0, len(c["close"]) - 60), len(c["close"]))]
    return {
        "symbol": eq["symbol"], "company": eq["company"], "sector": eq["sector"],
        "opportunity": eq["opportunity"], "indicators": eq["indicators"],
        "fundamentals": eq["fundamentals"], "news": eq["news"],
        "sector_analysis": eq["sector_analysis"], "levels": eq["levels"], "chart": chart,
    }
