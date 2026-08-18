# DhanSarthi — Production Readiness Checklist

Before promoting DhanSarthi to a live production environment, verify every requirement below:

---

## 1. Security & Credentials
- [ ] Production `SECRET_KEY` and `AUTH_JWT_SECRET` generated using strong entropy.
- [ ] No hardcoded passwords or API keys in repository files.
- [ ] `.env` ignored in `.gitignore`.
- [ ] Database credentials isolated to environment variables.
- [ ] Production API keys provisioned for Hugging Face and Alpha Vantage.

## 2. Infrastructure & Hosting
- [ ] Domain name configured and pointing to reverse proxy load balancer.
- [ ] HTTPS / TLS certificate issued (e.g. Let's Encrypt / AWS ACM).
- [ ] HTTP to HTTPS automatic redirection enabled.
- [ ] Security headers enabled (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `HSTS`).
- [ ] Request body size limit configured to 15MB to support document processing.

## 3. Database & Storage
- [ ] Managed PostgreSQL 16 instance provisioned.
- [ ] `pgvector` extension installed and verified.
- [ ] Alembic migrations run to `head` on production DB.
- [ ] Automated daily database backups scheduled.
- [ ] Backup restore procedure tested and verified.

## 4. Backend & Frontend Operations
- [ ] Backend running via Uvicorn/Gunicorn process manager (`workers=4`).
- [ ] CORS allowed origins set explicitly to production domain(s) (no `*`).
- [ ] Frontend build generated via `npm run build` using production `VITE_API_BASE_URL`.
- [ ] Nginx SPA fallback enabled (`try_files $uri /index.html;`).
- [ ] Health readiness endpoint monitored via Uptime / Health check service.

## 5. Final Verification
- [ ] All 410 backend pytest tests passing.
- [ ] Frontend linting exits with 0 errors.
- [ ] End-to-end smoke testing verified (Auth, Finance, Investments, AI Advisor, Documents, Reports).
