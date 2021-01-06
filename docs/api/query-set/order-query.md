<a name="queryset.order_query"></a>
# queryset.order\_query

<a name="queryset.order_query.OrderQuery"></a>
## OrderQuery Objects

```python
class OrderQuery()
```

Modifies the select query with given list of order_by clauses.

<a name="queryset.order_query.OrderQuery.apply"></a>
#### apply

```python
 | apply(expr: sqlalchemy.sql.select) -> sqlalchemy.sql.select
```

Applies all order_by clauses if set.

**Arguments**:

- `expr (sqlalchemy.sql.selectable.Select)`: query to modify

**Returns**:

`(sqlalchemy.sql.selectable.Select)`: modified query

