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

Allows to prefetch related models during the same query. 

**With `select_related` always only one query is run against the database**, meaning that one 
(sometimes complicated) join is generated and later nested models are processed in python.

To fetch related model use `ForeignKey` names.

To chain related `Models` relation use double underscores between names.

!!!note
    If you are coming from `django` note that `ormar` `select_related` differs -> in `django` you can `select_related`
    only singe relation types, while in `ormar` you can select related across `ForeignKey` relation, 
    reverse side of `ForeignKey` (so virtual auto generated keys) and `ManyToMany` fields (so all relations as of current version).

!!!note
    To control which model fields to select use `fields()` and `exclude_fields()` `QuerySet` methods.

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

### prefetch_related

`prefetch_related(related: Union[List, str]) -> QuerySet`

Allows to prefetch related models during query - but opposite to `select_related` each 
subsequent model is fetched in a separate database query. 

**With `prefetch_related` always one query per Model is run against the database**, 
meaning that you will have multiple queries executed one after another.

To fetch related model use `ForeignKey` names.

To chain related `Models` relation use double underscores between names.

!!!note
    To control which model fields to select use `fields()` and `exclude_fields()` `QuerySet` methods.

```python
album = await Album.objects.prefetch_related("tracks").all()
# will return album will all columns tracks
```

You can provide a string or a list of strings

```python
classes = await SchoolClass.objects.prefetch_related(
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

### select_related vs prefetch_related

Which should you use -> `select_related` or `prefetch_related`?

Well, it really depends on your data. The best answer is try yourself and see which one performs faster/better in your system constraints.

What to keep in mind:

#### Performance

**Number of queries**:
`select_related` always executes one query against the database, while `prefetch_related` executes multiple queries. 
Usually the query (I/O) operation is the slowest one but it does not have to be.

**Number of rows**:
Imagine that you have 10 000 object in one table A and each of those objects have 3 children in table B, 
and subsequently each object in table B has 2 children in table C. Something like this:

```
                     Model C
                   /
           Model B - Model C
         / 
Model A  - Model B - Model C
       \           \ 
        \            Model C
         \
           Model B - Model C
                   \ 
                     Model C
```

That means that `select_related` will always return 60 000 rows (10 000 * 3 * 2) later compacted to 10 000 models. 

How many rows will return `prefetch_related`?

Well, that depends, if each of models B and C is unique it will return 10 000 rows in first query, 30 000 rows 
(each of 3 children of A in table B are unique) in second query and 60 000 rows (each of 2 children of model B 
in table C are unique) in 3rd query. 

In this case `select_related` seems like a better choice, not only it will run one query comparing to 3 of 
`prefetch_related` but will also return 60 000 rows comparing to 100 000 of `prefetch_related` (10+30+60k).

But what if each Model A has exactly the same 3 models B and each models C has exactly same models C? `select_related`
will still return 60 000 rows, while `prefetch_related` will return 10 000 for model A, 3 rows for model B and 2 rows for Model C.
So in total 10 006 rows. Now depending on the structure of models (i.e. if it has long Text() fields etc.) `prefetch_related`
might be faster despite it needs to perform three separate queries instead of one. 

#### Memory

`ormar` is a mini ORM meaning that it does not keep a registry of already loaded models.
 
That means that in `select_related` example above you will always have 10 000 Models A, 30 000 Models B 
(even if the unique number of rows in db is 3 - processing of `select_related` spawns **new** child models for each parent model).
And 60 000 Models C. 

If the same Model B is shared by rows 1, 10, 100 etc. and you update one of those, the rest of rows
that share the same child will **not** be updated on the spot. 
If you persist your changes into the database the change **will be available only after reload 
(either each child separately or the whole query again)**. 
That means that `select_related` will use more memory as each child is instantiated as a new object - obviously using it's own space.

!!!note
    This might change in future versions if we decide to introduce caching.

!!!warning
    By default all children (or event the same models loaded 2+ times) are completely independent, distinct python objects, despite that they represent the same row in db.
    
    They will evaluate to True when compared, so in example above: 
    
    ```python
    # will return True if child1 of both rows is the same child db row 
    row1.child1 == row100.child1
    
    # same here:
    model1 = await Model.get(pk=1)
    model2 = await Model.get(pk=1) # same pk = same row in db
    # will return `True`
    model1 == model2
    ``` 
    
    but 
    
    ```python
    # will return False (note that id is a python `builtin` function not ormar one).
    id(row1.child1) == (ro100.child1)
    
    # from above - will also return False
    id(model1) == id(model2)
    ``` 


On the contrary - with `prefetch_related` each unique distinct child model is instantiated 
only once and the same child models is shared across all parent models. 
That means that in `prefetch_related` example above if there are 3 distinct models in table B and 2 in table C, 
there will be only 5 children nested models shared between all model A instances. That also means that if you update
any attribute it will be updated on all parents as they share the same child object.

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

`fields(columns: Union[List, str, set, dict]) -> QuerySet`

With `fields()` you can select subset of model columns to limit the data load.

!!!note
    Note that `fields()` and `exclude_fields()` works both for main models (on normal queries like `get`, `all` etc.) 
    as well as `select_related` and `prefetch_related` models (with nested notation).

Given a sample data like following:

```python
--8<-- "../docs_src/queries/docs006.py"
```

You can select specified fields by passing a `str, List[str], Set[str] or dict` with nested definition.

To include related models use notation `{related_name}__{column}[__{optional_next} etc.]`.

```python hl_lines="1"
all_cars = await Car.objects.select_related('manufacturer').fields(['id', 'name', 'manufacturer__name']).all()
for car in all_cars:
    # excluded columns will yield None
    assert all(getattr(car, x) is None for x in ['year', 'gearbox_type', 'gears', 'aircon_type'])
    # included column on related models will be available, pk column is always included
    # even if you do not include it in fields list
    assert car.manufacturer.name == 'Toyota'
    # also in the nested related models - you cannot exclude pk - it's always auto added
    assert car.manufacturer.founded is None
```

`fields()` can be called several times, building up the columns to select.

If you include related models into `select_related()` call but you won't specify columns for those models in fields 
- implies a list of all fields for those nested models.

```python hl_lines="1"
all_cars = await Car.objects.select_related('manufacturer').fields('id').fields(
    ['name']).all()
# all fiels from company model are selected
assert all_cars[0].manufacturer.name == 'Toyota'
assert all_cars[0].manufacturer.founded == 1937
```

!!!warning
    Mandatory fields cannot be excluded as it will raise `ValidationError`, to exclude a field it has to be nullable.

You cannot exclude mandatory model columns - `manufacturer__name` in this example.

```python
await Car.objects.select_related('manufacturer').fields(['id', 'name', 'manufacturer__founded']).all()
# will raise pydantic ValidationError as company.name is required
```

!!!tip
    Pk column cannot be excluded - it's always auto added even if not explicitly included.

You can also pass fields to include as dictionary or set.

To mark a field as included in a dictionary use it's name as key and ellipsis as value.

To traverse nested models use nested dictionaries.

To include fields at last level instead of nested dictionary a set can be used.

To include whole nested model specify model related field name and ellipsis.

Below you can see examples that are equivalent:

```python
--8<-- "../docs_src/queries/docs009.py"
```

!!!note
    All methods that do not return the rows explicitly returns a QueySet instance so you can chain them together
    
    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

### exclude_fields

`exclude_fields(columns: Union[List, str, set, dict]) -> QuerySet`

With `exclude_fields()` you can select subset of model columns that will be excluded to limit the data load.

It's the opposite of `fields()` method so check documentation above to see what options are available.

Especially check above how you can pass also nested dictionaries and sets as a mask to exclude fields from whole hierarchy.

!!!note
    Note that `fields()` and `exclude_fields()` works both for main models (on normal queries like `get`, `all` etc.) 
    as well as `select_related` and `prefetch_related` models (with nested notation).

Below you can find few simple examples:

```python hl_lines="47 48 60 61 67"
--8<-- "../docs_src/queries/docs008.py"
```

!!!warning
    Mandatory fields cannot be excluded as it will raise `ValidationError`, to exclude a field it has to be nullable.

!!!tip
    Pk column cannot be excluded - it's always auto added even if explicitly excluded.


!!!note
    All methods that do not return the rows explicitly returns a QueySet instance so you can chain them together
    
    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`


### order_by

`order_by(columns: Union[List, str]) -> QuerySet`

With `order_by()` you can order the results from database based on your choice of fields.

You can provide a string with field name or list of strings with different fields.

Ordering in sql will be applied in order of names you provide in order_by.

!!!tip
    By default if you do not provide ordering `ormar` explicitly orders by all primary keys
    
!!!warning
    If you are sorting by nested models that causes that the result rows are unsorted by the main model
    `ormar` will combine those children rows into one main model.
    
    Sample raw database rows result (sort by child model desc):
    ```
    MODEL: 1 - Child Model - 3
    MODEL: 2 - Child Model - 2
    MODEL: 1 - Child Model - 1
    ```
    
    will result in 2 rows of result:
    ```
    MODEL: 1 - Child Models: [3, 1] # encountered first in result, all children rows combined
    MODEL: 2 - Child Modles: [2]
    ```
    
    The main model will never duplicate in the result

Given sample Models like following:
    
```python
--8<-- "../docs_src/queries/docs007.py"
```

To order by main model field just provide a field name

```python
toys = await Toy.objects.select_related("owner").order_by("name").all()
assert [x.name.replace("Toy ", "") for x in toys] == [
    str(x + 1) for x in range(6)
]
assert toys[0].owner == zeus
assert toys[1].owner == aphrodite
```

To sort on nested models separate field names with dunder '__'.

You can sort this way across all relation types -> `ForeignKey`, reverse virtual FK and `ManyToMany` fields.

```python
toys = await Toy.objects.select_related("owner").order_by("owner__name").all()
assert toys[0].owner.name == toys[1].owner.name == "Aphrodite"
assert toys[2].owner.name == toys[3].owner.name == "Hermes"
assert toys[4].owner.name == toys[5].owner.name == "Zeus"
```

To sort in descending order provide a hyphen in front of the field name

```python
owner = (
    await Owner.objects.select_related("toys")
        .order_by("-toys__name")
        .filter(name="Zeus")
        .get()
)
assert owner.toys[0].name == "Toy 4"
assert owner.toys[1].name == "Toy 1"
```

!!!note
    All methods that do not return the rows explicitly returns a QueySet instance so you can chain them together
    
    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`


[models]: ./models.md
[relations]: ./relations.md