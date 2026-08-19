# DhanSarthi — Phase L.3 Intelligent Retrieval Query Rewriting

## Architecture & Overview

Phase L.3 introduces **`RetrievalQueryRewriter`**, a local, deterministic, and lightweight query expansion engine designed specifically for vector search against pgvector without LLM calls or external network requests.

### Core Pipeline Flow

```mermaid
flowchart TD
    UserQuery["User Input (e.g., 'SIP kya hota hai?')"] --> QueryUnderstanding["Query Understanding (Phase L.1)"]
    QueryUnderstanding --> ExecutionPlan["QueryExecutionPlan (Phase L.2)"]
    
    subgraph Intelligent Retrieval Query Rewriting (Phase L.3)
        ExecutionPlan --> Rewriter["RetrievalQueryRewriter"]
        Rewriter --> InjectionDefense["1. Prompt Injection Defense (Strips directives)"]
        Rewriter --> NoiseRemoval["2. Filler Noise Removal"]
        Rewriter --> CanonicalExpand["3. Canonical Financial Expansion (data/knowledge/query_terms.json)"]
        Rewriter --> IntentTerms["4. Intent & Scope Search Terms (e.g., 'definition', 'risks')"]
        Rewriter --> EntityAuthority["5. Entity & Regulatory Authority Terms (RBI, SEBI)"]
        Rewriter --> TemporalTerms["6. Temporal Terms (FY 2025-26)"]
        Rewriter --> Deduplication["7. Token-Level Deduplication & Bounding (< 250 chars)"]
    end
    
    Deduplication --> RewriteResult["RetrievalRewriteResult"]
    RewriteResult -->|retrieval_query| RAGRetriever["PostgresRAGRetriever"]
    RAGRetriever --> Reranker["DeterministicReranker (Phase J)"]
    Reranker --> PromptBuilder["AIContextBuilder"]
```

---

## Key Query Representations

1. **`original_query`**: The exact raw user input (preserved for UI display and conversation history).
2. **`resolved_query`**: The query after conversation pronoun resolution (used in LLM user question prompt).
3. **`retrieval_query`**: Search-optimized string passed to `PostgresRAGRetriever.retrieve()`.

---

## Core Capabilities Implemented

### 1. Canonical Term Expansion
Uses `data/knowledge/query_terms.json` to map shortcuts and acronyms:
- **`SIP`** → `systematic investment plan`, `periodic investment`, `regular investment`
- **`MF`** → `mutual fund`, `mutual funds`
- **`FD`** → `fixed deposit`, `bank fixed deposit`, `term deposit`
- **`RD`** → `recurring deposit`
- **`PPF`** → `public provident fund`
- **`NPS`** → `national pension system`
- **`NAV`** → `net asset value`
- **`EMI`** → `equated monthly installment`

### 2. Intent-Aware Terms
- **Definition queries**: Adds `definition`, `how it works`, `features`.
- **Risk queries**: Adds `investment risk`, `risk factors`, `market risk`, `volatility`.
- **Comparison queries**: Adds `comparison`, `risk`, `returns`, `liquidity`, `tax`.
- **Recommendation queries**: Adds `investment suitability`, `risks`, `benefits`, `considerations`.

### 3. Personal & Mixed Query Isolation
- **Personal Lookup**: `requires_rag = False`. Pure personal queries skip RAG entirely.
- **Analytical & Mixed Queries**: High-level financial principles are searched without injecting personal financial numbers into vector search strings.

### 4. Regulatory & Temporal Preservation
- Preserves regulatory authorities (`RBI`, `SEBI`, `AMFI`, `Income Tax Department`, `PFRDA`).
- Retains tax codes (`Section 80C`, `Section 80D`, `STCG`, `LTCG`, `TDS`).
- Retains financial year markers (`FY 2025-26`).

### 5. Security & Prompt Injection Defense
- Strips adversarial prompt injection attempts (`"ignore previous instructions"`, `"forget rules"`, `"bypass safety"`).
- User input is treated strictly as **DATA**, ensuring malicious directives are never passed to backend search or context models.

---

## Evaluation Benchmark Results

Evaluated using the authoritative Phase J RAG benchmark script (`app/ai/evaluate_rag.py`):

| Metric | Raw Query (Before L.3) | Rewritten Query (After L.3) | Improvement |
| :--- | :---: | :---: | :---: |
| **Hit@1** | 6.14% | **25.44%** | **+314%** |
| **Hit@3** | 11.40% | **35.96%** | **+215%** |
| **Hit@5** | 14.91% | **37.72%** | **+153%** |
| **MRR** | 0.0912 | **0.3022** | **+231%** |
| **Authority Accuracy** | 24.56% | **48.25%** | **+96%** |
| **Citation Accuracy** | 96.67% | **98.07%** | **+1.4%** |
| **Abstention Accuracy** | 63.89% | **63.89%** | **Preserved (100%)** |

---

## Performance & Test Results

### 1. Dedicated Test Suite (`backend/tests/ai/test_retrieval_rewriter.py`)
- **15/15 Passed** in 0.17s.
- Average rewrite latency: **< 1.0 ms per query** (target: < 5 ms).

### 2. Total Backend Test Suite
- Total Backend Pytest Suite: **494 Passed, 1 Skipped, 0 Failures** (100% PASS, 0 Regressions).

### 3. Frontend Quality & Production Build
- ESLint: **0 errors**.
- Vite Production Build: **Exited with code 0** (Clean Build).
