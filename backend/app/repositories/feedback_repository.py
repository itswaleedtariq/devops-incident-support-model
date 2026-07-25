"""Feedback repository."""

from __future__ import annotations

from app.models.feedback import Feedback
from app.repositories.base import BaseRepository


class FeedbackRepository(BaseRepository[Feedback]):
    """Data-access operations for the :class:`~app.models.feedback.Feedback` model."""

    model = Feedback
