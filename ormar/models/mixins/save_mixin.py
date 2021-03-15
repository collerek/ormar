import uuid
from typing import Dict, Optional, Set, TYPE_CHECKING

import ormar
from ormar.exceptions import ModelPersistenceError
from ormar.models.helpers.validation import validate_choices
from ormar.models.mixins import AliasMixin
from ormar.models.mixins.relation_mixin import RelationMixin


class SavePrepareMixin(RelationMixin, AliasMixin):
    """
    Used to prepare models to be saved in database
    """

    if TYPE_CHECKING:  # pragma: nocover
        _choices_fields: Optional[Set]

    @classmethod
    def prepare_model_to_save(cls, new_kwargs: dict) -> dict:
        """
        Combines all preparation methods before saving.
        Removes primary key for if it's nullable or autoincrement pk field,
        and it's set to None.
        Substitute related models with their primary key values as fk column.
        Populates the default values for field with default set and no value.
        Translate columns into aliases (db names).

        :param new_kwargs: dictionary of model that is about to be saved
        :type new_kwargs: Dict[str, str]
        :return: dictionary of model that is about to be saved
        :rtype: Dict[str, str]
        """
        new_kwargs = cls._remove_pk_from_kwargs(new_kwargs)
        new_kwargs = cls.substitute_models_with_pks(new_kwargs)
        new_kwargs = cls.populate_default_values(new_kwargs)
        new_kwargs = cls.translate_columns_to_aliases(new_kwargs)
        return new_kwargs

    @classmethod
    def _remove_pk_from_kwargs(cls, new_kwargs: dict) -> dict:
        """
        Removes primary key for if it's nullable or autoincrement pk field,
        and it's set to None.

        :param new_kwargs: dictionary of model that is about to be saved
        :type new_kwargs: Dict[str, str]
        :return: dictionary of model that is about to be saved
        :rtype: Dict[str, str]
        """
        pkname = cls.Meta.pkname
        pk = cls.Meta.model_fields[pkname]
        if new_kwargs.get(pkname, ormar.Undefined) is None and (
            pk.nullable or pk.autoincrement
        ):
            del new_kwargs[pkname]
        return new_kwargs

    @classmethod
    def parse_non_db_fields(cls, model_dict: Dict) -> Dict:
        """
        Receives dictionary of model that is about to be saved and changes uuid fields
        to strings in bulk_update.

        :param model_dict: dictionary of model that is about to be saved
        :type model_dict: Dict
        :return: dictionary of model that is about to be saved
        :rtype: Dict
        """
        for name, field in cls.Meta.model_fields.items():
            if field.__type__ == uuid.UUID and name in model_dict:
                parsers = {"string": lambda x: str(x), "hex": lambda x: "%.32x" % x.int}
                uuid_format = field.column_type.uuid_format
                parser = parsers.get(uuid_format, lambda x: x)
                model_dict[name] = parser(model_dict[name])
        return model_dict

    @classmethod
    def substitute_models_with_pks(cls, model_dict: Dict) -> Dict:  # noqa  CCR001
        """
        Receives dictionary of model that is about to be saved and changes all related
        models that are stored as foreign keys to their fk value.

        :param model_dict: dictionary of model that is about to be saved
        :type model_dict: Dict
        :return: dictionary of model that is about to be saved
        :rtype: Dict
        """
        for field in cls.extract_related_names():
            field_value = model_dict.get(field, None)
            if field_value is not None:
                target_field = cls.Meta.model_fields[field]
                target_pkname = target_field.to.Meta.pkname
                if isinstance(field_value, ormar.Model):
                    pk_value = getattr(field_value, target_pkname)
                    if not pk_value:
                        raise ModelPersistenceError(
                            f"You cannot save {field_value.get_name()} "
                            f"model without pk set!"
                        )
                    model_dict[field] = pk_value
                elif field_value:  # nested dict
                    if isinstance(field_value, list):
                        model_dict[field] = [
                            target.get(target_pkname) for target in field_value
                        ]
                    else:
                        model_dict[field] = field_value.get(target_pkname)
                else:
                    model_dict.pop(field, None)
        return model_dict

    @classmethod
    def populate_default_values(cls, new_kwargs: Dict) -> Dict:
        """
        Receives dictionary of model that is about to be saved and populates the default
        value on the fields that have the default value set, but no actual value was
        passed by the user.

        :param new_kwargs: dictionary of model that is about to be saved
        :type new_kwargs: Dict
        :return: dictionary of model that is about to be saved
        :rtype: Dict
        """
        for field_name, field in cls.Meta.model_fields.items():
            if (
                field_name not in new_kwargs
                and field.has_default(use_server=False)
                and not field.pydantic_only
            ):
                new_kwargs[field_name] = field.get_default()
            # clear fields with server_default set as None
            if field.server_default is not None and not new_kwargs.get(field_name):
                new_kwargs.pop(field_name, None)
        return new_kwargs

    @classmethod
    def validate_choices(cls, new_kwargs: Dict) -> Dict:
        """
        Receives dictionary of model that is about to be saved and validates the
        fields with choices set to see if the value is allowed.

        :param new_kwargs: dictionary of model that is about to be saved
        :type new_kwargs: Dict
        :return: dictionary of model that is about to be saved
        :rtype: Dict
        """
        if not cls._choices_fields:
            return new_kwargs

        for field_name, field in cls.Meta.model_fields.items():
            if field_name in new_kwargs and field_name in cls._choices_fields:
                validate_choices(field=field, value=new_kwargs.get(field_name))
        return new_kwargs
