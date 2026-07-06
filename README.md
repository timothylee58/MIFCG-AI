# MIFCG-AI — Malaysian Fintech Compliance Gateway

MIFCG-AI is a compliance and financial-intelligence platform for the Malaysian fintech market. It gives compliance officers, analysts, and B40/M40 consumers a single gateway to (1) query Malaysian regulatory documents (BNM, SC, PDPA, Bursa) with cited answers, (2) check eligibility for government aid schemes and get budgeting help, and — once built out — (3) monitor MYR FX rates and (4) score Bursa Malaysia-listed equities on risk/quality factors.

## Architecture overview

- **Frontend**: Next.js 15 (App Router, React 19, TypeScript, Tailwind) — route groups for `(auth)` and `(dashboard)`, deployed as a Node server.
- **Backend**: FastAPI (Python 3.11) exposing REST + Server-Sent-Events (SSE) endpoints under `/api/*`.
- **Database / Auth**: Supabase (Postgres + `pgvector` for embeddings + Supabase Auth), accessed from the backend via the service-role key and from the frontend via the anon key.
- **Cache**: Redis — caches RegComply query results and backs future FX-tick streaming.
- **RAG pipeline**: LangGraph orchestrates a router → retriever → synthesizer graph over Anthropic Claude (synthesis) and OpenAI embeddings (`text-embedding-3-small`) against `pgvector`-stored document chunks.

## Modules / features

| Module | Status | Description |
|---|---|---|
| **RegComply AI** (`/api/regcomply`) | Active | SSE-streaming compliance Q&A over ingested BNM/SC/PDPA/Bursa documents via a LangGraph RAG pipeline (router → retriever → synthesizer), with Redis-cached answers, citations, and a PDF ingestion endpoint that chunks + embeds documents into `pgvector`. |
| **Survival Pro** (`/api/survival-pro`) | Active | Eligibility checker for Malaysian government aid/subsidy schemes (income, household size, state, disability, etc.) plus an SSE-streaming "spend coach" chat for budgeting advice. |
| **FXWatch** (`/api/fxwatch`) | Phase 3 — scaffold | Intended to serve cached BNM MYR FX rates, SSE-stream live ticks, and manage rate alerts for 6 MYR pairs. All endpoints currently return `501 Not Implemented`. |
| **Bursa Risk** (`/api/bursa-risk`) | Phase 3 — scaffold | Intended to score KLCI-listed equities on factors (value, momentum, quality, low-vol, dividend) via an XGBoost model and run a Shariah-aware screener. All endpoints currently return `501 Not Implemented`. |

Each backend router exposes a `GET /api/<module>/` info endpoint reporting its own `status` (`"active"` or `"scaffold"`), which is the source of truth for the table above.

## Local development setup

### Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env            # then fill in the values — see Environment variables below
uvicorn app.main:app --reload
```

The API serves on `http://localhost:8000`, with interactive docs at `/docs` (disabled when `ENVIRONMENT=production`).

### Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.local.example .env.local   # then fill in the values — see Environment variables below
npm run dev
```

The app serves on `http://localhost:3000` and expects the backend to be reachable at `NEXT_PUBLIC_API_URL`.

### Docker Compose (both services + Redis)

A `docker-compose.yml` at the repo root runs `backend`, `frontend`, and `redis` together, reading `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ANTHROPIC_API_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, and `NEXT_PUBLIC_SUPABASE_ANON_KEY` from the host environment:

```bash
docker compose up
```

### Database

The Postgres schema (with `pgvector` enabled) lives in `supabase/migrations/001_initial_schema.sql`. It defines:
- `profiles` — extends `auth.users` with a `role` (`admin` / `analyst` / `viewer`), auto-created on signup via trigger.
- `compliance_documents` and `document_chunks` — ingested regulatory documents and their embedded chunks (`vector(1536)`, `ivfflat` index), plus a `match_document_chunks` semantic-search function.
- `audit_log` — per-user action log.
- Row Level Security is enabled on all tables: users can read/write only their own `profiles` row (admins see all), authenticated users can read compliance documents/chunks (only admins write), and users see only their own audit log entries (admins see all).

Apply it against your Supabase project via the Supabase CLI or dashboard SQL editor; pushes to `main` that touch `supabase/migrations/**` also auto-apply via CI (see CI/CD below).

## Environment variables

### Backend (`backend/.env.example` → `backend/.env`)

| Variable | Purpose |
|---|---|
| `SUPABASE_URL` | Supabase project URL — Supabase dashboard → Settings → API. |
| `SUPABASE_SERVICE_KEY` | Supabase service-role key (server-side, full DB access) — Supabase dashboard → Settings → API. |
| `REDIS_URL` | Connection string for Redis (defaults to local `redis://localhost:6379/0`). |
| `ANTHROPIC_API_KEY` | Claude API key used by the RegComply/Survival Pro LLM synthesis steps — console.anthropic.com. |
| `OPENAI_API_KEY` | OpenAI API key used only for `text-embedding-3-small` document embeddings. |
| `ALLOWED_ORIGINS` | Comma-separated list of origins allowed by CORS (e.g. local frontend + deployed frontend URL). |
| `ENVIRONMENT` | `development` / `test` / `production` — gates `/docs` and `/redoc` availability. |

### Frontend (`frontend/.env.local.example` → `frontend/.env.local`)

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Same Supabase project URL, exposed client-side — Supabase dashboard → Settings → API. |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon/public key for client-side auth — Supabase dashboard → Settings → API. |
| `NEXT_PUBLIC_API_URL` | Base URL of the FastAPI backend (e.g. `http://localhost:8000` locally). |

## Running tests

### Backend

```bash
cd backend
pytest tests/ -v
```

Tests exist for `health`, `regcomply`, and `survival_pro` (the active modules). The suite needs the same env vars as the app to import cleanly; CI (see `.github/workflows/ci.yml`) runs it with placeholder values (`SUPABASE_URL=https://placeholder.supabase.co`, `SUPABASE_SERVICE_KEY=placeholder`, `REDIS_URL=redis://localhost:6379/0`, `ANTHROPIC_API_KEY=sk-ant-placeholder`, `ENVIRONMENT=test`) — set the same locally if you don't have a real Supabase project handy. CI also runs `ruff check app/` and `mypy app/ --ignore-missing-imports`.

### Frontend

```bash
cd frontend
npm run type-check
npm run build
```

CI additionally runs `npm run lint`, and `npm run build` needs `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, and `NEXT_PUBLIC_API_URL` set (placeholders are fine for a build-only check).

## CI/CD & deployment

- **`.github/workflows/ci.yml`** runs on every push to `main`/`claude/**` and every PR to `main`:
  - Backend job: `ruff` lint → `mypy` type-check → `pytest` (with placeholder env vars).
  - Frontend job: `npm run lint` → `npm run type-check` → `npm run build` (with placeholder env vars).
  - On a push to `main` only, once both jobs pass, two deploy jobs push `backend/` and `frontend/` independently to Railway via the Railway CLI (`railway up --service mifcg-api` / `--service mifcg-frontend`), gated by a `RAILWAY_TOKEN` secret.
  - Both services also ship a `Dockerfile` and a `railway.toml` (backend runs `uvicorn app.main:app` behind a `/health` healthcheck; frontend runs `npm start` behind a `/` healthcheck, built with Nixpacks).
- **`.github/workflows/supabase-migrate.yml`** runs on pushes to `main` that touch `supabase/migrations/**`: it links the Supabase CLI to the project (`SUPABASE_PROJECT_REF`, `SUPABASE_ACCESS_TOKEN` secrets) and runs `supabase db push` to apply new migrations automatically.
