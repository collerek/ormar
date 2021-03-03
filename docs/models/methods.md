# Model methods

!!!tip
    Main interaction with the databases is exposed through a `QuerySet` object exposed on 
    each model as `Model.objects` similar to the django orm.

    To read more about **quering, joining tables, excluding fields etc. visit [queries][queries] section.**

Each model instance have a set of methods to `save`, `update` or `load` itself.

Available methods are described below.

## load

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

## load_all

`load_all(follow: bool = False, exclude: Union[List, str, Set, Dict] = None) -> Model`

Method works like `load()` but also goes through all relations of the `Model` on which the method is called, 
and reloads them from database.

By default the `load_all` method loads only models that are directly related (one step away) to the model on which the method is called.

But you can specify the `follow=True` parameter to traverse through nested models and load all of them in the relation tree.

!!!warning
    To avoid circular updates with `follow=True` set, `load_all` keeps a set of already visited Models, 
    and won't perform nested `loads` on Models that were already visited.
    
    So if you have a diamond or circular relations types you need to perform the loads in a manual way.
    
    ```python
    # in example like this the second Street (coming from City) won't be load_all, so ZipCode won't be reloaded
    Street -> District -> City -> Street -> ZipCode
    ```

Method accepts also optional exclude parameter that works exactly the same as exclude_fields method in `QuerySet`.
That way you can remove fields from related models being refreshed or skip whole related models.

Method performs one database query so it's more efficient than nested calls to `load()` and `all()` on related models.

!!!tip
    To read more about `exclude` read [exclude_fields][exclude_fields]

!!!warning
    All relations are cleared on `load_all()`, so if you exclude some nested models they will be empty after call.

## save

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

## update

`update(**kwargs) -> self`

You can update models by using `QuerySet.update()` method or by updating your model attributes (fields) and calling `update()` method.

If you try to update a model without a primary key set a `ModelPersistenceError` exception will be thrown.

To persist a newly created model use `save()` or `upsert(**kwargs)` methods.

```python
track = await Track.objects.get(name='The Bird')
await track.update(name='The Bird Strikes Again')
```

## upsert

`upsert(**kwargs) -> self`

It's a proxy to either `save()` or `update(**kwargs)` methods described above.

If the primary key is set -> the `update` method will be called.

If the pk is not set the `save()` method will be called.

```python
track = Track(name='The Bird')
await track.upsert() # will call save as the pk is empty

track = await Track.objects.get(name='The Bird')
await track.upsert(name='The Bird Strikes Again') # will call update as pk is already populated
```


## delete

You can delete models by using `QuerySet.delete()` method or by using your model and calling `delete()` method.

```python
track = await Track.objects.get(name='The Bird')
await track.delete() # will delete the model from database
```

!!!tip
    Note that that `track` object stays the same, only record in the database is removed.

## save_related

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

[fields]: ../fields.md
[relations]: ../relations/index.md
[queries]: ../queries/index.md
[pydantic]: https://pydantic-docs.helpmanual.io/
[sqlalchemy-core]: https://docs.sqlalchemy.org/en/latest/core/
[sqlalchemy-metadata]: https://docs.sqlalchemy.org/en/13/core/metadata.html
[databases]: https://github.com/encode/databases
[sqlalchemy connection string]: https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls
[sqlalchemy table creation]: https://docs.sqlalchemy.org/en/13/core/metadata.html#creating-and-dropping-database-tables
[alembic]: https://alembic.sqlalchemy.org/en/latest/tutorial.html
[save status]:  ../models/index/#model-save-status
[Internals]:  #internals
[exclude_fields]: ../queries/select-columns.md#exclude_fields
