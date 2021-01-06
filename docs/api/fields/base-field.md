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
 | @classmethod
 | is_valid_uni_relation(cls) -> bool
```

Checks if field is a relation definition but only for ForeignKey relation,
so excludes ManyToMany fields, as well as virtual ForeignKey
(second side of FK relation).

Is used to define if a field is a db ForeignKey column that
should be saved/populated when dealing with internal/own
Model columns only.

**Returns**:

`(bool)`: result of the check

<a name="fields.base.BaseField.get_alias"></a>
#### get\_alias

```python
 | @classmethod
 | get_alias(cls) -> str
```

Used to translate Model column names to database column names during db queries.

**Returns**:

`(str)`: returns custom database column name if defined by user,
otherwise field name in ormar/pydantic

<a name="fields.base.BaseField.is_valid_field_info_field"></a>
#### is\_valid\_field\_info\_field

```python
 | @classmethod
 | is_valid_field_info_field(cls, field_name: str) -> bool
```

Checks if field belongs to pydantic FieldInfo
- used during setting default pydantic values.
Excludes defaults and alias as they are populated separately
(defaults) or not at all (alias)

**Arguments**:

- `field_name (str)`: field name of BaseFIeld

**Returns**:

`(bool)`: True if field is present on pydantic.FieldInfo

<a name="fields.base.BaseField.convert_to_pydantic_field_info"></a>
#### convert\_to\_pydantic\_field\_info

```python
 | @classmethod
 | convert_to_pydantic_field_info(cls, allow_null: bool = False) -> FieldInfo
```

Converts a BaseField into pydantic.FieldInfo
that is later easily processed by pydantic.
Used in an ormar Model Metaclass.

**Arguments**:

- `allow_null (bool)`: flag if the default value can be None
or if it should be populated by pydantic Undefined

**Returns**:

`(pydantic.FieldInfo)`: actual instance of pydantic.FieldInfo with all needed fields populated

<a name="fields.base.BaseField.default_value"></a>
#### default\_value

```python
 | @classmethod
 | default_value(cls, use_server: bool = False) -> Optional[FieldInfo]
```

Returns a FieldInfo instance with populated default
(static) or default_factory (function).
If the field is a autoincrement primary key the default is None.
Otherwise field have to has either default, or default_factory populated.

If all default conditions fail None is returned.

Used in converting to pydantic FieldInfo.

**Arguments**:

- `use_server (bool)`: flag marking if server_default should be
treated as default value, default False

**Returns**:

`(Optional[pydantic.FieldInfo])`: returns a call to pydantic.Field
which is returning a FieldInfo instance

<a name="fields.base.BaseField.get_default"></a>
#### get\_default

```python
 | @classmethod
 | get_default(cls, use_server: bool = False) -> Any
```

Return default value for a field.
If the field is Callable the function is called and actual result is returned.
Used to populate default_values for pydantic Model in ormar Model Metaclass.

**Arguments**:

- `use_server (bool)`: flag marking if server_default should be
treated as default value, default False

**Returns**:

`(Any)`: default value for the field if set, otherwise implicit None

<a name="fields.base.BaseField.has_default"></a>
#### has\_default

```python
 | @classmethod
 | has_default(cls, use_server: bool = True) -> bool
```

Checks if the field has default value set.

**Arguments**:

- `use_server (bool)`: flag marking if server_default should be
treated as default value, default False

**Returns**:

`(bool)`: result of the check if default value is set

<a name="fields.base.BaseField.is_auto_primary_key"></a>
#### is\_auto\_primary\_key

```python
 | @classmethod
 | is_auto_primary_key(cls) -> bool
```

Checks if field is first a primary key and if it,
it's than check if it's set to autoincrement.
Autoincrement primary_key is nullable/optional.

**Returns**:

`(bool)`: result of the check for primary key and autoincrement

<a name="fields.base.BaseField.construct_constraints"></a>
#### construct\_constraints

```python
 | @classmethod
 | construct_constraints(cls) -> List
```

Converts list of ormar constraints into sqlalchemy ForeignKeys.
Has to be done dynamically as sqlalchemy binds ForeignKey to the table.
And we need a new ForeignKey for subclasses of current model

**Returns**:

`(List[sqlalchemy.schema.ForeignKey])`: List of sqlalchemy foreign keys - by default one.

<a name="fields.base.BaseField.get_column"></a>
#### get\_column

```python
 | @classmethod
 | get_column(cls, name: str) -> sqlalchemy.Column
```

Returns definition of sqlalchemy.Column used in creation of sqlalchemy.Table.
Populates name, column type constraints, as well as a number of parameters like
primary_key, index, unique, nullable, default and server_default.

**Arguments**:

- `name (str)`: name of the db column - used if alias is not set

**Returns**:

`(sqlalchemy.Column)`: actual definition of the database column as sqlalchemy requires.

<a name="fields.base.BaseField.expand_relationship"></a>
#### expand\_relationship

```python
 | @classmethod
 | expand_relationship(cls, value: Any, child: Union["Model", "NewBaseModel"], to_register: bool = True, relation_name: str = None) -> Any
```

Function overwritten for relations, in basic field the value is returned as is.
For relations the child model is first constructed (if needed),
registered in relation and returned.
For relation fields the value can be a pk value (Any type of field),
dict (from Model) or actual instance/list of a "Model".

**Arguments**:

- `value (Any)`: a Model field value, returned untouched for non relation fields.
- `child (Union["Model", "NewBaseModel"])`: a child Model to register
- `to_register (bool)`: flag if the relation should be set in RelationshipManager

**Returns**:

`(Any)`: returns untouched value for normal fields, expands only for relations

