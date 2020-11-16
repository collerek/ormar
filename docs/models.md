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
id: int = ormar.Integer(primary_key=True, autoincrement=False)
```

### Fields names vs Column names

By default names of the fields will be used for both the underlying `pydantic` model and `sqlalchemy` table.

If for whatever reason you prefer to change the name in the database but keep the name in the model you can do this 
with specifying `name` parameter during Field declaration

Here you have a sample model with changed names
```Python hl_lines="16-19"
--8<-- "../docs_src/models/docs008.py"
```

Note that you can also change the ForeignKey column name
```Python hl_lines="21"
--8<-- "../docs_src/models/docs009.py"
```

But for now you cannot change the ManyToMany column names as they go through other Model anyway.
```Python hl_lines="28"
--8<-- "../docs_src/models/docs010.py"
```

### Type Hints & Legacy

Before version 0.4.0 `ormar` supported only one way of defining `Fields` on a `Model` using python type hints as pydantic.

```Python hl_lines="15-17"
--8<-- "../docs_src/models/docs011.py"
```

But that didn't play well with static type checkers like `mypy` and `pydantic` PyCharm plugin.

Therefore from version >=0.4.0 `ormar` switched to new notation.

```Python hl_lines="15-17"
--8<-- "../docs_src/models/docs001.py"
```

Note that type hints are **optional** so perfectly valid `ormar` code can look like this:

```Python hl_lines="15-17"
--8<-- "../docs_src/models/docs012.py"
```

!!!warning
    Even if you use type hints **`ormar` does not use them to construct `pydantic` fields!**
    
    Type hints are there only to support static checkers and linting, 
    `ormar` construct annotations used by `pydantic` from own fields.


### Database initialization/ migrations

Note that all examples assume that you already have a database.

If that is not the case and you need to create your tables, that's super easy as `ormar` is using sqlalchemy for underlying table construction.

All you have to do is call `create_all()` like in the example below.

```python
import sqlalchemy
# get your database url in sqlalchemy format - same as used with databases instance used in Model definition
engine = sqlalchemy.create_engine("sqlite:///test.db")
# note that this has to be the same metadata that is used in ormar Models definition
metadata.create_all(engine)
```

You can also create single tables, sqlalchemy tables are exposed in `ormar.Meta` class.

```python
import sqlalchemy
# get your database url in sqlalchemy format - same as used with databases instance used in Model definition
engine = sqlalchemy.create_engine("sqlite:///test.db")
# Artist is an ormar model from previous examples
Artist.Meta.table.create(engine)
```

!!!warning
    You need to create the tables only once, so use a python console for that or remove the script from your production code after first use.

Likewise as with tables, since we base tables on sqlalchemy for migrations please use [alembic][alembic].

Use command line to reproduce this minimalistic example.

```python
alembic init alembic
alembic revision --autogenerate -m "made some changes"
alembic upgrade head
```

!!!info
    You can read more about table creation, altering and migrations in [sqlalchemy table creation][sqlalchemy table creation] documentation.

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

#### Best practice

Only thing that `ormar` expects is a class with name `Meta` and two class variables: `metadata` and `databases`.

So instead of providing the same parameters over and over again for all models you should creata a class and subclass it in all models.

```Python hl_lines="14 20 33"
--8<-- "../docs_src/models/docs013.py"
```

!!!warning
    You need to subclass your `MainMeta` class in each `Model` class as those classes store configuration variables 
    that otherwise would be overwritten by each `Model`.

### Table Names

By default table name is created from Model class name as lowercase name plus 's'.

You can overwrite this parameter by providing `Meta` class `tablename` argument.

```Python hl_lines="12 13 14"
--8<-- "../docs_src/models/docs002.py"
```

### Constraints

On a model level you can also set model-wise constraints on sql columns.

Right now only `UniqueColumns` constraint is present. 

!!!tip
    To read more about columns constraints like `primary_key`, `unique`, `ForeignKey` etc. visit [fields][fields].

You can set this parameter by providing `Meta` class `constraints` argument.

```Python hl_lines="14-17"
--8<-- "../docs_src/models/docs006.py"
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

For creating multiple objects at once a `bulk_create()` QuerySet's method is available.

Each model has a `QuerySet` initialised as `objects` parameter 

```Python hl_lines="23"
--8<-- "../docs_src/models/docs007.py"
```

!!!info
    To read more about `QuerySets` (including bulk operations) and available methods visit [queries][queries]

## `Model` save status

Each model instance is a separate python object and they do not know anything about each other.

```python
track1 = await Track.objects.get(name='The Bird')
track2 = await Track.objects.get(name='The Bird')
assert track1 == track2 # True

track1.name = 'The Bird2'
await track1.save()
assert track1.name == track2.name # False
# track2 does not update and knows nothing about track1
```

The objects itself have a saved status, which is set as following:

*  Model is saved after `save/update/load/upsert` method on model
*  Model is saved after `create/get/first/all/get_or_create/update_or_create` method
*  Model is saved when passed to `bulk_update` and `bulk_create`
*  Model is saved after `adding/removing` `ManyToMany` related objects (through model instance auto saved/deleted)
*  Model is **not** saved after change of any own field (including `pk` as `Model.pk` alias)
*  Model is **not** saved after adding/removing `ForeignKey` related object (fk column not saved)
*  Model is **not** saved after instantiation with `__init__` (w/o `QuerySet.create` or before calling `save`)

You can check if model is saved with `ModelInstance.saved` property

## `Model` methods

### load

By default when you query a table without prefetching related models, the ormar will still construct
your related models, but populate them only with the pk value. You can load the related model by calling `load()` method.

`load()` can also be used to refresh the model from the database (if it was changed by some other process). 

```python
track = await Track.objects.get(name='The Bird')
track.album.pk # will return malibu album pk (1)
track.album.name # will return None

# you need to actually load the data first
await track.album.load()
track.album.name # will return 'Malibu'
```

### save

`save() -> self`

You can create new models by using `QuerySet.create()` method or by initializing your model as a normal pydantic model 
and later calling `save()` method.

`save()` can also be used to persist changes that you made to the model, but only if the primary key is not set or the model does not exist in database.

The `save()` method does not check if the model exists in db, so if it does you will get a integrity error from your selected db backend if trying to save model with already existing primary key. 

```python
track = Track(name='The Bird')
await track.save() # will persist the model in database

track = await Track.objects.get(name='The Bird')
await track.save() # will raise integrity error as pk is populated
```

### update

`update(**kwargs) -> self`

You can update models by using `QuerySet.update()` method or by updating your model attributes (fields) and calling `update()` method.

If you try to update a model without a primary key set a `ModelPersistenceError` exception will be thrown.

To persist a newly created model use `save()` or `upsert(**kwargs)` methods.

```python
track = await Track.objects.get(name='The Bird')
await track.update(name='The Bird Strikes Again')
```

### upsert

`upsert(**kwargs) -> self`

It's an proxy to either `save()` or `update(**kwargs)` methods described above.

If the primary key is set -> the `update` method will be called.

If the pk is not set the `save()` method will be called.

```python
track = Track(name='The Bird')
await track.upsert() # will call save as the pk is empty

track = await Track.objects.get(name='The Bird')
await track.upsert(name='The Bird Strikes Again') # will call update as pk is already populated
```


### delete

You can delete models by using `QuerySet.delete()` method or by using your model and calling `delete()` method.

```python
track = await Track.objects.get(name='The Bird')
await track.delete() # will delete the model from database
```

!!!tip
    Note that that `track` object stays the same, only record in the database is removed.

### save_related

`save_related(follow: bool = False) -> None`

Method goes through all relations of the `Model` on which the method is called, 
and calls `upsert()` method on each model that is **not** saved. 

To understand when a model is saved check [save status][save status] section above.

By default the `save_related` method saved only models that are directly related (one step away) to the model on which the method is called.

But you can specify the `follow=True` parameter to traverse through nested models and save all of them in the relation tree.

!!!warning
    To avoid circular updates with `follow=True` set, `save_related` keeps a set of already visited Models, 
    and won't perform nested `save_related` on Models that were already visited.
    
    So if you have a diamond or circular relations types you need to perform the updates in a manual way.
    
    ```python
    # in example like this the second Street (coming from City) won't be save_related, so ZipCode won't be updated
    Street -> District -> City -> Street -> ZipCode
    ```

## Internals

Apart from special parameters defined in the `Model` during definition (tablename, metadata etc.) the `Model` provides you with useful internals.

### Pydantic Model

All `Model` classes inherit from `pydantic.BaseModel` so you can access all normal attributes of pydantic models.

For example to list pydantic model fields you can:

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
    You can access table primary key name by `Course.Meta.pkname`

!!!info
    For more options visit official [sqlalchemy-metadata][sqlalchemy-metadata] documentation.

### Fields Definition

To access ormar `Fields` you can use `Model.Meta.model_fields` parameter

For example to list table model fields you can:

```Python hl_lines="20"
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
[sqlalchemy table creation]: https://docs.sqlalchemy.org/en/13/core/metadata.html#creating-and-dropping-database-tables
[alembic]: https://alembic.sqlalchemy.org/en/latest/tutorial.html
[save status]:  ../models/#model-save-status
