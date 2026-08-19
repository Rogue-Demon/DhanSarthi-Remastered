"""
Latency Breakdown Model for DhanSarthi Phase L.7.1 / L.7.2 Observability.

Provides a presentation-independent structure for numerical timing metrics,
candidate counts, and execution flags across the AI Advisor pipeline lifecycle.

Phase L.7.2 additions:
- Fine-grained LLM timing: llm_response_parse_ms
- Prompt component sizing: system_prompt_chars, knowledge_context_chars,
  personal_context_chars, conversation_history_chars, user_query_chars, total_prompt_chars
- Token budget metadata: max_tokens_budget, model_name
- Cache observability: cache_hit
- Token count estimates: prompt_token_count, response_token_count
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class LatencyBreakdown(BaseModel):
    """Granular timing breakdown and performance metrics in numeric milliseconds."""

    # Query Understanding Sub-breakdown (ms)
    query_understanding_ms: float = Field(default=0.0, description="Total Query Understanding duration")
    typo_normalization_ms: float = Field(default=0.0, description="Typo correction & text normalization time")
    hinglish_ms: float = Field(default=0.0, description="Hinglish translation & parsing time")
    reference_resolution_ms: float = Field(default=0.0, description="Pronoun & conversation reference resolution time")
    entity_extraction_ms: float = Field(default=0.0, description="Domain entity extraction time")
    intent_scope_ms: float = Field(default=0.0, description="Intent & scope classification time")
    retrieval_rewrite_ms: float = Field(default=0.0, description="Retrieval query rewriting & expansion time")

    # Adaptive Routing (ms)
    adaptive_routing_ms: float = Field(default=0.0, description="Adaptive retrieval router decision time")

    # Retrieval Stack (ms)
    pgvector_ms: float = Field(default=0.0, description="PostgreSQL pgvector vector similarity search time")
    faiss_ms: float = Field(default=0.0, description="FAISS local index search time")
    fusion_ms: float = Field(default=0.0, description="RRF candidate fusion & deduplication time")

    # MiniLM Cross-Scoring (ms)
    minilm_ms: float = Field(default=0.0, description="Total MiniLM semantic scoring duration")
    minilm_model_load_ms: float = Field(default=0.0, description="MiniLM model load / initialization time (if triggered)")
    minilm_embedding_ms: float = Field(default=0.0, description="MiniLM embedding computation time")
    minilm_scoring_ms: float = Field(default=0.0, description="MiniLM cross-attention scoring time")

    # Phase J Reranker (ms)
    reranker_ms: float = Field(default=0.0, description="Phase J deterministic reranker duration")

    # Context Builder (ms)
    context_build_ms: float = Field(default=0.0, description="AIContext building & prompt formatting time")

    # LLM Provider (ms)
    llm_request_ms: float = Field(default=0.0, description="Total LLM HTTP round-trip latency (request + response body)")
    llm_generation_ms: float = Field(default=0.0, description="LLM text generation duration (equal to llm_request_ms for non-streaming providers)")
    llm_response_parse_ms: float = Field(default=0.0, description="Time to parse JSON response body and extract generated text")
    time_to_first_byte_ms: Optional[float] = Field(default=None, description="Time to first byte if reported by provider")
    time_to_first_token_ms: Optional[float] = Field(default=None, description="Time to first token if reported by provider")

    # Safety Validation & Database Persistence (ms)
    safety_validation_ms: float = Field(default=0.0, description="Safety validator inspection time")
    persistence_ms: float = Field(default=0.0, description="Database session commit & message persistence time")

    # Overall Lifecycle (ms)
    total_ms: float = Field(default=0.0, description="Total end-to-end request lifecycle duration")

    # Operational Counts & Execution Flags
    pgvector_used: bool = Field(default=False, description="Whether pgvector retrieval was executed")
    faiss_used: bool = Field(default=False, description="Whether FAISS retrieval was executed")
    minilm_used: bool = Field(default=False, description="Whether MiniLM semantic scoring was executed")
    candidate_count_pgvector: int = Field(default=0, description="Candidates retrieved from pgvector")
    candidate_count_faiss: int = Field(default=0, description="Candidates retrieved from FAISS")
    candidate_count_fused: int = Field(default=0, description="Candidates remaining after RRF fusion")
    candidate_count_before_rerank: int = Field(default=0, description="Candidates before Phase J reranking")
    candidate_count_after_rerank: int = Field(default=0, description="Candidates after Phase J reranking")
    rag_chunk_count: int = Field(default=0, description="Number of RAG knowledge chunks included in prompt")
    personal_context_fields_count: int = Field(default=0, description="Number of user financial sections with has_data=True")

    # Phase L.7.2 — Prompt Component Size Breakdown (chars)
    prompt_char_count: int = Field(default=0, description="Total assembled prompt length in characters")
    system_prompt_chars: int = Field(default=0, description="System instructions section length in characters")
    personal_context_chars: int = Field(default=0, description="Personal financial context JSON length in characters")
    knowledge_context_chars: int = Field(default=0, description="RAG knowledge blocks section length in characters")
    conversation_history_chars: int = Field(default=0, description="Conversation history section length in characters")
    user_query_chars: int = Field(default=0, description="User question section length in characters")

    # Phase L.7.2 — Token Budget & Model Metadata
    max_tokens_budget: int = Field(default=0, description="max_tokens budget selected for this request by TokenBudgetSelector")
    model_name: str = Field(default="", description="LLM model identifier used for this request")
    prompt_token_count: Optional[int] = Field(default=None, description="Estimated prompt token count (character-ratio estimate)")
    response_token_count: Optional[int] = Field(default=None, description="Estimated response token count (character-ratio estimate)")

    # Phase L.7.2 — Cache Observability
    cache_hit: bool = Field(default=False, description="Whether response was served from educational cache (no LLM call made)")

    # Phase L.7.3 — Provider Request Observability
    retry_count: int = Field(default=0, description="Number of retries attempted before a successful response or final failure")
    request_status: str = Field(default="SUCCESS", description="Terminal request outcome: SUCCESS | RETRY_SUCCESS | FAILED")
    provider_name: str = Field(default="", description="Active LLM provider identifier (e.g. 'huggingface', 'mock')")
    streaming_used: bool = Field(default=False, description="Whether SSE streaming was used for this request")

    # Phase L.7.4 — Adaptive LLM Inference Observability
    inference_config_ms: float = Field(default=0.0, description="Inference complexity classification & budget selection time")
    context_optimization_ms: float = Field(default=0.0, description="Context routing & character budget trimming time")
    history_selection_ms: float = Field(default=0.0, description="Adaptive history selection & character cap time")
    rag_context_optimization_ms: float = Field(default=0.0, description="RAG knowledge chunk optimization & token budget trimming time")

    effective_max_tokens: int = Field(default=0, description="Effective max_tokens output budget passed to LLM")
    effective_history_messages: int = Field(default=0, description="Number of conversation history messages retained after adaptive trimming")

    prompt_chars_before: int = Field(default=0, description="Unoptimized total prompt character count")
    prompt_chars_after: int = Field(default=0, description="Optimized final prompt character count")
    rag_chars_before: int = Field(default=0, description="Unoptimized RAG context character count")
    rag_chars_after: int = Field(default=0, description="Optimized RAG context character count")
    personal_context_chars_before: int = Field(default=0, description="Unoptimized personal context character count")
    personal_context_chars_after: int = Field(default=0, description="Optimized personal context character count")

    estimated_prompt_tokens: Optional[int] = Field(default=None, description="Estimated prompt token count")
    estimated_output_tokens: Optional[int] = Field(default=None, description="Estimated output token count")
    estimated_total_tokens: Optional[int] = Field(default=None, description="Estimated total token workload (prompt + output)")

    # Phase L.8 & L.9.8 — Real-Time LLM Inference Observability
    model_selection_ms: float = Field(default=0.0, description="Model routing & candidate selection duration")
    tokenizer_load_ms: float = Field(default=0.0, description="Tokenizer lazy loading / initialization duration")
    tokenizer_count_ms: float = Field(default=0.0, description="Tokenizer token counting duration")
    request_start_ms: Optional[float] = Field(default=None, description="Timestamp/epoch in ms when provider request started")
    provider_connection_ms: Optional[float] = Field(default=None, description="Time taken to establish connection to provider")
    provider_network_ms: float = Field(default=0.0, description="LLM provider HTTP connection & initial response latency")
    ttft_ms: Optional[float] = Field(default=None, description="Time to first token / chunk for streaming responses")
    generation_ms: float = Field(default=0.0, description="LLM provider text generation latency")
    total_llm_ms: float = Field(default=0.0, description="Total LLM round-trip execution latency")
    generated_tokens: Optional[int] = Field(default=None, description="Actual or tokenizer-counted generated token count")
    prompt_tokens: Optional[int] = Field(default=None, description="Actual or tokenizer-counted prompt token count")
    tokens_per_second: Optional[float] = Field(default=None, description="Generation speed in tokens per second")
    selected_model: str = Field(default="", description="Active model ID selected for this request")
    model_routing_reason: str = Field(default="", description="Rationale for the selected model candidate")

    # Phase L.9.1 Quality Evaluation & Controlled Retry
    quality_evaluation_ms: Optional[float] = Field(default=None, description="Time taken for response quality evaluation")
    quality_retry_used: bool = Field(default=False, description="Whether a controlled quality retry was executed")
    quality_retry_ms: Optional[float] = Field(default=None, description="Latency spent executing quality retry generation")
    quality_overall_score: Optional[float] = Field(default=None, description="Deterministic overall quality score (0.0 to 1.0)")
    quality_passed: Optional[bool] = Field(default=None, description="Whether final response passed quality evaluation")

    # Phase L.9.6 — Response Caching & In-Flight Deduplication Observability
    cache_lookup_ms: float = Field(default=0.0, description="Time taken to check response cache")
    cache_hit: bool = Field(default=False, description="Whether response was served from cache")
    cache_write_ms: float = Field(default=0.0, description="Time taken to write response to cache")
    cache_entry_age_ms: Optional[float] = Field(default=None, description="Age of the cached response entry in milliseconds")
    inflight_deduplicated: bool = Field(default=False, description="Whether request was coalesced with an in-flight duplicate")
    llm_skipped_due_to_cache: bool = Field(default=False, description="Whether LLM inference was avoided due to cache hit")

    # Phase L.9.7 — Intelligent Prompt Compression & Context Efficiency Observability
    prompt_compression_ms: float = Field(default=0.0, description="Time taken for prompt compression and context pruning")
    prompt_tokens_before: Optional[int] = Field(default=None, description="Prompt token count before compression")
    prompt_tokens_after: Optional[int] = Field(default=None, description="Prompt token count after compression")
    prompt_compression_ratio: Optional[float] = Field(default=None, description="Prompt compression ratio (tokens_after / tokens_before)")
    rag_chunks_before_compression: int = Field(default=0, description="RAG chunks count before compression")
    rag_chunks_after_compression: int = Field(default=0, description="RAG chunks count after compression")
    history_messages_before_compression: int = Field(default=0, description="History message count before compression")
    history_messages_after_compression: int = Field(default=0, description="History message count after compression")
    prompt_compression_mode: str = Field(default="", description="Compression mode applied: NONE, LIGHT, MODERATE, AGGRESSIVE")

    def to_dict(self) -> Dict[str, Any]:
        """Return numeric dictionary representation rounded to 2 decimal places."""
        data = self.model_dump()
        result = {}
        for k, v in data.items():
            if isinstance(v, float):
                result[k] = round(v, 2)
            else:
                result[k] = v
        return result
