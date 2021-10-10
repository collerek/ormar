import uuid
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    List,
    Optional,
    Set,
    TYPE_CHECKING,
    cast,
)

import pydantic

import ormar  # noqa: I100, I202
from ormar.exceptions import ModelPersistenceError
from ormar.models.mixins import AliasMixin
from ormar.models.mixins.relation_mixin import RelationMixin

if TYPE_CHECKING:  # pragma: no cover
    from ormar import ForeignKeyField, Model


class SavePrepareMixin(RelationMixin, AliasMixin):
    """
    Used to prepare models to be saved in database
    """

    if TYPE_CHECKING:  # pragma: nocover
        _choices_fields: Optional[Set]
        _skip_ellipsis: Callable
        __fields__: Dict[str, pydantic.fields.ModelField]

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
        new_kwargs = cls._remove_not_ormar_fields(new_kwargs)
        new_kwargs = cls.substitute_models_with_pks(new_kwargs)
        new_kwargs = cls.populate_default_values(new_kwargs)
        new_kwargs = cls.translate_columns_to_aliases(new_kwargs)
        return new_kwargs

    @classmethod
    def _remove_not_ormar_fields(cls, new_kwargs: dict) -> dict:
        """
        Removes primary key for if it's nullable or autoincrement pk field,
        and it's set to None.

        :param new_kwargs: dictionary of model that is about to be saved
        :type new_kwargs: Dict[str, str]
        :return: dictionary of model that is about to be saved
        :rtype: Dict[str, str]
        """
        ormar_fields = {
            k for k, v in cls.Meta.model_fields.items() if not v.pydantic_only
        }
        new_kwargs = {k: v for k, v in new_kwargs.items() if k in ormar_fields}
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
                parser: Callable[..., Any] = parsers.get(uuid_format, lambda x: x)
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
                if isinstance(field_value, ormar.Model):  # pragma: no cover
                    pk_value = getattr(field_value, target_pkname)
                    if not pk_value:
                        raise ModelPersistenceError(
                            f"You cannot save {field_value.get_name()} "
                            f"model without pk set!"
                        )
                    model_dict[field] = pk_value
                elif isinstance(field_value, (list, dict)) and field_value:
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

        fields_to_check = [
            field
            for field in cls.Meta.model_fields.values()
            if field.name in cls._choices_fields and field.name in new_kwargs
        ]
        for field in fields_to_check:
            if new_kwargs[field.name] not in field.choices:
                raise ValueError(
                    f"{field.name}: '{new_kwargs[field.name]}' "
                    f"not in allowed choices set:"
                    f" {field.choices}"
                )
        return new_kwargs

    @staticmethod
    async def _upsert_model(
        instance: "Model",
        save_all: bool,
        previous_model: Optional["Model"],
        relation_field: Optional["ForeignKeyField"],
        update_count: int,
    ) -> int:
        """
        Method updates given instance if:

        * instance is not saved or
        * instance have no pk or
        * save_all=True flag is set

        and instance is not __pk_only__.

        If relation leading to instance is a ManyToMany also the through model is saved

        :param instance: current model to upsert
        :type instance: Model
        :param save_all: flag if all models should be saved or only not saved ones
        :type save_all: bool
        :param relation_field: field with relation
        :type relation_field: Optional[ForeignKeyField]
        :param previous_model: previous model from which method came
        :type previous_model: Model
        :param update_count: no of updated models
        :type update_count: int
        :return: no of updated models
        :rtype: int
        """
        if (
            save_all or not instance.pk or not instance.saved
        ) and not instance.__pk_only__:
            await instance.upsert()
            if relation_field and relation_field.is_multi:
                await instance._upsert_through_model(
                    instance=instance,
                    relation_field=relation_field,
                    previous_model=cast("Model", previous_model),
                )
            update_count += 1
        return update_count

    @staticmethod
    async def _upsert_through_model(
        instance: "Model", previous_model: "Model", relation_field: "ForeignKeyField"
    ) -> None:
        """
        Upsert through model for m2m relation.

        :param instance: current model to upsert
        :type instance: Model
        :param relation_field: field with relation
        :type relation_field: Optional[ForeignKeyField]
        :param previous_model: previous model from which method came
        :type previous_model: Model
        """
        through_name = previous_model.Meta.model_fields[
            relation_field.name
        ].through.get_name()
        through = getattr(instance, through_name)
        if through:
            through_dict = through.dict(exclude=through.extract_related_names())
        else:
            through_dict = {}
        await getattr(
            previous_model, relation_field.name
        ).queryset_proxy.upsert_through_instance(instance, **through_dict)

    async def _update_relation_list(
        self,
        fields_list: Collection["ForeignKeyField"],
        follow: bool,
        save_all: bool,
        relation_map: Dict,
        update_count: int,
    ) -> int:
        """
        Internal method used in save_related to follow deeper from
        related models and update numbers of updated related instances.

        :type save_all: flag if all models should be saved
        :type save_all: bool
        :param fields_list: list of ormar fields to follow and save
        :type fields_list: Collection["ForeignKeyField"]
        :param relation_map: map of relations to follow
        :type relation_map: Dict
        :param follow: flag to trigger deep save -
        by default only directly related models are saved
        with follow=True also related models of related models are saved
        :type follow: bool
        :param update_count: internal parameter for recursive calls -
        number of updated instances
        :type update_count: int
        :return: tuple of update count and visited
        :rtype: int
        """
        for field in fields_list:
            values = self._get_field_values(name=field.name)
            for value in values:
                if follow:
                    update_count = await value.save_related(
                        follow=follow,
                        save_all=save_all,
                        relation_map=self._skip_ellipsis(  # type: ignore
                            relation_map, field.name, default_return={}
                        ),
                        update_count=update_count,
                        previous_model=self,
                        relation_field=field,
                    )
                else:
                    update_count = await value._upsert_model(
                        instance=value,
                        save_all=save_all,
                        previous_model=self,
                        relation_field=field,
                        update_count=update_count,
                    )
        return update_count

    def _get_field_values(self, name: str) -> List:
        """
        Extract field values and ensures it is a list.

        :param name: name of the field
        :type name: str
        :return: list of values
        :rtype: List
        """
        values = getattr(self, name) or []
        if not isinstance(values, list):
            values = [values]
        return values
