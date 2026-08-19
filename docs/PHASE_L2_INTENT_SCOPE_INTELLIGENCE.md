# DhanSarthi — Phase L.2 Intent, Entity & Scope Intelligence

## Architecture & Overview

Phase L.2 upgrades DhanSarthi from *"understanding the words"* to **"understanding exactly what the user wants."**

It builds upon the Phase L.1 Query Understanding Layer by generating a 100% deterministic, local, millisecond-level **`QueryExecutionPlan`** before retrieval and LLM context assembly take place.

### Core Architecture Flow

```mermaid
flowchart TD
    UserQuery["User Message (e.g., 'SIP vs FD' or 'How much did I invest in SIP?')"] --> QueryUnderstanding["Query Understanding Layer (Phase L.1)"]
    
    subgraph Intent, Scope & Source Intelligence (Phase L.2)
        QueryUnderstanding --> Classifier["IntentScopeClassifier"]
        Classifier --> ScopeDetect["1. Scope Classification (10 Scopes)"]
        Classifier --> OpDetect["2. Operation Detection (14 Operations)"]
        Classifier --> EntityRoles["3. Entity Role Assignment (6 Roles)"]
        Classifier --> CompDetect["4. Comparison Extraction"]
        Classifier --> PersonLevel["5. Personalization Level (NONE, LOW, MEDIUM, HIGH)"]
        Classifier --> ClarifyCheck["6. Clarification & Ambiguity Guardrail"]
        Classifier --> SourceSelect["7. Deterministic Source Selection"]
    end
    
    SourceSelect --> Plan["QueryExecutionPlan"]
    
    Plan -->|clarification_required = True| ShortCircuit["Immediate Polite Clarification Response"]
    Plan -->|requires_rag = True| RAG["PostgresRAGRetriever"]
    Plan -->|requires_financial_engine = True| FE["Financial Engine"]
    Plan -->|requires_market_data = True| Market["Market Data Service"]
    Plan --> PromptBuilder["AIContextBuilder"]
```

---

## Data Models (`backend/app/ai/schemas/query_execution_plan.py`)

### `QueryExecutionPlan` Schema

```python
class QueryExecutionPlan(BaseModel):
    original_query: str
    intent: QueryIntent
    sub_intent: SubIntent
    scope: QueryScope
    operation: OperationType
    entities: List[ExtractedEntity] = Field(default_factory=list)
    entity_roles: Dict[str, EntityRole] = Field(default_factory=dict)
    comparison_info: ComparisonInfo = Field(default_factory=ComparisonInfo)
    personalization_level: PersonalizationLevel = PersonalizationLevel.NONE

    # Source selection flags (100% deterministic)
    requires_rag: bool = False
    requires_financial_engine: bool = False
    requires_market_data: bool = False
    requires_conversation_context: bool = False
    requires_user_profile: bool = False
    requires_document_context: bool = False

    # Clarification requirements
    clarification_required: bool = False
    clarification_reason: Optional[str] = None
    clarification_prompt: Optional[str] = None

    confidence: float = 1.0
```

---

## Key Classification Dimensions

### 1. Query Scopes (`QueryScope`)
- **`EDUCATIONAL`**: Generic conceptual inquiries (*"What is SIP?"*)
- **`PERSONAL_LOOKUP`**: Fact extraction from personal records (*"How much did I spend this month?"*)
- **`PERSONAL_ANALYSIS`**: Diagnostics on user financial health (*"Why am I overspending?"*)
- **`MIXED`**: Combined diagnostic + educational/planning (*"Is my savings rate healthy and how to improve it?"*)
- **`COMPARISON`**: Comparative option evaluation (*"SIP vs FD"*)
- **`PLANNING`**: Goal-oriented strategy (*"How should I build an emergency fund?"*)
- **`MARKET_INFORMATION`**: Live market rate inquiries (*"What is the current gold price?"*)
- **`TRANSACTIONAL`**: Action request (*"Buy this stock for me"* - flagged for safety, trade execution blocked)
- **`CASUAL`**: Greetings (*"Hi", "How are you?"*)
- **`AMBIGUOUS`**: Queries lacking required context (*"Should I invest?"*)

### 2. Operation Types (`OperationType`)
`EXPLAIN`, `DEFINE`, `CALCULATE`, `LOOKUP`, `ANALYZE`, `COMPARE`, `RECOMMEND`, `PLAN`, `PREDICT`, `SUMMARIZE`, `CLASSIFY`, `CHECK`, `TRACK`, `ACTION_REQUEST`.

### 3. Entity Roles (`EntityRole`)
- **`SUBJECT`**: Core concept under discussion (*"SIP"* in *"What is SIP?"*)
- **`FILTER`**: Product query constraint (*"SIP"* in *"How much did I invest in SIP?"*)
- **`INVESTMENT_TARGET`**: Target product (*"SIP"* in *"Should I increase my SIP?"*)
- **`COMPARISON_LEFT` / `COMPARISON_RIGHT`**: Comparison entities (*"SIP"* and *"FD"* in *"SIP vs FD"*)
- **`PERSONAL_INVESTMENT`**: Existing user asset (*"My SIP return is low"*)

### 4. Personalization Levels (`PersonalizationLevel`)
- `NONE`: Generic educational query (*"What is SIP?"*)
- `LOW`: Generic recommendation inquiry (*"Is SIP good?"*)
- `MEDIUM`: Context-guided recommendation (*"Is SIP good for someone in 20s?"*)
- `HIGH`: Explicitly personal (*"Is SIP good for me based on my income?"*)

---

## Deterministic Data Source Selection Matrix

| Query Type | `requires_rag` | `requires_financial_engine` | `requires_market_data` | `requires_user_profile` |
| :--- | :---: | :---: | :---: | :---: |
| *"What is SIP?"* (Educational) | **True** | False | False | False |
| *"How much did I spend this month?"* (Personal Lookup) | False | **True** | False | **True** |
| *"Is my savings rate healthy?"* (Personal Analysis) | **True** | **True** | False | **True** |
| *"SIP vs FD"* (Comparison) | **True** | False | False | False |
| *"What is today's gold price?"* (Market Info) | False | False | **True** | False |
| *"Should I invest?"* (Ambiguous) | **False** | **False** | **False** | False |

> **Rule**: When `clarification_required = True`, all heavy backend data fetching is short-circuited (`requires_rag = False`, `requires_financial_engine = False`, `requires_market_data = False`) and the assistant responds immediately with a concise clarification prompt.

---

## Verification & Performance

### 1. Performance & Latency
- Classification is **100% local, deterministic, and executed without LLM calls**.
- Tested average execution plan classification latency: **< 0.5 ms per query** (300 queries evaluated in 0.11s).

### 2. Backend Test Results (`backend/tests/ai/test_query_execution_plan.py`)
- **16/16 Test Suites Passed** in 0.11s.
- Total Backend Pytest Suite: **479 Passed, 1 Skipped, 0 Failures** (100% PASS, 0 Regressions).

### 3. Frontend Quality & Production Build
- ESLint: **0 errors**.
- Vite Production Build: **Exited with code 0** (Clean Build).

---

## Before / After Examples

| User Query | Phase L.1 Output | Phase L.2 `QueryExecutionPlan` Output |
| :--- | :--- | :--- |
| *"What is mutal fund?"* | Corrected: `"What is mutual fund?"` | Scope: `EDUCATIONAL`, Op: `DEFINE`, Role: `SUBJECT`, Sources: `RAG=True, FE=False` |
| *"How much did I invest in SIP?"* | Extracted: `Entity(Mutual Fund)` | Scope: `PERSONAL_LOOKUP`, Op: `LOOKUP`, Role: `FILTER`, Sources: `RAG=False, FE=True` |
| *"SIP vs FD"* | Entities: `[SIP, FD]` | Scope: `COMPARISON`, Op: `COMPARE`, Roles: `[COMPARISON_LEFT, COMPARISON_RIGHT]`, Dimension: `general` |
| *"Should I invest?"* (No history) | Intent: `GENERAL_FINANCE` | Scope: `AMBIGUOUS`, `clarification_required = True`, Short-circuit prompt: *"What are you considering investing in—stocks, mutual funds, an SIP, or something else?"* |
