"""
Unit tests for IntentRouter classification logic.
"""

import pytest
from app.ai.router import IntentRouter, QueryIntent


def test_casual_intent_classification():
    router = IntentRouter()

    casual_queries = [
        "Hi",
        "Hello",
        "Good morning",
        "How are you?",
        "Thanks",
        "Thank you",
        "What can you do?",
        "Who are you?",
    ]

    for q in casual_queries:
        assert router.classify(q) == QueryIntent.CASUAL, f"Failed for query: {q}"


def test_general_finance_intent_classification():
    router = IntentRouter()

    general_queries = [
        "What is an SIP?",
        "What is PPF?",
        "Explain compound interest",
        "What is an emergency fund?",
        "What is a mutual fund?",
        "What is inflation?",
        "How does a fixed deposit work?",
    ]

    for q in general_queries:
        assert router.classify(q) == QueryIntent.GENERAL_FINANCE, f"Failed for query: {q}"


def test_personal_finance_intent_classification():
    router = IntentRouter()

    personal_queries = [
        "How much did I spend this month?",
        "What is my net worth?",
        "How much debt do I have?",
        "How much can I save?",
        "What are my biggest expenses?",
    ]

    for q in personal_queries:
        assert router.classify(q) == QueryIntent.PERSONAL_FINANCE, f"Failed for query: {q}"


def test_mixed_intent_classification():
    router = IntentRouter()

    mixed_queries = [
        "Is my savings rate healthy?",
        "What should I do about my debt?",
        "Should I increase my SIP based on my finances?",
        "My spending is increasing. What should I do?",
    ]

    for q in mixed_queries:
        assert router.classify(q) == QueryIntent.MIXED, f"Failed for query: {q}"
