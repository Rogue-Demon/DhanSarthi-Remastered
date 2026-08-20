"""
Latency Breakdown Model for DhanSarthi Phase L.7.1 / L.7.2 Observability.

Provides a presentation-independent structure for numerical timing metrics,
candidate counts, and execution flags across the AI Advisor pipeline lifecycle.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class LatencyBreakdown(BaseModel):
    """Granular timing breakdown and performance metrics in numeric milliseconds."""

    query_understanding_ms: float = Field(default=0.0)
    typo_normalization_ms: float = Field(default=0.0)
    hinglish_ms: float = Field(default=0.0)
    reference_resolution_ms: float = Field(default=0.0)
    entity_extraction_ms: float = Field(default=0.0)
    intent_scope_ms: float = Field(default=0.0)
    retrieval_rewrite_ms: float = Field(default=0.0)
    adaptive_routing_ms: float = Field(default=0.0)
    pgvector_ms: float = Field(default=0.0)
    faiss_ms: float = Field(default=0.0)
    fusion_ms: float = Field(default=0.0)
    minilm_ms: float = Field(default=0.0)
    minilm_model_load_ms: float = Field(default=0.0)
    minilm_embedding_ms: float = Field(default=0.0)
    minilm_scoring_ms: float = Field(default=0.0)
    reranker_ms: float = Field(default=0.0)
    context_build_ms: float = Field(default=0.0)
    llm_request_ms: float = Field(default=0.0)
    llm_generation_ms: float = Field(default=0.0)
    llm_response_parse_ms: float = Field(default=0.0)
    time_to_first_byte_ms: Optional[float] = Field(default=None)
    time_to_first_token_ms: Optional[float] = Field(default=None)
    safety_validation_ms: float = Field(default=0.0)
    # Phase L.11.1 Stage Profiling Metrics
    ownership_check_ms: float = Field(default=0.0)
    user_persistence_ms: float = Field(default=0.0)
    financial_context_ms: float = Field(default=0.0)
    history_retrieval_ms: float = Field(default=0.0)
    financial_intelligence_ms: float = Field(default=0.0)
    market_data_ms: float = Field(default=0.0)
    prompt_build_ms: float = Field(default=0.0)
    cache_eligibility_ms: float = Field(default=0.0)
    cache_key_ms: float = Field(default=0.0)
    assistant_persistence_ms: float = Field(default=0.0)
    persistence_ms: float = Field(default=0.0)
    telemetry_record_ms: float = Field(default=0.0)
    total_ms: float = Field(default=0.0)

    # Phase L.11.2 Fast-Path & Adaptive Token Budget Metrics
    personal_fast_path_used: bool = Field(default=False)
    general_rag_skipped: bool = Field(default=False)
    market_data_skipped: bool = Field(default=False)
    minimal_context_used: bool = Field(default=False)
    adaptive_output_budget: int = Field(default=0)
    fast_path_reason: Optional[str] = Field(default=None)

    pgvector_used: bool = Field(default=False)
    faiss_used: bool = Field(default=False)
    minilm_used: bool = Field(default=False)
    candidate_count_pgvector: int = Field(default=0)
    candidate_count_faiss: int = Field(default=0)
    candidate_count_fused: int = Field(default=0)
    candidate_count_before_rerank: int = Field(default=0)
    candidate_count_after_rerank: int = Field(default=0)
    rag_chunk_count: int = Field(default=0)
    personal_context_fields_count: int = Field(default=0)

    prompt_char_count: int = Field(default=0)
    system_prompt_chars: int = Field(default=0)
    personal_context_chars: int = Field(default=0)
    knowledge_context_chars: int = Field(default=0)
    conversation_history_chars: int = Field(default=0)
    user_query_chars: int = Field(default=0)

    max_tokens_budget: int = Field(default=0)
    model_name: str = Field(default="")
    prompt_token_count: Optional[int] = Field(default=None)
    response_token_count: Optional[int] = Field(default=None)

    retry_count: int = Field(default=0)
    request_status: str = Field(default="SUCCESS")
    provider_name: str = Field(default="")
    streaming_used: bool = Field(default=False)

    # Phase L.9.8 — Streaming UX / cancellation observability
    stream_chunks: int = Field(default=0, description="Number of non-empty provider chunks received")
    stream_cancelled: bool = Field(default=False, description="Whether the client/provider stream was cancelled")
    stream_completed: bool = Field(default=False, description="Whether the provider emitted a normal completion")
    stream_error: bool = Field(default=False, description="Whether streaming terminated with a provider/transport error")
    stream_first_chunk_ms: Optional[float] = Field(default=None, description="Monotonic time to first non-empty stream chunk")
    stream_duration_ms: Optional[float] = Field(default=None, description="Total provider streaming duration")

    inference_config_ms: float = Field(default=0.0)
    context_optimization_ms: float = Field(default=0.0)
    history_selection_ms: float = Field(default=0.0)
    rag_context_optimization_ms: float = Field(default=0.0)
    effective_max_tokens: int = Field(default=0)
    effective_history_messages: int = Field(default=0)
    prompt_chars_before: int = Field(default=0)
    prompt_chars_after: int = Field(default=0)
    rag_chars_before: int = Field(default=0)
    rag_chars_after: int = Field(default=0)
    personal_context_chars_before: int = Field(default=0)
    personal_context_chars_after: int = Field(default=0)
    estimated_prompt_tokens: Optional[int] = Field(default=None)
    estimated_output_tokens: Optional[int] = Field(default=None)
    estimated_total_tokens: Optional[int] = Field(default=None)

    model_selection_ms: float = Field(default=0.0)
    tokenizer_load_ms: float = Field(default=0.0)
    tokenizer_count_ms: float = Field(default=0.0)
    request_start_ms: Optional[float] = Field(default=None)
    provider_connection_ms: Optional[float] = Field(default=None)
    provider_network_ms: float = Field(default=0.0)
    ttft_ms: Optional[float] = Field(default=None)
    generation_ms: float = Field(default=0.0)
    total_llm_ms: float = Field(default=0.0)
    generated_tokens: Optional[int] = Field(default=None)
    prompt_tokens: Optional[int] = Field(default=None)
    tokens_per_second: Optional[float] = Field(default=None)
    selected_model: str = Field(default="")
    model_routing_reason: str = Field(default="")

    quality_evaluation_ms: Optional[float] = Field(default=None)
    quality_retry_used: bool = Field(default=False)
    quality_retry_ms: Optional[float] = Field(default=None)
    quality_overall_score: Optional[float] = Field(default=None)
    quality_passed: Optional[bool] = Field(default=None)

    cache_lookup_ms: float = Field(default=0.0)
    cache_hit: bool = Field(default=False)
    cache_write_ms: float = Field(default=0.0)
    cache_entry_age_ms: Optional[float] = Field(default=None)
    inflight_deduplicated: bool = Field(default=False)
    llm_skipped_due_to_cache: bool = Field(default=False)

    prompt_compression_ms: float = Field(default=0.0)
    prompt_tokens_before: Optional[int] = Field(default=None)
    prompt_tokens_after: Optional[int] = Field(default=None)
    prompt_compression_ratio: Optional[float] = Field(default=None)
    rag_chunks_before_compression: int = Field(default=0)
    rag_chunks_after_compression: int = Field(default=0)
    history_messages_before_compression: int = Field(default=0)
    history_messages_after_compression: int = Field(default=0)
    prompt_compression_mode: str = Field(default="")

    # Phase L.9.9 — AI Production Resilience, Failure Recovery & Graceful Degradation
    resilience_ms: float = Field(default=0.0)
    retry_count: int = Field(default=0)
    fallback_used: bool = Field(default=False)
    fallback_type: Optional[str] = Field(default=None)
    circuit_state: str = Field(default="CLOSED")
    failure_type: str = Field(default="NONE")
    recovery_time_ms: Optional[float] = Field(default=None)
    stream_interrupted: bool = Field(default=False)
    client_cancelled: bool = Field(default=False)
    safe_fallback_used: bool = Field(default=False)

    def to_dict(self) -> Dict[str, Any]:
        """Return numeric dictionary representation rounded to 2 decimal places."""
        data = self.model_dump()
        result: Dict[str, Any] = {}
        for key, value in data.items():
            result[key] = round(value, 2) if isinstance(value, float) else value
        return result
