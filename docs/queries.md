# Queries

## QuerySet

Each Model is auto registered with a QuerySet that represents the underlaying query and it's options.

Given the Models like this

```Python 
--8<-- "../docs_src/relations/docs001.py"
```

we can demonstrate available methods to fetch and save the data into the database.

### create(**kwargs)

Creates the model instance, saves it in a database and returns the updates model (with pk populated).
The allowed kwargs are `Model` fields names and proper value types. 

```python
malibu = await Album.objects.create(name="Malibu")
await Track.objects.create(album=malibu, title="The Bird", position=1)
```

The alternative is a split creation and persistence of the `Model`.
```python
malibu = Album(name="Malibu")
await malibu.save()
```

### load()

By default when you query a table without prefetching related models, the ormar will still construct
your related models, but populate them only with the pk value.

```python
track = await Track.objects.get(name='The Bird')
track.album.pk # will return malibu album pk (1)
track.album.name # will return None

# you need to actually load the data first
await track.album.load()
track.album.name # will return 'Malibu'
```

### get(**kwargs)

Get's the first row from the db meeting the criteria set by kwargs.

If no criteria set it will return the first row in db.

Passing a criteria is actually calling filter(**kwargs) method described below.

```python
track = await Track.objects.get(name='The Bird')
track2 = track = await Track.objects.get()
track == track2 # True since it's the only row in db
```

### all()

Returns all rows from a database for given model

```python
tracks = await Track.objects.select_related("album").all()
# will return a list of all Tracks
```

### filter(**kwargs)

Allows you to filter by any `Model` attribute/field 
as well as to fetch instances, with a filter across an FK relationship.

```python
track = Track.objects.filter(name="The Bird").get()
# will return a track with name equal to 'The Bird'
 
tracks = Track.objects.filter(album__name="Fantasies").all()
# will return all tracks where the columns album name = 'Fantasies'
```

You can use special filter suffix to change the filter operands:

*  exact - like `album__name__exact='Malibu'` (exact match)
*  iexact - like `album__name__iexact='malibu'` (exact match case insensitive)
*  contains - like `album__name__conatins='Mal'` (sql like)
*  icontains - like `album__name__icontains='mal'` (sql like case insensitive)
*  in - like `album__name__in=['Malibu', 'Barclay']` (sql in)
*  gt - like `position__gt=3` (sql >)
*  gte - like `position__gte=3` (sql >=)
*  lt - like `position__lt=3` (sql <)
*  lte - like `position__lte=3` (sql <=)

!!!note
    `filter()`, `select_related()`, `limit()` and `offset()` returns a QueySet instance so you can chain them together.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

### select_related(*args)

Allows to prefetch related models. 

To fetch related model use `ForeignKey` names.

To chain related `Models` relation use double underscore.

```python
album = await Album.objects.select_related("tracks").all()
# will return album will all columns tracks
```

You can provide a string or a list of strings

```python
classes = await SchoolClass.objects.select_related(
["teachers__category", "students"]).all()
# will return classes with teachers and teachers categories
# as well as classes students
```

!!!warning
    If you set `ForeignKey` field as not nullable (so required) during 
    all queries the not nullable `Models` will be auto prefetched, even if you do not include them in select_related.

!!!note
    `filter()`, `select_related()`, `limit()` and `offset()` returns a QueySet instance so you can chain them together.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

### limit(int)

You can limit the results to desired number of rows.

```python
tracks = await Track.objects.limit(1).all()
# will return just one Track
```

!!!note
    `filter()`, `select_related()`, `limit()` and `offset()` returns a QueySet instance so you can chain them together.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

### offset(int)

You can also offset the results by desired number of rows.

```python
tracks = await Track.objects.offset(1).limit(1).all()
# will return just one Track, but this time the second one
```

!!!note
    `filter()`, `select_related()`, `limit()` and `offset()` returns a QueySet instance so you can chain them together.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`