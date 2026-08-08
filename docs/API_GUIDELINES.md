# DhanSarthi — API GUIDELINES

> Defines the communication contract between the DhanSarthi React frontend
> and FastAPI backend.

---

# 1. PURPOSE

The API layer connects:

```text
React Frontend
      ↓
FastAPI
      ↓
Services
      ↓
Financial Engine / AI / RAG / Database
````

The API must provide predictable, validated, secure, and documented
communication between the frontend and backend.

---

# 2. GENERAL RULES

All APIs must:

* Validate incoming data.
* Return predictable response structures.
* Use appropriate HTTP status codes.
* Return useful errors.
* Enforce user authorization.
* Never expose sensitive internal information.
* Keep business logic out of route handlers.
* Use service-layer functions for application logic.

Preferred structure:

```text
Request
  ↓
FastAPI Router
  ↓
Pydantic Validation
  ↓
Service
  ↓
Domain / Repository / AI / RAG
  ↓
Response Schema
  ↓
Frontend
```

---

# 3. API VERSIONING

Use a versioned API prefix.

Recommended:

```text
/api/v1/
```

Examples:

```text
/api/v1/profile
/api/v1/finance
/api/v1/transactions
/api/v1/investments
/api/v1/loans
/api/v1/goals
/api/v1/documents
/api/v1/conversations
/api/v1/ai
```

Avoid breaking existing endpoints without a deliberate migration plan.

---

# 4. ENDPOINT NAMING

Use resource-oriented names.

Preferred:

```text
GET    /api/v1/transactions
POST   /api/v1/transactions
GET    /api/v1/transactions/{id}
PATCH  /api/v1/transactions/{id}
DELETE /api/v1/transactions/{id}
```

Avoid unnecessary action-style endpoints such as:

```text
/getTransactions
/createTransaction
/deleteTransaction
```

Actions may be appropriate when an operation is genuinely an action.

Example:

```text
POST /api/v1/loans/{id}/calculate
```

---

# 5. HTTP METHODS

Use HTTP methods consistently.

```text
GET
    Retrieve data

POST
    Create resource / execute controlled operation

PATCH
    Partially update resource

PUT
    Replace resource where appropriate

DELETE
    Delete resource
```

Do not use `POST` for every operation simply because it is convenient.

---

# 6. REQUEST VALIDATION

FastAPI/Pydantic schemas must validate API inputs.

Example:

```json
{
  "amount": 25000,
  "category": "food",
  "date": "2026-08-08"
}
```

Validate:

```text
Required fields
Data types
Ranges
Dates
Enums
Currency
Ownership
Business rules
```

Never rely only on React validation.

---

# 7. RESPONSE STRUCTURE

Responses should be predictable.

Example:

```json
{
  "data": {
    "id": "123",
    "amount": 25000
  }
}
```

For collections:

```json
{
  "data": [
    {
      "id": "123"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

The exact response structure may evolve, but consistency must be maintained.

---

# 8. ERROR FORMAT

Use a consistent error structure.

Example:

```json
{
  "error": {
    "code": "INVALID_TRANSACTION",
    "message": "The transaction amount is invalid."
  }
}
```

Errors may additionally contain safe validation details.

Never expose:

```text
Stack traces
Database errors
SQL queries
Internal file paths
API keys
System prompts
Provider credentials
```

---

# 9. HTTP STATUS CODES

Use appropriate status codes.

```text
200
Successful request

201
Resource created

204
Successful request with no response body

400
Invalid request

401
Authentication required

403
Access denied

404
Resource not found

409
Conflict

422
Validation failure

429
Rate limit exceeded

500
Unexpected server error

502/503
External service unavailable
```

---

# 10. USER DATA OWNERSHIP

Every user-specific endpoint must enforce ownership.

Example:

```text
GET /api/v1/transactions/{transaction_id}
```

The backend must verify:

```text
transaction.user_id == current_user.id
```

Never rely on the frontend to enforce ownership.

The same rule applies to:

```text
Transactions
Income
Expenses
Assets
Liabilities
Investments
Loans
Goals
Documents
Conversations
Messages
Financial Profiles
```

---

# 11. PROFILE API

Possible endpoints:

```text
GET   /api/v1/profile
PATCH /api/v1/profile
```

Profile may contain:

```text
Persona
Name
Country
Currency
Financial Preferences
Risk Profile
Goals
Other Relevant Preferences
```

Do not return unnecessary sensitive information.

---

# 12. FINANCE API

Possible endpoints:

```text
GET /api/v1/finance/summary

GET /api/v1/finance/income

GET /api/v1/finance/expenses

GET /api/v1/finance/assets

GET /api/v1/finance/liabilities

GET /api/v1/finance/net-worth

GET /api/v1/finance/cash-flow
```

The backend should calculate financial summaries using the Financial Engine
where appropriate.

---

# 13. TRANSACTION API

Possible endpoints:

```text
GET    /api/v1/transactions
POST   /api/v1/transactions
GET    /api/v1/transactions/{id}
PATCH  /api/v1/transactions/{id}
DELETE /api/v1/transactions/{id}
```

Supported filtering may include:

```text
Date Range
Category
Type
Amount Range
Account
Search
```

Large datasets must use pagination.

---

# 14. INVESTMENT API

Possible endpoints:

```text
GET    /api/v1/investments
POST   /api/v1/investments
GET    /api/v1/investments/{id}
PATCH  /api/v1/investments/{id}
DELETE /api/v1/investments/{id}

GET /api/v1/investments/summary
GET /api/v1/investments/portfolio
```

Investment types may include:

```text
Stocks
Mutual Funds
SIP
FD
RD
Bonds
ETFs
Other
```

---

# 15. LOAN API

Possible endpoints:

```text
GET    /api/v1/loans
POST   /api/v1/loans
GET    /api/v1/loans/{id}
PATCH  /api/v1/loans/{id}
DELETE /api/v1/loans/{id}

POST /api/v1/loans/calculate-emi
POST /api/v1/loans/analyze-affordability
```

Loan calculations must use the Financial Engine.

---

# 16. GOAL API

Possible endpoints:

```text
GET    /api/v1/goals
POST   /api/v1/goals
GET    /api/v1/goals/{id}
PATCH  /api/v1/goals/{id}
DELETE /api/v1/goals/{id}

POST /api/v1/goals/{id}/projection
```

---

# 17. TAX API

Possible endpoints:

```text
GET /api/v1/taxes/summary

POST /api/v1/taxes/calculate

GET /api/v1/taxes/deductions

GET /api/v1/taxes/suggestions
```

Tax calculations must use the applicable financial-year rules.

Do not hardcode tax calculations inside the route.

---

# 18. DOCUMENT API

Possible endpoints:

```text
GET    /api/v1/documents
POST   /api/v1/documents
GET    /api/v1/documents/{id}
DELETE /api/v1/documents/{id}

GET /api/v1/documents/{id}/status
GET /api/v1/documents/{id}/analysis
```

Upload flow:

```text
Frontend
   ↓
Upload
   ↓
FastAPI
   ↓
Validation
   ↓
Secure Storage
   ↓
Processing
   ↓
Extraction
   ↓
Validation
   ↓
Financial Mapping
   ↓
RAG / Analysis
```

Do not expose private storage locations directly.

---

# 19. AI ADVISOR API

The AI Advisor is the primary Smart Tool.

Possible endpoint:

```text
POST /api/v1/ai/chat
```

Request:

```json
{
  "conversation_id": "optional-id",
  "message": "Can I afford this loan?"
}
```

The backend determines the required:

```text
User Context
Financial Data
Financial Tools
RAG Context
AI Provider
```

The frontend should not construct the AI's financial context manually.

---

# 20. AI STREAMING

If streaming is implemented:

```text
POST /api/v1/ai/chat/stream
```

The stream should communicate:

```text
Start
Message Chunks
Sources / Metadata where applicable
Completion
Error
```

The frontend must handle:

```text
Loading
Partial Response
Completion
Connection Failure
Retry
Cancellation
```

Never treat an interrupted stream as a complete answer.

---

# 21. CONVERSATION API

Possible endpoints:

```text
GET    /api/v1/conversations
POST   /api/v1/conversations
GET    /api/v1/conversations/{id}
DELETE /api/v1/conversations/{id}

GET /api/v1/conversations/{id}/messages
```

Conversation ownership must always be verified.

---

# 22. FILE UPLOAD API

File uploads must validate:

```text
File Type
File Size
Filename
Content
User Ownership
```

Never trust the filename or MIME type alone.

Uploaded files should be stored privately.

---

# 23. PAGINATION

Collection endpoints should support pagination.

Recommended:

```text
?page=1&page_size=20
```

Possible metadata:

```json
{
  "page": 1,
  "page_size": 20,
  "total": 250,
  "total_pages": 13
}
```

Do not return thousands of financial records in a single request.

---

# 24. FILTERING & SORTING

Where appropriate:

```text
?date_from=2026-01-01
&date_to=2026-08-08
&category=food
&sort=-date
&page=1
&page_size=20
```

Backend must validate filter values.

---

# 25. API PERFORMANCE

Avoid unnecessary database queries.

Use:

```text
Pagination
Filtering
Indexes
Selective Fields
Efficient Queries
Caching where justified
```

Do not introduce caching before identifying an actual performance requirement.

---

# 26. API SECURITY

The backend must:

* Validate authorization.
* Validate ownership.
* Rate-limit sensitive endpoints where necessary.
* Protect file uploads.
* Avoid exposing internal errors.
* Validate all external input.
* Never trust frontend-provided user IDs.

For user-specific operations:

```text
current authenticated user
        ↓
authorized resource
```

must be verified server-side.

---

# 27. AI API SECURITY

AI endpoints require additional controls.

The backend must:

```text
Validate User
      ↓
Load Authorized Financial Context
      ↓
Execute Allowed Tools
      ↓
Retrieve Authorized RAG Data
      ↓
Generate Response
```

The frontend must never send arbitrary:

```text
SQL
Tool Calls
System Prompts
Database Queries
```

to the AI API.

---

# 28. API IDEMPOTENCY

For operations that may be retried, consider idempotency.

This is especially important for future operations that could create financial
records.

Avoid accidental duplicate:

```text
Transactions
Investments
Documents
Other Financial Records
```

when requests are retried.

---

# 29. API TIMEOUTS

External operations should have reasonable timeouts.

Examples:

```text
AI Provider
Embedding Provider
Market Data Provider
Storage
```

Do not allow one external service to block the entire API indefinitely.

---

# 30. EXTERNAL SERVICE ERRORS

If an external service fails:

```text
External Provider
      ↓
Service Layer
      ↓
Controlled Application Error
      ↓
API Response
```

Do not expose raw provider errors directly to users.

---

# 31. HEALTH ENDPOINTS

Provide basic health checks.

Example:

```text
GET /health
```

Optional readiness check:

```text
GET /health/ready
```

Health endpoints should not expose secrets or internal configuration.

---

# 32. API DOCUMENTATION

FastAPI's generated OpenAPI documentation should remain accurate.

When adding or modifying an endpoint:

```text
Request Schema
Response Schema
Description
Status Codes
Error Responses
```

should remain understandable.

---

# 33. FRONTEND API CLIENT

React should communicate through a centralized API client.

Preferred:

```text
React Feature
     ↓
Feature API / Hook
     ↓
Central API Client
     ↓
FastAPI
```

Avoid scattering raw API calls throughout React components.

---

# 34. API TYPES

Frontend TypeScript types should match backend response schemas.

Where practical, consider generating or sharing API types from the OpenAPI
contract instead of manually maintaining duplicate definitions.

---

# 35. API VERSION COMPATIBILITY

When changing an API:

```text
Identify Consumers
      ↓
Update Backend
      ↓
Update Frontend
      ↓
Update Tests
      ↓
Update Documentation
```

Do not silently break the existing frontend.

---

# 36. API TESTING

Every important endpoint should have tests covering:

```text
Success
Validation Failure
Unauthorized Access
Forbidden Access
Not Found
Invalid Input
Database Failure
External Service Failure where relevant
```

Financial endpoints should additionally test numerical correctness.

---

# 37. ANTIGRAVITY API RULES

When implementing APIs:

1. Read `ARCHITECTURE.md`.

2. Read `DATABASE_GUIDELINES.md` when database changes are involved.

3. Keep routers thin.

4. Use Pydantic schemas for request/response validation.

5. Put business logic in services.

6. Put financial calculations in the Financial Engine.

7. Enforce user ownership server-side.

8. Never trust a frontend-provided `user_id`.

9. Use appropriate HTTP methods and status codes.

10. Use consistent error responses.

11. Add pagination to large collections.

12. Never expose database errors or secrets.

13. Keep AI context construction on the backend.

14. Never allow arbitrary AI database access.

15. Update API documentation when contracts change.

16. Add tests for new endpoints.

17. Do not introduce breaking changes without a deliberate migration.

---

# FINAL API FLOW

```text
                     REACT FRONTEND
                           │
                           ▼
                     API CLIENT
                           │
                           ▼
                    FastAPI Router
                           │
                           ▼
                  Request Validation
                           │
                           ▼
                       Service
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        PostgreSQL    Financial Engine  AI/RAG
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                    Response Schema
                           │
                           ▼
                      FastAPI API
                           │
                           ▼
                     API Client
                           │
                           ▼
                    React Frontend
```

# END OF API_GUIDELINES.md

````