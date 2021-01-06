import inspect
from typing import List, Optional, Set, TYPE_CHECKING

from ormar.fields.foreign_key import ForeignKeyField


class RelationMixin:
    """
    Used to return relation fields/names etc. from given model
    """

    if TYPE_CHECKING:  # pragma no cover
        from ormar import ModelMeta

        Meta: ModelMeta
        _related_names: Optional[Set]
        _related_fields: Optional[List]

    @classmethod
    def extract_db_own_fields(cls) -> Set:
        """
        Returns only fields that are stored in the own database table, exclude all
        related fields.
        :return: set of model fields with relation fields excluded
        :rtype: Set
        """
        related_names = cls.extract_related_names()
        self_fields = {
            name for name in cls.Meta.model_fields.keys() if name not in related_names
        }
        return self_fields

    @classmethod
    def extract_related_fields(cls) -> List:
        """
        Returns List of ormar Fields for all relations declared on a model.
        List is cached in cls._related_fields for quicker access.

        :return: list of related fields
        :rtype: List
        """
        if isinstance(cls._related_fields, List):
            return cls._related_fields

        related_fields = []
        for name in cls.extract_related_names():
            related_fields.append(cls.Meta.model_fields[name])
        cls._related_fields = related_fields

        return related_fields

    @classmethod
    def extract_related_names(cls) -> Set:
        """
        Returns List of fields names for all relations declared on a model.
        List is cached in cls._related_names for quicker access.

        :return: list of related fields names
        :rtype: List
        """
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
        """
        Returns only fields that are stored in the own database table, exclude
        related fields that are not stored as foreign keys on given model.
        :return: set of model fields with non fk relation fields excluded
        :rtype: Set
        """
        related_names = cls.extract_related_names()
        related_names = {
            name
            for name in related_names
            if cls.Meta.model_fields[name].is_valid_uni_relation()
        }
        return related_names

    @classmethod
    def _exclude_related_names_not_required(cls, nested: bool = False) -> Set:
        """
        Returns a set of non mandatory related models field names.

        For a main model (not nested) only nullable related field names are returned,
        for nested models all related models are returned.

        :param nested: flag setting nested models (child of previous one, not main one)
        :type nested: bool
        :return: set of non mandatory related fields
        :rtype: Set
        """
        if nested:
            return cls.extract_related_names()
        related_names = cls.extract_related_names()
        related_names = {
            name for name in related_names if cls.Meta.model_fields[name].nullable
        }
        return related_names
