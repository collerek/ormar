from typing import Dict, TYPE_CHECKING


class AliasMixin:
    """
    Used to translate field names into database column names.
    """

    if TYPE_CHECKING:  # pragma: no cover
        from ormar import ModelMeta

        Meta: ModelMeta

    @classmethod
    def get_column_alias(cls, field_name: str) -> str:
        """
        Returns db alias (column name in db) for given ormar field.
        For fields without alias field name is returned.
        :param field_name: name of the field to get alias from
        :type field_name: str
        :return: alias (db name) if set, otherwise passed name
        :rtype: str
        """
        field = cls.Meta.model_fields.get(field_name)
        return field.get_alias() if field is not None else field_name

    @classmethod
    def get_column_name_from_alias(cls, alias: str) -> str:
        """
        Returns ormar field name for given db alias (column name in db).
        If field do not have alias it's returned as is.
        :param alias:
        :type alias: str
        :return: field name if set, otherwise passed alias (db name)
        :rtype: str
        """
        for field_name, field in cls.Meta.model_fields.items():
            if field.get_alias() == alias:
                return field_name
        return alias  # if not found it's not an alias but actual name

    @classmethod
    def translate_columns_to_aliases(cls, new_kwargs: Dict) -> Dict:
        """
        Translates dictionary of model fields changing field names into aliases.
        If field has no alias the field name remains intact.
        Only fields present in the dictionary are translated.
        :param new_kwargs: dict with fields names and their values
        :type new_kwargs: Dict
        :return: dict with aliases and their values
        :rtype: Dict
        """
        for field_name, field in cls.Meta.model_fields.items():
            if field_name in new_kwargs:
                new_kwargs[field.get_alias()] = new_kwargs.pop(field_name)
        return new_kwargs

    @classmethod
    def translate_aliases_to_columns(cls, new_kwargs: Dict) -> Dict:
        """
        Translates dictionary of model fields changing aliases into field names.
        If field has no alias the alias is already a field name.
        Only fields present in the dictionary are translated.
        :param new_kwargs: dict with aliases and their values
        :type new_kwargs: Dict
        :return: dict with fields names and their values
        :rtype: Dict
        """
        for field_name, field in cls.Meta.model_fields.items():
            if field.get_alias() and field.get_alias() in new_kwargs:
                new_kwargs[field_name] = new_kwargs.pop(field.get_alias())
        return new_kwargs
