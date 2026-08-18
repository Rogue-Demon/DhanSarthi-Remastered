"""
Financial Document Information Extractor.

Extracts structured, typed fields and transactions based on classified document type.
Uses deterministic regex and table-parsing logic with confidence scoring.
"""

from __future__ import annotations

import re
import uuid
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.models.enums import DocumentType
from app.documents.extraction.base import ExtractionOutput


class ExtractedField(BaseModel):
    """A single extracted metadata field with confidence and source context."""

    name: str
    value: Any  # Decimal, date, str
    confidence: float
    source_page: int
    source_text_ref: str


class TransactionCandidate(BaseModel):
    """A single transaction row candidate extracted from a bank statement or similar document."""

    candidate_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    date: str  # Kept as string to pass to normalizer
    description: str
    debit: Optional[str] = None
    credit: Optional[str] = None
    balance: Optional[str] = None
    currency: str = "INR"
    source_page: int = 1
    source_row: int = 0
    confidence: float = 1.0


class FinancialExtractionResult(BaseModel):
    """The complete set of extracted fields and transactions from a document."""

    document_type: DocumentType
    fields: List[ExtractedField] = Field(default_factory=list)
    transactions: List[TransactionCandidate] = Field(default_factory=list)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    raw_page_count: int = 1


class FinancialDocumentExtractor:
    """Extracts structured fields and transactions from parsed document contents."""

    def __init__(self) -> None:
        # Regex patterns for amounts
        self._amount_pattern = re.compile(r"(?:rs\.?|inr|usd|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", re.IGNORECASE)
        # Regex patterns for dates
        self._date_pattern = re.compile(r"\b(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})\b")

    def extract_info(
        self, doc_type: DocumentType, extraction: ExtractionOutput
    ) -> FinancialExtractionResult:
        """
        Main dispatch method for extracting financial information.
        """
        result = FinancialExtractionResult(
            document_type=doc_type,
            raw_page_count=extraction.page_count
        )

        if doc_type == DocumentType.BANK_STATEMENT:
            self._extract_bank_statement(extraction, result)
        elif doc_type == DocumentType.SALARY_SLIP:
            self._extract_salary_slip(extraction, result)
        elif doc_type == DocumentType.LOAN_STATEMENT:
            self._extract_loan_statement(extraction, result)
        elif doc_type == DocumentType.INVESTMENT_STATEMENT:
            self._extract_investment_statement(extraction, result)
        elif doc_type == DocumentType.BILL:
            self._extract_bill_invoice(extraction, result)
        else:
            self._extract_generic(extraction, result)

        # Set overall period start/end if available in fields
        for f in result.fields:
            if f.name == "period_start" and isinstance(f.value, date):
                result.period_start = f.value
            elif f.name == "period_end" and isinstance(f.value, date):
                result.period_end = f.value

        return result

    # ------------------------------------------------------------------
    # Type-specific extraction methods
    # ------------------------------------------------------------------

    def _extract_bank_statement(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        # 1. Look for account number/bank name
        text = ext.raw_text
        account_match = re.search(r"account\s*(?:no\.?|number)\s*[:\-]?\s*([a-zA-Z0-9]+)", text, re.IGNORECASE)
        if account_match:
            raw_ac = account_match.group(1)
            # Mask account number
            masked = f"XXXXXX{raw_ac[-4:]}" if len(raw_ac) >= 4 else raw_ac
            res.fields.append(
                ExtractedField(
                    name="account_number",
                    value=masked,
                    confidence=0.9,
                    source_page=1,
                    source_text_ref=account_match.group(0)
                )
            )

        # 2. Period dates
        period_match = re.search(r"(?:statement\s*period|period)\s*[:\-]?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})\s*(?:to|and|-)\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})", text, re.IGNORECASE)
        if period_match:
            p_start = self._parse_date_stub(period_match.group(1))
            p_end = self._parse_date_stub(period_match.group(2))
            if p_start:
                res.fields.append(ExtractedField(name="period_start", value=p_start, confidence=0.95, source_page=1, source_text_ref=period_match.group(1)))
            if p_end:
                res.fields.append(ExtractedField(name="period_end", value=p_end, confidence=0.95, source_page=1, source_text_ref=period_match.group(2)))

        # 3. Transactions from tables or rows
        row_index = 0
        for page in ext.pages:
            # If CSV/Table exists, parse directly
            if page.tables:
                for table in page.tables:
                    # Look for header row to identify column indexes
                    header_idx = -1
                    date_col, desc_col, debit_col, credit_col, bal_col = -1, -1, -1, -1, -1
                    
                    for r_idx, row in enumerate(table):
                        # Clean cells
                        cleaned_row = [c.lower() for c in row]
                        # Look for header keywords
                        if any(kw in cleaned_row for kw in ["date", "description", "particulars", "debit", "credit", "amount"]):
                            header_idx = r_idx
                            for c_idx, cell in enumerate(cleaned_row):
                                if "date" in cell:
                                    date_col = c_idx
                                elif "desc" in cell or "particulars" in cell or "narration" in cell:
                                    desc_col = c_idx
                                elif "debit" in cell or "withdrawal" in cell:
                                    debit_col = c_idx
                                elif "credit" in cell or "deposit" in cell:
                                    credit_col = c_idx
                                elif "balance" in cell:
                                    bal_col = c_idx
                            break
                    
                    start_row = header_idx + 1 if header_idx != -1 else 0
                    for r_idx in range(start_row, len(table)):
                        row = table[r_idx]
                        # Skip short or empty rows
                        if len(row) < 2:
                            continue
                        
                        # Fallback mappings if headers not found
                        d_col = date_col if date_col != -1 else 0
                        ds_col = desc_col if desc_col != -1 else (1 if len(row) > 1 else 0)
                        deb_col = debit_col if debit_col != -1 else (2 if len(row) > 2 else -1)
                        cred_col = credit_col if credit_col != -1 else (3 if len(row) > 3 else -1)
                        b_col = bal_col if bal_col != -1 else (4 if len(row) > 4 else -1)

                        t_date = row[d_col]
                        t_desc = row[ds_col]
                        
                        # Validate date pattern before proceeding
                        if not self._date_pattern.search(t_date):
                            continue

                        t_debit = row[deb_col] if deb_col != -1 and deb_col < len(row) else None
                        t_credit = row[cred_col] if cred_col != -1 and cred_col < len(row) else None
                        t_balance = row[b_col] if b_col != -1 and b_col < len(row) else None

                        res.transactions.append(
                            TransactionCandidate(
                                date=t_date,
                                description=t_desc,
                                debit=t_debit,
                                credit=t_credit,
                                balance=t_balance,
                                source_page=page.page_number,
                                source_row=row_index,
                                confidence=0.98
                            )
                        )
                        row_index += 1
            else:
                # Text-based transaction fallback parser (using line-by-line regex)
                lines = page.text.split("\n")
                for line in lines:
                    line = line.strip()
                    # A typical transaction line: Date [Description] Amount
                    # e.g., "12-08-2026 Salary Credit Rs. 85000.00"
                    date_match = self._date_pattern.search(line)
                    if date_match:
                        t_date = date_match.group(1)
                        # Remove date from line to avoid interfering with description/amount parsing
                        remaining = line.replace(t_date, "").strip()
                        
                        # Look for amounts
                        amounts = self._amount_pattern.findall(remaining)
                        if amounts:
                            # Simple heuristic: last amount is balance, second-to-last is debit/credit
                            t_desc = remaining
                            for amt in amounts:
                                t_desc = t_desc.replace(amt, "")
                            t_desc = re.sub(r"rs\.?|inr|usd|[\$₹]", "", t_desc, flags=re.IGNORECASE).strip()
                            t_desc = re.sub(r"\s+", " ", t_desc)

                            # If we found at least one amount, map it
                            amount_val = amounts[0]
                            # Detect debit vs credit keywords
                            is_credit = any(kw in remaining.lower() for kw in ["credit", "deposit", "salary", "refund", "interest received"])
                            
                            res.transactions.append(
                                TransactionCandidate(
                                    date=t_date,
                                    description=t_desc or "Transaction",
                                    debit=None if is_credit else amount_val,
                                    credit=amount_val if is_credit else None,
                                    balance=amounts[1] if len(amounts) > 1 else None,
                                    source_page=page.page_number,
                                    source_row=row_index,
                                    confidence=0.85
                                )
                            )
                            row_index += 1

    def _extract_salary_slip(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        text = ext.raw_text
        
        # Gross salary
        gross_match = re.search(r"(?:gross|gross\s*(?:salary|pay|earnings))\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if gross_match:
            res.fields.append(
                ExtractedField(
                    name="gross_salary",
                    value=self._parse_decimal_stub(gross_match.group(1)),
                    confidence=0.95,
                    source_page=1,
                    source_text_ref=gross_match.group(0)
                )
            )

        # Net salary
        net_match = re.search(r"(?:net|net\s*(?:salary|pay|take-home|take\s*home))\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if net_match:
            res.fields.append(
                ExtractedField(
                    name="net_salary",
                    value=self._parse_decimal_stub(net_match.group(1)),
                    confidence=0.98,
                    source_page=1,
                    source_text_ref=net_match.group(0)
                )
            )

        # Deductions
        ded_match = re.search(r"(?:total\s*deductions|deductions)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if ded_match:
            res.fields.append(
                ExtractedField(
                    name="total_deductions",
                    value=self._parse_decimal_stub(ded_match.group(1)),
                    confidence=0.9,
                    source_page=1,
                    source_text_ref=ded_match.group(0)
                )
            )

        # Salary period
        period_match = re.search(r"(?:salary\s*period|payslip\s*for|period)\s*[:\-]?\s*([a-zA-Z0-9\s,\-]+)", text, re.IGNORECASE)
        if period_match:
            res.fields.append(
                ExtractedField(
                    name="salary_period",
                    value=period_match.group(1).strip(),
                    confidence=0.85,
                    source_page=1,
                    source_text_ref=period_match.group(0)
                )
            )

        # Employer / Company Name
        emp_match = re.search(r"(?:employer|company|organization|company\s*name)\s*[:\-]?\s*([a-zA-Z0-9\s,\-\.]+)", text, re.IGNORECASE)
        if emp_match:
            res.fields.append(
                ExtractedField(
                    name="employer",
                    value=emp_match.group(1).strip(),
                    confidence=0.85,
                    source_page=1,
                    source_text_ref=emp_match.group(0)
                )
            )

    def _extract_loan_statement(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        text = ext.raw_text
        
        # Loan account number
        loan_ac = re.search(r"loan\s*(?:account|ac)\s*(?:no\.?|number)?\s*[:\-]?\s*([a-zA-Z0-9\-]+)", text, re.IGNORECASE)
        if loan_ac:
            raw_ac = loan_ac.group(1)
            masked = f"XXXXXX{raw_ac[-4:]}" if len(raw_ac) >= 4 else raw_ac
            res.fields.append(ExtractedField(name="loan_account_number", value=masked, confidence=0.9, source_page=1, source_text_ref=loan_ac.group(0)))

        # Principal amount
        pr_amt = re.search(r"(?:principal|loan\s*amount|disbursed\s*amount)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if pr_amt:
            res.fields.append(ExtractedField(name="principal_amount", value=self._parse_decimal_stub(pr_amt.group(1)), confidence=0.95, source_page=1, source_text_ref=pr_amt.group(0)))

        # Monthly EMI
        emi_match = re.search(r"(?:emi|monthly\s*installment|installment\s*amount)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if emi_match:
            res.fields.append(ExtractedField(name="emi", value=self._parse_decimal_stub(emi_match.group(1)), confidence=0.95, source_page=1, source_text_ref=emi_match.group(0)))

        # Interest rate
        rate_match = re.search(r"(?:interest\s*rate|rate\s*of\s*interest|roi)\s*[:\-]?\s*([\d\.]+)%", text, re.IGNORECASE)
        if rate_match:
            res.fields.append(ExtractedField(name="interest_rate", value=self._parse_decimal_stub(rate_match.group(1)), confidence=0.9, source_page=1, source_text_ref=rate_match.group(0)))

        # Outstanding balance
        bal_match = re.search(r"(?:outstanding\s*balance|outstanding\s*principal|amount\s*outstanding)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if bal_match:
            res.fields.append(ExtractedField(name="outstanding_balance", value=self._parse_decimal_stub(bal_match.group(1)), confidence=0.95, source_page=1, source_text_ref=bal_match.group(0)))

    def _extract_investment_statement(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        text = ext.raw_text
        
        # Folio number
        folio_match = re.search(r"folio\s*(?:no\.?|number)\s*[:\-]?\s*([a-zA-Z0-9\-]+)", text, re.IGNORECASE)
        if folio_match:
            res.fields.append(ExtractedField(name="folio_number", value=folio_match.group(1).strip(), confidence=0.95, source_page=1, source_text_ref=folio_match.group(0)))

        # Invested amount
        inv_match = re.search(r"(?:invested\s*amount|cost\s*of\s*investment|amount\s*invested)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if inv_match:
            res.fields.append(ExtractedField(name="invested_amount", value=self._parse_decimal_stub(inv_match.group(1)), confidence=0.95, source_page=1, source_text_ref=inv_match.group(0)))

        # Current value
        val_match = re.search(r"(?:current\s*value|portfolio\s*value|valuation)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if val_match:
            res.fields.append(ExtractedField(name="current_value", value=self._parse_decimal_stub(val_match.group(1)), confidence=0.95, source_page=1, source_text_ref=val_match.group(0)))

        # Mutual fund scheme name or details
        scheme_match = re.search(r"(?:scheme\s*name|fund\s*name)\s*[:\-]?\s*([a-zA-Z0-9\s,\-\(\)]+)", text, re.IGNORECASE)
        if scheme_match:
            res.fields.append(ExtractedField(name="scheme_name", value=scheme_match.group(1).strip(), confidence=0.85, source_page=1, source_text_ref=scheme_match.group(0)))

    def _extract_bill_invoice(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        text = ext.raw_text

        # Total amount / Amount due
        tot_match = re.search(r"(?:total\s*amount|amount\s*due|total\s*payable|invoice\s*total|bill\s*amount)\s*[:\-]?\s*(?:rs\.?|inr|[\$₹])?\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if tot_match:
            res.fields.append(ExtractedField(name="total_amount", value=self._parse_decimal_stub(tot_match.group(1)), confidence=0.95, source_page=1, source_text_ref=tot_match.group(0)))

        # Vendor / Biller name
        vendor_match = re.search(r"(?:vendor|biller|biller\s*name|merchant|provider|company)\s*[:\-]?\s*([a-zA-Z0-9\s,\-\.]+)", text, re.IGNORECASE)
        if vendor_match:
            res.fields.append(ExtractedField(name="vendor", value=vendor_match.group(1).strip(), confidence=0.85, source_page=1, source_text_ref=vendor_match.group(0)))

        # Bill date
        bill_date_match = re.search(r"(?:bill\s*date|invoice\s*date|date)\s*[:\-]?\s*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})", text, re.IGNORECASE)
        if bill_date_match:
            parsed_d = self._parse_date_stub(bill_date_match.group(1))
            if parsed_d:
                res.fields.append(ExtractedField(name="bill_date", value=parsed_d, confidence=0.9, source_page=1, source_text_ref=bill_date_match.group(0)))

    def _extract_generic(self, ext: ExtractionOutput, res: FinancialExtractionResult):
        # Look for general dates and amounts
        text = ext.raw_text
        date_matches = self._date_pattern.findall(text)
        if date_matches:
            d_val = self._parse_date_stub(date_matches[0])
            if d_val:
                res.fields.append(ExtractedField(name="document_date", value=d_val, confidence=0.7, source_page=1, source_text_ref=date_matches[0]))

        amt_matches = self._amount_pattern.findall(text)
        if amt_matches:
            res.fields.append(ExtractedField(name="amount", value=self._parse_decimal_stub(amt_matches[0]), confidence=0.7, source_page=1, source_text_ref=amt_matches[0]))

    # ------------------------------------------------------------------
    # Parsing helper methods
    # ------------------------------------------------------------------

    def _parse_decimal_stub(self, val_str: str) -> Decimal:
        cleaned = val_str.replace(",", "").strip()
        try:
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return Decimal("0.00")

    def _parse_date_stub(self, date_str: str) -> Optional[date]:
        """Simple deterministic date parser support."""
        cleaned = date_str.replace("-", "/").replace(".", "/").strip()
        parts = cleaned.split("/")
        if len(parts) == 3:
            try:
                # Expect DD/MM/YYYY or YYYY/MM/DD
                if len(parts[0]) == 4:
                    return date(int(parts[0]), int(parts[1]), int(parts[2]))
                else:
                    # Disambiguation fallback
                    y = int(parts[2])
                    if y < 100:
                        y += 2000
                    return date(y, int(parts[1]), int(parts[0]))
            except ValueError:
                return None
        return None
