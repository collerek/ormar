from typing import Dict, List, Optional, TYPE_CHECKING, Type

from pydantic.typing import ForwardRef
import ormar  # noqa: I100

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


def validate_related_names_in_relations(  # noqa CCR001
    model_fields: Dict, new_model: Type["Model"]
) -> None:
    """
    Performs a validation of relation_names in relation fields.
    If multiple fields are leading to the same related model
    only one can have empty related_name param
    (populated by default as model.name.lower()+'s').
    Also related_names have to be unique for given related model.

    :raises ModelDefinitionError: if validation of related_names fail
    :param model_fields: dictionary of declared ormar model fields
    :type model_fields: Dict[str, ormar.Field]
    :param new_model:
    :type new_model: Model class
    """
    already_registered: Dict[str, List[Optional[str]]] = dict()
    for field in model_fields.values():
        if field.is_relation:
            to_name = (
                field.to.get_name()
                if not field.to.__class__ == ForwardRef
                else str(field.to)
            )
            previous_related_names = already_registered.setdefault(to_name, [])
            if field.related_name in previous_related_names:
                raise ormar.ModelDefinitionError(
                    f"Multiple fields declared on {new_model.get_name(lower=False)} "
                    f"model leading to {field.to.get_name(lower=False)} model without "
                    f"related_name property set. \nThere can be only one relation with "
                    f"default/empty name: '{new_model.get_name() + 's'}'"
                    f"\nTip: provide different related_name for FK and/or M2M fields"
                )
            previous_related_names.append(field.related_name)
