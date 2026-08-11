"""
Tests for document value normalization (currencies, dates, Decimal amounts).
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from app.documents.normalizer import FinancialDocumentNormalizer
from app.documents.financial_extractor import ExtractedField, TransactionCandidate, FinancialExtractionResult
from app.models.enums import DocumentType


class TestDocumentNormalization:
    def test_amount_normalization(self):
        norm = FinancialDocumentNormalizer()
        
        # Test Decimal parsing from float/int/str
        assert norm.normalize_amount(45000) == Decimal("45000")
        assert norm.normalize_amount(1250.75) == Decimal("1250.75")
        assert norm.normalize_amount("Rs. 85,000.50") == Decimal("85000.50")
        assert norm.normalize_amount("₹1,20,000.00") == Decimal("120000")
        assert norm.normalize_amount("unknown") == Decimal("0.00")

    def test_currency_normalization(self):
        norm = FinancialDocumentNormalizer()
        
        assert norm.normalize_currency("₹") == "INR"
        assert norm.normalize_currency("rs") == "INR"
        assert norm.normalize_currency("inr") == "INR"
        assert norm.normalize_currency("$") == "USD"
        assert norm.normalize_currency("usd") == "USD"
        assert norm.normalize_currency("EUR") == "EUR"
        assert norm.normalize_currency(None) == "INR"

    def test_date_normalization(self):
        norm = FinancialDocumentNormalizer()
        
        expected = datetime.date(2026, 8, 12)
        
        # Standard format
        assert norm.normalize_date("12/08/2026") == expected
        # Hyphens/dots
        assert norm.normalize_date("12-08-2026") == expected
        assert norm.normalize_date("12.08.2026") == expected
        # ISO format
        assert norm.normalize_date("2026-08-12") == expected
        # Ambiguous MM/DD/YYYY check (12/08/2026 default to 12th Aug)
        assert norm.normalize_date("08/12/2026") == expected  # Disambiguates to DD/MM/YYYY when reasonable
        # Date objects directly
        assert norm.normalize_date(expected) == expected

    def test_extraction_result_normalization_in_place(self):
        norm = FinancialDocumentNormalizer()
        
        res = FinancialExtractionResult(
            document_type=DocumentType.BANK_STATEMENT,
            fields=[
                ExtractedField(name="period_start", value="12-08-2026", confidence=1.0, source_page=1, source_text_ref=""),
                ExtractedField(name="net_salary", value="₹85,000.00", confidence=1.0, source_page=1, source_text_ref=""),
            ],
            transactions=[
                TransactionCandidate(
                    date="13/08/2026",
                    description="ATM Withdrawal",
                    debit="₹2,000.00",
                    credit=None,
                    balance="₹13,000.00",
                    currency="rs"
                )
            ]
        )

        norm.normalize(res)

        # Verify fields normalized
        assert res.fields[0].value == datetime.date(2026, 8, 12)
        assert res.fields[1].value == Decimal("85000.00")

        # Verify transactions normalized
        tx = res.transactions[0]
        assert tx.date == "2026-08-13"
        assert tx.debit == "2000.00"
        assert tx.balance == "13000.00"
        assert tx.currency == "INR"
