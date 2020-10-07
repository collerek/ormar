# Queries

## QuerySet

Each Model is auto registered with a QuerySet that represents the underlaying query and it's options.

Most of the methods are also available through many to many relation interface.

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

```python hl_lines="24-28"
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()

class Book(ormar.Model):
    class Meta:
        tablename = "books"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    title: ormar.String(max_length=200)
    author: ormar.String(max_length=100)
    genre: ormar.String(max_length=100, default='Fiction', choices=['Fiction', 'Adventure', 'Historic', 'Fantasy'])

await Book.objects.create(title='Tom Sawyer', author="Twain, Mark", genre='Adventure')
await Book.objects.create(title='War and Peace', author="Tolstoy, Leo", genre='Fiction')
await Book.objects.create(title='Anna Karenina', author="Tolstoy, Leo", genre='Fiction')


# queryset needs to be filtered before deleting to prevent accidental overwrite
# to update whole database table each=True needs to be provided as a safety switch
await Book.objects.update(each=True, genre='Fiction')
all_books = await Book.objects.filter(genre='Fiction').all()
assert len(all_books) == 3
```

### update_or_create

`update_or_create(**kwargs) -> Model`

### bulk_create

`bulk_create(objects: List["Model"]) -> None`

Allows you to create multiple objects at once.

A valid list of `Model` objects needs to be passed.

```python hl_lines="20-26"
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()


class ToDo(ormar.Model):
    class Meta:
        tablename = "todos"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    text: ormar.String(max_length=500)
    completed: ormar.Boolean(default=False)

# create multiple instances at once with bulk_create
await ToDo.objects.bulk_create(
            [
                ToDo(text="Buy the groceries."),
                ToDo(text="Call Mum.", completed=True),
                ToDo(text="Send invoices.", completed=True),
            ]
        )

todoes = await ToDo.objects.all()
assert len(todoes) == 3
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

```python hl_lines="23-27"
import databases
import ormar
import sqlalchemy

database = databases.Database("sqlite:///db.sqlite")
metadata = sqlalchemy.MetaData()

class Book(ormar.Model):
    class Meta:
        tablename = "books"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    title: ormar.String(max_length=200)
    author: ormar.String(max_length=100)
    genre: ormar.String(max_length=100, default='Fiction', choices=['Fiction', 'Adventure', 'Historic', 'Fantasy'])

await Book.objects.create(title='Tom Sawyer', author="Twain, Mark", genre='Adventure')
await Book.objects.create(title='War and Peace in Space', author="Tolstoy, Leo", genre='Fantasy')
await Book.objects.create(title='Anna Karenina', author="Tolstoy, Leo", genre='Fiction')

# delete accepts kwargs that will be used in filter
# acting in same way as queryset.filter(**kwargs).delete()
await Book.objects.delete(genre='Fantasy') # delete all fantasy books
all_books = await Book.objects.all()
assert len(all_books) == 2
```

### all

Returns all rows from a database for given model

```python
tracks = await Track.objects.select_related("album").all()
# will return a list of all Tracks
```

### filter

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

### exclude

### select_related

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

### limit

You can limit the results to desired number of rows.

```python
tracks = await Track.objects.limit(1).all()
# will return just one Track
```

!!!note
    `filter()`, `select_related()`, `limit()` and `offset()` returns a QueySet instance so you can chain them together.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

### offset

You can also offset the results by desired number of rows.

```python
tracks = await Track.objects.offset(1).limit(1).all()
# will return just one Track, but this time the second one
```

### count


### exists

### fields



!!!note
    `filter()`, `select_related()`, `limit()` and `offset()` returns a QueySet instance so you can chain them together.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`
    
[models]: ./models.md