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

`nullable`: `bool` = `not primary_key` -> defaults to False for primary key column, and True for all other. 

Specifies if field is optional or required, used both with sql and pydantic.

!!!note
    By default all `ForeignKeys` are also nullable, meaning the related `Model` is not required.
    
    If you change the `ForeignKey` column to `nullable=False`, it becomes required.
    

!!!info
    If you want to know more about how you can preload related models during queries and how the relations work read the [queries][queries] and [relations][relations] sections. 


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

```Python hl_lines="21-23"
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
 
## index

`index`: `bool` = `False` -> by default False, 

Sets the index on a table's column.

Used in sql only.

## unique

`unique`: `bool` = `False` 

Sets the unique constraint on a table's column.

Used in sql only.

## pydantic_only (**DEPRECATED**)

**This parameter is deprecated and will be removed in one of next releases!**

**To check how to declare pydantic only fields that are not saved into database see [pydantic fields section](pydantic-fields.md)** 

`pydantic_only`: `bool` = `False` 

Prevents creation of a sql column for given field.

Used for data related to given model but not to be stored in the database.

Used in pydantic only.

## choices

`choices`: `Sequence` = `[]` 

A set of choices allowed to be used for given field.

Used for data validation on pydantic side.

Prevents insertion of value not present in the choices list.

Used in pydantic only.

[relations]: ../relations/index.md
[queries]: ../queries/index.md
[pydantic]: https://pydantic-docs.helpmanual.io/usage/types/#constrained-types
[server default]: https://docs.sqlalchemy.org/en/13/core/defaults.html#server-invoked-ddl-explicit-default-expressions