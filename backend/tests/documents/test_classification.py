"""
Tests for document classification based on text keyword signals.
"""

from __future__ import annotations

from app.models.enums import DocumentType
from app.documents.classifier import DocumentClassifier


class TestDocumentClassification:
    def test_classify_bank_statement(self):
        classifier = DocumentClassifier()
        text = (
            "HDFC Bank Statement of Account\n"
            "Account Number: 1234567890\n"
            "Transaction Date | Description | Debit | Credit | Balance\n"
            "12-08-2026 | Opening Balance | | | 15000.00\n"
            "13-08-2026 | Withdrawal ATM | 2000.00 | | 13000.00\n"
        )
        res = classifier.classify(text)
        assert res.document_type == DocumentType.BANK_STATEMENT
        assert res.confidence >= 0.6
        assert "account number" in res.signals

    def test_classify_salary_slip(self):
        classifier = DocumentClassifier()
        text = (
            "ABC Tech Solutions Private Limited\n"
            "Pay Slip for August 2026\n"
            "Basic Salary: 50,000.00\n"
            "House Rent Allowance (HRA): 20,000.00\n"
            "Provident Fund (EPF) Deduction: 6,000.00\n"
            "Net Pay / Take Home Salary: 64,000.00\n"
        )
        res = classifier.classify(text)
        assert res.document_type == DocumentType.SALARY_SLIP
        assert "payslip" in res.signals or "salary slip" in res.signals or "basic salary" in res.signals

    def test_classify_loan_statement(self):
        classifier = DocumentClassifier()
        text = (
            "SBI Home Loan Statement\n"
            "Loan Account Number: 987654321\n"
            "Principal Amount Disbursed: 45,00,000.00\n"
            "Rate of Interest: 8.5%\n"
            "Monthly EMI: 38,000.00\n"
            "Outstanding Principal Balance: 42,50,000.00\n"
        )
        res = classifier.classify(text)
        assert res.document_type == DocumentType.LOAN_STATEMENT
        assert "loan account" in res.signals or "outstanding principal" in res.signals

    def test_classify_investment_statement(self):
        classifier = DocumentClassifier()
        text = (
            "ICICI Prudential Mutual Fund Statement\n"
            "Folio Number: 456123789\n"
            "Scheme Name: Large & Midcap Fund - Growth Option\n"
            "NAV: 142.50\n"
            "Transaction Units: 124.52\n"
            "SIP Contribution: 5,000.00\n"
            "Current Portfolio Value: 75,000.00\n"
        )
        res = classifier.classify(text)
        assert res.document_type == DocumentType.INVESTMENT_STATEMENT
        assert "folio number" in res.signals or "mutual fund" in res.signals

    def test_classify_tax_document(self):
        classifier = DocumentClassifier()
        text = (
            "Form 16\n"
            "Certificate under Section 203 of the Income Tax Act\n"
            "PAN Card Number: ABCDE1234F\n"
            "Assessment Year: 2026-27\n"
            "Total Tax Deduction at Source (TDS): 45,000.00\n"
        )
        res = classifier.classify(text)
        assert res.document_type == DocumentType.TAX_DOCUMENT
        assert "form 16" in res.signals or "income tax" in res.signals

    def test_classify_bill(self):
        classifier = DocumentClassifier()
        text = (
            "Reliance Jio Broadband Invoice\n"
            "Bill Number: JIO-123456\n"
            "Bill Date: 12-08-2026\n"
            "Due Date: 25-08-2026\n"
            "Amount Due / Total Payable: 1,178.00\n"
        )
        res = classifier.classify(text)
        assert res.document_type == DocumentType.BILL
        assert "invoice" in res.signals or "due date" in res.signals

    def test_classify_unknown_below_threshold(self):
        classifier = DocumentClassifier()
        # Text containing only a few ambiguous words
        text = "Hello, this is a generic document file that does not contain financial tables."
        res = classifier.classify(text)
        assert res.document_type == DocumentType.UNKNOWN
