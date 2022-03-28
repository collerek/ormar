<a name="queryset.queryset"></a>
# queryset.queryset

<a name="queryset.queryset.QuerySet"></a>
## QuerySet Objects

```python
class QuerySet(Generic[T])
```

Main class to perform database queries, exposed on each model as objects attribute.

<a name="queryset.queryset.QuerySet.model_meta"></a>
#### model\_meta

```python
 | @property
 | model_meta() -> "ModelMeta"
```

Shortcut to model class Meta set on QuerySet model.

**Returns**:

`model Meta class`: Meta class of the model

<a name="queryset.queryset.QuerySet.model"></a>
#### model

```python
 | @property
 | model() -> Type["T"]
```

Shortcut to model class set on QuerySet.

**Returns**:

`Type[Model]`: model class

<a name="queryset.queryset.QuerySet.rebuild_self"></a>
#### rebuild\_self

```python
 | rebuild_self(filter_clauses: List = None, exclude_clauses: List = None, select_related: List = None, limit_count: int = None, offset: int = None, excludable: "ExcludableItems" = None, order_bys: List = None, prefetch_related: List = None, limit_raw_sql: bool = None, proxy_source_model: Optional[Type["Model"]] = None) -> "QuerySet"
```

Method that returns new instance of queryset based on passed params,
all not passed params are taken from current values.

<a name="queryset.queryset.QuerySet._prefetch_related_models"></a>
#### \_prefetch\_related\_models

```python
 | async _prefetch_related_models(models: List["T"], rows: List) -> List["T"]
```

Performs prefetch query for selected models names.

**Arguments**:

- `models` (`List[Model]`): list of already parsed main Models from main query
- `rows` (`List[sqlalchemy.engine.result.RowProxy]`): database rows from main query

**Returns**:

`List[Model]`: list of models with prefetch models populated

<a name="queryset.queryset.QuerySet._process_query_result_rows"></a>
#### \_process\_query\_result\_rows

```python
 | _process_query_result_rows(rows: List) -> List["T"]
```

Process database rows and initialize ormar Model from each of the rows.

**Arguments**:

- `rows` (`List[sqlalchemy.engine.result.RowProxy]`): list of database rows from query result

**Returns**:

`List[Model]`: list of models

<a name="queryset.queryset.QuerySet._resolve_filter_groups"></a>
#### \_resolve\_filter\_groups

```python
 | _resolve_filter_groups(groups: Any) -> Tuple[List[FilterGroup], List[str]]
```

Resolves filter groups to populate FilterAction params in group tree.

**Arguments**:

- `groups` (`Any`): tuple of FilterGroups

**Returns**:

`Tuple[List[FilterGroup], List[str]]`: list of resolver groups

<a name="queryset.queryset.QuerySet.check_single_result_rows_count"></a>
#### check\_single\_result\_rows\_count

```python
 | @staticmethod
 | check_single_result_rows_count(rows: Sequence[Optional["T"]]) -> None
```

Verifies if the result has one and only one row.

**Arguments**:

- `rows` (`List[Model]`): one element list of Models

<a name="queryset.queryset.QuerySet.database"></a>
#### database

```python
 | @property
 | database() -> databases.Database
```

Shortcut to models database from Meta class.

**Returns**:

`databases.Database`: database

<a name="queryset.queryset.QuerySet.table"></a>
#### table

```python
 | @property
 | table() -> sqlalchemy.Table
```

Shortcut to models table from Meta class.

**Returns**:

`sqlalchemy.Table`: database table

<a name="queryset.queryset.QuerySet.build_select_expression"></a>
#### build\_select\_expression

```python
 | build_select_expression(limit: int = None, offset: int = None, order_bys: List = None) -> sqlalchemy.sql.select
```

Constructs the actual database query used in the QuerySet.
If any of the params is not passed the QuerySet own value is used.

**Arguments**:

- `limit` (`int`): number to limit the query
- `offset` (`int`): number to offset by
- `order_bys` (`List`): list of order-by fields names

**Returns**:

`sqlalchemy.sql.selectable.Select`: built sqlalchemy select expression

<a name="queryset.queryset.QuerySet.filter"></a>
#### filter

```python
 | filter(*args: Any, *, _exclude: bool = False, **kwargs: Any) -> "QuerySet[T]"
```

Allows you to filter by any `Model` attribute/field
as well as to fetch instances, with a filter across an FK relationship.

You can use special filter suffix to change the filter operands:

*  exact - like `album__name__exact='Malibu'` (exact match)
*  iexact - like `album__name__iexact='malibu'` (exact match case insensitive)
*  contains - like `album__name__contains='Mal'` (sql like)
*  icontains - like `album__name__icontains='mal'` (sql like case insensitive)
*  in - like `album__name__in=['Malibu', 'Barclay']` (sql in)
*  isnull - like `album__name__isnull=True` (sql is null)
(isnotnull `album__name__isnull=False` (sql is not null))
*  gt - like `position__gt=3` (sql >)
*  gte - like `position__gte=3` (sql >=)
*  lt - like `position__lt=3` (sql <)
*  lte - like `position__lte=3` (sql <=)
*  startswith - like `album__name__startswith='Mal'` (exact start match)
*  istartswith - like `album__name__istartswith='mal'` (case insensitive)
*  endswith - like `album__name__endswith='ibu'` (exact end match)
*  iendswith - like `album__name__iendswith='IBU'` (case insensitive)

Note that you can also use python style filters - check the docs!

**Arguments**:

- `_exclude` (`bool`): flag if it should be exclude or filter
- `kwargs` (`Any`): fields names and proper value types

**Returns**:

`QuerySet`: filtered QuerySet

<a name="queryset.queryset.QuerySet.exclude"></a>
#### exclude

```python
 | exclude(*args: Any, **kwargs: Any) -> "QuerySet[T]"
```

Works exactly the same as filter and all modifiers (suffixes) are the same,
but returns a *not* condition.

So if you use `filter(name='John')` which is `where name = 'John'` in SQL,
the `exclude(name='John')` equals to `where name <> 'John'`

Note that all conditions are joined so if you pass multiple values it
becomes a union of conditions.

`exclude(name='John', age>=35)` will become
`where not (name='John' and age>=35)`

**Arguments**:

- `kwargs` (`Any`): fields names and proper value types

**Returns**:

`QuerySet`: filtered QuerySet

<a name="queryset.queryset.QuerySet.select_related"></a>
#### select\_related

```python
 | select_related(related: Union[List, str]) -> "QuerySet[T]"
```

Allows to prefetch related models during the same query.

**With `select_related` always only one query is run against the database**,
meaning that one (sometimes complicated) join is generated and later nested
models are processed in python.

To fetch related model use `ForeignKey` names.

To chain related `Models` relation use double underscores between names.

**Arguments**:

- `related` (`Union[List, str]`): list of relation field names, can be linked by '__' to nest

**Returns**:

`QuerySet`: QuerySet

<a name="queryset.queryset.QuerySet.select_all"></a>
#### select\_all

```python
 | select_all(follow: bool = False) -> "QuerySet[T]"
```

By default adds only directly related models.

If follow=True is set it adds also related models of related models.

To not get stuck in an infinite loop as related models also keep a relation
to parent model visited models set is kept.

That way already visited models that are nested are loaded, but the load do not
follow them inside. So Model A -> Model B -> Model C -> Model A -> Model X
will load second Model A but will never follow into Model X.
Nested relations of those kind need to be loaded manually.

**Arguments**:

by default only directly related models are saved
with follow=True also related models of related models are saved
- `follow` (`bool`): flag to trigger deep save -

**Returns**:

`Model`: reloaded Model

<a name="queryset.queryset.QuerySet.prefetch_related"></a>
#### prefetch\_related

```python
 | prefetch_related(related: Union[List, str]) -> "QuerySet[T]"
```

Allows to prefetch related models during query - but opposite to
`select_related` each subsequent model is fetched in a separate database query.

**With `prefetch_related` always one query per Model is run against the
database**, meaning that you will have multiple queries executed one
after another.

To fetch related model use `ForeignKey` names.

To chain related `Models` relation use double underscores between names.

**Arguments**:

- `related` (`Union[List, str]`): list of relation field names, can be linked by '__' to nest

**Returns**:

`QuerySet`: QuerySet

<a name="queryset.queryset.QuerySet.fields"></a>
#### fields

```python
 | fields(columns: Union[List, str, Set, Dict], _is_exclude: bool = False) -> "QuerySet[T]"
```

With `fields()` you can select subset of model columns to limit the data load.

Note that `fields()` and `exclude_fields()` works both for main models
(on normal queries like `get`, `all` etc.)
as well as `select_related` and `prefetch_related`
models (with nested notation).

You can select specified fields by passing a `str, List[str], Set[str] or
dict` with nested definition.

To include related models use notation
`{related_name}__{column}[__{optional_next} etc.]`.

`fields()` can be called several times, building up the columns to select.

If you include related models into `select_related()` call but you won't specify
columns for those models in fields - implies a list of all fields for
those nested models.

Mandatory fields cannot be excluded as it will raise `ValidationError`,
to exclude a field it has to be nullable.

Pk column cannot be excluded - it's always auto added even if
not explicitly included.

You can also pass fields to include as dictionary or set.

To mark a field as included in a dictionary use it's name as key
and ellipsis as value.

To traverse nested models use nested dictionaries.

To include fields at last level instead of nested dictionary a set can be used.

To include whole nested model specify model related field name and ellipsis.

**Arguments**:

- `_is_exclude` (`bool`): flag if it's exclude or include operation
- `columns` (`Union[List, str, Set, Dict]`): columns to include

**Returns**:

`QuerySet`: QuerySet

<a name="queryset.queryset.QuerySet.exclude_fields"></a>
#### exclude\_fields

```python
 | exclude_fields(columns: Union[List, str, Set, Dict]) -> "QuerySet[T]"
```

With `exclude_fields()` you can select subset of model columns that will
be excluded to limit the data load.

It's the opposite of `fields()` method so check documentation above
to see what options are available.

Especially check above how you can pass also nested dictionaries
and sets as a mask to exclude fields from whole hierarchy.

Note that `fields()` and `exclude_fields()` works both for main models
(on normal queries like `get`, `all` etc.)
as well as `select_related` and `prefetch_related` models
(with nested notation).

Mandatory fields cannot be excluded as it will raise `ValidationError`,
to exclude a field it has to be nullable.

Pk column cannot be excluded - it's always auto added even
if explicitly excluded.

**Arguments**:

- `columns` (`Union[List, str, Set, Dict]`): columns to exclude

**Returns**:

`QuerySet`: QuerySet

<a name="queryset.queryset.QuerySet.order_by"></a>
#### order\_by

```python
 | order_by(columns: Union[List, str, OrderAction]) -> "QuerySet[T]"
```

With `order_by()` you can order the results from database based on your
choice of fields.

You can provide a string with field name or list of strings with fields names.

Ordering in sql will be applied in order of names you provide in order_by.

By default if you do not provide ordering `ormar` explicitly orders by
all primary keys

If you are sorting by nested models that causes that the result rows are
unsorted by the main model `ormar` will combine those children rows into
one main model.

The main model will never duplicate in the result

To order by main model field just provide a field name

To sort on nested models separate field names with dunder '__'.

You can sort this way across all relation types -> `ForeignKey`,
reverse virtual FK and `ManyToMany` fields.

To sort in descending order provide a hyphen in front of the field name

**Arguments**:

- `columns` (`Union[List, str]`): columns by which models should be sorted

**Returns**:

`QuerySet`: QuerySet

<a name="queryset.queryset.QuerySet.values"></a>
#### values

```python
 | async values(fields: Union[List, str, Set, Dict] = None, exclude_through: bool = False, _as_dict: bool = True, _flatten: bool = False) -> List
```

Return a list of dictionaries with column values in order of the fields
passed or all fields from queried models.

To filter for given row use filter/exclude methods before values,
to limit number of rows use limit/offset or paginate before values.

Note that it always return a list even for one row from database.

**Arguments**:

- `exclude_through` (`bool`): flag if through models should be excluded
- `_flatten` (`bool`): internal parameter to flatten one element tuples
- `_as_dict` (`bool`): internal parameter if return dict or tuples
- `fields` (`Union[List, str, Set, Dict]`): field name or list of field names to extract from db

<a name="queryset.queryset.QuerySet.values_list"></a>
#### values\_list

```python
 | async values_list(fields: Union[List, str, Set, Dict] = None, flatten: bool = False, exclude_through: bool = False) -> List
```

Return a list of tuples with column values in order of the fields passed or
all fields from queried models.

When one field is passed you can flatten the list of tuples into list of values
of that single field.

To filter for given row use filter/exclude methods before values,
to limit number of rows use limit/offset or paginate before values.

Note that it always return a list even for one row from database.

**Arguments**:

- `exclude_through` (`bool`): flag if through models should be excluded
- `fields` (`Union[str, List[str]]`): field name or list of field names to extract from db
- `flatten` (`bool`): when one field is passed you can flatten the list of tuples

<a name="queryset.queryset.QuerySet.exists"></a>
#### exists

```python
 | async exists() -> bool
```

Returns a bool value to confirm if there are rows matching the given criteria
(applied with `filter` and `exclude` if set).

**Returns**:

`bool`: result of the check

<a name="queryset.queryset.QuerySet.count"></a>
#### count

```python
 | async count(distinct: bool = True) -> int
```

Returns number of rows matching the given criteria
(applied with `filter` and `exclude` if set before).
If `distinct` is `True` (the default), this will return the number of primary rows selected. If `False`,
the count will be the total number of rows returned
(including extra rows for `one-to-many` or `many-to-many` left `select_related` table joins).
`False` is the legacy (buggy) behavior for workflows that depend on it.

**Arguments**:

- `distinct` (`bool`): flag if the primary table rows should be distinct or not

**Returns**:

`int`: number of rows

<a name="queryset.queryset.QuerySet.max"></a>
#### max

```python
 | async max(columns: Union[str, List[str]]) -> Any
```

Returns max value of columns for rows matching the given criteria
(applied with `filter` and `exclude` if set before).

**Returns**:

`Any`: max value of column(s)

<a name="queryset.queryset.QuerySet.min"></a>
#### min

```python
 | async min(columns: Union[str, List[str]]) -> Any
```

Returns min value of columns for rows matching the given criteria
(applied with `filter` and `exclude` if set before).

**Returns**:

`Any`: min value of column(s)

<a name="queryset.queryset.QuerySet.sum"></a>
#### sum

```python
 | async sum(columns: Union[str, List[str]]) -> Any
```

Returns sum value of columns for rows matching the given criteria
(applied with `filter` and `exclude` if set before).

**Returns**:

`int`: sum value of columns

<a name="queryset.queryset.QuerySet.avg"></a>
#### avg

```python
 | async avg(columns: Union[str, List[str]]) -> Any
```

Returns avg value of columns for rows matching the given criteria
(applied with `filter` and `exclude` if set before).

**Returns**:

`Union[int, float, List]`: avg value of columns

<a name="queryset.queryset.QuerySet.update"></a>
#### update

```python
 | async update(each: bool = False, **kwargs: Any) -> int
```

Updates the model table after applying the filters from kwargs.

You have to either pass a filter to narrow down a query or explicitly pass
each=True flag to affect whole table.

**Arguments**:

- `each` (`bool`): flag if whole table should be affected if no filter is passed
- `kwargs` (`Any`): fields names and proper value types

**Returns**:

`int`: number of updated rows

<a name="queryset.queryset.QuerySet.delete"></a>
#### delete

```python
 | async delete(*args: Any, *, each: bool = False, **kwargs: Any) -> int
```

Deletes from the model table after applying the filters from kwargs.

You have to either pass a filter to narrow down a query or explicitly pass
each=True flag to affect whole table.

**Arguments**:

- `each` (`bool`): flag if whole table should be affected if no filter is passed
- `kwargs` (`Any`): fields names and proper value types

**Returns**:

`int`: number of deleted rows

<a name="queryset.queryset.QuerySet.paginate"></a>
#### paginate

```python
 | paginate(page: int, page_size: int = 20) -> "QuerySet[T]"
```

You can paginate the result which is a combination of offset and limit clauses.
Limit is set to page size and offset is set to (page-1) * page_size.

**Arguments**:

- `page_size` (`int`): numbers of items per page
- `page` (`int`): page number

**Returns**:

`QuerySet`: QuerySet

<a name="queryset.queryset.QuerySet.limit"></a>
#### limit

```python
 | limit(limit_count: int, limit_raw_sql: bool = None) -> "QuerySet[T]"
```

You can limit the results to desired number of parent models.

To limit the actual number of database query rows instead of number of main
models use the `limit_raw_sql` parameter flag, and set it to `True`.

**Arguments**:

- `limit_raw_sql` (`bool`): flag if raw sql should be limited
- `limit_count` (`int`): number of models to limit

**Returns**:

`QuerySet`: QuerySet

<a name="queryset.queryset.QuerySet.offset"></a>
#### offset

```python
 | offset(offset: int, limit_raw_sql: bool = None) -> "QuerySet[T]"
```

You can also offset the results by desired number of main models.

To offset the actual number of database query rows instead of number of main
models use the `limit_raw_sql` parameter flag, and set it to `True`.

**Arguments**:

- `limit_raw_sql` (`bool`): flag if raw sql should be offset
- `offset` (`int`): numbers of models to offset

**Returns**:

`QuerySet`: QuerySet

<a name="queryset.queryset.QuerySet.first"></a>
#### first

```python
 | async first(*args: Any, **kwargs: Any) -> "T"
```

Gets the first row from the db ordered by primary key column ascending.

**Raises**:

- `NoMatch`: if no rows are returned
- `MultipleMatches`: if more than 1 row is returned.

**Arguments**:

- `kwargs` (`Any`): fields names and proper value types

**Returns**:

`Model`: returned model

<a name="queryset.queryset.QuerySet.get_or_none"></a>
#### get\_or\_none

```python
 | async get_or_none(*args: Any, **kwargs: Any) -> Optional["T"]
```

Get's the first row from the db meeting the criteria set by kwargs.

If no criteria set it will return the last row in db sorted by pk.

Passing a criteria is actually calling filter(*args, **kwargs) method described
below.

If not match is found None will be returned.

**Arguments**:

- `kwargs` (`Any`): fields names and proper value types

**Returns**:

`Model`: returned model

<a name="queryset.queryset.QuerySet.get"></a>
#### get

```python
 | async get(*args: Any, **kwargs: Any) -> "T"
```

Get's the first row from the db meeting the criteria set by kwargs.

If no criteria set it will return the last row in db sorted by pk.

Passing a criteria is actually calling filter(*args, **kwargs) method described
below.

**Raises**:

- `NoMatch`: if no rows are returned
- `MultipleMatches`: if more than 1 row is returned.

**Arguments**:

- `kwargs` (`Any`): fields names and proper value types

**Returns**:

`Model`: returned model

<a name="queryset.queryset.QuerySet.get_or_create"></a>
#### get\_or\_create

```python
 | async get_or_create(_defaults: Optional[Dict[str, Any]] = None, *args: Any, **kwargs: Any) -> Tuple["T", bool]
```

Combination of create and get methods.

Tries to get a row meeting the criteria for kwargs
and if `NoMatch` exception is raised
it creates a new one with given kwargs.

Passing a criteria is actually calling filter(*args, **kwargs) method described
below.

**Arguments**:

- `kwargs` (`Any`): fields names and proper value types

**Returns**:

`Model`: returned or created Model

<a name="queryset.queryset.QuerySet.update_or_create"></a>
#### update\_or\_create

```python
 | async update_or_create(**kwargs: Any) -> "T"
```

Updates the model, or in case there is no match in database creates a new one.

**Arguments**:

- `kwargs` (`Any`): fields names and proper value types

**Returns**:

`Model`: updated or created model

<a name="queryset.queryset.QuerySet.all"></a>
#### all

```python
 | async all(*args: Any, **kwargs: Any) -> List["T"]
```

Returns all rows from a database for given model for set filter options.

Passing args and/or kwargs is a shortcut and equals to calling
`filter(*args, **kwargs).all()`.

If there are no rows meeting the criteria an empty list is returned.

**Arguments**:

- `kwargs` (`Any`): fields names and proper value types

**Returns**:

`List[Model]`: list of returned models

<a name="queryset.queryset.QuerySet.create"></a>
#### create

```python
 | async create(**kwargs: Any) -> "T"
```

Creates the model instance, saves it in a database and returns the updates model
(with pk populated if not passed and autoincrement is set).

The allowed kwargs are `Model` fields names and proper value types.

**Arguments**:

- `kwargs` (`Any`): fields names and proper value types

**Returns**:

`Model`: created model

<a name="queryset.queryset.QuerySet.bulk_create"></a>
#### bulk\_create

```python
 | async bulk_create(objects: List["T"]) -> None
```

Performs a bulk update in one database session to speed up the process.

Allows you to create multiple objects at once.

A valid list of `Model` objects needs to be passed.

Bulk operations do not send signals.

**Arguments**:

- `objects` (`List[Model]`): list of ormar models already initialized and ready to save.

<a name="queryset.queryset.QuerySet.bulk_update"></a>
#### bulk\_update

```python
 | async bulk_update(objects: List["T"], columns: List[str] = None) -> None
```

Performs bulk update in one database session to speed up the process.

Allows to update multiple instance at once.

All `Models` passed need to have primary key column populated.

You can also select which fields to update by passing `columns` list
as a list of string names.

Bulk operations do not send signals.

**Arguments**:

- `objects` (`List[Model]`): list of ormar models
- `columns` (`List[str]`): list of columns to update
