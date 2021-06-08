<a name="models.newbasemodel"></a>
# models.newbasemodel

<a name="models.newbasemodel.NewBaseModel"></a>
## NewBaseModel Objects

```python
class NewBaseModel(pydantic.BaseModel,  ModelTableProxy, metaclass=ModelMetaclass)
```

Main base class of ormar Model.
Inherits from pydantic BaseModel and has all mixins combined in ModelTableProxy.
Constructed with ModelMetaclass which in turn also inherits pydantic metaclass.

Abstracts away all internals and helper functions, so final Model class has only
the logic concerned with database connection and data persistance.

<a name="models.newbasemodel.NewBaseModel.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(*args: Any, **kwargs: Any) -> None
```

Initializer that creates a new ormar Model that is also pydantic Model at the
same time.

Passed keyword arguments can be only field names and their corresponding values
as those will be passed to pydantic validation that will complain if extra
params are passed.

If relations are defined each relation is expanded and children models are also
initialized and validated. Relation from both sides is registered so you can
access related models from both sides.

Json fields are automatically loaded/dumped if needed.

Models marked as abstract=True in internal Meta class cannot be initialized.

Accepts also special __pk_only__ flag that indicates that Model is constructed
only with primary key value (so no other fields, it's a child model on other
Model), that causes skipping the validation, that's the only case when the
validation can be skipped.

Accepts also special __excluded__ parameter that contains a set of fields that
should be explicitly set to None, as otherwise pydantic will try to populate
them with their default values if default is set.

**Raises**:

- `ModelError`: if abstract model is initialized, model has ForwardRefs
that has not been updated or unknown field is passed

**Arguments**:

- `args` (`Any`): ignored args
- `kwargs` (`Any`): keyword arguments - all fields values and some special params

<a name="models.newbasemodel.NewBaseModel.__setattr__"></a>
#### \_\_setattr\_\_

```python
 | __setattr__(name: str, value: Any) -> None
```

Overwrites setattr in pydantic parent as otherwise descriptors are not called.

**Arguments**:

- `name` (`str`): name of the attribute to set
- `value` (`Any`): value of the attribute to set

**Returns**:

`None`: None

<a name="models.newbasemodel.NewBaseModel.__getattr__"></a>
#### \_\_getattr\_\_

```python
 | __getattr__(item: str) -> Any
```

Used only to silence mypy errors for Through models and reverse relations.
Not used in real life as in practice calls are intercepted
by RelationDescriptors

**Arguments**:

- `item` (`str`): name of attribute

**Returns**:

`Any`: Any

<a name="models.newbasemodel.NewBaseModel._internal_set"></a>
#### \_internal\_set

```python
 | _internal_set(name: str, value: Any) -> None
```

Delegates call to pydantic.

**Arguments**:

- `name` (`str`): name of param
- `value` (`Any`): value to set

<a name="models.newbasemodel.NewBaseModel._verify_model_can_be_initialized"></a>
#### \_verify\_model\_can\_be\_initialized

```python
 | _verify_model_can_be_initialized() -> None
```

Raises exception if model is abstract or has ForwardRefs in relation fields.

**Returns**:

`None`: None

<a name="models.newbasemodel.NewBaseModel._process_kwargs"></a>
#### \_process\_kwargs

```python
 | _process_kwargs(kwargs: Dict) -> Tuple[Dict, Dict]
```

Initializes nested models.

Removes property_fields

Checks if field is in the model fields or pydatnic fields.

Nullifies fields that should be excluded.

Extracts through models from kwargs into temporary dict.

**Arguments**:

- `kwargs` (`Dict`): passed to init keyword arguments

**Returns**:

`Tuple[Dict, Dict]`: modified kwargs

<a name="models.newbasemodel.NewBaseModel._initialize_internal_attributes"></a>
#### \_initialize\_internal\_attributes

```python
 | _initialize_internal_attributes() -> None
```

Initializes internal attributes during __init__()

**Returns**:

`None`: 

<a name="models.newbasemodel.NewBaseModel.__eq__"></a>
#### \_\_eq\_\_

```python
 | __eq__(other: object) -> bool
```

Compares other model to this model. when == is called.

**Arguments**:

- `other` (`object`): other model to compare

**Returns**:

`bool`: result of comparison

<a name="models.newbasemodel.NewBaseModel.__same__"></a>
#### \_\_same\_\_

```python
 | __same__(other: "NewBaseModel") -> bool
```

Used by __eq__, compares other model to this model.
Compares:
* _orm_ids,
* primary key values if it's set
* dictionary of own fields (excluding relations)

**Arguments**:

- `other` (`NewBaseModel`): model to compare to

**Returns**:

`bool`: result of comparison

<a name="models.newbasemodel.NewBaseModel.get_name"></a>
#### get\_name

```python
 | @classmethod
 | get_name(cls, lower: bool = True) -> str
```

Returns name of the Model class, by default lowercase.

**Arguments**:

- `lower` (`bool`): flag if name should be set to lowercase

**Returns**:

`str`: name of the model

<a name="models.newbasemodel.NewBaseModel.pk_column"></a>
#### pk\_column

```python
 | @property
 | pk_column() -> sqlalchemy.Column
```

Retrieves primary key sqlalchemy column from models Meta.table.
Each model has to have primary key.
Only one primary key column is allowed.

**Returns**:

`sqlalchemy.Column`: primary key sqlalchemy column

<a name="models.newbasemodel.NewBaseModel.saved"></a>
#### saved

```python
 | @property
 | saved() -> bool
```

Saved status of the model. Changed by setattr and loading from db

<a name="models.newbasemodel.NewBaseModel.signals"></a>
#### signals

```python
 | @property
 | signals() -> "SignalEmitter"
```

Exposes signals from model Meta

<a name="models.newbasemodel.NewBaseModel.pk_type"></a>
#### pk\_type

```python
 | @classmethod
 | pk_type(cls) -> Any
```

Shortcut to models primary key field type

<a name="models.newbasemodel.NewBaseModel.db_backend_name"></a>
#### db\_backend\_name

```python
 | @classmethod
 | db_backend_name(cls) -> str
```

Shortcut to database dialect,
cause some dialect require different treatment

<a name="models.newbasemodel.NewBaseModel.remove"></a>
#### remove

```python
 | remove(parent: "Model", name: str) -> None
```

Removes child from relation with given name in RelationshipManager

<a name="models.newbasemodel.NewBaseModel.set_save_status"></a>
#### set\_save\_status

```python
 | set_save_status(status: bool) -> None
```

Sets value of the save status

<a name="models.newbasemodel.NewBaseModel.get_properties"></a>
#### get\_properties

```python
 | @classmethod
 | get_properties(cls, include: Union[Set, Dict, None], exclude: Union[Set, Dict, None]) -> Set[str]
```

Returns a set of names of functions/fields decorated with
@property_field decorator.

They are added to dictionary when called directly and therefore also are
present in fastapi responses.

**Arguments**:

- `include` (`Union[Set, Dict, None]`): fields to include
- `exclude` (`Union[Set, Dict, None]`): fields to exclude

**Returns**:

`Set[str]`: set of property fields names

<a name="models.newbasemodel.NewBaseModel.update_forward_refs"></a>
#### update\_forward\_refs

```python
 | @classmethod
 | update_forward_refs(cls, **localns: Any) -> None
```

Processes fields that are ForwardRef and need to be evaluated into actual
models.

Expands relationships, register relation in alias manager and substitutes
sqlalchemy columns with new ones with proper column type (null before).

Populates Meta table of the Model which is left empty before.

Sets self_reference flag on models that links to themselves.

Calls the pydantic method to evaluate pydantic fields.

**Arguments**:

- `localns` (`Any`): local namespace

**Returns**:

`None`: None

<a name="models.newbasemodel.NewBaseModel._get_not_excluded_fields"></a>
#### \_get\_not\_excluded\_fields

```python
 | @staticmethod
 | _get_not_excluded_fields(fields: Union[List, Set], include: Optional[Dict], exclude: Optional[Dict]) -> List
```

Returns related field names applying on them include and exclude set.

**Arguments**:

- `include` (`Union[Set, Dict, None]`): fields to include
- `exclude` (`Union[Set, Dict, None]`): fields to exclude

**Returns**:

`List of fields with relations that is not excluded`: 

<a name="models.newbasemodel.NewBaseModel._extract_nested_models_from_list"></a>
#### \_extract\_nested\_models\_from\_list

```python
 | @staticmethod
 | _extract_nested_models_from_list(relation_map: Dict, models: MutableSequence, include: Union[Set, Dict, None], exclude: Union[Set, Dict, None], exclude_primary_keys: bool, exclude_through_models: bool) -> List
```

Converts list of models into list of dictionaries.

**Arguments**:

- `models` (`List`): List of models
- `include` (`Union[Set, Dict, None]`): fields to include
- `exclude` (`Union[Set, Dict, None]`): fields to exclude

**Returns**:

`List[Dict]`: list of models converted to dictionaries

<a name="models.newbasemodel.NewBaseModel._skip_ellipsis"></a>
#### \_skip\_ellipsis

```python
 | @classmethod
 | _skip_ellipsis(cls, items: Union[Set, Dict, None], key: str, default_return: Any = None) -> Union[Set, Dict, None]
```

Helper to traverse the include/exclude dictionaries.
In dict() Ellipsis should be skipped as it indicates all fields required
and not the actual set/dict with fields names.

**Arguments**:

- `items` (`Union[Set, Dict, None]`): current include/exclude value
- `key` (`str`): key for nested relations to check

**Returns**:

`Union[Set, Dict, None]`: nested value of the items

<a name="models.newbasemodel.NewBaseModel._convert_all"></a>
#### \_convert\_all

```python
 | @staticmethod
 | _convert_all(items: Union[Set, Dict, None]) -> Union[Set, Dict, None]
```

Helper to convert __all__ pydantic special index to ormar which does not
support index based exclusions.

**Arguments**:

- `items` (`Union[Set, Dict, None]`): current include/exclude value

<a name="models.newbasemodel.NewBaseModel._extract_nested_models"></a>
#### \_extract\_nested\_models

```python
 | _extract_nested_models(relation_map: Dict, dict_instance: Dict, include: Optional[Dict], exclude: Optional[Dict], exclude_primary_keys: bool, exclude_through_models: bool) -> Dict
```

Traverse nested models and converts them into dictionaries.
Calls itself recursively if needed.

**Arguments**:

- `nested` (`bool`): flag if current instance is nested
- `dict_instance` (`Dict`): current instance dict
- `include` (`Optional[Dict]`): fields to include
- `exclude` (`Optional[Dict]`): fields to exclude

**Returns**:

`Dict`: current model dict with child models converted to dictionaries

<a name="models.newbasemodel.NewBaseModel.dict"></a>
#### dict

```python
 | dict(*, include: Union[Set, Dict] = None, exclude: Union[Set, Dict] = None, by_alias: bool = False, skip_defaults: bool = None, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False, exclude_primary_keys: bool = False, exclude_through_models: bool = False, relation_map: Dict = None) -> "DictStrAny"
```

Generate a dictionary representation of the model,
optionally specifying which fields to include or exclude.

Nested models are also parsed to dictionaries.

Additionally fields decorated with @property_field are also added.

**Arguments**:

- `exclude_through_models` (`bool`): flag to exclude through models from dict
- `exclude_primary_keys` (`bool`): flag to exclude primary keys from dict
- `include` (`Union[Set, Dict, None]`): fields to include
- `exclude` (`Union[Set, Dict, None]`): fields to exclude
- `by_alias` (`bool`): flag to get values by alias - passed to pydantic
- `skip_defaults` (`bool`): flag to not set values - passed to pydantic
- `exclude_unset` (`bool`): flag to exclude not set values - passed to pydantic
- `exclude_defaults` (`bool`): flag to exclude default values - passed to pydantic
- `exclude_none` (`bool`): flag to exclude None values - passed to pydantic
- `relation_map` (`Dict`): map of the relations to follow to avoid circural deps

**Returns**:



<a name="models.newbasemodel.NewBaseModel.json"></a>
#### json

```python
 | json(*, include: Union[Set, Dict] = None, exclude: Union[Set, Dict] = None, by_alias: bool = False, skip_defaults: bool = None, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False, encoder: Optional[Callable[[Any], Any]] = None, exclude_primary_keys: bool = False, exclude_through_models: bool = False, **dumps_kwargs: Any, ,) -> str
```

Generate a JSON representation of the model, `include` and `exclude`
arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(),
other arguments as per `json.dumps()`.

<a name="models.newbasemodel.NewBaseModel.update_from_dict"></a>
#### update\_from\_dict

```python
 | update_from_dict(value_dict: Dict) -> "NewBaseModel"
```

Updates self with values of fields passed in the dictionary.

**Arguments**:

- `value_dict` (`Dict`): dictionary of fields names and values

**Returns**:

`NewBaseModel`: self

<a name="models.newbasemodel.NewBaseModel._convert_to_bytes"></a>
#### \_convert\_to\_bytes

```python
 | _convert_to_bytes(column_name: str, value: Any) -> Union[str, Dict]
```

Converts value to bytes from string

**Arguments**:

- `column_name` (`str`): name of the field
- `value` (`Any`): value fo the field

**Returns**:

`Any`: converted value if needed, else original value

<a name="models.newbasemodel.NewBaseModel._convert_bytes_to_str"></a>
#### \_convert\_bytes\_to\_str

```python
 | _convert_bytes_to_str(column_name: str, value: Any) -> Union[str, Dict]
```

Converts value to str from bytes for represent_as_base64_str columns.

**Arguments**:

- `column_name` (`str`): name of the field
- `value` (`Any`): value fo the field

**Returns**:

`Any`: converted value if needed, else original value

<a name="models.newbasemodel.NewBaseModel._convert_json"></a>
#### \_convert\_json

```python
 | _convert_json(column_name: str, value: Any) -> Union[str, Dict]
```

Converts value to/from json if needed (for Json columns).

**Arguments**:

- `column_name` (`str`): name of the field
- `value` (`Any`): value fo the field

**Returns**:

`Any`: converted value if needed, else original value

<a name="models.newbasemodel.NewBaseModel._extract_own_model_fields"></a>
#### \_extract\_own\_model\_fields

```python
 | _extract_own_model_fields() -> Dict
```

Returns a dictionary with field names and values for fields that are not
relations fields (ForeignKey, ManyToMany etc.)

**Returns**:

`Dict`: dictionary of fields names and values.

<a name="models.newbasemodel.NewBaseModel._extract_model_db_fields"></a>
#### \_extract\_model\_db\_fields

```python
 | _extract_model_db_fields() -> Dict
```

Returns a dictionary with field names and values for fields that are stored in
current model's table.

That includes own non-relational fields ang foreign key fields.

**Returns**:

`Dict`: dictionary of fields names and values.

<a name="models.newbasemodel.NewBaseModel.get_relation_model_id"></a>
#### get\_relation\_model\_id

```python
 | get_relation_model_id(target_field: "BaseField") -> Optional[int]
```

Returns an id of the relation side model to use in prefetch query.

**Arguments**:

- `target_field` (`"BaseField"`): field with relation definition

**Returns**:

`Optional[int]`: value of pk if set

