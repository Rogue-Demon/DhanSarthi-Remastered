# DhanSarthi — FINANCIAL ENGINE

> This document defines the deterministic financial calculation and analysis
> layer used by DhanSarthi.

---

# 1. PURPOSE

The Financial Engine is the **calculation and financial-analysis layer** of
DhanSarthi.

Its responsibility is to produce reliable financial calculations that can
then be explained by the AI Advisor.

Core principle:

```text
Financial Engine = Calculates
AI Advisor       = Explains + Personalizes
RAG              = Provides Knowledge
PostgreSQL       = Stores Data
````

The LLM must not be the source of truth for numerical calculations.

---

# 2. CORE FINANCIAL AREAS

The Financial Engine should support the following areas.

## Personal Finance

```text
Income
Expenses
Cash Flow
Savings
Net Worth
Assets
Liabilities
Debt
Financial Health
```

## Investments

```text
SIP
Mutual Funds
Stocks
FD
RD
Bonds
ETFs
Portfolio
Returns
Allocation
Projections
```

## Loans

```text
EMI
Interest
Principal
Amortization
Affordability
Debt-to-Income
Repayment
Loan Comparison
```

## Goals

```text
Goal Amount
Current Savings
Required Contribution
Time Horizon
Projected Progress
Goal Shortfall
```

## Taxes

```text
Taxable Income
Deductions
Tax Estimates
Tax-Saving Analysis
```

Tax calculations must use the appropriate financial-year rules.

---

# 3. MONEY CALCULATION RULES

## 3.1 Monetary Values

Use appropriate decimal-based arithmetic for monetary calculations.

Avoid relying on binary floating-point arithmetic for critical money values.

Example:

```text
₹10,000.10
```

must not be silently converted into an inaccurate floating-point value.

---

## 3.2 Rounding

Rounding rules must be explicit.

For example:

```text
Internal Calculation
        ↓
High Precision
        ↓
Final Presentation
        ↓
Currency Rounding
```

Do not round intermediate values unnecessarily.

---

## 3.3 Currency

Financial calculations must know which currency they operate on.

The current product may primarily use:

```text
INR
```

but currency should not be hardcoded throughout the financial engine.

---

# 4. PERSONAL FINANCE CALCULATIONS

## 4.1 Total Income

Conceptually:

```text
Total Income =
Sum of applicable income sources
```

Possible sources:

```text
Salary
Business Income
Freelance
Interest
Rental Income
Other Income
```

---

## 4.2 Total Expenses

```text
Total Expenses =
Sum of applicable expenses
```

Expenses may be categorized as:

```text
Housing
Food
Transportation
Education
Healthcare
Entertainment
Shopping
Utilities
Debt Payments
Other
```

---

## 4.3 Net Cash Flow

```text
Net Cash Flow =
Total Income - Total Expenses
```

Positive:

```text
Income > Expenses
```

Negative:

```text
Expenses > Income
```

---

## 4.4 Savings Rate

Conceptually:

```text
Savings =
Income - Expenses
```

```text
Savings Rate =
Savings / Income × 100
```

If income is zero or unavailable, the engine must not divide by zero.

---

# 5. NET WORTH

Net worth is:

```text
Net Worth =
Total Assets - Total Liabilities
```

Assets may include:

```text
Cash
Bank Balance
Investments
Property
Gold
Other Assets
```

Liabilities may include:

```text
Loans
Credit Card Debt
Other Debt
```

The AI can use this result to explain financial position.

---

# 6. DEBT ANALYSIS

## 6.1 Debt-to-Income Ratio

Conceptually:

```text
DTI =
Monthly Debt Obligations
/
Gross Monthly Income
× 100
```

The exact interpretation should be clearly documented.

Do not label a user as financially unsafe using a single ratio alone.

Consider other factors such as:

```text
Emergency Fund
Income Stability
Expenses
Interest Rates
Financial Goals
```

---

## 6.2 Debt Service

The engine should calculate:

```text
Existing Debt Payments
+
New Proposed Debt Payment
```

when evaluating a new loan.

---

# 7. LOAN ENGINE

## 7.1 EMI

For a standard reducing-balance loan:

```text
EMI =
P × r × (1+r)^n
/
((1+r)^n - 1)
```

Where:

```text
P = Principal
r = Periodic Interest Rate
n = Number of Periods
```

The implementation must clearly define:

```text
Annual Interest Rate
Monthly Interest Rate
Loan Tenure
Payment Frequency
```

---

## 7.2 Total Payment

```text
Total Payment =
EMI × Number of Payments
```

---

## 7.3 Total Interest

```text
Total Interest =
Total Payment - Principal
```

---

## 7.4 Amortization

The engine should be able to generate a repayment schedule containing:

```text
Payment Number
Opening Balance
EMI
Principal Component
Interest Component
Closing Balance
```

---

# 8. LOAN AFFORDABILITY

Loan affordability should not depend only on EMI.

Consider:

```text
Income
Expenses
Existing EMI
New EMI
Debt-to-Income
Cash Flow
Emergency Fund
Loan Tenure
Interest Rate
```

Preferred flow:

```text
Loan Details
      +
User Financial Profile
      ↓
Financial Engine
      ↓
Affordability Analysis
      ↓
Risk Indicators
      ↓
AI Explanation
```

The system should produce an analysis, not a guaranteed approval decision.

---

# 9. SIP ENGINE

For regular SIP contributions, the engine may calculate future value using the appropriate periodic investment formula.

Inputs may include:

```text
Monthly Contribution
Expected Annual Return
Investment Duration
Contribution Frequency
```

Output may include:

```text
Total Invested
Estimated Growth
Estimated Future Value
```

The result must clearly identify the return as an assumption.

Example:

```text
Assumed annual return: 10%

This is an assumed rate for projection purposes,
not a guaranteed return.
```

---

# 10. INVESTMENT RETURNS

The engine should distinguish between:

```text
Absolute Return
Annualized Return
XIRR / Money-Weighted Return
```

when sufficient transaction data is available.

Do not calculate investment performance using an inappropriate formula simply
because it is easier.

---

# 11. PORTFOLIO ANALYSIS

The portfolio engine may calculate:

```text
Total Investment
Current Value
Profit / Loss
Asset Allocation
Investment Allocation
Concentration
Portfolio Growth
```

Possible allocation categories:

```text
Equity
Debt
Gold
Cash
Other
```

The AI should explain portfolio results but must not fabricate market prices.

---

# 12. FD / RD CALCULATIONS

For fixed-income products, calculate where applicable:

```text
Principal
Interest Rate
Tenure
Compounding Frequency
Maturity Value
Interest Earned
```

The calculation must reflect the actual product assumptions.

Do not assume every FD/RD uses the same compounding method.

---

# 13. GOAL PLANNING

For a financial goal:

```text
Goal Amount
Current Amount
Time Remaining
Expected Return
Required Contribution
```

The engine may determine:

```text
Required Monthly Contribution
Projected Goal Value
Shortfall
Surplus
```

Example:

```text
Goal
₹10,00,000

Current Savings
₹2,00,000

Remaining Period
5 years
```

The engine determines the required contribution using the specified assumptions.

---

# 14. TAX ENGINE

Tax logic must be separated from general calculations.

Tax calculations depend on:

```text
Financial Year
User Profile
Income
Deductions
Applicable Tax Rules
Tax Regime
```

Tax rules must not be permanently hardcoded into random service functions.

Prefer a structured rule system.

Example:

```text
TaxRuleSet
    ↓
Financial Year
    ↓
Applicable Rules
    ↓
Tax Calculation
```

If the applicable rule is unknown or outdated, the system must not invent it.

---

# 15. FINANCIAL HEALTH

DhanSarthi may calculate financial health indicators such as:

```text
Savings Rate
Debt Ratio
Emergency Fund Coverage
Cash Flow
Net Worth
Investment Allocation
Goal Progress
```

These indicators should be treated as analytical signals.

Avoid presenting a single score as an absolute measure of someone's financial health.

---

# 16. RECOMMENDATION INPUTS

The Financial Engine may provide structured indicators to the recommendation layer.

Example:

```json
{
  "cash_flow": "positive",
  "savings_rate": 24.5,
  "debt_to_income": 31.2,
  "emergency_fund_months": 2.8
}
```

The AI can then explain the implications.

---

# 17. AI INTEGRATION

The preferred architecture is:

```text
User Question
      ↓
AI Intent Detection
      ↓
Relevant User Data
      ↓
Financial Engine
      ↓
Structured Result
      ↓
AI Explanation
```

Example:

```text
User:
"Can I afford a ₹15 lakh loan?"

AI
 ↓
Retrieve income + expenses + existing loans
 ↓
Calculate EMI
 ↓
Calculate debt ratio
 ↓
Calculate cash-flow impact
 ↓
Evaluate affordability indicators
 ↓
Explain result
```

The AI should not independently calculate the final numbers if the engine
already provides them.

---

# 18. VALIDATION

Every financial calculation should validate:

```text
Required Inputs
Input Types
Positive/Negative Constraints
Zero Values
Maximum Reasonable Values
Date Ranges
Interest Rates
Tenure
Currency
```

Example:

```text
Loan Principal <= 0
```

should result in a validation error.

---

# 19. EDGE CASES

The engine must handle cases such as:

```text
Zero Income
Zero Interest
Zero Expenses
Negative Cash Flow
Very Short Tenure
Very Long Tenure
Missing Data
Partial Data
Rounding Differences
Early Loan Repayment
Irregular Investments
```

Do not silently produce misleading results.

---

# 20. TESTING

Every financial formula must have automated tests.

Minimum test categories:

```text
Normal Case
Boundary Case
Zero Case
Invalid Input
Large Value
Decimal Value
Expected Result
```

For example, EMI testing should verify:

```text
Principal
Rate
Tenure
EMI
Total Interest
Amortization
```

against trusted expected values.

---

# 21. FINANCIAL ENGINE RULES FOR ANTIGRAVITY

When implementing or modifying the Financial Engine:

1. Keep calculations deterministic.

2. Use decimal-safe monetary arithmetic.

3. Validate all inputs.

4. Never hide assumptions.

5. Do not put financial calculations inside React components.

6. Do not put critical financial calculations inside LLM prompts.

7. Do not rely on the LLM for numerical accuracy.

8. Keep calculations independent from FastAPI where practical.

9. Write tests for every important formula.

10. Clearly define rounding behavior.

11. Clearly define units and frequencies.

12. Handle missing and invalid values explicitly.

13. Keep tax rules versioned and identifiable by financial year.

14. Do not fabricate market data.

15. Do not treat projections as guarantees.

16. Keep calculation logic separate from recommendation language.

---

# 22. FINAL FINANCIAL FLOW

The complete financial decision flow is:

```text
                 USER
                  │
                  ▼
             User Question
                  │
                  ▼
             AI Intent
                  │
                  ▼
          Relevant User Data
                  │
                  ▼
          Financial Engine
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
      Finance   Loan    Investment
      Analysis  Engine    Engine
        │         │         │
        └─────────┼─────────┘
                  ▼
           Structured Result
                  │
                  ▼
             AI Advisor
                  │
                  ▼
        Explanation + Risks
        + Assumptions
        + Next Steps
                  │
                  ▼
                 USER
```

---

# FINAL CONTRACT

The Financial Engine is the numerical source of truth for DhanSarthi.

The AI Advisor must explain financial-engine results rather than inventing
them.

All calculations must be:

```text
Deterministic
Validated
Tested
Traceable
Explainable
```

Financial projections are estimates.

Investment returns are not guarantees.

Loan affordability analysis is not loan approval.

Tax analysis is dependent on applicable rules and available information.

# END OF FINANCIAL_ENGINE.md

````
