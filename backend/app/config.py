import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


GROQ_API_KEY = _require("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

PINECONE_API_KEY = _require("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "ai-news-assistant")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")   # newsapi.org — covers floods, incidents, regional India

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
EMBEDDING_DIM = 384
