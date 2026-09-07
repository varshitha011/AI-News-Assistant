"""Conversational AI agent with RAG, news search, and stock lookup.
Uses prompt-based tool calling — no bind_tools — to avoid Groq API tool_use errors.
"""

import json
import re
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import GROQ_API_KEY, GROQ_MODEL

# Plain LLM — NO bind_tools
llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.3)


def _system_prompt() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""You are an intelligent personal AI news and information assistant. Current time: {now}.

You can call tools by responding with ONLY a JSON object (no other text, no markdown):

Search news by keyword:
{{"tool": "search_news", "args": {{"query": "your search term"}}}}

Get news by category:
{{"tool": "get_category_news", "args": {{"category": "technology"}}}}

Get stock price:
{{"tool": "get_stock", "args": {{"symbol": "NVDA"}}}}

Valid categories: general, technology, business, science, health, sports, entertainment, world

Rules:
- If the user asks about news, current events, or topics → call get_category_news or search_news
- If the user asks about a stock or company price → call get_stock
- After receiving tool results, give a clear, concise answer
- Support multi-turn conversation — remember context from earlier messages
- If no tool is needed, answer directly
- Never output tool JSON and text at the same time — one or the other"""


def _extract_tool_call(text: str) -> dict | None:
    """Extract JSON tool call from model response."""
    text = text.strip()
    # Try direct parse first
    try:
        d = json.loads(text)
        if "tool" in d:
            return d
    except Exception:
        pass
    # Try finding JSON block in text
    match = re.search(r'\{[^{}]*"tool"[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return None


async def _run_tool(name: str, args: dict) -> str:
    try:
        if name == "search_news":
            from app.news import search_news
            articles = await search_news(args.get("query", ""), max_articles=5)
            if not articles:
                return "No news found for that query."
            return "\n\n".join(
                f"- {a['title']} ({a['source']}): {a['description']}"
                for a in articles
            )

        elif name == "get_category_news":
            from app.news import fetch_top_news
            from app.rag import store_articles
            cat = args.get("category", "general")
            articles = await fetch_top_news(cat, max_articles=6)
            try:
                store_articles(articles)
            except Exception:
                pass
            return "\n\n".join(
                f"- {a['title']} ({a['source']}): {a['description']}"
                for a in articles
            )

        elif name == "get_stock":
            from app.stocks import get_stock_quote
            q = await get_stock_quote(args.get("symbol", "AAPL"))
            if q.get("error"):
                return f"Could not fetch {q['symbol']}: {q['error']}"
            sign = "+" if q["change"] >= 0 else ""
            return (f"{q['name']} ({q['symbol']}): {q['currency']} {q['price']} "
                    f"({sign}{q['change']}, {sign}{q['change_pct']}%)")
        else:
            return f"Unknown tool: {name}"
    except Exception as e:
        return f"Tool error: {e}"


async def chat(messages_history: list[dict], user_message: str) -> str:
    # Try RAG retrieval for context
    rag_context = ""
    try:
        from app.rag import retrieve_relevant
        docs = retrieve_relevant(user_message, top_k=3)
        if docs:
            rag_context = "\n\nRelevant articles from knowledge base:\n" + "\n".join(
                f"- {d['title']} ({d['source']}): {d['description']}" for d in docs
            )
    except Exception:
        pass

    msgs = [SystemMessage(content=_system_prompt() + rag_context)]
    for m in messages_history[-10:]:
        if m["role"] == "user":
            msgs.append(HumanMessage(content=m["content"]))
        else:
            msgs.append(AIMessage(content=m["content"]))
    msgs.append(HumanMessage(content=user_message))

    for _ in range(4):
        response = llm.invoke(msgs)
        content = response.content if isinstance(response.content, str) else str(response.content)
        msgs.append(AIMessage(content=content))

        tool_call = _extract_tool_call(content)
        if not tool_call:
            return content.strip() or "I couldn't process that request."

        result = await _run_tool(tool_call.get("tool", ""), tool_call.get("args", {}))
        msgs.append(HumanMessage(content=f"Tool result:\n{result}"))

    return "I reached the maximum steps. Please rephrase your question."
