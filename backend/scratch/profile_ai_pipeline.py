"""
Phase K.1 Baseline Performance Profiling Script.
Measures latency breakdown across each stage of the AI pipeline.
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any

sys.stdout.reconfigure(encoding='utf-8')

from app.core.database import SessionLocal
from app.api.deps import get_llm_provider, get_embedding_provider
from app.services.conversation_service import ConversationService
from app.services.dashboard_service import DashboardService
from app.services.financial_intelligence_service import FinancialIntelligenceService
from app.market_data.service import MarketDataService
from app.ai.advisor.service import AIAdvisorService
from app.ai.context.builder import AIContextBuilder
from app.ai.rag.retriever import PostgresRAGRetriever
from app.ai.safety.validator import SimpleSafetyValidator
from app.ai.schemas.advisor import SendMessageRequest
from app.ai.router import IntentRouter, QueryIntent


async def profile_single_query(advisor_svc: AIAdvisorService, conv_id: int, query_text: str, user_id: int = 999) -> Dict[str, Any]:
    t_start = time.perf_counter()
    timings = {}

    # Stage 1: Ownership & User Message Persistence
    t0 = time.perf_counter()
    conv = advisor_svc._conv.get_conversation(conversation_id=conv_id, user_id=user_id)
    user_msg = advisor_svc._conv.store_user_message(conversation_id=conv_id, content=query_text)
    advisor_svc._conv.update_title_from_first_message(conv, query_text)
    timings["1_user_msg_persistence_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Stage 2: Intent Classification
    t0 = time.perf_counter()
    intent = advisor_svc._router.classify(query_text)
    sub_intent = advisor_svc._router.classify_sub_intent(query_text)
    timings["2_intent_classification_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Stage 3: Financial Context Construction
    t0 = time.perf_counter()
    full_facts = advisor_svc._dash.build_dashboard(user_id=user_id)
    timings["3_financial_context_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Stage 4: Conversation History Retrieval
    t0 = time.perf_counter()
    history_limit = 20
    recent_messages = advisor_svc._conv.get_recent_messages(conversation_id=conv_id, limit=history_limit + 1)
    history = [m for m in recent_messages if m.id != user_msg.id]
    timings["4_history_retrieval_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Stage 5: RAG Retrieval (with detailed inner breakdown)
    t0 = time.perf_counter()
    retrieved_docs = []
    if intent in (QueryIntent.GENERAL_FINANCE, QueryIntent.MIXED):
        try:
            # Measure embedding vs DB vs rerank inside RAG
            t_embed_start = time.perf_counter()
            orig_query, norm_query, expanded_terms, is_hist, target_yr = advisor_svc._rag._query_processor.process(query_text)
            query_vector = await advisor_svc._rag._embedding_provider.embed(norm_query or query_text)
            t_embed_end = time.perf_counter()
            timings["5a_rag_embedding_ms"] = round((t_embed_end - t_embed_start) * 1000, 2)

            t_vector_start = time.perf_counter()
            matches = advisor_svc._rag._chunk_repo.search_similarity(query_embedding=query_vector, limit=20, threshold=0.15)
            t_vector_end = time.perf_counter()
            timings["5b_rag_vector_search_ms"] = round((t_vector_end - t_vector_start) * 1000, 2)

            t_rerank_start = time.perf_counter()
            retrieved_docs = advisor_svc._rag._reranker.rerank_and_filter(
                matches=matches,
                query_terms=expanded_terms,
                threshold=advisor_svc._rag.similarity_threshold,
                top_k=advisor_svc._rag.top_k,
            )
            t_rerank_end = time.perf_counter()
            timings["5c_rag_rerank_ms"] = round((t_rerank_end - t_rerank_start) * 1000, 2)
        except Exception as e:
            print(f"RAG Error: {e}")
            retrieved_docs = []
    timings["5_rag_retrieval_total_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Stage 6: Financial Intelligence & Snapshot
    t0 = time.perf_counter()
    financial_intelligence = None
    if advisor_svc._intel is not None:
        try:
            financial_intelligence = advisor_svc._intel.build_summary(user_id=user_id)
        except Exception:
            pass
    timings["6_financial_intelligence_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Stage 7: Live Market Data
    t0 = time.perf_counter()
    live_market_data = await advisor_svc._retrieve_live_market_data(query_text, user_id)
    timings["7_live_market_data_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Stage 8: Context Building & Prompt Construction
    t0 = time.perf_counter()
    ai_context = advisor_svc._builder.build_context(
        question=query_text,
        full_context=full_facts,
        retrieved_docs=retrieved_docs,
        conversation_history=history,
        financial_intelligence=financial_intelligence,
        live_market_data=live_market_data,
    )
    prompt = advisor_svc._builder.build_prompt(context=ai_context)
    timings["8_prompt_construction_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    timings["8_prompt_length_chars"] = len(prompt)

    # Stage 9: LLM Generation Call
    t0 = time.perf_counter()
    if intent == QueryIntent.CASUAL:
        msg_clean = query_text.strip().lower()
        if msg_clean in {"hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings"}:
            raw_response = "Hey! 👋 I'm DhanSarthi. How can I help you with your finances today?"
        else:
            raw_response = await advisor_svc._call_llm_with_timeout(ai_context, prompt)
    else:
        raw_response = await advisor_svc._call_llm_with_timeout(ai_context, prompt)
    timings["9_llm_generation_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    timings["9_response_length_chars"] = len(raw_response)

    # Stage 10: Safety Validation
    t0 = time.perf_counter()
    advisor_svc._safety.validate_response(response=raw_response, context=ai_context)
    timings["10_safety_validation_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # Stage 11: Assistant Persistence
    t0 = time.perf_counter()
    assistant_metadata = {
        "provider": "huggingface",
        "intent": intent.value,
        "sub_intent": sub_intent.value,
    }
    advisor_svc._conv.store_assistant_message(
        conversation_id=conv_id, content=raw_response, metadata=assistant_metadata
    )
    timings["11_assistant_persistence_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    timings["total_backend_ms"] = round((time.perf_counter() - t_start) * 1000, 2)
    timings["intent"] = intent.value
    timings["sub_intent"] = sub_intent.value
    timings["rag_docs_count"] = len(retrieved_docs)

    return timings


async def main():
    db = SessionLocal()
    llm = get_llm_provider()
    emb = get_embedding_provider()

    rag = PostgresRAGRetriever(db=db, embedding_provider=emb)
    safety = SimpleSafetyValidator()
    builder = AIContextBuilder()
    dash = DashboardService(db)
    conv_svc = ConversationService(db)
    intel_svc = FinancialIntelligenceService(db)
    market_svc = MarketDataService()

    advisor_svc = AIAdvisorService(
        db=db,
        llm_provider=llm,
        rag_retriever=rag,
        safety_validator=safety,
        context_builder=builder,
        dashboard_service=dash,
        conversation_service=conv_svc,
        financial_intelligence_service=intel_svc,
        market_data_service=market_svc,
    )

    conv = conv_svc.create_conversation(user_id=999, title="Baseline Profiling Thread")

    benchmark_queries = [
        ("1. Greeting", "Hi"),
        ("2. General Finance", "What is SIP?"),
        ("3. General Finance", "What is a mutual fund?"),
        ("4. Personal Finance", "How much did I spend this month?"),
        ("5. Personal Health", "How am I doing financially?"),
        ("6. Spending Analysis", "Where am I overspending?"),
        ("7. Debt Analysis", "Should I focus on debt or investing?"),
        ("8. Savings Rate", "Is my savings rate healthy?"),
    ]

    profile_results = {}

    for label, q_text in benchmark_queries:
        print(f"Profiling: {label} - '{q_text}'...")
        res = await profile_single_query(advisor_svc, conv.id, q_text, user_id=999)
        profile_results[label] = res
        print(f"  --> Total: {res['total_backend_ms']} ms | LLM: {res['9_llm_generation_ms']} ms | Financial Ctx: {res['3_financial_context_ms']} ms | RAG: {res['5_rag_retrieval_total_ms']} ms")

    with open("scratch/baseline_profile_results.json", "w", encoding="utf-8") as f:
        json.dump(profile_results, f, indent=2)

    print("\nBaseline Profile Results saved to scratch/baseline_profile_results.json")


if __name__ == "__main__":
    asyncio.run(main())
