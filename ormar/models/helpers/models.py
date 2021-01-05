from typing import Dict, List, Optional, TYPE_CHECKING, Tuple, Type

import ormar
from ormar.fields.foreign_key import ForeignKeyField
from ormar.models.helpers.pydantic import populate_pydantic_default_values

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


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
def validate_related_names_in_relations(
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
            previous_related_names = already_registered.setdefault(field.to, [])
            if field.related_name in previous_related_names:
                raise ormar.ModelDefinitionError(
                    f"Multiple fields declared on {new_model.get_name(lower=False)} "
                    f"model leading to {field.to.get_name(lower=False)} model without "
                    f"related_name property set. \nThere can be only one relation with "
                    f"default/empty name: '{new_model.get_name() + 's'}'"
                    f"\nTip: provide different related_name for FK and/or M2M fields"
                )
            previous_related_names.append(field.related_name)
