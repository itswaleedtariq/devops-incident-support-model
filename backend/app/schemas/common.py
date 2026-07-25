"""
Shared pagination and query schemas.
"""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination query parameters used across list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number, 1-based.")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Records per page (max 100).",
    )
    sort_by: str | None = Field(
        default=None,
        description="Column name to sort by (whitelisted by endpoint).",
    )
    sort_order: Literal["asc", "desc"] = Field(
        default="desc",
        description="Sort direction.",
    )
    search: str | None = Field(
        default=None,
        max_length=200,
        description="Free-text search across searchable fields.",
    )

    @property
    def offset(self) -> int:
        """SQL OFFSET calculated from page and page_size."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """SQL LIMIT (alias for page_size)."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard paginated payload wrapped inside ``StandardResponse.data``.
    """

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int
