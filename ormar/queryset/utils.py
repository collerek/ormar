import collections.abc
import copy
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    TYPE_CHECKING,
    Tuple,
    Type,
    Union,
)

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model, BaseField


def check_node_not_dict_or_not_last_node(
    part: str, is_last: bool, current_level: Any
) -> bool:
    """
    Checks if given name is not present in the current level of the structure.
    Checks if given name is not the last name in the split list of parts.
    Checks if the given name in current level is not a dictionary.

    All those checks verify if there is a need for deeper traversal.

    :param part:
    :type part: str
    :param is_last: flag to check if last element
    :type is_last: bool
    :param current_level: current level of the traversed structure
    :type current_level: Any
    :return: result of the check
    :rtype: bool
    """
    return (part not in current_level and not is_last) or (
        part in current_level and not isinstance(current_level[part], dict)
    )


def translate_list_to_dict(  # noqa: CCR001
    list_to_trans: Union[List, Set], is_order: bool = False
) -> Dict:
    """
    Splits the list of strings by '__' and converts them to dictionary with nested
    models grouped by parent model. That way each model appears only once in the whole
    dictionary and children are grouped under parent name.

    Default required key ise Ellipsis like in pydantic.

    :param list_to_trans: input list
    :type list_to_trans: Union[List, Set]
    :param is_order: flag if change affects order_by clauses are they require special
    default value with sort order.
    :type is_order: bool
    :return: converted to dictionary input list
    :rtype: Dict
    """
    new_dict: Dict = dict()
    for path in list_to_trans:
        current_level = new_dict
        parts = path.split("__")
        def_val: Any = ...
        if is_order:
            if parts[0][0] == "-":
                def_val = "desc"
                parts[0] = parts[0][1:]
            else:
                def_val = "asc"

        for ind, part in enumerate(parts):
            is_last = ind == len(parts) - 1
            if check_node_not_dict_or_not_last_node(
                part=part, is_last=is_last, current_level=current_level
            ):
                current_level[part] = dict()
            elif part not in current_level:
                current_level[part] = def_val
            current_level = current_level[part]
    return new_dict


def convert_set_to_required_dict(set_to_convert: set) -> Dict:
    """
    Converts set to dictionary of required keys.
    Required key is Ellipsis.

    :param set_to_convert: set to convert to dict
    :type set_to_convert: set
    :return: set converted to dict of ellipsis
    :rtype: Dict
    """
    new_dict = dict()
    for key in set_to_convert:
        new_dict[key] = Ellipsis
    return new_dict


def update(current_dict: Any, updating_dict: Any) -> Dict:  # noqa: CCR001
    """
    Update one dict with another but with regard for nested keys.

    That way nested sets are unionised, dicts updated and
    only other values are overwritten.

    :param current_dict: dict to update
    :type current_dict: Dict[str, ellipsis]
    :param updating_dict: dict with values to update
    :type updating_dict: Dict
    :return: combination of both dicts
    :rtype: Dict
    """
    if current_dict is Ellipsis:
        current_dict = dict()
    for key, value in updating_dict.items():
        if isinstance(value, collections.abc.Mapping):
            old_key = current_dict.get(key, {})
            if isinstance(old_key, set):
                old_key = convert_set_to_required_dict(old_key)
            current_dict[key] = update(old_key, value)
        elif isinstance(value, set) and isinstance(current_dict.get(key), set):
            current_dict[key] = current_dict.get(key).union(value)
        else:
            current_dict[key] = value
    return current_dict


def subtract_dict(current_dict: Any, updating_dict: Any) -> Dict:  # noqa: CCR001
    """
    Update one dict with another but with regard for nested keys.

    That way nested sets are unionised, dicts updated and
    only other values are overwritten.

    :param current_dict: dict to update
    :type current_dict: Dict[str, ellipsis]
    :param updating_dict: dict with values to update
    :type updating_dict: Dict
    :return: combination of both dicts
    :rtype: Dict
    """
    for key, value in updating_dict.items():
        old_key = current_dict.get(key, {})
        new_value: Optional[Union[Dict, Set]] = None
        if not old_key:
            continue
        if isinstance(value, set) and isinstance(old_key, set):
            new_value = old_key.difference(value)
        elif isinstance(value, (set, collections.abc.Mapping)) and isinstance(
            old_key, (set, collections.abc.Mapping)
        ):
            value = (
                convert_set_to_required_dict(value)
                if not isinstance(value, collections.abc.Mapping)
                else value
            )
            old_key = (
                convert_set_to_required_dict(old_key)
                if not isinstance(old_key, collections.abc.Mapping)
                else old_key
            )
            new_value = subtract_dict(old_key, value)

        if new_value:
            current_dict[key] = new_value
        else:
            current_dict.pop(key, None)
    return current_dict


def update_dict_from_list(curr_dict: Dict, list_to_update: Union[List, Set]) -> Dict:
    """
    Converts the list into dictionary and later performs special update, where
    nested keys that are sets or dicts are combined and not overwritten.

    :param curr_dict: dict to update
    :type curr_dict: Dict
    :param list_to_update: list with values to update the dict
    :type list_to_update: List[str]
    :return: updated dict
    :rtype: Dict
    """
    updated_dict = copy.copy(curr_dict)
    dict_to_update = translate_list_to_dict(list_to_update)
    update(updated_dict, dict_to_update)
    return updated_dict


def extract_nested_models(  # noqa: CCR001
    model: "Model", model_type: Type["Model"], select_dict: Dict, extracted: Dict
) -> None:
    """
    Iterates over model relations and extracts all nested models from select_dict and
    puts them in corresponding list under relation name in extracted dict.keys

    Basically flattens all relation to dictionary of all related models, that can be
    used on several models and extract all of their children into dictionary of lists
    witch children models.

    Goes also into nested relations if needed (specified in select_dict).

    :param model: parent Model
    :type model: Model
    :param model_type: parent model class
    :type model_type: Type[Model]
    :param select_dict: dictionary of related models from select_related
    :type select_dict: Dict
    :param extracted: dictionary with already extracted models
    :type extracted: Dict
    """
    follow = [rel for rel in model_type.extract_related_names() if rel in select_dict]
    for related in follow:
        child = getattr(model, related)
        if not child:
            continue
        target_model = model_type.Meta.model_fields[related].to
        if isinstance(child, list):
            extracted.setdefault(target_model.get_name(), []).extend(child)
            if select_dict[related] is not Ellipsis:
                for sub_child in child:
                    extract_nested_models(
                        sub_child, target_model, select_dict[related], extracted
                    )
        else:
            extracted.setdefault(target_model.get_name(), []).append(child)
            if select_dict[related] is not Ellipsis:
                extract_nested_models(
                    child, target_model, select_dict[related], extracted
                )


def extract_models_to_dict_of_lists(
    model_type: Type["Model"],
    models: Sequence["Model"],
    select_dict: Dict,
    extracted: Dict = None,
) -> Dict:
    """
    Receives a list of models and extracts all of the children and their children
    into dictionary of lists with children models, flattening the structure to one dict
    with all children models under their relation keys.

    :param model_type: parent model class
    :type model_type: Type[Model]
    :param models: list of models from which related models should be extracted.
    :type models: List[Model]
    :param select_dict: dictionary of related models from select_related
    :type select_dict: Dict
    :param extracted: dictionary with already extracted models
    :type extracted: Dict
    :return: dictionary of lists f related models
    :rtype: Dict
    """
    if not extracted:
        extracted = dict()
    for model in models:
        extract_nested_models(model, model_type, select_dict, extracted)
    return extracted


def get_relationship_alias_model_and_str(
    source_model: Type["Model"], related_parts: List
) -> Tuple[str, Type["Model"], str, bool]:
    """
    Walks the relation to retrieve the actual model on which the clause should be
    constructed, extracts alias based on last relation leading to target model.
    :param related_parts: list of related names extracted from string
    :type related_parts: Union[List, List[str]]
    :param source_model: model from which relation starts
    :type source_model: Type[Model]
    :return: table prefix, target model and relation string
    :rtype: Tuple[str, Type["Model"], str]
    """
    table_prefix = ""
    is_through = False
    target_model = source_model
    previous_model = target_model
    previous_models = [target_model]
    manager = target_model.Meta.alias_manager
    for relation in related_parts[:]:
        related_field = target_model.Meta.model_fields[relation]

        if related_field.is_through:
            (previous_model, relation, is_through) = _process_through_field(
                related_parts=related_parts,
                relation=relation,
                related_field=related_field,
                previous_model=previous_model,
                previous_models=previous_models,
            )
        if related_field.is_multi:
            previous_model = related_field.through
            relation = related_field.default_target_field_name()  # type: ignore
        table_prefix = manager.resolve_relation_alias(
            from_model=previous_model, relation_name=relation
        )
        target_model = related_field.to
        previous_model = target_model
        if not is_through:
            previous_models.append(previous_model)
    relation_str = "__".join(related_parts)

    return table_prefix, target_model, relation_str, is_through


def _process_through_field(
    related_parts: List,
    relation: Optional[str],
    related_field: "BaseField",
    previous_model: Type["Model"],
    previous_models: List[Type["Model"]],
) -> Tuple[Type["Model"], Optional[str], bool]:
    """
    Helper processing through models as they need to be treated differently.

    :param related_parts: split relation string
    :type related_parts: List[str]
    :param relation: relation name
    :type relation: str
    :param related_field: field with relation declaration
    :type related_field: "ForeignKeyField"
    :param previous_model: model from which relation is coming
    :type previous_model: Type["Model"]
    :param previous_models: list of already visited models in relation chain
    :type previous_models: List[Type["Model"]]
    :return: previous_model, relation, is_through
    :rtype: Tuple[Type["Model"], str, bool]
    """
    is_through = True
    related_parts.remove(relation)
    through_field = related_field.owner.Meta.model_fields[
        related_field.related_name or ""
    ]
    if len(previous_models) > 1 and previous_models[-2] == through_field.to:
        previous_model = through_field.to
        relation = through_field.related_name
    else:
        relation = related_field.related_name
    return previous_model, relation, is_through
