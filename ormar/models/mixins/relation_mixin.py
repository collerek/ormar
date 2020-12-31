import inspect
from typing import List, Optional, Set, TYPE_CHECKING

from ormar.fields.foreign_key import ForeignKeyField


class RelationMixin:
    if TYPE_CHECKING:  # pragma no cover
        from ormar import ModelMeta

        Meta: ModelMeta
        _related_names: Optional[Set]
        _related_fields: Optional[List]

    @classmethod
    def extract_db_own_fields(cls) -> Set:
        related_names = cls.extract_related_names()
        self_fields = {
            name for name in cls.Meta.model_fields.keys() if name not in related_names
        }
        return self_fields

    @classmethod
    def extract_related_fields(cls) -> List:

        if isinstance(cls._related_fields, List):
            return cls._related_fields

        related_fields = []
        for name in cls.extract_related_names():
            related_fields.append(cls.Meta.model_fields[name])
        cls._related_fields = related_fields

        return related_fields

    @classmethod
    def extract_related_names(cls) -> Set:

        if isinstance(cls._related_names, Set):
            return cls._related_names

        related_names = set()
        for name, field in cls.Meta.model_fields.items():
            if inspect.isclass(field) and issubclass(field, ForeignKeyField):
                related_names.add(name)
        cls._related_names = related_names

        return related_names

    @classmethod
    def _extract_db_related_names(cls) -> Set:
        related_names = cls.extract_related_names()
        related_names = {
            name
            for name in related_names
            if cls.Meta.model_fields[name].is_valid_uni_relation()
        }
        return related_names

    @classmethod
    def _exclude_related_names_not_required(cls, nested: bool = False) -> Set:
        if nested:
            return cls.extract_related_names()
        related_names = cls.extract_related_names()
        related_names = {
            name for name in related_names if cls.Meta.model_fields[name].nullable
        }
        return related_names
