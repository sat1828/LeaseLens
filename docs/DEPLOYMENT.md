# LeaseLens — Deployment Guide

## Prerequisites
- Supabase account (PostgreSQL + pgvector free tier)
- Railway.app account (API backend)
- Vercel account (frontend)
- Anthropic API key
- Stripe account (when ready to monetize)

---

## Step 1: Database (Supabase — Free)

1. Go to [supabase.com](https://supabase.com) → New Project
2. Save your database password
3. Go to Settings → Database → Connection string → URI
4. Copy the connection string (replace `[YOUR-PASSWORD]`)
5. Enable pgvector: SQL Editor → run `CREATE EXTENSION IF NOT EXISTS vector;`
6. Run migrations:
   ```bash
   cd backend
   cp .env.example .env
   # Fill in DATABASE_URL and DATABASE_URL_SYNC from Supabase
   pip install -r requirements.txt
   alembic upgrade head
   ```

---

## Step 2: Backend (Railway — Free tier available)

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select the `backend` directory (set root to `/backend`)
4. Add environment variables in Railway dashboard:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   DATABASE_URL=postgresql+asyncpg://...  (from Supabase)
   DATABASE_URL_SYNC=postgresql://...
   APP_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
   FRONTEND_URL=https://your-app.vercel.app
   APP_ENV=production
   ```
5. Railway auto-detects Python → deploys uvicorn
6. Note your Railway URL: `https://leaselens-api.up.railway.app`

---

## Step 3: Frontend (Vercel — Free)

1. Go to [vercel.com](https://vercel.com) → New Project → Import from GitHub
2. Set root directory to `frontend`
3. Add environment variable:
   ```
   VITE_API_URL=https://your-railway-url.up.railway.app
   ```
4. Deploy → Vercel gives you `https://leaselens.vercel.app`

---

## Step 4: Stripe (when you have users)

1. Create products in Stripe Dashboard:
   - Pro Plan: ₹299/month recurring → copy Price ID
   - Team Plan: ₹1,499/month recurring → copy Price ID
2. Add to Railway env vars:
   ```
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_PRO_PRICE_ID=price_...
   STRIPE_TEAM_PRICE_ID=price_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```
3. Set webhook endpoint: `https://your-api.railway.app/api/v1/payments/webhook`
4. Events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.deleted`
   - `customer.subscription.paused`

---

## Local Development

```bash
# 1. Start PostgreSQL + Redis (Docker)
docker-compose up db redis -d

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in ANTHROPIC_API_KEY
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd frontend
npm install
cp .env.example .env  # VITE_API_URL=http://localhost:8000
npm run dev
# → http://localhost:5173

# 4. Run tests
cd backend && pytest tests/ -v
```

---

## Environment Variables Summary

| Variable | Where to get it | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com | ✅ Yes |
| `DATABASE_URL` | Supabase dashboard | ✅ Yes |
| `APP_SECRET_KEY` | Generate randomly | ✅ Yes |
| `STRIPE_SECRET_KEY` | Stripe dashboard | When monetizing |
| `STRIPE_PRO_PRICE_ID` | Stripe dashboard | When monetizing |
| `FIELD_ENCRYPTION_KEY` | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` | Production |
