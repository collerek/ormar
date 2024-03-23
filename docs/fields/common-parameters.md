# Common Parameters

All `Field` types have a set of common parameters.

## primary_key

`primary_key`: `bool` = `False` -> by default False.

Sets the primary key column on a table, foreign keys always refer to the pk of the `Model`.

Used in sql only.

## autoincrement

`autoincrement`: `bool` = `primary_key and type == int` -> defaults to True if column is a primary key and of type Integer, otherwise False.

Can be only used with int/bigint fields.

If a field has autoincrement it becomes optional.

Used both in sql and pydantic (changes pk field to optional for autoincrement).

## nullable

`nullable`: `bool` = `False` -> defaults to False for all fields except relation fields.

Automatically changed to True if user provide one of the following:

* `default` value or function is provided
* `server_default` value or function is provided
* `autoincrement` is set on `Integer` `primary_key` field

Specifies if field is optional or required, used both with sql and pydantic.

By default, used for both `pydantic` and `sqlalchemy` as those are the most common settings:

* `nullable=False` - means database column is not null and field is required in pydantic
* `nullable=True` - means database column is null and field is optional in pydantic

If you want to set different setting for pydantic and the database see `sql_nullable` below.

!!!note
    By default all `ForeignKeys` are also nullable, meaning the related `Model` is not required.
    
    If you change the `ForeignKey` column to `nullable=False`, it becomes required.
    

## sql_nullable

`sql_nullable`: `bool` = `nullable` -> defaults to the value of nullable (described above). 

Specifies if field is not null or allows nulls in the database only. 

Use this setting in combination with `nullable` only if you want to set different options on pydantic model and in the database. 

A sample usage might be i.e. making field not null in the database, but allow this field to be nullable in pydantic (i.e. with `server_default` value).
That will prevent the updates of the field to null (as with `server_default` set you cannot insert null values already as the default value would be used)



## default

`default`: `Any` = `None` -> defaults to None. 

A default value used if no other value is passed.

In sql invoked on an insert, used during pydantic model definition.

If the field has a default value it becomes optional.

You can pass a static value or a Callable (function etc.)

Used both in sql and pydantic.

Sample usage:

```python
# note the distinction between passing a value and Callable pointer

# value
name: str = ormar.String(max_length=200, default="Name")

# note that when you call a function it's not a pointer to Callable
# a definition like this will call the function at startup and assign
# the result of the function to the default, so it will be constant value for all instances
created_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.now())

# if you want to pass Callable reference (note that it cannot have arguments)
# note lack of the parenthesis -> ormar will call this function for you on each model
created_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)

# Callable can be a function, builtin, class etc.
```

## server default

`server_default`: `Any` = `None`  -> defaults to None. 

A default value used if no other value is passed.

In sql invoked on the server side so you can pass i.e. sql function (like now() or query/value wrapped in sqlalchemy text() clause).

If the field has a server_default value it becomes optional.

You can pass a static value or a Callable (function etc.)

Used in sql only.

Sample usage:

```Python hl_lines="20-22"
--8<-- "../docs_src/fields/docs004.py"
```

!!!warning
    `server_default` accepts `str`, `sqlalchemy.sql.elements.ClauseElement` or `sqlalchemy.sql.elements.TextClause`
    so if you want to set i.e. Integer value you need to wrap it in `sqlalchemy.text()` function like above

!!!tip
    You can pass also valid sql (dialect specific) wrapped in `sqlalchemy.text()`
    
    For example `func.now()` above could be exchanged for `text('(CURRENT_TIMESTAMP)')` for sqlite backend

!!!info
    `server_default` is passed straight to sqlalchemy table definition so you can read more in [server default][server default] sqlalchemy documentation

## name

`name`: `str` = `None` -> defaults to None

Allows you to specify a column name alias to be used. 

Useful for existing database structures that use a reserved keyword, or if you would like to use database name that is different from `ormar` field name. 

Take for example the snippet below. 

`from`, being a reserved word in python, will prevent you from creating a model with that column name. 

Changing the model name to `from_` and adding the parameter `name='from'` will cause ormar to use `from` for the database column name. 

```python
 #... rest of Model cut for brevity
 from_: str = ormar.String(max_length=15, name='from')
```

Similarly, you can change the foreign key column names in database, while keeping the desired relation name in ormar:

```python
 # ... rest of Model cut for brevity
album: Optional[Album] = ormar.ForeignKey(Album, name="album_id")
```

## index

`index`: `bool` = `False` -> by default False, 

Sets the index on a table's column.

Used in sql only.

## unique

`unique`: `bool` = `False` 

Sets the unique constraint on a table's column.

Used in sql only.

## overwrite_pydantic_type

By default, ormar uses predefined pydantic field types that it applies on model creation (hence the type hints are optional).

If you want to, you can apply your own type, that will be **completely** replacing the build in one.
So it's on you as a user to provide a type that is valid in the context of given ormar field type.

!!!warning
    Note that by default you should use build in arguments that are passed to underlying pydantic field. 
    
    You can check what arguments are supported in field types section or in [pydantic](https://pydantic-docs.helpmanual.io/usage/schema/#field-customisation) docs.

!!!danger
    Setting a wrong type of pydantic field can break your model, so overwrite it only when you know what you are doing.
    
    As it's easy to break functionality of ormar the `overwrite_pydantic_type` argument is not available on relation fields!

```python
base_ormar_config = ormar.OrmarConfig(
    metadata=metadata
    database=database
)


# sample overwrites
class OverwriteTest(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="overwrites")

    id: int = ormar.Integer(primary_key=True)
    my_int: str = ormar.Integer(overwrite_pydantic_type=PositiveInt)
    constraint_dict: Json = ormar.JSON(
        overwrite_pydantic_type=Optional[Json[Dict[str, int]]])
```

[relations]: ../relations/index.md
[queries]: ../queries/index.md
[pydantic]: https://pydantic-docs.helpmanual.io/usage/types/#constrained-types
[server default]: https://docs.sqlalchemy.org/en/13/core/defaults.html#server-invoked-ddl-explicit-default-expressions
