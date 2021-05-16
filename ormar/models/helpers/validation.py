import base64
import datetime
import decimal
import numbers
import uuid
from enum import Enum
from typing import Any, Dict, List, Set, TYPE_CHECKING, Tuple, Type, Union

try:
    import orjson as json
except ImportError:  # pragma: no cover
    import json  # type: ignore

import pydantic
from pydantic.fields import SHAPE_LIST
from pydantic.main import SchemaExtraCallable

import ormar  # noqa: I100, I202
from ormar.fields import BaseField
from ormar.models.helpers.models import meta_field_not_set
from ormar.queryset.utils import translate_list_to_dict

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


def check_if_field_has_choices(field: BaseField) -> bool:
    """
    Checks if given field has choices populated.
    A if it has one, a validator for this field needs to be attached.

    :param field: ormar field to check
    :type field: BaseField
    :return: result of the check
    :rtype: bool
    """
    return hasattr(field, "choices") and bool(field.choices)


def convert_choices_if_needed(  # noqa: CCR001
    field: "BaseField", value: Any
) -> Tuple[Any, List]:
    """
    Converts dates to isoformat as fastapi can check this condition in routes
    and the fields are not yet parsed.

    Converts enums to list of it's values.

    Converts uuids to strings.

    Converts decimal to float with given scale.

    :param field: ormar field to check with choices
    :type field: BaseField
    :param values: current values of the model to verify
    :type values: Dict
    :return: value, choices list
    :rtype: Tuple[Any, List]
    """
    # TODO use same maps as with EncryptedString
    choices = [o.value if isinstance(o, Enum) else o for o in field.choices]

    if field.__type__ in [datetime.datetime, datetime.date, datetime.time]:
        value = value.isoformat() if not isinstance(value, str) else value
        choices = [o.isoformat() for o in field.choices]
    elif field.__type__ == pydantic.Json:
        value = json.dumps(value) if not isinstance(value, str) else value
        value = value.decode("utf-8") if isinstance(value, bytes) else value
    elif field.__type__ == uuid.UUID:
        value = str(value) if not isinstance(value, str) else value
        choices = [str(o) for o in field.choices]
    elif field.__type__ == decimal.Decimal:
        precision = field.scale  # type: ignore
        value = (
            round(float(value), precision)
            if isinstance(value, decimal.Decimal)
            else value
        )
        choices = [round(float(o), precision) for o in choices]
    elif field.__type__ == bytes:
        if field.represent_as_base64_str:
            value = value if isinstance(value, bytes) else base64.b64decode(value)
        else:
            value = value if isinstance(value, bytes) else value.encode("utf-8")

    return value, choices


def validate_choices(field: "BaseField", value: Any) -> None:
    """
    Validates if given value is in provided choices.

    :raises ValueError: If value is not in choices.
    :param field:field to validate
    :type field: BaseField
    :param value: value of the field
    :type value: Any
    """
    value, choices = convert_choices_if_needed(field=field, value=value)
    if value is not ormar.Undefined and value not in choices:
        raise ValueError(
            f"{field.name}: '{value}' " f"not in allowed choices set:" f" {choices}"
        )


def choices_validator(cls: Type["Model"], values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validator that is attached to pydantic model pre root validators.
    Validator checks if field value is in field.choices list.

    :raises ValueError: if field value is outside of allowed choices.
    :param cls: constructed class
    :type cls: Model class
    :param values: dictionary of field values (pydantic side)
    :type values: Dict[str, Any]
    :return: values if pass validation, otherwise exception is raised
    :rtype: Dict[str, Any]
    """
    for field_name, field in cls.Meta.model_fields.items():
        if check_if_field_has_choices(field):
            value = values.get(field_name, ormar.Undefined)
            validate_choices(field=field, value=value)
    return values


def generate_model_example(model: Type["Model"], relation_map: Dict = None) -> Dict:
    """
    Generates example to be included in schema in fastapi.

    :param model: ormar.Model
    :type model: Type["Model"]
    :param relation_map: dict with relations to follow
    :type relation_map: Optional[Dict]
    :return:
    :rtype: Dict[str, int]
    """
    example: Dict[str, Any] = dict()
    relation_map = (
        relation_map
        if relation_map is not None
        else translate_list_to_dict(model._iterate_related_models())
    )
    for name, field in model.Meta.model_fields.items():
        if not field.is_relation:
            example[name] = field.__sample__
        elif isinstance(relation_map, dict) and name in relation_map:
            example[name] = get_nested_model_example(
                name=name, field=field, relation_map=relation_map
            )
    to_exclude = {name for name in model.Meta.model_fields}
    pydantic_repr = generate_pydantic_example(pydantic_model=model, exclude=to_exclude)
    example.update(pydantic_repr)

    return example


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
    elif issubclass(type_, pydantic.BaseModel):
        return generate_pydantic_example(pydantic_model=type_)
    else:
        return "string"


def construct_modify_schema_function(fields_with_choices: List) -> SchemaExtraCallable:
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
        schema["example"] = generate_model_example(model=model)
        if "Main base class of ormar Model." in schema.get("description", ""):
            schema["description"] = f"{model.__name__}"

    return staticmethod(schema_extra)  # type: ignore


def construct_schema_function_without_choices() -> SchemaExtraCallable:
    """
    Modifies model example and description if needed.

    Note that schema extra has to be a function, otherwise it's called to soon
    before all the relations are expanded.

    :return: callable that will be run by pydantic to modify the schema
    :rtype: Callable
    """

    def schema_extra(schema: Dict[str, Any], model: Type["Model"]) -> None:
        schema["example"] = generate_model_example(model=model)
        if "Main base class of ormar Model." in schema.get("description", ""):
            schema["description"] = f"{model.__name__}"

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
        for name, field in model.Meta.model_fields.items():
            if check_if_field_has_choices(field):
                fields_with_choices.append(name)
                validators = getattr(model, "__pre_root_validators__", [])
                if choices_validator not in validators:
                    validators.append(choices_validator)
                    model.__pre_root_validators__ = validators
                if not model._choices_fields:
                    model._choices_fields = set()
                model._choices_fields.add(name)

        if fields_with_choices:
            model.Config.schema_extra = construct_modify_schema_function(
                fields_with_choices=fields_with_choices
            )
        else:
            model.Config.schema_extra = construct_schema_function_without_choices()
