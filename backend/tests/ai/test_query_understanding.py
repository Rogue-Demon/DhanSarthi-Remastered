"""
Unit Test Suite for DhanSarthi Query Understanding Layer (Phase L.1).

Tests:
  A. Normal queries
  B. Typo & spelling correction
  C. Hinglish & mixed-language understanding
  D. Financial abbreviation recognition
  E. Conversation-aware pronoun & reference resolution
  F. Personal finance queries & data flags
  G. Mixed advice queries & intent routing
  H. Temporal expression recognition
  I. Ambiguous queries (handling low confidence without hallucinating)
"""

from __future__ import annotations

import pytest
from app.ai.query_understanding.service import QueryUnderstandingService
from app.ai.router import QueryIntent, SubIntent
from app.models.conversation import ConversationMessage, MessageRole


@pytest.fixture
def service():
    return QueryUnderstandingService()


# ---------------------------------------------------------------------------
# A. Normal Queries
# ---------------------------------------------------------------------------


def test_normal_queries(service):
    res1 = service.analyze("What is SIP?")
    assert res1.intent == QueryIntent.GENERAL_FINANCE
    assert res1.requires_rag is True
    assert "Systematic Investment Plan" in res1.financial_terms or "SIP" in res1.retrieval_query

    res2 = service.analyze("What is a mutual fund?")
    assert res2.intent == QueryIntent.GENERAL_FINANCE
    assert res2.requires_rag is True
    assert "Mutual Funds" in res2.financial_terms or "mutual fund" in res2.corrected_query.lower()

    res3 = service.analyze("How does PPF work?")
    assert res3.intent == QueryIntent.GENERAL_FINANCE
    assert "Public Provident Fund" in res3.financial_terms or "ppf" in res3.corrected_query.lower()


# ---------------------------------------------------------------------------
# B. Financial Typo & Spelling Correction
# ---------------------------------------------------------------------------


def test_typos(service):
    res1 = service.analyze("What is mutal fund?")
    assert res1.correction_applied is True
    assert "mutual fund" in res1.corrected_query.lower()

    res2 = service.analyze("how does sip wrk?")
    assert res2.correction_applied is True
    assert "work" in res2.corrected_query.lower()

    res3 = service.analyze("what is invesment?")
    assert res3.correction_applied is True
    assert "investment" in res3.corrected_query.lower()

    res4 = service.analyze("what is retirment expence?")
    assert res4.correction_applied is True
    assert "retirement" in res4.corrected_query.lower()
    assert "expense" in res4.corrected_query.lower()


# ---------------------------------------------------------------------------
# C. Hinglish & Mixed-Language Understanding
# ---------------------------------------------------------------------------


def test_hinglish(service):
    res1 = service.analyze("SIP kya hota hai?")
    assert res1.detected_language_mix is True
    assert res1.language == "hi-Latn"
    assert "What is SIP?" in res1.corrected_query or "SIP" in res1.retrieval_query

    res2 = service.analyze("FD safe hai kya?")
    assert res2.detected_language_mix is True
    assert "fixed deposit" in res2.corrected_query.lower() or "fd" in res2.corrected_query.lower()

    res3 = service.analyze("mera savings rate kaisa hai?")
    assert res3.detected_language_mix is True
    assert res3.requires_personal_data is True
    assert res3.intent in (QueryIntent.PERSONAL_FINANCE, QueryIntent.MIXED)


# ---------------------------------------------------------------------------
# D. Financial Abbreviation Recognition
# ---------------------------------------------------------------------------


def test_abbreviations(service):
    res1 = service.analyze("what is MF?")
    assert any(e.value == "Mutual Funds" for e in res1.entities)

    res2 = service.analyze("what is FD?")
    assert any(e.value == "Fixed Deposit" for e in res2.entities)

    res3 = service.analyze("what is NAV?")
    assert any(e.value == "Net Asset Value" for e in res3.entities) or "NAV" in res3.financial_terms

    res4 = service.analyze("what is NPS?")
    assert any(e.value == "National Pension System" for e in res4.entities)


# ---------------------------------------------------------------------------
# E. Conversation Context & Reference Resolution
# ---------------------------------------------------------------------------


def test_conversation_reference_resolution(service):
    # Simulated dialogue history
    history = [
        ConversationMessage(id=1, conversation_id=10, role=MessageRole.USER, content="What is SIP?"),
        ConversationMessage(
            id=2,
            conversation_id=10,
            role=MessageRole.ASSISTANT,
            content="SIP stands for Systematic Investment Plan, a periodic investment facility in mutual funds.",
        ),
    ]

    res = service.analyze("Is it risky?", history=history)
    assert res.conversation_reference is not None
    assert res.conversation_reference.pronoun == "it"
    assert "SIP" in res.conversation_reference.resolved_target or "Systematic Investment Plan" in res.conversation_reference.resolved_target
    assert "Systematic Investment Plan" in res.resolved_query or "SIP" in res.resolved_query


# ---------------------------------------------------------------------------
# F. Personal Queries & Data Flags
# ---------------------------------------------------------------------------


def test_personal_queries(service):
    res1 = service.analyze("How much did I spend this month?")
    assert res1.intent == QueryIntent.PERSONAL_FINANCE
    assert res1.requires_personal_data is True
    assert res1.requires_rag is False

    res2 = service.analyze("Am I saving enough?")
    assert res2.requires_personal_data is True

    res3 = service.analyze("Where am I overspending?")
    assert res3.intent == QueryIntent.PERSONAL_FINANCE
    assert res3.sub_intent == SubIntent.SPENDING_ANALYSIS


# ---------------------------------------------------------------------------
# G. Mixed Queries & Advice Routing
# ---------------------------------------------------------------------------


def test_mixed_queries(service):
    res1 = service.analyze("Is my savings rate healthy?")
    assert res1.intent == QueryIntent.MIXED
    assert res1.requires_personal_data is True
    assert res1.requires_rag is True

    res2 = service.analyze("Should I focus on debt or investing?")
    assert res2.intent == QueryIntent.MIXED
    assert res2.requires_personal_data is True


# ---------------------------------------------------------------------------
# H. Temporal Expression Recognition
# ---------------------------------------------------------------------------


def test_temporal_queries(service):
    res1 = service.analyze("What did I spend last month?")
    assert len(res1.temporal_references) > 0
    assert any(t.expression == "last month" for t in res1.temporal_references)

    res2 = service.analyze("What was my income in FY 2025-26?")
    assert len(res2.temporal_references) > 0
    assert any(t.is_historical is True for t in res2.temporal_references)


# ---------------------------------------------------------------------------
# I. Ambiguous Queries Without History
# ---------------------------------------------------------------------------


def test_ambiguous_queries_no_history(service):
    res = service.analyze("What is it?")
    # Without history, reference confidence must be 0.0 or None, no hallucinated target
    if res.conversation_reference:
        assert res.conversation_reference.confidence == 0.0
        assert res.conversation_reference.resolved_target == "UNKNOWN"
