# DhanSarthi Phase L.0 — AI Advisor Architecture Audit

## 1. Executive Summary

This architecture audit documents the complete end-to-end design, data flow, component interfaces, latency characteristics, and security boundaries of the DhanSarthi AI Advisor system as of Phase K. The objective is to establish a rigorous, empirical baseline prior to implementing Phase L enhancements.

DhanSarthi's AI Advisor architecture currently combines a deterministic **Financial Engine** (the sole authority for personal financial metrics), an authoritative **PostgreSQL pgvector RAG Retriever** (for regulatory and statutory financial knowledge), a multi-intent **IntentRouter**, and a **Hugging Face LLM Provider** (`meta-llama/Llama-3.1-8B-Instruct`).

### Critical Architectural Policy
> [!IMPORTANT]
> Phase L will **not** replace the existing RAG system, PostgreSQL database, pgvector extension, `PostgresRAGRetriever`, Financial Engine, or HuggingFaceProvider. All new components—including local MiniLM embeddings, FAISS fast candidate retrieval, spelling/typo correction, Hinglish parsing, and conversation-aware query rewriting—will **complement** and extend the existing foundation.

---

## 2. Current AI Architecture

The DhanSarthi AI Advisor architecture follows a strictly layered, decoupled design pattern:

```mermaid
flowchart TD
    UI[React AI Advisor Workspace] -->|POST /ai/conversations/{id}/messages| API[FastAPI AI Endpoint]
    API -->|JWT Authentication & Rate Limit| DEPS[FastAPI Dependency Injector]
    DEPS -->|Instantiate| SRV[AIAdvisorService]
    
    SRV -->|1. Store User Msg| CS[ConversationService]
    SRV -->|2. Classify Intent| IR[IntentRouter]
    
    subgraph Execution Branching
        IR -->|CASUAL| CAS[Quick Casual Response]
        IR -->|PERSONAL_FINANCE / MIXED| FE[Financial Engine / DashboardService]
        IR -->|GENERAL_FINANCE / MIXED| RAG[PostgresRAGRetriever]
    end
    
    FE -->|Deterministic Facts & Signals| FIS[FinancialIntelligenceService]
    RAG -->|Normalize & Expand| QP[QueryProcessor]
    QP -->|Embed Query| HF_EMB[EmbeddingProvider / HuggingFaceProvider]
    HF_EMB -->|384d Vector| KCR[KnowledgeChunkRepository / pgvector]
    KCR -->|Candidate Pool| DRR[DeterministicReranker]
    DRR -->|Top Ranked Chunks| SRV
    
    FIS -->|Health & Signals| CB[AIContextBuilder]
    SRV -->|3. Assemble Prompt| CB
    CB -->|Structured Prompt| HFP[HuggingFaceProvider LLM]
    HFP -->|LLM Response| SV[SimpleSafetyValidator]
    SV -->|4. Store Assistant Msg| CS
    CS -->|5. Return Response| UI
```

---

## 3. Current Request Flow

Tracing a user message through `POST /api/v1/ai/conversations/{conversation_id}/messages`:

1. **Frontend Request**: The React client sends `SendMessageRequest` (`{ message: "What is SIP?" }`) with a JWT Bearer token in the `Authorization` header.
2. **FastAPI Route & Security**: `backend/app/api/v1/ai.py` handles the request.
   - `get_current_user_id` decodes the JWT token and verifies active user status.
   - `AIRateLimiter` enforces the 30 requests / 60 seconds rate limit per user.
3. **Service Orchestration (`AIAdvisorService.send_chat_message`)**:
   - Step 1: Verifies conversation ownership (`ConversationService.get_conversation`).
   - Step 2: Commits the user message to PostgreSQL (`ConversationService.store_user_message`).
   - Step 3: Classifies query intent using `IntentRouter.classify` and sub-intent via `IntentRouter.classify_sub_intent`.
   - Step 4: Retrieves user financial facts (`DashboardService.build_dashboard`) and financial intelligence (`FinancialIntelligenceService.build_summary`).
   - Step 5: If intent is `GENERAL_FINANCE` or `MIXED`, executes `PostgresRAGRetriever.retrieve`.
   - Step 6: Fetches recent conversation history (excluding the current user message).
   - Step 7: Assembles `AIContext` and structured prompt string using `AIContextBuilder`.
   - Step 8: Calls `HuggingFaceProvider.generate` with `asyncio.wait_for` (60s timeout).
   - Step 9: Passes response through `SimpleSafetyValidator.validate_response`.
   - Step 10: Commits assistant response with metadata (citations, timing, signals) via `ConversationService.store_assistant_message`.
   - Step 11: Returns `SendMessageResponse` to frontend.

---

## 4. Embedding Architecture Audit

### Technical Inspection Findings

| Audit Dimension | Current Implementation |
| :--- | :--- |
| **Provider Class** | `HuggingFaceProvider` (implementing `EmbeddingProvider` interface) |
| **Default Model** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Config Setting** | `settings.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"` |
| **Vector Dimension** | **384 dimensions** (`settings.embedding_dimension = 384`) |
| **Generation Endpoint** | `https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2` |
| **Fallback Mechanism** | Deterministic 384-dimensional fallback vector if remote HF endpoint is unavailable |
| **Database Schema** | `KnowledgeChunk.embedding = mapped_column(VectorType(dim=384), nullable=True)` |
| **SQL Type** | Native pgvector `Vector(384)` on PostgreSQL; JSON list fallback on SQLite |
| **Similarity Metric** | Native pgvector L2 Distance (`l2_distance`) on PostgreSQL; Cosine Similarity in Python on SQLite |

### Audit Questions & Direct Answers

* **A. What embedding model is currently used?**
  `sentence-transformers/all-MiniLM-L6-v2` via Hugging Face Inference API.
* **B. Is it already MiniLM?**
  **Yes.** The model string and dimension in configuration are already set to MiniLM.
* **C. If not, what model is used?**
  N/A (already MiniLM).
* **D. Is it compatible with all-MiniLM-L6-v2?**
  Yes, it is the exact same 384-dimensional model.
* **E. Would changing the model require re-embedding all knowledge chunks?**
  If the model or vector dimension were changed, re-embedding would be mandatory. However, since the database already stores 384-dimensional MiniLM vectors, no re-embedding is required.
* **F. How many knowledge chunks currently exist?**
  **78 total knowledge chunks** (75 active chunks, 3 archived chunks).
* **G. How many embeddings exist?**
  **78 embeddings** stored in PostgreSQL `knowledge_chunks.embedding`.
* **H. Are historical/archived documents embedded?**
  **Yes.** 3 archived documents and their 3 corresponding chunks retain their 384-dim embeddings in the database. Filter `KnowledgeDocument.status == ACTIVE` excludes archived documents from standard searches, but `is_historical` flag enables targeted access.
* **I. How is embedding versioning handled?**
  Version control is managed at the `KnowledgeDocument` level via the `version` field (e.g. `"1.0"`), `document_hash` (SHA-256 content checksum), and `status` enum (`ACTIVE`, `ARCHIVED`).

---

## 5. Current RAG Retrieval Audit

### Retrieval Pipeline Breakdown

```
User Query
  │
  ▼
1. QueryProcessor.process()
   ├── Normalize text (strip punctuation, lowercase, strip Hinglish suffixes)
   ├── Term expansion (map query tokens against 26 financial terms in query_terms.json)
   └── Historical intent detection (FY/AY patterns, historical keywords)
  │
  ▼
2. Vector Embedding Generation
   └── EmbeddingProvider.embed(normalized_query) -> 384d Float Vector
  │
  ▼
3. Candidate Pool Retrieval (KnowledgeChunkRepository.search_similarity)
   └── Native pgvector L2 distance search (Limit = top_k * 5 = 25 chunks, threshold = 0.15)
  │
  ▼
4. DeterministicReranker.rerank_and_filter()
   ├── Multi-Factor Scoring:
   │     sem_score (0.30) + title_score (0.20) + kw_score (0.10) +
   │     topic_score (0.15) + auth_score (0.15) + temp_score (0.05) + qual_score (0.05)
   ├── RAG Abstention Check (Top score < threshold=0.30 -> return [])
   ├── Deduplication (Filter near-duplicate 150-char normalized snippets)
   └── Context Diversity (Max 2 chunks per document)
  │
  ▼
5. Output: Top-K Ranked RetrievedDocument List (Max top_k = 4 or 5)
```

---

## 6. Query Understanding Audit

### Current Capabilities vs Gaps

| Capability | Current Status | Test Example | Result |
| :--- | :--- | :--- | :--- |
| **Spelling / Typo Correction** | ❌ **NOT SUPPORTED** | `"what is mutal fund"` | Fails to match `"mutual fund"`; vector similarity degraded. |
| **Hinglish Suffix Trimming** | ⚠️ **PARTIAL (Regex)** | `"SIP kya hai"` | Trims `"kya hai"` -> `"sip"`, expands via dictionary. Works for fixed patterns. |
| **Hinglish Grammatical Parsing** | ❌ **NOT SUPPORTED** | `"fd safe hai kya"`, `"mera savings rate kaisa hai"` | No transliteration or grammar parsing; relies solely on keyword extraction. |
| **Financial Abbreviation Recognition** | ⚠️ **PARTIAL (Dictionary)** | `"what is sip"`, `"what is ppf"` | Maps 26 predefined terms in `query_terms.json`. Unlisted acronyms fail. |
| **Conversation-Aware Follow-ups** | ❌ **NOT SUPPORTED in Retrieval** | `"what is it"` (after SIP question) | History is passed to LLM prompt, but `QueryProcessor` does NOT rewrite the query for RAG retrieval. Vector search for `"what is it"` fails. |

---

## 7. Intent & Sub-Intent System Audit

### Current Intent Classification Matrix

| Primary Intent | Sub-Intents | Purpose | RAG Triggered? | DB Facts Triggered? |
| :--- | :--- | :--- | :--- | :--- |
| `CASUAL` | `GENERAL` | Greetings, bot capabilities, thanks | ❌ No | ❌ No |
| `GENERAL_FINANCE` | `INVESTMENT_ANALYSIS`, `GENERAL` | Conceptual, educational, regulatory questions | ✅ Yes | ❌ No |
| `PERSONAL_FINANCE` | `SPENDING_ANALYSIS`, `NET_WORTH_ANALYSIS`, etc. | Pure user metric queries (*"How much did I spend?"*) | ❌ No | ✅ Yes |
| `MIXED` | `PERSONAL_HEALTH`, `DEBT_ANALYSIS`, `FINANCIAL_PLANNING` | Personal metric + advice/guidance | ✅ Yes | ✅ Yes |

---

## 8. Financial Engine Audit

### Isolation & Authority Guarantees

1. **Source of Truth**: `DashboardService`, `FinancialContextService`, `FinancialIntelligenceService`, `health_snapshot.py`, and `signals.py` compute all numbers deterministically in Python/PostgreSQL.
2. **LLM Boundary**: Personal metrics are passed inside `<personal_financial_context>` XML tags as read-only JSON. System instructions explicitly state:
   > *"Personal financial values inside `<personal_financial_context>` are authoritative facts. Never alter, recalculate, invent, or contradict them. DO NOT execute numerical calculations yourself."*
3. **User Isolation**: All Financial Engine queries require `user_id` extracted directly from the verified JWT token. RAG documents contain zero user-specific data.

---

## 9. LLM Provider Audit

### HuggingFaceProvider Infrastructure

- **Endpoint**: `https://router.huggingface.co/v1/chat/completions`
- **Active Model**: `meta-llama/Llama-3.1-8B-Instruct`
- **Max Tokens**: 1024 (`AI_MAX_TOKENS`)
- **Temperature**: 0.2
- **Timeout**: 60 seconds (`AI_REQUEST_TIMEOUT_SECONDS`)
- **HTTP Client**: `httpx.AsyncClient`

---

## 10. FastAPI Architecture Audit

FastAPI handles routing, authentication, rate limiting, and dependency injection:
- `backend/app/api/v1/ai.py`: Defines chat endpoints.
- `backend/app/api/deps.py`: Manages dependency instances (`get_ai_advisor_service`, `get_rag_retriever`, `get_llm_provider`).
- `backend/app/ai/rate_limiter.py`: In-memory rate limiting per user ID.

---

## 11. Recommended MiniLM Integration Point

- **Placement**: Create `LocalMiniLMProvider` in `backend/app/ai/providers/minilm.py` implementing `EmbeddingProvider`.
- **Model Storage**: Load `sentence-transformers/all-MiniLM-L6-v2` locally using `sentence-transformers` library with CPU singleton caching.
- **Compatibility**: Generates 384d float vectors matching existing pgvector column schema (`VectorType(dim=384)`).
- **Execution**: Replaces remote HTTP API call in `get_embedding_provider()` to eliminate network latency for embeddings.

---

## 12. Recommended FAISS Integration Point

- **Placement**: Create `FAISSIndexManager` in `backend/app/ai/rag/faiss_index.py`.
- **Co-existence**: Operates as in-memory candidate retrieval index alongside `PostgresRAGRetriever`.
- **Index Type**: `faiss.IndexFlatIP` (Cosine similarity on normalized 384d vectors) or `IndexHNSWFlat`.
- **Candidate Return Structure**: Returns `List[Tuple[int, float]]` mapping `chunk_id` to similarity score.
- **Fallback**: If FAISS index is uninitialized or fails, transparently fall back to `KnowledgeChunkRepository.search_similarity` (pgvector).

---

## 13. Recommended Hybrid Retrieval Architecture

```
User Query
  │
  ▼
QueryProcessor (Normalization, Expansion, Rewriting)
  │
  ▼
Local MiniLM Embedding (384d)
  │
  ├──► 1. FAISS In-Memory Search (Primary Candidate Retrieval, ~1ms)
  └──► 2. pgvector DB Search (Fallback / Verification Candidate Retrieval)
  │
  ▼
Candidate Pool Merger & Deduplication (chunk_ids)
  │
  ▼
Phase J DeterministicReranker (Multi-Factor Scoring)
  │
  ▼
Top-K Ranked RAG Chunks
```

---

## 14. Query Understanding Architecture Proposal

To complement the current system without breaking existing pipelines:
1. **Spelling & Typo Recognizer**: Integrate `SymSpell` or `RapidFuzz` in `QueryProcessor` using a financial dictionary built from `query_terms.json` and RAG titles.
2. **Hinglish & Mixed-Language Parser**: Expand the Hinglish dictionary mapping in `QueryProcessor` to translate key intent phrases before embedding generation.
3. **Financial Acronym Resolver**: Expand `query_terms.json` to cover expanded financial terminology.

---

## 15. Query Rewriting Proposal

For follow-up questions containing pronouns (*"what is it"*, *"is that good for me"*):
- Store previous N messages in conversation context.
- Use a lightweight rule-based or fast LLM rewriter to transform ambiguous queries into standalone search strings (e.g. `"is that good for me"` after a SIP question -> `"is SIP investment good for my financial health"`).

---

## 16. Query-to-Answer Relevance Guard Proposal

Post-generation validation step before returning to user:
- Compare generated assistant response against original question using semantic similarity.
- Verify that response explicitly addresses intent (e.g. checks if user asked about SIP and response mentions SIP).

---

## 17. Latency Bottleneck Analysis

| Pipeline Stage | Current Latency | Latency Impact | Proposed Phase L Optimization |
| :--- | :--- | :--- | :--- |
| **Intent Classification** | 0.1 – 1.8 ms | Negligible | Keep deterministic rules |
| **Financial Engine Context** | 10 – 40 ms | Low | Optimize query pre-fetching |
| **RAG Embedding Generation** | 5 – 25 ms (HTTP) | Medium | Replace with Local MiniLM (~1 ms) |
| **Vector DB Search (pgvector)** | 15 – 28 ms | Low | Complement with FAISS (~0.5 ms) |
| **Deterministic Reranker** | 1 – 4 ms | Negligible | Keep deterministic scoring |
| **Remote LLM Generation (HF)** | **29,000 – 48,000 ms** | **99.7% of total time** | Intent-aware token budgets & session pooling |
| **Safety Validation** | 1.5 – 2.7 ms | Negligible | Keep regex validation |
| **DB Persistence** | 5 – 20 ms | Low | Keep transaction safety |

---

## 18. Security Constraints

Future Phase L additions must preserve:
1. Strict user-scoped isolation in DB queries (`user_id`).
2. Prompt injection defense (`<untrusted_knowledge_content>` tags).
3. Separation of read-only `<personal_financial_context>`.
4. `SimpleSafetyValidator` rule enforcement.
5. Exclusion of archived documents unless `is_historical` flag is set.

---

## 19. Benchmark Extension Plan

Extend existing Phase J benchmark (`data/evaluation/rag/benchmark.json` - 125 queries) with:
- **Typo & Spelling Suite**: 20 queries with common typos (*"mutal fund"*, *"sip plan"*, *"ppff rate"*).
- **Hinglish Suite**: 20 queries (*"fd safe hai kya"*, *"mera savings rate kaisa hai"*).
- **Follow-up / Conversation-Aware Suite**: 15 multi-turn query sequences.
- **FAISS vs pgvector Latency Evaluation**: Measure candidate retrieval time comparison.

---

## 20. Architectural Risks

1. **Memory Footprint**: Loading local MiniLM in Python memory requires ~120 MB RAM.
2. **FAISS Index Sync**: Ensuring in-memory FAISS index stays in sync with PostgreSQL `knowledge_chunks` when documents are added/updated.
3. **Hinglish Ambiguity**: Over-translating non-financial conversational Hinglish phrases.

---

## 21. Recommended Phase L Implementation Order

1. **Phase L.1**: Local MiniLM Embedding Provider & FAISS Candidate Retriever Co-existence.
2. **Phase L.2**: Query Understanding (Typo/Spelling Correction & Hinglish Parser).
3. **Phase L.3**: Conversation-Aware Query Rewriting for RAG.
4. **Phase L.4**: Benchmark Extension & Latency / Quality Validation.

---

## Final Component Audit Summary Table

| Component | Current Implementation | Keep/Modify/Add | Reason | Risk |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI** | Route handler & dependency injection | **Keep** | Fully functional & secure | None |
| **IntentRouter** | Rule-based classifier (4 intents, 8 sub-intents) | **Modify** | Add fine-grained typo-tolerant intent matching | Low |
| **QueryProcessor** | Text normalizer & synonym expander | **Modify** | Add typo correction, Hinglish parser, and query rewriting | Low |
| **EmbeddingProvider** | Remote Hugging Face API call | **Modify** | Add local MiniLM implementation for speed | Low |
| **MiniLM** | Configured as model string (384d) | **Add** | Local `sentence-transformers` execution | Low |
| **pgvector** | PostgreSQL `VectorType(384)` + L2 distance | **Keep** | Source of truth vector storage | None |
| **FAISS** | Not installed | **Add** | In-memory candidate search (~1ms) complementary to pgvector | Low |
| **PostgresRAGRetriever** | RAG retrieval orchestrator | **Keep / Modify** | Keep core retriever; wrap candidate fetch with FAISS hybrid pool | Low |
| **DeterministicReranker** | Multi-factor deterministic scoring | **Keep** | High precision, 100% explainable reranking | None |
| **Financial Engine** | `DashboardService` & `FinancialIntelligenceService` | **Keep** | Sole ground-truth authority for personal metrics | None |
| **AIContextBuilder** | Prompt assembly & XML context boundary | **Keep / Modify** | Keep prompt structure; optimize static instructions | Low |
| **HuggingFaceProvider** | Remote HF Llama-3.1-8B-Instruct client | **Keep / Modify** | Keep provider; add persistent session pool & dynamic tokens | Low |
| **SafetyValidator** | `SimpleSafetyValidator` (5 rules) | **Keep** | Essential safety & prompt injection defense | None |
| **PostgreSQL** | Database persistence | **Keep** | Core relational & vector data store | None |
| **React Frontend** | AI Advisor Chat Workspace | **Keep** | Fully functional UI with streaming support readiness | None |
