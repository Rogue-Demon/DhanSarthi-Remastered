"""
DhanSarthi Financial Engine — Net Worth Module.

Provides deterministic calculation of total assets, total liabilities, liquid vs
illiquid assets breakdown, and net worth balance sheet summary.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Dict

from app.financial.exceptions import InvalidFinancialInput
from app.financial.types import NetWorthInput, NetWorthResult


def calculate_net_worth(input_data: NetWorthInput) -> NetWorthResult:
    """
    Calculate total assets, liquid/illiquid assets, total liabilities, and net worth.

    Formula:
        Net Worth = Total Assets - Total Liabilities

    Args:
        input_data: NetWorthInput payload with lists of assets and liabilities.

    Returns:
        NetWorthResult: Structured balance sheet and net worth metrics.

    Raises:
        InvalidFinancialInput: If asset values or liability balances are negative.
    """
    ref_date = input_data.reference_date or date.today()

    total_assets = Decimal("0")
    liquid_assets = Decimal("0")
    illiquid_assets = Decimal("0")
    assets_by_type: Dict[str, Decimal] = {}

    for asset in input_data.assets:
        if asset.current_value < Decimal("0"):
            raise InvalidFinancialInput(
                f"Asset value cannot be negative: {asset.current_value} for asset '{asset.name}'",
                details={"asset_name": asset.name, "value": str(asset.current_value)},
            )
        val = asset.current_value
        total_assets += val
        if asset.is_liquid:
            liquid_assets += val
        else:
            illiquid_assets += val

        a_type = asset.asset_type.value if hasattr(asset.asset_type, "value") else str(asset.asset_type)
        assets_by_type[a_type] = assets_by_type.get(a_type, Decimal("0")) + val

    total_liabilities = Decimal("0")
    liabilities_by_type: Dict[str, Decimal] = {}

    for liability in input_data.liabilities:
        if liability.outstanding_balance < Decimal("0"):
            raise InvalidFinancialInput(
                f"Liability balance cannot be negative: {liability.outstanding_balance} for '{liability.name}'",
                details={
                    "liability_name": liability.name,
                    "balance": str(liability.outstanding_balance),
                },
            )
        bal = liability.outstanding_balance
        total_liabilities += bal
        l_type = liability.liability_type.value if hasattr(liability.liability_type, "value") else str(liability.liability_type)
        liabilities_by_type[l_type] = liabilities_by_type.get(l_type, Decimal("0")) + bal

    net_worth = total_assets - total_liabilities

    return NetWorthResult(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=net_worth,
        liquid_assets=liquid_assets,
        illiquid_assets=illiquid_assets,
        assets_by_type=assets_by_type,
        liabilities_by_type=liabilities_by_type,
        reference_date=ref_date,
    )
