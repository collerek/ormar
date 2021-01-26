# Filtering and sorting data

*  `filter(**kwargs) -> QuerySet`
*  `exclude(**kwargs) -> QuerySet`
*  `order_by(columns:Union[List, str]) -> QuerySet`

## filter

`filter(**kwargs) -> QuerySet`

Allows you to filter by any `Model` attribute/field as well as to fetch instances, with
a filter across an FK relationship.

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

!!!note All methods that do not return the rows explicitly returns a QueySet instance so
you can chain them together

    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

!!!warning Note that you do not have to specify the `%` wildcard in contains and other
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
notes = await Track.objects.exclude(position_gt=3).all()
# returns all tracks with position < 3
```

### order_by

`order_by(columns: Union[List, str]) -> QuerySet`

With `order_by()` you can order the results from database based on your choice of
fields.

You can provide a string with field name or list of strings with different fields.

Ordering in sql will be applied in order of names you provide in order_by.

!!!tip By default if you do not provide ordering `ormar` explicitly orders by all
primary keys

!!!warning If you are sorting by nested models that causes that the result rows are
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
--8 < -- "../docs_src/queries/docs007.py"
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

!!!note All methods that do not return the rows explicitly returns a QueySet instance so
you can chain them together

    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

