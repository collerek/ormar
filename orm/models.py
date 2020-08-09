import copy
import inspect
import json
import uuid
from typing import Any, List, Optional, TYPE_CHECKING, Tuple, Type, TypeVar
from typing import Callable, Dict, Set

import databases

import orm.queryset as qry
from orm.exceptions import ModelDefinitionError
from orm.fields import BaseField, ForeignKey
from orm.relations import RelationshipManager

import pydantic
from pydantic import BaseConfig, BaseModel, create_model

import sqlalchemy

relationship_manager = RelationshipManager()


def parse_pydantic_field_from_model_fields(object_dict: dict) -> Dict[str, Tuple]:
    pydantic_fields = {
        field_name: (
            base_field.__type__,
            ... if base_field.is_required else base_field.default_value,
        )
        for field_name, base_field in object_dict.items()
        if isinstance(base_field, BaseField)
    }
    return pydantic_fields


def register_relation_on_build(table_name: str, field: ForeignKey, name: str) -> None:
    child_relation_name = field.to.get_name(title=True) + "_" + name.lower() + "s"
    reverse_name = field.related_name or child_relation_name
    relation_name = name.lower().title() + "_" + field.to.get_name()
    relationship_manager.add_relation_type(
        relation_name, reverse_name, field, table_name
    )


def sqlalchemy_columns_from_model_fields(
    name: str, object_dict: Dict, table_name: str
) -> Tuple[Optional[str], List[sqlalchemy.Column], Dict[str, BaseField]]:
    pkname: Optional[str] = None
    columns: List[sqlalchemy.Column] = []
    model_fields: Dict[str, BaseField] = {}

    for field_name, field in object_dict.items():
        if isinstance(field, BaseField):
            model_fields[field_name] = field
            if not field.pydantic_only:
                if field.primary_key:
                    pkname = field_name
                if isinstance(field, ForeignKey):
                    register_relation_on_build(table_name, field, name)
                columns.append(field.get_column(field_name))
    return pkname, columns, model_fields


def get_pydantic_base_orm_config() -> Type[BaseConfig]:
    class Config(BaseConfig):
        orm_mode = True

    return Config


class ModelMetaclass(type):
    def __new__(mcs: type, name: str, bases: Any, attrs: dict) -> type:
        new_model = super().__new__(  # type: ignore
            mcs, name, bases, attrs
        )

        if attrs.get("__abstract__"):
            return new_model

        tablename = attrs["__tablename__"]
        metadata = attrs["__metadata__"]

        # sqlalchemy table creation
        pkname, columns, model_fields = sqlalchemy_columns_from_model_fields(
            name, attrs, tablename
        )
        attrs["__table__"] = sqlalchemy.Table(tablename, metadata, *columns)
        attrs["__columns__"] = columns
        attrs["__pkname__"] = pkname

        if not pkname:
            raise ModelDefinitionError("Table has to have a primary key.")

        # pydantic model creation
        pydantic_fields = parse_pydantic_field_from_model_fields(attrs)
        pydantic_model = create_model(
            name, __config__=get_pydantic_base_orm_config(), **pydantic_fields
        )
        attrs["__pydantic_fields__"] = pydantic_fields
        attrs["__pydantic_model__"] = pydantic_model
        attrs["__fields__"] = copy.deepcopy(pydantic_model.__fields__)
        attrs["__signature__"] = copy.deepcopy(pydantic_model.__signature__)
        attrs["__annotations__"] = copy.deepcopy(pydantic_model.__annotations__)
        attrs["__model_fields__"] = model_fields

        attrs["_orm_relationship_manager"] = relationship_manager

        new_model = super().__new__(  # type: ignore
            mcs, name, bases, attrs
        )

        return new_model


class FakePydantic(list, metaclass=ModelMetaclass):
    # FakePydantic inherits from list in order to be treated as
    # request.Body parameter in fastapi routes,
    # inheriting from pydantic.BaseModel causes metaclass conflicts
    __abstract__ = True
    if TYPE_CHECKING:  # pragma no cover
        __model_fields__: Dict[str, TypeVar[BaseField]]
        __table__: sqlalchemy.Table
        __fields__: Dict[str, pydantic.fields.ModelField]
        __pydantic_model__: Type[BaseModel]
        __pkname__: str
        __tablename__: str
        __metadata__: sqlalchemy.MetaData
        __database__: databases.Database
        _orm_relationship_manager: RelationshipManager

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._orm_id: str = uuid.uuid4().hex
        self._orm_saved: bool = False
        self.values: Optional[BaseModel] = None

        if "pk" in kwargs:
            kwargs[self.__pkname__] = kwargs.pop("pk")
        kwargs = {
            k: self.__model_fields__[k].expand_relationship(v, self)
            for k, v in kwargs.items()
        }
        self.values = self.__pydantic_model__(**kwargs)

    def __del__(self) -> None:
        self._orm_relationship_manager.deregister(self)

    def __setattr__(self, key: str, value: Any) -> None:
        if key in self.__fields__:
            if self._is_conversion_to_json_needed(key) and not isinstance(value, str):
                try:
                    value = json.dumps(value)
                except TypeError:  # pragma no cover
                    pass

            value = self.__model_fields__[key].expand_relationship(value, self)

            relation_key = self.__class__.__name__.title() + "_" + key
            if not self._orm_relationship_manager.contains(relation_key, self):
                setattr(self.values, key, value)
        else:
            super().__setattr__(key, value)

    def __getattribute__(self, key: str) -> Any:
        if key != "__fields__" and key in self.__fields__:
            relation_key = self.__class__.__name__.title() + "_" + key
            if self._orm_relationship_manager.contains(relation_key, self):
                return self._orm_relationship_manager.get(relation_key, self)

            item = getattr(self.values, key, None)
            if (
                item is not None
                and self._is_conversion_to_json_needed(key)
                and isinstance(item, str)
            ):
                try:
                    item = json.loads(item)
                except TypeError:  # pragma no cover
                    pass
            return item
        return super().__getattribute__(key)

    def __eq__(self, other: "Model") -> bool:
        return self.values.dict() == other.values.dict()

    def __same__(self, other: "Model") -> bool:
        if self.__class__ != other.__class__:  # pragma no cover
            return False
        return self._orm_id == other._orm_id or (
            self.values is not None and other.values is not None and self.pk == other.pk
        )

    def __repr__(self) -> str:  # pragma no cover
        return self.values.__repr__()

    @classmethod
    def __get_validators__(cls) -> Callable:  # pragma no cover
        yield cls.__pydantic_model__.validate

    @classmethod
    def get_name(cls, title: bool = False, lower: bool = True) -> str:
        name = cls.__name__
        if lower:
            name = name.lower()
        if title:
            name = name.title()
        return name

    @property
    def pk_column(self) -> sqlalchemy.Column:
        return self.__table__.primary_key.columns.values()[0]

    @classmethod
    def pk_type(cls):
        return cls.__model_fields__[cls.__pkname__].__type__

    def dict(self) -> Dict:  # noqa: A003
        dict_instance = self.values.dict()
        for field in self._extract_related_names():
            nested_model = getattr(self, field)
            if isinstance(nested_model, list):
                dict_instance[field] = [x.dict() for x in nested_model]
            else:
                dict_instance[field] = (
                    nested_model.dict() if nested_model is not None else {}
                )
        return dict_instance

    def from_dict(self, value_dict: Dict) -> None:
        for key, value in value_dict.items():
            setattr(self, key, value)

    def _is_conversion_to_json_needed(self, column_name: str) -> bool:
        return self.__model_fields__.get(column_name).__type__ == pydantic.Json

    def _extract_own_model_fields(self) -> Dict:
        related_names = self._extract_related_names()
        self_fields = {k: v for k, v in self.dict().items() if k not in related_names}
        return self_fields

    @classmethod
    def _extract_related_names(cls) -> Set:
        related_names = set()
        for name, field in cls.__fields__.items():
            if inspect.isclass(field.type_) and issubclass(
                field.type_, pydantic.BaseModel
            ):
                related_names.add(name)
        return related_names

    def _extract_model_db_fields(self) -> Dict:
        self_fields = self._extract_own_model_fields()
        self_fields = {
            k: v for k, v in self_fields.items() if k in self.__table__.columns
        }
        for field in self._extract_related_names():
            if getattr(self, field) is not None:
                self_fields[field] = getattr(
                    getattr(self, field), self.__model_fields__[field].to.__pkname__
                )
        return self_fields


class Model(FakePydantic):
    __abstract__ = True

    objects = qry.QuerySet()

    @classmethod
    def from_row(
        cls,
        row: sqlalchemy.engine.ResultProxy,
        select_related: List = None,
        previous_table: str = None,
    ) -> "Model":

        item = {}
        select_related = select_related or []

        table_prefix = cls._orm_relationship_manager.resolve_relation_join(
            previous_table, cls.__table__.name
        )
        previous_table = cls.__table__.name
        for related in select_related:
            if "__" in related:
                first_part, remainder = related.split("__", 1)
                model_cls = cls.__model_fields__[first_part].to
                child = model_cls.from_row(
                    row, select_related=[remainder], previous_table=previous_table
                )
                item[first_part] = child
            else:
                model_cls = cls.__model_fields__[related].to
                child = model_cls.from_row(row, previous_table=previous_table)
                item[related] = child

        for column in cls.__table__.columns:
            if column.name not in item:
                item[column.name] = row[
                    f'{table_prefix + "_" if table_prefix else ""}{column.name}'
                ]

        return cls(**item)

    @property
    def pk(self) -> str:
        return getattr(self.values, self.__pkname__)

    @pk.setter
    def pk(self, value: Any) -> None:
        setattr(self.values, self.__pkname__, value)

    async def save(self) -> int:
        self_fields = self._extract_model_db_fields()
        if self.__model_fields__.get(self.__pkname__).autoincrement:
            self_fields.pop(self.__pkname__, None)
        expr = self.__table__.insert()
        expr = expr.values(**self_fields)
        item_id = await self.__database__.execute(expr)
        self.pk = item_id
        return item_id

    async def update(self, **kwargs: Any) -> int:
        if kwargs:
            new_values = {**self.dict(), **kwargs}
            self.from_dict(new_values)

        self_fields = self._extract_model_db_fields()
        self_fields.pop(self.__pkname__)
        expr = (
            self.__table__.update()
            .values(**self_fields)
            .where(self.pk_column == getattr(self, self.__pkname__))
        )
        result = await self.__database__.execute(expr)
        return result

    async def delete(self) -> int:
        expr = self.__table__.delete()
        expr = expr.where(self.pk_column == (getattr(self, self.__pkname__)))
        result = await self.__database__.execute(expr)
        return result

    async def load(self) -> "Model":
        expr = self.__table__.select().where(self.pk_column == self.pk)
        row = await self.__database__.fetch_one(expr)
        self.from_dict(dict(row))
        return self
