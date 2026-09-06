"""Stock data — uses Yahoo Finance (free, no API key)."""

import httpx
from datetime import datetime


async def get_stock_quote(symbol: str) -> dict:
    """Get current stock price and change from Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with httpx.AsyncClient(timeout=8, headers=headers) as client:
            r = await client.get(url, params={"interval": "1d", "range": "2d"})
            r.raise_for_status()
            data = r.json()
            meta = data["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice", 0)
            prev = meta.get("chartPreviousClose", meta.get("previousClose", price))
            change = price - prev
            change_pct = (change / prev * 100) if prev else 0
            return {
                "symbol": symbol.upper(),
                "price": round(price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "currency": meta.get("currency", "USD"),
                "name": meta.get("longName", meta.get("shortName", symbol)),
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        return {"symbol": symbol.upper(), "error": str(e), "price": None}


async def get_multiple_quotes(symbols: list[str]) -> list[dict]:
    results = []
    for s in symbols:
        q = await get_stock_quote(s)
        results.append(q)
    return results


DEFAULT_WATCHLIST = ["^NSEI", "^NSEBANK", "NVDA", "AAPL", "TSLA", "RELIANCE.NS", "TCS.NS", "INFY.NS"]
