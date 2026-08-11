"""
Dashboard API router for DhanSarthi — Phase 8.

Provides two authenticated endpoints:
  - GET /api/v1/dashboard            → DashboardResponse  (frontend)
  - GET /api/v1/financial/context    → FinancialContextResponse  (AI / diagnostic)

Both endpoints:
  - Require a valid JWT Bearer token.
  - Derive user identity from the verified token only (no client-supplied user_id).
  - Support optional date_from / date_to query parameters.
  - Default to the last 30 days when no period is specified.

The API layer is intentionally thin — all logic lives in DashboardService.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user_id, get_dashboard_service
from app.schemas.dashboard import DashboardResponse, FinancialContextResponse
from app.services.dashboard_service import DashboardService

# Dashboard endpoints live at their own prefix
dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Financial context endpoint is added to the existing /financial prefix
context_router = APIRouter(prefix="/financial", tags=["financial"])


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard
# ---------------------------------------------------------------------------


@dashboard_router.get("", response_model=DashboardResponse)
def get_dashboard(
    user_id: int = Depends(get_current_user_id),
    service: DashboardService = Depends(get_dashboard_service),
    date_from: Optional[date] = Query(
        default=None,
        description="Start of calculation period (inclusive). Defaults to 30 days before end.",
    ),
    date_to: Optional[date] = Query(
        default=None,
        description="End of calculation period (inclusive). Defaults to today.",
    ),
) -> DashboardResponse:
    """
    Return the consolidated personalized financial dashboard for the authenticated user.

    The response is period-consistent: all flow-based metrics (income, expenses,
    savings, cash flow) use the same date range.  Balance-sheet metrics (assets,
    liabilities, net worth, investments) reflect the current stored values
    regardless of the period.

    Default period: last 30 days ending today.
    """
    return service.build_dashboard(user_id, date_from=date_from, date_to=date_to)


# ---------------------------------------------------------------------------
# GET /api/v1/financial/context
# ---------------------------------------------------------------------------


@context_router.get("/context", response_model=FinancialContextResponse)
def get_financial_context(
    user_id: int = Depends(get_current_user_id),
    service: DashboardService = Depends(get_dashboard_service),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
) -> FinancialContextResponse:
    """
    Return the full machine-readable financial context for the authenticated user.

    Structurally identical to the dashboard response.  Intended for:
      - AI Advisor integration (future — direct service call preferred over HTTP).
      - Diagnostic / debugging use.
      - Frontend supplementary data.

    Future AI services inside the same backend should call
    ``FinancialContextService.build_context()`` directly rather than
    making an HTTP request to this endpoint.
    """
    return service.build_financial_context(user_id, date_from=date_from, date_to=date_to)
