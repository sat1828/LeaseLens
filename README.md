<div align="center">

<br/>

# ⌀ LeaseLens

### Your landlord had a lawyer. Now you do too.

**AI-powered rental agreement auditor built for Indian tenants.**  
Clause by clause. Citation by citation. In ~20 seconds.

<br/>

<img width="900" height="540" alt="01_hero" src="https://github.com/user-attachments/assets/7ea2a4c5-85b5-4b74-8df2-cad5ffe8a63f" />

<br/>

[![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React_18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL_16_+_pgvector-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Claude AI](https://img.shields.io/badge/Claude_Sonnet_4-CC785C?style=flat-square)](https://www.anthropic.com/)
[![Stripe](https://img.shields.io/badge/Stripe-635BFF?style=flat-square&logo=stripe&logoColor=white)](https://stripe.com/)
[![Docker](https://img.shields.io/badge/Docker_Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

<br/>

</div>

---

## The Problem

Every year, thousands of Indian tenants sign rental agreements they don't fully understand — documents written by landlords, reviewed by landlords' lawyers, and handed across a table with *"just sign here."* Illegal security deposit demands. Asymmetric lock-in clauses. Rights waived under the Model Tenancy Act 2021 in a single buried sentence.

LeaseLens flips that. Drop in a PDF. Walk out with a full legal audit and a counter-proposal letter backed by actual citations — in the time it takes to make tea.

---

## What You Get

Upload or paste a rental agreement and receive:

| Output | Description |
|--------|-------------|
| **Fairness Score (0–100)** | Weighted composite across clause categories, calibrated to Indian tenancy law |
| **Clause-by-clause risk map** | Every clause tagged `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` / `SAFE` |
| **Legal status per clause** | `ILLEGAL` / `SUSPECT` / `UNFAIR` / `MISSING` / `STANDARD` |
| **Specific citations** | Model Tenancy Act 2021, State Rent Control Acts, Supreme Court judgments |
| **Counter-proposal letter** | Professional, citation-backed, ready to email your landlord today |

> **Privacy first.** The PDF is extracted in-memory and the binary is discarded immediately. No S3 bucket. No storage. No data trail.

---

## Upload & Analyze

<img width="900" height="540" alt="02_upload" src="https://github.com/user-attachments/assets/2c82be65-ffeb-4b33-8ce9-b8cf5910ef7f" />

---

## Audit Results

<img width="900" height="540" alt="03_result" src="https://github.com/user-attachments/assets/9f56a419-475b-4e29-8f8c-723c4d39cf9d" />

---

## Counter-Proposal Letter

<img width="900" height="540" alt="04_letter" src="https://github.com/user-attachments/assets/391188e8-1c44-4bf7-a7b8-f3bd22e958b4" />

---

## Analysis History

<img width="900" height="540" alt="06_history" src="https://github.com/user-attachments/assets/7aaa4c78-9d26-4f3b-80f9-70011c17342e" />

---

## Architecture

<img width="900" height="540" alt="05_architecture" src="https://github.com/user-attachments/assets/2d67523d-5ceb-40b0-9f28-d2c418b89c43" />

```
┌──────────────────────────────────────┐
│   React 18 + TypeScript + Vite       │
│   TailwindCSS · Framer Motion        │
│   Zustand · Axios                    │
└─────────────────┬────────────────────┘
                  │  HTTPS / REST + JWT
┌─────────────────▼────────────────────┐
│   FastAPI  (Python 3.12)             │
│   Uvicorn / Gunicorn                 │
│   JWT auth · Rate limiting · CORS    │
└────┬──────────┬─────────┬────────────┘
     │          │         │
  ┌──▼──┐  ┌───▼───┐  ┌──▼────────┐
  │ PDF │  │Claude │  │  Stripe   │
  │ Svc │  │Sonnet4│  │ Checkout  │
  │PyMu │  │       │  │ Webhooks  │
  │ OCR │  └───────┘  └───────────┘
  └─────┘
     │
┌────▼────────────────────────────────┐
│  PostgreSQL 16 + pgvector (Supabase)│
│  Redis (allkeys-lru · 256mb)        │
│  Alembic migrations                 │
└─────────────────────────────────────┘

  Deploy: Railway · Vercel · GitHub Actions
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | React 18 + TypeScript + Vite + TailwindCSS + Framer Motion | TypeScript catches errors at compile time. Vite eliminates hot-reload lag. Framer Motion for result animations that communicate work happened. |
| **Backend** | FastAPI · Python 3.12 · Uvicorn · Gunicorn | Async-native request handling, auto OpenAPI docs, Python 3.12 interpreter speedups. Gunicorn wrapping UvicornWorker is the production-standard pattern. |
| **AI** | Anthropic Claude `claude-sonnet-4-20250514` | Reasons well over long legal documents. MTA 2021 is well-represented in training. Prompt structured to return clause-level JSON — no regex parsing of free-form output. |
| **Database** | PostgreSQL 16 + pgvector (Supabase) | pgvector is scaffolded for future RAG over jurisdiction-specific legal chunks. Supabase free tier includes pgvector — zero ops overhead until you have real scale problems. |
| **Cache** | Redis (allkeys-lru · 256mb) | Avoids re-running identical analysis requests. `allkeys-lru` means it self-manages under memory pressure. |
| **Auth** | JWT (`python-jose`) + bcrypt | No OAuth dependency overhead. Access + refresh token pair, bcrypt hashing. |
| **Payments** | Stripe Checkout + Webhooks | Freemium gate lives in code. `STRIPE_SECRET_KEY` is optional in `.env` — absent means payment flow never initializes. Ship without charging, wire it when you need to. |
| **PDF** | PyMuPDF + Tesseract OCR | PyMuPDF for text-layer PDFs, Tesseract fallback for scanned docs. Both in-memory — binary never hits disk. |
| **Deploy** | Railway (API) + Vercel (Frontend) + GitHub Actions (CI/CD) | Three commands from zero to production. |
| **Local** | Docker Compose + pgvector/pg16 + Redis | `docker-compose up` and the full stack runs, migrations included. |

---

## Repository Structure

```
leaselens/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py          # Register · Login · JWT refresh
│   │   │   ├── analyze.py       # PDF upload · text paste · analysis polling
│   │   │   └── payments.py      # Stripe Checkout session · webhook handler
│   │   │
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings → reads .env
│   │   │   ├── security.py      # JWT encode/decode · bcrypt helpers
│   │   │   └── logging.py       # Structured JSON logs
│   │   │
│   │   ├── db/
│   │   │   └── session.py       # SQLAlchemy async engine + session factory
│   │   │
│   │   ├── models/
│   │   │   ├── user.py          # User · SubscriptionTier enum
│   │   │   ├── analysis.py      # Analysis result · per-clause breakdown
│   │   │   └── legal.py         # LegalChunk — pgvector RAG-ready (future)
│   │   │
│   │   ├── schemas/             # Pydantic request / response models
│   │   │
│   │   ├── services/
│   │   │   ├── ai.py            # Claude integration · prompt construction
│   │   │   ├── pdf.py           # PyMuPDF extraction + Tesseract fallback
│   │   │   ├── auth.py          # User creation · login validation
│   │   │   └── stripe.py        # Checkout sessions · webhook processing
│   │   │
│   │   └── main.py              # FastAPI app · middleware · lifespan hooks
│   │
│   ├── alembic/                 # DB migrations (auto-run on container start)
│   ├── tests/                   # pytest suite
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   └── src/
│       ├── api/                 # Axios client with JWT interceptor
│       ├── components/          # Upload · Analysis · Letter · Auth · Layout
│       ├── hooks/               # useAnalysis — polling state machine
│       ├── pages/               # Home · Analyze · Result · History · Pricing
│       ├── store/               # Zustand slices: auth + analysis
│       └── App.tsx              # React Router setup
│
├── docs/
│   └── DEPLOYMENT.md            # Railway + Vercel production walkthrough
│
├── docker-compose.yml           # Full local stack with service healthchecks
├── START_HERE_WINDOWS.bat       # Windows pre-flight: checks Python, Node, Git
└── .github/workflows/           # CI/CD pipeline (GitHub Actions)
```

---

## Running Locally

**Prerequisites:** Python 3.12+, Node.js 20+, Docker, Git

```bash
# 1. Clone
git clone https://github.com/sat1828/LeaseLens.git
cd LeaseLens

# 2. Backend
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# → fill in ANTHROPIC_API_KEY, SECRET_KEY, DATABASE_URL

# 3. Spin up DB + Redis only
docker-compose up db redis -d

# 4. Run migrations + start API
alembic upgrade head
uvicorn app.main:app --reload   # → http://localhost:8000

# 5. Frontend (new terminal)
cd ../frontend
npm install
cp .env.example .env            # → VITE_API_URL=http://localhost:8000
npm run dev                     # → http://localhost:5173
```

**Full stack via Docker (fastest path):**
```bash
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
docker-compose up
# API  → http://localhost:8000
# UI   → http://localhost:3000
# Docs → http://localhost:8000/docs
```

Migrations run automatically on container start — no manual `alembic upgrade head` needed.

**On Windows?** Double-click `START_HERE_WINDOWS.bat` first. It checks Python, Node.js, and Git are on `PATH` before you lose time debugging missing tools.

---

## Environment Variables

```bash
# backend/.env

# ── Required ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-api03-...    # console.anthropic.com
SECRET_KEY=                            # openssl rand -hex 32
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/leaselens
DATABASE_URL_SYNC=postgresql://postgres:password@localhost:5432/leaselens

# ── Optional: Stripe (leave blank to disable payments) ──────────────────────
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_PRO=price_...

# ── Optional: Redis (defaults to localhost:6379 if absent) ──────────────────
REDIS_URL=redis://localhost:6379/0

# ── Optional: App config ────────────────────────────────────────────────────
APP_ENV=development                    # or "production"
ALLOWED_ORIGINS=http://localhost:5173
```

---

## API Reference

```
POST   /auth/register          Register new user
POST   /auth/login             Login → JWT access + refresh tokens
POST   /auth/refresh           Refresh access token

POST   /analyze/upload         Upload PDF → returns analysis_id
POST   /analyze/text           Paste raw text → returns analysis_id
GET    /analyze/{id}           Poll status (pending → complete → result)
GET    /analyze/history        Past analyses for the authenticated user

POST   /payments/checkout      Create Stripe Checkout session
POST   /payments/webhook       Stripe webhook (subscription lifecycle)

GET    /health                 Health check (Docker · Railway)
GET    /docs                   Auto-generated OpenAPI UI (FastAPI)
```

---

## Docker Compose — What's Happening

The `docker-compose.yml` wires four services with explicit healthcheck dependency chains:

```yaml
# DB comes up healthy first
db:
  image: pgvector/pgvector:pg16
  healthcheck:
    test: pg_isready -U postgres -d leaselens

# Redis comes up healthy second
redis:
  image: redis:7-alpine
  healthcheck:
    test: redis-cli ping

# API waits for both, runs migrations, then starts
api:
  depends_on:
    db:    { condition: service_healthy }
    redis: { condition: service_healthy }
  command: >
    sh -c "alembic upgrade head &&
           gunicorn app.main:app -k uvicorn.workers.UvicornWorker ..."

# Frontend waits for API healthcheck before serving
frontend:
  depends_on:
    api: { condition: service_healthy }
```

`POSTGRES_PASSWORD` uses `:?` syntax — the stack refuses to start rather than silently using a blank password. This is a small thing that matters in production.

---

## Design Decisions

**PDFs are never stored.** Lease documents contain home addresses, salary figures, Aadhaar numbers sometimes. In-memory extraction and binary discard isn't just good privacy practice — it's the only defensible choice for a product handling this class of document.

**No RAG in v1.** Claude's training covers the Model Tenancy Act well enough for the core use case. The `LegalChunk` model and pgvector schema are already in the codebase but not yet wired to the prompt. The right time to enable it is when you've collected specific jurisdiction failures that retrieval would fix — not upfront speculation.

**Stripe is optional by design.** The freemium tier check is in code. If `STRIPE_SECRET_KEY` isn't set, the payment flow never initializes. Ship first. Charge the day a real user asks how to pay.

**Supabase for pgvector.** Free tier ships pgvector. No self-managed Postgres to operate for a solo build. Migration path to self-hosted is one environment variable.

**`POSTGRES_PASSWORD` fails loudly.** `:?` in docker-compose means the whole stack refuses to start if the variable isn't set. No silent defaults, no accidental blank-password production deploys.

---

## Deployment

Full walkthrough in `docs/DEPLOYMENT.md`.

**Backend → Railway**
1. Connect repo, set root directory to `backend/`
2. Set all env vars from `.env.example` as Railway variables
3. Railway detects the Dockerfile and builds automatically
4. Set `APP_ENV=production`

**Frontend → Vercel**
1. Connect repo, set root directory to `frontend/`
2. Set `VITE_API_URL` to your Railway backend URL
3. Vercel handles build + CDN + HTTPS

**CI/CD → GitHub Actions**
- `pytest` runs on every push
- Deploys to Railway + Vercel on merge to `main`

---

## Codebase Breakdown

```
Python      ████████████████████████▌  49.4%
TypeScript  ███████████████████████▋   47.5%
Dockerfile  ▌                           0.9%
HTML        ▌                           0.8%
JavaScript  ▎                           0.5%
CSS         ▎                           0.5%
Batchfile   ▏                           0.4%
```

---

## What's Next

The core is deliberately lean — ship first, extend when you have real failures to fix:

- **State-level RAG** — wire `LegalChunk` + pgvector to the prompt; Tamil Nadu, Maharashtra, and Delhi rent control details need retrieval, not just training data
- **Regional language output** — counter-proposal letters in Odia, Tamil, Kannada, Hindi
- **WhatsApp intake** — send the PDF to a number, get the audit back; removes the browser entirely for mobile-first users
- **Landlord-side view** — flag clauses likely to cause disputes before the agreement is served

---

## License

MIT. Take it, fork it, ship it.

---

<div align="center">

**Built to protect the tenant. One PDF at a time.**

*India has 110 million rental households.*  
*Most of them signed without knowing what they agreed to.*

</div>
