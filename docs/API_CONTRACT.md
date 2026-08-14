# DhanSarthi — Authoritative API Contract Reference

This document serves as the authoritative integration contract between the DhanSarthi React frontend and the FastAPI backend. It reflects the exact paths, parameters, schemas, and authentication requirements active in the backend codebase as of Phase A.

---

## 1. Authentication

All authentication endpoints are registered under the `/auth` prefix. JWT session state is handled on the client using local storage.

| Method | Path | Auth | Request Model | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/auth/register` | None | `UserRegisterRequest` | `AuthenticatedUserResponse` (201) | `409 Conflict` (Email exists), `422` | Register page | Implemented + verified |
| **POST** | `/api/v1/auth/login` | None | `LoginRequest` | `TokenResponse` (200) | `401 Unauthorized`, `422` | Login page | Implemented + verified |
| **POST** | `/api/v1/auth/logout` | Required | None | `{"detail": "..."}` (200) | `401 Unauthorized` | Profile switcher / Header | Implemented + verified |
| **GET** | `/api/v1/auth/me` | Required | None | `AuthenticatedUserResponse` (200) | `401 Unauthorized` | Auth provider initialization | Implemented + verified |

* **Token Behavior:** The client attaches the received token string as an `Authorization: Bearer <token>` header for all authenticated requests. On receiving an `HTTP 401`, client interceptors automatically discard the local session.

---

## 2. Profile Management

User financial profiles, displays, and dynamic persona configurations.

| Method | Path | Auth | Request Model | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/profile` | Required | None | `ProfileResponse` (200) | `401`, `404` | Auth provider session check | Implemented + verified |
| **POST** | `/api/v1/profile` | Required | `ProfileCreate` | `ProfileResponse` (201) | `401`, `409`, `422` | Onboarding persona select | Implemented + verified |
| **PATCH** | `/api/v1/profile` | Required | `ProfileUpdate` | `ProfileResponse` (200) | `401`, `404`, `422` | Profile settings / switcher | Implemented + verified |

---

## 3. Finance (Authoritative Ledger Transactions & Records)

CRUD operations on stored ledger categories.

### Income Records

| Method | Path | Auth | Request Model / Parameters | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/income` | Required | Query: `page`, `page_size`, `date_from`, `date_to`, `category`, `frequency` | `PaginatedResponse_IncomeResponse_` (200) | `401`, `422` | Finance: Income tab | Implemented + verified |
| **POST** | `/api/v1/income` | Required | `IncomeCreate` | `IncomeResponse` (201) | `401`, `422` | Finance: Add income | Implemented + verified |
| **GET** | `/api/v1/income/{income_id}` | Required | Path: `income_id` | `IncomeResponse` (200) | `401`, `403`, `404` | Finance: View record | Implemented + verified |
| **PATCH** | `/api/v1/income/{income_id}` | Required | Path: `income_id`, Body: `IncomeUpdate` | `IncomeResponse` (200) | `401`, `403`, `404`, `422` | Finance: Edit record | Implemented + verified |
| **DELETE** | `/api/v1/income/{income_id}` | Required | Path: `income_id` | None (204 No Content) | `401`, `403`, `404` | Finance: Delete record | Implemented + verified |

### Expense Records

| Method | Path | Auth | Request Model / Parameters | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/expenses` | Required | Query: `page`, `page_size`, `date_from`, `date_to`, `category`, `frequency` | `PaginatedResponse_ExpenseResponse_` (200) | `401`, `422` | Finance: Expenses tab | Implemented + verified |
| **POST** | `/api/v1/expenses` | Required | `ExpenseCreate` | `ExpenseResponse` (201) | `401`, `422` | Finance: Add expense | Implemented + verified |
| **GET** | `/api/v1/expenses/{expense_id}` | Required | Path: `expense_id` | `ExpenseResponse` (200) | `401`, `403`, `404` | Finance: View record | Implemented + verified |
| **PATCH** | `/api/v1/expenses/{expense_id}` | Required | Path: `expense_id`, Body: `ExpenseUpdate` | `ExpenseResponse` (200) | `401`, `403`, `404`, `422` | Finance: Edit record | Implemented + verified |
| **DELETE** | `/api/v1/expenses/{expense_id}` | Required | Path: `expense_id` | None (204 No Content) | `401`, `403`, `404` | Finance: Delete record | Implemented + verified |

### Transaction Ledger

| Method | Path | Auth | Request Model / Parameters | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/transactions` | Required | Query: `page`, `page_size`, `date_from`, `date_to`, `category`, `transaction_type` | `PaginatedResponse_TransactionResponse_` (200) | `401`, `422` | Finance: Ledger overview | Implemented + verified |
| **POST** | `/api/v1/transactions` | Required | `TransactionCreate` | `TransactionResponse` (201) | `401`, `422` | Finance: Add transaction | Implemented + verified |
| **GET** | `/api/v1/transactions/{transaction_id}` | Required | Path: `transaction_id` | `TransactionResponse` (200) | `401`, `403`, `404` | Finance: View ledger record | Implemented + verified |
| **PATCH** | `/api/v1/transactions/{transaction_id}` | Required | Path: `transaction_id`, Body: `TransactionUpdate` | `TransactionResponse` (200) | `401`, `403`, `404`, `422` | Finance: Edit ledger record | Implemented + verified |
| **DELETE** | `/api/v1/transactions/{transaction_id}` | Required | Path: `transaction_id` | None (204 No Content) | `401`, `403`, `404` | Finance: Delete ledger record | Implemented + verified |

### Stored Assets & Liabilities

| Method | Path | Auth | Request Model / Parameters | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/assets` | Required | Query: `page`, `page_size`, `asset_type` | `PaginatedResponse_AssetResponse_` (200) | `401`, `422` | Finance: Assets tab | Implemented + verified |
| **POST** | `/api/v1/assets` | Required | `AssetCreate` | `AssetResponse` (201) | `401`, `422` | Finance: Add asset | Implemented + verified |
| **PATCH** | `/api/v1/assets/{asset_id}` | Required | Path: `asset_id`, Body: `AssetUpdate` | `AssetResponse` (200) | `401`, `403`, `404`, `422` | Finance: Edit asset | Implemented + verified |
| **DELETE** | `/api/v1/assets/{asset_id}` | Required | Path: `asset_id` | None (204 No Content) | `401`, `403`, `404` | Finance: Delete asset | Implemented + verified |
| **GET** | `/api/v1/liabilities` | Required | Query: `page`, `page_size`, `liability_type` | `PaginatedResponse_LiabilityResponse_` (200) | `401`, `422` | Finance: Liabilities tab | Implemented + verified |
| **POST** | `/api/v1/liabilities` | Required | `LiabilityCreate` | `LiabilityResponse` (201) | `401`, `422` | Finance: Add liability | Implemented + verified |
| **PATCH** | `/api/v1/liabilities/{liability_id}` | Required | Path: `liability_id`, Body: `LiabilityUpdate` | `LiabilityResponse` (200) | `401`, `403`, `404`, `422` | Finance: Edit liability | Implemented + verified |
| **DELETE** | `/api/v1/liabilities/{liability_id}` | Required | Path: `liability_id` | None (204 No Content) | `401`, `403`, `404` | Finance: Delete liability | Implemented + verified |

### Loan Obligations

| Method | Path | Auth | Request Model / Parameters | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/loans` | Required | Query: `page`, `page_size`, `loan_type`, `status` | `PaginatedResponse_LoanResponse_` (200) | `401`, `422` | Finance: Debt tab / Loans | Implemented + verified |
| **POST** | `/api/v1/loans` | Required | `LoanCreate` | `LoanResponse` (201) | `401`, `422` | Finance: Add loan | Implemented + verified |
| **GET** | `/api/v1/loans/{loan_id}` | Required | Path: `loan_id` | `LoanResponse` (200) | `401`, `403`, `404` | Finance: View loan details | Implemented + verified |
| **PATCH** | `/api/v1/loans/{loan_id}` | Required | Path: `loan_id`, Body: `LoanUpdate` | `LoanResponse` (200) | `401`, `403`, `404`, `422` | Finance: Edit loan parameters | Implemented + verified |
| **DELETE** | `/api/v1/loans/{loan_id}` | Required | Path: `loan_id` | None (204 No Content) | `401`, `403`, `404` | Finance: Delete loan record | Implemented + verified |
| **GET** | `/api/v1/loans/{loan_id}/payments` | Required | Path: `loan_id` | `list[LoanPaymentResponse]` (200) | `401`, `403`, `404` | Finance: Amortization tracker | Implemented + verified |
| **POST** | `/api/v1/loans/{loan_id}/payments` | Required | Path: `loan_id`, Body: `LoanPaymentCreate` | `LoanPaymentResponse` (201) | `401`, `403`, `404`, `422` | Finance: Record loan payment | Implemented + verified |
| **GET** | `/api/v1/loans/{loan_id}/payments/{payment_id}` | Required | Path: `loan_id`, `payment_id` | `LoanPaymentResponse` (200) | `401`, `403`, `404` | Finance: View loan payment | Implemented + verified |

### Budget Allocation

| Method | Path | Auth | Request Model / Parameters | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/budgets` | Required | Query: `page`, `page_size`, `category`, `period` | `PaginatedResponse_BudgetResponse_` (200) | `401`, `422` | Finance: Budget tab | Implemented + verified |
| **POST** | `/api/v1/budgets` | Required | `BudgetCreate` | `BudgetResponse` (201) | `401`, `422` | Finance: Set category budget | Implemented + verified |
| **GET** | `/api/v1/budgets/{budget_id}` | Required | Path: `budget_id` | `BudgetResponse` (200) | `401`, `403`, `404` | Finance: View budget details | Implemented + verified |
| **PATCH** | `/api/v1/budgets/{budget_id}` | Required | Path: `budget_id`, Body: `BudgetUpdate` | `BudgetResponse` (200) | `401`, `403`, `404`, `422` | Finance: Edit budget limits | Implemented + verified |
| **DELETE** | `/api/v1/budgets/{budget_id}` | Required | Path: `budget_id` | None (204 No Content) | `401`, `403`, `404` | Finance: Remove budget constraint | Implemented + verified |

### Financial Goals

| Method | Path | Auth | Request Model / Parameters | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/goals` | Required | Query: `page`, `page_size`, `status`, `priority` | `PaginatedResponse_GoalResponse_` (200) | `401`, `422` | Finance: Goals tab | Implemented + verified |
| **POST** | `/api/v1/goals` | Required | `GoalCreate` | `GoalResponse` (201) | `401`, `422` | Finance: Create saving goal | Implemented + verified |
| **GET** | `/api/v1/goals/{goal_id}` | Required | Path: `goal_id` | `GoalResponse` (200) | `401`, `403`, `404` | Finance: View goal progress | Implemented + verified |
| **PATCH** | `/api/v1/goals/{goal_id}` | Required | Path: `goal_id`, Body: `GoalUpdate` | `GoalResponse` (200) | `401`, `403`, `404`, `422` | Finance: Edit goal details | Implemented + verified |
| **DELETE** | `/api/v1/goals/{goal_id}` | Required | Path: `goal_id` | None (204 No Content) | `401`, `403`, `404` | Finance: Remove goal | Implemented + verified |

---

## 4. Dashboard Summary

Consolidated financial summary and context versions for the main workspace view.

| Method | Path | Auth | Request Model / Parameters | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/dashboard` | Required | Query: `date_from`, `date_to` | `DashboardResponse` (200) | `401`, `422` | Core Dashboard | Implemented + verified |

---

## 5. Financial Engine (Deterministic Calculations)

Calculates values deterministically without database persistence.

| Method | Path | Auth | Request Model / Parameters | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/financial/summary` | Required | Query: `date_from`, `date_to` | `FinancialSummaryResponse` (200) | `401`, `422` | Finance Overview header | Implemented + verified |
| **GET** | `/api/v1/financial/cash-flow` | Required | Query: `date_from`, `date_to` | dynamic dictionary (200) | `401`, `422` | Finance: CashFlow charts | Implemented + verified |
| **GET** | `/api/v1/financial/savings` | Required | Query: `date_from`, `date_to` | dynamic dictionary (200) | `401`, `422` | Finance: Savings overview | Implemented + verified |
| **GET** | `/api/v1/financial/net-worth` | Required | None | dynamic dictionary (200) | `401` | Finance: Net worth monitor | Implemented + verified |
| **GET** | `/api/v1/financial/debt` | Required | None | dynamic dictionary (200) | `401` | Finance: Debt monitoring | Implemented + verified |
| **GET** | `/api/v1/financial/investments/summary` | Required | None | dynamic dictionary (200) | `401` | Investments: Portfolio summary | Implemented + verified |
| **POST** | `/api/v1/financial/loan/calculate` | None | `LoanCalculateRequest` | dynamic dictionary (EMI + schedule) (200) | `422` | Finance: Loan calculators | Implemented + verified |
| **POST** | `/api/v1/financial/investments/sip/calculate` | None | `SIPCalculateRequest` | dynamic dictionary (projections) (200) | `422` | Investments: SIP calculators | Implemented + verified |
| **GET** | `/api/v1/financial/budget` | Required | None | dynamic dictionary (utilization metrics) (200) | `401` | Finance: Budget status | Implemented + verified |
| **GET** | `/api/v1/financial/goals` | Required | None | list of goal projections (200) | `401` | Finance: Goal progress charts | Implemented + verified |
| **GET** | `/api/v1/financial/context` | Required | Query: `date_from`, `date_to` | `FinancialContextResponse` (200) | `401`, `422` | Diagnostic diagnostics | Implemented + verified |

---

## 6. Financial Intelligence (Rule-Based Insights)

Provides structural analyzers and Compounding SIP scenario comparisons.

| Method | Path | Auth | Request Model / Parameters | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/financial-intelligence/summary` | Required | Query: `date_from`, `date_to` | `FinancialIntelligenceSummary` (200) | `401`, `422` | Dashboard alert widgets | Implemented + verified |
| **GET** | `/api/v1/financial-intelligence/cash-flow` | Required | Query: `date_from`, `date_to` | `FinancialInsight` (200) | `401`, `422` | CashFlow insights cards | Implemented + verified |
| **GET** | `/api/v1/financial-intelligence/debt` | Required | Query: `date_from`, `date_to` | `FinancialInsight` (200) | `401`, `422` | Debt insights cards | Implemented + verified |
| **GET** | `/api/v1/financial-intelligence/investments` | Required | Query: `date_from`, `date_to` | `FinancialInsight` (200) | `401`, `422` | Investment allocation insights | Implemented + verified |
| **GET** | `/api/v1/financial-intelligence/goals` | Required | Query: `date_from`, `date_to` | `list[FinancialInsight]` (200) | `401`, `422` | Goal feasibility details | Implemented + verified |
| **POST** | `/api/v1/financial-intelligence/loan-scenario` | Required | `LoanScenarioInput` | `LoanScenarioResult` (200) | `401`, `422` | Finance: Simulators (DTI/EMI) | Implemented + verified |
| **POST** | `/api/v1/financial-intelligence/scenario` | Required | `GenericScenarioInput` | `GenericScenarioResult` (200) | `401`, `422` | Finance: Scenario compounders | Implemented + verified |

---

## 7. Investments Ledger

Custom assets and transaction allocations for stocks, mutual funds, SIPs, and other products.

| Method | Path | Auth | Request Model / Parameters | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/investments` | Required | Query: `page`, `page_size`, `investment_type` | `PaginatedResponse_InvestmentResponse_` (200) | `401`, `422` | Investments tabs | Implemented + verified |
| **POST** | `/api/v1/investments` | Required | `InvestmentCreate` | `InvestmentResponse` (201) | `401`, `422` | Investments: Add investment | Implemented + verified |
| **GET** | `/api/v1/investments/{investment_id}` | Required | Path: `investment_id` | `InvestmentResponse` (200) | `401`, `403`, `404` | Investments: View parameters | Implemented + verified |
| **PATCH** | `/api/v1/investments/{investment_id}` | Required | Path: `investment_id`, Body: `InvestmentUpdate` | `InvestmentResponse` (200) | `401`, `403`, `404`, `422` | Investments: Edit holding value | Implemented + verified |
| **DELETE** | `/api/v1/investments/{investment_id}` | Required | Path: `investment_id` | None (204 No Content) | `401`, `403`, `404` | Investments: Remove holding | Implemented + verified |
| **GET** | `/api/v1/investments/{investment_id}/transactions` | Required | Path: `investment_id` | `list[InvestmentTransactionResponse]` (200) | `401`, `403`, `404` | Investments: Ledger transactions | Implemented + verified |
| **POST** | `/api/v1/investments/{investment_id}/transactions` | Required | Path: `investment_id`, Body: `InvestmentTransactionCreate` | `InvestmentTransactionResponse` (201) | `401`, `403`, `404`, `422` | Investments: Record buy/sell | Implemented + verified |
| **GET** | `/api/v1/investments/{investment_id}/transactions/{transaction_id}` | Required | Path: `investment_id`, `transaction_id` | `InvestmentTransactionResponse` (200) | `401`, `403`, `404` | Investments: View transaction detail | Implemented + verified |

---

## 8. AI Advisor & Conversations

Natural-language explanations, contextual prompts, and chat histories.

| Method | Path | Auth | Request Model / Parameters | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/ai/advisor` | Required | `AIAdvisorRequest` | `AIAdvisorResponse` (200) | `401`, `500` (misconfigured), `422` | AI Advisor prompt widget | Implemented + verified |
| **POST** | `/api/v1/ai/conversations` | Required | `ConversationCreateRequest` | `ConversationResponse` (201) | `401`, `422` | AIAdvisor: New chat thread | Implemented + verified |
| **GET** | `/api/v1/ai/conversations` | Required | Query: `skip`, `limit` | `ConversationListResponse` (200) | `401`, `422` | AIAdvisor: Saved list tab | Implemented + verified |
| **GET** | `/api/v1/ai/conversations/{conversation_id}` | Required | Path: `conversation_id` | `ConversationDetailResponse` (200) | `401`, `403`, `404` | AIAdvisor: Thread history view | Implemented + verified |
| **DELETE** | `/api/v1/ai/conversations/{conversation_id}` | Required | Path: `conversation_id` | None (204 No Content) | `401`, `403`, `404` | AIAdvisor: Delete thread | Implemented + verified |
| **POST** | `/api/v1/ai/conversations/{conversation_id}/messages` | Required | Path: `conversation_id`, Body: `SendMessageRequest` | `SendMessageResponse` (201) | `401`, `403`, `404`, `502` (LLM timeout), `422` | AIAdvisor: Chat messenger | Implemented + verified |

---

## 9. Document Intelligence

File processing, metadata extraction (salary slips, bank statements), and ledger imports.

| Method | Path | Auth | Request Model / Parameters | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/documents` | Required | Multipart: `file` | `DocumentResponse` (201) | `401`, `413` (Too large), `415` (Unsupported), `409` (Duplicate), `422` | None (Handoff to Phase E) | Implemented + verified |
| **GET** | `/api/v1/documents` | Required | Query: `skip`, `limit` | `DocumentListResponse` (200) | `401`, `422` | None (Handoff to Phase E) | Implemented + verified |
| **GET** | `/api/v1/documents/{document_id}` | Required | Path: `document_id` | `DocumentResponse` (200) | `401`, `403`, `404` | None (Handoff to Phase E) | Implemented + verified |
| **DELETE** | `/api/v1/documents/{document_id}` | Required | Path: `document_id` | None (204 No Content) | `401`, `403`, `404` | None (Handoff to Phase E) | Implemented + verified |
| **POST** | `/api/v1/documents/{document_id}/process` | Required | Path: `document_id` | `ExtractionResponse` (200) | `401`, `403`, `404` | None (Handoff to Phase E) | Implemented + verified |
| **GET** | `/api/v1/documents/{document_id}/extraction` | Required | Path: `document_id` | `ExtractionResponse` (200) | `401`, `403`, `404` | None (Handoff to Phase E) | Implemented + verified |
| **POST** | `/api/v1/documents/{document_id}/confirm` | Required | Path: `document_id`, Body: `ConfirmationRequest` | `ConfirmationResponse` (200) | `401`, `403`, `404`, `422` | None (Handoff to Phase E) | Implemented + verified |

---

## 10. Market Data

Real-time stock searches, mutual fund nav quotes, exchange rates, and benchmarks.

| Method | Path | Auth | Request Model / Parameters | Response Model | Errors | Frontend Consumer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/market/stocks/search` | None | Query: `q` | `list[StockSearchResult]` (200) | `422` | Investments: Stocks tab | Implemented + verified |
| **GET** | `/api/v1/market/stocks/{symbol}` | None | Path: `symbol`, Query: `exchange` | `StockQuote` (200) | `404`, `422` | Investments: Stock details | Implemented + verified |
| **GET** | `/api/v1/market/mutual-funds/search` | None | Query: `q` | `list[MutualFundSearchResult]` (200) | `422` | Investments: Funds search | Implemented + verified |
| **GET** | `/api/v1/market/mutual-funds/{scheme_id}/nav` | None | Path: `scheme_id` | `MutualFundNAV` (200) | `404`, `422` | Investments: NAV details | Implemented + verified |
| **GET** | `/api/v1/market/fx/{base}/{quote}` | None | Path: `base`, `quote` | `ExchangeRate` (200) | `404`, `422` | Profile: Currency converter | Implemented + verified |
| **GET** | `/api/v1/market/indices/{index_name}` | None | Path: `index_name` | `IndexQuote` (200) | `404`, `422` | Dashboard: Ticker row | Implemented + verified |
| **GET** | `/api/v1/market/interest-rates/{country}/{type_name}` | None | Path: `country`, `type_name` | `InterestRate` (200) | `404`, `422` | Finance: Repayment calculators | Implemented + verified |
| **GET** | `/api/v1/market/portfolio/estimated` | Required | None | dynamic dictionary (Estimated valuation) (200) | `401` | Investments: Portfolio charts | Implemented + verified |

---

## 11. Reports Backlog

The frontend currently references an export/reports endpoint that does not correspond to backend calculations.

* **Frontend Expectation:** `GET /reports/download`
* **Backend Status:** Unimplemented (No `/reports` router configured).
* **Backlog Allocation:** Postponed to **Phase F (Reports & Exports)** as per step 7 guidelines.
