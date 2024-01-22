import base64
import datetime
import decimal
import uuid
from typing import Any, Callable, Dict, Optional, Union

import pydantic
from pydantic_core import SchemaValidator, core_schema

try:
    import orjson as json
except ImportError:  # pragma: no cover
    import json  # type: ignore


def parse_bool(value: str) -> bool:
    return value == "true"


def encode_bool(value: bool) -> str:
    return "true" if value else "false"


def encode_decimal(value: decimal.Decimal, precision: int = None) -> float:
    if precision:
        return (
            round(float(value), precision)
            if isinstance(value, decimal.Decimal)
            else value
        )
    return float(value)


def encode_bytes(value: Union[str, bytes], represent_as_string: bool = False) -> bytes:
    if represent_as_string:
        value=  value if isinstance(value, bytes) else base64.b64decode(value)
    else:
        value = value if isinstance(value, bytes) else value.encode("utf-8")
    print(' encode_bytes: value =', value)
    return value


def encode_json(value: Any) -> Optional[str]:
    if isinstance(value, (datetime.date, datetime.datetime, datetime.time)):
        value = value.isoformat()
    value = json.dumps(value) if not isinstance(value, str) else re_dump_value(value)
    value = value.decode("utf-8") if isinstance(value, bytes) else value
    print(' encode_json: value =', value)
    return value


def re_dump_value(value: str) -> Union[str, bytes]:
    """
    Rw-dumps choices due to different string representation in orjson and json
    :param value: string to re-dump
    :type value: str
    :return: re-dumped choices
    :rtype: List[str]
    """
    try:
        result: Union[str, bytes] = json.dumps(json.loads(value))
    except json.JSONDecodeError:
        result = value
    return result


ENCODERS_MAP: Dict[type, Callable] = {
    datetime.datetime: lambda x: x.isoformat(),
    datetime.date: lambda x: x.isoformat(),
    datetime.time: lambda x: x.isoformat(),
    pydantic.Json: encode_json,
    decimal.Decimal: encode_decimal,
    uuid.UUID: str,
    bytes: encode_bytes,
}

SQL_ENCODERS_MAP: Dict[type, Callable] = {bool: encode_bool, **ENCODERS_MAP}


DECODERS_MAP = {
    bool: parse_bool,
    datetime.datetime: SchemaValidator(core_schema.datetime_schema()).validate_python,
    datetime.date: SchemaValidator(core_schema.date_schema()).validate_python,
    datetime.time: SchemaValidator(core_schema.time_schema()).validate_python,
    pydantic.Json: json.loads,
    decimal.Decimal: decimal.Decimal,
}
