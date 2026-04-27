# Deploy to Cloud.ru (Container Apps + Managed PostgreSQL)

This project consists of:
- `frontend` (Next.js, Telegram Mini App UI)
- `backend` (FastAPI)
- `bot` (aiogram polling bot)
- PostgreSQL (recommended: Cloud.ru **Managed PostgreSQL**)

Below is a practical deployment path on Cloud.ru **Evolution** using:
- **Artifact Registry** (for Docker images)
- **Container Apps** (to run containers)
- **Managed PostgreSQL®** (database)

## 1) Create Cloud resources

### 1.1 Artifact Registry
Create a registry in Cloud.ru console and copy its URI.

Registry URI looks like:
`<registry_name>.cr.cloud.ru`

Authenticate with personal key:
`docker login <registry_name>.cr.cloud.ru -u <key_id> -p <key_secret>`

### 1.2 Managed PostgreSQL
Create a Managed PostgreSQL cluster and a database/user for Kopilka.

You will need a connection string for `DATABASE_URL` (see env vars below).

## 2) Build & push Docker images

From the repo root:

### 2.1 Backend
```bash
docker build -t <registry_name>.cr.cloud.ru/kopilka-backend:latest ./backend --platform linux/amd64
docker push <registry_name>.cr.cloud.ru/kopilka-backend:latest
```

### 2.2 Frontend
The frontend image bakes `NEXT_PUBLIC_API_URL` into Next.js rewrites during build, so pass it as a build-arg.

```bash
docker build \
  -t <registry_name>.cr.cloud.ru/kopilka-frontend:latest ./frontend \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_URL=https://<public-backend-url>
docker push <registry_name>.cr.cloud.ru/kopilka-frontend:latest
```

### 2.3 Bot
```bash
docker build -t <registry_name>.cr.cloud.ru/kopilka-bot:latest ./bot --platform linux/amd64
docker push <registry_name>.cr.cloud.ru/kopilka-bot:latest
```

## 3) Create Container Apps

Create three Container Apps (services):

### 3.1 Backend service (public)
- Container port: `8000`
- Public address: **enabled** (you need a public URL)
- Optional: set liveness probe to `GET /health` (backend exposes it).

### 3.2 Frontend service (public)
- Container port: `3000`
- Public address: **enabled**

### 3.3 Bot service (no public address)
- Public address: **disabled**
- Min instances: `1`, Max instances: `1`
- No probes (bot does polling, not HTTP).

Container Apps creates a public URL when the “Public address” option is enabled.

## 4) Environment variables (Container Apps)

### Backend
- `DATABASE_URL` = Postgres URL from Managed PostgreSQL (TLS/host/port per console)
- `WEBAPP_URL` = `https://<public-frontend-url>` (for CORS)
- `JWT_SECRET` = strong random string

### Frontend
- `NEXT_PUBLIC_API_URL` must match the backend public URL **used at build time**.
  - If backend URL changes, rebuild + push new frontend image.

### Bot
- `BOT_TOKEN` = BotFather token (rotate if leaked)
- `WEBAPP_URL` = `https://<public-frontend-url>`

## 5) Telegram config

In BotFather:
- set the Mini App / Web App URL to the frontend public URL from Container Apps.

## 6) Operational checks
- Backend: open `https://<backend-url>/health` → should return `{"status":"ok"}`
- Frontend: open `https://<frontend-url>` in browser
- Telegram: `/start` → button opens the Mini App
