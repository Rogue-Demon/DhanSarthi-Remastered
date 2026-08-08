# DhanSarthi — DATABASE GUIDELINES

> Defines how PostgreSQL stores, organizes, protects, and accesses DhanSarthi
> financial, AI, document, and RAG data.

---

# 1. DATABASE PURPOSE

DhanSarthi uses PostgreSQL as its primary relational database.

PostgreSQL stores:

```text
User Profiles
Financial Data
Transactions
Investments
Loans
Goals
Documents Metadata
AI Conversations
AI Messages
RAG Metadata
Audit Information
````

For vector search, PostgreSQL may use:

```text
pgvector
```

Core principle:

```text
PostgreSQL
    ↓
Structured User Data + Application Data
    +
pgvector
    ↓
Vector Retrieval for RAG
```

---

# 2. DATABASE LAYER

The preferred backend flow is:

```text
FastAPI
   ↓
Service
   ↓
Repository
   ↓
SQLAlchemy / Database Layer
   ↓
PostgreSQL
```

Routes should not directly execute database queries.

---

# 3. CORE ENTITIES

The database should support the following major entities:

```text
User
Profile

Income
Expense
Transaction

Asset
Liability

Investment
Loan

Goal
Budget

Document

Conversation
Message

Knowledge Document
Knowledge Chunk
Embedding Metadata

Audit Log
```

The exact schema may evolve as the application grows.

---

# 4. USER & PROFILE

A user represents an application account.

A profile contains financial/persona information.

Conceptually:

```text
User
 │
 └── Profile
```

Profile may contain:

```text
Persona
Country
Currency
Risk Profile
Financial Preferences
Goals / Preferences
```

Supported personas:

```text
STUDENT
PROFESSIONAL
BUSINESS
```

---

# 5. USER DATA ISOLATION

Every user-owned financial record must be associated with the correct user.

Example:

```text
Transaction
    ↓
user_id
```

The same principle applies to:

```text
Income
Expense
Asset
Liability
Investment
Loan
Goal
Budget
Document
Conversation
Message
```

The backend must verify ownership before reading or modifying any record.

Never rely on the frontend to enforce data isolation.

---

# 6. FINANCIAL DATA

## Income

Possible fields:

```text
id
user_id
source
amount
currency
frequency
date
category
created_at
updated_at
```

Examples:

```text
Salary
Freelance
Business Income
Interest
Rental Income
Other
```

---

## Expense

Possible fields:

```text
id
user_id
category
amount
currency
date
description
created_at
updated_at
```

---

## Transaction

Transactions represent actual financial movements.

Possible fields:

```text
id
user_id
type
amount
currency
category
description
transaction_date
source
created_at
updated_at
```

Transaction type may be:

```text
INCOME
EXPENSE
TRANSFER
```

Do not confuse a financial transaction with an investment holding.

---

# 7. ASSETS

Assets may include:

```text
Cash
Bank Balance
Property
Gold
Investments
Other Assets
```

Possible structure:

```text
Asset
 ├── id
 ├── user_id
 ├── type
 ├── name
 ├── value
 ├── currency
 ├── valuation_date
 └── metadata
```

---

# 8. LIABILITIES

Liabilities may include:

```text
Home Loan
Personal Loan
Education Loan
Credit Card Debt
Other Debt
```

Possible structure:

```text
Liability
 ├── id
 ├── user_id
 ├── type
 ├── name
 ├── outstanding_amount
 ├── currency
 ├── interest_rate
 └── metadata
```

Loans may have their own detailed entity.

---

# 9. INVESTMENTS

Investment records should support multiple investment types.

Examples:

```text
STOCK
MUTUAL_FUND
SIP
FD
RD
BOND
ETF
GOLD
OTHER
```

Possible fields:

```text
id
user_id
type
name
principal
current_value
currency
quantity
purchase_date
maturity_date
interest_rate
metadata
created_at
updated_at
```

Not every investment type will use every field.

Avoid forcing unrelated investment concepts into one confusing schema.

---

# 10. INVESTMENT TRANSACTIONS

For more detailed portfolio tracking, investment transactions may be stored separately.

Example:

```text
Investment
     │
     └── InvestmentTransaction
```

Investment transactions may include:

```text
BUY
SELL
DIVIDEND
INTEREST
CONTRIBUTION
WITHDRAWAL
```

This allows portfolio calculations to be reconstructed from transaction history.

---

# 11. LOANS

Loans require detailed financial information.

Possible fields:

```text
id
user_id
loan_type
lender
principal_amount
outstanding_amount
interest_rate
tenure
remaining_tenure
emi
start_date
end_date
status
currency
created_at
updated_at
```

Loan types may include:

```text
HOME
PERSONAL
EDUCATION
VEHICLE
BUSINESS
OTHER
```

The exact supported types should follow the product requirements.

---

# 12. LOAN PAYMENTS

Where detailed repayment tracking is required:

```text
Loan
  │
  └── LoanPayment
```

Possible fields:

```text
id
loan_id
payment_date
amount
principal_component
interest_component
remaining_balance
```

This allows repayment history and amortization analysis.

---

# 13. GOALS

A financial goal may contain:

```text
id
user_id
name
target_amount
current_amount
target_date
currency
priority
status
created_at
updated_at
```

Examples:

```text
Emergency Fund
Education
Travel
Home
Retirement
Business Expansion
```

---

# 14. BUDGETS

Budgets may be associated with:

```text
User
Category
Period
Amount
```

Example:

```text
Budget
 ├── user_id
 ├── category
 ├── amount
 ├── period
 └── currency
```

Business users may require additional budget structures.

---

# 15. BUSINESS FINANCE

Business financial data must remain distinguishable from personal financial
data.

Business-specific concepts may include:

```text
Revenue
Operating Expense
Receivable
Payable
Business Asset
Business Liability
Business Budget
```

If the product supports organization-level accounts later, the architecture
should allow:

```text
Organization
   │
   └── Members
```

without mixing organization data with personal data.

---

# 16. DOCUMENTS

The database should store document metadata rather than relying on the
database as the primary binary file store.

Possible fields:

```text
id
user_id
filename
document_type
storage_key
mime_type
file_size
status
created_at
processed_at
```

Possible processing states:

```text
UPLOADED
PROCESSING
PROCESSED
FAILED
REVIEW_REQUIRED
```

Private files should live in secure object storage or an equivalent private
storage system.

---

# 17. DOCUMENT EXTRACTION DATA

Extracted information should be traceable back to its source document.

Conceptually:

```text
Document
   ↓
Extraction
   ↓
Validated Financial Data
```

Where appropriate, store:

```text
confidence
source_location
extraction_version
review_status
```

Do not silently overwrite original document information.

---

# 18. AI CONVERSATIONS

AI conversations should be stored separately from financial records.

Conceptually:

```text
Conversation
    │
    └── Messages
```

Conversation:

```text
id
user_id
title
created_at
updated_at
```

Message:

```text
id
conversation_id
role
content
created_at
metadata
```

Roles may include:

```text
USER
ASSISTANT
SYSTEM
TOOL
```

System/internal messages should not be exposed to users unless explicitly
designed for that purpose.

---

# 19. AI MESSAGE METADATA

Where useful, messages may store metadata such as:

```text
model
prompt_version
tool_usage
sources
latency
token_usage
```

Do not store secrets or unnecessary sensitive provider information.

---

# 20. RAG KNOWLEDGE DATA

RAG data should be logically separated from normal user financial records.

Conceptually:

```text
KnowledgeDocument
      │
      └── KnowledgeChunk
              │
              └── Embedding
```

---

# 21. KNOWLEDGE DOCUMENT

Possible fields:

```text
id
title
source
publisher
category
country
financial_year
effective_date
published_date
last_updated
authority_level
version
created_at
```

This metadata supports filtering and source ranking.

---

# 22. KNOWLEDGE CHUNK

Possible fields:

```text
id
document_id
chunk_index
content
metadata
created_at
```

Chunks should preserve their relationship to the original document.

---

# 23. VECTOR EMBEDDINGS

If pgvector is used:

```text
KnowledgeChunk
      ↓
Embedding Vector
      ↓
pgvector
```

The embedding model/version should be identifiable.

Example metadata:

```text
embedding_provider
embedding_model
embedding_version
```

Do not mix incompatible embedding models in the same vector index without a
deliberate strategy.

---

# 24. USER DOCUMENT RAG

User documents may also have embeddings.

However:

```text
User A
   ↓
Private chunks

User B
   ↓
Private chunks
```

must remain isolated.

Every private RAG record must have an ownership boundary such as:

```text
user_id
```

or an equivalent access-control mechanism.

---

# 25. DATABASE RELATIONSHIPS

High-level relationship:

```text
User
 │
 ├── Profile
 ├── Income
 ├── Expense
 ├── Transaction
 ├── Asset
 ├── Liability
 ├── Investment
 │      └── InvestmentTransaction
 ├── Loan
 │      └── LoanPayment
 ├── Goal
 ├── Budget
 ├── Document
 └── Conversation
          └── Message
```

Knowledge system:

```text
KnowledgeDocument
       │
       └── KnowledgeChunk
                │
                └── Embedding
```

---

# 26. FOREIGN KEYS

Use foreign keys to preserve relationships.

Examples:

```text
profile.user_id
transaction.user_id
investment.user_id
loan.user_id
goal.user_id
document.user_id
conversation.user_id
message.conversation_id
knowledge_chunk.document_id
```

Do not rely solely on application code for relational integrity.

---

# 27. DELETE BEHAVIOR

Delete behavior must be deliberate.

For user-owned records, consider appropriate cascading behavior.

Example:

```text
User
 ↓
Conversation
 ↓
Messages
```

Deleting a parent must not accidentally leave orphaned records.

For sensitive financial records, soft deletion may be preferable where auditability
is important.

---

# 28. SOFT DELETE

Where appropriate, use fields such as:

```text
deleted_at
```

instead of permanently deleting records.

This is especially useful where:

```text
Auditability
Recovery
Historical Analysis
```

matter.

Do not use soft deletion everywhere without a reason.

---

# 29. INDEXING

Indexes should be based on actual query patterns.

Likely candidates include:

```text
user_id
created_at
transaction_date
conversation_id
document_id
financial_year
```

Composite indexes may be useful for common queries such as:

```text
user_id + transaction_date
user_id + category
user_id + created_at
```

Do not create excessive indexes.

---

# 30. UNIQUE CONSTRAINTS

Use database constraints for data that must be unique.

Examples may include:

```text
Unique External Identifier
Unique Document Identifier
Other Domain-Specific Identifiers
```

Do not rely only on frontend checks for uniqueness.

---

# 31. CHECK CONSTRAINTS

Where appropriate, use database constraints.

Examples:

```text
amount >= 0
interest_rate >= 0
```

The exact constraints depend on the domain.

Application validation and database constraints should complement each other.

---

# 32. NULLABILITY

Fields should only be nullable when the domain allows missing information.

Avoid making every field nullable simply to simplify development.

Example:

```text
transaction.amount
```

should normally be required.

---

# 33. MONEY TYPES

For monetary values, use PostgreSQL types and application representations that
preserve financial precision.

Avoid storing important monetary values as:

```text
TEXT
```

or relying on imprecise floating-point types.

The exact SQLAlchemy/PostgreSQL representation should be consistent across the
project.

---

# 34. ENUMS

Enums may be used for controlled values such as:

```text
Persona
Transaction Type
Investment Type
Loan Type
Document Status
Message Role
```

Choose between PostgreSQL enums and application-level validation based on
migration and flexibility requirements.

Do not create enums for values that change frequently.

---

# 35. TIMESTAMPS

Use a consistent timestamp strategy.

Important fields include:

```text
created_at
updated_at
deleted_at
processed_at
```

The application must have a clear timezone policy.

---

# 36. MIGRATIONS

All schema changes must use database migrations.

Preferred workflow:

```text
Model Change
    ↓
Migration
    ↓
Review
    ↓
Apply
    ↓
Test
```

Do not manually modify production tables as the normal development process.

---

# 37. MIGRATION RULES

Before applying a migration:

```text
Check Existing Schema
Check Data Impact
Check Constraints
Check Indexes
Check Rollback Strategy
```

Destructive migrations require additional review.

Examples:

```text
Dropping a Column
Dropping a Table
Changing Data Types
Deleting Data
```

---

# 38. DATABASE TRANSACTIONS

Use database transactions for operations that must succeed or fail together.

Example:

```text
Create Investment
    +
Create Investment Transaction
```

should not leave the database partially updated.

---

# 39. CONCURRENCY

Important financial updates should consider concurrent requests.

Potential examples:

```text
Updating Loan
Updating Investment
Updating Financial Goal
Processing Document
```

Use appropriate transaction isolation or locking only when actually required.

---

# 40. QUERY RULES

Database queries should:

* Select only required data.
* Use indexes where appropriate.
* Avoid N+1 queries.
* Use pagination for large collections.
* Avoid unnecessary joins.
* Use transactions where needed.

---

# 41. USER DATA SECURITY

Sensitive financial data must never be exposed through:

```text
Public APIs
Public Storage
Logs
Error Messages
Debug Output
```

Database credentials must never be committed to Git.

---

# 42. DATABASE BACKUPS

Production PostgreSQL must have a backup strategy.

Backups should consider:

```text
Frequency
Retention
Encryption
Recovery
Testing
```

A backup is not considered reliable until restoration has been tested.

---

# 43. DEVELOPMENT DATABASE

Local development should use a reproducible PostgreSQL environment.

Preferred:

```text
Docker PostgreSQL
```

If pgvector is required locally:

```text
PostgreSQL
+
pgvector
```

should be available through the development setup.

---

# 44. SEED DATA

Development seed data may be used for:

```text
Student
Professional
Business
```

personas.

Seed data must be clearly marked as synthetic/demo data.

Never use real user financial information as seed data.

---

# 45. DATABASE + AI

The AI must never have unrestricted database access.

Preferred:

```text
AI
 ↓
Controlled Tool
 ↓
Service
 ↓
Repository
 ↓
PostgreSQL
```

Not:

```text
AI
 ↓
Raw SQL
 ↓
PostgreSQL
```

---

# 46. DATABASE + RAG

RAG retrieval should also use controlled application services.

Preferred:

```text
AI
 ↓
RAG Service
 ↓
Retriever
 ↓
pgvector
```

The AI must not directly construct arbitrary vector/database queries.

---

# 47. AUDIT LOGS

Important operations may be recorded in an audit log.

Examples:

```text
Document Uploaded
Financial Record Updated
Document Deleted
Important AI Tool Called
Security Event
```

Audit logs should avoid storing unnecessary sensitive content.

---

# 48. DATABASE TESTING

Database tests should verify:

```text
Relationships
Constraints
User Isolation
Migrations
Queries
Indexes where important
Transaction Behavior
```

Especially test:

```text
User A cannot access User B's data.
```

---

# 49. PERFORMANCE

Optimize only after identifying actual bottlenecks.

Potential improvements:

```text
Indexes
Query Optimization
Pagination
Connection Pooling
Caching
Materialized Views
```

Do not introduce distributed database infrastructure prematurely.

---

# 50. ANTIGRAVITY DATABASE RULES

When modifying PostgreSQL:

1. Read this document first.

2. Inspect the existing schema.

3. Reuse existing entities where appropriate.

4. Never create duplicate financial entities without a reason.

5. Add migrations for schema changes.

6. Use foreign keys for relationships.

7. Enforce user ownership.

8. Use appropriate monetary precision.

9. Add indexes based on real query patterns.

10. Avoid unnecessary nullable fields.

11. Test migrations.

12. Test user-data isolation.

13. Never expose database credentials.

14. Never give the AI unrestricted database access.

15. Keep RAG/vector data properly isolated.

16. Do not delete production data through development scripts.

17. Update documentation when significant schema changes occur.

---

# FINAL DATABASE FLOW

```text
                         PostgreSQL
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
   User Financial Data     AI Data          RAG Data
          │                  │                  │
    ┌─────┼─────┐       ┌────┴────┐       ┌────┴─────┐
    ▼     ▼     ▼       ▼         ▼       ▼          ▼
 Finance Loans Investments Conversations Messages Knowledge
                                               │
                                               ▼
                                           pgvector
```

The database remains the structured source of truth for application data.

The Financial Engine calculates.

RAG retrieves knowledge.

The AI interprets and communicates.

# END OF DATABASE_GUIDELINES.md

````

