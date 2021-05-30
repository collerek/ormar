import string
from random import choices
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
    Type,
    Union,
    cast,
)

import pydantic
from pydantic.fields import ModelField

from ormar.models.mixins.relation_mixin import RelationMixin  # noqa: I100, I202
from ormar.queryset.utils import translate_list_to_dict


class PydanticMixin(RelationMixin):
    if TYPE_CHECKING:  # pragma: no cover
        __fields__: Dict[str, ModelField]
        _skip_ellipsis: Callable
        _get_not_excluded_fields: Callable

    @classmethod
    def get_pydantic(
        cls, *, include: Union[Set, Dict] = None, exclude: Union[Set, Dict] = None,
    ) -> Type[pydantic.BaseModel]:
        """
        Returns a pydantic model out of ormar model.

        Converts also nested ormar models into pydantic models.

        Can be used to fully exclude certain fields in fastapi response and requests.

        :param include: fields of own and nested models to include
        :type include: Union[Set, Dict, None]
        :param exclude: fields of own and nested models to exclude
        :type exclude: Union[Set, Dict, None]
        """
        relation_map = translate_list_to_dict(cls._iterate_related_models())

        return cls._convert_ormar_to_pydantic(
            include=include, exclude=exclude, relation_map=relation_map
        )

    @classmethod
    def _convert_ormar_to_pydantic(
        cls,
        relation_map: Dict[str, Any],
        include: Union[Set, Dict] = None,
        exclude: Union[Set, Dict] = None,
    ) -> Type[pydantic.BaseModel]:
        if include and isinstance(include, Set):
            include = translate_list_to_dict(include)
        if exclude and isinstance(exclude, Set):
            exclude = translate_list_to_dict(exclude)
        fields_dict: Dict[str, Any] = dict()
        defaults: Dict[str, Any] = dict()
        fields_to_process = cls._get_not_excluded_fields(
            fields={*cls.Meta.model_fields.keys()}, include=include, exclude=exclude
        )
        for name in fields_to_process:
            field = cls._determine_pydantic_field_type(
                name=name,
                defaults=defaults,
                include=include,
                exclude=exclude,
                relation_map=relation_map,
            )
            if field is not None:
                fields_dict[name] = field
        model = type(
            f"{cls.__name__}_{''.join(choices(string.ascii_uppercase, k=3))}",
            (pydantic.BaseModel,),
            {"__annotations__": fields_dict, **defaults},
        )
        return cast(Type[pydantic.BaseModel], model)

    @classmethod
    def _determine_pydantic_field_type(
        cls,
        name: str,
        defaults: Dict,
        include: Union[Set, Dict, None],
        exclude: Union[Set, Dict, None],
        relation_map: Dict[str, Any],
    ) -> Any:
        field = cls.Meta.model_fields[name]
        target: Any = None
        if field.is_relation and name in relation_map:  # type: ignore
            target = field.to._convert_ormar_to_pydantic(
                include=cls._skip_ellipsis(include, name),
                exclude=cls._skip_ellipsis(exclude, name),
                relation_map=cls._skip_ellipsis(
                    relation_map, field, default_return=dict()
                ),
            )
            if field.is_multi or field.virtual:
                target = List[target]  # type: ignore
        elif not field.is_relation:
            defaults[name] = cls.__fields__[name].field_info
            target = field.__type__
        if target is not None and field.nullable:
            target = Optional[target]
        return target
