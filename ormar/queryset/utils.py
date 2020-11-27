import collections.abc
import copy
from typing import (
    Any,
    Dict,
    List,
    Sequence,
    Set,
    TYPE_CHECKING,
    Type,
    Union,
)

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model


def check_node_not_dict_or_not_last_node(
    part: str, parts: List, current_level: Any
) -> bool:
    return (part not in current_level and part != parts[-1]) or (
        part in current_level and not isinstance(current_level[part], dict)
    )


def translate_list_to_dict(  # noqa: CCR001
    list_to_trans: Union[List, Set], is_order: bool = False
) -> Dict:
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

        for part in parts:
            if check_node_not_dict_or_not_last_node(
                part=part, parts=parts, current_level=current_level
            ):
                current_level[part] = dict()
            elif part not in current_level:
                current_level[part] = def_val
            current_level = current_level[part]
    return new_dict


def convert_set_to_required_dict(set_to_convert: set) -> Dict:
    new_dict = dict()
    for key in set_to_convert:
        new_dict[key] = Ellipsis
    return new_dict


def update(current_dict: Any, updating_dict: Any) -> Dict:  # noqa: CCR001
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


def update_dict_from_list(curr_dict: Dict, list_to_update: Union[List, Set]) -> Dict:
    updated_dict = copy.copy(curr_dict)
    dict_to_update = translate_list_to_dict(list_to_update)
    update(updated_dict, dict_to_update)
    return updated_dict


def extract_nested_models(  # noqa: CCR001
    model: "Model", model_type: Type["Model"], select_dict: Dict, extracted: Dict
) -> None:
    follow = [rel for rel in model_type.extract_related_names() if rel in select_dict]
    for related in follow:
        child = getattr(model, related)
        if child:
            target_model = model_type.Meta.model_fields[related].to
            if isinstance(child, list):
                extracted.setdefault(target_model.get_name(), []).extend(child)
                if select_dict[related] is not Ellipsis:
                    for sub_child in child:
                        extract_nested_models(
                            sub_child, target_model, select_dict[related], extracted,
                        )
            else:
                extracted.setdefault(target_model.get_name(), []).append(child)
                if select_dict[related] is not Ellipsis:
                    extract_nested_models(
                        child, target_model, select_dict[related], extracted,
                    )


def extract_models_to_dict_of_lists(
    model_type: Type["Model"],
    models: Sequence["Model"],
    select_dict: Dict,
    extracted: Dict = None,
) -> Dict:
    if not extracted:
        extracted = dict()
    for model in models:
        extract_nested_models(model, model_type, select_dict, extracted)
    return extracted
