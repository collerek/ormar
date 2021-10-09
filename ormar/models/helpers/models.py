import collections
import itertools
import sqlite3
from typing import Any, Dict, List, TYPE_CHECKING, Tuple, Type

import pydantic
from pydantic.typing import ForwardRef
import ormar  # noqa: I100
from ormar.models.helpers.pydantic import populate_pydantic_default_values
from ormar.models.utils import Extra

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model
    from ormar.fields import BaseField


def is_field_an_forward_ref(field: "BaseField") -> bool:
    """
    Checks if field is a relation field and whether any of the referenced models
    are ForwardRefs that needs to be updated before proceeding.

    :param field: model field to verify
    :type field: Type[BaseField]
    :return: result of the check
    :rtype: bool
    """
    return field.is_relation and (
        field.to.__class__ == ForwardRef or field.through.__class__ == ForwardRef
    )


def populate_default_options_values(  # noqa: CCR001
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
    :param model_fields: dict of model fields
    :type model_fields: Union[Dict[str, type], Dict]
    """
    if not hasattr(new_model.Meta, "constraints"):
        new_model.Meta.constraints = []
    if not hasattr(new_model.Meta, "model_fields"):
        new_model.Meta.model_fields = model_fields
    if not hasattr(new_model.Meta, "abstract"):
        new_model.Meta.abstract = False
    if not hasattr(new_model.Meta, "extra"):
        new_model.Meta.extra = Extra.forbid
    if not hasattr(new_model.Meta, "orders_by"):
        new_model.Meta.orders_by = []
    if not hasattr(new_model.Meta, "exclude_parent_fields"):
        new_model.Meta.exclude_parent_fields = []

    if any(
        is_field_an_forward_ref(field) for field in new_model.Meta.model_fields.values()
    ):
        new_model.Meta.requires_ref_update = True
    else:
        new_model.Meta.requires_ref_update = False

    new_model._json_fields = {
        name
        for name, field in new_model.Meta.model_fields.items()
        if field.__type__ == pydantic.Json
    }
    new_model._bytes_fields = {
        name
        for name, field in new_model.Meta.model_fields.items()
        if field.__type__ == bytes
    }

    new_model.__relation_map__ = None


class Connection(sqlite3.Connection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        super().__init__(*args, **kwargs)
        self.execute("PRAGMA foreign_keys=1;")


def substitue_backend_pool_for_sqlite(new_model: Type["Model"]) -> None:
    """
    Recreates Connection pool for sqlite3 with new factory that
    executes "PRAGMA foreign_keys=1; on initialization to enable foreign keys.

    :param new_model: newly declared ormar Model
    :type new_model: Model class
    """
    backend = new_model.Meta.database._backend
    if (
        backend._dialect.name == "sqlite" and "factory" not in backend._options
    ):  # pragma: no cover
        backend._options["factory"] = Connection
        old_pool = backend._pool
        backend._pool = old_pool.__class__(backend._database_url, **backend._options)


def check_required_meta_parameters(new_model: Type["Model"]) -> None:
    """
    Verifies if ormar.Model has database and metadata set.

    Recreates Connection pool for sqlite3

    :param new_model: newly declared ormar Model
    :type new_model: Model class
    """
    if not hasattr(new_model.Meta, "database"):
        if not getattr(new_model.Meta, "abstract", False):
            raise ormar.ModelDefinitionError(
                f"{new_model.__name__} does not have database defined."
            )

    else:
        substitue_backend_pool_for_sqlite(new_model=new_model)

    if not hasattr(new_model.Meta, "metadata"):
        if not getattr(new_model.Meta, "abstract", False):
            raise ormar.ModelDefinitionError(
                f"{new_model.__name__} does not have metadata defined."
            )


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


def group_related_list(list_: List) -> collections.OrderedDict:
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
    return collections.OrderedDict(
        sorted(result_dict.items(), key=lambda item: len(item[1]))
    )


def meta_field_not_set(model: Type["Model"], field_name: str) -> bool:
    """
    Checks if field with given name is already present in model.Meta.
    Then check if it's set to something truthful
    (in practice meaning not None, as it's non or ormar Field only).

    :param model: newly constructed model
    :type model: Model class
    :param field_name: name of the ormar field
    :type field_name: str
    :return: result of the check
    :rtype: bool
    """
    return not hasattr(model.Meta, field_name) or not getattr(model.Meta, field_name)
