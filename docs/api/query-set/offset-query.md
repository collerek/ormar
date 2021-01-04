<a name="queryset.offset_query"></a>
# queryset.offset\_query

<a name="queryset.offset_query.OffsetQuery"></a>
## OffsetQuery Objects

```python
class OffsetQuery()
```

Modifies the select query with offset if set

<a name="queryset.offset_query.OffsetQuery.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(query_offset: Optional[int]) -> None
```

<a name="queryset.offset_query.OffsetQuery.apply"></a>
#### apply

```python
 | apply(expr: sqlalchemy.sql.select) -> sqlalchemy.sql.select
```

Applies the offset clause.

**Arguments**:

- `expr (sqlalchemy.sql.selectable.Select)`: query to modify

**Returns**:

`(sqlalchemy.sql.selectable.Select)`: modified query

