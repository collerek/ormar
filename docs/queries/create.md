# Insert data into database

Following methods allow you to insert data into the database.

* `create(**kwargs) -> Model`
* `get_or_create(**kwargs) -> Model`
* `update_or_create(**kwargs) -> Model`
* `bulk_create(objects: List[Model]) -> None`


* `Model`
      * `Model.save()` method
      * `Model.upsert()` method
      * `Model.save_related()` method


* `QuerysetProxy`
      * `QuerysetProxy.create(**kwargs)` method
      * `QuerysetProxy.get_or_create(**kwargs)` method
      * `QuerysetProxy.update_or_create(**kwargs)` method

## create

`create(**kwargs): -> Model`

Creates the model instance, saves it in a database and returns the updates model
(with pk populated if not passed and autoincrement is set).

The allowed kwargs are `Model` fields names and proper value types.

```python
class Album(ormar.Model):
    class Meta:
        tablename = "album"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
```

```python
malibu = await Album.objects.create(name="Malibu")
await Track.objects.create(album=malibu, title="The Bird", position=1)
```

The alternative is a split creation and persistence of the `Model`.

```python
malibu = Album(name="Malibu")
await malibu.save()
```

!!!tip 
        Check other `Model` methods in [models][models]

## get_or_create

`get_or_create(**kwargs) -> Model`

Combination of create and get methods.

Tries to get a row meeting the criteria and if `NoMatch` exception is raised it creates
a new one with given kwargs.

```python
class Album(ormar.Model):
    class Meta:
        tablename = "album"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
```

```python
album = await Album.objects.get_or_create(name='The Cat')
# object is created as it does not exist
album2 = await Album.objects.get_or_create(name='The Cat')
assert album == album2
# return True as the same db row is returned
```

!!!warning 
    Despite being a equivalent row from database the `album` and `album2` in
    example above are 2 different python objects!
    Updating one of them will not refresh the second one until you excplicitly load() the
    fresh data from db.

!!!note 
    Note that if you want to create a new object you either have to pass pk column
    value or pk column has to be set as autoincrement

## update_or_create

`update_or_create(**kwargs) -> Model`

Updates the model, or in case there is no match in database creates a new one.

```Python hl_lines="26-32"
--8<-- "../docs_src/queries/docs003.py"
```

!!!note 
    Note that if you want to create a new object you either have to pass pk column
    value or pk column has to be set as autoincrement

## bulk_create

`bulk_create(objects: List["Model"]) -> None`

Allows you to create multiple objects at once.

A valid list of `Model` objects needs to be passed.

```python hl_lines="21-27"
--8<-- "../docs_src/queries/docs004.py"
```

## Model methods

Each model instance have a set of methods to `save`, `update` or `load` itself.

###save

You can create new models by using `QuerySet.create()` method or by initializing your model as a normal pydantic model 
and later calling `save()` method.

!!!tip
    Read more about `save()` method in [models-save][models-save]

###upsert

It's a proxy to either `save()` or `update(**kwargs)` methods of a Model.
If the pk is not set the `save()` method will be called.

!!!tip
    Read more about `upsert()` method in [models-upsert][models-upsert]

###save_related

Method goes through all relations of the `Model` on which the method is called, 
and calls `upsert()` method on each model that is **not** saved. 

!!!tip
    Read more about `save_related()` method in [models-save-related][models-save-related]

## QuerysetProxy methods

When access directly the related `ManyToMany` field as well as `ReverseForeignKey` returns the list of related models.

But at the same time it exposes subset of QuerySet API, so you can filter, create, select related etc related models directly from parent model.

### create

Works exactly the same as [create](./#create) function above but allows you to create related objects
from other side of the relation.

!!!tip
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section


### get_or_create

Works exactly the same as [get_or_create](./#get_or_create) function above but allows you to query or create related objects
from other side of the relation.

!!!tip
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section


### update_or_create

Works exactly the same as [update_or_create](./#update_or_create) function above but allows you to update or create related objects
from other side of the relation.

!!!tip
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section

[models]: ../models/methods.md
[models-save]: ../models/methods.md#save
[models-upsert]: ../models/methods.md#upsert
[models-save-related]: ../models/methods.md#save_related
[querysetproxy]: ../relations/queryset-proxy.md