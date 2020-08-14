from typing import Any, List, Optional, TYPE_CHECKING, Type, Union

import sqlalchemy
from pydantic import BaseModel

import orm  # noqa I101
from orm.exceptions import RelationshipInstanceError
from orm.fields.base import BaseField

if TYPE_CHECKING:  # pragma no cover
    from orm.models import Model


def create_dummy_instance(fk: Type["Model"], pk: Any = None) -> "Model":
    init_dict = {
        **{fk.__pkname__: pk or -1},
        **{
            k: create_dummy_instance(v.to)
            for k, v in fk.__model_fields__.items()
            if isinstance(v, ForeignKey) and not v.nullable and not v.virtual
        },
    }
    return fk(**init_dict)


class ForeignKey(BaseField):
    def __init__(
        self,
        to: Type["Model"],
        name: str = None,
        related_name: str = None,
        nullable: bool = True,
        virtual: bool = False,
    ) -> None:
        super().__init__(nullable=nullable, name=name)
        self.virtual = virtual
        self.related_name = related_name
        self.to = to

    @property
    def __type__(self) -> Type[BaseModel]:
        return self.to.__pydantic_model__

    def get_constraints(self) -> List[sqlalchemy.schema.ForeignKey]:
        fk_string = self.to.__tablename__ + "." + self.to.__pkname__
        return [sqlalchemy.schema.ForeignKey(fk_string)]

    def get_column_type(self) -> sqlalchemy.Column:
        to_column = self.to.__model_fields__[self.to.__pkname__]
        return to_column.get_column_type()

    def _extract_model_from_sequence(
        self, value: List, child: "Model"
    ) -> Union["Model", List["Model"]]:
        return [self.expand_relationship(val, child) for val in value]

    def _register_existing_model(self, value: "Model", child: "Model") -> "Model":
        self.register_relation(value, child)
        return value

    def _construct_model_from_dict(self, value: dict, child: "Model") -> "Model":
        model = self.to(**value)
        self.register_relation(model, child)
        return model

    def _construct_model_from_pk(self, value: Any, child: "Model") -> "Model":
        if not isinstance(value, self.to.pk_type()):
            raise RelationshipInstanceError(
                f"Relationship error - ForeignKey {self.to.__name__} "
                f"is of type {self.to.pk_type()} "
                f"while {type(value)} passed as a parameter."
            )
        model = create_dummy_instance(fk=self.to, pk=value)
        self.register_relation(model, child)
        return model

    def register_relation(self, model: "Model", child: "Model") -> None:
        child_model_name = self.related_name or child.get_name()
        model._orm_relationship_manager.add_relation(
            model, child, child_model_name, virtual=self.virtual
        )

    def expand_relationship(
        self, value: Any, child: "Model"
    ) -> Optional[Union["Model", List["Model"]]]:

        if value is None:
            return None

        constructors = {
            f"{self.to.__name__}": self._register_existing_model,
            "dict": self._construct_model_from_dict,
            "list": self._extract_model_from_sequence,
        }

        model = constructors.get(
            value.__class__.__name__, self._construct_model_from_pk
        )(value, child)
        return model
