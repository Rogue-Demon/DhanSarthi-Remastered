# DhanSarthi — KNOWLEDGE STRUCTURE

> Defines how DhanSarthi stores, organizes, retrieves, validates, and uses
> knowledge for the AI Advisor and RAG system.

---

# 1. PURPOSE

The Knowledge System provides reliable information to the AI Advisor.

It should help the AI answer questions involving:

- Financial concepts
- Loans
- Investments
- SIP
- Mutual Funds
- FD / RD
- Taxation
- Personal finance
- Financial planning
- User-provided financial documents
- Other approved financial knowledge

Core principle:

```text
Knowledge Base = Provides information
Financial Engine = Performs calculations
PostgreSQL = Stores structured user data
AI Advisor = Explains and personalizes
````

---

# 2. KNOWLEDGE SOURCES

Knowledge should be divided into two major categories.

## 2.1 General Knowledge

Examples:

```text
Government / Regulatory Information
Official Financial Institutions
Official Product Documentation
Trusted Financial Resources
Approved Educational Material
```

Prefer authoritative sources over generic web content.

---

## 2.2 User-Specific Knowledge

Examples:

```text
Bank Statements
Salary Slips
Investment Statements
Loan Documents
Tax Documents
Uploaded CSV / Excel Files
Other User-Provided Documents
```

User-specific knowledge must always remain isolated to the authorized user.

---

# 3. SOURCE AUTHORITY

Every knowledge source should have metadata such as:

```text
source
title
publisher
category
country
financial_year
effective_date
last_updated
authority_level
```

Example authority levels:

```text
HIGH
MEDIUM
LOW
```

Prefer:

```text
Official / Regulatory
      ↓
Trusted Financial Source
      ↓
Approved Educational Source
      ↓
General Source
```

Do not treat every retrieved document as equally trustworthy.

---

# 4. KNOWLEDGE CATEGORIES

The knowledge base may contain:

```text
Personal Finance
Investments
Stocks
Mutual Funds
SIP
FD
RD
Loans
Tax
Insurance
Retirement
Budgeting
Financial Planning
Business Finance
```

The exact categories may expand as the product grows.

---

# 5. DOCUMENT INGESTION

The RAG ingestion pipeline should be:

```text
Source
 ↓
Document Collection
 ↓
File / Content Validation
 ↓
Text Extraction
 ↓
Cleaning
 ↓
Metadata Assignment
 ↓
Chunking
 ↓
Embedding
 ↓
Vector Storage
```

For user-uploaded documents:

```text
Upload
 ↓
Secure Storage
 ↓
Extraction
 ↓
Validation
 ↓
Metadata
 ↓
Embedding
 ↓
Private Knowledge Store
```

---

# 6. CHUNKING

Documents should be divided into meaningful chunks before embedding.

A chunk should preserve enough context to remain understandable.

Avoid:

```text
Very Large Chunks
```

because retrieval becomes less precise.

Avoid:

```text
Extremely Small Chunks
```

because important context may be lost.

Chunking should preferably respect:

```text
Sections
Paragraphs
Headings
Tables
Logical Financial Topics
```

The exact chunk size may be tuned experimentally.

---

# 7. EMBEDDINGS

Each searchable knowledge chunk should have an embedding.

Conceptually:

```text
Text Chunk
    ↓
Embedding Model
    ↓
Vector
    ↓
PostgreSQL + pgvector
```

The embedding model should be configurable.

Do not hardcode the embedding provider throughout the application.

---

# 8. METADATA FILTERING

Retrieval should use metadata where appropriate.

Possible filters:

```text
Country
Financial Year
Topic
Document Type
Authority
Effective Date
User ID
```

Example:

```text
Tax Question
     ↓
Filter relevant financial year
     ↓
Retrieve relevant tax knowledge
```

For user documents:

```text
user_id = current_user_id
```

must be enforced.

---

# 9. RETRIEVAL

The preferred RAG flow is:

```text
User Question
      ↓
Query Understanding
      ↓
Metadata Filtering
      ↓
Vector Search
      ↓
Relevance Ranking
      ↓
Top Relevant Chunks
      ↓
AI Context
```

Retrieval should prioritize relevance rather than simply returning the nearest
documents.

---

# 10. HYBRID RETRIEVAL

Where useful, DhanSarthi may combine:

```text
Semantic / Vector Search
+
Keyword Search
+
Metadata Filtering
```

This is particularly useful for:

```text
Tax Sections
Financial Product Names
Legal / Regulatory Terms
Specific Document Identifiers
```

The exact implementation may evolve.

---

# 11. RANKING

Retrieved information should be ranked using factors such as:

```text
Semantic Relevance
Source Authority
Freshness
Financial Year
User Relevance
Document Type
```

Conceptually:

```text
Retrieved Results
      ↓
Relevance
      +
Authority
      +
Freshness
      ↓
Final Context
```

---

# 12. FRESHNESS

Financial knowledge can become outdated.

Knowledge should therefore track:

```text
Published Date
Effective Date
Last Updated
Financial Year
Expiry / Review Date where applicable
```

When current information is required, outdated knowledge should not be treated
as current.

---

# 13. USER DOCUMENTS

User documents must be logically separated from general knowledge.

Example:

```text
General Knowledge
      │
      └── Shared Knowledge Base

User A
      │
      └── Private Knowledge

User B
      │
      └── Private Knowledge
```

User A must never retrieve User B's documents.

---

# 14. DOCUMENT TYPES

The system may support:

```text
PDF
CSV
Excel
Text
Images / OCR
```

Only implement formats actually required by the current product.

---

# 15. DOCUMENT TRUST

Uploaded documents should not automatically be considered correct.

The system should distinguish:

```text
Source Document
Extracted Data
Validated Data
```

Example:

```text
Bank Statement
      ↓
Extracted Transactions
      ↓
Validation
      ↓
Structured Financial Data
```

---

# 16. RAG + FINANCIAL ENGINE

RAG should provide knowledge.

The Financial Engine should perform calculations.

Example:

```text
User:
"Can I afford this loan?"

RAG:
Provides relevant loan concepts/rules.

Financial Engine:
Calculates EMI, debt ratio and cash-flow impact.

AI:
Combines both and explains the result.
```

Do not use RAG as a replacement for deterministic financial calculations.

---

# 17. RAG + AI RESPONSE

The AI should use retrieved knowledge as supporting context.

Flow:

```text
Question
 ↓
Retrieve Relevant Knowledge
 ↓
Validate Context
 ↓
AI Reasoning
 ↓
Grounded Response
```

The AI should not claim that a retrieved source says something if the source
does not actually support the statement.

---

# 18. CITATIONS / SOURCES

When appropriate, responses should identify the source used.

For example:

```text
Source:
<document / authority>

Relevant information:
<short explanation>
```

The exact UI representation will be defined by the frontend implementation.

---

# 19. KNOWLEDGE SECURITY

The knowledge system must prevent:

```text
Cross-User Retrieval
Unauthorized Document Access
Sensitive Data Leakage
Prompt Injection Through Documents
Untrusted Content Being Treated as Instructions
```

Documents are data.

They must not override system or developer instructions.

---

# 20. KNOWLEDGE UPDATE PROCESS

When knowledge changes:

```text
New Source
 ↓
Validate
 ↓
Version
 ↓
Ingest
 ↓
Embed
 ↓
Index
 ↓
Mark Older Version
```

For regulated or time-sensitive information, the system should retain enough
metadata to determine which version was used.

---

# 21. RAG EVALUATION

RAG quality should be tested for:

```text
Retrieval Accuracy
Relevance
Source Authority
Freshness
User Isolation
Context Quality
Hallucination Reduction
```

Important queries should have expected relevant sources.

---

# 22. ANTIGRAVITY RULES

When implementing the knowledge system:

1. Keep general knowledge separate from user-specific documents.

2. Always enforce user-level access for private documents.

3. Store useful metadata with every knowledge source.

4. Prefer authoritative sources.

5. Track financial year and effective dates where applicable.

6. Do not treat outdated information as current.

7. Do not embed raw sensitive data unnecessarily.

8. Use pgvector through a controlled RAG service.

9. Keep embedding providers configurable.

10. Keep retrieval logic separate from AI response generation.

11. Treat documents as untrusted data.

12. Never allow document content to override system instructions.

13. Do not use RAG for calculations that belong to the Financial Engine.

14. Test retrieval quality before declaring RAG complete.

---

# FINAL KNOWLEDGE FLOW

```text
                  KNOWLEDGE SOURCES
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
      General Knowledge        User Documents
             │                       │
             ▼                       ▼
        Validation               Validation
             │                       │
             └───────────┬───────────┘
                         ▼
                    Processing
                         │
                         ▼
                      Chunking
                         │
                         ▼
                     Embedding
                         │
                         ▼
                  PostgreSQL + pgvector
                         │
                         ▼
                    Retrieval
                         │
                         ▼
                     Ranking
                         │
                         ▼
                  Relevant Context
                         │
                         ▼
                    AI Advisor
                         │
                         ▼
                     Response
```

# END OF KNOWLEDGE_STRUCTURE.md

