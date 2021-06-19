from typing import Any, List, Optional, TYPE_CHECKING, Type

import sqlalchemy

import ormar

if TYPE_CHECKING:
    from ormar.models.model import T


class PrimaryKeyConstraint(sqlalchemy.PrimaryKeyConstraint):
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
            column_name = self.owner.get_column_name_from_alias(column)
            if (
                self.owner.Meta.model_fields.get(column_name)
                and self.owner.Meta.model_fields.get(column_name).is_relation
            ):
                self.owner.Meta.model_fields[column_name].nullable = False
                self.owner.__fields__[column_name].required = True
                self.column_aliases.append(column)
            else:
                self.owner.Meta.model_fields[column_name].nullable = False
                self.owner.__fields__[column_name].required = True
                self.column_aliases.append(column)
        super().__init__(*self.column_aliases, **self._kwargs)


class ForeignKeyConstraint(sqlalchemy.ForeignKeyConstraint):
    def __init__(
        self, to: Type["T"], columns: List[str], **kwargs: Any,
    ):
        # TODO: Handle ForwardRefs?
        target_table_name = to.Meta.tablename
        related_columns = [f"{target_table_name}.{x}" for x in to.pk_aliases_list]
        super().__init__(columns=tuple(columns), refcolumns=related_columns, **kwargs)
