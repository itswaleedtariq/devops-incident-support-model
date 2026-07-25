"""
Models package base — convenience re-export.

Model modules import ``Base`` from here instead of reaching into the
``database`` sub-package, keeping the import surface clean:

    from app.models.base import Base   # preferred in model files
"""

from app.database.base import Base

__all__ = ["Base"]
