import itertools
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Type

import ormar  # noqa: I100
from ormar.fields.foreign_key import ForeignKeyField
from ormar.models.helpers.pydantic import populate_pydantic_default_values
from pydantic.typing import ForwardRef

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.fields import BaseField


def is_field_an_forward_ref(field: Type["BaseField"]) -> bool:
    """
    Checks if field is a relation field and whether any of the referenced models
    are ForwardRefs that needs to be updated before proceeding.

    :param field: model field to verify
    :type field: Type[BaseField]
    :return: result of the check
    :rtype: bool
    """
    return issubclass(field, ForeignKeyField) and (
        field.to.__class__ == ForwardRef or field.through.__class__ == ForwardRef
    )


def populate_default_options_values(
    new_model: Type["Model"], model_fields: Dict
) -> None:
    """
    Sets all optional Meta values to it's defaults
    and set model_fields that were already previously extracted.

    Here should live all options that are not overwritten/set for all models.

    Current options are:
    * constraints = []
    * abstract = False

    :param new_model: newly constructed Model
    :type new_model: Model class
    :param model_fields:
    :type model_fields: Union[Dict[str, type], Dict]
    """
    if not hasattr(new_model.Meta, "constraints"):
        new_model.Meta.constraints = []
    if not hasattr(new_model.Meta, "model_fields"):
        new_model.Meta.model_fields = model_fields
    if not hasattr(new_model.Meta, "abstract"):
        new_model.Meta.abstract = False

    if any(
        is_field_an_forward_ref(field) for field in new_model.Meta.model_fields.values()
    ):
        new_model.Meta.requires_ref_update = True
    else:
        new_model.Meta.requires_ref_update = False


def extract_annotations_and_default_vals(attrs: Dict) -> Tuple[Dict, Dict]:
    """
    Extracts annotations from class namespace dict and triggers
    extraction of ormar model_fields.

    :param attrs: namespace of the class created
    :type attrs: Dict
    :return: namespace of the class updated, dict of extracted model_fields
    :rtype: Tuple[Dict, Dict]
    """
    key = "__annotations__"
    attrs[key] = attrs.get(key, {})
    attrs, model_fields = populate_pydantic_default_values(attrs)
    return attrs, model_fields


# cannot be in relations helpers due to cyclical import
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
        if issubclass(field, ForeignKeyField):
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


def group_related_list(list_: List) -> Dict:
    """
    Translates the list of related strings into a dictionary.
    That way nested models are grouped to traverse them in a right order
    and to avoid repetition.

    Sample: ["people__houses", "people__cars__models", "people__cars__colors"]
    will become:
    {'people': {'houses': [], 'cars': ['models', 'colors']}}

    Result dictionary is sorted by length of the values and by key

    :param list_: list of related models used in select related
    :type list_: List[str]
    :return: list converted to dictionary to avoid repetition and group nested models
    :rtype: Dict[str, List]
    """
    result_dict: Dict[str, Any] = dict()
    list_.sort(key=lambda x: x.split("__")[0])
    grouped = itertools.groupby(list_, key=lambda x: x.split("__")[0])
    for key, group in grouped:
        group_list = list(group)
        new = sorted(
            ["__".join(x.split("__")[1:]) for x in group_list if len(x.split("__")) > 1]
        )
        if any("__" in x for x in new):
            result_dict[key] = group_related_list(new)
        else:
            result_dict.setdefault(key, []).extend(new)
    return {k: v for k, v in sorted(result_dict.items(), key=lambda item: len(item[1]))}
