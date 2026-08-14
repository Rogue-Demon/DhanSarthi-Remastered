"""
Universal Financial Field Mapping Registry for DhanSarthi Document Intelligence.

Decouples raw field extraction from domain persistence. Provides data-driven
routing rules mapping (DocumentType, field_name) to target financial entities
(Income, Expense, Asset, Liability, Metadata, ReviewOnly, Unsupported).
"""

from __future__ import annotations

import enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.models.enums import DocumentType, AssetType, LiabilityType, IncomeFrequency, ExpenseFrequency


class DestinationType(str, enum.Enum):
    """Target financial subsystem domain."""

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    METADATA = "METADATA"
    REVIEW_ONLY = "REVIEW_ONLY"
    UNSUPPORTED = "UNSUPPORTED"


class FieldImportBehavior(str, enum.Enum):
    """How the field is processed during confirmation."""

    FINANCIAL_RECORD = "FINANCIAL_RECORD"
    METADATA = "METADATA"
    REVIEW_ONLY = "REVIEW_ONLY"
    UNSUPPORTED = "UNSUPPORTED"


class FieldStatus(str, enum.Enum):
    """Detailed status reporting for extracted fields."""

    SUPPORTED = "SUPPORTED"
    IMPORTED = "IMPORTED"
    SKIPPED = "SKIPPED"
    REVIEW_ONLY = "REVIEW_ONLY"
    UNSUPPORTED = "UNSUPPORTED"
    DUPLICATE = "DUPLICATE"
    INVALID = "INVALID"


class FieldMappingRule(BaseModel):
    """Mapping rule defining how an extracted field is routed."""

    field_name: str
    doc_type: Optional[DocumentType] = None  # None matches any doc_type
    destination_type: DestinationType
    behavior: FieldImportBehavior
    destination_field: Optional[str] = None
    default_category: Optional[str] = None
    explanation: str


class FieldMappingRegistry:
    """Central registry of document field import rules."""

    def __init__(self) -> None:
        self._rules: Dict[Tuple[Optional[DocumentType], str], FieldMappingRule] = {}
        self._register_default_rules()

    def register(self, rule: FieldMappingRule) -> None:
        """Register a mapping rule."""
        key = (rule.doc_type, rule.field_name.lower())
        self._rules[key] = rule

    def get_rule(self, doc_type: DocumentType, field_name: str) -> FieldMappingRule:
        """
        Lookup rule by specific (doc_type, field_name) first, falling back to
        (None, field_name) generic rule, or returning an UNSUPPORTED fallback.
        """
        fname = field_name.lower()
        specific_key = (doc_type, fname)
        if specific_key in self._rules:
            return self._rules[specific_key]

        generic_key = (None, fname)
        if generic_key in self._rules:
            return self._rules[generic_key]

        return FieldMappingRule(
            field_name=field_name,
            doc_type=doc_type,
            destination_type=DestinationType.UNSUPPORTED,
            behavior=FieldImportBehavior.UNSUPPORTED,
            explanation=f"Field '{field_name}' does not have a mapped financial destination."
        )

    def _register_default_rules(self) -> None:
        """Populate pre-configured mapping rules for all supported document types."""

        # ------------------------------------------------------------------
        # SALARY SLIP MAPPINGS
        # ------------------------------------------------------------------
        self.register(FieldMappingRule(
            field_name="net_salary",
            doc_type=DocumentType.SALARY_SLIP,
            destination_type=DestinationType.INCOME,
            behavior=FieldImportBehavior.FINANCIAL_RECORD,
            destination_field="amount",
            default_category="Salary",
            explanation="Net Salary is imported as primary income cash inflow."
        ))
        self.register(FieldMappingRule(
            field_name="gross_salary",
            doc_type=DocumentType.SALARY_SLIP,
            destination_type=DestinationType.METADATA,
            behavior=FieldImportBehavior.METADATA,
            destination_field="gross_salary",
            explanation="Gross Salary recorded as informational metadata to prevent double-counting with Net Salary."
        ))
        self.register(FieldMappingRule(
            field_name="total_deductions",
            doc_type=DocumentType.SALARY_SLIP,
            destination_type=DestinationType.METADATA,
            behavior=FieldImportBehavior.METADATA,
            destination_field="total_deductions",
            explanation="Total deductions logged as informational metadata."
        ))
        self.register(FieldMappingRule(
            field_name="salary_period",
            doc_type=DocumentType.SALARY_SLIP,
            destination_type=DestinationType.METADATA,
            behavior=FieldImportBehavior.METADATA,
            destination_field="income_date",
            explanation="Salary period used for income date resolution and recorded as metadata."
        ))
        self.register(FieldMappingRule(
            field_name="employer",
            doc_type=DocumentType.SALARY_SLIP,
            destination_type=DestinationType.METADATA,
            behavior=FieldImportBehavior.METADATA,
            destination_field="source",
            explanation="Employer name used as income source name."
        ))

        # ------------------------------------------------------------------
        # BILL / INVOICE / EXPENSE MAPPINGS
        # ------------------------------------------------------------------
        self.register(FieldMappingRule(
            field_name="total_amount",
            doc_type=DocumentType.BILL,
            destination_type=DestinationType.EXPENSE,
            behavior=FieldImportBehavior.FINANCIAL_RECORD,
            destination_field="amount",
            default_category="Utilities",
            explanation="Bill total amount mapped to Expense."
        ))
        self.register(FieldMappingRule(
            field_name="amount_due",
            doc_type=DocumentType.BILL,
            destination_type=DestinationType.EXPENSE,
            behavior=FieldImportBehavior.FINANCIAL_RECORD,
            destination_field="amount",
            default_category="Bills",
            explanation="Amount due mapped to Expense."
        ))
        self.register(FieldMappingRule(
            field_name="vendor",
            doc_type=DocumentType.BILL,
            destination_type=DestinationType.METADATA,
            behavior=FieldImportBehavior.METADATA,
            destination_field="merchant",
            explanation="Vendor name used as expense merchant."
        ))
        self.register(FieldMappingRule(
            field_name="biller_name",
            doc_type=DocumentType.BILL,
            destination_type=DestinationType.METADATA,
            behavior=FieldImportBehavior.METADATA,
            destination_field="merchant",
            explanation="Biller name used as expense merchant."
        ))

        # ------------------------------------------------------------------
        # LOAN STATEMENT / LIABILITY MAPPINGS
        # ------------------------------------------------------------------
        self.register(FieldMappingRule(
            field_name="outstanding_balance",
            doc_type=DocumentType.LOAN_STATEMENT,
            destination_type=DestinationType.LIABILITY,
            behavior=FieldImportBehavior.FINANCIAL_RECORD,
            destination_field="amount",
            default_category="PERSONAL_DEBT",
            explanation="Outstanding loan balance mapped to Liability."
        ))
        self.register(FieldMappingRule(
            field_name="principal_amount",
            doc_type=DocumentType.LOAN_STATEMENT,
            destination_type=DestinationType.METADATA,
            behavior=FieldImportBehavior.METADATA,
            destination_field="principal",
            explanation="Original principal recorded as liability metadata."
        ))
        self.register(FieldMappingRule(
            field_name="emi",
            doc_type=DocumentType.LOAN_STATEMENT,
            destination_type=DestinationType.METADATA,
            behavior=FieldImportBehavior.METADATA,
            destination_field="monthly_payment",
            explanation="Monthly EMI recorded as loan payment metadata."
        ))
        self.register(FieldMappingRule(
            field_name="interest_rate",
            doc_type=DocumentType.LOAN_STATEMENT,
            destination_type=DestinationType.METADATA,
            behavior=FieldImportBehavior.METADATA,
            destination_field="interest_rate",
            explanation="Interest rate recorded as liability metadata."
        ))
        self.register(FieldMappingRule(
            field_name="lender",
            doc_type=DocumentType.LOAN_STATEMENT,
            destination_type=DestinationType.METADATA,
            behavior=FieldImportBehavior.METADATA,
            destination_field="institution",
            explanation="Lender name recorded as institution metadata."
        ))

        # ------------------------------------------------------------------
        # INVESTMENT / ASSET MAPPINGS
        # ------------------------------------------------------------------
        self.register(FieldMappingRule(
            field_name="current_value",
            doc_type=DocumentType.INVESTMENT_STATEMENT,
            destination_type=DestinationType.ASSET,
            behavior=FieldImportBehavior.FINANCIAL_RECORD,
            destination_field="value",
            default_category="BANK_BALANCE",
            explanation="Current portfolio/holding value mapped to Asset."
        ))
        self.register(FieldMappingRule(
            field_name="invested_amount",
            doc_type=DocumentType.INVESTMENT_STATEMENT,
            destination_type=DestinationType.METADATA,
            behavior=FieldImportBehavior.METADATA,
            destination_field="cost_basis",
            explanation="Cost basis recorded as asset metadata."
        ))
        self.register(FieldMappingRule(
            field_name="folio_number",
            doc_type=DocumentType.INVESTMENT_STATEMENT,
            destination_type=DestinationType.REVIEW_ONLY,
            behavior=FieldImportBehavior.REVIEW_ONLY,
            explanation="Folio number displayed for review only."
        ))

        # ------------------------------------------------------------------
        # GENERIC / FALLBACK FIELD MAPPINGS
        # ------------------------------------------------------------------
        self.register(FieldMappingRule(
            field_name="account_number",
            doc_type=None,
            destination_type=DestinationType.REVIEW_ONLY,
            behavior=FieldImportBehavior.REVIEW_ONLY,
            explanation="Masked account number displayed for context."
        ))
        self.register(FieldMappingRule(
            field_name="period_start",
            doc_type=None,
            destination_type=DestinationType.METADATA,
            behavior=FieldImportBehavior.METADATA,
            explanation="Statement period start date."
        ))
        self.register(FieldMappingRule(
            field_name="period_end",
            doc_type=None,
            destination_type=DestinationType.METADATA,
            behavior=FieldImportBehavior.METADATA,
            explanation="Statement period end date."
        ))
        self.register(FieldMappingRule(
            field_name="amount",
            doc_type=None,
            destination_type=DestinationType.INCOME,
            behavior=FieldImportBehavior.FINANCIAL_RECORD,
            destination_field="amount",
            explanation="Generic financial amount."
        ))


# Global singleton instance
default_mapping_registry = FieldMappingRegistry()
