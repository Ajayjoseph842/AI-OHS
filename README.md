# Hazero - AI Compliance Assistant (MVP Scaffold)

Hazero is an AI-powered compliance assistant for SMB warehouses (Canada/US).

Core MVP features:
- Free chatbot that answers OHSA/OSHA questions with citations (RAG stub)
- Pro workflow: incident log, training tracker, export audit binder to PDF
- Reverse trial: 30-day Pro, then downgrade to chatbot-only if not paid

## Stack
- Backend: FastAPI (Python)
- Frontend: React + TypeScript (Vite)
- DB: PostgreSQL (with pgvector for embeddings)
- AI: OpenAI/OpenRouter (RAG stubbed)
- PDF: ReportLab
- Auth: JWT (email + password)

## Prerequisites
- Python 3.11+
- Node 18+
- Docker (for Postgres)

## Quickstart

### 1) Start Postgres (with pgvector)

```bash
docker compose -f docker-compose.yml up -d
```

This exposes Postgres on localhost:5432.

### 2) Backend: install deps and run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

By default, the app runs at http://localhost:8000

- Interactive docs: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

### 3) Frontend: install deps and run

```bash
cd frontend
npm install
npm run dev
```

By default, Vite serves at http://localhost:5173

### Environment variables
Copy `.env.example` to `.env` under `backend/` and adjust as needed.

- `DATABASE_URL` points to the Docker Postgres.
- `JWT_SECRET` set a strong secret for JWT.
- `OPENAI_API_KEY` optional for RAG stub, can be empty locally.

### Notes
- RAG and vector DB integrations are stubbed. Replace `services/rag.py` with your chosen provider (Pinecone or Supabase) and embed your OHSA/OSHA corpora.
- PDF templates are simplistic; upgrade `services/pdf.py` to match inspector-credible forms (MOL Form 7, OSHA 300/301).
- Reverse trial logic is implemented as a dependency that guards Pro-only routes.
