import asyncio
import json
import sys
from decimal import Decimal
from datetime import date

# Ensure stdout handles UTF-8 (Rupee symbol etc.)
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
from app.models.user import User
from app.models.profile import Profile
from app.models.income import Income
from app.models.expense import Expense
from app.models.enums import Persona, RiskProfile, IncomeFrequency


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, (date,)):
            return o.isoformat()
        return super().default(o)


async def main():
    db = SessionLocal()
    try:
        # Seed test user 999
        user = db.get(User, 999)
        if not user:
            user = User(id=999, email="smoke_test_999@dhansarthi.local", password_hash="hash")
            db.add(user)
            db.flush()

        profile = db.query(Profile).filter_by(user_id=999).first()
        if not profile:
            profile = Profile(
                user_id=999,
                display_name="Smoke Test User",
                persona=Persona.PROFESSIONAL,
                country="IN",
                currency="INR",
                risk_profile=RiskProfile.MODERATE,
            )
            db.add(profile)
            db.flush()

        # Add income and expense data for personal finance / savings rate tests
        inc_count = db.query(Income).filter_by(user_id=999).count()
        if inc_count == 0:
            db.add(Income(
                user_id=999,
                source="Monthly Salary",
                amount=Decimal("100000"),
                income_date=date.today(),
                category="SALARY",
                frequency=IncomeFrequency.MONTHLY,
            ))
            db.flush()

        exp_count = db.query(Expense).filter_by(user_id=999).count()
        if exp_count == 0:
            db.add(Expense(
                user_id=999,
                description="Rent & Groceries",
                amount=Decimal("40000"),
                expense_date=date.today(),
                category="RENT",
            ))
            db.flush()

        db.commit()

        # Instantiate live services
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

        print(f"Active Provider Class: {llm.__class__.__name__}")

        # Create fresh conversation
        conv = conv_svc.create_conversation(user_id=999, title="Live Smoke Test Thread")
        conv_id = conv.id
        print(f"Created Conversation ID: {conv_id}")

        queries = [
            ("Test 1 — What is SIP?", "What is SIP?"),
            ("Test 2 — What is a Mutual Fund?", "What is a mutual fund?"),
            ("Test 3 — How much did I spend this month?", "How much did I spend this month?"),
            ("Test 4 — Is my savings rate healthy?", "Is my savings rate healthy?"),
        ]

        results = []
        for label, q_text in queries:
            print(f"\n--- Running {label} ---")
            req = SendMessageRequest(message=q_text)
            try:
                res = await advisor_svc.send_chat_message(user_id=999, conversation_id=conv_id, request=req)
                ans = res.assistant_message.content
                sources_str = ", ".join([f"{s.title} ({s.source})" for s in res.sources]) if res.sources else "None"
                meta_sources = res.assistant_message.message_metadata.get("source_ids", [])
                print(f"Response ({len(ans)} chars):\n{ans}")
                print(f"Sources ({len(res.sources)}): {sources_str}")
                print(f"Metadata Source IDs: {meta_sources}")
                results.append({
                    "label": label,
                    "query": q_text,
                    "response": ans,
                    "sources": [s.model_dump(mode="json") for s in res.sources],
                    "metadata": json.loads(json.dumps(res.assistant_message.message_metadata, default=str)),
                    "status": "PASS",
                })
            except Exception as e:
                print(f"Error: {e}")
                results.append({
                    "label": label,
                    "query": q_text,
                    "error": str(e),
                    "status": "FAIL",
                })

        with open("scratch/live_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, cls=DecimalEncoder)

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
