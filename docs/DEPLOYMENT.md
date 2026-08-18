# DhanSarthi — Production Deployment & Operations Guide

This guide describes how to deploy, configure, and operate DhanSarthi in a production environment.

---

## 1. System Architecture

```text
Internet / Clients
       ↓ (HTTPS / Port 443)
Reverse Proxy / Nginx
       ↓
+-------------------+--------------------+
| Frontend (React)  | Backend (FastAPI)  |
+-------------------+--------------------+
       |                     |
       v                     v
Static Files            PostgreSQL + pgvector
```

---

## 2. Environment Configuration

Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to `frontend/.env`.

### Critical Environment Variables

| Variable | Description | Production Guidance |
| -------- | ----------- | ------------------- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://user:pass@host:5432/dbname` |
| `SECRET_KEY` | Application secret key | Cryptographically random string (e.g. 64 bytes) |
| `AUTH_JWT_SECRET` | JWT signing secret key | Cryptographically random string |
| `CORS_ORIGINS` | Allowed CORS origins | Exact domain(s), e.g., `https://app.dhansarthi.com` |
| `AI_PROVIDER` | AI provider | `huggingface` (or `mock` for staging) |
| `AI_PROVIDER_API_KEY` | LLM Provider API token | Production Hugging Face API key |
| `EMBEDDING_PROVIDER` | RAG Embedding provider | `huggingface` (or `mock`) |
| `ALPHA_VANTAGE_API_KEY` | Stock & FX provider key | Alpha Vantage API key |

> [!CAUTION]
> Never commit `.env` files or expose API keys / secret keys in public repositories.

---

## 3. Database & Migrations

### Prerequisites
- PostgreSQL 16+
- `pgvector` extension enabled (`CREATE EXTENSION IF NOT EXISTS vector;`)

### Running Database Migrations
```bash
cd backend
python -m alembic upgrade head
```

---

## 4. Container Deployment (Docker Compose)

```bash
docker-compose up -d --build
```

- **Frontend**: http://localhost (Port 80)
- **Backend API**: http://localhost:8000 (Port 8000)
- **PostgreSQL**: Port 5432

---

## 5. Reverse Proxy & HTTPS Setup

Configure TLS/SSL via Nginx / Certbot:

```nginx
server {
    listen 443 ssl http2;
    server_name app.dhansarthi.com;

    ssl_certificate /etc/letsencrypt/live/app.dhansarthi.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.dhansarthi.com/privkey.pem;

    client_max_body_size 15M;

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 6. Health Checks & Monitoring

- **Health Liveness**: `GET /api/v1/health` (Returns 200 OK if API server is up)
- **Health Readiness**: `GET /api/v1/health/readiness` (Returns 200 OK if DB connection is active)

---

## 7. Database Backup & Disaster Recovery

### Automated Daily Backup Script
```bash
pg_dump -h localhost -U postgres -d dhansarthi -F c -b -v -f /backups/dhansarthi_$(date +%Y%m%d_%H%M%S).dump
```

### Restore Procedure
```bash
pg_restore -h localhost -U postgres -d dhansarthi -v -c /backups/dhansarthi_20260814.dump
```
