import uuid
from typing import Any, Optional, Union

from sqlalchemy import CHAR
from sqlalchemy.engine.default import DefaultDialect
from sqlalchemy.types import TypeDecorator


class UUID(TypeDecorator):  # pragma nocover
    """
    Platform-independent GUID type.
    Uses CHAR(36) if in a string mode, otherwise uses CHAR(32), to store UUID.

    For details for different methods check documentation of parent class.
    """

    impl = CHAR

    def __init__(self, *args: Any, uuid_format: str = "hex", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.uuid_format = uuid_format

    def __repr__(self) -> str:
        if self.uuid_format == "string":
            return "CHAR(36)"
        return "CHAR(32)"

    def _cast_to_uuid(self, value: Union[str, int, bytes]) -> uuid.UUID:
        """
        Parses given value into uuid.UUID field.

        :param value: value to be parsed
        :type value: Union[str, int, bytes]
        :return: initialized uuid
        :rtype: uuid.UUID
        """
        if not isinstance(value, uuid.UUID):
            if isinstance(value, bytes):
                ret_value = uuid.UUID(bytes=value)
            elif isinstance(value, int):
                ret_value = uuid.UUID(int=value)
            elif isinstance(value, str):
                ret_value = uuid.UUID(value)
        else:
            ret_value = value
        return ret_value

    def load_dialect_impl(self, dialect: DefaultDialect) -> Any:
        return (
            dialect.type_descriptor(CHAR(36))
            if self.uuid_format == "string"
            else dialect.type_descriptor(CHAR(32))
        )

    def process_bind_param(
        self, value: Union[str, int, bytes, uuid.UUID, None], dialect: DefaultDialect
    ) -> Optional[str]:
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = self._cast_to_uuid(value)
        return str(value) if self.uuid_format == "string" else "%.32x" % value.int

    def process_result_value(
        self, value: Optional[str], dialect: DefaultDialect
    ) -> Optional[uuid.UUID]:
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(value)
        return value
