from typing import Any, List, Optional, TYPE_CHECKING, Tuple, Type, Union

import sqlalchemy
from pydantic import BaseModel

import orm  # noqa I101
from orm.exceptions import RelationshipInstanceError
from orm.fields.base import BaseField

if TYPE_CHECKING:  # pragma no cover
    from orm.models import Model


def create_dummy_instance(fk: Type["Model"], pk: int = None) -> "Model":
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

    def extract_model_from_sequence(
        self, value: Any, child: "Model"
    ) -> Tuple[Union["Model", List["Model"]], bool]:
        if isinstance(value, list) and not isinstance(value, self.to):
            model = [self.expand_relationship(val, child) for val in value]
            return model, True

        if isinstance(value, self.to):
            model = value
        else:
            model = self.to(**value)
        return model, False

    def construct_model_from_pk(self, value: Any) -> "Model":
        if not isinstance(value, self.to.pk_type()):
            raise RelationshipInstanceError(
                f"Relationship error - ForeignKey {self.to.__name__} "
                f"is of type {self.to.pk_type()} "
                f"while {type(value)} passed as a parameter."
            )
        return create_dummy_instance(fk=self.to, pk=value)

    def expand_relationship(
        self, value: Any, child: "Model"
    ) -> Optional[Union["Model", List["Model"]]]:

        if value is None:
            return None

        is_sequence = False

        if isinstance(value, orm.models.Model) and not isinstance(value, self.to):
            raise RelationshipInstanceError(
                f"Relationship error - expecting: {self.to.__name__}, "
                f"but {value.__class__.__name__} encountered."
            )

        if isinstance(value, (dict, list, self.to)):
            model, is_sequence = self.extract_model_from_sequence(value, child)
        else:
            model = self.construct_model_from_pk(value)

        if not is_sequence:
            model._orm_relationship_manager.add_relation(
                model, child, virtual=self.virtual
            )

        return model
