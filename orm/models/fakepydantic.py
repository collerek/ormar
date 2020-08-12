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
    Union,
)

import databases
import pydantic
import sqlalchemy
from pydantic import BaseModel

import orm  # noqa I100
from orm.fields import BaseField
from orm.models.metaclass import ModelMetaclass
from orm.relations import RelationshipManager

if TYPE_CHECKING:  # pragma no cover
    from orm.models.model import Model


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
            value = self._convert_json(key, value, op="dumps")
            value = self.__model_fields__[key].expand_relationship(value, self)

            relation_key = self.get_name(title=True) + "_" + key
            if not self._orm_relationship_manager.contains(relation_key, self):
                setattr(self.values, key, value)
        else:
            super().__setattr__(key, value)

    def __getattribute__(self, key: str) -> Any:
        if key != "__fields__" and key in self.__fields__:
            relation_key = self.get_name(title=True) + "_" + key
            if self._orm_relationship_manager.contains(relation_key, self):
                return self._orm_relationship_manager.get(relation_key, self)

            item = getattr(self.values, key, None)
            item = self._convert_json(key, item, op="loads")
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
    def pk_type(cls) -> Any:
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
        for field in one.__model_fields__.keys():
            if isinstance(getattr(one, field), list) and not isinstance(
                getattr(one, field), orm.Model
            ):
                setattr(other, field, getattr(one, field) + getattr(other, field))
            elif isinstance(getattr(one, field), orm.Model):
                if getattr(one, field).pk == getattr(other, field).pk:
                    setattr(
                        other,
                        field,
                        cls.merge_two_instances(
                            getattr(one, field), getattr(other, field)
                        ),
                    )
        return other
