<a name="models.mixins.excludable_mixin"></a>
# models.mixins.excludable\_mixin

<a name="models.mixins.excludable_mixin.ExcludableMixin"></a>
## ExcludableMixin Objects

```python
class ExcludableMixin(RelationMixin)
```

Used to include/exclude given set of fields on models during load and dict() calls.

<a name="models.mixins.excludable_mixin.ExcludableMixin.get_child"></a>
#### get\_child

```python
 | @staticmethod
 | get_child(items: Union[Set, Dict, None], key: str = None) -> Union[Set, Dict, None]
```

Used to get nested dictionaries keys if they exists otherwise returns
passed items.

**Arguments**:

- `items (Union[Set, Dict, None])`: bag of items to include or exclude
- `key (str)`: name of the child to extract

**Returns**:

`(Union[Set, Dict, None])`: child extracted from items if exists

<a name="models.mixins.excludable_mixin.ExcludableMixin.get_excluded"></a>
#### get\_excluded

```python
 | @staticmethod
 | get_excluded(exclude: Union[Set, Dict, None], key: str = None) -> Union[Set, Dict, None]
```

Proxy to ExcludableMixin.get_child for exclusions.

**Arguments**:

- `exclude (Union[Set, Dict, None])`: bag of items to exclude
- `key (str)`: name of the child to extract

**Returns**:

`(Union[Set, Dict, None])`: child extracted from items if exists

<a name="models.mixins.excludable_mixin.ExcludableMixin.get_included"></a>
#### get\_included

```python
 | @staticmethod
 | get_included(include: Union[Set, Dict, None], key: str = None) -> Union[Set, Dict, None]
```

Proxy to ExcludableMixin.get_child for inclusions.

**Arguments**:

- `include (Union[Set, Dict, None])`: bag of items to include
- `key (str)`: name of the child to extract

**Returns**:

`(Union[Set, Dict, None])`: child extracted from items if exists

<a name="models.mixins.excludable_mixin.ExcludableMixin.is_excluded"></a>
#### is\_excluded

```python
 | @staticmethod
 | is_excluded(exclude: Union[Set, Dict, None], key: str = None) -> bool
```

Checks if given key should be excluded on model/ dict.

**Arguments**:

- `exclude (Union[Set, Dict, None])`: bag of items to exclude
- `key (str)`: name of the child to extract

**Returns**:

`(Union[Set, Dict, None])`: child extracted from items if exists

<a name="models.mixins.excludable_mixin.ExcludableMixin.is_included"></a>
#### is\_included

```python
 | @staticmethod
 | is_included(include: Union[Set, Dict, None], key: str = None) -> bool
```

Checks if given key should be included on model/ dict.

**Arguments**:

- `include (Union[Set, Dict, None])`: bag of items to include
- `key (str)`: name of the child to extract

**Returns**:

`(Union[Set, Dict, None])`: child extracted from items if exists

<a name="models.mixins.excludable_mixin.ExcludableMixin._populate_pk_column"></a>
#### \_populate\_pk\_column

```python
 | @staticmethod
 | _populate_pk_column(model: Type["Model"], columns: List[str], use_alias: bool = False) -> List[str]
```

Adds primary key column/alias (depends on use_alias flag) to list of
column names that are selected.

**Arguments**:

- `model (Type["Model"])`: model on columns are selected
- `columns (List[str])`: list of columns names
- `use_alias (bool)`: flag to set if aliases or field names should be used

**Returns**:

`(List[str])`: list of columns names with pk column in it

<a name="models.mixins.excludable_mixin.ExcludableMixin.own_table_columns"></a>
#### own\_table\_columns

```python
 | @classmethod
 | own_table_columns(cls, model: Type["Model"], fields: Optional[Union[Set, Dict]], exclude_fields: Optional[Union[Set, Dict]], use_alias: bool = False) -> List[str]
```

Returns list of aliases or field names for given model.
Aliases/names switch is use_alias flag.

If provided only fields included in fields will be returned.
If provided fields in exclude_fields will be excluded in return.

Primary key field is always added and cannot be excluded (will be added anyway).

**Arguments**:

- `model (Type["Model"])`: model on columns are selected
- `fields (Optional[Union[Set, Dict]])`: set/dict of fields to include
- `exclude_fields (Optional[Union[Set, Dict]])`: set/dict of fields to exclude
- `use_alias (bool)`: flag if aliases or field names should be used

**Returns**:

`(List[str])`: list of column field names or aliases

<a name="models.mixins.excludable_mixin.ExcludableMixin._update_excluded_with_related_not_required"></a>
#### \_update\_excluded\_with\_related\_not\_required

```python
 | @classmethod
 | _update_excluded_with_related_not_required(cls, exclude: Union["AbstractSetIntStr", "MappingIntStrAny", None], nested: bool = False) -> Union[Set, Dict]
```

Used during generation of the dict().
To avoid cyclical references and max recurrence limit nested models have to
exclude related models that are not mandatory.

For a main model (not nested) only nullable related field names are added to
exclusion, for nested models all related models are excluded.

**Arguments**:

- `exclude (Union[Set, Dict, None])`: set/dict with fields to exclude
- `nested (bool)`: flag setting nested models (child of previous one, not main one)

**Returns**:

`(Union[Set, Dict])`: set or dict with excluded fields added.

<a name="models.mixins.excludable_mixin.ExcludableMixin.get_names_to_exclude"></a>
#### get\_names\_to\_exclude

```python
 | @classmethod
 | get_names_to_exclude(cls, fields: Optional[Union[Dict, Set]] = None, exclude_fields: Optional[Union[Dict, Set]] = None) -> Set
```

Returns a set of models field names that should be explicitly excluded
during model initialization.

Those fields will be set to None to avoid ormar/pydantic setting default
values on them. They should be returned as None in any case.

Used in parsing data from database rows that construct Models by initializing
them with dicts constructed from those db rows.

**Arguments**:

- `fields (Optional[Union[Set, Dict]])`: set/dict of fields to include
- `exclude_fields (Optional[Union[Set, Dict]])`: set/dict of fields to exclude

**Returns**:

`(Set)`: set of field names that should be excluded

