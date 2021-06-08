<a name="fields.model_fields"></a>
# fields.model\_fields

<a name="fields.model_fields.is_field_nullable"></a>
#### is\_field\_nullable

```python
is_field_nullable(nullable: Optional[bool], default: Any, server_default: Any, pydantic_only: Optional[bool]) -> bool
```

Checks if the given field should be nullable/ optional based on parameters given.

**Arguments**:

- `nullable` (`Optional[bool]`): flag explicit setting a column as nullable
- `default` (`Any`): value or function to be called as default in python
- `server_default` (`Any`): function to be called as default by sql server
- `pydantic_only` (`Optional[bool]`): flag if fields should not be included in the sql table

**Returns**:

`bool`: result of the check

<a name="fields.model_fields.is_auto_primary_key"></a>
#### is\_auto\_primary\_key

```python
is_auto_primary_key(primary_key: bool, autoincrement: bool) -> bool
```

Checks if field is an autoincrement pk -> if yes it's optional.

**Arguments**:

- `primary_key` (`bool`): flag if field is a pk field
- `autoincrement` (`bool`): flag if field should be autoincrement

**Returns**:

`bool`: result of the check

<a name="fields.model_fields.ModelFieldFactory"></a>
## ModelFieldFactory Objects

```python
class ModelFieldFactory()
```

Default field factory that construct Field classes and populated their values.

<a name="fields.model_fields.ModelFieldFactory.get_column_type"></a>
#### get\_column\_type

```python
 | @classmethod
 | get_column_type(cls, **kwargs: Any) -> Any
```

Return proper type of db column for given field type.
Accepts required and optional parameters that each column type accepts.

**Arguments**:

- `kwargs` (`Any`): key, value pairs of sqlalchemy options

**Returns**:

`sqlalchemy Column`: initialized column with proper options

<a name="fields.model_fields.ModelFieldFactory.validate"></a>
#### validate

```python
 | @classmethod
 | validate(cls, **kwargs: Any) -> None
```

Used to validate if all required parameters on a given field type are set.

**Arguments**:

- `kwargs` (`Any`): all params passed during construction

<a name="fields.model_fields.String"></a>
## String Objects

```python
class String(ModelFieldFactory,  str)
```

String field factory that construct Field classes and populated their values.

<a name="fields.model_fields.String.get_column_type"></a>
#### get\_column\_type

```python
 | @classmethod
 | get_column_type(cls, **kwargs: Any) -> Any
```

Return proper type of db column for given field type.
Accepts required and optional parameters that each column type accepts.

**Arguments**:

- `kwargs` (`Any`): key, value pairs of sqlalchemy options

**Returns**:

`sqlalchemy Column`: initialized column with proper options

<a name="fields.model_fields.String.validate"></a>
#### validate

```python
 | @classmethod
 | validate(cls, **kwargs: Any) -> None
```

Used to validate if all required parameters on a given field type are set.

**Arguments**:

- `kwargs` (`Any`): all params passed during construction

<a name="fields.model_fields.Integer"></a>
## Integer Objects

```python
class Integer(ModelFieldFactory,  int)
```

Integer field factory that construct Field classes and populated their values.

<a name="fields.model_fields.Integer.get_column_type"></a>
#### get\_column\_type

```python
 | @classmethod
 | get_column_type(cls, **kwargs: Any) -> Any
```

Return proper type of db column for given field type.
Accepts required and optional parameters that each column type accepts.

**Arguments**:

- `kwargs` (`Any`): key, value pairs of sqlalchemy options

**Returns**:

`sqlalchemy Column`: initialized column with proper options

<a name="fields.model_fields.Text"></a>
## Text Objects

```python
class Text(ModelFieldFactory,  str)
```

Text field factory that construct Field classes and populated their values.

<a name="fields.model_fields.Text.get_column_type"></a>
#### get\_column\_type

```python
 | @classmethod
 | get_column_type(cls, **kwargs: Any) -> Any
```

Return proper type of db column for given field type.
Accepts required and optional parameters that each column type accepts.

**Arguments**:

- `kwargs` (`Any`): key, value pairs of sqlalchemy options

**Returns**:

`sqlalchemy Column`: initialized column with proper options

<a name="fields.model_fields.Float"></a>
## Float Objects

```python
class Float(ModelFieldFactory,  float)
```

Float field factory that construct Field classes and populated their values.

<a name="fields.model_fields.Float.get_column_type"></a>
#### get\_column\_type

```python
 | @classmethod
 | get_column_type(cls, **kwargs: Any) -> Any
```

Return proper type of db column for given field type.
Accepts required and optional parameters that each column type accepts.

**Arguments**:

- `kwargs` (`Any`): key, value pairs of sqlalchemy options

**Returns**:

`sqlalchemy Column`: initialized column with proper options

<a name="fields.model_fields.DateTime"></a>
## DateTime Objects

```python
class DateTime(ModelFieldFactory,  datetime.datetime)
```

DateTime field factory that construct Field classes and populated their values.

<a name="fields.model_fields.DateTime.get_column_type"></a>
#### get\_column\_type

```python
 | @classmethod
 | get_column_type(cls, **kwargs: Any) -> Any
```

Return proper type of db column for given field type.
Accepts required and optional parameters that each column type accepts.

**Arguments**:

- `kwargs` (`Any`): key, value pairs of sqlalchemy options

**Returns**:

`sqlalchemy Column`: initialized column with proper options

<a name="fields.model_fields.Date"></a>
## Date Objects

```python
class Date(ModelFieldFactory,  datetime.date)
```

Date field factory that construct Field classes and populated their values.

<a name="fields.model_fields.Date.get_column_type"></a>
#### get\_column\_type

```python
 | @classmethod
 | get_column_type(cls, **kwargs: Any) -> Any
```

Return proper type of db column for given field type.
Accepts required and optional parameters that each column type accepts.

**Arguments**:

- `kwargs` (`Any`): key, value pairs of sqlalchemy options

**Returns**:

`sqlalchemy Column`: initialized column with proper options

<a name="fields.model_fields.Time"></a>
## Time Objects

```python
class Time(ModelFieldFactory,  datetime.time)
```

Time field factory that construct Field classes and populated their values.

<a name="fields.model_fields.Time.get_column_type"></a>
#### get\_column\_type

```python
 | @classmethod
 | get_column_type(cls, **kwargs: Any) -> Any
```

Return proper type of db column for given field type.
Accepts required and optional parameters that each column type accepts.

**Arguments**:

- `kwargs` (`Any`): key, value pairs of sqlalchemy options

**Returns**:

`sqlalchemy Column`: initialized column with proper options

<a name="fields.model_fields.JSON"></a>
## JSON Objects

```python
class JSON(ModelFieldFactory,  pydantic.Json)
```

JSON field factory that construct Field classes and populated their values.

<a name="fields.model_fields.JSON.get_column_type"></a>
#### get\_column\_type

```python
 | @classmethod
 | get_column_type(cls, **kwargs: Any) -> Any
```

Return proper type of db column for given field type.
Accepts required and optional parameters that each column type accepts.

**Arguments**:

- `kwargs` (`Any`): key, value pairs of sqlalchemy options

**Returns**:

`sqlalchemy Column`: initialized column with proper options

<a name="fields.model_fields.BigInteger"></a>
## BigInteger Objects

```python
class BigInteger(Integer,  int)
```

BigInteger field factory that construct Field classes and populated their values.

<a name="fields.model_fields.BigInteger.get_column_type"></a>
#### get\_column\_type

```python
 | @classmethod
 | get_column_type(cls, **kwargs: Any) -> Any
```

Return proper type of db column for given field type.
Accepts required and optional parameters that each column type accepts.

**Arguments**:

- `kwargs` (`Any`): key, value pairs of sqlalchemy options

**Returns**:

`sqlalchemy Column`: initialized column with proper options

<a name="fields.model_fields.Decimal"></a>
## Decimal Objects

```python
class Decimal(ModelFieldFactory,  decimal.Decimal)
```

Decimal field factory that construct Field classes and populated their values.

<a name="fields.model_fields.Decimal.get_column_type"></a>
#### get\_column\_type

```python
 | @classmethod
 | get_column_type(cls, **kwargs: Any) -> Any
```

Return proper type of db column for given field type.
Accepts required and optional parameters that each column type accepts.

**Arguments**:

- `kwargs` (`Any`): key, value pairs of sqlalchemy options

**Returns**:

`sqlalchemy Column`: initialized column with proper options

<a name="fields.model_fields.Decimal.validate"></a>
#### validate

```python
 | @classmethod
 | validate(cls, **kwargs: Any) -> None
```

Used to validate if all required parameters on a given field type are set.

**Arguments**:

- `kwargs` (`Any`): all params passed during construction

<a name="fields.model_fields.UUID"></a>
## UUID Objects

```python
class UUID(ModelFieldFactory,  uuid.UUID)
```

UUID field factory that construct Field classes and populated their values.

<a name="fields.model_fields.UUID.get_column_type"></a>
#### get\_column\_type

```python
 | @classmethod
 | get_column_type(cls, **kwargs: Any) -> Any
```

Return proper type of db column for given field type.
Accepts required and optional parameters that each column type accepts.

**Arguments**:

- `kwargs` (`Any`): key, value pairs of sqlalchemy options

**Returns**:

`sqlalchemy Column`: initialized column with proper options

