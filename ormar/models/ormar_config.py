from typing import TYPE_CHECKING, Dict, List, Optional, Set, Type, Union

import databases
import sqlalchemy
from sqlalchemy.sql.schema import ColumnCollectionConstraint

from ormar.fields import BaseField, ForeignKeyField, ManyToManyField
from ormar.models.helpers import alias_manager
from ormar.models.utils import Extra
from ormar.queryset.queryset import QuerySet
from ormar.relations import AliasManager
from ormar.signals import SignalEmitter


class OrmarConfig:

    if TYPE_CHECKING:  # pragma: no cover
        pkname: str
        metadata: sqlalchemy.MetaData
        database: databases.Database
        tablename: str
        order_by: List[str]
        abstract: bool
        exclude_parent_fields: List[str]
        constraints: List[ColumnCollectionConstraint]

    def __init__(
        self,
        metadata: Optional[sqlalchemy.MetaData] = None,
        database: Optional[databases.Database] = None,
        engine: Optional[sqlalchemy.engine.Engine] = None,
        tablename: Optional[str] = None,
        order_by: Optional[List[str]] = None,
        abstract: bool = False,
        exclude_parent_fields: Optional[List[str]] = None,
        queryset_class: Type[QuerySet] = QuerySet,
        extra: Extra = Extra.forbid,
        constraints: Optional[List[ColumnCollectionConstraint]] = None,
    ) -> None:
        self.pkname = None  # type: ignore
        self.metadata = metadata
        self.database = database  # type: ignore
        self.engine = engine  # type: ignore
        self.tablename = tablename  # type: ignore
        self.orders_by = order_by or []
        self.columns: List[sqlalchemy.Column] = []
        self.constraints = constraints or []
        self.model_fields: Dict[
            str, Union[BaseField, ForeignKeyField, ManyToManyField]
        ] = {}
        self.alias_manager: AliasManager = alias_manager
        self.property_fields: Set = set()
        self.signals: SignalEmitter = SignalEmitter()
        self.abstract = abstract
        self.requires_ref_update: bool = False
        self.exclude_parent_fields = exclude_parent_fields or []
        self.extra = extra
        self.queryset_class = queryset_class
        self.table: sqlalchemy.Table = None

    def copy(
        self,
        metadata: Optional[sqlalchemy.MetaData] = None,
        database: Optional[databases.Database] = None,
        engine: Optional[sqlalchemy.engine.Engine] = None,
        tablename: Optional[str] = None,
        order_by: Optional[List[str]] = None,
        abstract: Optional[bool] = None,
        exclude_parent_fields: Optional[List[str]] = None,
        queryset_class: Optional[Type[QuerySet]] = None,
        extra: Optional[Extra] = None,
        constraints: Optional[List[ColumnCollectionConstraint]] = None,
    ) -> "OrmarConfig":
        return OrmarConfig(
            metadata=metadata or self.metadata,
            database=database or self.database,
            engine=engine or self.engine,
            tablename=tablename,
            order_by=order_by,
            abstract=abstract or self.abstract,
            exclude_parent_fields=exclude_parent_fields,
            queryset_class=queryset_class or self.queryset_class,
            extra=extra or self.extra,
            constraints=constraints,
        )
