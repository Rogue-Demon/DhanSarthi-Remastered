"""
DhanSarthi domain enumerations.

All Python enums used across SQLAlchemy models, Pydantic schemas, and
application logic are defined here so there is a single source of truth.

Each enum inherits from ``str`` so values are JSON-serializable and
comparable to plain strings without explicit conversion.
"""

from __future__ import annotations

import enum


class Persona(str, enum.Enum):
    """User financial persona — determines DhanSarthi dashboard and features."""

    STUDENT = "STUDENT"
    PROFESSIONAL = "PROFESSIONAL"
    BUSINESS = "BUSINESS"


class RiskProfile(str, enum.Enum):
    """Investment risk tolerance declared by the user."""

    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"


class IncomeFrequency(str, enum.Enum):
    """How often an income source recurs."""

    ONE_TIME = "ONE_TIME"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


class ExpenseFrequency(str, enum.Enum):
    """How often an expense recurs (nullable on the Expense model)."""

    ONE_TIME = "ONE_TIME"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class TransactionType(str, enum.Enum):
    """Classification of a financial movement event."""

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER = "TRANSFER"


class AssetType(str, enum.Enum):
    """Classification of a user-owned asset."""

    CASH = "CASH"
    BANK_BALANCE = "BANK_BALANCE"
    PROPERTY = "PROPERTY"
    GOLD = "GOLD"
    OTHER = "OTHER"


class LiabilityType(str, enum.Enum):
    """Classification of a user liability obligation."""

    PERSONAL_DEBT = "PERSONAL_DEBT"
    CREDIT_CARD = "CREDIT_CARD"
    HOME_LOAN = "HOME_LOAN"
    EDUCATION_LOAN = "EDUCATION_LOAN"
    BUSINESS = "BUSINESS"
    OTHER = "OTHER"


class InvestmentType(str, enum.Enum):
    """Investment product classification."""

    STOCK = "STOCK"
    MUTUAL_FUND = "MUTUAL_FUND"
    SIP = "SIP"
    FD = "FD"
    RD = "RD"
    BOND = "BOND"
    ETF = "ETF"
    GOLD = "GOLD"
    OTHER = "OTHER"


class InvestmentTransactionType(str, enum.Enum):
    """Type of activity recorded against an investment holding."""

    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    INTEREST = "INTEREST"
    CONTRIBUTION = "CONTRIBUTION"
    WITHDRAWAL = "WITHDRAWAL"


class LoanType(str, enum.Enum):
    """Loan product classification."""

    HOME = "HOME"
    PERSONAL = "PERSONAL"
    EDUCATION = "EDUCATION"
    VEHICLE = "VEHICLE"
    BUSINESS = "BUSINESS"
    OTHER = "OTHER"


class LoanStatus(str, enum.Enum):
    """Current lifecycle state of a loan."""

    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    DEFAULTED = "DEFAULTED"
    PAUSED = "PAUSED"


class GoalStatus(str, enum.Enum):
    """Current state of a user financial goal."""

    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class BudgetPeriod(str, enum.Enum):
    """Budget recurrence period."""

    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
    CUSTOM = "CUSTOM"


class KnowledgeAuthority(str, enum.Enum):
    """Publishing authority classification for RAG documents."""

    GOVERNMENT = "GOVERNMENT"
    REGULATOR = "REGULATOR"
    OFFICIAL_INSTITUTION = "OFFICIAL_INSTITUTION"
    APPROVED_EDUCATIONAL = "APPROVED_EDUCATIONAL"
    GENERAL = "GENERAL"


class KnowledgeCategory(str, enum.Enum):
    """Taxonomy of general financial knowledge."""

    TAX = "TAX"
    INVESTMENT = "INVESTMENT"
    LOAN = "LOAN"
    SAVINGS = "SAVINGS"
    BUDGETING = "BUDGETING"
    FINANCIAL_PLANNING = "FINANCIAL_PLANNING"
    GENERAL_FINANCE = "GENERAL_FINANCE"


class KnowledgeDocumentStatus(str, enum.Enum):
    """Lifecycle state of a RAG knowledge document."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DRAFT = "DRAFT"
    ARCHIVED = "ARCHIVED"


class ConversationStatus(str, enum.Enum):
    """Lifecycle state of an AI conversation thread."""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class MessageRole(str, enum.Enum):
    """Role of a participant in a conversation message."""

    USER = "USER"
    ASSISTANT = "ASSISTANT"


class DocumentStatus(str, enum.Enum):
    """Lifecycle state of a user-uploaded financial document."""

    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class DocumentType(str, enum.Enum):
    """Classification of a user-uploaded financial document."""

    BANK_STATEMENT = "BANK_STATEMENT"
    SALARY_SLIP = "SALARY_SLIP"
    LOAN_STATEMENT = "LOAN_STATEMENT"
    INVESTMENT_STATEMENT = "INVESTMENT_STATEMENT"
    TAX_DOCUMENT = "TAX_DOCUMENT"
    BILL = "BILL"
    UNKNOWN = "UNKNOWN"



