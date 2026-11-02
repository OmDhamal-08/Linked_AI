# Linkdine AI

A web app that helps students and professionals write better LinkedIn posts. You either describe something you did
(a project, an internship, a certification) and it writes a post for you, or you paste a draft and it tells you what's weak
and rewrites it.

Under the hood it's a RAG pipeline: instead of just prompting an LLM, it first pulls writing patterns (hook styles,
structures, keywords, CTAs) from a small knowledge base of example posts and uses those to guide the generation.

I built this to learn how retrieval, prompt design and output validation fit together in a real full-stack app,
with auth, usage limits and an admin panel around it.

## Features

- **Generate** a post from a form: what you did, the tools you used, tone, audience, length.
- **Enhance** an existing draft: hook strength, readability, keyword and structure analysis, concrete suggestions, and a rewritten version.
- **Quality score** for every post (hook, keywords, readability, structure). It's a writing-quality score, not a reach prediction.
- **History**: view, edit, copy and delete saved posts; edit hashtags.
- **Free / Premium plans** with daily limits, all driven by config. Payments are mocked for now.
- **Admin panel**: upload CSV/JSON datasets into the knowledge base, browse records, see usage and errors.
- **Pluggable providers**: swap the LLM (mock, OpenAI, Anthropic) or the embedding model with an env variable.

## Tech stack

| | |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, React Hook Form, Zod |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2, Alembic |
| Database | PostgreSQL + pgvector (SQLite works for local dev) |
| AI | OpenAI / Anthropic behind one interface, plus a mock provider for offline dev |
| Testing | pytest (95 tests), Vitest + Testing Library (23 tests) |

## How it works

```text
Next.js frontend ──REST /api/v1──► FastAPI
                                     │
             ┌───────────────────────┼──────────────────────┐
             ▼                       ▼                      ▼
        Auth (JWT)            Post service            Usage / plans
                                     │
                     1. analyse the request (topic, category, keywords)
                     2. embed it and search the knowledge base (pgvector)
                     3. re-score results: vector + keyword + metadata → top K
                     4. turn the top K into "content intelligence"
                        (common hooks, structure, keywords, CTA style)
                     5. build the prompt (rules / user input / patterns / task)
                     6. call the LLM
                     7. validate the output (length, spam, repetition,
                        made-up numbers, prompt leakage) → retry once if bad
                     8. score it and save it
```

A few decisions worth mentioning:

- **The knowledge base stores derived patterns, not the original posts.** During ingestion the text is cleaned,
  PII (emails, phones, PAN, Aadhaar) is redacted, duplicates are dropped, metadata is extracted, and only the embedding and
  metadata are kept. The original text is thrown away.
- **Hybrid retrieval.** Pure vector similarity with small data was noisy, so results are re-ranked with keyword overlap
  and metadata matches (weights are configurable).
- **User input and retrieved data are treated as untrusted** in the prompt and kept in separate sections, to limit prompt injection.
- **Everything provider-specific sits behind an interface** (`ai/`, `embeddings/`, `rag/vector_store.py`,
  `services/payment_service.py`), wired up in `services/container.py`. The mock LLM and hashing embeddings mean the whole
  app runs and tests without any API key.

## Project structure

```text
backend/
  app/
    api/v1/        routes: auth, users, posts, usage, subscriptions, admin, meta, health
    services/      business logic (posts, RAG, scoring, validation, usage, plans)
    rag/           query analyzer, vector store, retriever, reranker
    ai/            LLM providers
    embeddings/    embedding providers
    ingestion/     loader, validator, cleaner, PII redaction, pipeline
    nlp/           rule-based text analysis
    prompts/       prompt templates
    models/ repositories/ schemas/ core/ db/
  alembic/         migrations
  scripts/         seed, ingest, generate synthetic data
  evaluation/      RAG evaluation script and query set
  tests/
frontend/
  app/             pages (landing, auth, dashboard, generate, enhance, history, analytics, admin…)
  components/ hooks/ lib/ types/ __tests__/
```

## Running it locally

You need Python 3.12+ and Node 20+.

**Backend**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env
alembic upgrade head
python scripts/seed_database.py   # demo user + sample knowledge base
uvicorn app.main:app --reload     # http://localhost:8000/docs
```

**Frontend**

```bash
cd frontend
npm install
copy .env.example .env.local      # macOS/Linux: cp .env.example .env.local
npm run dev                       # http://localhost:3000
```

Log in with the demo account from `backend/.env` (`DEMO_USER_EMAIL` / `DEMO_USER_PASSWORD`).

By default it runs on SQLite with the mock LLM, so no keys or database server are needed.

**With PostgreSQL + pgvector**

```bash
docker compose up -d db
```

Then in `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://linkdine:linkdine_dev_password@localhost:5432/linkdine
VECTOR_STORE=pgvector
```

and run `alembic upgrade head` and the seed script again. The migration enables the `vector` extension itself.

## Configuration

All settings live in `backend/.env` (see `.env.example` for the full list). The ones you'll actually change:

| Variable | What it does |
|---|---|
| `JWT_SECRET` | Signs login tokens. Use a long random string. |
| `ADMIN_EMAILS` | Comma-separated emails that get the admin panel. |
| `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL` | `mock`, `openai` or `anthropic` |
| `AI_FALLBACK_PROVIDER` | Optional second provider used only if the first fails |
| `EMBEDDING_PROVIDER`, `EMBEDDING_DIM` | `hashing` (384, local) or `openai` (1536) |
| `FREE_GENERATIONS_PER_DAY`, `FREE_ENHANCEMENTS_PER_DAY` | Free plan limits |
| `RAG_TOP_K` | How many patterns are retrieved per request |

Example for a real model:

```env
AI_PROVIDER=openai
AI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini
```

If a real provider is set without a key, the backend logs a warning and falls back to the mock. `GET /api/v1/health`
shows what's active.

If you change the embedding model or dimension, re-create the knowledge base table and re-ingest the data.

## Adding your own data

Drop `.csv` or `.json` files into `backend/data/raw/` and run:

```bash
python scripts/ingest_dataset.py
```

or upload them from `/admin`. Only a `text` column is required (40–5000 chars). Optional columns: `category`, `topic`,
`keywords`, `tone`, `hook_type`, `structure`, `cta_type`, `hashtags`, `audience`. Anything missing is inferred.

The included `synthetic_knowledge.csv` is generated sample data (`scripts/generate_synthetic_dataset.py`), only meant for development.

## Tests

```bash
cd backend && pytest
cd frontend && npm test && npm run typecheck
```

RAG evaluation on the sample data:

```bash
cd backend
python evaluation/evaluate_rag.py --k 5
```

On the synthetic set this gives precision@5 ≈ 0.87. The queries come from the same templates as the data, so treat it as a
regression check rather than a real accuracy number.

## API overview

All routes are under `/api/v1`; protected ones need `Authorization: Bearer <token>`.

| Method | Path | |
|---|---|---|
| POST | `/auth/signup`, `/auth/login`, `/auth/logout` | accounts |
| GET | `/users/me` | current user |
| POST | `/posts/generate`, `/posts/enhance`, `/posts/analyze` | main features |
| GET / PATCH / DELETE | `/posts`, `/posts/{id}` | history |
| GET | `/usage`, `/subscription` | limits and plan |
| GET | `/meta/taxonomy`, `/meta/plans` | form options and plan limits |
| POST / GET / DELETE | `/admin/knowledge/...` | knowledge base management |

Full interactive docs at `/docs` when running in development.

## Deployment

- **Backend:** `backend/Dockerfile` runs migrations and starts Uvicorn on port 8000. Works on Render, Railway or Fly.io.
  Set `ENVIRONMENT=production`, `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, the AI keys and `ALLOW_MOCK_PAYMENTS=false`.
- **Database:** any managed Postgres with pgvector (Supabase, Neon).
- **Frontend:** Vercel, with `frontend/` as root and `NEXT_PUBLIC_API_BASE_URL` pointing at the backend.

## Known limitations / what's next

- The mock LLM produces template text. Real output quality needs an OpenAI or Anthropic key.
- Hashing embeddings are lexical; OpenAI embeddings give much better semantic retrieval.
- The sample dataset is small and synthetic. A curated dataset of a few hundred real, licensed examples is the next step.
- Tokens are stored in `localStorage`; moving to httpOnly cookies is on the list.
- Rate limiting is in-memory (single instance only), ingestion is synchronous, payments are mocked.
- Planned: Stripe/Razorpay, a cross-encoder reranker, personalisation from the user profile, Hindi/Marathi support.
