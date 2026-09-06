"""RAG layer — store and retrieve news articles from Pinecone."""

import uuid
from datetime import datetime

from fastembed import TextEmbedding
from pinecone import Pinecone, ServerlessSpec

from app.config import (
    EMBEDDING_DIM, EMBEDDING_MODEL,
    PINECONE_API_KEY, PINECONE_CLOUD, PINECONE_INDEX, PINECONE_REGION,
)

_pc = Pinecone(api_key=PINECONE_API_KEY)
_embedder = TextEmbedding(model_name=EMBEDDING_MODEL)


def _ensure_index():
    existing = [i.name for i in _pc.list_indexes()]
    if PINECONE_INDEX not in existing:
        _pc.create_index(
            name=PINECONE_INDEX,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
        )
    return _pc.Index(PINECONE_INDEX)


_index = _ensure_index()


def _embed(text: str) -> list[float]:
    return list(_embedder.embed([text]))[0].tolist()


def store_articles(articles: list[dict]) -> int:
    """Embed and upsert articles into Pinecone. Returns count stored."""
    vectors = []
    for a in articles:
        text = f"{a['title']}. {a.get('description', '')} {a.get('content', '')}"
        vid = f"news-{uuid.uuid4().hex[:10]}"
        vectors.append({
            "id": vid,
            "values": _embed(text[:1000]),
            "metadata": {
                "title": a.get("title", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "source": a.get("source", ""),
                "category": a.get("category", "general"),
                "published_at": a.get("published_at", datetime.now().isoformat()),
                "image": a.get("image", ""),
            },
        })
    if vectors:
        for i in range(0, len(vectors), 50):
            _index.upsert(vectors=vectors[i:i+50])
    return len(vectors)


def retrieve_relevant(query: str, top_k: int = 5, category: str = "") -> list[dict]:
    """Retrieve most relevant articles for a query."""
    filter_dict = {"category": {"$eq": category}} if category else {}
    result = _index.query(
        vector=_embed(query),
        top_k=top_k,
        filter=filter_dict if filter_dict else None,
        include_metadata=True,
    )
    matches = result.matches if hasattr(result, "matches") else result.get("matches", [])
    docs = []
    for m in matches:
        meta = m.metadata if hasattr(m, "metadata") else m.get("metadata", {})
        docs.append({
            "title": meta.get("title", ""),
            "description": meta.get("description", ""),
            "url": meta.get("url", ""),
            "source": meta.get("source", ""),
            "category": meta.get("category", ""),
            "published_at": meta.get("published_at", ""),
            "image": meta.get("image", ""),
            "score": m.score if hasattr(m, "score") else m.get("score", 0),
        })
    return docs
