"""
Normalizer for extracted financial information.

Ensures currency codes, date structures, transaction direction types, and amounts
adhere to standard project specifications.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Any

from app.models.enums import DocumentType, TransactionType
from app.documents.financial_extractor import ExtractedField, TransactionCandidate, FinancialExtractionResult


class FinancialDocumentNormalizer:
    """Normalizes extracted candidate structures before validation and review."""

    def normalize(self, result: FinancialExtractionResult) -> None:
        """Modifies the extraction result fields and transactions in-place with normalized representations."""
        # 1. Normalize Extracted Fields
        for f in result.fields:
            if "salary" in f.name or "amount" in f.name or "balance" in f.name or "emi" in f.name:
                f.value = self.normalize_amount(f.value)
            elif "date" in f.name or "period" in f.name:
                normalized_dt = self.normalize_date(f.value)
                if normalized_dt:
                    f.value = normalized_dt

        # 2. Normalize Transactions list
        for t in result.transactions:
            # Clean currency code
            t.currency = self.normalize_currency(t.currency)
            
            # Clean debit / credit / balance amounts
            t.debit = self.clean_amount_str(t.debit)
            t.credit = self.clean_amount_str(t.credit)
            t.balance = self.clean_amount_str(t.balance)
            
            # Clean transaction date string to standard DD/MM/YYYY or similar representation if parseable
            parsed_date = self.normalize_date(t.date)
            if parsed_date:
                t.date = parsed_date.isoformat()

    def normalize_amount(self, value: Any) -> Decimal:
        """Ensures amounts are high-precision Decimal values."""
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        cleaned = self.clean_amount_str(str(value))
        if cleaned:
            try:
                return Decimal(cleaned)
            except (InvalidOperation, ValueError):
                pass
        return Decimal("0.00")

    def clean_amount_str(self, val: Optional[str]) -> Optional[str]:
        """Strip formatting, symbols, commas from currency strings."""
        if not val or not val.strip():
            return None
        # Extract digits, commas, dots, and optional minus sign
        match = re.search(r"-?[\d,]+(?:\.\d+)?", val)
        if match:
            num_part = match.group(0)
            cleaned = num_part.replace(",", "")
            return cleaned
        return None

    def normalize_currency(self, currency_str: Optional[str]) -> str:
        """Maps currency strings/symbols to ISO 4217 standard (e.g. ₹ -> INR)."""
        if not currency_str:
            return "INR"
        curr = currency_str.upper().strip()
        if curr in ("INR", "₹", "RS", "RS.", "RUPEES"):
            return "INR"
        if curr in ("USD", "$"):
            return "USD"
        if curr in ("EUR", "€"):
            return "EUR"
        return curr

    def normalize_date(self, value: Any) -> Optional[date]:
        """Parses various date patterns into date objects with future-date disambiguation."""
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        
        date_str = str(value).strip().replace("-", "/").replace(".", "/")
        parts = date_str.split("/")
        if len(parts) != 3:
            return None

        try:
            if len(parts[0]) == 4:
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
            
            d = int(parts[0])
            m = int(parts[1])
            y = int(parts[2])
            if y < 100:
                y += 2000
            
            # Default assumption: DD/MM/YYYY
            try:
                dt_dm = date(y, m, d)
            except ValueError:
                dt_dm = None
                
            # Alternative assumption: MM/DD/YYYY
            try:
                dt_md = date(y, d, m)
            except ValueError:
                dt_md = None

            if dt_dm and dt_md:
                # Disambiguate if default parsed date (DD/MM/YYYY) lies in the future
                # but alternative (MM/DD/YYYY) does not.
                today = date.today()
                if dt_dm > today + timedelta(days=7) and dt_md <= today + timedelta(days=7):
                    return dt_md
                return dt_dm
            
            return dt_dm or dt_md
        except ValueError:
            return None
