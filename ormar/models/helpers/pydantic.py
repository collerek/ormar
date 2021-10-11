import inspect
from typing import Dict, Optional, TYPE_CHECKING, Tuple, Type

import pydantic
from pydantic.fields import ModelField
from pydantic.utils import lenient_issubclass

from ormar.exceptions import ModelDefinitionError  # noqa: I100, I202
from ormar.fields import BaseField

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.fields import ManyToManyField


def create_pydantic_field(
    field_name: str, model: Type["Model"], model_field: "ManyToManyField"
) -> None:
    """
    Registers pydantic field on through model that leads to passed model
    and is registered as field_name passed.

    Through model is fetched from through attributed on passed model_field.

    :param field_name: field name to register
    :type field_name: str
    :param model: type of field to register
    :type model: Model class
    :param model_field: relation field from which through model is extracted
    :type model_field: ManyToManyField class
    """
    model_field.through.__fields__[field_name] = ModelField(
        name=field_name,
        type_=model,
        model_config=model.__config__,
        required=False,
        class_validators={},
    )


def get_pydantic_field(field_name: str, model: Type["Model"]) -> "ModelField":
    """
    Extracts field type and if it's required from Model model_fields by passed
    field_name. Returns a pydantic field with type of field_name field type.

    :param field_name: field name to fetch from Model and name of pydantic field
    :type field_name: str
    :param model: type of field to register
    :type model: Model class
    :return: newly created pydantic field
    :rtype: pydantic.ModelField
    """
    type_ = model.Meta.model_fields[field_name].__type__
    return ModelField(
        name=field_name,
        type_=type_,  # type: ignore
        model_config=model.__config__,
        required=not model.Meta.model_fields[field_name].nullable,
        class_validators={},
    )


def populate_pydantic_default_values(attrs: Dict) -> Tuple[Dict, Dict]:
    """
    Extracts ormar fields from annotations (deprecated) and from namespace
    dictionary of the class. Fields declared on model are all subclasses of the
    BaseField class.

    Trigger conversion of ormar field into pydantic FieldInfo, which has all needed
    parameters saved.

    Overwrites the annotations of ormar fields to corresponding types declared on
    ormar fields (constructed dynamically for relations).
    Those annotations are later used by pydantic to construct it's own fields.

    :param attrs: current class namespace
    :type attrs: Dict
    :return: namespace of the class updated, dict of extracted model_fields
    :rtype: Tuple[Dict, Dict]
    """
    model_fields = {}
    potential_fields = {}

    potential_fields.update(get_potential_fields(attrs))
    for field_name, field in potential_fields.items():
        field.name = field_name
        model_fields[field_name] = field
        default_type = (
            field.__type__ if not field.nullable else Optional[field.__type__]
        )
        overwrite_type = (
            field.__pydantic_type__
            if field.__type__ != field.__pydantic_type__
            else None
        )
        attrs["__annotations__"][field_name] = overwrite_type or default_type
    return attrs, model_fields


def merge_or_generate_pydantic_config(attrs: Dict, name: str) -> None:
    """
    Checks if the user provided pydantic Config,
    and if he did merges it with the default one.

    Updates the attrs in place with a new config.

    :rtype: None
    """
    DefaultConfig = get_pydantic_base_orm_config()
    if "Config" in attrs:
        ProvidedConfig = attrs["Config"]
        if not inspect.isclass(ProvidedConfig):
            raise ModelDefinitionError(
                f"Config provided for class {name} has to be a class."
            )

        class Config(ProvidedConfig, DefaultConfig):  # type: ignore
            pass

        attrs["Config"] = Config
    else:
        attrs["Config"] = DefaultConfig


def get_pydantic_base_orm_config() -> Type[pydantic.BaseConfig]:
    """
    Returns empty pydantic Config with orm_mode set to True.

    :return: empty default config with orm_mode set.
    :rtype: pydantic Config
    """

    class Config(pydantic.BaseConfig):
        orm_mode = True
        validate_assignment = True

    return Config


def get_potential_fields(attrs: Dict) -> Dict:
    """
    Gets all the fields in current class namespace that are Fields.

    :param attrs: current class namespace
    :type attrs: Dict
    :return: extracted fields that are ormar Fields
    :rtype: Dict
    """
    return {
        k: v
        for k, v in attrs.items()
        if (lenient_issubclass(v, BaseField) or isinstance(v, BaseField))
    }


def remove_excluded_parent_fields(model: Type["Model"]) -> None:
    """
    Removes pydantic fields that should be excluded from parent models

    :param model:
    :type model: Type["Model"]
    """
    excludes = {*model.Meta.exclude_parent_fields} - {*model.Meta.model_fields.keys()}
    if excludes:
        model.__fields__ = {
            k: v for k, v in model.__fields__.items() if k not in excludes
        }
