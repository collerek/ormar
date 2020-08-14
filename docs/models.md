# Models

## Defining models

By defining an ormar Model you get corresponding **Pydantic model** as well as **Sqlalchemy table** for free.
They are being managed in the background and you do not have to create them on your own.

### Model Class

To build an ormar model you simply need to inherit a `ormar.Model` class.

```Python hl_lines="10"
--8<-- "../docs_src/models/docs001.py"
```

### Defining Fields

Next assign one or more of the [Fields][fields] as a class level variables.

Each table **has to** have a primary key column, which you specify by setting `primary_key=True` on selected field.

Only one primary key column is allowed.

```Python hl_lines="14 15 16"
--8<-- "../docs_src/models/docs001.py"
```

!!! warning 
    Not assigning `primary_key` column or assigning more than one column per `Model` will raise `ModelDefinitionError`
    exception.

By default if you assign primary key to `Integer` field, the `autoincrement` option is set to true.

You can disable by passing `autoincremant=False`.

```Python 
id = ormar.Integer(primary_key=True, autoincrement=False)
```

Names of the fields will be used for both the underlying `pydantic` model and `sqlalchemy` table.

### Dependencies

Since ormar depends on [`databases`][databases] and [`sqlalchemy-core`][sqlalchemy-core] for database connection 
and table creation you need to assign each `Model` with two special parameters.

#### Databases

One is `Database` instance created with your database url in [sqlalchemy connection string][sqlalchemy connection string] format.

Created instance needs to be passed to every `Model` with `__database__` parameter.

```Python hl_lines="1 6 11"
--8<-- "../docs_src/models/docs001.py"
```

!!! tip
    You need to create the `Database` instance **only once** and use it for all models. 
    You can create several ones if you want to use multiple databases.

#### Sqlalchemy

Second dependency is sqlalchemy `MetaData` instance.

Created instance needs to be passed to every `Model` with `__metadata__` parameter.

```Python hl_lines="2 7 12"
--8<-- "../docs_src/models/docs001.py"
```

!!! tip
    You need to create the `MetaData` instance **only once** and use it for all models. 
    You can create several ones if you want to use multiple databases.

### Table Names

By default table name is created from Model class name as lowercase name plus 's'.

You can overwrite this parameter by providing `__tablename__` argument.

```Python hl_lines="11 12 13"
--8<-- "../docs_src/models/docs002.py"
```

## Initialization

There are two ways to create and persist the `Model` instance in the database.

!!!tip 
    Use `ipython` to try this from the console, since it supports `await`.

If you plan to modify the instance in the later execution of your program you can initiate your `Model` as a normal class and later await a `save()` call.  

```Python hl_lines="19 20"
--8<-- "../docs_src/models/docs007.py"
```

If you want to initiate your `Model` and at the same time save in in the database use a QuerySet's method `create()`.

Each model has a `QuerySet` initialised as `objects` parameter 

```Python hl_lines="22"
--8<-- "../docs_src/models/docs007.py"
```

!!!info
    To read more about `QuerySets` and available methods visit [queries][queries]

## Attributes Delegation

Each call to `Model` fields parameter under the hood is delegated to either the `pydantic` model
or other related `Model` in case of relations. 

The fields and relations are not stored on the `Model` itself

```Python hl_lines="31 32 33 34 35 36 37 38 39 40 41"
--8<-- "../docs_src/models/docs006.py"
```

!!! warning
    In example above model instances are created but not persisted that's why `id` of `department` is None!

!!!info
    To read more about `ForeignKeys` and `Model` relations visit [relations][relations]

## Internals

Apart from special parameters defined in the `Model` during definition (tablename, metadata etc.) the `Model` provides you with useful internals.

### Pydantic Model

To access auto created pydantic model you can use `Model.__pydantic_model__` parameter

For example to list model fields you can:

```Python hl_lines="18"
--8<-- "../docs_src/models/docs003.py"
```

!!!tip
    Note how the primary key `id` field is optional as `Integer` primary key by default has `autoincrement` set to `True`.

!!!info
    For more options visit official [pydantic][pydantic] documentation.

### Sqlalchemy Table

To access auto created sqlalchemy table you can use `Model.__table__` parameter

For example to list table columns you can:

```Python hl_lines="18"
--8<-- "../docs_src/models/docs004.py"
```

!!!tip
    You can access table primary key name by `Course.__pkname__`

!!!info
    For more options visit official [sqlalchemy-metadata][sqlalchemy-metadata] documentation.

### Fields Definition

To access ormar `Fields` you can use `Model.__model_fields__` parameter

For example to list table model fields you can:

```Python hl_lines="18"
--8<-- "../docs_src/models/docs005.py"
```

[fields]: ./fields.md
[relations]: ./relations.md
[queries]: ./queries.md
[pydantic]: https://pydantic-docs.helpmanual.io/
[sqlalchemy-core]: https://docs.sqlalchemy.org/en/latest/core/
[sqlalchemy-metadata]: https://docs.sqlalchemy.org/en/13/core/metadata.html
[databases]: https://github.com/encode/databases
[sqlalchemy connection string]: https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls