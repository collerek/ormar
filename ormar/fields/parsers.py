import datetime
import decimal
from typing import Any

import pydantic
from pydantic.datetime_parse import parse_date, parse_datetime, parse_time

try:
    import orjson as json
except ImportError:  # pragma: no cover
    import json  # type: ignore


def parse_bool(value: str) -> bool:
    return value == "true"


def encode_bool(value: bool) -> str:
    return "true" if value else "false"


def encode_json(value: Any) -> str:
    value = json.dumps(value) if not isinstance(value, str) else value
    value = value.decode("utf-8") if isinstance(value, bytes) else value
    return value


ENCODERS_MAP = {
    bool: encode_bool,
    datetime.datetime: lambda x: x.isoformat(),
    datetime.date: lambda x: x.isoformat(),
    datetime.time: lambda x: x.isoformat(),
    pydantic.Json: encode_json,
    decimal.Decimal: float,
}

DECODERS_MAP = {
    bool: parse_bool,
    datetime.datetime: parse_datetime,
    datetime.date: parse_date,
    datetime.time: parse_time,
    pydantic.Json: json.loads,
    decimal.Decimal: decimal.Decimal,
}
