<a name="fields.base"></a>
# fields.base

<a name="fields.base.BaseField"></a>
## BaseField Objects

```python
class BaseField(FieldInfo)
```

BaseField serves as a parent class for all basic Fields in ormar.
It keeps all common parameters available for all fields as well as
set of useful functions.

All values are kept as class variables, ormar Fields are never instantiated.
Subclasses pydantic.FieldInfo to keep the fields related
to pydantic field types like ConstrainedStr

<a name="fields.base.BaseField.is_valid_uni_relation"></a>
#### is\_valid\_uni\_relation

```python
 | is_valid_uni_relation() -> bool
```

Checks if field is a relation definition but only for ForeignKey relation,
so excludes ManyToMany fields, as well as virtual ForeignKey
(second side of FK relation).

Is used to define if a field is a db ForeignKey column that
should be saved/populated when dealing with internal/own
Model columns only.

**Returns**:

`bool`: result of the check

<a name="fields.base.BaseField.get_alias"></a>
#### get\_alias

```python
 | get_alias() -> str
```

Used to translate Model column names to database column names during db queries.

**Returns**:

`str`: returns custom database column name if defined by user,

<a name="fields.base.BaseField.get_pydantic_default"></a>
#### get\_pydantic\_default

```python
 | get_pydantic_default() -> Dict
```

Generates base pydantic.FieldInfo with only default and optionally
required to fix pydantic Json field being set to required=False.
Used in an ormar Model Metaclass.

**Returns**:

`pydantic.FieldInfo`: instance of base pydantic.FieldInfo

<a name="fields.base.BaseField.default_value"></a>
#### default\_value

```python
 | default_value(use_server: bool = False) -> Optional[Dict]
```

Returns a FieldInfo instance with populated default
(static) or default_factory (function).
If the field is a autoincrement primary key the default is None.
Otherwise field have to has either default, or default_factory populated.

If all default conditions fail None is returned.

Used in converting to pydantic FieldInfo.

**Arguments**:

treated as default value, default False
- `use_server` (`bool`): flag marking if server_default should be

**Returns**:

`Optional[pydantic.FieldInfo]`: returns a call to pydantic.Field

<a name="fields.base.BaseField.get_default"></a>
#### get\_default

```python
 | get_default(use_server: bool = False) -> Any
```

Return default value for a field.
If the field is Callable the function is called and actual result is returned.
Used to populate default_values for pydantic Model in ormar Model Metaclass.

**Arguments**:

treated as default value, default False
- `use_server` (`bool`): flag marking if server_default should be

**Returns**:

`Any`: default value for the field if set, otherwise implicit None

<a name="fields.base.BaseField.has_default"></a>
#### has\_default

```python
 | has_default(use_server: bool = True) -> bool
```

Checks if the field has default value set.

**Arguments**:

treated as default value, default False
- `use_server` (`bool`): flag marking if server_default should be

**Returns**:

`bool`: result of the check if default value is set

<a name="fields.base.BaseField.is_auto_primary_key"></a>
#### is\_auto\_primary\_key

```python
 | is_auto_primary_key() -> bool
```

Checks if field is first a primary key and if it,
it's than check if it's set to autoincrement.
Autoincrement primary_key is nullable/optional.

**Returns**:

`bool`: result of the check for primary key and autoincrement

<a name="fields.base.BaseField.construct_constraints"></a>
#### construct\_constraints

```python
 | construct_constraints() -> List
```

Converts list of ormar constraints into sqlalchemy ForeignKeys.
Has to be done dynamically as sqlalchemy binds ForeignKey to the table.
And we need a new ForeignKey for subclasses of current model

**Returns**:

`List[sqlalchemy.schema.ForeignKey]`: List of sqlalchemy foreign keys - by default one.

<a name="fields.base.BaseField.get_column"></a>
#### get\_column

```python
 | get_column(name: str) -> sqlalchemy.Column
```

Returns definition of sqlalchemy.Column used in creation of sqlalchemy.Table.
Populates name, column type constraints, as well as a number of parameters like
primary_key, index, unique, nullable, default and server_default.

**Arguments**:

- `name` (`str`): name of the db column - used if alias is not set

**Returns**:

`sqlalchemy.Column`: actual definition of the database column as sqlalchemy requires.

<a name="fields.base.BaseField._get_encrypted_column"></a>
#### \_get\_encrypted\_column

```python
 | _get_encrypted_column(name: str) -> sqlalchemy.Column
```

Returns EncryptedString column type instead of actual column.

**Arguments**:

- `name` (`str`): column name

**Returns**:

`sqlalchemy.Column`: newly defined column

<a name="fields.base.BaseField.expand_relationship"></a>
#### expand\_relationship

```python
 | expand_relationship(value: Any, child: Union["Model", "NewBaseModel"], to_register: bool = True) -> Any
```

Function overwritten for relations, in basic field the value is returned as is.
For relations the child model is first constructed (if needed),
registered in relation and returned.
For relation fields the value can be a pk value (Any type of field),
dict (from Model) or actual instance/list of a "Model".

**Arguments**:

- `value` (`Any`): a Model field value, returned untouched for non relation fields.
- `child` (`Union["Model", "NewBaseModel"]`): a child Model to register
- `to_register` (`bool`): flag if the relation should be set in RelationshipManager

**Returns**:

`Any`: returns untouched value for normal fields, expands only for relations

<a name="fields.base.BaseField.set_self_reference_flag"></a>
#### set\_self\_reference\_flag

```python
 | set_self_reference_flag() -> None
```

Sets `self_reference` to True if field to and owner are same model.

**Returns**:

`None`: None

<a name="fields.base.BaseField.has_unresolved_forward_refs"></a>
#### has\_unresolved\_forward\_refs

```python
 | has_unresolved_forward_refs() -> bool
```

Verifies if the filed has any ForwardRefs that require updating before the
model can be used.

**Returns**:

`bool`: result of the check

<a name="fields.base.BaseField.evaluate_forward_ref"></a>
#### evaluate\_forward\_ref

```python
 | evaluate_forward_ref(globalns: Any, localns: Any) -> None
```

Evaluates the ForwardRef to actual Field based on global and local namespaces

**Arguments**:

- `globalns` (`Any`): global namespace
- `localns` (`Any`): local namespace

**Returns**:

`None`: None

<a name="fields.base.BaseField.get_related_name"></a>
#### get\_related\_name

```python
 | get_related_name() -> str
```

Returns name to use for reverse relation.
It's either set as `related_name` or by default it's owner model. get_name + 's'

**Returns**:

`str`: name of the related_name or default related name.

