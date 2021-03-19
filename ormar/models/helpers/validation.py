import datetime
import decimal
import uuid
from enum import Enum
from typing import Any, Dict, List, TYPE_CHECKING, Tuple, Type

try:
    import orjson as json
except ImportError:  # pragma: no cover
    import json  # type: ignore

import pydantic
from pydantic.main import SchemaExtraCallable

import ormar  # noqa: I100, I202
from ormar.fields import BaseField
from ormar.models.helpers.models import meta_field_not_set

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


def construct_modify_schema_function(fields_with_choices: List) -> SchemaExtraCallable:
    """
    Modifies the schema to include fields with choices validator.
    Those fields will be displayed in schema as Enum types with available choices
    values listed next to them.

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
