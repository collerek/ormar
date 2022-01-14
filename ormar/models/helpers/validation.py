import base64
import decimal
import numbers
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Set,
    TYPE_CHECKING,
    Type,
    Union,
)

try:
    import orjson as json
except ImportError:  # pragma: no cover
    import json  # type: ignore  # noqa: F401

import pydantic
from pydantic.class_validators import make_generic_validator
from pydantic.fields import ModelField, SHAPE_LIST

import ormar  # noqa: I100, I202
from ormar.models.helpers.models import meta_field_not_set
from ormar.queryset.utils import translate_list_to_dict

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.fields import BaseField


def check_if_field_has_choices(field: "BaseField") -> bool:
    """
    Checks if given field has choices populated.
    A if it has one, a validator for this field needs to be attached.

    :param field: ormar field to check
    :type field: BaseField
    :return: result of the check
    :rtype: bool
    """
    return hasattr(field, "choices") and bool(field.choices)


def convert_value_if_needed(field: "BaseField", value: Any) -> Any:
    """
    Converts dates to isoformat as fastapi can check this condition in routes
    and the fields are not yet parsed.
    Converts enums to list of it's values.
    Converts uuids to strings.
    Converts decimal to float with given scale.

    :param field: ormar field to check with choices
    :type field: BaseField
    :param value: current values of the model to verify
    :type value: Any
    :return: value, choices list
    :rtype: Any
    """
    encoder = ormar.ENCODERS_MAP.get(field.__type__, lambda x: x)
    if field.__type__ == decimal.Decimal:
        precision = field.scale  # type: ignore
        value = encoder(value, precision)
    elif field.__type__ == bytes:
        represent_as_string = field.represent_as_base64_str
        value = encoder(value, represent_as_string)
    elif encoder:
        value = encoder(value)
    return value


def generate_validator(ormar_field: "BaseField") -> Callable:
    choices = ormar_field.choices

    def validate_choices(cls: type, value: Any, field: "ModelField") -> None:
        """
        Validates if given value is in provided choices.

        :raises ValueError: If value is not in choices.
        :param field:field to validate
        :type field: BaseField
        :param value: value of the field
        :type value: Any
        """
        adjusted_value = convert_value_if_needed(field=ormar_field, value=value)
        if adjusted_value is not ormar.Undefined and adjusted_value not in choices:
            raise ValueError(
                f"{field.name}: '{adjusted_value}' "
                f"not in allowed choices set:"
                f" {choices}"
            )
        return value

    return validate_choices


def generate_model_example(model: Type["Model"], relation_map: Dict = None) -> Dict:
    """
    Generates example to be included in schema in fastapi.

    :param model: ormar.Model
    :type model: Type["Model"]
    :param relation_map: dict with relations to follow
    :type relation_map: Optional[Dict]
    :return: dict with example values
    :rtype: Dict[str, int]
    """
    example: Dict[str, Any] = dict()
    relation_map = (
        relation_map
        if relation_map is not None
        else translate_list_to_dict(model._iterate_related_models())
    )
    for name, field in model.Meta.model_fields.items():
        populates_sample_fields_values(
            example=example, name=name, field=field, relation_map=relation_map
        )
    to_exclude = {name for name in model.Meta.model_fields}
    pydantic_repr = generate_pydantic_example(pydantic_model=model, exclude=to_exclude)
    example.update(pydantic_repr)

    return example


def populates_sample_fields_values(
    example: Dict[str, Any], name: str, field: "BaseField", relation_map: Dict = None
) -> None:
    """
    Iterates the field and sets fields to sample values

    :param field: ormar field
    :type field: BaseField
    :param name: name of the field
    :type name: str
    :param example: example dict
    :type example: Dict[str, Any]
    :param relation_map: dict with relations to follow
    :type relation_map: Optional[Dict]
    """
    if not field.is_relation:
        is_bytes_str = field.__type__ == bytes and field.represent_as_base64_str
        example[name] = field.__sample__ if not is_bytes_str else "string"
    elif isinstance(relation_map, dict) and name in relation_map:
        example[name] = get_nested_model_example(
            name=name, field=field, relation_map=relation_map
        )


def get_nested_model_example(
    name: str, field: "BaseField", relation_map: Dict
) -> Union[List, Dict]:
    """
    Gets representation of nested model.

    :param name: name of the field to follow
    :type name: str
    :param field: ormar field
    :type field: BaseField
    :param relation_map: dict with relation map
    :type relation_map: Dict
    :return: nested model or list of nested model repr
    :rtype: Union[List, Dict]
    """
    value = generate_model_example(field.to, relation_map=relation_map.get(name, {}))
    new_value: Union[List, Dict] = [value] if field.is_multi or field.virtual else value
    return new_value


def generate_pydantic_example(
    pydantic_model: Type[pydantic.BaseModel], exclude: Set = None
) -> Dict:
    """
    Generates dict with example.

    :param pydantic_model: model to parse
    :type pydantic_model: Type[pydantic.BaseModel]
    :param exclude: list of fields to exclude
    :type exclude: Optional[Set]
    :return: dict with fields and sample values
    :rtype: Dict
    """
    example: Dict[str, Any] = dict()
    exclude = exclude or set()
    name_to_check = [name for name in pydantic_model.__fields__ if name not in exclude]
    for name in name_to_check:
        field = pydantic_model.__fields__[name]
        type_ = field.type_
        if field.shape == SHAPE_LIST:
            example[name] = [get_pydantic_example_repr(type_)]
        else:
            example[name] = get_pydantic_example_repr(type_)
    return example


def get_pydantic_example_repr(type_: Any) -> Any:
    """
    Gets sample representation of pydantic field for example dict.

    :param type_: type of pydantic field
    :type type_: Any
    :return: representation to include in example
    :rtype: Any
    """
    if issubclass(type_, (numbers.Number, decimal.Decimal)):
        return 0
    if issubclass(type_, pydantic.BaseModel):
        return generate_pydantic_example(pydantic_model=type_)
    return "string"


def overwrite_example_and_description(
    schema: Dict[str, Any], model: Type["Model"]
) -> None:
    """
    Overwrites the example with properly nested children models.
    Overwrites the description if it's taken from ormar.Model.

    :param schema: schema of current model
    :type schema: Dict[str, Any]
    :param model: model class
    :type model: Type["Model"]
    """
    schema["example"] = generate_model_example(model=model)
    if "Main base class of ormar Model." in schema.get("description", ""):
        schema["description"] = f"{model.__name__}"


def overwrite_binary_format(schema: Dict[str, Any], model: Type["Model"]) -> None:
    """
    Overwrites format of the field if it's a LargeBinary field with
    a flag to represent the field as base64 encoded string.

    :param schema: schema of current model
    :type schema: Dict[str, Any]
    :param model: model class
    :type model: Type["Model"]
    """
    for field_id, prop in schema.get("properties", {}).items():
        if (
            field_id in model._bytes_fields
            and model.Meta.model_fields[field_id].represent_as_base64_str
        ):
            prop["format"] = "base64"
            if prop.get("enum"):
                prop["enum"] = [
                    base64.b64encode(choice).decode() for choice in prop.get("enum", [])
                ]


def construct_modify_schema_function(fields_with_choices: List) -> Callable:
    """
    Modifies the schema to include fields with choices validator.
    Those fields will be displayed in schema as Enum types with available choices
    values listed next to them.

    Note that schema extra has to be a function, otherwise it's called to soon
    before all the relations are expanded.

    :param fields_with_choices: list of fields with choices validation
    :type fields_with_choices: List
    :return: callable that will be run by pydantic to modify the schema
    :rtype: Callable
    """

    def schema_extra(schema: Dict[str, Any], model: Type["Model"]) -> None:
        for field_id, prop in schema.get("properties", {}).items():
            if field_id in fields_with_choices:
                prop["enum"] = list(model.Meta.model_fields[field_id].choices)
                prop["description"] = prop.get("description", "") + "An enumeration."
        overwrite_example_and_description(schema=schema, model=model)
        overwrite_binary_format(schema=schema, model=model)

    return staticmethod(schema_extra)  # type: ignore


def construct_schema_function_without_choices() -> Callable:
    """
    Modifies model example and description if needed.

    Note that schema extra has to be a function, otherwise it's called to soon
    before all the relations are expanded.

    :return: callable that will be run by pydantic to modify the schema
    :rtype: Callable
    """

    def schema_extra(schema: Dict[str, Any], model: Type["Model"]) -> None:
        overwrite_example_and_description(schema=schema, model=model)
        overwrite_binary_format(schema=schema, model=model)

    return staticmethod(schema_extra)  # type: ignore


def populate_choices_validators(model: Type["Model"]) -> None:  # noqa CCR001
    """
    Checks if Model has any fields with choices set.
    If yes it adds choices validation into pre root validators.

    :param model: newly constructed Model
    :type model: Model class
    """
    fields_with_choices = []
    if not meta_field_not_set(model=model, field_name="model_fields"):
        if not hasattr(model, "_choices_fields"):
            model._choices_fields = set()
        for name, field in model.Meta.model_fields.items():
            if check_if_field_has_choices(field) and name not in model._choices_fields:
                fields_with_choices.append(name)
                validator = make_generic_validator(generate_validator(field))
                model.__fields__[name].validators.append(validator)
                model._choices_fields.add(name)

        if fields_with_choices:
            model.Config.schema_extra = construct_modify_schema_function(
                fields_with_choices=fields_with_choices
            )
        else:
            model.Config.schema_extra = construct_schema_function_without_choices()
