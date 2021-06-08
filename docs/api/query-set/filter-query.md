<a name="queryset.filter_query"></a>
# queryset.filter\_query

<a name="queryset.filter_query.FilterQuery"></a>
## FilterQuery Objects

```python
class FilterQuery()
```

Modifies the select query with given list of where/filter clauses.

<a name="queryset.filter_query.FilterQuery.apply"></a>
#### apply

```python
 | apply(expr: sqlalchemy.sql.select) -> sqlalchemy.sql.select
```

Applies all filter clauses if set.

**Arguments**:

- `expr` (`sqlalchemy.sql.selectable.Select`): query to modify

**Returns**:

`sqlalchemy.sql.selectable.Select`: modified query

