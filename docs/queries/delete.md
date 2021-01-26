# Delete/ remove data from database

* `delete(each: bool = False, **kwargs) -> int`
* `Model.delete()` method

## delete

`delete(each: bool = False, **kwargs) -> int`

QuerySet level delete is used to delete multiple records at once.

You either have to filter the QuerySet first or provide a `each=True` flag to delete
whole table.

If you do not provide this flag or a filter a `QueryDefinitionError` will be raised.

Return number of rows deleted.

```python hl_lines="26-30"
--8<-- "../docs_src/queries/docs005.py"
```

## Model method