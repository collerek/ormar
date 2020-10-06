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

```Python hl_lines="15 16 17"
--8<-- "../docs_src/models/docs001.py"
```

!!! warning 
    Not assigning `primary_key` column or assigning more than one column per `Model` will raise `ModelDefinitionError`
    exception.

By default if you assign primary key to `Integer` field, the `autoincrement` option is set to true.

You can disable by passing `autoincremant=False`.

```Python 
id: ormar.Integer(primary_key=True, autoincrement=False)
```

Names of the fields will be used for both the underlying `pydantic` model and `sqlalchemy` table.

### Dependencies

Since ormar depends on [`databases`][databases] and [`sqlalchemy-core`][sqlalchemy-core] for database connection 
and table creation you need to assign each `Model` with two special parameters.

#### Databases

One is `Database` instance created with your database url in [sqlalchemy connection string][sqlalchemy connection string] format.

Created instance needs to be passed to every `Model` with `Meta` class `database` parameter.

```Python hl_lines="1 6 12"
--8<-- "../docs_src/models/docs001.py"
```

!!! tip
    You need to create the `Database` instance **only once** and use it for all models. 
    You can create several ones if you want to use multiple databases.

#### Sqlalchemy

Second dependency is sqlalchemy `MetaData` instance.

Created instance needs to be passed to every `Model` with `Meta` class `metadata` parameter.

```Python hl_lines="2 7 13"
--8<-- "../docs_src/models/docs001.py"
```

!!! tip
    You need to create the `MetaData` instance **only once** and use it for all models. 
    You can create several ones if you want to use multiple databases.

### Table Names

By default table name is created from Model class name as lowercase name plus 's'.

You can overwrite this parameter by providing `Meta` class `tablename` argument.

```Python hl_lines="12 13 14"
--8<-- "../docs_src/models/docs002.py"
```

## Initialization

There are two ways to create and persist the `Model` instance in the database.

!!!tip 
    Use `ipython` to try this from the console, since it supports `await`.

If you plan to modify the instance in the later execution of your program you can initiate your `Model` as a normal class and later await a `save()` call.  

```Python hl_lines="20 21"
--8<-- "../docs_src/models/docs007.py"
```

If you want to initiate your `Model` and at the same time save in in the database use a QuerySet's method `create()`.

Each model has a `QuerySet` initialised as `objects` parameter 

```Python hl_lines="23"
--8<-- "../docs_src/models/docs007.py"
```

!!!info
    To read more about `QuerySets` and available methods visit [queries][queries]

## Internals

Apart from special parameters defined in the `Model` during definition (tablename, metadata etc.) the `Model` provides you with useful internals.

### Pydantic Model

All `Model` classes inherit from `pydantic.BaseModel` so you can access all normal attributes of pydantic models.

For example to list model fields you can:

```Python hl_lines="20"
--8<-- "../docs_src/models/docs003.py"
```

!!!tip
    Note how the primary key `id` field is optional as `Integer` primary key by default has `autoincrement` set to `True`.

!!!info
    For more options visit official [pydantic][pydantic] documentation.

### Sqlalchemy Table

To access auto created sqlalchemy table you can use `Model.Meta.table` parameter

For example to list table columns you can:

```Python hl_lines="20"
--8<-- "../docs_src/models/docs004.py"
```

!!!tip
    You can access table primary key name by `Course.__pkname__`

!!!info
    For more options visit official [sqlalchemy-metadata][sqlalchemy-metadata] documentation.

### Fields Definition

To access ormar `Fields` you can use `Model.Meta.model_fields` parameter

For example to list table model fields you can:

```Python hl_lines="19"
--8<-- "../docs_src/models/docs005.py"
```

!!!info
    Note that fields stored on a model are `classes` not `instances`.
    
    So if you print just model fields you will get:
    
    `{'id': <class 'ormar.fields.model_fields.Integer'>, `
    
      `'name': <class 'ormar.fields.model_fields.String'>, `
      
      `'completed': <class 'ormar.fields.model_fields.Boolean'>}`


[fields]: ./fields.md
[relations]: ./relations.md
[queries]: ./queries.md
[pydantic]: https://pydantic-docs.helpmanual.io/
[sqlalchemy-core]: https://docs.sqlalchemy.org/en/latest/core/
[sqlalchemy-metadata]: https://docs.sqlalchemy.org/en/13/core/metadata.html
[databases]: https://github.com/encode/databases
[sqlalchemy connection string]: https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls