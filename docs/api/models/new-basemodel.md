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

- `ModelError`: if abstract model is initialized or unknown field is passed

**Arguments**:

- `args (Any)`: ignored args
- `kwargs (Any)`: keyword arguments - all fields values and some special params

<a name="models.newbasemodel.NewBaseModel.__setattr__"></a>
#### \_\_setattr\_\_

```python
 | __setattr__(name: str, value: Any) -> None
```

Overwrites setattr in object to allow for special behaviour of certain params.

Parameter "pk" is translated into actual primary key field name.

Relations are expanded (child model constructed if needed) and registered on
both ends of the relation. The related models are handled by RelationshipManager
exposed at _orm param.

Json fields converted if needed.

Setting pk, foreign key value or any other field value sets Model save status
to False. Setting a reverse relation or many to many relation does not as it
does not modify the state of the model (but related model or through model).

To short circuit all checks and expansions the set of attribute names present
on each model is gathered into _quick_access_fields that is looked first and
if field is in this set the object setattr is called directly.

**Arguments**:

- `name (str)`: name of the attribute to set
- `value (Any)`: value of the attribute to set

**Returns**:

`(None)`: None

<a name="models.newbasemodel.NewBaseModel.__getattribute__"></a>
#### \_\_getattribute\_\_

```python
 | __getattribute__(item: str) -> Any
```

Because we need to overwrite getting the attribute by ormar instead of pydantic
as well as returning related models and not the value stored on the model the
__getattribute__ needs to be used not __getattr__.

It's used to access all attributes so it can be a big overhead that's why a
number of short circuits is used.

To short circuit all checks and expansions the set of attribute names present
on each model is gathered into _quick_access_fields that is looked first and
if field is in this set the object setattr is called directly.

To avoid recursion object's getattribute is used to actually get the attribute
value from the model after the checks.

Even the function calls are constructed with objects functions.

Parameter "pk" is translated into actual primary key field name.

Relations are returned so the actual related model is returned and not current
model's field. The related models are handled by RelationshipManager exposed
at _orm param.

Json fields are converted if needed.

**Arguments**:

- `item (str)`: name of the attribute to retrieve

**Returns**:

`(Any)`: value of the attribute

<a name="models.newbasemodel.NewBaseModel._extract_related_model_instead_of_field"></a>
#### \_extract\_related\_model\_instead\_of\_field

```python
 | _extract_related_model_instead_of_field(item: str) -> Optional[Union["T", Sequence["T"]]]
```

Retrieves the related model/models from RelationshipManager.

**Arguments**:

- `item (str)`: name of the relation

**Returns**:

`(Optional[Union[Model, List[Model]]])`: related model, list of related models or None

<a name="models.newbasemodel.NewBaseModel.__eq__"></a>
#### \_\_eq\_\_

```python
 | __eq__(other: object) -> bool
```

Compares other model to this model. when == is called.

**Arguments**:

- `other (object)`: other model to compare

**Returns**:

`(bool)`: result of comparison

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

- `other (NewBaseModel)`: model to compare to

**Returns**:

`(bool)`: result of comparison

<a name="models.newbasemodel.NewBaseModel.get_name"></a>
#### get\_name

```python
 | @classmethod
 | get_name(cls, lower: bool = True) -> str
```

Returns name of the Model class, by default lowercase.

**Arguments**:

- `lower (bool)`: flag if name should be set to lowercase

**Returns**:

`(str)`: name of the model

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

`(sqlalchemy.Column)`: primary key sqlalchemy column

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
 | remove(parent: "T", name: str) -> None
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

- `include (Union[Set, Dict, None])`: fields to include
- `exclude (Union[Set, Dict, None])`: fields to exclude

**Returns**:

`(Set[str])`: set of property fields names

<a name="models.newbasemodel.NewBaseModel._get_related_not_excluded_fields"></a>
#### \_get\_related\_not\_excluded\_fields

```python
 | _get_related_not_excluded_fields(include: Optional[Dict], exclude: Optional[Dict]) -> List
```

Returns related field names applying on them include and exclude set.

**Arguments**:

- `include (Union[Set, Dict, None])`: fields to include
- `exclude (Union[Set, Dict, None])`: fields to exclude

**Returns**:

`(List of fields with relations that is not excluded)`: 

<a name="models.newbasemodel.NewBaseModel._extract_nested_models_from_list"></a>
#### \_extract\_nested\_models\_from\_list

```python
 | @staticmethod
 | _extract_nested_models_from_list(models: MutableSequence, include: Union[Set, Dict, None], exclude: Union[Set, Dict, None]) -> List
```

Converts list of models into list of dictionaries.

**Arguments**:

- `models (List)`: List of models
- `include (Union[Set, Dict, None])`: fields to include
- `exclude (Union[Set, Dict, None])`: fields to exclude

**Returns**:

`(List[Dict])`: list of models converted to dictionaries

<a name="models.newbasemodel.NewBaseModel._skip_ellipsis"></a>
#### \_skip\_ellipsis

```python
 | _skip_ellipsis(items: Union[Set, Dict, None], key: str) -> Union[Set, Dict, None]
```

Helper to traverse the include/exclude dictionaries.
In dict() Ellipsis should be skipped as it indicates all fields required
and not the actual set/dict with fields names.

**Arguments**:

- `items (Union[Set, Dict, None])`: current include/exclude value
- `key (str)`: key for nested relations to check

**Returns**:

`(Union[Set, Dict, None])`: nested value of the items

<a name="models.newbasemodel.NewBaseModel._extract_nested_models"></a>
#### \_extract\_nested\_models

```python
 | _extract_nested_models(nested: bool, dict_instance: Dict, include: Optional[Dict], exclude: Optional[Dict]) -> Dict
```

Traverse nested models and converts them into dictionaries.
Calls itself recursively if needed.

**Arguments**:

- `nested (bool)`: flag if current instance is nested
- `dict_instance (Dict)`: current instance dict
- `include (Optional[Dict])`: fields to include
- `exclude (Optional[Dict])`: fields to exclude

**Returns**:

`(Dict)`: current model dict with child models converted to dictionaries

<a name="models.newbasemodel.NewBaseModel.dict"></a>
#### dict

```python
 | dict(*, include: Union[Set, Dict] = None, exclude: Union[Set, Dict] = None, by_alias: bool = False, skip_defaults: bool = None, exclude_unset: bool = False, exclude_defaults: bool = False, exclude_none: bool = False, nested: bool = False) -> "DictStrAny"
```

Generate a dictionary representation of the model,
optionally specifying which fields to include or exclude.

Nested models are also parsed to dictionaries.

Additionally fields decorated with @property_field are also added.

**Arguments**:

- `include (Union[Set, Dict, None])`: fields to include
- `exclude (Union[Set, Dict, None])`: fields to exclude
- `by_alias (bool)`: flag to get values by alias - passed to pydantic
- `skip_defaults (bool)`: flag to not set values - passed to pydantic
- `exclude_unset (bool)`: flag to exclude not set values - passed to pydantic
- `exclude_defaults (bool)`: flag to exclude default values - passed to pydantic
- `exclude_none (bool)`: flag to exclude None values - passed to pydantic
- `nested (bool)`: flag if the current model is nested

**Returns**:

`()`: 

<a name="models.newbasemodel.NewBaseModel.update_from_dict"></a>
#### update\_from\_dict

```python
 | update_from_dict(value_dict: Dict) -> "NewBaseModel"
```

Updates self with values of fields passed in the dictionary.

**Arguments**:

- `value_dict (Dict)`: dictionary of fields names and values

**Returns**:

`(NewBaseModel)`: self

<a name="models.newbasemodel.NewBaseModel._convert_json"></a>
#### \_convert\_json

```python
 | _convert_json(column_name: str, value: Any, op: str) -> Union[str, Dict]
```

Converts value to/from json if needed (for Json columns).

**Arguments**:

- `column_name (str)`: name of the field
- `value (Any)`: value fo the field
- `op (str)`: operator on json

**Returns**:

`(Any)`: converted value if needed, else original value

<a name="models.newbasemodel.NewBaseModel._is_conversion_to_json_needed"></a>
#### \_is\_conversion\_to\_json\_needed

```python
 | _is_conversion_to_json_needed(column_name: str) -> bool
```

Checks if given column name is related to JSON field.

**Arguments**:

- `column_name (str)`: name of the field

**Returns**:

`(bool)`: result of the check

<a name="models.newbasemodel.NewBaseModel._extract_own_model_fields"></a>
#### \_extract\_own\_model\_fields

```python
 | _extract_own_model_fields() -> Dict
```

Returns a dictionary with field names and values for fields that are not
relations fields (ForeignKey, ManyToMany etc.)

**Returns**:

`(Dict)`: dictionary of fields names and values.

<a name="models.newbasemodel.NewBaseModel._extract_model_db_fields"></a>
#### \_extract\_model\_db\_fields

```python
 | _extract_model_db_fields() -> Dict
```

Returns a dictionary with field names and values for fields that are stored in
current model's table.

That includes own non-relational fields ang foreign key fields.

**Returns**:

`(Dict)`: dictionary of fields names and values.

<a name="models.newbasemodel.NewBaseModel.get_relation_model_id"></a>
#### get\_relation\_model\_id

```python
 | get_relation_model_id(target_field: Type["BaseField"]) -> Optional[int]
```

Returns an id of the relation side model to use in prefetch query.

**Arguments**:

- `target_field (Type["BaseField"])`: field with relation definition

**Returns**:

`(Optional[int])`: value of pk if set

