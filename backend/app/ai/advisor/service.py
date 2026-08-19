"""
Core AI Advisor Service for DhanSarthi.

Orchestrates the entire query reasoning pipeline:
  1. Verify conversation ownership (for conversation-threaded calls).
  2. Retrieve user financial context (from DashboardService).
  3. Query RAG retriever for general financial knowledge.
  4. Load recent conversation history.
  5. Build query-filtered AIContext and assemble prompt.
  6. Generate response via LLMProvider (with timeout).
  7. Validate output using AISafetyValidator.
  8. Persist assistant message (after user message already committed).
  9. Return safe, structured response.

Transaction strategy:
  - User message committed BEFORE LLM call (so it is never lost on LLM failure).
  - Assistant message committed AFTER successful validation.
  - LLM errors do NOT store a fake assistant message.
"""

from __future__ import annotations

import asyncio
import re
import time
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.context.builder import AIContextBuilder
from app.ai.exceptions import AIAdvisorError, AISafetyError
from app.ai.providers.base import LLMProvider
from app.ai.rag.base import RAGRetriever
from app.ai.safety.base import AISafetyValidator
from app.ai.schemas.advisor import (
    AIAdvisorRequest,
    AIAdvisorResponse,
    CitationSource,
    MessageResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from app.core.config import settings
from app.services.conversation_service import ConversationService
from app.services.dashboard_service import DashboardService
from app.services.financial_intelligence_service import FinancialIntelligenceService
from app.ai.router import IntentRouter, QueryIntent
from app.market_data.service import MarketDataService
from app.ai.query_understanding.service import QueryUnderstandingService
from app.ai.generation.token_budget import TokenBudgetSelector
from app.ai.cache import (
    CacheEligibilityPolicy,
    CacheKeyBuilder,
    InFlightDeduplicator,
    IntelligentResponseCache,
    ResponseCacheEntry,
    get_response_cache,
    get_educational_cache,
    get_inflight_deduplicator,
)


from app.ai.rag.adaptive_router import AdaptiveRetrievalRouter
from app.ai.observability.latency import LatencyTracker
from app.ai.inference.budget import AdaptiveTokenBudgetSelector
from app.ai.inference.context_optimizer import LLMContextOptimizer
from app.ai.inference.model_router import ModelRouter, ModelRoutingDecision
from app.ai.evaluation.response_quality import ResponseQualityEvaluator, ResponseQualityResult
from app.ai.inference.prompt_compressor import PromptCompressor, get_prompt_compressor


class AIAdvisorService:
    """Orchestrates de-identified user data retrieval, RAG, prompt assembly, and LLM query safety."""

    def __init__(
        self,
        db: Session,
        llm_provider: LLMProvider,
        rag_retriever: RAGRetriever,
        safety_validator: AISafetyValidator,
        context_builder: AIContextBuilder,
        dashboard_service: DashboardService,
        conversation_service: Optional[ConversationService] = None,
        financial_intelligence_service: Optional[FinancialIntelligenceService] = None,
        market_data_service: Optional[MarketDataService] = None,
        query_understanding_service: Optional[QueryUnderstandingService] = None,
        adaptive_router: Optional[AdaptiveRetrievalRouter] = None,
        cache: Optional[IntelligentResponseCache] = None,
        inflight: Optional[InFlightDeduplicator] = None,
        compressor: Optional[PromptCompressor] = None,
    ) -> None:
        self._db = db
        self._llm = llm_provider
        self._rag = rag_retriever
        self._safety = safety_validator
        self._builder = context_builder
        self._dash = dashboard_service
        self._conv = conversation_service
        self._intel = financial_intelligence_service
        self._market = market_data_service
        self._router = IntentRouter()
        self._understanding = query_understanding_service or QueryUnderstandingService()
        self._adaptive_router = adaptive_router or AdaptiveRetrievalRouter()
        self._budget_selector = TokenBudgetSelector()
        self._adaptive_budget_selector = AdaptiveTokenBudgetSelector()
        self._context_optimizer = LLMContextOptimizer()
        self._model_router = ModelRouter()
        self._cache = cache if cache is not None else get_response_cache()
        self._edu_cache = get_educational_cache()
        self._inflight = inflight if inflight is not None else get_inflight_deduplicator()
        self._compressor = compressor if compressor is not None else get_prompt_compressor()
        self._quality_evaluator = ResponseQualityEvaluator(safety_validator=self._safety)


    # ------------------------------------------------------------------
    # Legacy single-endpoint advisor (Phase 9 compatibility)
    # ------------------------------------------------------------------

    async def get_guidance(
        self, user_id: int, request: AIAdvisorRequest
    ) -> AIAdvisorResponse:
        """
        Produce personalized, safe financial guidance for the authenticated user.

        If conversation_service is available, creates/uses a real conversation.
        Otherwise operates in a stateless mode (legacy Phase 9 behaviour).
        """
        conv_id = request.conversation_id or str(uuid.uuid4())
        tracker = LatencyTracker()

        # Classify query intent using Phase L.1 - L.3 Query Understanding
        understanding = self._understanding.analyze(request.message, tracker=tracker)
        intent = understanding.intent

        # Financial context
        full_facts = self._dash.build_dashboard(user_id=user_id)

        # Phase L.6 Adaptive Retrieval Routing
        retrieved_docs = []
        retrieval_plan = self._adaptive_router.route(
            query_understanding=understanding,
            execution_plan=understanding.execution_plan,
            retrieval_query=understanding.retrieval_query,
            tracker=tracker,
        )

        # RAG retrieval (executed according to adaptive plan)
        if retrieval_plan.strategy != "NONE":
            try:
                retrieved_docs = await self._rag.retrieve(
                    query=understanding.retrieval_query,
                    retrieval_plan=retrieval_plan,
                    tracker=tracker,
                )
            except Exception:
                retrieved_docs = []

        # Financial intelligence
        financial_intelligence = None
        if self._intel is not None:
            try:
                financial_intelligence = self._intel.build_summary(user_id=user_id)
            except Exception:
                pass

        # Retrieve live market data
        live_market_data = await self._retrieve_live_market_data(request.message, user_id)

        # Build context (no history in stateless mode)
        ai_context = self._builder.build_context(
            question=request.message,
            full_context=full_facts,
            retrieved_docs=retrieved_docs,
            financial_intelligence=financial_intelligence,
            live_market_data=live_market_data,
            tracker=tracker,
        )
        _ep = understanding.execution_plan
        _scope_str = _ep.scope.value if _ep and _ep.scope else None
        _op_str = _ep.operation.value if _ep and _ep.operation else None
        _is_comparison = bool(_ep and _ep.comparison_info and _ep.comparison_info.is_comparison)
        _is_historical = bool(
            understanding.temporal_references and
            any(t.is_historical for t in understanding.temporal_references)
        )

        # Phase L.7.4 Adaptive LLM Inference Optimization
        inference_config = None
        if settings.ai_adaptive_inference_enabled:
            start_inf = time.perf_counter()
            inference_config = self._adaptive_budget_selector.select_config(
                query=request.message,
                intent=intent,
                execution_plan=_ep,
                sub_intent=understanding.sub_intent,
                personalization_level=getattr(_ep, "personalization_level", None),
                temporal_references=understanding.temporal_references,
            )
            if tracker:
                tracker.record("inference_config_ms", (time.perf_counter() - start_inf) * 1000.0)

            # Context Optimization & Trimming
            start_opt = time.perf_counter()
            retrieved_docs = self._context_optimizer.optimize_rag_docs(retrieved_docs, inference_config, intent=intent, is_comparison=_is_comparison)
            if tracker:
                tracker.record("context_optimization_ms", (time.perf_counter() - start_opt) * 1000.0)

            max_tokens_budget = inference_config.max_tokens
        else:
            max_tokens_budget = self._budget_selector.select(
                intent=intent,
                scope=_scope_str,
                operation=_op_str,
                is_comparison=_is_comparison,
                is_historical=_is_historical,
            )

        # Build context (no history in stateless mode)
        include_personal = True if not inference_config else self._context_optimizer.should_include_personal_context(intent, inference_config)
        ai_context = self._builder.build_context(
            question=request.message,
            full_context=full_facts if include_personal else None,
            retrieved_docs=retrieved_docs,
            financial_intelligence=financial_intelligence if include_personal else None,
            live_market_data=live_market_data,
            tracker=tracker,
        )

        prompt = self._builder.build_prompt(
            context=ai_context,
            tracker=tracker,
            intent=intent.value if intent else None,
            scope=_scope_str,
            config=inference_config,
        )

        if inference_config and tracker:
            est_p, est_o, est_t = self._context_optimizer.estimate_tokens(prompt, inference_config.max_tokens)
            inference_config.estimated_prompt_tokens = est_p
            inference_config.estimated_output_tokens = est_o
            inference_config.estimated_total_tokens = est_t

        with tracker.timer("model_selection_ms"):
            routing_decision = self._model_router.route(
                query=request.message,
                intent=intent,
                config=inference_config,
                execution_plan=understanding.execution_plan,
            )

        # Check cache eligibility
        is_cache_eligible = CacheEligibilityPolicy.is_eligible(
            query=request.message,
            intent=intent,
            scope=_scope_str,
            operation=_op_str,
            has_personal_context=bool(ai_context.user_financial_context and self._builder._has_any_financial_data(ai_context.user_financial_context)) or getattr(understanding, "requires_personal_data", False),
            has_live_market_data=bool(live_market_data) or getattr(understanding, "requires_market_data", False),
            requires_financial_engine=getattr(understanding, "requires_personal_data", False),
            requires_market_data=getattr(understanding, "requires_market_data", False),
            is_ambiguous=getattr(understanding, "is_ambiguous", False),
            is_adversarial=getattr(understanding, "is_adversarial", False),
        )

        cached_entry = None
        cache_key = ""
        if is_cache_eligible:
            cache_key = CacheKeyBuilder.build_key(
                query=understanding.retrieval_query or request.message,
                model_id=routing_decision.model,
                max_tokens_budget=max_tokens_budget,
                scope=_scope_str,
                operation=_op_str,
            )
            with tracker.timer("cache_lookup_ms"):
                cached_entry = self._cache.get(cache_key)

        if cached_entry is not None:
            tracker.record_flag("cache_hit", True)
            tracker.record_flag("llm_skipped_due_to_cache", True)
            tracker.record("cache_entry_age_ms", cached_entry.age_ms)
            tracker.finish()
            sources = [f"{doc.title} ({doc.source})" for doc in retrieved_docs] if retrieved_docs else []
            return AIAdvisorResponse(
                response=cached_entry.response_text,
                conversation_id=conv_id,
                sources=sources,
            )

        # CACHE MISS
        tracker.record_flag("cache_hit", False)

        # Phase L.9.7 — Intelligent Prompt Compression
        _is_comparison = (_op_str == "COMPARE") or bool(understanding and getattr(understanding, "is_comparison", False))
        if getattr(settings, "ai_prompt_compression_enabled", True):
            with tracker.timer("prompt_compression_ms"):
                comp_res = self._compressor.compress(
                    context=ai_context,
                    raw_prompt=prompt,
                    intent=intent,
                    complexity=inference_config.complexity if inference_config else InferenceComplexity.MODERATE,
                    scope=_scope_str,
                    is_comparison=_is_comparison,
                    is_personal=bool(ai_context.user_financial_context and self._builder._has_any_financial_data(ai_context.user_financial_context)),
                    requires_financial_engine=getattr(understanding, "requires_personal_data", False),
                    is_historical=bool(_scope_str and "HISTORICAL" in _scope_str.upper()),
                )
                prompt = comp_res.compressed_prompt
                if comp_res.compressed_context is not None:
                    ai_context = comp_res.compressed_context
                    retrieved_docs = ai_context.retrieved_knowledge
                tracker.record_count("prompt_tokens_before", comp_res.original_tokens)
                tracker.record_count("prompt_tokens_after", comp_res.compressed_tokens)
                tracker.record("prompt_compression_ratio", comp_res.compression_ratio)
                tracker.record_count("rag_chunks_before_compression", comp_res.rag_chunks_before)
                tracker.record_count("rag_chunks_after_compression", comp_res.rag_chunks_after)
                tracker.record_count("history_messages_before_compression", comp_res.history_messages_before)
                tracker.record_count("history_messages_after_compression", comp_res.history_messages_after)
                tracker.record_str("prompt_compression_mode", comp_res.compression_mode)

        # LLM call / Casual response
        msg_clean = request.message.strip().lower()
        if intent == QueryIntent.CASUAL:
            if msg_clean in {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings"}:
                raw_response = "Hey! 👋 I'm DhanSarthi. How can I help you with your finances today?"
            elif "how are you" in msg_clean:
                raw_response = "I'm doing great, thank you! Ready to help you with your financial questions and planning. How can I assist you today?"
            elif msg_clean in {"thanks", "thank you", "thanks a lot", "thx"}:
                raw_response = "You're very welcome! Let me know whenever you have more questions about your money or investments."
            elif any(phrase in msg_clean for phrase in ["what can you do", "what are your capabilities", "who are you", "how can you help"]):
                raw_response = "I am DhanSarthi, your AI Financial Advisor. I can help you with:\n1. Tracking your expenses, net worth, and cash flow.\n2. Explaining financial concepts like SIP, PPF, mutual funds, and inflation.\n3. Analyzing your savings rate and debt priorities.\n4. Planning your financial goals. How would you like to start?"
            else:
                raw_response = await self._call_llm_with_timeout(
                    ai_context, prompt, tracker=tracker, max_tokens=max_tokens_budget, config=inference_config, routing_decision=routing_decision
                )
        else:
            raw_response = await self._call_llm_with_timeout(
                ai_context, prompt, tracker=tracker, max_tokens=max_tokens_budget, config=inference_config, routing_decision=routing_decision
            )

        # Safety validation & Quality Evaluation with Controlled One-Retry
        _is_comp = bool(understanding.execution_plan and getattr(understanding.execution_plan, "comparison_info", None) and understanding.execution_plan.comparison_info.is_comparison)
        raw_response, quality_result, retry_used = await self._evaluate_and_retry_if_needed(
            raw_response=raw_response,
            query=request.message,
            ai_context=ai_context,
            prompt=prompt,
            retrieved_docs=retrieved_docs,
            intent=intent,
            is_comparison=_is_comp,
            tracker=tracker,
            max_tokens_budget=max_tokens_budget,
            inference_config=inference_config,
            routing_decision=routing_decision,
        )

        # Store in cache if eligible and passed
        if is_cache_eligible and cache_key and quality_result.overall_pass:
            with tracker.timer("cache_write_ms"):
                self._cache.put(
                    key=cache_key,
                    response_text=raw_response,
                    citations=[
                        {
                            "document_id": doc.document_id,
                            "title": doc.title,
                            "source": doc.source,
                            "source_url": doc.metadata.get("source_url"),
                        }
                        for doc in retrieved_docs[:10]
                    ],
                    quality={
                        "overall_score": round(quality_result.overall_score, 2),
                        "passed": quality_result.overall_pass,
                        "dimensions": quality_result.dimensions,
                    },
                    model_id=routing_decision.model,
                    prompt_tokens=tracker.breakdown.prompt_tokens or 0,
                    generated_tokens=tracker.breakdown.generated_tokens or 0,
                )

        tracker.finish()
        sources = [f"{doc.title} ({doc.source})" for doc in retrieved_docs] if retrieved_docs else []

        return AIAdvisorResponse(
            response=raw_response,
            conversation_id=conv_id,
            sources=sources,
        )

    # ------------------------------------------------------------------
    # Conversation-threaded chat endpoint (Phase 11)
    # ------------------------------------------------------------------

    async def send_chat_message(
        self,
        user_id: int,
        conversation_id: int,
        request: SendMessageRequest,
    ) -> SendMessageResponse:
        """
        Process a user message in a conversation thread.
        """
        if self._conv is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Conversation service is not configured.",
            )

        tracker = LatencyTracker()

        # 1. Verify ownership — raises 404/403 on failure
        conversation = self._conv.get_conversation(
            conversation_id=conversation_id, user_id=user_id
        )

        # 2. Store user message (commit before LLM call)
        with tracker.timer("persistence_ms"):
            user_msg = self._conv.store_user_message(
                conversation_id=conversation_id,
                content=request.message,
            )

        # Auto-generate title from first message
        self._conv.update_title_from_first_message(conversation, request.message)

        # 3. Financial context (always uses authenticated user_id)
        try:
            full_facts = self._dash.build_dashboard(user_id=user_id)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not retrieve financial context: {str(exc)}",
            )

        # 4. Recent conversation history (excluding current message we just stored)
        history_limit = settings.ai_max_history_messages
        recent_messages = self._conv.get_recent_messages(
            conversation_id=conversation_id, limit=history_limit + 1
        )
        # Exclude the just-stored user message (last one)
        history = [m for m in recent_messages if m.id != user_msg.id]

        # Analyze query using Query Understanding Layer
        understanding = self._understanding.analyze(request.message, history=history, tracker=tracker)
        intent = understanding.intent

        # Fast short-circuit if query is too ambiguous and requires clarification
        if understanding.execution_plan and understanding.execution_plan.clarification_required:
            clarification_text = understanding.execution_plan.clarification_prompt or "Could you please clarify your question?"
            response_time_ms = tracker.finish()
            assistant_metadata = {
                "provider": settings.ai_provider,
                "model": settings.ai_model,
                "response_time_ms": response_time_ms,
                "retrieval_count": 0,
                "intent": intent.value,
                "sub_intent": understanding.sub_intent.value,
                "scope": understanding.execution_plan.scope.value,
                "operation": understanding.execution_plan.operation.value,
                "clarification_required": True,
                "clarification_reason": understanding.execution_plan.clarification_reason,
                "corrected_query": understanding.corrected_query,
                "language": understanding.language,
                "correction_applied": understanding.correction_applied,
                "latency": tracker.to_dict(),
            }
            with tracker.timer("persistence_ms"):
                assistant_msg = self._conv.store_assistant_message(
                    conversation_id=conversation_id,
                    content=clarification_text,
                    metadata=assistant_metadata,
                )
            return SendMessageResponse(
                conversation_id=conversation_id,
                user_message=MessageResponse.model_validate(user_msg),
                assistant_message=MessageResponse.model_validate(assistant_msg),
            )

        # 5. Adaptive Retrieval Routing & Execution
        retrieved_docs = []
        retrieval_plan = self._adaptive_router.route(
            query_understanding=understanding,
            execution_plan=understanding.execution_plan,
            retrieval_query=understanding.retrieval_query,
            tracker=tracker,
        )
        if retrieval_plan.strategy != "NONE":
            try:
                retrieved_docs = await self._rag.retrieve(
                    query=understanding.retrieval_query,
                    retrieval_plan=retrieval_plan,
                    tracker=tracker,
                )
            except Exception:
                retrieved_docs = []  # RAG failure is non-fatal; proceed without knowledge

        # Financial intelligence
        financial_intelligence = None
        if self._intel is not None:
            try:
                financial_intelligence = self._intel.build_summary(user_id=user_id)
            except Exception:
                pass

        # Retrieve live market data
        live_market_data = await self._retrieve_live_market_data(request.message, user_id)

        # 6. Build AIContext with history (uses resolved_query for contextual clarity)
        ai_context = self._builder.build_context(
            question=understanding.resolved_query or request.message,
            full_context=full_facts,
            retrieved_docs=retrieved_docs,
            conversation_history=history,
            financial_intelligence=financial_intelligence,
            live_market_data=live_market_data,
            tracker=tracker,
        )
        # Determine execution plan metadata for budget + cache decisions
        _ep = understanding.execution_plan
        _scope_str = _ep.scope.value if _ep and _ep.scope else None
        _op_str = _ep.operation.value if _ep and _ep.operation else None
        _is_comparison = bool(_ep and _ep.comparison_info and _ep.comparison_info.is_comparison)
        _is_historical = bool(
            understanding.temporal_references and
            any(t.is_historical for t in understanding.temporal_references)
        )

        # Phase L.7.4 Adaptive LLM Inference Optimization
        inference_config = None
        if settings.ai_adaptive_inference_enabled:
            start_inf = time.perf_counter()
            inference_config = self._adaptive_budget_selector.select_config(
                query=request.message,
                intent=intent,
                execution_plan=_ep,
                sub_intent=understanding.sub_intent,
                personalization_level=getattr(_ep, "personalization_level", None),
                temporal_references=understanding.temporal_references,
            )
            if tracker:
                tracker.record("inference_config_ms", (time.perf_counter() - start_inf) * 1000.0)

            # Context Optimization & Trimming
            start_opt = time.perf_counter()
            history = self._context_optimizer.optimize_history(history, inference_config, intent=intent)
            retrieved_docs = self._context_optimizer.optimize_rag_docs(retrieved_docs, inference_config, intent=intent, is_comparison=_is_comparison)
            if tracker:
                tracker.record("context_optimization_ms", (time.perf_counter() - start_opt) * 1000.0)

            max_tokens_budget = inference_config.max_tokens
        else:
            max_tokens_budget = self._budget_selector.select(
                intent=intent,
                scope=_scope_str,
                operation=_op_str,
                is_comparison=_is_comparison,
                is_historical=_is_historical,
            )

        # 6. Build AIContext with optimized history & docs
        include_personal = True if not inference_config else self._context_optimizer.should_include_personal_context(intent, inference_config)
        ai_context = self._builder.build_context(
            question=understanding.resolved_query or request.message,
            full_context=full_facts if include_personal else None,
            retrieved_docs=retrieved_docs,
            conversation_history=history,
            financial_intelligence=financial_intelligence if include_personal else None,
            live_market_data=live_market_data,
            tracker=tracker,
        )

        prompt = self._builder.build_prompt(
            context=ai_context,
            tracker=tracker,
            intent=intent.value if intent else None,
            scope=_scope_str,
            config=inference_config,
        )

        if inference_config and tracker:
            est_p, est_o, est_t = self._context_optimizer.estimate_tokens(prompt, inference_config.max_tokens)
            inference_config.estimated_prompt_tokens = est_p
            inference_config.estimated_output_tokens = est_o
            inference_config.estimated_total_tokens = est_t

        with tracker.timer("model_selection_ms"):
            routing_decision = self._model_router.route(
                query=request.message,
                intent=intent,
                config=inference_config,
                execution_plan=_ep,
            )

        # 7. LLM call / Casual turn processing
        msg_clean = request.message.strip().lower()
        _has_personal = bool(ai_context.user_financial_context and self._builder._has_any_financial_data(ai_context.user_financial_context))
        _has_market = bool(live_market_data)

        # Check cache eligibility
        is_cache_eligible = CacheEligibilityPolicy.is_eligible(
            query=request.message,
            intent=intent,
            scope=_scope_str,
            operation=_op_str,
            has_personal_context=_has_personal or getattr(understanding, "requires_personal_data", False),
            has_live_market_data=_has_market or getattr(understanding, "requires_market_data", False),
            requires_financial_engine=getattr(understanding, "requires_personal_data", False),
            requires_market_data=getattr(understanding, "requires_market_data", False),
            is_ambiguous=getattr(understanding, "is_ambiguous", False),
            is_adversarial=getattr(understanding, "is_adversarial", False),
        )

        cached_entry = None
        cache_key = ""
        if is_cache_eligible:
            cache_key = CacheKeyBuilder.build_key(
                query=understanding.retrieval_query or request.message,
                model_id=routing_decision.model,
                max_tokens_budget=max_tokens_budget,
                scope=_scope_str,
                operation=_op_str,
            )
            with tracker.timer("cache_lookup_ms"):
                cached_entry = self._cache.get(cache_key)

        cache_meta = {"hit": False, "source": "llm_generation"}

        if cached_entry is not None:
            # CACHE HIT
            tracker.record_flag("cache_hit", True)
            tracker.record_flag("llm_skipped_due_to_cache", True)
            tracker.record("cache_entry_age_ms", cached_entry.age_ms)
            raw_response = cached_entry.response_text
            retry_used = False
            q_info = cached_entry.quality or {"overall_score": 1.0, "passed": True, "dimensions": {}}
            quality_result = ResponseQualityResult(
                overall_score=q_info.get("overall_score", 1.0),
                overall_pass=q_info.get("passed", True),
                failure_reasons=[],
                dimensions=q_info.get("dimensions", {}),
            )
            cache_meta = {"hit": True, "source": "response_cache", "age_ms": round(cached_entry.age_ms, 2)}
        else:
            # CACHE MISS (or ineligible)
            tracker.record_flag("cache_hit", False)

            # Phase L.9.7 — Intelligent Prompt Compression
            if getattr(settings, "ai_prompt_compression_enabled", True):
                with tracker.timer("prompt_compression_ms"):
                    comp_res = self._compressor.compress(
                        context=ai_context,
                        raw_prompt=prompt,
                        intent=intent,
                        complexity=inference_config.complexity if inference_config else InferenceComplexity.MODERATE,
                        scope=_scope_str,
                        is_comparison=_is_comparison,
                        is_personal=bool(ai_context.user_financial_context and self._builder._has_any_financial_data(ai_context.user_financial_context)),
                        requires_financial_engine=getattr(understanding, "requires_personal_data", False),
                        is_historical=bool(_scope_str and "HISTORICAL" in _scope_str.upper()),
                    )
                    prompt = comp_res.compressed_prompt
                    if comp_res.compressed_context is not None:
                        ai_context = comp_res.compressed_context
                        retrieved_docs = ai_context.retrieved_knowledge
                    tracker.record_count("prompt_tokens_before", comp_res.original_tokens)
                    tracker.record_count("prompt_tokens_after", comp_res.compressed_tokens)
                    tracker.record("prompt_compression_ratio", comp_res.compression_ratio)
                    tracker.record_count("rag_chunks_before_compression", comp_res.rag_chunks_before)
                    tracker.record_count("rag_chunks_after_compression", comp_res.rag_chunks_after)
                    tracker.record_count("history_messages_before_compression", comp_res.history_messages_before)
                    tracker.record_count("history_messages_after_compression", comp_res.history_messages_after)
                    tracker.record_str("prompt_compression_mode", comp_res.compression_mode)

            try:
                if intent == QueryIntent.CASUAL:
                    if msg_clean in {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings"}:
                        raw_response = "Hey! 👋 I'm DhanSarthi. How can I help you with your finances today?"
                    elif "how are you" in msg_clean:
                        raw_response = "I'm doing great, thank you! Ready to help you with your financial questions and planning. How can I assist you today?"
                    elif msg_clean in {"thanks", "thank you", "thanks a lot", "thx"}:
                        raw_response = "You're very welcome! Let me know whenever you have more questions about your money or investments."
                    elif any(phrase in msg_clean for phrase in ["what can you do", "what are your capabilities", "who are you", "how can you help"]):
                        raw_response = "I am DhanSarthi, your AI Financial Advisor. I can help you with:\n1. Tracking your expenses, net worth, and cash flow.\n2. Explaining financial concepts like SIP, PPF, mutual funds, and inflation.\n3. Analyzing your savings rate and debt priorities.\n4. Planning your financial goals. How would you like to start?"
                    else:
                        raw_response = await self._call_llm_with_timeout(
                            ai_context, prompt, tracker=tracker, max_tokens=max_tokens_budget, config=inference_config, routing_decision=routing_decision
                        )
                    raw_response, quality_result, retry_used = await self._evaluate_and_retry_if_needed(
                        raw_response=raw_response,
                        query=request.message,
                        ai_context=ai_context,
                        prompt=prompt,
                        retrieved_docs=retrieved_docs,
                        intent=intent,
                        is_comparison=_is_comparison,
                        tracker=tracker,
                        max_tokens_budget=max_tokens_budget,
                        inference_config=inference_config,
                        routing_decision=routing_decision,
                    )
                elif is_cache_eligible and cache_key:
                    # In-Flight Deduplication for eligible queries
                    async def _do_generate_and_eval():
                        resp_text = await self._call_llm_with_timeout(
                            ai_context, prompt, tracker=tracker, max_tokens=max_tokens_budget, config=inference_config, routing_decision=routing_decision
                        )
                        return await self._evaluate_and_retry_if_needed(
                            raw_response=resp_text,
                            query=request.message,
                            ai_context=ai_context,
                            prompt=prompt,
                            retrieved_docs=retrieved_docs,
                            intent=intent,
                            is_comparison=_is_comparison,
                            tracker=tracker,
                            max_tokens_budget=max_tokens_budget,
                            inference_config=inference_config,
                            routing_decision=routing_decision,
                        )

                    (raw_response, quality_result, retry_used), was_coalesced = await self._inflight.execute_or_join(
                        cache_key, _do_generate_and_eval
                    )
                    tracker.record_flag("inflight_deduplicated", was_coalesced)
                    if was_coalesced:
                        tracker.record_flag("llm_skipped_due_to_cache", True)
                else:
                    raw_response = await self._call_llm_with_timeout(
                        ai_context, prompt, tracker=tracker, max_tokens=max_tokens_budget, config=inference_config, routing_decision=routing_decision
                    )
                    raw_response, quality_result, retry_used = await self._evaluate_and_retry_if_needed(
                        raw_response=raw_response,
                        query=request.message,
                        ai_context=ai_context,
                        prompt=prompt,
                        retrieved_docs=retrieved_docs,
                        intent=intent,
                        is_comparison=_is_comparison,
                        tracker=tracker,
                        max_tokens_budget=max_tokens_budget,
                        inference_config=inference_config,
                        routing_decision=routing_decision,
                    )
            except AISafetyError as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"AI response failed safety validation: {str(exc)}",
                )

            # Store in cache only if eligible, passed quality, not fallback, not retry failure
            if is_cache_eligible and cache_key and quality_result.overall_pass and not getattr(quality_result, "is_fallback", False):
                with tracker.timer("cache_write_ms"):
                    self._cache.put(
                        key=cache_key,
                        response_text=raw_response,
                        citations=[
                            {
                                "document_id": doc.document_id,
                                "title": doc.title,
                                "source": doc.source,
                                "source_url": doc.metadata.get("source_url"),
                            }
                            for doc in retrieved_docs[:10]
                        ],
                        quality={
                            "overall_score": round(quality_result.overall_score, 2),
                            "passed": quality_result.overall_pass,
                            "dimensions": quality_result.dimensions,
                        },
                        model_id=routing_decision.model,
                        prompt_tokens=tracker.breakdown.prompt_tokens or 0,
                        generated_tokens=tracker.breakdown.generated_tokens or 0,
                    )

        # 9. Build citation sources from RAG documents
        citation_sources: List[CitationSource] = []
        source_ids: List[str] = []
        if intent in (QueryIntent.GENERAL_FINANCE, QueryIntent.MIXED):
            for doc in retrieved_docs:
                citation_sources.append(
                    CitationSource(
                        title=doc.title,
                        source=doc.source,
                        source_url=doc.metadata.get("source_url"),
                        document_id=doc.document_id,
                        relevance_score=doc.relevance_score,
                    )
                )
                source_ids.append(doc.document_id)

        # 10. Store assistant message with safe operational metadata
        citations_meta = [
            {
                "document_id": doc.document_id,
                "title": doc.title,
                "source": doc.source,
                "authority": doc.metadata.get("authority"),
                "effective_date": doc.metadata.get("effective_date"),
                "source_url": doc.metadata.get("source_url"),
            }
            for doc in retrieved_docs[:10]
        ]
        sub_intent = self._router.classify_sub_intent(request.message)

        # Extract signals, health score, and formulas from financial_intelligence
        signals_meta = []
        health_score_meta = None
        data_quality_meta = "LIMITED"
        if financial_intelligence:
            data_quality_meta = getattr(financial_intelligence, "data_quality", "LIMITED")
            if getattr(financial_intelligence, "signals", None):
                signals_meta = [
                    s.model_dump() if hasattr(s, "model_dump") else s
                    for s in financial_intelligence.signals
                ]
            if getattr(financial_intelligence, "health_snapshot", None):
                hs = financial_intelligence.health_snapshot
                if hasattr(hs, "health_score") and hs.health_score:
                    health_score_meta = hs.health_score.model_dump() if hasattr(hs.health_score, "model_dump") else hs.health_score

        response_time_ms = int(tracker.finish())

        assistant_metadata = {
            "provider": settings.ai_provider,
            "model": settings.ai_model,
            "response_time_ms": response_time_ms,
            "retrieval_count": len(retrieved_docs),
            "intent": intent.value,
            "sub_intent": sub_intent.value,
            "scope": understanding.execution_plan.scope.value if understanding.execution_plan else "EDUCATIONAL",
            "operation": understanding.execution_plan.operation.value if understanding.execution_plan else "EXPLAIN",
            "corrected_query": understanding.corrected_query,
            "language": understanding.language,
            "correction_applied": understanding.correction_applied,
            "data_completeness": data_quality_meta,
            "signals": signals_meta,
            "health_score": health_score_meta,
            "source_ids": source_ids[:10],  # store at most 10
            "citations": citations_meta,
            "quality": {
                "overall_score": round(quality_result.overall_score, 2),
                "passed": quality_result.overall_pass,
                "retry_used": retry_used,
                "failure_reasons": quality_result.failure_reasons,
                "dimensions": quality_result.dimensions,
            },
            "cache": cache_meta,
            "latency": tracker.to_dict(),
        }

        with tracker.timer("persistence_ms"):
            assistant_msg = self._conv.store_assistant_message(
                conversation_id=conversation_id,
                content=raw_response,
                metadata=assistant_metadata,
            )

        return SendMessageResponse(
            conversation_id=conversation_id,
            user_message=MessageResponse.model_validate(user_msg),
            assistant_message=MessageResponse.model_validate(assistant_msg),
            sources=citation_sources,
            response_time_ms=response_time_ms,
        )

    # ------------------------------------------------------------------
    # Phase L.7.3 — SSE streaming chat (AI_STREAMING_ENABLED=true path)
    # ------------------------------------------------------------------

    async def stream_chat_message(
        self,
        user_id: int,
        conversation_id: int,
        request: "SendMessageRequest",
        emit_sse: bool = False,
    ):
        """
        Process a user message and yield AI response chunks as an async generator.

        The streaming pipeline is identical to send_chat_message up to the LLM call.
        Instead of awaiting generate(), it calls generate_stream() and yields chunks.
        The COMPLETE assembled text is safety-validated before persistence, ensuring
        that partially-streamed content is never stored if it fails validation.

        Callers should:
          1. Yield each chunk to the SSE transport.
          2. Ignore persistence — this method handles it internally.

        Raises:
            HTTPException: On pipeline failures (finance context, RAG, safety).
            AISafetyError: If the assembled response fails SafetyValidator.
        """
        from typing import AsyncIterator as _AsyncIterator

        if self._conv is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Conversation service is not configured.",
            )

        tracker = LatencyTracker()
        tracker.record_flag("streaming_used", True)

        conversation = self._conv.get_conversation(
            conversation_id=conversation_id, user_id=user_id
        )

        with tracker.timer("persistence_ms"):
            user_msg = self._conv.store_user_message(
                conversation_id=conversation_id,
                content=request.message,
            )

        self._conv.update_title_from_first_message(conversation, request.message)

        try:
            full_facts = self._dash.build_dashboard(user_id=user_id)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not retrieve financial context: {str(exc)}",
            )

        history_limit = settings.ai_max_history_messages
        recent_messages = self._conv.get_recent_messages(
            conversation_id=conversation_id, limit=history_limit + 1
        )
        history = [m for m in recent_messages if m.id != user_msg.id]

        understanding = self._understanding.analyze(request.message, history=history, tracker=tracker)
        intent = understanding.intent

        retrieved_docs = []
        retrieval_plan = self._adaptive_router.route(
            query_understanding=understanding,
            execution_plan=understanding.execution_plan,
            retrieval_query=understanding.retrieval_query,
            tracker=tracker,
        )
        if retrieval_plan.strategy != "NONE":
            try:
                retrieved_docs = await self._rag.retrieve(
                    query=understanding.retrieval_query,
                    retrieval_plan=retrieval_plan,
                    tracker=tracker,
                )
            except Exception:
                retrieved_docs = []

        financial_intelligence = None
        if self._intel is not None:
            try:
                financial_intelligence = self._intel.build_summary(user_id=user_id)
            except Exception:
                pass

        live_market_data = await self._retrieve_live_market_data(request.message, user_id)

        ai_context = self._builder.build_context(
            question=understanding.resolved_query or request.message,
            full_context=full_facts,
            retrieved_docs=retrieved_docs,
            conversation_history=history,
            financial_intelligence=financial_intelligence,
            live_market_data=live_market_data,
            tracker=tracker,
        )

        _ep = understanding.execution_plan
        _scope_str = _ep.scope.value if _ep and _ep.scope else None
        _op_str = _ep.operation.value if _ep and _ep.operation else None
        _is_comparison = bool(_ep and _ep.comparison_info and _ep.comparison_info.is_comparison)
        _is_historical = bool(
            understanding.temporal_references and
            any(t.is_historical for t in understanding.temporal_references)
        )

        # Phase L.7.4 Adaptive LLM Inference Optimization
        inference_config = None
        if settings.ai_adaptive_inference_enabled:
            start_inf = time.perf_counter()
            inference_config = self._adaptive_budget_selector.select_config(
                query=request.message,
                intent=intent,
                execution_plan=_ep,
                sub_intent=understanding.sub_intent,
                personalization_level=getattr(_ep, "personalization_level", None),
                temporal_references=understanding.temporal_references,
            )
            if tracker:
                tracker.record("inference_config_ms", (time.perf_counter() - start_inf) * 1000.0)

            # Context Optimization & Trimming
            start_opt = time.perf_counter()
            history = self._context_optimizer.optimize_history(history, inference_config, intent=intent)
            retrieved_docs = self._context_optimizer.optimize_rag_docs(retrieved_docs, inference_config, intent=intent, is_comparison=_is_comparison)
            if tracker:
                tracker.record("context_optimization_ms", (time.perf_counter() - start_opt) * 1000.0)

            max_tokens_budget = inference_config.max_tokens
        else:
            max_tokens_budget = self._budget_selector.select(
                intent=intent,
                scope=_scope_str,
                operation=_op_str,
                is_comparison=_is_comparison,
                is_historical=_is_historical,
            )

        include_personal = True if not inference_config else self._context_optimizer.should_include_personal_context(intent, inference_config)
        ai_context = self._builder.build_context(
            question=understanding.resolved_query or request.message,
            full_context=full_facts if include_personal else None,
            retrieved_docs=retrieved_docs,
            conversation_history=history,
            financial_intelligence=financial_intelligence if include_personal else None,
            live_market_data=live_market_data,
            tracker=tracker,
        )

        prompt = self._builder.build_prompt(
            context=ai_context,
            tracker=tracker,
            intent=intent.value if intent else None,
            scope=_scope_str,
            config=inference_config,
        )

        with tracker.timer("model_selection_ms"):
            _ep = getattr(understanding, "execution_plan", None)
            routing_decision = self._model_router.route(
                query=request.message,
                intent=intent,
                config=inference_config,
                execution_plan=_ep,
            )

        # Build citations metadata early for emission
        citations_meta = [
            {
                "document_id": doc.document_id,
                "title": doc.title,
                "source": doc.source,
                "authority": doc.metadata.get("authority"),
                "effective_date": doc.metadata.get("effective_date"),
                "source_url": doc.metadata.get("source_url"),
            }
            for doc in retrieved_docs[:10]
        ]

        # Check cache eligibility
        is_cache_eligible = CacheEligibilityPolicy.is_eligible(
            query=request.message,
            intent=intent,
            scope=_scope_str,
            operation=_op_str,
            has_personal_context=bool(ai_context.user_financial_context and self._builder._has_any_financial_data(ai_context.user_financial_context)) or getattr(understanding, "requires_personal_data", False),
            has_live_market_data=bool(live_market_data) or getattr(understanding, "requires_market_data", False),
            requires_financial_engine=getattr(understanding, "requires_personal_data", False),
            requires_market_data=getattr(understanding, "requires_market_data", False),
            is_ambiguous=getattr(understanding, "is_ambiguous", False),
            is_adversarial=getattr(understanding, "is_adversarial", False),
        )

        cached_entry = None
        cache_key = ""
        if is_cache_eligible:
            cache_key = CacheKeyBuilder.build_key(
                query=understanding.retrieval_query or request.message,
                model_id=routing_decision.model,
                max_tokens_budget=max_tokens_budget,
                scope=_scope_str,
                operation=_op_str,
            )
            with tracker.timer("cache_lookup_ms"):
                cached_entry = self._cache.get(cache_key)

        if cached_entry is not None:
            # CACHE HIT: stream cached content cleanly
            tracker.record_flag("cache_hit", True)
            tracker.record_flag("llm_skipped_due_to_cache", True)
            tracker.record("cache_entry_age_ms", cached_entry.age_ms)
            raw_response = cached_entry.response_text

            if emit_sse:
                yield f"event: start\ndata: {json.dumps({'message_id': user_msg.id, 'conversation_id': conversation_id})}\n\n"
            
            # Stream words with slight delay for realistic visual rendering
            words = raw_response.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                if emit_sse:
                    yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"
                else:
                    yield chunk
                await asyncio.sleep(0.005)

            # Persist assistant message
            response_time_ms = int(tracker.finish())
            assistant_metadata = {
                "provider": settings.ai_provider,
                "model": settings.ai_model,
                "response_time_ms": response_time_ms,
                "retrieval_count": len(retrieved_docs),
                "intent": intent.value,
                "sub_intent": self._router.classify_sub_intent(request.message).value,
                "streaming": True,
                "cache": {"hit": True, "source": "response_cache", "age_ms": round(cached_entry.age_ms, 2)},
                "quality": cached_entry.quality or {"overall_score": 1.0, "passed": True, "dimensions": {}},
                "latency": tracker.to_dict(),
            }
            with tracker.timer("persistence_ms"):
                asst_msg = self._conv.store_assistant_message(
                    conversation_id=conversation_id,
                    content=raw_response,
                    metadata=assistant_metadata,
                )

            if emit_sse:
                yield f"event: metadata\ndata: {json.dumps({'citations': citations_meta, 'quality': cached_entry.quality or {'overall_score': 1.0, 'passed': True, 'dimensions': {}}, 'latency': tracker.to_dict(), 'selected_model': routing_decision.model, 'tokens_per_second': 150.0})}\n\n"
                yield f"event: complete\ndata: {json.dumps({'message_id': asst_msg.id, 'status': 'completed'})}\n\n"
            return

        # CACHE MISS
        tracker.record_flag("cache_hit", False)

        # Phase L.9.7 — Intelligent Prompt Compression
        if getattr(settings, "ai_prompt_compression_enabled", True):
            with tracker.timer("prompt_compression_ms"):
                comp_res = self._compressor.compress(
                    context=ai_context,
                    raw_prompt=prompt,
                    intent=intent,
                    complexity=inference_config.complexity if inference_config else InferenceComplexity.MODERATE,
                    scope=_scope_str,
                    is_comparison=_is_comparison,
                    is_personal=bool(ai_context.user_financial_context and self._builder._has_any_financial_data(ai_context.user_financial_context)),
                    requires_financial_engine=getattr(understanding, "requires_personal_data", False),
                    is_historical=bool(_scope_str and "HISTORICAL" in _scope_str.upper()),
                )
                prompt = comp_res.compressed_prompt
                if comp_res.compressed_context is not None:
                    ai_context = comp_res.compressed_context
                    retrieved_docs = ai_context.retrieved_knowledge
                tracker.record_count("prompt_tokens_before", comp_res.original_tokens)
                tracker.record_count("prompt_tokens_after", comp_res.compressed_tokens)
                tracker.record("prompt_compression_ratio", comp_res.compression_ratio)
                tracker.record_count("rag_chunks_before_compression", comp_res.rag_chunks_before)
                tracker.record_count("rag_chunks_after_compression", comp_res.rag_chunks_after)
                tracker.record_count("history_messages_before_compression", comp_res.history_messages_before)
                tracker.record_count("history_messages_after_compression", comp_res.history_messages_after)
                tracker.record_str("prompt_compression_mode", comp_res.compression_mode)

        if emit_sse:
            yield f"event: start\ndata: {json.dumps({'message_id': user_msg.id, 'conversation_id': conversation_id})}\n\n"

        # --- Stream generation ---
        assembled_parts: List[str] = []
        tokens_streamed = False
        try:
            async for chunk in self._llm.generate_stream(
                context=ai_context,
                prompt=prompt,
                tracker=tracker,
                max_tokens=max_tokens_budget,
                config=inference_config,
                routing_decision=routing_decision,
            ):
                tokens_streamed = True
                assembled_parts.append(chunk)
                if emit_sse:
                    yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"
                else:
                    yield chunk

        except asyncio.CancelledError:
            # Client cancelled or disconnected -> Clean exit, NEVER persist partial content
            logger.debug("Stream generation cancelled by client or task.")
            raise
        except HTTPException:
            raise
        except Exception as exc:
            if emit_sse:
                code = "STREAM_INTERRUPTED" if tokens_streamed else "PROVIDER_ERROR"
                yield f"event: error\ndata: {json.dumps({'code': code, 'message': str(exc)})}\n\n"
            if not tokens_streamed:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"AI provider stream error: {str(exc)}",
                )
            return

        raw_response = "".join(assembled_parts) if assembled_parts else "I apologize, but no response was generated. Please try again."

        # --- Safety & Quality validation + Single Hidden Retry ---
        try:
            raw_response, quality_result, retry_used = await self._evaluate_and_retry_if_needed(
                raw_response=raw_response,
                query=request.message,
                ai_context=ai_context,
                prompt=prompt,
                retrieved_docs=retrieved_docs,
                intent=intent,
                is_comparison=_is_comparison,
                tracker=tracker,
                max_tokens_budget=max_tokens_budget,
                inference_config=inference_config,
                routing_decision=routing_decision,
            )
        except AISafetyError as exc:
            if emit_sse:
                yield f"event: error\ndata: {json.dumps({'code': 'SAFETY_ERROR', 'message': str(exc)})}\n\n"
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"AI stream response failed safety validation: {str(exc)}",
            )

        # Store in cache if eligible and passed
        if is_cache_eligible and cache_key and quality_result.overall_pass and not getattr(quality_result, "is_fallback", False):
            with tracker.timer("cache_write_ms"):
                self._cache.put(
                    key=cache_key,
                    response_text=raw_response,
                    citations=[
                        {
                            "document_id": doc.document_id,
                            "title": doc.title,
                            "source": doc.source,
                            "source_url": doc.metadata.get("source_url"),
                        }
                        for doc in retrieved_docs[:10]
                    ],
                    quality={
                        "overall_score": round(quality_result.overall_score, 2),
                        "passed": quality_result.overall_pass,
                        "dimensions": quality_result.dimensions,
                    },
                    model_id=routing_decision.model,
                    prompt_tokens=tracker.breakdown.prompt_tokens or 0,
                    generated_tokens=tracker.breakdown.generated_tokens or 0,
                )

        # --- Persist final accepted assistant message ---
        sub_intent = self._router.classify_sub_intent(request.message)
        response_time_ms = int(tracker.finish())
        assistant_metadata = {
            "provider": settings.ai_provider,
            "model": settings.ai_model,
            "response_time_ms": response_time_ms,
            "retrieval_count": len(retrieved_docs),
            "intent": intent.value,
            "sub_intent": sub_intent.value,
            "streaming": True,
            "cache": {"hit": False, "source": "llm_generation"},
            "quality": {
                "overall_score": round(quality_result.overall_score, 2),
                "passed": quality_result.overall_pass,
                "retry_used": retry_used,
                "failure_reasons": quality_result.failure_reasons,
                "dimensions": quality_result.dimensions,
            },
            "latency": tracker.to_dict(),
        }
        with tracker.timer("persistence_ms"):
            asst_msg = self._conv.store_assistant_message(
                conversation_id=conversation_id,
                content=raw_response,
                metadata=assistant_metadata,
            )

        if emit_sse:
            yield f"event: metadata\ndata: {json.dumps({'citations': citations_meta, 'quality': {'overall_score': round(quality_result.overall_score, 2), 'passed': quality_result.overall_pass, 'retry_used': retry_used, 'dimensions': quality_result.dimensions}, 'latency': tracker.to_dict(), 'selected_model': routing_decision.model, 'tokens_per_second': tracker.breakdown.tokens_per_second or 0.0})}\n\n"
            yield f"event: complete\ndata: {json.dumps({'message_id': asst_msg.id, 'status': 'completed'})}\n\n"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _call_llm_with_timeout(
        self,
        ai_context,
        prompt: str,
        tracker: Optional[LatencyTracker] = None,
        max_tokens: Optional[int] = None,
        config: Optional[Any] = None,
        routing_decision: Optional[Any] = None,
    ) -> str:
        """Call LLM provider with configured timeout, per-intent token budget, and model candidate.

        Args:
            ai_context: Structured AIContext container.
            prompt: Final assembled prompt string.
            tracker: Optional LatencyTracker for observability.
            max_tokens: Per-request token budget from TokenBudgetSelector.
            config: Optional InferenceConfig for adaptive optimization.
            routing_decision: Optional ModelRoutingDecision for model candidate selection.
        """
        timeout = settings.ai_request_timeout_seconds
        try:
            res = await asyncio.wait_for(
                self._llm.generate(
                    context=ai_context,
                    prompt=prompt,
                    tracker=tracker,
                    max_tokens=max_tokens,
                    config=config,
                    routing_decision=routing_decision,
                ),
                timeout=timeout,
            )
            if tracker:
                tps = tracker.get_inference_tokens_per_second()
                if tps > 0:
                    tracker.record("tokens_per_second", tps)
            return res

        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=(
                    f"AI provider did not respond within {timeout} seconds. "
                    "Please try again later."
                ),
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI provider error: {str(exc)}",
            )

    async def _retrieve_live_market_data(
        self, question: str, user_id: int
    ) -> Optional[dict]:
        if self._market is None:
            return None

        live_data = {}
        q = question.lower()

        # 1. Check if user is asking about portfolio value
        if any(kw in q for kw in ["portfolio worth", "portfolio value", "my investments worth", "my holdings worth"]):
            try:
                est = await self._market.calculate_estimated_portfolio(user_id, self._db)
                live_data["portfolio_estimation"] = est
            except Exception:
                pass

        # 2. Extract FX rates (e.g. USD to INR, EUR/INR)
        fx_matches = re.findall(r"\b([A-Za-z]{3})\s*(?:to|/|in)\s*([A-Za-z]{3})\b", question)
        if fx_matches:
            rates = []
            for base, quote in fx_matches[:2]:  # Limit to 2 pairs
                try:
                    r = await self._market.get_exchange_rate(base, quote)
                    rates.append(r.model_dump())
                except Exception:
                    pass
            if rates:
                live_data["exchange_rates"] = rates

        # 3. Extract mutual fund scheme IDs (5 to 8 digit numbers)
        mf_matches = re.findall(r"\b([0-9]{5,8})\b", question)
        if mf_matches:
            funds = []
            for scheme_id in mf_matches[:3]:
                try:
                    nav = await self._market.get_mutual_fund_nav(scheme_id)
                    funds.append(nav.model_dump())
                except Exception:
                    pass
            if funds:
                live_data["mutual_funds"] = funds

        # 4. Extract stock symbols (uppercase, e.g. RELIANCE.NS, TCS, MSFT)
        # Exclude common abbreviations
        exclude_set = {"USD", "INR", "EUR", "RAG", "SIP", "NAV", "DTI", "FD", "RD", "EMI", "AI", "BSE", "NSE", "GDP"}
        stock_matches = re.findall(r"\b([A-Z]{2,10}(?:\.[A-Z]{2})?)\b", question)
        stocks = []
        for sym in stock_matches:
            if sym not in exclude_set and len(stocks) < 3:
                try:
                    quote = await self._market.get_stock_quote(sym)
                    stocks.append(quote.model_dump())
                except Exception:
                    pass
        if stocks:
            live_data["stocks"] = stocks

        # 5. Extract indices
        indices = []
        if "nifty" in q:
            try:
                idx = await self._market.get_market_index("NIFTY_50")
                indices.append(idx.model_dump())
            except Exception:
                pass
        if "sensex" in q:
            try:
                idx = await self._market.get_market_index("SENSEX")
                indices.append(idx.model_dump())
            except Exception:
                pass
        if indices:
            live_data["indices"] = indices

        # 6. Extract interest rates
        rates = []
        if "repo rate" in q:
            try:
                rate = await self._market.get_interest_rate("IN", "Repo Rate")
                rates.append(rate.model_dump())
            except Exception:
                pass
        if "savings rate" in q:
            try:
                rate = await self._market.get_interest_rate("IN", "Savings Deposit Rate")
                rates.append(rate.model_dump())
            except Exception:
                pass
        if rates:
            live_data["interest_rates"] = rates

        return live_data if live_data else None

    def _extract_expected_financial_facts(self, ai_context) -> Dict[str, Any]:
        """Extract ground truth financial numbers from validated context for accuracy evaluation."""
        facts: Dict[str, Any] = {}
        if not ai_context or not getattr(ai_context, "user_financial_context", None):
            return facts
        ufc = ai_context.user_financial_context
        for k in ["monthly_income", "monthly_expenses", "savings_rate", "net_worth", "total_debt", "total_investments", "emergency_fund"]:
            if hasattr(ufc, k) and getattr(ufc, k) is not None:
                try:
                    facts[k] = float(getattr(ufc, k))
                except (ValueError, TypeError):
                    pass
        return facts

    async def _evaluate_and_retry_if_needed(
        self,
        raw_response: str,
        query: str,
        ai_context,
        prompt: str,
        retrieved_docs: List[Any],
        intent: QueryIntent,
        is_comparison: bool,
        tracker: LatencyTracker,
        max_tokens_budget: int,
        inference_config: Optional[Any] = None,
        routing_decision: Optional[Any] = None,
    ) -> tuple[str, ResponseQualityResult, bool]:
        """
        Validates initial response quality; executes EXACTLY ONE controlled retry if quality fails.
        Returns: (final_response, final_quality_result, retry_used)
        """
        # 1. Safety validation on initial response (Safety is a hard gate)
        self._safety.validate_response(response=raw_response, context=ai_context, tracker=tracker)

        requires_rag = bool(retrieved_docs and intent in (QueryIntent.GENERAL_FINANCE, QueryIntent.MIXED))
        requires_personalization = bool(
            getattr(ai_context, "user_financial_context", None)
            and self._builder._has_any_financial_data(ai_context.user_financial_context)
            and intent in (QueryIntent.PERSONAL_FINANCE, QueryIntent.MIXED)
        )
        expected_facts = self._extract_expected_financial_facts(ai_context)

        # 2. Evaluate initial response quality
        with tracker.timer("quality_evaluation_ms"):
            quality_result = self._quality_evaluator.evaluate(
                query=query,
                response_text=raw_response,
                ai_context=ai_context,
                retrieved_docs=retrieved_docs,
                expected_financial_facts=expected_facts,
                requires_rag=requires_rag,
                requires_personalization=requires_personalization,
                is_comparison=is_comparison,
            )

        tracker.record("quality_overall_score", quality_result.overall_score)
        tracker.record_flag("quality_passed", quality_result.overall_pass)

        if quality_result.overall_pass:
            tracker.record_flag("quality_retry_used", False)
            return raw_response, quality_result, False

        # 3. Controlled One-Retry (MAX_QUALITY_RETRIES = 1)
        tracker.record_flag("quality_retry_used", True)
        retry_start = time.perf_counter()

        retry_prompt = prompt
        if quality_result.retry_guidance:
            retry_prompt += f"\n\n[CRITICAL CORRECTION INSTRUCTION]:\n{quality_result.retry_guidance}"

        try:
            retry_budget = min(max_tokens_budget + 256, settings.ai_max_tokens)
            retry_budget = min(retry_budget, settings.ai_max_tokens_global_safety_max)
            retry_response = await self._call_llm_with_timeout(
                ai_context,
                retry_prompt,
                tracker=tracker,
                max_tokens=retry_budget,
                config=inference_config,
                routing_decision=routing_decision,
            )
            tracker.record("quality_retry_ms", (time.perf_counter() - retry_start) * 1000.0)

            # Validate safety on retry response
            self._safety.validate_response(response=retry_response, context=ai_context, tracker=tracker)

            # Re-evaluate quality on retry response
            with tracker.timer("quality_evaluation_ms"):
                retry_quality_result = self._quality_evaluator.evaluate(
                    query=query,
                    response_text=retry_response,
                    ai_context=ai_context,
                    retrieved_docs=retrieved_docs,
                    expected_financial_facts=expected_facts,
                    requires_rag=requires_rag,
                    requires_personalization=requires_personalization,
                    is_comparison=is_comparison,
                )

            tracker.record("quality_overall_score", retry_quality_result.overall_score)
            tracker.record_flag("quality_passed", retry_quality_result.overall_pass)

            if retry_quality_result.overall_pass:
                return retry_response, retry_quality_result, True

        except Exception:
            pass

        # 4. Safe Deterministic Fallback if initial and retry both fail
        if requires_personalization:
            fallback_text = (
                "I want to make sure I give you accurate guidance. I couldn't confidently validate the response "
                "against your verified financial data. Please ask your question again or check your account dashboard."
            )
        else:
            fallback_text = (
                "I want to make sure I give you a properly grounded answer. I couldn't confidently validate the response "
                "against authoritative financial sources. Please try asking the question another way."
            )

        fallback_result = ResponseQualityResult(
            overall_pass=True,
            overall_score=0.80,
            completeness_score=0.80,
            relevance_score=0.80,
            grounding_score=1.0,
            citation_score=1.0,
            personal_accuracy_score=1.0,
            safety_score=1.0,
            failure_reasons=["SAFE_FALLBACK_APPLIED: Initial and retry response failed quality validation."],
            dimensions={"completeness": 0.8, "relevance": 0.8, "grounding": 1.0, "citation": 1.0, "personal_accuracy": 1.0, "safety": 1.0},
        )
        return fallback_text, fallback_result, True
