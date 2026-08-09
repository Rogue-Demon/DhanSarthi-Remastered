"""
DhanSarthi FastAPI application factory.

Exception handlers translate application-level errors into safe HTTP
responses.  No internal database details, SQL text, or credentials are
ever returned to the client.
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import (
    DatabaseError,
    DhanSarthiError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
)
from app.schemas.health import HealthResponse


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


def _register_exception_handlers(application: FastAPI) -> None:
    """Attach application-level exception handlers to *application*."""

    @application.exception_handler(ResourceNotFoundError)
    async def not_found_handler(
        _request: Request, exc: ResourceNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message},
        )

    @application.exception_handler(ResourceAlreadyExistsError)
    async def conflict_handler(
        _request: Request, exc: ResourceAlreadyExistsError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": exc.message},
        )

    @application.exception_handler(DatabaseError)
    async def database_error_handler(
        _request: Request, _exc: DatabaseError
    ) -> JSONResponse:
        # Internal details are already logged inside handle_db_exceptions.
        # Return a generic message so no schema/SQL information leaks.
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "A database error occurred. Please try again later."},
        )

    @application.exception_handler(DhanSarthiError)
    async def application_error_handler(
        _request: Request, exc: DhanSarthiError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_application() -> FastAPI:
    application = FastAPI(title=settings.app_name, version="0.1.0")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    application.include_router(api_router, prefix=settings.api_v1_prefix)
    _register_exception_handlers(application)

    @application.get("/", tags=["root"])
    def root() -> dict[str, str]:
        return {
            "message": (
                "Welcome to DhanSarthi API. "
                "Go to /docs for the API documentation."
            )
        }

    @application.get("/health", response_model=HealthResponse, tags=["health"])
    def health_check() -> HealthResponse:
        """Application liveness check — does not verify the database."""
        return HealthResponse(status="ok")

    @application.get("/health/ready", response_model=HealthResponse, tags=["health"])
    def readiness_check() -> HealthResponse:
        """Database readiness check — verifies connectivity with SELECT 1.

        Returns 200 ``{"status": "ready"}`` when the database is reachable.
        Returns 503 ``{"detail": "Database is unavailable."}`` otherwise.

        Does NOT expose the database URL, credentials, hostname, or SQL text.
        """
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is unavailable.",
            ) from exc
        return HealthResponse(status="ready")

    return application


app = create_application()
