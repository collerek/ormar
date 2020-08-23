import json
import uuid
from typing import (
    AbstractSet,
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    TYPE_CHECKING,
    Type,
    TypeVar,
    Union,
)

import databases
import pydantic
import sqlalchemy
from pydantic import BaseModel

import ormar  # noqa I100
from ormar.fields import BaseField
from ormar.models.metaclass import ModelMeta, ModelMetaclass
from ormar.models.modelproxy import ModelTableProxy
from ormar.relations import RelationshipManager

if TYPE_CHECKING:  # pragma no cover
    from ormar.models.model import Model

    IntStr = Union[int, str]
    DictStrAny = Dict[str, Any]
    AbstractSetIntStr = AbstractSet[IntStr]
    MappingIntStrAny = Mapping[IntStr, Any]


class NewBaseModel(pydantic.BaseModel, ModelTableProxy, metaclass=ModelMetaclass):
    __slots__ = ("_orm_id", "_orm_saved")

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
        Meta: ModelMeta

    # noinspection PyMissingConstructor
    def __init__(self, *args: Any, **kwargs: Any) -> None:

        object.__setattr__(self, "_orm_id", uuid.uuid4().hex)
        object.__setattr__(self, "_orm_saved", False)

        pk_only = kwargs.pop("__pk_only__", False)
        if "pk" in kwargs:
            kwargs[self.Meta.pkname] = kwargs.pop("pk")
        kwargs = {
            k: self._convert_json(
                k, self.Meta.model_fields[k].expand_relationship(v, self), "dumps"
            )
            for k, v in kwargs.items()
        }

        values, fields_set, validation_error = pydantic.validate_model(self, kwargs)
        if validation_error and not pk_only:
            raise validation_error

        object.__setattr__(self, "__dict__", values)
        object.__setattr__(self, "__fields_set__", fields_set)

    def __del__(self) -> None:
        self.Meta._orm_relationship_manager.deregister(self)

    def __setattr__(self, name: str, value: Any) -> None:
        relation_key = self.get_name(title=True) + "_" + name
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        elif name == "pk":
            object.__setattr__(self, self.Meta.pkname, value)
        elif self.Meta._orm_relationship_manager.contains(relation_key, self):
            self.Meta.model_fields[name].expand_relationship(value, self)
        else:
            value = (
                self._convert_json(name, value, "dumps")
                if name in self.__fields__
                else value
            )
            super().__setattr__(name, value)

    def __getattribute__(self, item: str) -> Any:
        if item != "__fields__" and item in self.__fields__:
            related = self._extract_related_model_instead_of_field(item)
            if related:
                return related
            value = object.__getattribute__(self, item)
            value = self._convert_json(item, value, "loads")
            return value
        return super().__getattribute__(item)

    def __getattr__(self, item: str) -> Optional[Union["Model", List["Model"]]]:
        return self._extract_related_model_instead_of_field(item)

    def _extract_related_model_instead_of_field(
        self, item: str
    ) -> Optional[Union["Model", List["Model"]]]:
        relation_key = self.get_name(title=True) + "_" + item
        if self.Meta._orm_relationship_manager.contains(relation_key, self):
            return self.Meta._orm_relationship_manager.get(relation_key, self)

    def __same__(self, other: "Model") -> bool:
        if self.__class__ != other.__class__:  # pragma no cover
            return False
        return (
            self._orm_id == other._orm_id
            or self.__dict__ == other.__dict__
            or (self.pk == other.pk and self.pk is not None)
        )

    @classmethod
    def get_name(cls, title: bool = False, lower: bool = True) -> str:
        name = cls.__name__
        if lower:
            name = name.lower()
        if title:
            name = name.title()
        return name

    @property
    def pk(self) -> Any:
        return getattr(self, self.Meta.pkname)

    @property
    def pk_column(self) -> sqlalchemy.Column:
        return self.Meta.table.primary_key.columns.values()[0]

    @classmethod
    def pk_type(cls) -> Any:
        return cls.Meta.model_fields[cls.Meta.pkname].__type__

    def dict(  # noqa A003
        self,
        *,
        include: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        exclude: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        nested: bool = False
    ) -> "DictStrAny":  # noqa: A003'
        dict_instance = super().dict(
            include=include,
            exclude=self._exclude_related_names_not_required(nested),
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        for field in self._extract_related_names():
            nested_model = getattr(self, field)

            if self.Meta.model_fields[field].virtual and nested:
                continue
            if isinstance(nested_model, list):
                dict_instance[field] = [x.dict(nested=True) for x in nested_model]
            elif nested_model is not None:
                dict_instance[field] = nested_model.dict(nested=True)
        return dict_instance

    def from_dict(self, value_dict: Dict) -> None:
        for key, value in value_dict.items():
            setattr(self, key, value)

    def _convert_json(self, column_name: str, value: Any, op: str) -> Union[str, dict]:

        if not self._is_conversion_to_json_needed(column_name):
            return value

        condition = (
            isinstance(value, str) if op == "loads" else not isinstance(value, str)
        )
        operand = json.loads if op == "loads" else json.dumps

        if condition:
            try:
                return operand(value)
            except TypeError:  # pragma no cover
                pass
        return value

    def _is_conversion_to_json_needed(self, column_name: str) -> bool:
        return self.Meta.model_fields.get(column_name).__type__ == pydantic.Json
