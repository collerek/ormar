#Pagination and rows number

*  `paginate(page: int) -> QuerySet`
*  `limit(limit_count: int) -> QuerySet`
*  `offset(offset: int) -> QuerySet`
*  `get(**kwargs): -> Model`
*  `first(): -> Model`


## paginate

`paginate(page: int, page_size: int = 20) -> QuerySet`

Combines the `offset` and `limit` methods based on page number and size

```python
tracks = await Track.objects.paginate(3).all()
# will return 20 tracks starting at row 41 
# (with default page size of 20)
```

Note that `paginate(2)` is equivalent to `offset(20).limit(20)`

## limit

`limit(limit_count: int, limit_raw_sql: bool = None) -> QuerySet`

You can limit the results to desired number of parent models.

To limit the actual number of database query rows instead of number of main models
use the `limit_raw_sql` parameter flag, and set it to `True`.

```python
tracks = await Track.objects.limit(1).all()
# will return just one Track
```

!!!note
    All methods that do not return the rows explicitly returns a QueySet instance so you can chain them together
    
    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`

## offset

`offset(offset: int, limit_raw_sql: bool = None) -> QuerySet`

You can also offset the results by desired number of main models.

To offset the actual number of database query rows instead of number of main models
use the `limit_raw_sql` parameter flag, and set it to `True`.

```python
tracks = await Track.objects.offset(1).limit(1).all()
# will return just one Track, but this time the second one
```

!!!note
    All methods that do not return the rows explicitly returns a QueySet instance so you can chain them together
    
    So operations like `filter()`, `select_related()`, `limit()` and `offset()` etc. can be chained.
    
    Something like `Track.object.select_related("album").filter(album__name="Malibu").offset(1).limit(1).all()`



## get

`get(**kwargs): -> Model` 

Get's the first row from the db meeting the criteria set by kwargs.

If no criteria set it will return the last row in db sorted by pk.

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

## first

`first(): -> Model` 

Gets the first row from the db ordered by primary key column ascending.
