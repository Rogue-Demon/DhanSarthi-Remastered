"""
Safety validator tests — Phase 11.

Covers:
  - Empty response rejection
  - Secret/credential pattern detection
  - System prompt leakage detection
  - Autonomous action claim detection
  - Unsafe guarantee detection
  - Valid responses pass all checks
"""

from __future__ import annotations

import pytest
from app.ai.exceptions import AISafetyError
from app.ai.safety.validator import SimpleSafetyValidator
from app.ai.schemas.advisor import AIContext


def _make_context(question: str = "What is SIP?") -> AIContext:
    return AIContext(question=question)


class TestSimpleSafetyValidator:
    def test_valid_response_passes(self):
        v = SimpleSafetyValidator()
        v.validate_response(
            "SIP is a Systematic Investment Plan that allows you to invest regularly.",
            _make_context(),
        )

    def test_empty_response_raises(self):
        v = SimpleSafetyValidator()
        with pytest.raises(AISafetyError) as exc:
            v.validate_response("", _make_context())
        assert "empty" in str(exc.value).lower()

    def test_whitespace_only_raises(self):
        v = SimpleSafetyValidator()
        with pytest.raises(AISafetyError):
            v.validate_response("   \n\t  ", _make_context())

    def test_jwt_token_leak_raises(self):
        v = SimpleSafetyValidator()
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        with pytest.raises(AISafetyError) as exc:
            v.validate_response(f"Your token: {fake_jwt}", _make_context())
        assert "token" in str(exc.value).lower() or "api" in str(exc.value).lower()

    def test_api_key_assignment_leak_raises(self):
        v = SimpleSafetyValidator()
        with pytest.raises(AISafetyError):
            v.validate_response("Use api_key: sk-abc123xyz", _make_context())

    def test_system_prompt_leakage_raises(self):
        v = SimpleSafetyValidator()
        with pytest.raises(AISafetyError) as exc:
            v.validate_response(
                "System Instructions: You are DhanSarthi, a personalized advisor.",
                _make_context(),
            )
        assert "system" in str(exc.value).lower() or "instruction" in str(exc.value).lower()

    def test_autonomous_transfer_claim_raises(self):
        v = SimpleSafetyValidator()
        with pytest.raises(AISafetyError):
            v.validate_response(
                "I have transferred ₹50,000 from your account on your behalf.",
                _make_context(),
            )

    def test_autonomous_buy_claim_raises(self):
        v = SimpleSafetyValidator()
        with pytest.raises(AISafetyError):
            v.validate_response(
                "I have bought 100 shares of TCS on your behalf.",
                _make_context(),
            )

    def test_unsafe_return_guarantee_raises(self):
        v = SimpleSafetyValidator()
        with pytest.raises(AISafetyError):
            v.validate_response(
                "I guarantee this investment will give you a 20% return.",
                _make_context(),
            )

    def test_unsafe_loan_approval_guarantee_raises(self):
        v = SimpleSafetyValidator()
        with pytest.raises(AISafetyError):
            v.validate_response(
                "I guarantee your loan approval from the bank.",
                _make_context(),
            )

    def test_general_advice_with_disclaimer_passes(self):
        v = SimpleSafetyValidator()
        # Safe response: no secrets, no leakage, no guarantees
        response = (
            "Based on your income of ₹1,00,000/month, you have a savings rate of 30%. "
            "This is a healthy savings rate. Consider increasing your SIP contribution "
            "by ₹5,000 per month. Please consult a financial advisor before making decisions."
        )
        v.validate_response(response, _make_context("What is my savings rate?"))

    def test_execute_transfer_action_raises(self):
        v = SimpleSafetyValidator()
        with pytest.raises(AISafetyError):
            v.validate_response(
                "To help you, I will execute transfer of funds to your investment account.",
                _make_context(),
            )
