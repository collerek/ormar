# Queries

## QuerySet

Each Model is auto registered with a `QuerySet` that represents the underlaying query and it's options.

Most of the methods are also available through many to many relation interface.

!!!info
    To see which one are supported and how to construct relations visit [relations][relations].

Given the Models like this

```Python 
--8<-- "../docs_src/queries/docs001.py"
```

we can demonstrate available methods to fetch and save the data into the database.


### create

`create(**kwargs): -> Model` 

Creates the model instance, saves it in a database and returns the updates model 
(with pk populated if not passed and autoincrement is set).

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

!!!tip
    Check other `Model` methods in [models][models]

### get

`get(**kwargs): -> Model` 

Get's the first row from the db meeting the criteria set by kwargs.

If no criteria set it will return the first row in db.

Passing a criteria is actually calling filter(**kwargs) method described below.

```python
track = await Track.objects.get(name='The Bird')
# note that above is equivalent to await Track.objects.filter(name='The Bird').get()
track2 = track = await Track.objects.get()
track == track2 # True since it's the only row in db in our example
```

!!!warning
    If no row meets the criteria `NoMatch` exception is raised.
    
    If there are multiple rows meeting the criteria the `MultipleMatches` exception is raised.

### get_or_create

`get_or_create(**kwargs) -> Model`

Combination of create and get methods.

Tries to get a row meeting the criteria and if `NoMatch` exception is raised it creates a new one with given kwargs.

```python
album = await Album.objects.get_or_create(name='The Cat')
# object is created as it does not exist
album2 = await Album.objects.get_or_create(name='The Cat')
assert album == album2
# return True as the same db row is returned
```

!!!warning
    Despite being a equivalent row from database the `album` and `album2` in example above are 2 different python objects!
    Updating one of them will not refresh the second one until you excplicitly load() the fresh data from db.

!!!note
    Note that if you want to create a new object you either have to pass pk column value or pk column has to be set as autoincrement

### update

`update(each: bool = False, **kwargs) -> int`

QuerySet level update is used to update multiple records with the same value at once.

You either have to filter the QuerySet first or provide a `each=True` flag to update whole table.

If you do not provide this flag or a filter a `QueryDefinitionError` will be raised.

Return number of rows updated.

```Python hl_lines="26-28"
--8<-- "../docs_src/queries/docs002.py"
```

!!!warning
    Queryset needs to be filtered before updating to prevent accidental overwrite.
    
    To update whole database table `each=True` needs to be provided as a safety switch
    

### update_or_create

`update_or_create(**kwargs) -> Model`

Updates the model, or in case there is no match in database creates a new one.

```Python hl_lines="26-32"
--8<-- "../docs_src/queries/docs003.py"
```

!!!note
    Note that if you want to create a new object you either have to pass pk column value or pk column has to be set as autoincrement


### bulk_create

`bulk_create(objects: List["Model"]) -> None`

Allows you to create multiple objects at once.

A valid list of `Model` objects needs to be passed.

```python hl_lines="21-27"
--8<-- "../docs_src/queries/docs004.py"
```

### bulk_update

`bulk_update(objects: List["Model"], columns: List[str] = None) -> None`

Allows to update multiple instance at once.

All `Models` passed need to have primary key column populated.

You can also select which fields to update by passing `columns` list as a list of string names.

```python hl_lines="8"
# continuing the example from bulk_create
# update objects
for todo in todoes:
    todo.completed = False

# perform update of all objects at once
# objects need to have pk column set, otherwise exception is raised
await ToDo.objects.bulk_update(todoes)

completed = await ToDo.objects.filter(completed=False).all()
assert len(completed) == 3
```

### delete

`delete(each: bool = False, **kwargs) -> int`

QuerySet level delete is used to delete multiple records at once.

You either have to filter the QuerySet first or provide a `each=True` flag to delete whole table.

If you do not provide this flag or a filter a `QueryDefinitionError` will be raised.

Return number of rows deleted.

```python hl_lines="26-30"
--8<-- "../docs_src/queries/docs005.py"
```

### all

`all(self, **kwargs) -> List[Optional["Model"]]`

Returns all rows from a database for given model for set filter options.

Passing kwargs is a shortcut and equals to calling `filter(**kwrags).all()`.

If there are no rows meeting the criteria an empty list is returned.

```python
tracks = await Track.objects.select_related("album").all(title='Sample')
# will return a list of all Tracks with title Sample

tracks = await Track.objects.all()
# will return a list of all Tracks in database

```

### filter

`filter(**kwargs) -> QuerySet`

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
*  startswith - like `album__name__startswith='Mal'` (exact start match)
*  istartswith - like `album__name__istartswith='mal'` (exact start match case insensitive)
*  endswith - like `album__name__endswith='ibu'` (exact end match)
*  iendswith - like `album__name__iendswith='IBU'` (exact end match case insensitive)

!!!note
    All methods that do not return the rows explicitly returns a QueySet instance so you can chain them together
    
    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

### exclude

`exclude(**kwargs) -> QuerySet`

Works exactly the same as filter and all modifiers (suffixes) are the same, but returns a not condition.

So if you use `filter(name='John')` which equals to `where name = 'John'` in SQL, 
the `exclude(name='John')` equals to `where name <> 'John'`

Note that all conditions are joined so if you pass multiple values it becomes a union of conditions.

`exclude(name='John', age>=35)` will become `where not (name='John' and age>=35)`

```python
notes = await Track.objects.exclude(position_gt=3).all()
# returns all tracks with position < 3
```

### select_related

`select_related(related: Union[List, str]) -> QuerySet`

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

Exactly the same behavior is for Many2Many fields, where you put the names of Many2Many fields and the final `Models` are fetched for you.

!!!warning
    If you set `ForeignKey` field as not nullable (so required) during 
    all queries the not nullable `Models` will be auto prefetched, even if you do not include them in select_related.

!!!note
    All methods that do not return the rows explicitly returns a QueySet instance so you can chain them together
    
    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`


### limit

`limit(limit_count: int) -> QuerySet`

You can limit the results to desired number of rows.

```python
tracks = await Track.objects.limit(1).all()
# will return just one Track
```

!!!note
    All methods that do not return the rows explicitly returns a QueySet instance so you can chain them together
    
    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

### offset

`offset(offset: int) -> QuerySet`

You can also offset the results by desired number of rows.

```python
tracks = await Track.objects.offset(1).limit(1).all()
# will return just one Track, but this time the second one
```

!!!note
    All methods that do not return the rows explicitly returns a QueySet instance so you can chain them together
    
    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`


### count

`count() -> int`

Returns number of rows matching the given criteria (applied with `filter` and `exclude`)

```python
# returns count of rows in db
no_of_books = await Book.objects.count()
```

### exists

`exists() -> bool`

Returns a bool value to confirm if there are rows matching the given criteria (applied with `filter` and `exclude`)

```python
# returns a boolean value if given row exists
has_sample = await Book.objects.filter(title='Sample').exists()
```

### fields

`fields(columns: Union[List, str]) -> QuerySet`

With `fields()` you can select subset of model columns to limit the data load.

```python hl_lines="47 59 60 66"
--8<-- "../docs_src/queries/docs006.py"
```

!!!warning
    Mandatory fields cannot be excluded as it will raise `ValidationError`, to exclude a field it has to be nullable.

!!!tip
    Pk column cannot be excluded - it's always auto added even if not explicitly included.


!!!note
    All methods that do not return the rows explicitly returns a QueySet instance so you can chain them together
    
    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

[models]: ./models.md
[relations]: ./relations.md