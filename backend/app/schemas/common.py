"""
Common Pydantic schemas for DhanSarthi REST API.

Provides standard pagination envelopes and shared response structures across all endpoints.
"""

from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized pagination response envelope."""

    items: List[T] = Field(..., description="Page items")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total: int = Field(..., description="Total count of records matching filter")
    total_pages: int = Field(..., description="Total number of available pages")
