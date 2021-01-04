<a name="queryset.limit_query"></a>
# queryset.limit\_query

<a name="queryset.limit_query.LimitQuery"></a>
## LimitQuery Objects

```python
class LimitQuery()
```

Modifies the select query with limit clause.

<a name="queryset.limit_query.LimitQuery.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(limit_count: Optional[int]) -> None
```

<a name="queryset.limit_query.LimitQuery.apply"></a>
#### apply

```python
 | apply(expr: sqlalchemy.sql.select) -> sqlalchemy.sql.select
```

Applies the limit clause.

**Arguments**:

- `expr (sqlalchemy.sql.selectable.Select)`: query to modify

**Returns**:

`(sqlalchemy.sql.selectable.Select)`: modified query

