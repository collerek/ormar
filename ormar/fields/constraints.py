from typing import Any, Optional

from sqlalchemy import CheckConstraint, Index, UniqueConstraint


class UniqueColumns(UniqueConstraint):
    """
    Subclass of sqlalchemy.UniqueConstraint.
    Used to avoid importing anything from sqlalchemy by user.
    """


class IndexColumns(Index):
    def __init__(self, *args: Any, name: Optional[str] = None, **kw: Any) -> None:
        if not name:
            name = "TEMPORARY_NAME"
        super().__init__(name, *args, **kw)

    """
    Subclass of sqlalchemy.Index.
    Used to avoid importing anything from sqlalchemy by user.
    """


class CheckColumns(CheckConstraint):
    """
    Subclass of sqlalchemy.CheckConstraint.
    Used to avoid importing anything from sqlalchemy by user.

    Note that some databases do not actively support check constraints such as MySQL.
    """
