# DhanSarthi — DEPLOYMENT GUIDE

> Defines how DhanSarthi should be configured, deployed, tested, monitored,
> and maintained across development, staging, and production.

---

# 1. DEPLOYMENT OVERVIEW

DhanSarthi consists of several major components:

```text
                    DhanSarthi
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Frontend       Backend        Database
        React         FastAPI       PostgreSQL
          │              │              │
          │              ├──── AI ──────┤
          │              │              │
          │              └──── RAG ─────
          │
          ▼
       Browser
````

Production deployment should keep these components logically separated.

---

# 2. ENVIRONMENTS

Use separate environments:

```text
Development
     ↓
Staging
     ↓
Production
```

Each environment should have its own:

```text
Database
Environment Variables
Storage
AI Configuration
RAG Configuration
```

Never use the production database for local development.

---

# 3. PROJECT COMPONENTS

Expected deployment components:

```text
Frontend
    React + TypeScript

Backend
    Python + FastAPI

Database
    PostgreSQL

Vector Search
    pgvector

AI
    Configured AI Provider

RAG
    Knowledge + Embeddings + Retrieval

File Storage
    Private Object/File Storage
```

The exact cloud provider may change.

The architecture should remain provider-independent where practical.

---

# 4. FRONTEND DEPLOYMENT

The React frontend should be built as a production application.

Typical flow:

```text
React Source
    ↓
Install Dependencies
    ↓
Run Tests
    ↓
Build
    ↓
Production Assets
    ↓
Static Hosting / CDN
```

Before deployment:

```text
npm install
npm run lint
npm run build
```

If tests exist:

```text
npm test
```

The exact commands must follow the project's package configuration.

---

# 5. FRONTEND ENVIRONMENT VARIABLES

Frontend environment variables must contain only values safe to expose to the
browser.

Example:

```text
API_BASE_URL
PUBLIC_APP_NAME
PUBLIC_ENVIRONMENT
```

Never expose:

```text
Database Password
AI Provider Secret
API Secret
JWT Signing Secret
Private Storage Credentials
```

Frontend variables are not secret.

---

# 6. BACKEND DEPLOYMENT

FastAPI production flow:

```text
Python Source
    ↓
Install Dependencies
    ↓
Run Tests
    ↓
Database Migration
    ↓
Start FastAPI
    ↓
Health Check
    ↓
Production Traffic
```

Use a production ASGI server configuration.

Do not use a development server configuration for production.

---

# 7. BACKEND ENVIRONMENT VARIABLES

Backend secrets must be provided through the deployment environment.

Examples:

```text
DATABASE_URL
AI_PROVIDER_API_KEY
EMBEDDING_API_KEY
SECRET_KEY
STORAGE credentials
OTHER_PROVIDER_SECRETS
```

Do not commit these values to Git.

Provide an example environment file:

```text
.env.example
```

containing variable names but not real secrets.

---

# 8. DATABASE DEPLOYMENT

Production PostgreSQL should be deployed using a managed or properly
maintained PostgreSQL service.

Required considerations:

```text
Persistent Storage
Backups
Encryption
Connection Security
Monitoring
Connection Pooling
Migration Management
```

If pgvector is required:

```text
PostgreSQL
+
pgvector
```

must be supported by the selected deployment environment.

---

# 9. DATABASE MIGRATIONS

Production schema changes must use migrations.

Flow:

```text
Code Change
    ↓
Migration Generated
    ↓
Migration Reviewed
    ↓
Backup / Safety Check
    ↓
Migration Applied
    ↓
Application Updated
```

Never rely on automatic destructive schema creation in production.

---

# 10. RAG DEPLOYMENT

RAG consists of:

```text
Knowledge Sources
       ↓
Ingestion
       ↓
Chunking
       ↓
Embeddings
       ↓
PostgreSQL + pgvector
       ↓
Retrieval
       ↓
AI Advisor
```

The embedding model configuration must be available to the backend.

Knowledge ingestion should preferably be a controlled process rather than
running automatically on every API request.

---

# 11. AI PROVIDER

AI provider credentials must exist only on the backend.

Preferred:

```text
React
  ↓
FastAPI
  ↓
AI Service
  ↓
AI Provider
```

Never:

```text
React
  ↓
AI Provider directly
```

This prevents exposing provider credentials and keeps AI orchestration under
backend control.

---

# 12. FILE STORAGE

User-uploaded files should use private storage.

Possible storage:

```text
Private Object Storage
Private File Storage
```

Files should not automatically become publicly accessible.

Database stores metadata such as:

```text
Document ID
User ID
Filename
Storage Key
File Type
Processing Status
```

The database should not be used as the primary location for large binary files
unless there is a deliberate reason.

---

# 13. NETWORK ARCHITECTURE

A production architecture may look like:

```text
                   Internet
                      │
                      ▼
                Frontend / CDN
                      │
                      ▼
                 HTTPS / API
                      │
                      ▼
                 FastAPI
                 /      \
                /        \
               ▼          ▼
        PostgreSQL       AI/RAG
                            │
                            ▼
                       AI Provider
```

Database and private infrastructure should not be unnecessarily exposed to
the public internet.

---

# 14. HTTPS

Production traffic must use HTTPS.

HTTPS should cover:

```text
Browser → Frontend
Browser → API
API → External Services
```

Never transmit sensitive financial information over unencrypted HTTP in
production.

---

# 15. CORS

Configure CORS explicitly.

Production should allow only trusted frontend origins.

Avoid:

```text
allow_origins=["*"]
```

for a sensitive production application unless there is a specific and
well-understood reason.

---

# 16. HEALTH CHECKS

The backend should expose a basic health endpoint:

```text
GET /health
```

Optional readiness endpoint:

```text
GET /health/ready
```

Health checks may verify:

```text
Application
Database Connectivity
Required Dependencies
```

Do not expose sensitive configuration through health endpoints.

---

# 17. LOGGING

Production logs should provide enough information for debugging without
exposing sensitive financial information.

Log:

```text
Request ID
Timestamp
Endpoint
Status
Latency
Error Code
Service Information
```

Avoid logging:

```text
Passwords
API Keys
Tokens
Full Financial Profiles
Private Documents
Full AI Prompts containing sensitive data
```

---

# 18. ERROR MONITORING

Production should monitor:

```text
Backend Errors
Frontend Errors
Database Errors
AI Provider Failures
RAG Failures
Document Processing Failures
Timeouts
High Latency
```

Use an error-monitoring platform when appropriate.

---

# 19. PERFORMANCE MONITORING

Track important metrics such as:

```text
API Response Time
AI Response Time
Database Query Time
RAG Retrieval Time
Document Processing Time
Error Rate
Request Rate
```

For AI:

```text
Token Usage
Provider Latency
Failure Rate
```

should be monitored where available.

---

# 20. RATE LIMITING

Rate-limit sensitive or expensive endpoints.

Especially:

```text
AI Chat
Document Upload
Document Processing
Expensive Financial Analysis
```

This protects the application from:

```text
Abuse
Accidental Excessive Usage
Cost Spikes
Denial-of-Service Attempts
```

---

# 21. AI COST CONTROL

AI requests may create significant operating costs.

Implement appropriate controls such as:

```text
Request Limits
Token Limits
Context Limits
Timeouts
Retry Limits
Model Selection
User Usage Limits
```

Do not retry failed AI requests indefinitely.

---

# 22. DATABASE BACKUPS

Production PostgreSQL must have automated backups.

Consider:

```text
Backup Frequency
Retention
Encryption
Point-in-Time Recovery
Restore Testing
```

Important:

> A backup is not considered reliable until restoration has been tested.

---

# 23. DISASTER RECOVERY

Define recovery procedures for:

```text
Database Failure
Backend Failure
Storage Failure
AI Provider Failure
Deployment Failure
```

At minimum:

```text
Identify Failure
    ↓
Stop Further Damage
    ↓
Restore Service
    ↓
Verify Data
    ↓
Verify AI/RAG
    ↓
Resume Traffic
```

---

# 24. DEPLOYMENT STRATEGY

Prefer:

```text
Development
    ↓
Pull Request
    ↓
Tests
    ↓
Staging
    ↓
Verification
    ↓
Production
```

Avoid directly deploying untested changes to production.

---

# 25. CI/CD

A CI/CD pipeline should ideally perform:

```text
Install
   ↓
Lint
   ↓
Type Check
   ↓
Unit Tests
   ↓
Integration Tests
   ↓
Build
   ↓
Security Checks
   ↓
Deploy
```

The exact CI/CD provider may vary.

---

# 26. DOCKER

Docker may be used to make development and deployment reproducible.

Possible services:

```text
frontend
backend
postgres
```

For local development:

```text
Docker Compose
```

may be used.

Production container configuration should be optimized separately from local
development.

---

# 27. SECRET MANAGEMENT

Never commit secrets to Git.

Do not store secrets inside:

```text
Source Code
README
Dockerfile
Frontend Bundle
Database
Logs
```

Use:

```text
Environment Variables
Secret Manager
Platform Secret Storage
```

where appropriate.

---

# 28. PRODUCTION CONFIGURATION

Production configuration should define:

```text
Environment
Database
AI Provider
Embedding Provider
Storage
Allowed Origins
Logging
Rate Limits
Feature Flags
```

Avoid hardcoding environment-specific values.

---

# 29. DEPLOYMENT ROLLBACK

Every production deployment should have a rollback strategy.

Example:

```text
New Release
    ↓
Health Check
    ↓
Problem?
   / \
 Yes  No
  ↓    ↓
Rollback Continue
```

Database migrations must also consider rollback or forward-recovery strategies.

---

# 30. AI/RAG FAILURE HANDLING

DhanSarthi should remain understandable when AI services fail.

Example:

```text
AI Provider unavailable
        ↓
Controlled Error
        ↓
User receives:
"AI Advisor is temporarily unavailable.
Please try again later."
```

Never expose raw provider errors.

If RAG fails, the AI must not pretend that retrieval succeeded.

---

# 31. DOCUMENT PROCESSING FAILURE

If document processing fails:

```text
Upload
  ↓
Processing
  ↓
Failure
  ↓
FAILED / REVIEW_REQUIRED
```

The user should receive a clear status.

Do not silently treat an unprocessed document as successfully analyzed.

---

# 32. PRODUCTION SECURITY CHECKLIST

Before production:

```text
[ ] HTTPS enabled
[ ] Secrets removed from source code
[ ] Production CORS configured
[ ] Database private
[ ] Database backups enabled
[ ] User data isolation tested
[ ] File storage private
[ ] AI keys backend-only
[ ] Rate limiting configured
[ ] Error monitoring enabled
[ ] Logs reviewed for sensitive information
[ ] Security headers configured
[ ] Dependencies reviewed
```

---

# 33. APPLICATION CHECKLIST

Before deployment:

```text
[ ] Frontend builds successfully
[ ] Backend starts successfully
[ ] Database migrations succeed
[ ] Health endpoint works
[ ] API endpoints tested
[ ] AI chat tested
[ ] RAG retrieval tested
[ ] Financial calculations tested
[ ] Document processing tested
[ ] User isolation tested
[ ] Error handling tested
```

---

# 34. POST-DEPLOYMENT CHECKLIST

Immediately after deployment:

```text
[ ] Frontend loads
[ ] API reachable
[ ] Database connected
[ ] Health check passes
[ ] User profile works
[ ] Financial dashboard works
[ ] Transactions work
[ ] Investments work
[ ] Loans work
[ ] AI Advisor works
[ ] RAG retrieval works
[ ] Document upload works
[ ] Logs are healthy
```

---

# 35. DEPLOYMENT RULES FOR ANTIGRAVITY

When preparing DhanSarthi for deployment:

1. Read all relevant documentation before changing infrastructure.

2. Never commit secrets.

3. Never expose database credentials to React.

4. Never expose AI provider keys to React.

5. Use environment variables for environment-specific configuration.

6. Use migrations for database changes.

7. Test builds before deployment.

8. Test the backend health endpoint.

9. Test critical API endpoints.

10. Test AI and RAG independently.

11. Verify user-data isolation.

12. Keep uploaded documents private.

13. Configure production CORS explicitly.

14. Use HTTPS.

15. Configure backups before production.

16. Have a rollback strategy.

17. Do not deploy untested destructive database changes.

18. Do not expose internal errors to users.

19. Monitor AI usage and cost.

20. Update deployment documentation when infrastructure changes.

---

# 36. RECOMMENDED PRODUCTION FLOW

```text
                         GIT
                          │
                          ▼
                    CI / Validation
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
        Frontend Build            Backend Build
             │                         │
             ▼                         ▼
          Frontend                  FastAPI
             │                         │
             │                    ┌────┴────┐
             │                    ▼         ▼
             │               PostgreSQL   AI/RAG
             │                              │
             │                              ▼
             │                        AI Provider
             │
             └──────────────┬───────────────
                            ▼
                         USERS
```

---

# 37. FINAL DEPLOYMENT CONTRACT

DhanSarthi production deployment must prioritize:

```text
Security
Reliability
Data Privacy
Financial Data Integrity
Observability
Recoverability
Cost Control
Maintainability
```

The deployment environment must never weaken the application's core rules.

In particular:

```text
Frontend
    ≠
Secrets

AI
    ≠
Direct Database Access

User
    ≠
Another User's Data

RAG
    ≠
Source of Financial Calculations

Production
    ≠
Untested Development Environment
```

# END OF DEPLOYMENT_GUIDE.md

````

