"""API v1 router — registers all domain routers under /api/v1/."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.profile import router as profile_router
from app.api.v1.income import router as income_router
from app.api.v1.expenses import router as expenses_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.assets import router as assets_router
from app.api.v1.liabilities import router as liabilities_router
from app.api.v1.investments import router as investments_router
from app.api.v1.loans import router as loans_router
from app.api.v1.goals import router as goals_router
from app.api.v1.budgets import router as budgets_router
from app.api.v1.financial import router as financial_router
from app.api.v1.dashboard import dashboard_router, context_router
from app.api.v1.ai import router as ai_router
from app.api.v1.documents import router as documents_router
from app.api.v1.financial_intelligence import router as financial_intelligence_router
from app.api.v1.market import router as market_router
from app.api.v1.reports import router as reports_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(profile_router)
api_router.include_router(income_router)
api_router.include_router(expenses_router)
api_router.include_router(transactions_router)
api_router.include_router(assets_router)
api_router.include_router(liabilities_router)
api_router.include_router(investments_router)
api_router.include_router(loans_router)
api_router.include_router(goals_router)
api_router.include_router(budgets_router)
api_router.include_router(financial_router)
api_router.include_router(dashboard_router)
api_router.include_router(context_router)
api_router.include_router(ai_router)
api_router.include_router(documents_router)
api_router.include_router(financial_intelligence_router)
api_router.include_router(market_router)
api_router.include_router(reports_router)


