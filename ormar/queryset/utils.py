import collections.abc
import copy
from typing import Any, Dict, List, Set, Union


def check_node_not_dict_or_not_last_node(
    part: str, parts: List, current_level: Any
) -> bool:
    return (part not in current_level and part != parts[-1]) or (
        part in current_level and not isinstance(current_level[part], dict)
    )


def translate_list_to_dict(list_to_trans: Union[List, Set]) -> Dict:  # noqa: CCR001
    new_dict: Dict = dict()
    for path in list_to_trans:
        current_level = new_dict
        parts = path.split("__")
        for part in parts:
            if check_node_not_dict_or_not_last_node(
                part=part, parts=parts, current_level=current_level
            ):
                current_level[part] = dict()
            elif part not in current_level:
                current_level[part] = ...
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
