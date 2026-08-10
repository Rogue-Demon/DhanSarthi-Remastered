"""Tests for Investment and SIP calculation module."""

from decimal import Decimal

import pytest

from app.financial import (
    CompoundingInput,
    InvestmentItemInput,
    InvalidFinancialInput,
    InvalidInvestmentParameters,
    PortfolioInput,
    SIPInput,
    analyze_portfolio,
    calculate_compounding,
    calculate_investment_return,
    calculate_sip,
)
from app.models.enums import InvestmentType


def test_sip_standard():
    # Monthly contribution: 5,000, Return: 12% p.a., Duration: 10 years (120 months)
    # Monthly rate r = 0.01
    # FV = 5000 * (((1.01^120) - 1) / 0.01) * 1.01 = 1161695.38
    inp = SIPInput(
        monthly_contribution=Decimal("5000.00"),
        expected_annual_return_percent=Decimal("12.00"),
        duration_years=Decimal("10.00"),
    )
    res = calculate_sip(inp)

    assert res.monthly_contribution == Decimal("5000.00")
    assert res.duration_years == Decimal("10.00")
    assert res.total_invested == Decimal("600000.00")
    assert res.estimated_future_value == Decimal("1161695.38")
    assert res.estimated_gains == Decimal("561695.38")
    assert "disclaimer" in res.assumptions


def test_sip_zero_return():
    inp = SIPInput(
        monthly_contribution=Decimal("1000.00"),
        expected_annual_return_percent=Decimal("0.00"),
        duration_years=Decimal("1.00"),
    )
    res = calculate_sip(inp)

    assert res.total_invested == Decimal("12000.00")
    assert res.estimated_future_value == Decimal("12000.00")
    assert res.estimated_gains == Decimal("0.00")


def test_sip_invalid_inputs():
    with pytest.raises(InvalidInvestmentParameters):
        calculate_sip(SIPInput(monthly_contribution=Decimal("0"), expected_annual_return_percent=Decimal("10"), duration_years=Decimal("5")))

    with pytest.raises(InvalidInvestmentParameters):
        calculate_sip(SIPInput(monthly_contribution=Decimal("1000"), expected_annual_return_percent=Decimal("-5"), duration_years=Decimal("5")))

    with pytest.raises(InvalidInvestmentParameters):
        calculate_sip(SIPInput(monthly_contribution=Decimal("1000"), expected_annual_return_percent=Decimal("10"), duration_years=Decimal("0")))


def test_compounding_generic():
    inp = CompoundingInput(
        principal=Decimal("10000.00"),
        periodic_contribution=Decimal("0.00"),
        annual_rate_percent=Decimal("10.00"),
        compounding_frequency_per_year=1,
        duration_years=Decimal("3.00"),
    )
    res = calculate_compounding(inp)

    # 10000 * (1.10^3) = 13310.00
    assert res.total_invested == Decimal("10000.00")
    assert res.future_value == Decimal("13310.00")
    assert res.interest_earned == Decimal("3310.00")


def test_investment_return_positive_and_negative():
    pos_inv = InvestmentItemInput(
        name="Tech Stock",
        investment_type=InvestmentType.STOCK,
        invested_amount=Decimal("10000.00"),
        current_value=Decimal("15000.00"),
    )
    res_pos = calculate_investment_return(pos_inv)
    assert res_pos.gain_loss == Decimal("5000.00")
    assert res_pos.return_percentage == Decimal("50.00")

    neg_inv = InvestmentItemInput(
        name="Crypto",
        investment_type=InvestmentType.OTHER,
        invested_amount=Decimal("10000.00"),
        current_value=Decimal("7000.00"),
    )
    res_neg = calculate_investment_return(neg_inv)
    assert res_neg.gain_loss == Decimal("-3000.00")
    assert res_neg.return_percentage == Decimal("-30.00")


def test_portfolio_summary():
    items = [
        InvestmentItemInput(name="Stock A", investment_type=InvestmentType.STOCK, invested_amount=Decimal("50000"), current_value=Decimal("60000")),
        InvestmentItemInput(name="MF B", investment_type=InvestmentType.MUTUAL_FUND, invested_amount=Decimal("30000"), current_value=Decimal("40000")),
    ]
    res = analyze_portfolio(PortfolioInput(investments=items))

    assert res.total_invested == Decimal("80000")
    assert res.current_value == Decimal("100000")
    assert res.total_gain_loss == Decimal("20000")
    assert res.total_return_percentage == Decimal("25.00")  # 20000 / 80000 * 100
    assert res.allocation_percentages["STOCK"] == Decimal("60.00")  # 60k / 100k * 100
    assert res.allocation_percentages["MUTUAL_FUND"] == Decimal("40.00")  # 40k / 100k * 100


def test_portfolio_negative_input_raises_error():
    items = [InvestmentItemInput(name="Bad", investment_type=InvestmentType.STOCK, invested_amount=Decimal("-100"), current_value=Decimal("100"))]
    with pytest.raises(InvalidFinancialInput):
        analyze_portfolio(PortfolioInput(investments=items))
