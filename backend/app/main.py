import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.news import fetch_top_news, search_news
from app.stocks import get_multiple_quotes, DEFAULT_WATCHLIST
from app.rag import store_articles, retrieve_relevant
from app.agent import chat

app = FastAPI(title="AI News Assistant", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── NEWS ──
@app.get("/news/{category}")
async def get_news(category: str = "general", max: int = 10):
    articles = await fetch_top_news(category, max_articles=max)
    # Store in RAG index for later retrieval
    try:
        store_articles(articles)
    except Exception:
        pass
    return {"articles": articles, "category": category}


@app.get("/news/search/{query}")
async def search(query: str, max: int = 5):
    articles = await search_news(query, max_articles=max)
    return {"articles": articles, "query": query}


# ── STOCKS ──
@app.get("/stocks")
async def get_stocks(symbols: str = ""):
    watchlist = symbols.split(",") if symbols else DEFAULT_WATCHLIST
    quotes = await get_multiple_quotes([s.strip() for s in watchlist if s.strip()])
    return {"quotes": quotes}


@app.get("/stocks/{symbol}")
async def get_stock(symbol: str):
    from app.stocks import get_stock_quote
    return await get_stock_quote(symbol)


# ── CHAT ──
class ChatRequest(BaseModel):
    messages: list[dict]  # [{"role": "user"|"assistant", "content": str}]
    message: str


@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        reply = await chat(req.messages, req.message)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── HEALTH ──
@app.get("/health")
def health():
    return {"status": "ok"}
