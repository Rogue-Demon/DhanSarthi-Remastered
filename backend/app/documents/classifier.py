"""
Rule-based Document Classifier for DhanSarthi.

Determines the likely DocumentType of a document based on text keywords/signals
and returns classification confidence.
"""

from __future__ import annotations

from typing import List
from pydantic import BaseModel
from app.models.enums import DocumentType
from app.core.config import settings


class ClassificationResult(BaseModel):
    """Structure returned by the document classifier."""

    document_type: DocumentType
    confidence: float
    signals: List[str]


class DocumentClassifier:
    """Classifies raw text using keyword frequency and weights."""

    def __init__(self) -> None:
        # Define keyword sets with weights
        self._rules = {
            DocumentType.BANK_STATEMENT: {
                "keywords": [
                    "account number", "statement of account", "transaction date",
                    "debit", "credit", "opening balance", "closing balance",
                    "withdrawal", "deposit", "cheque", "ledger balance", "rtgs", "neft"
                ],
                "weight": 1.0
            },
            DocumentType.SALARY_SLIP: {
                "keywords": [
                    "payslip", "pay slip", "salary slip", "basic salary", "basic pay",
                    "provident fund", "epf", "net pay", "gross earnings", "deductions",
                    "allowance", "house rent allowance", "hra", "lta", "gratuity"
                ],
                "weight": 1.0
            },
            DocumentType.LOAN_STATEMENT: {
                "keywords": [
                    "loan account", "outstanding principal", "emi", "tenure",
                    "rate of interest", "principal amount", "outstanding balance",
                    "disbursement", "interest rate", "repayment schedule", "lender", "foreclosure"
                ],
                "weight": 1.0
            },
            DocumentType.INVESTMENT_STATEMENT: {
                "keywords": [
                    "folio number", "mutual fund", "nav", "portfolio value",
                    "transaction units", "sip", "dividend", "mutual fund statement",
                    "demat", "holding statement", "units balance", "scheme name", "isin"
                ],
                "weight": 1.0
            },
            DocumentType.TAX_DOCUMENT: {
                "keywords": [
                    "form 16", "income tax", "section 80c", "tax deduction", "tds",
                    "assessment year", "pan card", "itr", "tax return", "financial year",
                    "form 26as", "taxable income"
                ],
                "weight": 1.0
            },
            DocumentType.BILL: {
                "keywords": [
                    "invoice", "bill number", "utility bill", "due date", "amount due",
                    "total payable", "billing period", "consumer number", "gstin", "invoice date"
                ],
                "weight": 1.0
            }
        }

    def classify(self, text: str) -> ClassificationResult:
        """
        Scan text to count matching keywords for each category.

        Returns:
            ClassificationResult containing the classified DocumentType and confidence.
        """
        if not text or not text.strip():
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                signals=[]
            )

        lower_text = text.lower()
        scores = {}
        signals_map = {}

        for doc_type, rule in self._rules.items():
            matched = []
            score = 0.0
            for kw in rule["keywords"]:
                count = lower_text.count(kw)
                if count > 0:
                    matched.append(kw)
                    # logarithmic scaling for frequency to avoid single keyword flood
                    import math
                    score += rule["weight"] * (1 + math.log(count))
            
            scores[doc_type] = score
            signals_map[doc_type] = matched

        if not scores:
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                signals=[]
            )

        # Find the highest scoring document type
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        total_score = sum(scores.values())

        if total_score == 0.0 or best_score == 0.0:
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                signals=[]
            )

        # Confidence is best score / total score of all categories
        confidence = best_score / total_score
        signals = signals_map[best_type]

        # Enforce threshold config
        threshold = settings.document_classification_threshold
        if confidence < threshold:
            # If best type is not certain enough, classify as UNKNOWN but keep signals
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=confidence,
                signals=signals
            )

        return ClassificationResult(
            document_type=best_type,
            confidence=round(confidence, 2),
            signals=signals
        )
