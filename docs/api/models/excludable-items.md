<a name="models.excludable"></a>
# models.excludable

<a name="models.excludable.Excludable"></a>
## Excludable Objects

```python
@dataclass
class Excludable()
```

Class that keeps sets of fields to exclude and include

<a name="models.excludable.Excludable.get_copy"></a>
#### get\_copy

```python
 | get_copy() -> "Excludable"
```

Return copy of self to avoid in place modifications

**Returns**:

`(ormar.models.excludable.Excludable)`: copy of self with copied sets

<a name="models.excludable.Excludable.set_values"></a>
#### set\_values

```python
 | set_values(value: Set, is_exclude: bool) -> None
```

Appends the data to include/exclude sets.

**Arguments**:

- `value (set)`: set of values to add
- `is_exclude (bool)`: flag if values are to be excluded or included

<a name="models.excludable.Excludable.is_included"></a>
#### is\_included

```python
 | is_included(key: str) -> bool
```

Check if field in included (in set or set is {...})

**Arguments**:

- `key (str)`: key to check

**Returns**:

`(bool)`: result of the check

<a name="models.excludable.Excludable.is_excluded"></a>
#### is\_excluded

```python
 | is_excluded(key: str) -> bool
```

Check if field in excluded (in set or set is {...})

**Arguments**:

- `key (str)`: key to check

**Returns**:

`(bool)`: result of the check

<a name="models.excludable.ExcludableItems"></a>
## ExcludableItems Objects

```python
class ExcludableItems()
```

Keeps a dictionary of Excludables by alias + model_name keys
to allow quick lookup by nested models without need to travers
deeply nested dictionaries and passing include/exclude around

<a name="models.excludable.ExcludableItems.from_excludable"></a>
#### from\_excludable

```python
 | @classmethod
 | from_excludable(cls, other: "ExcludableItems") -> "ExcludableItems"
```

Copy passed ExcludableItems to avoid inplace modifications.

**Arguments**:

- `other (ormar.models.excludable.ExcludableItems)`: other excludable items to be copied

**Returns**:

`(ormar.models.excludable.ExcludableItems)`: copy of other

<a name="models.excludable.ExcludableItems.get"></a>
#### get

```python
 | get(model_cls: Type["Model"], alias: str = "") -> Excludable
```

Return Excludable for given model and alias.

**Arguments**:

- `model_cls (ormar.models.metaclass.ModelMetaclass)`: target model to check
- `alias (str)`: table alias from relation manager

**Returns**:

`(ormar.models.excludable.Excludable)`: Excludable for given model and alias

<a name="models.excludable.ExcludableItems.build"></a>
#### build

```python
 | build(items: Union[List[str], str, Tuple[str], Set[str], Dict], model_cls: Type["Model"], is_exclude: bool = False) -> None
```

Receives the one of the types of items and parses them as to achieve
a end situation with one excludable per alias/model in relation.

Each excludable has two sets of values - one to include, one to exclude.

**Arguments**:

- `items (Union[List[str], str, Tuple[str], Set[str], Dict])`: values to be included or excluded
- `model_cls (ormar.models.metaclass.ModelMetaclass)`: source model from which relations are constructed
- `is_exclude (bool)`: flag if items should be included or excluded

<a name="models.excludable.ExcludableItems._set_excludes"></a>
#### \_set\_excludes

```python
 | _set_excludes(items: Set, model_name: str, is_exclude: bool, alias: str = "") -> None
```

Sets set of values to be included or excluded for given key and model.

**Arguments**:

- `items (set)`: items to include/exclude
- `model_name (str)`: name of model to construct key
- `is_exclude (bool)`: flag if values should be included or excluded
- `alias (str)`: 

<a name="models.excludable.ExcludableItems._traverse_dict"></a>
#### \_traverse\_dict

```python
 | _traverse_dict(values: Dict, source_model: Type["Model"], model_cls: Type["Model"], is_exclude: bool, related_items: List = None, alias: str = "") -> None
```

Goes through dict of nested values and construct/update Excludables.

**Arguments**:

- `values (Dict)`: items to include/exclude
- `source_model (ormar.models.metaclass.ModelMetaclass)`: source model from which relations are constructed
- `model_cls (ormar.models.metaclass.ModelMetaclass)`: model from which current relation is constructed
- `is_exclude (bool)`: flag if values should be included or excluded
- `related_items (List)`: list of names of related fields chain
- `alias (str)`: alias of relation

<a name="models.excludable.ExcludableItems._traverse_list"></a>
#### \_traverse\_list

```python
 | _traverse_list(values: Set[str], model_cls: Type["Model"], is_exclude: bool) -> None
```

Goes through list of values and construct/update Excludables.

**Arguments**:

- `values (set)`: items to include/exclude
- `model_cls (ormar.models.metaclass.ModelMetaclass)`: model from which current relation is constructed
- `is_exclude (bool)`: flag if values should be included or excluded

