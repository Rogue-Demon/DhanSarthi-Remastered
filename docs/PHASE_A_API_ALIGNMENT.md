# DhanSarthi — Phase A API Contract Alignment & Handoff Report

This report documents the contract alignment completed during Phase A. It matches frontend API expectations with actual FastAPI backend routers, registers corrected endpoints, and details gaps to be solved in later phases.

---

## 1. API Contract Comparison

Below is the structured audit and alignment status for all major app modules.

| Area | Frontend expectation | Actual Backend route | Status | Action taken in Phase A |
| :--- | :--- | :--- | :--- | :--- |
| **Authentication** | `/auth/login`, `/auth/register`, `/auth/logout`, `/auth/me` | `/api/v1/auth/*` | **FIXED** | Aligned fallback API Base URL to include `/api/v1` in `env.config.js`. Corrected request body stringification to not corrupt `FormData`. |
| **Profile** | GET `/profile`, PATCH `/profile` | `/api/v1/profile` | **FIXED** | Mapped GET, POST, and PATCH routes in `endpoints.js`. Synchronized onboarding persona mapping in `AuthProvider.jsx`. |
| **Income** | None (used mock config) | `/api/v1/income` | **FIXED** | Added `/income` REST routes to `endpoints.js`. |
| **Expenses** | None (used mock config) | `/api/v1/expenses` | **FIXED** | Added `/expenses` REST routes to `endpoints.js`. |
| **Transactions Ledger** | `/finance/transactions` | `/api/v1/transactions` | **FIXED** | Aligned endpoint registry key to `/transactions` with dynamic path functions in `endpoints.js`. |
| **Assets & Liabilities** | None (used mock config) | `/api/v1/assets`, `/api/v1/liabilities` | **FIXED** | Added assets and liabilities REST routes to `endpoints.js`. |
| **Loans & Payments** | None (used mock config) | `/api/v1/loans` | **FIXED** | Mapped loan CRUD routes and loan amortization sub-resources (`/loans/{id}/payments`) to `endpoints.js`. |
| **Budgets** | `/finance/budgets` | `/api/v1/budgets` | **FIXED** | Aligned endpoint registry key to `/budgets` in `endpoints.js`. |
| **Goals** | None (used mock config) | `/api/v1/goals` | **FIXED** | Added `/goals` REST routes to `endpoints.js`. |
| **Dashboard** | `/finance/overview` | `/api/v1/dashboard` | **FIXED** | Aligned endpoint registry key to `/dashboard` in `endpoints.js`. |
| **Financial Engine** | None | `/api/v1/financial/*` | **FIXED** | Added all deterministic calculations (summary, cash-flow, savings, net-worth, debt, loan/SIP calculators) to `endpoints.js`. |
| **Financial Intelligence** | None | `/api/v1/financial-intelligence/*` | **FIXED** | Added summary, cash-flow, debt, investment, goals analysis, and scenario simulation routes to `endpoints.js`. |
| **AI Advisor** | `/advisor/chat`, `/advisor/history` | `/api/v1/ai/*` | **FIXED** | Corrected keys in `endpoints.js` to map to `/ai/advisor` and `/ai/conversations/*` with conversation message controllers. |
| **Documents** | None (no UI existed) | `/api/v1/documents` | **FIXED** | Mapped `/documents` upload, extraction, and confirm endpoints. Added native multipart/form-data upload headers for `FormData` bodies. |
| **Market Data** | None | `/api/v1/market/*` | **FIXED** | Added search, quotes, NAV, exchange rates, and index details endpoints to `endpoints.js`. |
| **Reports** | `/reports/download` | None | **MISSING_BACKEND** | Flagged as a contract gap. Handoff to Phase F. |

---

## 2. Remaining Contract Gaps (Handoff Backlog)

The following sections detail integrations and features intentionally left unimplemented in Phase A, mapped to their respective future phases.

### Phase B — Core Frontend Integration
* **Dashboard Integration:** Migrate `DashboardSummary` and widgets to consume `GET /api/v1/dashboard` instead of mock configurations.
* **Ledger CRUD Operations:** Bind add, edit, list, and delete actions for Income, Expenses, Assets, Liabilities, Budgets, Goals, and Transactions.
* **Loan and Payment Tracking:** Integrate `/loans` CRUD and payment scheduling tables in the Debt tab.

### Phase C — Investments & Market Data
* **Investments Ledger:** Bind Investments CRUD and sub-ledger transactions (`/investments/{id}/transactions`).
* **Live Market Feeds:** Integrate search and quote lookups for stocks (`/market/stocks/*`) and mutual funds (`/market/mutual-funds/*`).
* **Interactive Calculators:** Replace current static inputs in SIP and Loan calculators with calculations fetched from `/api/v1/financial/loan/calculate` and `/api/v1/financial/investments/sip/calculate`.
* **Simulators & Scenarios:** Integrate financial intelligence simulations (`/api/v1/financial-intelligence/loan-scenario` and `/api/v1/financial-intelligence/scenario`).

### Phase D — AI Advisor
* **Chat Messenger Threads:** Connect the AI Advisor chat workspace to conversation threads: listing histories (`/api/v1/ai/conversations`), creating threads (`/api/v1/ai/conversations` [POST]), and posting messages with streamed responses (`/api/v1/ai/conversations/{id}/messages`).
* **Personalization and Citations:** Integrate the source citations (`resp.sources`) in the chat UI.

### Phase E — Document Intelligence
* **Document Upload & Audit:** Implement the file upload workspace using `FormData` (now fully supported in `apiClient`).
* **OCR Extraction:** Bind process triggers (`/api/v1/documents/{id}/process`) and results checking (`/api/v1/documents/{id}/extraction`).
* **Import Confirmations:** Bind the selective ledger importer (`/api/v1/documents/{id}/confirm`).

### Phase F — Reports
* **Reports Generator Backend:** Implement the reports generation router on the backend (`/reports` prefix) supplying downloadable summaries.
* **Frontend Export:** Map reports downloads from the Reports page to the newly created backend reports exporter.

### Phase G — Security & Testing
* **Token Expiry Refinement:** Integrate refresh tokens or redirect to login upon credential expiration (handled gracefully in response interceptors).
* **Validation Testing:** Write frontend integration tests targeting `apiClient` error formatting.

### Phase H — Deployment
* **Docker Compose:** Align production environment variables (`VITE_API_BASE_URL` and `DATABASE_URL`) under containers.
