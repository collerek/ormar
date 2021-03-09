# inspired by sqlalchemy-utils (https://github.com/kvesteri/sqlalchemy-utils)
import abc
import base64
import datetime
import json
from enum import Enum
from typing import Any, Callable, TYPE_CHECKING, Type, Union

import sqlalchemy.types as types
from sqlalchemy.engine.default import DefaultDialect

from ormar import ModelDefinitionError

cryptography = None
try:
    import cryptography
    from cryptography.fernet import Fernet
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
except ImportError:
    pass

if TYPE_CHECKING:
    from ormar import BaseField


class EncryptBackend(abc.ABC):

    def _update_key(self, key):
        if isinstance(key, str):
            key = key.encode()
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(key)
        engine_key = digest.finalize()

        self._initialize_engine(engine_key)

    @abc.abstractmethod
    def _initialize_engine(self, secret_key: bytes):
        pass

    @abc.abstractmethod
    def encrypt(self, value: Any) -> str:
        pass

    @abc.abstractmethod
    def decrypt(self, value: Any) -> str:
        pass


class HashBackend(EncryptBackend):
    """
    One-way hashing - in example for passwords, no way to decrypt the value!
    """

    def _initialize_engine(self, secret_key: bytes):
        self.secret_key = base64.urlsafe_b64encode(secret_key)

    def encrypt(self, value: Any) -> str:
        if not isinstance(value, str):
            value = repr(value)
        value = value.encode()
        digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
        digest.update(self.secret_key)
        digest.update(value)
        hashed_value = digest.finalize()
        return hashed_value.hex()

    def decrypt(self, value: Any) -> str:
        if not isinstance(value, str):
            value = str(value)
        return value


class FernetBackend(EncryptBackend):
    """
    Two-way encryption, data stored in db are encrypted but decrypted during query.
    """

    def _initialize_engine(self, secret_key: bytes):
        self.secret_key = base64.urlsafe_b64encode(secret_key)
        self.fernet = Fernet(self.secret_key)

    def encrypt(self, value: Any) -> str:
        if not isinstance(value, str):
            value = repr(value)
        value = value.encode()
        encrypted = self.fernet.encrypt(value)
        return encrypted.decode('utf-8')

    def decrypt(self, value: Any) -> str:
        if not isinstance(value, str):
            value = str(value)
        decrypted = self.fernet.decrypt(value.encode())
        if not isinstance(decrypted, str):
            decrypted = decrypted.decode('utf-8')
        return decrypted


class EncryptBackends(Enum):
    NONE = 0
    FERNET = 1
    HASH = 2
    CUSTOM = 3


backends_map = {
    EncryptBackends.FERNET: FernetBackend,
    EncryptBackends.HASH: HashBackend,
    EncryptBackends.CUSTOM: None
}


class EncryptedString(types.TypeDecorator):  # pragma nocover
    """
    Used to store encrypted values in a database
    """

    impl = types.TypeEngine

    def __init__(self,
                 *args: Any,
                 encrypt_secret: Union[str, Callable],
                 _field_type: Type["BaseField"],
                 encrypt_max_length: int = 5000,
                 encrypt_backend: EncryptBackends = EncryptBackends.FERNET,
                 encrypt_custom_backend: Type[EncryptBackend] = None,
                 **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not cryptography:
            raise ModelDefinitionError(
                "In order to encrypt a column 'cryptography' is required!"
            )
        backend = backends_map.get(encrypt_backend, encrypt_custom_backend)
        if not backend or not issubclass(backend, EncryptBackend):
            raise ModelDefinitionError("Wrong or no encrypt backend provided!")
        self.backend = backend()
        self._field_type = _field_type
        self._underlying_type = _field_type.column_type
        self._key = encrypt_secret
        self.max_length = encrypt_max_length

    def __repr__(self) -> str:
        return f"VARCHAR({self.max_length})"

    def load_dialect_impl(self, dialect: DefaultDialect) -> Any:
        return dialect.type_descriptor(types.VARCHAR(self.max_length))

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value

    def _update_key(self):
        key = self._key() if callable(self._key) else self._key
        self.backend._update_key(key)

    def process_bind_param(self, value, dialect):
        """Encrypt a value on the way in."""
        if value is not None:
            self._update_key()

            try:
                value = self._underlying_type.process_bind_param(
                    value, dialect
                )

            except AttributeError:
                # Doesn't have 'process_bind_param'
                type_ = self._field_type.__type__
                if issubclass(type_, bool):
                    value = 'true' if value else 'false'

                elif issubclass(type_, (datetime.date, datetime.time)):
                    value = value.isoformat()

                # elif issubclass(type_, JSONType):
                #     value = json.dumps(value)

            return self.backend.encrypt(value)

    def process_result_value(self, value, dialect):
        """Decrypt value on the way out."""
        if value is not None:
            self._update_key()
            decrypted_value = self.backend.decrypt(value)

            try:
                return self.underlying_type.process_result_value(
                    decrypted_value, dialect
                )

            except AttributeError:
                # Doesn't have 'process_result_value'

                # Handle 'boolean' and 'dates'
                type_ = self._field_type.__type__
                # date_types = [datetime.datetime, datetime.time, datetime.date]

                if issubclass(type_, bool):
                    return decrypted_value == 'true'

                # elif type_ in date_types:
                #     return DatetimeHandler.process_value(
                #         decrypted_value, type_
                #     )

                # elif issubclass(type_, JSONType):
                #     return json.loads(decrypted_value)

                # Handle all others
                return self.underlying_type.python_type(decrypted_value)

    def _coerce(self, value):
        return self.underlying_type._coerce(value)
