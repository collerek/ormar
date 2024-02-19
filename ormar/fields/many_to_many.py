from typing import (
    TYPE_CHECKING,
    Any,
    ForwardRef,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
    overload,
)

import ormar  # noqa: I100
from ormar import ModelDefinitionError
from ormar.fields import BaseField
from ormar.fields.foreign_key import (
    ForeignKeyField,
    create_dummy_model,
    validate_not_allowed_fields,
)

if TYPE_CHECKING:  # pragma no cover
    from ormar.models import Model, T
    from ormar.relations.relation_proxy import RelationProxy

REF_PREFIX = "#/components/schemas/"


def forbid_through_relations(through: Type["Model"]) -> None:
    """
    Verifies if the through model does not have relations.

    :param through: through Model to be checked
    :type through: Type['Model]
    """
    if any(field.is_relation for field in through.ormar_config.model_fields.values()):
        raise ModelDefinitionError(
            f"Through Models cannot have explicit relations "
            f"defined. Remove the relations from Model "
            f"{through.get_name(lower=False)}"
        )


def populate_m2m_params_based_on_to_model(
    to: Type["Model"], nullable: bool
) -> Tuple[Any, Any, Any]:
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
    to_field = to.ormar_config.model_fields[to.ormar_config.pkname]
    pk_only_model = create_dummy_model(to, to_field)
    base_type = Union[  # type: ignore
        to_field.__type__,  # type: ignore
        to,  # type: ignore
        pk_only_model,  # type: ignore
        List[to],  # type: ignore
        List[pk_only_model],  # type: ignore
    ]
    __type__ = (
        base_type  # type: ignore
        if not nullable
        else Optional[base_type]  # type: ignore
    )
    column_type = to_field.column_type
    return __type__, column_type, pk_only_model


@overload
def ManyToMany(to: Type["T"], **kwargs: Any) -> "RelationProxy[T]":  # pragma: no cover
    ...


@overload
def ManyToMany(to: ForwardRef, **kwargs: Any) -> "RelationProxy":  # pragma: no cover
    ...


def ManyToMany(  # type: ignore
    to: Union[Type["T"], "ForwardRef"],
    through: Optional[Union[Type["T"], "ForwardRef"]] = None,
    *,
    name: Optional[str] = None,
    unique: bool = False,
    virtual: bool = False,
    **kwargs: Any,
) -> "RelationProxy[T]":
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

    skip_reverse = kwargs.pop("skip_reverse", False)
    skip_field = kwargs.pop("skip_field", False)

    through_relation_name = kwargs.pop("through_relation_name", None)
    through_reverse_relation_name = kwargs.pop("through_reverse_relation_name", None)

    if through is not None and through.__class__ != ForwardRef:
        forbid_through_relations(cast(Type["Model"], through))

    validate_not_allowed_fields(kwargs)
    pk_only_model = None
    if to.__class__ == ForwardRef:
        __type__ = (
            Union[to, List[to]]  # type: ignore
            if not nullable
            else Optional[Union[to, List[to]]]  # type: ignore
        )
        column_type = None
    else:
        __type__, column_type, pk_only_model = populate_m2m_params_based_on_to_model(
            to=to, nullable=nullable  # type: ignore
        )
    namespace = dict(
        __type__=__type__,
        to=to,
        to_pk_only=pk_only_model,
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
        default=None,
        server_default=None,
        owner=owner,
        self_reference=self_reference,
        is_relation=True,
        is_multi=True,
        orders_by=orders_by,
        related_orders_by=related_orders_by,
        skip_reverse=skip_reverse,
        skip_field=skip_field,
        through_relation_name=through_relation_name,
        through_reverse_relation_name=through_reverse_relation_name,
    )

    Field = type("ManyToMany", (ManyToManyField, BaseField), {})
    return Field(**namespace)


class ManyToManyField(  # type: ignore
    ForeignKeyField,
    ormar.QuerySetProtocol,
    ormar.RelationProtocol,
):
    """
    Actual class returned from ManyToMany function call and stored in model_fields.
    """

    def __init__(self, **kwargs: Any) -> None:
        if TYPE_CHECKING:  # pragma: no cover
            self.__type__: type
            self.to: Type["Model"]
            self.through: Type["Model"]
        super().__init__(**kwargs)

    def get_source_related_name(self) -> str:
        """
        Returns name to use for source relation name.
        For FK it's the same, differs for m2m fields.
        It's either set as `related_name` or by default it's field name.
        :return: name of the related_name or default related name.
        :rtype: str
        """
        return (
            self.through.ormar_config.model_fields[
                self.default_source_field_name()
            ].related_name
            or self.name
        )

    def has_unresolved_forward_refs(self) -> bool:
        """
        Verifies if the filed has any ForwardRefs that require updating before the
        model can be used.

        :return: result of the check
        :rtype: bool
        """
        return self.to.__class__ == ForwardRef or self.through.__class__ == ForwardRef

    def evaluate_forward_ref(self, globalns: Any, localns: Any) -> None:
        """
        Evaluates the ForwardRef to actual Field based on global and local namespaces

        :param globalns: global namespace
        :type globalns: Any
        :param localns: local namespace
        :type localns: Any
        :return: None
        :rtype: None
        """
        if self.to.__class__ == ForwardRef:
            self._evaluate_forward_ref(globalns, localns)
            (
                self.__type__,
                self.column_type,
                pk_only_model,
            ) = populate_m2m_params_based_on_to_model(
                to=self.to, nullable=self.nullable
            )
            self.to_pk_only = pk_only_model

        if self.through.__class__ == ForwardRef:
            self._evaluate_forward_ref(globalns, localns, is_through=True)

            forbid_through_relations(self.through)

    def get_relation_name(self) -> str:
        """
        Returns name of the relation, which can be a own name or through model
        names for m2m models

        :return: result of the check
        :rtype: bool
        """
        if self.self_reference and self.name == self.self_reference_primary:
            return self.default_source_field_name()
        return self.default_target_field_name()

    def get_source_model(self) -> Type["Model"]:
        """
        Returns model from which the relation comes -> either owner or through model

        :return: source model
        :rtype: Type["Model"]
        """
        return self.through

    def create_default_through_model(self) -> None:
        """
        Creates default empty through model if no additional fields are required.
        """
        owner_name = self.owner.get_name(lower=False)
        to_name = self.to.get_name(lower=False)
        class_name = f"{owner_name}{to_name}"
        table_name = f"{owner_name.lower()}s_{to_name.lower()}s"
        base_namespace = {
            "__module__": self.owner.__module__,
            "__qualname__": f"{self.owner.__qualname__}.{class_name}",
        }
        new_config = ormar.models.ormar_config.OrmarConfig(
            tablename=table_name,
            database=self.owner.ormar_config.database,
            metadata=self.owner.ormar_config.metadata,
        )
        through_model = type(
            class_name,
            (ormar.Model,),
            {
                **base_namespace,
                "ormar_config": new_config,
                "id": ormar.Integer(name="id", primary_key=True),
            },
        )
        self.through = cast(Type["Model"], through_model)
