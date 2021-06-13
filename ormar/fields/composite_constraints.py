from typing import Any, List, Optional, TYPE_CHECKING, Type
from sqlalchemy import PrimaryKeyConstraint, ForeignKeyConstraint

import ormar

if TYPE_CHECKING:
    from ormar.models.model import T


class PrimaryKeyConstraint(PrimaryKeyConstraint):
    def __init__(self, *args: str, db_name: str = None, **kwargs: Any):
        # TODO: Resolve names to aliases if ormar names allowed
        self.column_names = args
        self.column_aliases = []
        self.db_name = db_name
        self.owner: Optional[Type["T"]] = None
        self._kwargs = kwargs
        super().__init__(*args, **kwargs)

    def _resolve_column_aliases(self):
        if not self.owner:
            raise ormar.ModelDefinitionError("Cannot resolve aliases without owner")
        for column in self.column_names:
            if self.owner.Meta.model_fields[column].is_relation:
                self.owner.Meta.model_fields[column].nullable = False
                self.owner.__fields__[column].required = True
                self.column_aliases.extend(
                    self.owner.Meta.model_fields[column].to.pk_names_list
                )
            else:
                self.column_aliases.append(self.owner.get_column_alias(column))
        super().__init__(*self.column_aliases, **self._kwargs)


class ForeignKeyConstraint(ForeignKeyConstraint):
    def __init__(
        self,
        to: Type["T"],
        columns: List[str],
        related_columns: List[str],
        name: str = None,
        related_name: str = None,
        db_name: str = None,
        self_reference: bool = False,
        related_orders_by: List[str] = None,
        skip_reverse: bool = False,
        **kwargs: Any,
    ):
        self.to = to
        self.owner = None
        self.ormar_columns = columns
        self.related_columns = related_columns
        self.ormar_name = name or to.get_name()
        self.related_name = related_name
        self.name = db_name
        self.self_reference = self_reference
        self.related_orders_by = related_orders_by
        self.skip_reverse = skip_reverse
        # TODO: Handle ForwardRefs?
        target_table_name = to.Meta.tablename
        related_columns = [f"{target_table_name}.{x}" for x in related_columns]
        super().__init__(
            columns=tuple(columns), refcolumns=related_columns, name=db_name, **kwargs
        )
