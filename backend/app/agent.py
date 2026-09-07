"""
Conversational AI agent — no tool calling API used at all.
We detect intent from the user message, fetch data directly,
then pass it to the LLM as context. Zero tool schemas, zero interception.
"""

import re
from datetime import datetime

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)

STOCK_SYMBOLS = {
    "nvidia": "NVDA", "nvda": "NVDA", "apple": "AAPL", "aapl": "AAPL",
    "tesla": "TSLA", "tsla": "TSLA", "microsoft": "MSFT", "msft": "MSFT",
    "google": "GOOGL", "alphabet": "GOOGL", "amazon": "AMZN", "amzn": "AMZN",
    "meta": "META", "reliance": "RELIANCE.NS", "tcs": "TCS.NS",
    "infosys": "INFY.NS", "wipro": "WIPRO.NS", "nifty": "^NSEI",
    "sensex": "^BSESN", "nse": "^NSEI", "bse": "^BSESN",
}

CATEGORY_KEYWORDS = {
    "technology": ["tech", "ai", "software", "computer", "robot", "startup", "app",
                   "gadget", "phone", "laptop", "internet", "cyber", "digital", "isro",
                   "nasa", "space", "satellite", "rocket"],
    "business":   ["business", "economy", "market", "trade", "company", "corporate",
                   "crochet", "industry", "commerce", "gdp", "entrepreneur"],
    "science":    ["science", "research", "experiment", "discovery", "biology",
                   "physics", "chemistry", "isro", "nasa", "space", "climate"],
    "health":     ["health", "medical", "doctor", "hospital", "disease", "medicine",
                   "vaccine", "mental", "fitness", "diet", "nutrition"],
    "sports":     ["sport", "cricket", "football", "ipl", "match", "player", "team",
                   "tournament", "olympic", "fifa", "tennis", "basketball"],
    "entertainment": ["movie", "film", "music", "celebrity", "bollywood", "hollywood",
                      "actor", "singer", "show", "series", "netflix", "award"],
    "world":      ["world", "global", "international", "country", "war", "peace",
                   "politics", "president", "minister", "election", "india"],
    "general":    [],
}


def _detect_category(text):
    lower = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(k in lower for k in keywords):
            return cat
    return "general"


def _detect_stock_symbol(text):
    lower = text.lower()
    for keyword, symbol in STOCK_SYMBOLS.items():
        if keyword in lower:
            return symbol
    match = re.search(r'\b([A-Z]{2,5})\b', text)
    if match:
        return match.group(1)
    return None


def _is_stock_question(text):
    lower = text.lower()
    stock_words = ["stock", "price", "share", "market cap", "trading", "invest",
                   "bull", "bear", "portfolio", "equity", "nasdaq", "nyse",
                   "nifty", "sensex", "nse", "bse"]
    return any(w in lower for w in stock_words) or _detect_stock_symbol(text) is not None


async def _fetch_context(user_message):
    context_parts = []

    try:
        from app.rag import retrieve_relevant
        docs = retrieve_relevant(user_message, top_k=3)
        if docs:
            context_parts.append("Relevant articles from knowledge base:\n" + "\n".join(
                f"- {d['title']} ({d['source']}): {d['description']}" for d in docs
            ))
    except Exception:
        pass

    if _is_stock_question(user_message):
        symbol = _detect_stock_symbol(user_message)
        if symbol:
            try:
                from app.stocks import get_stock_quote
                q = await get_stock_quote(symbol)
                if not q.get("error"):
                    sign = "+" if q["change"] >= 0 else ""
                    context_parts.append(
                        f"Stock data: {q['name']} ({q['symbol']}) = "
                        f"{q['currency']} {q['price']} "
                        f"({sign}{q['change']}, {sign}{q['change_pct']}%)"
                    )
            except Exception:
                pass

    try:
        from app.news import fetch_top_news, search_news
        from app.rag import store_articles
        articles = await search_news(user_message, max_articles=4)
        if not articles or all(a["url"] == "#" for a in articles):
            cat = _detect_category(user_message)
            articles = await fetch_top_news(cat, max_articles=5)
        if articles:
            try:
                store_articles(articles)
            except Exception:
                pass
            context_parts.append("Current news articles:\n" + "\n".join(
                f"- {a['title']} ({a['source']}): {a['description']}"
                for a in articles
            ))
    except Exception:
        pass

    return "\n\n".join(context_parts)


async def chat(messages_history, user_message):
    context = await _fetch_context(user_message)

    system = f"""You are an intelligent personal AI news and information assistant.
Current time: {datetime.now().strftime("%Y-%m-%d %H:%M")}.

Answer the user's question using the context below. Be clear, concise and helpful.
If the context has relevant information use it. Otherwise use your general knowledge.
Always cite sources when available.

{context}"""

    messages = [{"role": "system", "content": system}]
    for m in messages_history[-10:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.4,
        max_tokens=1024,
    )
    return response.choices[0].message.content or "I could not generate a response."
