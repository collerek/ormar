import sys
from typing import Any, List, Optional, TYPE_CHECKING, Tuple, Type, Union, cast

from pydantic.typing import ForwardRef, evaluate_forwardref
import ormar  # noqa: I100
from ormar import ModelDefinitionError
from ormar.fields import BaseField
from ormar.fields.foreign_key import ForeignKeyField, validate_not_allowed_fields

if TYPE_CHECKING:  # pragma no cover
    from ormar.models import Model

    if sys.version_info < (3, 7):
        ToType = Type["Model"]
    else:
        ToType = Union[Type["Model"], "ForwardRef"]

REF_PREFIX = "#/components/schemas/"


def forbid_through_relations(through: Type["Model"]) -> None:
    """
    Verifies if the through model does not have relations.

    :param through: through Model to be checked
    :type through: Type['Model]
    """
    if any(field.is_relation for field in through.Meta.model_fields.values()):
        raise ModelDefinitionError(
            f"Through Models cannot have explicit relations "
            f"defined. Remove the relations from Model "
            f"{through.get_name(lower=False)}"
        )


def populate_m2m_params_based_on_to_model(
    to: Type["Model"], nullable: bool
) -> Tuple[Any, Any]:
    """
    Based on target to model to which relation leads to populates the type of the
    pydantic field to use and type of the target column field.

    :param to: target related ormar Model
    :type to: Model class
    :param nullable: marks field as optional/ required
    :type nullable: bool
    :return: Tuple[List, Any]
    :rtype: tuple with target pydantic type and target col type
    """
    to_field = to.Meta.model_fields[to.Meta.pkname]
    __type__ = (
        Union[to_field.__type__, to, List[to]]  # type: ignore
        if not nullable
        else Optional[Union[to_field.__type__, to, List[to]]]  # type: ignore
    )
    column_type = to_field.column_type
    return __type__, column_type


def ManyToMany(
    to: "ToType",
    through: Optional["ToType"] = None,
    *,
    name: str = None,
    unique: bool = False,
    virtual: bool = False,
    **kwargs: Any,
) -> Any:
    """
    Despite a name it's a function that returns constructed ManyToManyField.
    This function is actually used in model declaration
    (as ormar.ManyToMany(ToModel, through=ThroughModel)).

    Accepts number of relation setting parameters as well as all BaseField ones.

    :param to: target related ormar Model
    :type to: Model class
    :param through: through model for m2m relation
    :type through: Model class
    :param name: name of the database field - later called alias
    :type name: str
    :param unique: parameter passed to sqlalchemy.ForeignKey, unique flag
    :type unique: bool
    :param virtual: marks if relation is virtual.
    It is for reversed FK and auto generated FK on through model in Many2Many relations.
    :type virtual: bool
    :param kwargs: all other args to be populated by BaseField
    :type kwargs: Any
    :return: ormar ManyToManyField with m2m relation to selected model
    :rtype: ManyToManyField
    """
    related_name = kwargs.pop("related_name", None)
    nullable = kwargs.pop("nullable", True)
    owner = kwargs.pop("owner", None)
    self_reference = kwargs.pop("self_reference", False)
    orders_by = kwargs.pop("orders_by", None)
    related_orders_by = kwargs.pop("related_orders_by", None)

    if through is not None and through.__class__ != ForwardRef:
        forbid_through_relations(cast(Type["Model"], through))

    validate_not_allowed_fields(kwargs)

    if to.__class__ == ForwardRef:
        __type__ = to if not nullable else Optional[to]
        column_type = None
    else:
        __type__, column_type = populate_m2m_params_based_on_to_model(
            to=to, nullable=nullable  # type: ignore
        )
    namespace = dict(
        __type__=__type__,
        to=to,
        through=through,
        alias=name,
        name=name,
        nullable=nullable,
        unique=unique,
        column_type=column_type,
        related_name=related_name,
        virtual=virtual,
        primary_key=False,
        index=False,
        pydantic_only=False,
        default=None,
        server_default=None,
        owner=owner,
        self_reference=self_reference,
        is_relation=True,
        is_multi=True,
        orders_by=orders_by,
        related_orders_by=related_orders_by,
    )

    return type("ManyToMany", (ManyToManyField, BaseField), namespace)


class ManyToManyField(ForeignKeyField, ormar.QuerySetProtocol, ormar.RelationProtocol):
    """
    Actual class returned from ManyToMany function call and stored in model_fields.
    """

    @classmethod
    def get_source_related_name(cls) -> str:
        """
        Returns name to use for source relation name.
        For FK it's the same, differs for m2m fields.
        It's either set as `related_name` or by default it's field name.
        :return: name of the related_name or default related name.
        :rtype: str
        """
        return (
            cls.through.Meta.model_fields[cls.default_source_field_name()].related_name
            or cls.name
        )

    @classmethod
    def default_target_field_name(cls) -> str:
        """
        Returns default target model name on through model.
        :return: name of the field
        :rtype: str
        """
        prefix = "from_" if cls.self_reference else ""
        return f"{prefix}{cls.to.get_name()}"

    @classmethod
    def default_source_field_name(cls) -> str:
        """
        Returns default target model name on through model.
        :return: name of the field
        :rtype: str
        """
        prefix = "to_" if cls.self_reference else ""
        return f"{prefix}{cls.owner.get_name()}"

    @classmethod
    def has_unresolved_forward_refs(cls) -> bool:
        """
        Verifies if the filed has any ForwardRefs that require updating before the
        model can be used.

        :return: result of the check
        :rtype: bool
        """
        return cls.to.__class__ == ForwardRef or cls.through.__class__ == ForwardRef

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
        if cls.to.__class__ == ForwardRef:
            cls.to = evaluate_forwardref(
                cls.to,  # type: ignore
                globalns,
                localns or None,
            )

            (cls.__type__, cls.column_type,) = populate_m2m_params_based_on_to_model(
                to=cls.to, nullable=cls.nullable,
            )

        if cls.through.__class__ == ForwardRef:
            cls.through = evaluate_forwardref(
                cls.through,  # type: ignore
                globalns,
                localns or None,
            )
            forbid_through_relations(cls.through)

    @classmethod
    def get_relation_name(cls) -> str:
        """
        Returns name of the relation, which can be a own name or through model
        names for m2m models

        :return: result of the check
        :rtype: bool
        """
        if cls.self_reference and cls.name == cls.self_reference_primary:
            return cls.default_source_field_name()
        return cls.default_target_field_name()

    @classmethod
    def get_source_model(cls) -> Type["Model"]:
        """
        Returns model from which the relation comes -> either owner or through model

        :return: source model
        :rtype: Type["Model"]
        """
        return cls.through

    @classmethod
    def create_default_through_model(cls) -> None:
        """
        Creates default empty through model if no additional fields are required.
        """
        owner_name = cls.owner.get_name(lower=False)
        to_name = cls.to.get_name(lower=False)
        class_name = f"{owner_name}{to_name}"
        table_name = f"{owner_name.lower()}s_{to_name.lower()}s"
        new_meta_namespace = {
            "tablename": table_name,
            "database": cls.owner.Meta.database,
            "metadata": cls.owner.Meta.metadata,
        }
        new_meta = type("Meta", (), new_meta_namespace)
        through_model = type(class_name, (ormar.Model,), {"Meta": new_meta})
        cls.through = cast(Type["Model"], through_model)
