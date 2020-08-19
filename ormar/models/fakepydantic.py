import inspect
import json
import uuid
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
    Type,
    TypeVar,
    Union, AbstractSet, Mapping,
)

import databases
import pydantic
import sqlalchemy
from pydantic import BaseModel

import ormar  # noqa I100
from ormar import ForeignKey
from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField
from ormar.models.metaclass import ModelMetaclass, ModelMeta
from ormar.relations import RelationshipManager

if TYPE_CHECKING:  # pragma no cover
    from ormar.models.model import Model

    IntStr = Union[int, str]
    DictStrAny = Dict[str, Any]
    AbstractSetIntStr = AbstractSet[IntStr]
    MappingIntStrAny = Mapping[IntStr, Any]


class FakePydantic(pydantic.BaseModel, metaclass=ModelMetaclass):
    # FakePydantic inherits from list in order to be treated as
    # request.Body parameter in fastapi routes,
    # inheriting from pydantic.BaseModel causes metaclass conflicts
    __slots__ = ('_orm_id', '_orm_saved')

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
            k: self.Meta.model_fields[k].expand_relationship(v, self)
            for k, v in kwargs.items()
        }

        values, fields_set, validation_error = pydantic.validate_model(
            self, kwargs
        )
        if validation_error and not pk_only:
            raise validation_error

        object.__setattr__(self, '__dict__', values)
        object.__setattr__(self, '__fields_set__', fields_set)

        # super().__init__(**kwargs)
        # self.values = self.__pydantic_model__(**kwargs)

    def __del__(self) -> None:
        self.Meta._orm_relationship_manager.deregister(self)

    def __setattr__(self, name, value):
        relation_key = self.get_name(title=True) + "_" + name
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        elif name == 'pk':
            object.__setattr__(self, self.Meta.pkname, value)     
        elif self.Meta._orm_relationship_manager.contains(relation_key, self):
            self.Meta.model_fields[name].expand_relationship(value, self)
        else:
        	super().__setattr__(name, value)

    def __getattr__(self, item):
        relation_key = self.get_name(title=True) + "_" + item
        if self.Meta._orm_relationship_manager.contains(relation_key, self):
            return self.Meta._orm_relationship_manager.get(relation_key, self)

    # def __setattr__(self, key: str, value: Any) -> None:
    #     if key in ('_orm_id', '_orm_relationship_manager', '_orm_saved', 'objects', '__model_fields__'):
    #         return setattr(self, key, value)
    #     # elif key in self._extract_related_names():
    #     #     value = self._convert_json(key, value, op="dumps")
    #     #     value = self.Meta.model_fields[key].expand_relationship(value, self)
    #     #     relation_key = self.get_name(title=True) + "_" + key
    #     #     if not self.Meta._orm_relationship_manager.contains(relation_key, self):
    #     #         setattr(self.values, key, value)
    #     else:
    #         super().__setattr__(key, value)

    # def __getattribute__(self, key: str) -> Any:
    #     if key != 'Meta' and key in self.Meta.model_fields:
    #         relation_key = self.get_name(title=True) + "_" + key
    #         if self.Meta._orm_relationship_manager.contains(relation_key, self):
    #             return self.Meta._orm_relationship_manager.get(relation_key, self)
    #         item = getattr(self.__fields__, key, None)
    #         item = self._convert_json(key, item, op="loads")
    #         return item
    #     return super().__getattribute__(key)

    def __same__(self, other: "Model") -> bool:
        if self.__class__ != other.__class__:  # pragma no cover
            return False
        return (self._orm_id == other._orm_id or 
                self.__dict__ == other.__dict__  or 
               (self.pk == other.pk and self.pk is not None
        ))

    # def __repr__(self) -> str:  # pragma no cover
    #     return self.values.__repr__()

    # @classmethod
    # def __get_validators__(cls) -> Callable:  # pragma no cover
    #     yield cls.__pydantic_model__.validate

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

    @pk.setter
    def pk(self, value: Any) -> None:
        setattr(self, self.Meta.pkname, value)

    @property
    def pk_column(self) -> sqlalchemy.Column:
        return self.Meta.table.primary_key.columns.values()[0]

    @classmethod
    def pk_type(cls) -> Any:
        return cls.Meta.model_fields[cls.Meta.pkname].__type__

    def dict(
            self,
            *,
            include: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
            exclude: Union['AbstractSetIntStr', 'MappingIntStrAny'] = None,
            by_alias: bool = False,
            skip_defaults: bool = None,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
            nested: bool = False
    ) -> 'DictStrAny':  # noqa: A003
        print('callin super', self.__class__)
        print('to exclude', self._exclude_related_names_not_required(nested))
        dict_instance = super().dict(include=include,
                                     exclude=self._exclude_related_names_not_required(nested),
                                     by_alias=by_alias,
                                     skip_defaults=skip_defaults,
                                     exclude_unset=exclude_unset,
                                     exclude_defaults=exclude_defaults,
                                     exclude_none=exclude_none)
        print('after super')
        for field in self._extract_related_names():
            print(self.__class__, field, nested)
            nested_model = getattr(self, field)

            if self.Meta.model_fields[field].virtual and nested:
                continue
            if isinstance(nested_model, list) and not isinstance(
                    nested_model, ormar.Model
            ):
                print('nested list')
                dict_instance[field] = [x.dict(nested=True) for x in nested_model]
            else:
                print('instance')
                if nested_model is not None:
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

    def _extract_own_model_fields(self) -> Dict:
        related_names = self._extract_related_names()
        self_fields = {k: v for k, v in self.dict().items() if k not in related_names}
        return self_fields

    @classmethod
    def _extract_related_names(cls) -> Set:
        related_names = set()
        for name, field in cls.Meta.model_fields.items():
            if inspect.isclass(field) and issubclass(
                    field, ForeignKeyField
            ):
                related_names.add(name)
        return related_names

    @classmethod
    def _exclude_related_names_not_required(cls, nested:bool=False) -> Set:
        if nested:
            return cls._extract_related_names()
        related_names = set()
        for name, field in cls.Meta.model_fields.items():
            if inspect.isclass(field) and issubclass(field, ForeignKeyField) and field.nullable:
                related_names.add(name)
        return related_names

    def _extract_model_db_fields(self) -> Dict:
        self_fields = self._extract_own_model_fields()
        self_fields = {
            k: v for k, v in self_fields.items() if k in self.Meta.table.columns
        }
        for field in self._extract_related_names():
            if getattr(self, field) is not None:
                self_fields[field] = getattr(
                    getattr(self, field), self.Meta.model_fields[field].to.Meta.pkname
                )
        return self_fields

    @classmethod
    def merge_instances_list(cls, result_rows: List["Model"]) -> List["Model"]:
        merged_rows = []
        for index, model in enumerate(result_rows):
            if index > 0 and model.pk == result_rows[index - 1].pk:
                result_rows[-1] = cls.merge_two_instances(model, merged_rows[-1])
            else:
                merged_rows.append(model)
        return merged_rows

    @classmethod
    def merge_two_instances(cls, one: "Model", other: "Model") -> "Model":
        for field in one.Meta.model_fields.keys():
            if isinstance(getattr(one, field), list) and not isinstance(
                    getattr(one, field), ormar.Model
            ):
                setattr(other, field, getattr(one, field) + getattr(other, field))
            elif isinstance(getattr(one, field), ormar.Model):
                if getattr(one, field).pk == getattr(other, field).pk:
                    setattr(
                        other,
                        field,
                        cls.merge_two_instances(
                            getattr(one, field), getattr(other, field)
                        ),
                    )
        return other
