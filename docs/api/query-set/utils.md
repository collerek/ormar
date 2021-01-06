<a name="queryset.utils"></a>
# queryset.utils

<a name="queryset.utils.check_node_not_dict_or_not_last_node"></a>
#### check\_node\_not\_dict\_or\_not\_last\_node

```python
check_node_not_dict_or_not_last_node(part: str, parts: List, current_level: Any) -> bool
```

Checks if given name is not present in the current level of the structure.
Checks if given name is not the last name in the split list of parts.
Checks if the given name in current level is not a dictionary.

All those checks verify if there is a need for deeper traversal.

**Arguments**:

- `part (str)`: 
- `parts (List[str])`: 
- `current_level (Any)`: current level of the traversed structure

**Returns**:

`(bool)`: result of the check

<a name="queryset.utils.translate_list_to_dict"></a>
#### translate\_list\_to\_dict

```python
translate_list_to_dict(list_to_trans: Union[List, Set], is_order: bool = False) -> Dict
```

Splits the list of strings by '__' and converts them to dictionary with nested
models grouped by parent model. That way each model appears only once in the whole
dictionary and children are grouped under parent name.

Default required key ise Ellipsis like in pydantic.

**Arguments**:

- `list_to_trans (set)`: input list
- `is_order (bool)`: flag if change affects order_by clauses are they require special
default value with sort order.

**Returns**:

`(Dict)`: converted to dictionary input list

<a name="queryset.utils.convert_set_to_required_dict"></a>
#### convert\_set\_to\_required\_dict

```python
convert_set_to_required_dict(set_to_convert: set) -> Dict
```

Converts set to dictionary of required keys.
Required key is Ellipsis.

**Arguments**:

- `set_to_convert (set)`: set to convert to dict

**Returns**:

`(Dict)`: set converted to dict of ellipsis

<a name="queryset.utils.update"></a>
#### update

```python
update(current_dict: Any, updating_dict: Any) -> Dict
```

Update one dict with another but with regard for nested keys.

That way nested sets are unionised, dicts updated and
only other values are overwritten.

**Arguments**:

- `current_dict (Dict[str, ellipsis])`: dict to update
- `updating_dict (Dict)`: dict with values to update

**Returns**:

`(Dict)`: combination of both dicts

<a name="queryset.utils.update_dict_from_list"></a>
#### update\_dict\_from\_list

```python
update_dict_from_list(curr_dict: Dict, list_to_update: Union[List, Set]) -> Dict
```

Converts the list into dictionary and later performs special update, where
nested keys that are sets or dicts are combined and not overwritten.

**Arguments**:

- `curr_dict (Dict)`: dict to update
- `list_to_update (List[str])`: list with values to update the dict

**Returns**:

`(Dict)`: updated dict

<a name="queryset.utils.extract_nested_models"></a>
#### extract\_nested\_models

```python
extract_nested_models(model: "Model", model_type: Type["Model"], select_dict: Dict, extracted: Dict) -> None
```

Iterates over model relations and extracts all nested models from select_dict and
puts them in corresponding list under relation name in extracted dict.keys

Basically flattens all relation to dictionary of all related models, that can be
used on several models and extract all of their children into dictionary of lists
witch children models.

Goes also into nested relations if needed (specified in select_dict).

**Arguments**:

- `model (Model)`: parent Model
- `model_type (Type[Model])`: parent model class
- `select_dict (Dict)`: dictionary of related models from select_related
- `extracted (Dict)`: dictionary with already extracted models

<a name="queryset.utils.extract_models_to_dict_of_lists"></a>
#### extract\_models\_to\_dict\_of\_lists

```python
extract_models_to_dict_of_lists(model_type: Type["Model"], models: Sequence["Model"], select_dict: Dict, extracted: Dict = None) -> Dict
```

Receives a list of models and extracts all of the children and their children
into dictionary of lists with children models, flattening the structure to one dict
with all children models under their relation keys.

**Arguments**:

- `model_type (Type[Model])`: parent model class
- `models (List[Model])`: list of models from which related models should be extracted.
- `select_dict (Dict)`: dictionary of related models from select_related
- `extracted (Dict)`: dictionary with already extracted models

**Returns**:

`(Dict)`: dictionary of lists f related models

