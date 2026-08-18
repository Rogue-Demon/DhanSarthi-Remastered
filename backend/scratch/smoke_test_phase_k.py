"""
Phase K Live End-to-End Smoke Test Script.
Runs the 6 required personalized intelligence queries against Hugging Face LLM.
"""

import asyncio
import json
import sys
from decimal import Decimal

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


class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return str(o)


async def main():
    db = SessionLocal()
    llm = get_llm_provider()
    emb = get_embedding_provider()

    print(f"Active Provider Class: {llm.__class__.__name__}")

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

    conv = conv_svc.create_conversation(user_id=999, title="Phase K Live Benchmark Thread")
    print(f"Created Conversation ID: {conv.id}")

    queries = [
        ("Query 1", "How am I doing financially?"),
        ("Query 2", "Am I saving enough?"),
        ("Query 3", "Where am I overspending?"),
        ("Query 4", "Should I focus on debt or investing?"),
        ("Query 5", "Can I afford my goal?"),
        ("Query 6", "Is my savings rate healthy?"),
    ]

    results = []

    for label, text in queries:
        print(f"\n==========================================")
        print(f"Running {label}: '{text}'")
        print(f"==========================================")

        req = SendMessageRequest(message=text)
        try:
            res = await advisor_svc.send_chat_message(
                user_id=999, conversation_id=conv.id, request=req
            )
            ans = res.assistant_message.content
            meta = res.assistant_message.message_metadata

            intent = meta.get("intent")
            sub_intent = meta.get("sub_intent")
            signals = meta.get("signals", [])
            health_score = meta.get("health_score")
            data_comp = meta.get("data_completeness")
            citations = meta.get("citations", [])

            print(f"Intent: {intent} | Sub-Intent: {sub_intent}")
            print(f"Data Completeness: {data_comp}")
            print(f"Health Score: {health_score}")
            print(f"Signals Triggered ({len(signals)}): {[s.get('title') for s in signals]}")
            print(f"Citations ({len(citations)}): {[c.get('title') for c in citations]}")
            print(f"Response ({len(ans)} chars):\n{ans[:400]}...\n")

            results.append({
                "label": label,
                "query": text,
                "intent": intent,
                "sub_intent": sub_intent,
                "data_completeness": data_comp,
                "signals_count": len(signals),
                "citations_count": len(citations),
                "response_snippet": ans[:300],
                "status": "PASS",
            })
        except Exception as e:
            print(f"ERROR on {label}: {e}")
            results.append({
                "label": label,
                "query": text,
                "error": str(e),
                "status": "FAIL",
            })

    with open("scratch/phase_k_live_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, cls=CustomEncoder)

    print("\nLive Smoke Test Summary saved to scratch/phase_k_live_results.json")


if __name__ == "__main__":
    asyncio.run(main())
