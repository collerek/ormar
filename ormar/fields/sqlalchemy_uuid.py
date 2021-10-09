import uuid
from typing import Any, Optional

from sqlalchemy import CHAR
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class UUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses CHAR(36) if in a string mode, otherwise uses CHAR(32), to store UUID.

    For details for different methods check documentation of parent class.
    """

    impl = CHAR

    def __init__(self, *args: Any, uuid_format: str = "hex", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.uuid_format = uuid_format

    def __repr__(self) -> str:  # pragma: nocover
        if self.uuid_format == "string":
            return "CHAR(36)"
        return "CHAR(32)"

    def load_dialect_impl(self, dialect: Dialect) -> Any:
        return (
            dialect.type_descriptor(CHAR(36))
            if self.uuid_format == "string"
            else dialect.type_descriptor(CHAR(32))
        )

    def process_bind_param(self, value: uuid.UUID, dialect: Dialect) -> Optional[str]:
        if value is None:
            return value
        return str(value) if self.uuid_format == "string" else "%.32x" % value.int

    def process_result_value(
        self, value: Optional[str], dialect: Dialect
    ) -> Optional[uuid.UUID]:
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(value)
        return value  # pragma: nocover
