# Aggregation functions

Currently 2 aggregation functions are supported.


* `count() -> int`
* `exists() -> bool`


* `QuerysetProxy`
    * `QuerysetProxy.count()` method
    * `QuerysetProxy.exists()` method
  

## count

`count() -> int`

Returns number of rows matching the given criteria (i.e. applied with `filter` and `exclude`)

```python
class Book(ormar.Model):
    class Meta:
        tablename = "books"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    author: str = ormar.String(max_length=100)
    genre: str = ormar.String(
        max_length=100,
        default="Fiction",
        choices=["Fiction", "Adventure", "Historic", "Fantasy"],
    )
```

```python
# returns count of rows in db for Books model
no_of_books = await Book.objects.count()
```

## exists

`exists() -> bool`

Returns a bool value to confirm if there are rows matching the given criteria (applied with `filter` and `exclude`)

```python
class Book(ormar.Model):
    class Meta:
        tablename = "books"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    author: str = ormar.String(max_length=100)
    genre: str = ormar.String(
        max_length=100,
        default="Fiction",
        choices=["Fiction", "Adventure", "Historic", "Fantasy"],
    )
```

```python
# returns a boolean value if given row exists
has_sample = await Book.objects.filter(title='Sample').exists()
```

## QuerysetProxy methods

When access directly the related `ManyToMany` field as well as `ReverseForeignKey`
returns the list of related models.

But at the same time it exposes a subset of QuerySet API, so you can filter, create,
select related etc related models directly from parent model.

### count

Works exactly the same as [count](./#count) function above but allows you to select columns from related
objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section

### exists

Works exactly the same as [exists](./#exists) function above but allows you to select columns from related
objects from other side of the relation.

!!!tip 
    To read more about `QuerysetProxy` visit [querysetproxy][querysetproxy] section

