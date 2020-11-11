import json
import uuid
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
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
from ormar.fields.foreign_key import ForeignKeyField
from ormar.models.metaclass import ModelMeta, ModelMetaclass
from ormar.models.modelproxy import ModelTableProxy
from ormar.relations.alias_manager import AliasManager
from ormar.relations.relation_manager import RelationsManager

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model

    T = TypeVar("T", bound=Model)

    IntStr = Union[int, str]
    DictStrAny = Dict[str, Any]
    AbstractSetIntStr = AbstractSet[IntStr]
    MappingIntStrAny = Mapping[IntStr, Any]


class NewBaseModel(pydantic.BaseModel, ModelTableProxy, metaclass=ModelMetaclass):
    __slots__ = ("_orm_id", "_orm_saved", "_orm")

    if TYPE_CHECKING:  # pragma no cover
        __model_fields__: Dict[str, Type[BaseField]]
        __table__: sqlalchemy.Table
        __fields__: Dict[str, pydantic.fields.ModelField]
        __pydantic_model__: Type[BaseModel]
        __pkname__: str
        __tablename__: str
        __metadata__: sqlalchemy.MetaData
        __database__: databases.Database
        _orm_relationship_manager: AliasManager
        _orm: RelationsManager
        Meta: ModelMeta

    # noinspection PyMissingConstructor
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # type: ignore

        object.__setattr__(self, "_orm_id", uuid.uuid4().hex)
        object.__setattr__(self, "_orm_saved", False)
        object.__setattr__(
            self,
            "_orm",
            RelationsManager(
                related_fields=[
                    field
                    for name, field in self.Meta.model_fields.items()
                    if issubclass(field, ForeignKeyField)
                ],
                owner=self,
            ),
        )

        pk_only = kwargs.pop("__pk_only__", False)
        if "pk" in kwargs:
            kwargs[self.Meta.pkname] = kwargs.pop("pk")
        # build the models to set them and validate but don't register
        new_kwargs = {
            k: self._convert_json(
                k,
                self.Meta.model_fields[k].expand_relationship(
                    v, self, to_register=False
                ),
                "dumps",
            )
            for k, v in kwargs.items()
        }

        values, fields_set, validation_error = pydantic.validate_model(
            self, new_kwargs  # type: ignore
        )
        if validation_error and not pk_only:
            raise validation_error

        object.__setattr__(self, "__dict__", values)
        object.__setattr__(self, "__fields_set__", fields_set)

        # register the columns models after initialization
        for related in self.extract_related_names():
            self.Meta.model_fields[related].expand_relationship(
                new_kwargs.get(related), self, to_register=True
            )

    def __setattr__(self, name: str, value: Any) -> None:  # noqa CCR001
        if name in ("_orm_id", "_orm_saved", "_orm"):
            object.__setattr__(self, name, value)
        elif name == "pk":
            object.__setattr__(self, self.Meta.pkname, value)
        elif name in self._orm:
            model = self.Meta.model_fields[name].expand_relationship(value, self)
            if isinstance(self.__dict__.get(name), list):
                self.__dict__[name].append(model)
            else:
                self.__dict__[name] = model
        else:
            value = (
                self._convert_json(name, value, "dumps")
                if name in self.__fields__
                else value
            )
            super().__setattr__(name, value)

    def __getattribute__(self, item: str) -> Any:
        if item in ("_orm_id", "_orm_saved", "_orm", "__fields__"):
            return object.__getattribute__(self, item)
        if item != "extract_related_names" and item in self.extract_related_names():
            return self._extract_related_model_instead_of_field(item)
        if item == "pk":
            return self.__dict__.get(self.Meta.pkname, None)
        if item != "__fields__" and item in self.__fields__:
            value = self.__dict__.get(item, None)
            value = self._convert_json(item, value, "loads")
            return value
        return super().__getattribute__(item)

    def _extract_related_model_instead_of_field(
        self, item: str
    ) -> Optional[Union["T", Sequence["T"]]]:
        # alias = self.get_column_alias(item)
        if item in self._orm:
            return self._orm.get(item)
        return None  # pragma no cover

    def __eq__(self, other: object) -> bool:
        if isinstance(other, NewBaseModel):
            return self.__same__(other)
        return super().__eq__(other)  # pragma no cover

    def __same__(self, other: "NewBaseModel") -> bool:
        return (
            self._orm_id == other._orm_id
            or self.dict() == other.dict()
            or (self.pk == other.pk and self.pk is not None)
        )

    @classmethod
    def get_name(cls, lower: bool = True) -> str:
        name = cls.__name__
        if lower:
            name = name.lower()
        return name

    @property
    def pk_column(self) -> sqlalchemy.Column:
        return self.Meta.table.primary_key.columns.values()[0]

    @classmethod
    def pk_type(cls) -> Any:
        return cls.Meta.model_fields[cls.Meta.pkname].__type__

    @classmethod
    def db_backend_name(cls) -> str:
        return cls.Meta.database._backend._dialect.name

    def remove(self, name: "T") -> None:
        self._orm.remove_parent(self, name)

    @classmethod
    def get_properties(
        cls,
        include: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        exclude: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
    ) -> List[str]:
        props = [
            prop
            for prop in dir(cls)
            if isinstance(getattr(cls, prop), property)
            and prop not in ("__values__", "__fields__", "fields", "pk_column")
        ]
        if include:
            props = [prop for prop in props if prop in include]
        if exclude:
            props = [prop for prop in props if prop not in exclude]
        return props

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
        for field in self.extract_related_names():
            nested_model = getattr(self, field)

            if self.Meta.model_fields[field].virtual and nested:
                continue
            if isinstance(nested_model, list):
                result = []
                for model in nested_model:
                    try:
                        result.append(model.dict(nested=True))
                    except ReferenceError:  # pragma no cover
                        continue
                dict_instance[field] = result
            elif nested_model is not None:
                dict_instance[field] = nested_model.dict(nested=True)
            else:
                dict_instance[field] = None

        # include model properties as fields
        props = self.get_properties(include=include, exclude=exclude)
        if props:
            dict_instance.update({prop: getattr(self, prop) for prop in props})

        return dict_instance

    def from_dict(self, value_dict: Dict) -> "NewBaseModel":
        for key, value in value_dict.items():
            setattr(self, key, value)
        return self

    def _convert_json(self, column_name: str, value: Any, op: str) -> Union[str, Dict]:
        if not self._is_conversion_to_json_needed(column_name):
            return value

        condition = (
            isinstance(value, str) if op == "loads" else not isinstance(value, str)
        )
        operand: Callable[[Any], Any] = (
            json.loads if op == "loads" else json.dumps  # type: ignore
        )

        if condition:
            try:
                return operand(value)
            except TypeError:  # pragma no cover
                pass
        return value

    def _is_conversion_to_json_needed(self, column_name: str) -> bool:
        return self.Meta.model_fields[column_name].__type__ == pydantic.Json
