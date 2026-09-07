"""
Conversational AI agent using Groq SDK directly.
Uses a custom action format that Groq won't intercept as tool calls.
"""

import json
import re
from datetime import datetime

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)


def _system_prompt() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""You are an intelligent personal AI news and information assistant. Current time: {now}.

When you need to fetch information, output an ACTION block like this (and nothing else):

ACTION: search_news | query=your search term
ACTION: get_category_news | category=technology
ACTION: get_stock | symbol=NVDA

Valid categories: general, technology, business, science, health, sports, entertainment, world

Rules:
- For news/current events questions -> output ACTION: get_category_news
- For specific person/topic searches -> output ACTION: search_news
- For stock price questions -> output ACTION: get_stock
- After getting results, give a clear concise answer
- For general knowledge, answer directly without an ACTION
- Never mix ACTION and text in the same response
- Only output one ACTION per response"""


def _extract_action(text: str) -> dict | None:
    text = text.strip()
    match = re.search(r'ACTION:\s*(\w+)\s*\|(.+)', text)
    if not match:
        return None
    name = match.group(1).strip()
    params_str = match.group(2).strip()
    params = {}
    for part in params_str.split('|'):
        if '=' in part:
            k, v = part.split('=', 1)
            params[k.strip()] = v.strip()
    return {"tool": name, "params": params}


async def _run_action(action: dict) -> str:
    name = action.get("tool", "")
    params = action.get("params", {})
    try:
        if name == "search_news":
            from app.news import search_news
            articles = await search_news(params.get("query", ""), max_articles=5)
            if not articles:
                return "No news found for that query."
            return "\n".join(f"- {a['title']} ({a['source']}): {a['description']}" for a in articles)

        elif name == "get_category_news":
            from app.news import fetch_top_news
            from app.rag import store_articles
            cat = params.get("category", "general")
            articles = await fetch_top_news(cat, max_articles=6)
            try:
                store_articles(articles)
            except Exception:
                pass
            return "\n".join(f"- {a['title']} ({a['source']}): {a['description']}" for a in articles)

        elif name == "get_stock":
            from app.stocks import get_stock_quote
            q = await get_stock_quote(params.get("symbol", "AAPL"))
            if q.get("error"):
                return f"Could not fetch {q['symbol']}: {q['error']}"
            sign = "+" if q["change"] >= 0 else ""
            return f"{q['name']} ({q['symbol']}): {q['currency']} {q['price']} ({sign}{q['change']}, {sign}{q['change_pct']}%)"

        return f"Unknown action: {name}"
    except Exception as e:
        return f"Action error: {e}"


async def chat(messages_history: list[dict], user_message: str) -> str:
    # RAG context
    rag_context = ""
    try:
        from app.rag import retrieve_relevant
        docs = retrieve_relevant(user_message, top_k=3)
        if docs:
            rag_context = "\n\nRelevant from knowledge base:\n" + "\n".join(
                f"- {d['title']}: {d['description']}" for d in docs
            )
    except Exception:
        pass

    messages = [{"role": "system", "content": _system_prompt() + rag_context}]
    for m in messages_history[-10:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_message})

    for _ in range(4):
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        content = response.choices[0].message.content or ""
        messages.append({"role": "assistant", "content": content})

        action = _extract_action(content)
        if not action:
            return content.strip() or "I couldn't process that request."

        result = await _run_action(action)
        messages.append({"role": "user", "content": f"Results:\n{result}"})

    return "I reached the maximum steps. Please try a more specific question."
