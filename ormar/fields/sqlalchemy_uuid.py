import uuid
from typing import Any, Optional, Union

from sqlalchemy.dialects.postgresql import UUID as psqlUUID
from sqlalchemy.engine.default import DefaultDialect
from sqlalchemy.types import CHAR, TypeDecorator


class UUID(TypeDecorator):  # pragma nocover
    """Platform-independent GUID type.

    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), to store UUID.

    """

    impl = CHAR

    def _cast_to_uuid(self, value: Union[str, int, bytes]) -> uuid.UUID:
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
        if dialect.name == "postgresql":
            return dialect.type_descriptor(psqlUUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(
        self, value: Union[str, int, bytes, uuid.UUID, None], dialect: DefaultDialect
    ) -> Optional[str]:
        if value is None:
            return value
        elif not isinstance(value, uuid.UUID):
            value = self._cast_to_uuid(value)
        if dialect.name == "postgresql":
            return str(value)
        else:
            return "%.32x" % value.int

    def process_result_value(
        self, value: Optional[str], dialect: DefaultDialect
    ) -> Optional[uuid.UUID]:
        if value is None:
            return value
        if dialect.name == "postgresql":
            return uuid.UUID(value)
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value
