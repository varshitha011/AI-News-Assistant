"""News fetcher — uses NewsAPI (primary) with GNews and mock fallback."""

import httpx
from datetime import datetime
from app.config import GNEWS_API_KEY, NEWSAPI_KEY

NEWSAPI_BASE = "https://newsapi.org/v2"
GNEWS_BASE = "https://gnews.io/api/v4"

NEWSAPI_CATEGORIES = {
    "general": "general", "technology": "technology", "business": "business",
    "science": "science", "health": "health", "sports": "sports",
    "entertainment": "entertainment", "world": "general",
}


async def fetch_top_news(category: str = "general", max_articles: int = 10) -> list[dict]:
    """Fetch top headlines — tries NewsAPI first, then GNews, then mock."""
    if NEWSAPI_KEY:
        try:
            cat = NEWSAPI_CATEGORIES.get(category, "general")
            url = f"{NEWSAPI_BASE}/top-headlines"
            params = {
                "category": cat,
                "language": "en",
                "pageSize": max_articles,
                "apiKey": NEWSAPI_KEY,
            }
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                articles = r.json().get("articles", [])
                if articles:
                    return [_normalize_newsapi(a, category) for a in articles]
        except Exception as e:
            print(f"NewsAPI top-headlines error: {e}")

    if GNEWS_API_KEY:
        try:
            url = f"{GNEWS_BASE}/top-headlines"
            params = {"category": category, "lang": "en", "max": max_articles, "apikey": GNEWS_API_KEY}
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                articles = r.json().get("articles", [])
                if articles:
                    return [_normalize_gnews(a, category) for a in articles]
        except Exception as e:
            print(f"GNews error: {e}")

    return _mock_news(category)


async def search_news(query: str, max_articles: int = 6) -> list[dict]:
    """Search news by keyword — NewsAPI first, then GNews, then mock."""
    if NEWSAPI_KEY:
        try:
            url = f"{NEWSAPI_BASE}/everything"
            params = {
                "q": query,
                "language": "en",
                "pageSize": max_articles,
                "sortBy": "publishedAt",
                "apiKey": NEWSAPI_KEY,
            }
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                articles = r.json().get("articles", [])
                if articles:
                    return [_normalize_newsapi(a, "search") for a in articles]
        except Exception as e:
            print(f"NewsAPI search error: {e}")

    if GNEWS_API_KEY:
        try:
            url = f"{GNEWS_BASE}/search"
            params = {"q": query, "lang": "en", "max": max_articles, "apikey": GNEWS_API_KEY}
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                articles = r.json().get("articles", [])
                if articles:
                    return [_normalize_gnews(a, "search") for a in articles]
        except Exception as e:
            print(f"GNews search error: {e}")

    return _mock_news("general", query)


def _normalize_newsapi(a: dict, category: str) -> dict:
    source = a.get("source", {})
    return {
        "title": a.get("title", "") or "",
        "description": a.get("description", "") or "",
        "content": a.get("content", "") or a.get("description", "") or "",
        "url": a.get("url", ""),
        "source": source.get("name", "Unknown") if isinstance(source, dict) else str(source),
        "published_at": a.get("publishedAt", datetime.now().isoformat()),
        "category": category,
        "image": a.get("urlToImage", "") or "",
    }


def _normalize_gnews(a: dict, category: str) -> dict:
    source = a.get("source", {})
    return {
        "title": a.get("title", "") or "",
        "description": a.get("description", "") or "",
        "content": a.get("content", "") or a.get("description", "") or "",
        "url": a.get("url", ""),
        "source": source.get("name", "Unknown") if isinstance(source, dict) else str(source),
        "published_at": a.get("publishedAt", datetime.now().isoformat()),
        "category": category,
        "image": a.get("image", "") or "",
    }


def _mock_news(category: str, query: str = "") -> list[dict]:
    now = datetime.now().isoformat()
    base = [
        {"title": "Assam floods: Over 2 lakh people affected across 14 districts",
         "description": "Heavy rains triggered flooding in Assam affecting over 2 lakh people.",
         "content": "The Brahmaputra river is flowing above danger level in several districts.",
         "url": "#", "source": "NDTV", "published_at": now, "category": "world", "image": ""},
        {"title": "Railway workers strike called off after government talks",
         "description": "The 48-hour railway strike was called off after negotiations with the ministry.",
         "content": "Union leaders agreed to resume work after assurances from the ministry.",
         "url": "#", "source": "The Hindu", "published_at": now, "category": "world", "image": ""},
        {"title": "Cyclone alert issued for coastal Odisha and West Bengal",
         "description": "IMD issues red alert for cyclone landfall expected in 48 hours.",
         "content": "Fishermen advised not to venture into the sea. Evacuation in progress.",
         "url": "#", "source": "Times of India", "published_at": now, "category": "world", "image": ""},
        {"title": "OpenAI releases new reasoning model surpassing GPT-4",
         "description": "OpenAI has announced a new model with significantly improved reasoning capabilities.",
         "content": "Major improvements in math, coding and complex reasoning tasks.",
         "url": "#", "source": "TechCrunch", "published_at": now, "category": "technology", "image": ""},
        {"title": "India's GDP grows 7.2% in Q2, beats expectations",
         "description": "India's economy continues strong growth driven by manufacturing and services.",
         "content": "Manufacturing up 8.1% year-over-year.",
         "url": "#", "source": "Economic Times", "published_at": now, "category": "business", "image": ""},
        {"title": "NVIDIA stock hits new all-time high amid AI demand surge",
         "description": "NVIDIA shares rose 3.2% as enterprise AI adoption accelerates.",
         "content": "Data center revenue expected to double year-over-year.",
         "url": "#", "source": "Bloomberg", "published_at": now, "category": "business", "image": ""},
        {"title": "IPL 2026: Mumbai Indians win in a thriller",
         "description": "Mumbai Indians defeated Chennai Super Kings by 3 runs.",
         "content": "A last-ball finish gave Mumbai their record 6th IPL title.",
         "url": "#", "source": "Cricinfo", "published_at": now, "category": "sports", "image": ""},
        {"title": "New breakthrough in cancer detection using AI",
         "description": "Researchers achieve 94% accuracy in early cancer detection.",
         "content": "A team trained a model on 100,000 patient scans.",
         "url": "#", "source": "Nature", "published_at": now, "category": "health", "image": ""},
    ]
    if query:
        q = query.lower()
        filtered = [a for a in base if q in a["title"].lower() or q in a["description"].lower()]
        return filtered if filtered else base[:4]
    return [a for a in base if a["category"] == category or category == "general"][:6]
