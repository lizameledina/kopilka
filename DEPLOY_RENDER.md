# Deploy (Recommended): Vercel + Render + Supabase

This repo has:
- `frontend` — Next.js (Telegram Mini App UI)
- `backend` — FastAPI
- `bot` — aiogram polling bot
- PostgreSQL — Supabase (managed Postgres)

Recommended production-ish setup:
- **Frontend** on **Vercel**
- **Backend** + **Bot** on **Render**
- **Database** on **Supabase**

## 0) Supabase

Create a Supabase project and copy the DB host/password.

Backend `DATABASE_URL` should be:

`postgresql+asyncpg://postgres:<PASSWORD>@<HOST>:5432/postgres?ssl=require`

Example host: `db.<ref>.supabase.co`

## 1) Frontend (Vercel)

1. Import GitHub repo into Vercel.
2. Set **Root Directory** to `frontend`.
3. Add env var:
   - `NEXT_PUBLIC_API_URL` = `https://<YOUR_BACKEND_PUBLIC_URL>`
4. Deploy.

Copy the deployed URL (you'll use it as `WEBAPP_URL` and in BotFather).

## 2) Backend (Render)

Create a **Web Service** from your GitHub repo:
- Root Directory: `backend`
- Runtime: Docker
- Plan: any

Environment variables:
- `DATABASE_URL` = (Supabase URL, includes `ssl=require`)
- `BOT_TOKEN` = BotFather token (used to validate Telegram initData)
- `WEBAPP_URL` = `https://<YOUR_VERCEL_APP>` (for CORS)
- `JWT_SECRET` = long random string

Notes:
- `backend/Dockerfile` uses `$PORT` automatically on Render.
- First start runs Alembic migrations; DB must be reachable.

After deploy, check:
- `https://<render-backend>/docs`
- `https://<render-backend>/openapi.json`

## 3) Bot (Render)

Create a **Background Worker** (or “Worker”) from the same repo:
- Root Directory: `bot`
- Runtime: Docker

Environment variables:
- `BOT_TOKEN` = BotFather token
- `WEBAPP_URL` = `https://<YOUR_VERCEL_APP>`
- `API_URL` (if used in your bot) = `https://<render-backend>`

## 4) Telegram (BotFather)

In BotFather, set your Mini App / Web App URL to:
- `https://<YOUR_VERCEL_APP>`

