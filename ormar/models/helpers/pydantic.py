import warnings
from typing import Dict, Optional, TYPE_CHECKING, Tuple, Type

from pydantic import BaseConfig
from pydantic.fields import ModelField
from pydantic.utils import lenient_issubclass

import ormar  # noqa: I100, I202
from ormar.fields import BaseField, ManyToManyField

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


def verify_related_name_dont_duplicate(
    child: Type["Model"], parent_model: Type["Model"], related_name: str,
) -> None:
    """
    Verifies whether the used related_name (regardless of the fact if user defined or
    auto generated) is already used on related model, but is connected with other model
    than the one that we connect right now.

    :raises: ModelDefinitionError if name is already used but lead to different related
    model
    :param child: related Model class
    :type child: ormar.models.metaclass.ModelMetaclass
    :param parent_model: parent Model class
    :type parent_model: ormar.models.metaclass.ModelMetaclass
    :param related_name:
    :type related_name:
    :return: None
    :rtype: None
    """
    if parent_model.Meta.model_fields.get(related_name):
        fk_field = parent_model.Meta.model_fields.get(related_name)
        if not fk_field:  # pragma: no cover
            return
        if fk_field.to != child and fk_field.to.Meta != child.Meta:
            raise ormar.ModelDefinitionError(
                f"Relation with related_name "
                f"'{related_name}' "
                f"leading to model "
                f"{parent_model.get_name(lower=False)} "
                f"cannot be used on model "
                f"{child.get_name(lower=False)} "
                f"because it's already used by model "
                f"{fk_field.to.get_name(lower=False)}"
            )


def reverse_field_not_already_registered(
    child: Type["Model"], child_model_name: str, parent_model: Type["Model"]
) -> bool:
    """
    Checks if child is already registered in parents pydantic fields.

    :raises: ModelDefinitionError if related name is already used but lead to different
    related model
    :param child: related Model class
    :type child: ormar.models.metaclass.ModelMetaclass
    :param child_model_name: related_name of the child if provided
    :type child_model_name: str
    :param parent_model: parent Model class
    :type parent_model: ormar.models.metaclass.ModelMetaclass
    :return: result of the check
    :rtype: bool
    """
    check_result = child_model_name not in parent_model.Meta.model_fields
    check_result2 = child.get_name() not in parent_model.Meta.model_fields

    if not check_result:
        verify_related_name_dont_duplicate(
            child=child, parent_model=parent_model, related_name=child_model_name
        )
    if not check_result2:
        verify_related_name_dont_duplicate(
            child=child, parent_model=parent_model, related_name=child.get_name()
        )

    return check_result and check_result2


def create_pydantic_field(
    field_name: str, model: Type["Model"], model_field: Type[ManyToManyField]
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
    return ModelField(
        name=field_name,
        type_=model.Meta.model_fields[field_name].__type__,  # type: ignore
        model_config=model.__config__,
        required=not model.Meta.model_fields[field_name].nullable,
        class_validators={},
    )


def populate_default_pydantic_field_value(
    ormar_field: Type[BaseField], field_name: str, attrs: dict
) -> dict:
    """
    Grabs current value of the ormar Field in class namespace
    (so the default_value declared on ormar model if set)
    and converts it to pydantic.FieldInfo
    that pydantic is able to extract later.

    On FieldInfo there are saved all needed params like max_length of the string
    and other constraints that pydantic can use to build
    it's own field validation used by ormar.

    :param ormar_field: field to convert
    :type ormar_field: ormar Field
    :param field_name: field to convert name
    :type field_name: str
    :param attrs: current class namespace
    :type attrs: Dict
    :return: updated namespace dict
    :rtype: Dict
    """
    curr_def_value = attrs.get(field_name, ormar.Undefined)
    if lenient_issubclass(curr_def_value, ormar.fields.BaseField):
        curr_def_value = ormar.Undefined
    if curr_def_value is None:
        attrs[field_name] = ormar_field.convert_to_pydantic_field_info(allow_null=True)
    else:
        attrs[field_name] = ormar_field.convert_to_pydantic_field_info()
    return attrs


def populate_pydantic_default_values(attrs: Dict) -> Tuple[Dict, Dict]:
    """
    Extracts ormar fields from annotations (deprecated) and from namespace
    dictionary of the class. Fields declared on model are all subclasses of the
    BaseField class.

    Trigger conversion of ormar field into pydantic FieldInfo, which has all needed
    paramaters saved.

    Overwrites the annotations of ormar fields to corresponding types declared on
    ormar fields (constructed dynamically for relations).
    Those annotations are later used by pydantic to construct it's own fields.

    :param attrs: current class namespace
    :type attrs: Dict
    :return: namespace of the class updated, dict of extracted model_fields
    :rtype: Tuple[Dict, Dict]
    """
    model_fields = {}
    potential_fields = {
        k: v
        for k, v in attrs["__annotations__"].items()
        if lenient_issubclass(v, BaseField)
    }
    if potential_fields:
        warnings.warn(
            "Using ormar.Fields as type Model annotation has been deprecated,"
            " check documentation of current version",
            DeprecationWarning,
        )

    potential_fields.update(get_potential_fields(attrs))
    for field_name, field in potential_fields.items():
        field.name = field_name
        attrs = populate_default_pydantic_field_value(field, field_name, attrs)
        model_fields[field_name] = field
        attrs["__annotations__"][field_name] = (
            field.__type__ if not field.nullable else Optional[field.__type__]
        )
    return attrs, model_fields


def get_pydantic_base_orm_config() -> Type[BaseConfig]:
    """
    Returns empty pydantic Config with orm_mode set to True.

    :return: empty default config with orm_mode set.
    :rtype: pydantic Config
    """

    class Config(BaseConfig):
        orm_mode = True

    return Config


def populate_default_options_values(
    new_model: Type["Model"], model_fields: Dict
) -> None:
    """
    Sets all optional Meta values to it's defaults
    and set model_fields that were already previously extracted.

    Here should live all options that are not overwritten/set for all models.

    Current options are:
    * constraints = []
    * abstract = False

    :param new_model: newly constructed Model
    :type new_model: Model class
    :param model_fields:
    :type model_fields: Union[Dict[str, type], Dict]
    """
    if not hasattr(new_model.Meta, "constraints"):
        new_model.Meta.constraints = []
    if not hasattr(new_model.Meta, "model_fields"):
        new_model.Meta.model_fields = model_fields
    if not hasattr(new_model.Meta, "abstract"):
        new_model.Meta.abstract = False


def get_potential_fields(attrs: Dict) -> Dict:
    """
    Gets all the fields in current class namespace that are Fields.

    :param attrs: current class namespace
    :type attrs: Dict
    :return: extracted fields that are ormar Fields
    :rtype: Dict
    """
    return {k: v for k, v in attrs.items() if lenient_issubclass(v, BaseField)}


def extract_annotations_and_default_vals(attrs: Dict) -> Tuple[Dict, Dict]:
    """
    Extracts annotations from class namespace dict and triggers
    extraction of ormar model_fields.

    :param attrs: namespace of the class created
    :type attrs: Dict
    :return: namespace of the class updated, dict of extracted model_fields
    :rtype: Tuple[Dict, Dict]
    """
    key = "__annotations__"
    attrs[key] = attrs.get(key, {})
    attrs, model_fields = populate_pydantic_default_values(attrs)
    return attrs, model_fields
