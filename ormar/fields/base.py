from typing import Any, List, Optional, TYPE_CHECKING, Type, Union

import sqlalchemy
from pydantic import Field, Json, typing
from pydantic.fields import FieldInfo, Required, Undefined

import ormar  # noqa I101
from ormar import ModelDefinitionError
from ormar.fields.sqlalchemy_encrypted import (
    EncryptBackend,
    EncryptBackends,
    EncryptedString,
)

if TYPE_CHECKING:  # pragma no cover
    from ormar.models import Model
    from ormar.models import NewBaseModel


class BaseField(FieldInfo):
    """
    BaseField serves as a parent class for all basic Fields in ormar.
    It keeps all common parameters available for all fields as well as
    set of useful functions.

    All values are kept as class variables, ormar Fields are never instantiated.
    Subclasses pydantic.FieldInfo to keep the fields related
    to pydantic field types like ConstrainedStr
    """

    __type__ = None
    related_name = None

    column_type: sqlalchemy.Column
    constraints: List = []
    name: str
    alias: str

    primary_key: bool
    autoincrement: bool
    nullable: bool
    index: bool
    unique: bool
    pydantic_only: bool
    choices: typing.Sequence

    virtual: bool = False  # ManyToManyFields and reverse ForeignKeyFields
    is_multi: bool = False  # ManyToManyField
    is_relation: bool = False  # ForeignKeyField + subclasses
    is_through: bool = False  # ThroughFields

    owner: Type["Model"]
    to: Type["Model"]
    through: Type["Model"]
    self_reference: bool = False
    self_reference_primary: Optional[str] = None
    orders_by: Optional[List[str]] = None
    related_orders_by: Optional[List[str]] = None

    encrypt_secret: str
    encrypt_backend: EncryptBackends = EncryptBackends.NONE
    encrypt_custom_backend: Optional[Type[EncryptBackend]] = None

    default: Any
    server_default: Any

    @classmethod
    def is_valid_uni_relation(cls) -> bool:
        """
        Checks if field is a relation definition but only for ForeignKey relation,
        so excludes ManyToMany fields, as well as virtual ForeignKey
        (second side of FK relation).

        Is used to define if a field is a db ForeignKey column that
        should be saved/populated when dealing with internal/own
        Model columns only.

        :return: result of the check
        :rtype: bool
        """
        return not cls.is_multi and not cls.virtual

    @classmethod
    def get_alias(cls) -> str:
        """
        Used to translate Model column names to database column names during db queries.

        :return: returns custom database column name if defined by user,
        otherwise field name in ormar/pydantic
        :rtype: str
        """
        return cls.alias if cls.alias else cls.name

    @classmethod
    def is_valid_field_info_field(cls, field_name: str) -> bool:
        """
        Checks if field belongs to pydantic FieldInfo
        - used during setting default pydantic values.
        Excludes defaults and alias as they are populated separately
        (defaults) or not at all (alias)

        :param field_name: field name of BaseFIeld
        :type field_name: str
        :return: True if field is present on pydantic.FieldInfo
        :rtype: bool
        """
        return (
            field_name not in ["default", "default_factory", "alias", "allow_mutation"]
            and not field_name.startswith("__")
            and hasattr(cls, field_name)
            and not callable(getattr(cls, field_name))
        )

    @classmethod
    def get_base_pydantic_field_info(cls, allow_null: bool) -> FieldInfo:
        """
        Generates base pydantic.FieldInfo with only default and optionally
        required to fix pydantic Json field being set to required=False.
        Used in an ormar Model Metaclass.

        :param allow_null: flag if the default value can be None
        or if it should be populated by pydantic Undefined
        :type allow_null: bool
        :return: instance of base pydantic.FieldInfo
        :rtype: pydantic.FieldInfo
        """
        base = cls.default_value()
        if base is None:
            base = (
                FieldInfo(default=None)
                if (cls.nullable or allow_null)
                else FieldInfo(default=Undefined)
            )
        if cls.__type__ == Json and base.default is Undefined:
            base.default = Required
        return base

    @classmethod
    def convert_to_pydantic_field_info(cls, allow_null: bool = False) -> FieldInfo:
        """
        Converts a BaseField into pydantic.FieldInfo
        that is later easily processed by pydantic.
        Used in an ormar Model Metaclass.

        :param allow_null: flag if the default value can be None
        or if it should be populated by pydantic Undefined
        :type allow_null: bool
        :return: actual instance of pydantic.FieldInfo with all needed fields populated
        :rtype: pydantic.FieldInfo
        """
        base = cls.get_base_pydantic_field_info(allow_null=allow_null)
        for attr_name in FieldInfo.__dict__.keys():
            if cls.is_valid_field_info_field(attr_name):
                setattr(base, attr_name, cls.__dict__.get(attr_name))
        return base

    @classmethod
    def default_value(cls, use_server: bool = False) -> Optional[FieldInfo]:
        """
        Returns a FieldInfo instance with populated default
        (static) or default_factory (function).
        If the field is a autoincrement primary key the default is None.
        Otherwise field have to has either default, or default_factory populated.

        If all default conditions fail None is returned.

        Used in converting to pydantic FieldInfo.

        :param use_server: flag marking if server_default should be
        treated as default value, default False
        :type use_server: bool
        :return: returns a call to pydantic.Field
        which is returning a FieldInfo instance
        :rtype: Optional[pydantic.FieldInfo]
        """
        if cls.is_auto_primary_key():
            return Field(default=None)
        if cls.has_default(use_server=use_server):
            default = cls.default if cls.default is not None else cls.server_default
            if callable(default):
                return Field(default_factory=default)
            return Field(default=default)
        return None

    @classmethod
    def get_default(cls, use_server: bool = False) -> Any:  # noqa CCR001
        """
        Return default value for a field.
        If the field is Callable the function is called and actual result is returned.
        Used to populate default_values for pydantic Model in ormar Model Metaclass.

        :param use_server: flag marking if server_default should be
        treated as default value, default False
        :type use_server: bool
        :return: default value for the field if set, otherwise implicit None
        :rtype: Any
        """
        if cls.has_default():
            default = (
                cls.default
                if cls.default is not None
                else (cls.server_default if use_server else None)
            )
            if callable(default):
                default = default()
            return default

    @classmethod
    def has_default(cls, use_server: bool = True) -> bool:
        """
        Checks if the field has default value set.

        :param use_server: flag marking if server_default should be
        treated as default value, default False
        :type use_server: bool
        :return: result of the check if default value is set
        :rtype: bool
        """
        return cls.default is not None or (
            cls.server_default is not None and use_server
        )

    @classmethod
    def is_auto_primary_key(cls) -> bool:
        """
        Checks if field is first a primary key and if it,
        it's than check if it's set to autoincrement.
        Autoincrement primary_key is nullable/optional.

        :return: result of the check for primary key and autoincrement
        :rtype: bool
        """
        if cls.primary_key:
            return cls.autoincrement
        return False

    @classmethod
    def construct_constraints(cls) -> List:
        """
        Converts list of ormar constraints into sqlalchemy ForeignKeys.
        Has to be done dynamically as sqlalchemy binds ForeignKey to the table.
        And we need a new ForeignKey for subclasses of current model

        :return: List of sqlalchemy foreign keys - by default one.
        :rtype: List[sqlalchemy.schema.ForeignKey]
        """
        constraints = [
            sqlalchemy.ForeignKey(
                con.reference,
                ondelete=con.ondelete,
                onupdate=con.onupdate,
                name=f"fk_{cls.owner.Meta.tablename}_{cls.to.Meta.tablename}"
                f"_{cls.to.get_column_alias(cls.to.Meta.pkname)}_{cls.name}",
            )
            for con in cls.constraints
        ]
        return constraints

    @classmethod
    def get_column(cls, name: str) -> sqlalchemy.Column:
        """
        Returns definition of sqlalchemy.Column used in creation of sqlalchemy.Table.
        Populates name, column type constraints, as well as a number of parameters like
        primary_key, index, unique, nullable, default and server_default.

        :param name: name of the db column - used if alias is not set
        :type name: str
        :return: actual definition of the database column as sqlalchemy requires.
        :rtype: sqlalchemy.Column
        """
        if cls.encrypt_backend == EncryptBackends.NONE:
            column = sqlalchemy.Column(
                cls.alias or name,
                cls.column_type,
                *cls.construct_constraints(),
                primary_key=cls.primary_key,
                nullable=cls.nullable and not cls.primary_key,
                index=cls.index,
                unique=cls.unique,
                default=cls.default,
                server_default=cls.server_default,
            )
        else:
            column = cls._get_encrypted_column(name=name)
        return column

    @classmethod
    def _get_encrypted_column(cls, name: str) -> sqlalchemy.Column:
        """
        Returns EncryptedString column type instead of actual column.

        :param name: column name
        :type name: str
        :return: newly defined column
        :rtype:  sqlalchemy.Column
        """
        if cls.primary_key or cls.is_relation:
            raise ModelDefinitionError(
                "Primary key field and relations fields" "cannot be encrypted!"
            )
        column = sqlalchemy.Column(
            cls.alias or name,
            EncryptedString(
                _field_type=cls,
                encrypt_secret=cls.encrypt_secret,
                encrypt_backend=cls.encrypt_backend,
                encrypt_custom_backend=cls.encrypt_custom_backend,
            ),
            nullable=cls.nullable,
            index=cls.index,
            unique=cls.unique,
            default=cls.default,
            server_default=cls.server_default,
        )
        return column

    @classmethod
    def expand_relationship(
        cls,
        value: Any,
        child: Union["Model", "NewBaseModel"],
        to_register: bool = True,
    ) -> Any:
        """
        Function overwritten for relations, in basic field the value is returned as is.
        For relations the child model is first constructed (if needed),
        registered in relation and returned.
        For relation fields the value can be a pk value (Any type of field),
        dict (from Model) or actual instance/list of a "Model".

        :param value: a Model field value, returned untouched for non relation fields.
        :type value: Any
        :param child: a child Model to register
        :type child: Union["Model", "NewBaseModel"]
        :param to_register: flag if the relation should be set in RelationshipManager
        :type to_register: bool
        :return: returns untouched value for normal fields, expands only for relations
        :rtype: Any
        """
        return value

    @classmethod
    def set_self_reference_flag(cls) -> None:
        """
        Sets `self_reference` to True if field to and owner are same model.
        :return: None
        :rtype: None
        """
        if cls.owner is not None and (
            cls.owner == cls.to or cls.owner.Meta == cls.to.Meta
        ):
            cls.self_reference = True
            cls.self_reference_primary = cls.name

    @classmethod
    def has_unresolved_forward_refs(cls) -> bool:
        """
        Verifies if the filed has any ForwardRefs that require updating before the
        model can be used.

        :return: result of the check
        :rtype: bool
        """
        return False

    @classmethod
    def evaluate_forward_ref(cls, globalns: Any, localns: Any) -> None:
        """
        Evaluates the ForwardRef to actual Field based on global and local namespaces

        :param globalns: global namespace
        :type globalns: Any
        :param localns: local namespace
        :type localns: Any
        :return: None
        :rtype: None
        """

    @classmethod
    def get_related_name(cls) -> str:
        """
        Returns name to use for reverse relation.
        It's either set as `related_name` or by default it's owner model. get_name + 's'
        :return: name of the related_name or default related name.
        :rtype: str
        """
        return ""  # pragma: no cover
