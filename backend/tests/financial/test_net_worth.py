"""Tests for Net Worth calculation module."""

from decimal import Decimal

import pytest

from app.financial import (
    AssetItemInput,
    InvalidFinancialInput,
    LiabilityItemInput,
    NetWorthInput,
    calculate_net_worth,
)
from app.models.enums import AssetType, LiabilityType


def test_net_worth_positive():
    assets = [
        AssetItemInput(name="Cash", asset_type=AssetType.CASH, current_value=Decimal("50000"), is_liquid=True),
        AssetItemInput(name="Flat", asset_type=AssetType.PROPERTY, current_value=Decimal("5000000"), is_liquid=False),
    ]
    liabilities = [
        LiabilityItemInput(name="Home Loan", liability_type=LiabilityType.HOME_LOAN, outstanding_balance=Decimal("3000000")),
    ]
    inp = NetWorthInput(assets=assets, liabilities=liabilities)
    res = calculate_net_worth(inp)

    assert res.total_assets == Decimal("5050000")
    assert res.total_liabilities == Decimal("3000000")
    assert res.net_worth == Decimal("2050000")
    assert res.liquid_assets == Decimal("50000")
    assert res.illiquid_assets == Decimal("5000000")
    assert res.assets_by_type["CASH"] == Decimal("50000")
    assert res.assets_by_type["PROPERTY"] == Decimal("5000000")
    assert res.liabilities_by_type["HOME_LOAN"] == Decimal("3000000")


def test_net_worth_negative():
    assets = [AssetItemInput(name="Bank", asset_type=AssetType.BANK_BALANCE, current_value=Decimal("10000"), is_liquid=True)]
    liabilities = [LiabilityItemInput(name="Credit Card", liability_type=LiabilityType.CREDIT_CARD, outstanding_balance=Decimal("50000"))]
    res = calculate_net_worth(NetWorthInput(assets=assets, liabilities=liabilities))

    assert res.net_worth == Decimal("-40000")


def test_net_worth_empty():
    res = calculate_net_worth(NetWorthInput())
    assert res.total_assets == Decimal("0")
    assert res.total_liabilities == Decimal("0")
    assert res.net_worth == Decimal("0")


def test_net_worth_negative_asset_raises_error():
    assets = [AssetItemInput(name="Bad Asset", asset_type=AssetType.OTHER, current_value=Decimal("-500"))]
    with pytest.raises(InvalidFinancialInput):
        calculate_net_worth(NetWorthInput(assets=assets))


def test_net_worth_negative_liability_raises_error():
    liabilities = [LiabilityItemInput(name="Bad Debt", liability_type=LiabilityType.OTHER, outstanding_balance=Decimal("-500"))]
    with pytest.raises(InvalidFinancialInput):
        calculate_net_worth(NetWorthInput(liabilities=liabilities))
