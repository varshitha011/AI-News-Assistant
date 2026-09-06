# AI News Assistant

A personal AI information assistant — news feed + stock ticker + conversational AI chat with RAG.

## Stack
- **Frontend**: React + Vite → Render Static Site
- **Backend**: FastAPI → Render Web Service
- **LLM**: Groq (llama-3.3-70b-versatile)
- **Vector DB**: Pinecone (RAG)
- **Embeddings**: fastembed (ONNX, no GPU)
- **News**: GNews API (free tier, mock fallback)
- **Stocks**: Yahoo Finance (free, no key)

## Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # fill in your keys
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env  # set VITE_API_URL=http://localhost:8000
npm run dev
```

## Deploy to Render

1. Push to GitHub
2. Backend: New Web Service → connect repo → root dir `backend` → build `pip install -r requirements.txt` → start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Frontend: New Static Site → connect repo → root dir `frontend` → build `npm install && npm run build` → publish `dist`
4. Set `VITE_API_URL` on the frontend to your backend URL

## Required API Keys
- `GROQ_API_KEY` — from console.groq.com
- `PINECONE_API_KEY` — from app.pinecone.io
- `GNEWS_API_KEY` — optional, from gnews.io (falls back to mock data)
