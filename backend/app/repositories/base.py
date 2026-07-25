"""
Generic base repository.

Provides a reusable async CRUD layer with pagination, filtering, sorting,
search, bulk operations, and soft-delete support.  Subclasses parameterise
by their concrete model and expose model-specific query helpers.

Repositories MUST NOT contain business logic — that belongs to the service
layer.  Repositories only translate service intent into SQL.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import Select, and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.logging import get_logger

logger = get_logger("repositories.base")

#: Type variable bound to any SQLAlchemy declarative model.
ModelT = TypeVar("ModelT", bound=DeclarativeBase)


class BaseRepository(Generic[ModelT]):
    """
    Generic async repository over a single SQLAlchemy model.

    Subclasses provide the ``model`` class attribute::

        class UserRepository(BaseRepository[User]):
            model = User
    """

    #: The SQLAlchemy model class the repository operates on.
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(self, **fields: Any) -> ModelT:
        """Insert a new record built from *fields* and return it."""
        instance = self.model(**fields)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def add(self, instance: ModelT) -> ModelT:
        """Add an already-constructed *instance* to the session."""
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def bulk_create(self, items: Sequence[dict[str, Any]]) -> list[ModelT]:
        """Insert multiple records in a single flush."""
        instances = [self.model(**item) for item in items]
        self.session.add_all(instances)
        await self.session.flush()
        return instances

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get(self, id_: uuid.UUID) -> ModelT | None:
        """Return the record with primary key *id_* or ``None``."""
        return await self.session.get(self.model, id_)

    async def get_or_raise(self, id_: uuid.UUID) -> ModelT:
        """Return the record with primary key *id_* or raise :class:`LookupError`."""
        obj = await self.get(id_)
        if obj is None:
            raise LookupError(
                f"{self.model.__name__} with id={id_} not found."
            )
        return obj

    async def exists(self, **filters: Any) -> bool:
        """Return ``True`` if at least one row matches *filters*."""
        stmt = select(func.count()).select_from(self.model)
        stmt = self._apply_filters(stmt, filters)
        result = await self.session.execute(stmt)
        return (result.scalar_one() or 0) > 0

    async def count(self, **filters: Any) -> int:
        """Return the number of rows matching *filters*."""
        stmt = select(func.count()).select_from(self.model)
        stmt = self._apply_filters(stmt, filters)
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def find_all(self, **filters: Any) -> list[ModelT]:
        """Return every row matching *filters* (no pagination)."""
        stmt = select(self.model)
        stmt = self._apply_filters(stmt, filters)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_one(self, **filters: Any) -> ModelT | None:
        """Return the first row matching *filters* or ``None``."""
        stmt = select(self.model).limit(1)
        stmt = self._apply_filters(stmt, filters)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def paginate(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        sort_by: str | None = None,
        sort_order: str = "desc",
        search: str | None = None,
        search_fields: Sequence[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[ModelT], int]:
        """
        Return ``(items, total)`` for the current page.

        Args:
            offset:        SQL OFFSET (rows to skip).
            limit:         SQL LIMIT (rows per page).
            sort_by:       Column name to sort by; must be a real column.
            sort_order:    ``"asc"`` or ``"desc"``.
            search:        Text to search across *search_fields*.
            search_fields: Columns searched with ILIKE (case-insensitive).
            filters:       Extra ``column == value`` filters.
        """
        stmt: Select = select(self.model)
        count_stmt: Select = select(func.count()).select_from(self.model)

        if filters:
            stmt = self._apply_filters(stmt, filters)
            count_stmt = self._apply_filters(count_stmt, filters)

        if search and search_fields:
            like = f"%{search}%"
            search_clauses = [
                getattr(self.model, f).ilike(like) for f in search_fields
                if hasattr(self.model, f)
            ]
            if search_clauses:
                stmt = stmt.where(or_(*search_clauses))
                count_stmt = count_stmt.where(or_(*search_clauses))

        if sort_by and hasattr(self.model, sort_by):
            col = getattr(self.model, sort_by)
            stmt = stmt.order_by(col.desc() if sort_order == "desc" else col.asc())

        stmt = stmt.offset(offset).limit(limit)

        items_result = await self.session.execute(stmt)
        items = list(items_result.scalars().all())

        total_result = await self.session.execute(count_stmt)
        total = int(total_result.scalar_one() or 0)

        return items, total

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update(self, instance: ModelT, **fields: Any) -> ModelT:
        """Apply *fields* to *instance* and flush."""
        for key, value in fields.items():
            setattr(instance, key, value)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def bulk_update(
        self, filters: dict[str, Any], values: dict[str, Any]
    ) -> int:
        """
        Bulk-update all rows matching *filters* with *values*.

        Returns the number of rows updated.
        """
        stmt = update(self.model).values(**values)
        stmt = self._apply_filters(stmt, filters)
        result = await self.session.execute(stmt)
        return int(result.rowcount or 0)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(self, instance: ModelT) -> None:
        """Physically delete *instance* from the database."""
        await self.session.delete(instance)
        await self.session.flush()

    async def delete_by_id(self, id_: uuid.UUID) -> bool:
        """Physically delete the record with primary key *id_*.  Returns success."""
        stmt = delete(self.model).where(self.model.id == id_)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return (result.rowcount or 0) > 0

    async def soft_delete(self, instance: ModelT) -> ModelT:
        """
        Mark *instance* as deleted using the soft-delete mixin columns.

        Raises :class:`AttributeError` if the model does not use ``SoftDeleteMixin``.
        """
        if not hasattr(instance, "is_deleted"):
            raise AttributeError(
                f"{self.model.__name__} does not support soft-delete "
                "(missing SoftDeleteMixin)."
            )
        instance.is_deleted = True  # type: ignore[attr-defined]
        instance.deleted_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
        self.session.add(instance)
        await self.session.flush()
        return instance

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply_filters(self, stmt, filters: dict[str, Any]):
        """Apply ``column == value`` filters, ignoring unknown columns."""
        if not filters:
            return stmt
        clauses = []
        for key, value in filters.items():
            if hasattr(self.model, key):
                clauses.append(getattr(self.model, key) == value)
        if clauses:
            stmt = stmt.where(and_(*clauses))
        return stmt
