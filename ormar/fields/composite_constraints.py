from typing import Any, List, TYPE_CHECKING, Type
from sqlalchemy import PrimaryKeyConstraint, ForeignKeyConstraint

if TYPE_CHECKING:
    from ormar.models.model import T


class PrimaryKeyConstraint(PrimaryKeyConstraint):
    def __init__(self, *args: str, db_name: str = None, **kwargs: Any):
        self.column_names = args
        self.db_name = db_name
        super().__init__(*args, **kwargs)


class ForeignKeyConstraint(ForeignKeyConstraint):
    def __init__(
        self,
        to: Type["T"],
        columns: List[str],
        related_columns: List[str],
        name: str = None,
        related_name: str = None,
        db_name: str = None,
        **kwargs: Any,
    ):
        self.to = to
        self.columns = columns
        self.related_columns = related_columns
        self.name = name
        self.related_name = related_name
        self.db_name = db_name
        # TODO: Handle ForwardRefs?
        target_table_name = to.Meta.tablename
        related_columns = [f"{target_table_name}.{x}" for x in related_columns]
        super().__init__(
            columns=tuple(columns), refcolumns=related_columns, name=db_name, **kwargs
        )
