# Aggregation functions

`ormar` currently supports 2 aggregation functions:

*  `count() -> int`
*  `exists() -> bool`

## count

`count() -> int`

Returns number of rows matching the given criteria (i.e. applied with `filter` and `exclude`)

```python
# returns count of rows in db for Books model
no_of_books = await Book.objects.count()
```

## exists

`exists() -> bool`

Returns a bool value to confirm if there are rows matching the given criteria (applied with `filter` and `exclude`)

```python
# returns a boolean value if given row exists
has_sample = await Book.objects.filter(title='Sample').exists()
```
