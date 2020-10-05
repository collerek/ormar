from ormar.exceptions import ModelDefinitionError, ModelNotSet, MultipleMatches, NoMatch
from ormar.fields import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Decimal,
    Float,
    ForeignKey,
    Integer,
    JSON,
    ManyToMany,
    String,
    Text,
    Time,
    UUID,
    UniqueColumns,
)
from ormar.models import Model
from ormar.queryset import QuerySet
from ormar.relations import RelationType


class UndefinedType:  # pragma no cover
    def __repr__(self) -> str:
        return "OrmarUndefined"


Undefined = UndefinedType()

__version__ = "0.3.6"
__all__ = [
    "Integer",
    "BigInteger",
    "Boolean",
    "Time",
    "Text",
    "String",
    "JSON",
    "DateTime",
    "Date",
    "Decimal",
    "Float",
    "ManyToMany",
    "Model",
    "ModelDefinitionError",
    "ModelNotSet",
    "MultipleMatches",
    "NoMatch",
    "ForeignKey",
    "QuerySet",
    "RelationType",
    "Undefined",
    "UUID",
    "UniqueColumns",
]
