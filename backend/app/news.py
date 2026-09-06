"""News fetcher — uses GNews API (free tier) with a mock fallback."""

import httpx
from datetime import datetime
from app.config import GNEWS_API_KEY

CATEGORIES = [
    "general", "technology", "business", "science",
    "health", "sports", "entertainment", "world",
]

GNEWS_BASE = "https://gnews.io/api/v4"


async def fetch_top_news(category: str = "general", max_articles: int = 10) -> list[dict]:
    """Fetch top headlines from GNews API."""
    if not GNEWS_API_KEY:
        return _mock_news(category)

    cat = category if category in CATEGORIES else "general"
    url = f"{GNEWS_BASE}/top-headlines"
    params = {
        "category": cat,
        "lang": "en",
        "max": max_articles,
        "apikey": GNEWS_API_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            articles = data.get("articles", [])
            return [_normalize(a, category) for a in articles]
    except Exception as e:
        print(f"GNews error: {e}")
        return _mock_news(category)


async def search_news(query: str, max_articles: int = 5) -> list[dict]:
    """Search news by keyword."""
    if not GNEWS_API_KEY:
        return _mock_news("general", query)

    url = f"{GNEWS_BASE}/search"
    params = {"q": query, "lang": "en", "max": max_articles, "apikey": GNEWS_API_KEY}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            articles = data.get("articles", [])
            return [_normalize(a, "search") for a in articles]
    except Exception as e:
        print(f"GNews search error: {e}")
        return _mock_news("general", query)


def _normalize(article: dict, category: str) -> dict:
    return {
        "title": article.get("title", ""),
        "description": article.get("description", ""),
        "content": article.get("content", article.get("description", "")),
        "url": article.get("url", ""),
        "source": article.get("source", {}).get("name", "Unknown"),
        "published_at": article.get("publishedAt", datetime.now().isoformat()),
        "category": category,
        "image": article.get("image", ""),
    }


def _mock_news(category: str, query: str = "") -> list[dict]:
    now = datetime.now().isoformat()
    base = [
        {"title": "OpenAI releases new reasoning model surpassing GPT-4",
         "description": "OpenAI has announced a new model with significantly improved reasoning capabilities.",
         "content": "OpenAI's latest model demonstrates major improvements in math, coding, and complex reasoning tasks.",
         "url": "#", "source": "TechCrunch", "published_at": now, "category": "technology", "image": ""},
        {"title": "India's GDP grows 7.2% in Q2, beats expectations",
         "description": "India's economy continues strong growth driven by manufacturing and services.",
         "content": "India's GDP growth of 7.2% in Q2 outpaced forecasts, with manufacturing up 8.1%.",
         "url": "#", "source": "Economic Times", "published_at": now, "category": "business", "image": ""},
        {"title": "NVIDIA stock hits new all-time high amid AI demand surge",
         "description": "NVIDIA shares rose 3.2% today as enterprise AI adoption accelerates.",
         "content": "NVIDIA's data center revenue is expected to double year-over-year.",
         "url": "#", "source": "Bloomberg", "published_at": now, "category": "business", "image": ""},
        {"title": "New breakthrough in cancer detection using AI",
         "description": "Researchers achieve 94% accuracy in early cancer detection using machine learning.",
         "content": "A team of scientists trained a model on 100,000 patient scans with near-perfect accuracy.",
         "url": "#", "source": "Nature", "published_at": now, "category": "health", "image": ""},
        {"title": "Climate summit reaches new emissions agreement",
         "description": "World leaders agree to cut emissions by 45% by 2035.",
         "content": "The historic agreement was signed by 190 countries at this year's climate summit.",
         "url": "#", "source": "Reuters", "published_at": now, "category": "world", "image": ""},
        {"title": "Apple unveils next-generation chips for MacBook",
         "description": "Apple's M4 Ultra chip delivers 40% performance improvement.",
         "content": "The new chip features a 12-core CPU and 40-core GPU at 3nm architecture.",
         "url": "#", "source": "The Verge", "published_at": now, "category": "technology", "image": ""},
        {"title": "IPL 2026: Mumbai Indians win in a thriller",
         "description": "Mumbai Indians defeated Chennai Super Kings by 3 runs.",
         "content": "A last-ball finish gave Mumbai their record 6th IPL title.",
         "url": "#", "source": "Cricinfo", "published_at": now, "category": "sports", "image": ""},
        {"title": "Meta announces open-source AI model with 400B parameters",
         "description": "Meta's new LLaMA model is available for free commercial use.",
         "content": "The model outperforms closed-source alternatives on several benchmarks.",
         "url": "#", "source": "Meta AI Blog", "published_at": now, "category": "technology", "image": ""},
    ]
    if query:
        q = query.lower()
        filtered = [a for a in base if q in a["title"].lower() or q in a["description"].lower()]
        return filtered if filtered else base[:3]
    return [a for a in base if a["category"] == category or category == "general"][:6]
