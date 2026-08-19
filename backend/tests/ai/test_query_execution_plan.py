"""
Unit Test Suite for DhanSarthi Phase L.2 — Intent, Entity & Scope Intelligence.

Tests:
  1. Educational query routing
  2. Personal lookup queries
  3. Personal analysis queries
  4. Investment analysis queries
  5. Planning queries
  6. Comparison detection & dimensions
  7. Mixed query routing
  8. Market data query routing
  9. Ambiguous queries & clarification detection
 10. Personalization level detection
 11. Deterministic data source selection
 12. Entity roles assignment
 13. Conversational context resolution & execution planning
 14. Transactional request detection & safety
 15. Classification performance latency (sub-5ms)
 16. Regression against Phase L.1 Query Understanding Layer
"""

from __future__ import annotations

import time
import pytest

from app.ai.query_understanding.service import QueryUnderstandingService
from app.ai.router import QueryIntent, SubIntent
from app.ai.schemas.query_execution_plan import (
    EntityRole,
    OperationType,
    PersonalizationLevel,
    QueryScope,
)
from app.models.conversation import ConversationMessage, MessageRole


@pytest.fixture
def service():
    return QueryUnderstandingService()


# ---------------------------------------------------------------------------
# 1. Educational Query Routing
# ---------------------------------------------------------------------------


def test_educational_routing(service):
    res1 = service.analyze("What is SIP?")
    plan1 = res1.execution_plan
    assert plan1 is not None
    assert plan1.scope == QueryScope.EDUCATIONAL
    assert plan1.operation in (OperationType.DEFINE, OperationType.EXPLAIN)
    assert plan1.requires_rag is True
    assert plan1.requires_financial_engine is False
    assert plan1.requires_market_data is False
    assert plan1.personalization_level == PersonalizationLevel.NONE

    res2 = service.analyze("What is PPF?")
    assert res2.execution_plan.scope == QueryScope.EDUCATIONAL
    assert res2.execution_plan.requires_rag is True

    res3 = service.analyze("How does NPS work?")
    assert res3.execution_plan.scope == QueryScope.EDUCATIONAL
    assert res3.execution_plan.operation in (OperationType.EXPLAIN, OperationType.DEFINE)


# ---------------------------------------------------------------------------
# 2. Personal Lookup Queries
# ---------------------------------------------------------------------------


def test_personal_lookup_routing(service):
    res1 = service.analyze("How much did I spend this month?")
    plan1 = res1.execution_plan
    assert plan1 is not None
    assert plan1.scope == QueryScope.PERSONAL_LOOKUP
    assert plan1.operation == OperationType.LOOKUP
    assert plan1.requires_financial_engine is True
    assert plan1.requires_rag is False
    assert plan1.personalization_level == PersonalizationLevel.HIGH

    res2 = service.analyze("How much do I have in savings?")
    assert res2.execution_plan.scope == QueryScope.PERSONAL_LOOKUP
    assert res2.execution_plan.requires_financial_engine is True

    res3 = service.analyze("What is my net worth?")
    assert res3.execution_plan.scope == QueryScope.PERSONAL_LOOKUP
    assert res3.execution_plan.requires_financial_engine is True


# ---------------------------------------------------------------------------
# 3. Personal Analysis Queries
# ---------------------------------------------------------------------------


def test_personal_analysis_routing(service):
    res1 = service.analyze("Why am I overspending?")
    plan1 = res1.execution_plan
    assert plan1 is not None
    assert plan1.scope == QueryScope.PERSONAL_ANALYSIS
    assert plan1.operation == OperationType.ANALYZE
    assert plan1.requires_financial_engine is True

    res2 = service.analyze("Is my savings rate healthy?")
    plan2 = res2.execution_plan
    assert plan2.requires_financial_engine is True
    assert plan2.requires_rag is True
    assert plan2.personalization_level == PersonalizationLevel.HIGH


# ---------------------------------------------------------------------------
# 4. Investment Analysis Queries
# ---------------------------------------------------------------------------


def test_investment_analysis_routing(service):
    res1 = service.analyze("How is my portfolio performing?")
    plan1 = res1.execution_plan
    assert plan1 is not None
    assert plan1.requires_financial_engine is True
    assert plan1.personalization_level == PersonalizationLevel.HIGH

    res2 = service.analyze("How concentrated is my portfolio?")
    assert res2.execution_plan.requires_financial_engine is True


# ---------------------------------------------------------------------------
# 5. Planning Queries
# ---------------------------------------------------------------------------


def test_planning_routing(service):
    res1 = service.analyze("How should I build an emergency fund?")
    plan1 = res1.execution_plan
    assert plan1 is not None
    assert plan1.scope == QueryScope.PLANNING
    assert plan1.operation == OperationType.PLAN
    assert plan1.requires_rag is True

    res2 = service.analyze("How much should I save for retirement?")
    assert res2.execution_plan.scope == QueryScope.PLANNING


# ---------------------------------------------------------------------------
# 6. Comparison Detection & Dimensions
# ---------------------------------------------------------------------------


def test_comparison_detection(service):
    res1 = service.analyze("SIP vs FD")
    plan1 = res1.execution_plan
    assert plan1 is not None
    assert plan1.scope == QueryScope.COMPARISON
    assert plan1.operation == OperationType.COMPARE
    assert plan1.comparison_info.is_comparison is True
    assert len(plan1.comparison_info.comparison_items) >= 2
    assert plan1.personalization_level == PersonalizationLevel.LOW

    res2 = service.analyze("PPF vs NPS")
    assert res2.execution_plan.comparison_info.is_comparison is True

    res3 = service.analyze("Should I invest in SIP or repay my loan?")
    plan3 = res3.execution_plan
    assert plan3.comparison_info.is_comparison is True
    assert plan3.comparison_info.comparison_dimension == "financial_decision"
    assert plan3.comparison_info.personalization_required is True


# ---------------------------------------------------------------------------
# 7. Mixed Queries
# ---------------------------------------------------------------------------


def test_mixed_query_routing(service):
    res = service.analyze("Is my savings rate healthy and how can I improve it?")
    plan = res.execution_plan
    assert plan is not None
    assert plan.requires_rag is True
    assert plan.requires_financial_engine is True
    assert plan.personalization_level == PersonalizationLevel.HIGH


# ---------------------------------------------------------------------------
# 8. Market Data Queries
# ---------------------------------------------------------------------------


def test_market_data_routing(service):
    res1 = service.analyze("What is the current gold price?")
    plan1 = res1.execution_plan
    assert plan1 is not None
    assert plan1.scope == QueryScope.MARKET_INFORMATION
    assert plan1.requires_market_data is True
    assert plan1.requires_rag is False
    assert plan1.requires_financial_engine is False

    res2 = service.analyze("How is NIFTY performing today?")
    assert res2.execution_plan.requires_market_data is True


# ---------------------------------------------------------------------------
# 9. Ambiguous Queries & Clarification Detection
# ---------------------------------------------------------------------------


def test_ambiguous_queries_clarification(service):
    res1 = service.analyze("Should I invest?")
    plan1 = res1.execution_plan
    assert plan1 is not None
    assert plan1.clarification_required is True
    assert plan1.scope == QueryScope.AMBIGUOUS
    assert plan1.clarification_prompt is not None
    assert "stocks, mutual funds" in plan1.clarification_prompt
    # Important safety rule: data fetching blocked when clarification needed
    assert plan1.requires_rag is False
    assert plan1.requires_financial_engine is False

    res2 = service.analyze("What is it?")
    assert res2.execution_plan.clarification_required is True
    assert res2.execution_plan.scope == QueryScope.AMBIGUOUS

    res3 = service.analyze("How much?")
    assert res3.execution_plan.clarification_required is True


# ---------------------------------------------------------------------------
# 10. Personalization Level Detection
# ---------------------------------------------------------------------------


def test_personalization_levels(service):
    res1 = service.analyze("What is SIP?")
    assert res1.execution_plan.personalization_level == PersonalizationLevel.NONE

    res2 = service.analyze("Is SIP good?")
    assert res2.execution_plan.personalization_level == PersonalizationLevel.LOW

    res3 = service.analyze("Is SIP good for me?")
    assert res3.execution_plan.personalization_level == PersonalizationLevel.HIGH

    res4 = service.analyze("How much did I invest in SIP?")
    assert res4.execution_plan.personalization_level == PersonalizationLevel.HIGH


# ---------------------------------------------------------------------------
# 11. Deterministic Source Selection
# ---------------------------------------------------------------------------


def test_source_selection_determinism(service):
    # Educational query
    r1 = service.analyze("What is SIP?")
    assert r1.execution_plan.requires_rag is True
    assert r1.execution_plan.requires_financial_engine is False
    assert r1.execution_plan.requires_market_data is False

    # Personal lookup
    r2 = service.analyze("How much did I invest in SIP?")
    assert r2.execution_plan.requires_financial_engine is True

    # Market query
    r3 = service.analyze("What is NIFTY today?")
    assert r3.execution_plan.requires_market_data is True
    assert r3.execution_plan.requires_rag is False


# ---------------------------------------------------------------------------
# 12. Entity Roles Assignment
# ---------------------------------------------------------------------------


def test_entity_roles(service):
    res1 = service.analyze("What is SIP?")
    assert res1.execution_plan.entity_roles.get("Systematic Investment Plan") == EntityRole.SUBJECT or res1.execution_plan.entity_roles.get("SIP") == EntityRole.SUBJECT

    res2 = service.analyze("How much did I invest in SIP?")
    assert res2.execution_plan.entity_roles.get("Systematic Investment Plan") == EntityRole.FILTER or res2.execution_plan.entity_roles.get("SIP") == EntityRole.FILTER

    res3 = service.analyze("SIP vs FD")
    plan3 = res3.execution_plan
    roles3 = list(plan3.entity_roles.values())
    assert EntityRole.COMPARISON_LEFT in roles3 or EntityRole.COMPARISON_RIGHT in roles3


# ---------------------------------------------------------------------------
# 13. Conversational Context Resolution & Execution Planning
# ---------------------------------------------------------------------------


def test_conversational_context(service):
    history = [
        ConversationMessage(id=1, conversation_id=10, role=MessageRole.USER, content="What is SIP?"),
        ConversationMessage(
            id=2,
            conversation_id=10,
            role=MessageRole.ASSISTANT,
            content="SIP stands for Systematic Investment Plan, a periodic investment facility in mutual funds.",
        ),
    ]

    res = service.analyze("Is it safe?", history=history)
    plan = res.execution_plan
    assert plan is not None
    assert plan.clarification_required is False
    assert plan.requires_conversation_context is True
    assert plan.requires_rag is True


# ---------------------------------------------------------------------------
# 14. Transactional Request Safety
# ---------------------------------------------------------------------------


def test_transactional_safety(service):
    res = service.analyze("Buy this stock for me")
    plan = res.execution_plan
    assert plan is not None
    assert plan.scope == QueryScope.TRANSACTIONAL
    assert plan.operation == OperationType.ACTION_REQUEST


# ---------------------------------------------------------------------------
# 15. Performance Latency (Millisecond level)
# ---------------------------------------------------------------------------


def test_performance_latency(service):
    start = time.monotonic()
    for _ in range(100):
        service.analyze("What is SIP?")
        service.analyze("How much did I spend this month?")
        service.analyze("SIP vs FD")
    elapsed_ms = (time.monotonic() - start) * 1000
    avg_ms = elapsed_ms / 300
    # Average classification time per query must be under 2ms
    assert avg_ms < 2.0


# ---------------------------------------------------------------------------
# 16. Regression Test Against Phase L.1
# ---------------------------------------------------------------------------


def test_phase_l1_regression(service):
    res = service.analyze("What is mutal fund?")
    assert res.correction_applied is True
    assert "mutual fund" in res.corrected_query.lower()

    res_h = service.analyze("SIP kya hota hai?")
    assert res_h.detected_language_mix is True
    assert res_h.language == "hi-Latn"
