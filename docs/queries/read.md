# Read/ Load data from database

*  `get(**kwargs): -> Model`
*  `get_or_create(**kwargs) -> Model`
*  `first(): -> Model`
*  `all(**kwargs) -> List[Optional[Model]]`
*  `Model.load() method`

## get

`get(**kwargs): -> Model`

Get's the first row from the db meeting the criteria set by kwargs.

If no criteria set it will return the last row in db sorted by pk.

Passing a criteria is actually calling filter(**kwargs) method described below.

```python
track = await Track.objects.get(name='The Bird')
# note that above is equivalent to await Track.objects.filter(name='The Bird').get()
track2 = track = await Track.objects.get()
track == track2  # True since it's the only row in db in our example
```

!!!warning If no row meets the criteria `NoMatch` exception is raised.

    If there are multiple rows meeting the criteria the `MultipleMatches` exception is raised.

## get_or_create

`get_or_create(**kwargs) -> Model`

Combination of create and get methods.

Tries to get a row meeting the criteria and if `NoMatch` exception is raised it creates
a new one with given kwargs.

```python
album = await Album.objects.get_or_create(name='The Cat')
# object is created as it does not exist
album2 = await Album.objects.get_or_create(name='The Cat')
assert album == album2
# return True as the same db row is returned
```

!!!warning Despite being a equivalent row from database the `album` and `album2` in
example above are 2 different python objects!
Updating one of them will not refresh the second one until you excplicitly load() the
fresh data from db.

!!!note Note that if you want to create a new object you either have to pass pk column
value or pk column has to be set as autoincrement

## first

`first(): -> Model`

Gets the first row from the db ordered by primary key column ascending.

## all

`all(**kwargs) -> List[Optional["Model"]]`

Returns all rows from a database for given model for set filter options.

Passing kwargs is a shortcut and equals to calling `filter(**kwrags).all()`.

If there are no rows meeting the criteria an empty list is returned.

```python
tracks = await Track.objects.select_related("album").all(title='Sample')
# will return a list of all Tracks with title Sample

tracks = await Track.objects.all()
# will return a list of all Tracks in database

```

## Model method
