"""
Financial Entity & Temporal Expression Extractor for DhanSarthi.

Extracts domain entities (products, institutions, tax categories, loan types,
amounts) and temporal references from user queries.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from app.ai.schemas.query_understanding import EntityCategory, ExtractedEntity, TemporalReference


class EntityExtractor:
    """Extracts domain entities and temporal expressions."""

    ENTITY_PATTERNS = [
        (r"\b(sip|systematic investment plan)\b", EntityCategory.INVESTMENT_PRODUCT, "Systematic Investment Plan"),
        (r"\b(mutual fund|mutual funds|mf)\b", EntityCategory.INVESTMENT_PRODUCT, "Mutual Funds"),
        (r"\b(ppf|public provident fund)\b", EntityCategory.INVESTMENT_PRODUCT, "Public Provident Fund"),
        (r"\b(nps|national pension system)\b", EntityCategory.INVESTMENT_PRODUCT, "National Pension System"),
        (r"\b(fd|fixed deposit)\b", EntityCategory.INVESTMENT_PRODUCT, "Fixed Deposit"),
        (r"\b(rd|recurring deposit)\b", EntityCategory.INVESTMENT_PRODUCT, "Recurring Deposit"),
        (r"\b(sgb|sovereign gold bond)\b", EntityCategory.INVESTMENT_PRODUCT, "Sovereign Gold Bond"),
        (r"\b(nav|net asset value)\b", EntityCategory.INVESTMENT_PRODUCT, "Net Asset Value"),
        (r"\b(ter|total expense ratio)\b", EntityCategory.INVESTMENT_PRODUCT, "Total Expense Ratio"),
        (r"\b(rbi|reserve bank of india)\b", EntityCategory.FINANCIAL_INSTITUTION, "RBI"),
        (r"\b(sebi)\b", EntityCategory.FINANCIAL_INSTITUTION, "SEBI"),
        (r"\b(pfrda)\b", EntityCategory.FINANCIAL_INSTITUTION, "PFRDA"),
        (r"\b(amfi)\b", EntityCategory.FINANCIAL_INSTITUTION, "AMFI"),
        (r"\b(dicgc)\b", EntityCategory.FINANCIAL_INSTITUTION, "DICGC"),
        (r"\b(kyc|know your customer)\b", EntityCategory.FINANCIAL_INSTITUTION, "KYC"),
        (r"\b(pan|permanent account number)\b", EntityCategory.TAX_CATEGORY, "PAN"),
        (r"\b(section 80c|80c)\b", EntityCategory.TAX_CATEGORY, "Section 80C"),
        (r"\b(section 80d|80d)\b", EntityCategory.TAX_CATEGORY, "Section 80D"),
        (r"\b(stcg|short term capital gains)\b", EntityCategory.TAX_CATEGORY, "STCG"),
        (r"\b(ltcg|long term capital gains)\b", EntityCategory.TAX_CATEGORY, "LTCG"),
        (r"\b(tds|tax deducted at source)\b", EntityCategory.TAX_CATEGORY, "TDS"),
        (r"\b(itr|income tax return)\b", EntityCategory.TAX_CATEGORY, "ITR"),
        (r"\b(home loan|housing loan)\b", EntityCategory.LOAN_TYPE, "Home Loan"),
        (r"\b(personal loan)\b", EntityCategory.LOAN_TYPE, "Personal Loan"),
        (r"\b(car loan|vehicle loan)\b", EntityCategory.LOAN_TYPE, "Car Loan"),
        (r"\b(emi|equated monthly installment)\b", EntityCategory.LOAN_TYPE, "EMI"),
        (r"\b(dti|debt to income|debt-to-income)\b", EntityCategory.LOAN_TYPE, "Debt-to-Income"),
        (r"\b(salary|paycheck)\b", EntityCategory.INCOME_CATEGORY, "Salary"),
        (r"\b(rent)\b", EntityCategory.EXPENSE_CATEGORY, "Rent"),
        (r"\b(gold)\b", EntityCategory.ASSET_TYPE, "Gold"),
        (r"\b(property|real estate)\b", EntityCategory.ASSET_TYPE, "Real Estate"),
        (r"\b(credit card)\b", EntityCategory.LIABILITY_TYPE, "Credit Card"),
    ]

    TEMPORAL_PATTERNS = [
        (r"\b(this month)\b", "this month", False),
        (r"\b(last month)\b", "last month", True),
        (r"\b(this year)\b", "this year", False),
        (r"\b(last year)\b", "last year", True),
        (r"\b(today)\b", "today", False),
        (r"\b(yesterday)\b", "yesterday", True),
        (r"\b(last 6 months)\b", "last 6 months", True),
        (r"\b(since january)\b", "since january", False),
        (r"\b(fy\s*\d{4}[-\s]?\d{2,4})\b", "financial year", True),
        (r"\b(ay\s*\d{4}[-\s]?\d{2,4})\b", "assessment year", True),
        (r"\b(in\s*202\d)\b", "year", True),
        (r"\b(before\s*202\d)\b", "historical period", True),
    ]

    def extract(self, query: str) -> Tuple[List[ExtractedEntity], List[TemporalReference]]:
        """
        Extract financial entities and temporal references from query.

        Returns:
            (entities, temporal_references)
        """
        if not query or not query.strip():
            return [], []

        q_lower = query.lower()
        entities: List[ExtractedEntity] = []
        seen_entities = set()

        # 1. Match predefined domain entity patterns
        for pattern, cat, canonical_name in self.ENTITY_PATTERNS:
            match = re.search(pattern, q_lower, re.IGNORECASE)
            if match:
                key = (cat.value, canonical_name)
                if key not in seen_entities:
                    seen_entities.add(key)
                    entities.append(
                        ExtractedEntity(
                            entity_type=cat,
                            value=canonical_name,
                            raw_text=match.group(0),
                            confidence=1.0,
                        )
                    )

        # 2. Extract monetary amount entities (e.g., ₹50,000, 50000, 1.25 lakh, 5 lakh)
        amount_matches = re.findall(
            r"(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?\s*(?:lakh|crore|k|m)?)\b",
            q_lower,
            re.IGNORECASE,
        )
        for amt_str in amount_matches:
            amt_clean = amt_str.strip()
            if amt_clean and amt_clean not in {"2024", "2025", "2026", "2027"}:
                key = (EntityCategory.AMOUNT.value, amt_clean)
                if key not in seen_entities:
                    seen_entities.add(key)
                    entities.append(
                        ExtractedEntity(
                            entity_type=EntityCategory.AMOUNT,
                            value=amt_clean,
                            raw_text=amt_clean,
                            confidence=1.0,
                        )
                    )

        # 3. Extract temporal references
        temporal_refs: List[TemporalReference] = []
        seen_temps = set()

        for pattern, period, is_hist in self.TEMPORAL_PATTERNS:
            match = re.search(pattern, q_lower, re.IGNORECASE)
            if match:
                raw_expr = match.group(0)
                if raw_expr not in seen_temps:
                    seen_temps.add(raw_expr)
                    temporal_refs.append(
                        TemporalReference(
                            expression=raw_expr,
                            target_period=period,
                            is_historical=is_hist or ("2024" in raw_expr or "2023" in raw_expr),
                        )
                    )

        return entities, temporal_refs
