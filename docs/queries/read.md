# Read data from database

Following methods allow you to load data from the database.

* `get(**kwargs) -> Model`
* `get_or_create(**kwargs) -> Model`
* `first() -> Model`
* `all(**kwargs) -> List[Optional[Model]]`


* `Model`
    * `Model.load()` method


* `QuerysetProxy`
    * `QuerysetProxy.get(**kwargs)` method
    * `QuerysetProxy.get_or_create(**kwargs)` method
    * `QuerysetProxy.first()` method
    * `QuerysetProxy.all(**kwargs)` method

## get

`get(**kwargs) -> Model`

Get's the first row from the db meeting the criteria set by kwargs.

If no criteria set it will return the last row in db sorted by pk column.

Passing a criteria is actually calling filter(**kwargs) method described below.

```python
class Track(ormar.Model):
    class Meta:
        tablename = "track"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    name: str = ormar.String(max_length=100)
    position: int = ormar.Integer()
```

```python
track = await Track.objects.get(name='The Bird')
# note that above is equivalent to await Track.objects.filter(name='The Bird').get()
track2 = track = await Track.objects.get()
track == track2
# True since it's the only row in db in our example
# and get without arguments return first row by pk column desc 
```

!!!warning 
    If no row meets the criteria `NoMatch` exception is raised.

    If there are multiple rows meeting the criteria the `MultipleMatches` exception is raised.

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
    Despite being an equivalent row from database the `album` and `album2` in
    example above are 2 different python objects!
    Updating one of them will not refresh the second one until you excplicitly load() the
    fresh data from db.

!!!note 
    Note that if you want to create a new object you either have to pass pk column
    value or pk column has to be set as autoincrement

## first

`first() -> Model`

Gets the first row from the db ordered by primary key column ascending.

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
await Album.objects.create(name='The Cat')
await Album.objects.create(name='The Dog')
album = await Album.objects.first()
# first row by primary_key column asc
assert album.name == 'The Cat'
```

## all

`all(**kwargs) -> List[Optional["Model"]]`

Returns all rows from a database for given model for set filter options.

Passing kwargs is a shortcut and equals to calling `filter(**kwrags).all()`.

If there are no rows meeting the criteria an empty list is returned.

```python
class Album(ormar.Model):
    class Meta:
        tablename = "album"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Track(ormar.Model):
    class Meta:
        tablename = "track"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    title: str = ormar.String(max_length=100)
    position: int = ormar.Integer()
```

```python
tracks = await Track.objects.select_related("album").all(album__title='Sample')
# will return a list of all Tracks for album Sample
# for more on joins visit joining and subqueries section

tracks = await Track.objects.all()
# will return a list of all Tracks in database

```

## Model methods

Each model instance have a set of methods to `save`, `update` or `load` itself.

### load

You can load the `ForeignKey` related model by calling `load()` method.

`load()` can be used to refresh the model from the database (if it was changed by some other process).

!!!tip
    Read more about `load()` method in [models methods](../models/methods.md#load)

## QuerysetProxy methods

When access directly the related `ManyToMany` field as well as `ReverseForeignKey`
returns the list of related models.

But at the same time it exposes subset of QuerySet API, so you can filter, create,
select related etc related models directly from parent model.

### get

Works exactly the same as [get](./#get) function above but allows you to fetch related
objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section

### get_or_create

Works exactly the same as [get_or_create](./#get_or_create) function above but allows
you to query or create related objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section

### first

Works exactly the same as [first](./#first) function above but allows you to query
related objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section

### all

Works exactly the same as [all](./#all) function above but allows you to query related
objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section


[querysetproxy]: ../relations/queryset-proxy.md