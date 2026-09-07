"""
Conversational AI agent using Groq SDK directly — no LangChain LLM wrapper.
This avoids the tool_use_failed error caused by langchain-groq auto-injecting
tool schemas into the API request.
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

You can use tools by responding with ONLY a JSON object and nothing else:

To search news by keyword:
{{"tool": "search_news", "query": "your search term"}}

To get news by category:
{{"tool": "get_category_news", "category": "technology"}}

To get stock price:
{{"tool": "get_stock", "symbol": "NVDA"}}

Valid categories: general, technology, business, science, health, sports, entertainment, world

Rules:
- For news questions → respond with the get_category_news JSON
- For specific topic searches → respond with search_news JSON
- For stock questions → respond with get_stock JSON
- After getting tool results, give a clear concise answer in plain text
- For general knowledge questions, answer directly without using a tool
- Never mix JSON and text in the same response"""


def _extract_tool_call(text: str) -> dict | None:
    text = text.strip()
    try:
        d = json.loads(text)
        if "tool" in d:
            return d
    except Exception:
        pass
    match = re.search(r'\{[^{}]*"tool"[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return None


async def _run_tool(call: dict) -> str:
    name = call.get("tool", "")
    try:
        if name == "search_news":
            from app.news import search_news
            articles = await search_news(call.get("query", ""), max_articles=5)
            if not articles:
                return "No news found."
            return "\n".join(f"- {a['title']} ({a['source']}): {a['description']}" for a in articles)

        elif name == "get_category_news":
            from app.news import fetch_top_news
            from app.rag import store_articles
            cat = call.get("category", "general")
            articles = await fetch_top_news(cat, max_articles=6)
            try:
                store_articles(articles)
            except Exception:
                pass
            return "\n".join(f"- {a['title']} ({a['source']}): {a['description']}" for a in articles)

        elif name == "get_stock":
            from app.stocks import get_stock_quote
            q = await get_stock_quote(call.get("symbol", "AAPL"))
            if q.get("error"):
                return f"Could not fetch {q['symbol']}: {q['error']}"
            sign = "+" if q["change"] >= 0 else ""
            return f"{q['name']} ({q['symbol']}): {q['currency']} {q['price']} ({sign}{q['change']}, {sign}{q['change_pct']}%)"

        return f"Unknown tool: {name}"
    except Exception as e:
        return f"Tool error: {e}"


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

    # Add conversation history (last 10 turns)
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

        tool_call = _extract_tool_call(content)
        if not tool_call:
            return content.strip() or "I couldn't process that request."

        result = await _run_tool(tool_call)
        messages.append({"role": "user", "content": f"Tool result:\n{result}"})

    return "I reached the maximum steps. Please try a more specific question."
