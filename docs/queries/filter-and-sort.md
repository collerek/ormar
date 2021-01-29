# Filtering and sorting data

You can use following methods to filter the data (sql where clause).

* `filter(**kwargs) -> QuerySet`
* `exclude(**kwargs) -> QuerySet`
* `get(**kwargs) -> Model`
* `get_or_create(**kwargs) -> Model`
* `all(**kwargs) -> List[Optional[Model]]`


* `QuerysetProxy`
    * `QuerysetProxy.filter(**kwargs)` method
    * `QuerysetProxy.exclude(**kwargs)` method
    * `QuerysetProxy.get(**kwargs)` method
    * `QuerysetProxy.get_or_create(**kwargs)` method
    * `QuerysetProxy.all(**kwargs)` method

And following methods to sort the data (sql order by clause).

* `order_by(columns:Union[List, str]) -> QuerySet`
* `QuerysetProxy`
    * `QuerysetProxy.order_by(columns:Union[List, str])` method

## Filtering

### filter

`filter(**kwargs) -> QuerySet`

Allows you to filter by any `Model` attribute/field as well as to fetch instances, with
a filter across an FK relationship.

```python
class Album(ormar.Model):
    class Meta:
        tablename = "albums"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    is_best_seller: bool = ormar.Boolean(default=False)

class Track(ormar.Model):
    class Meta:
        tablename = "tracks"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    name: str = ormar.String(max_length=100)
    position: int = ormar.Integer()
    play_count: int = ormar.Integer(nullable=True)
```

```python
track = Track.objects.filter(name="The Bird").get()
# will return a track with name equal to 'The Bird'

tracks = Track.objects.filter(album__name="Fantasies").all()
# will return all tracks where the columns album name = 'Fantasies'
```

You can use special filter suffix to change the filter operands:

* exact - like `album__name__exact='Malibu'` (exact match)
* iexact - like `album__name__iexact='malibu'` (exact match case insensitive)
* contains - like `album__name__contains='Mal'` (sql like)
* icontains - like `album__name__icontains='mal'` (sql like case insensitive)
* in - like `album__name__in=['Malibu', 'Barclay']` (sql in)
* gt - like `position__gt=3` (sql >)
* gte - like `position__gte=3` (sql >=)
* lt - like `position__lt=3` (sql <)
* lte - like `position__lte=3` (sql <=)
* startswith - like `album__name__startswith='Mal'` (exact start match)
* istartswith - like `album__name__istartswith='mal'` (exact start match case
  insensitive)
* endswith - like `album__name__endswith='ibu'` (exact end match)
* iendswith - like `album__name__iendswith='IBU'` (exact end match case insensitive)

!!!note 
    All methods that do not return the rows explicitly returns a QueySet instance so
    you can chain them together

    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

!!!warning 
    Note that you do not have to specify the `%` wildcard in contains and other
    filters, it's added for you. If you include `%` in your search value it will be escaped
    and treated as literal percentage sign inside the text.

### exclude

`exclude(**kwargs) -> QuerySet`

Works exactly the same as filter and all modifiers (suffixes) are the same, but returns
a not condition.

So if you use `filter(name='John')` which equals to `where name = 'John'` in SQL,
the `exclude(name='John')` equals to `where name <> 'John'`

Note that all conditions are joined so if you pass multiple values it becomes a union of
conditions.

`exclude(name='John', age>=35)` will become `where not (name='John' and age>=35)`

```python
class Album(ormar.Model):
    class Meta:
        tablename = "albums"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    is_best_seller: bool = ormar.Boolean(default=False)

class Track(ormar.Model):
    class Meta:
        tablename = "tracks"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    album: Optional[Album] = ormar.ForeignKey(Album)
    name: str = ormar.String(max_length=100)
    position: int = ormar.Integer()
    play_count: int = ormar.Integer(nullable=True)
```

```python
notes = await Track.objects.exclude(position_gt=3).all()
# returns all tracks with position < 3
```

## get

`get(**kwargs) -> Model`

Get's the first row from the db meeting the criteria set by kwargs.

When any kwargs are passed it's a shortcut equivalent to calling `filter(**kwargs).get()`

!!!tip
    To read more about `filter` go to [filter](./#filter).
    
    To read more about `get` go to [read/get](../read/#get)

## get_or_create

`get_or_create(**kwargs) -> Model`

Combination of create and get methods.

When any kwargs are passed it's a shortcut equivalent to calling `filter(**kwargs).get_or_create()`

!!!tip
    To read more about `filter` go to [filter](./#filter).
    
    To read more about `get_or_create` go to [read/get_or_create](../read/#get_or_create)

!!!warning
    When given item does not exist you need to pass kwargs for all required fields of the
    model, including but not limited to primary_key column (unless it's autoincrement).

## all

`all(**kwargs) -> List[Optional["Model"]]`

Returns all rows from a database for given model for set filter options.

When any kwargs are passed it's a shortcut equivalent to calling `filter(**kwargs).all()`

!!!tip
    To read more about `filter` go to [filter](./#filter).
    
    To read more about `all` go to [read/all](../read/#all)

### QuerysetProxy methods

When access directly the related `ManyToMany` field as well as `ReverseForeignKey`
returns the list of related models.

But at the same time it exposes subset of QuerySet API, so you can filter, create,
select related etc related models directly from parent model.

#### filter

Works exactly the same as [filter](./#filter) function above but allows you to filter related
objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section


#### exclude

Works exactly the same as [exclude](./#exclude) function above but allows you to filter related
objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section


#### get

Works exactly the same as [get](./#get) function above but allows you to filter related
objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section

#### get_or_create

Works exactly the same as [get_or_create](./#get_or_create) function above but allows
you to filter related objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section

#### all

Works exactly the same as [all](./#all) function above but allows you to filter related
objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section

## Sorting

### order_by

`order_by(columns: Union[List, str]) -> QuerySet`

With `order_by()` you can order the results from database based on your choice of
fields.

You can provide a string with field name or list of strings with different fields.

Ordering in sql will be applied in order of names you provide in order_by.

!!!tip 
    By default if you do not provide ordering `ormar` explicitly orders by all
    primary keys

!!!warning 
    If you are sorting by nested models that causes that the result rows are
    unsorted by the main model
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
--8 < -- "../../docs_src/queries/docs007.py"
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

You can sort this way across all relation types -> `ForeignKey`, reverse virtual FK
and `ManyToMany` fields.

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
    All methods that do not return the rows explicitly returns a QueySet instance so
    you can chain them together

    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

### QuerysetProxy methods

When access directly the related `ManyToMany` field as well as `ReverseForeignKey`
returns the list of related models.

But at the same time it exposes subset of QuerySet API, so you can filter, create,
select related etc related models directly from parent model.

#### order_by

Works exactly the same as [order_by](./#order_by) function above but allows you to sort related
objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section


[querysetproxy]: ../relations/queryset-proxy.md