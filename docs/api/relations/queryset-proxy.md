<a name="relations.querysetproxy"></a>
# relations.querysetproxy

<a name="relations.querysetproxy.QuerysetProxy"></a>
## QuerysetProxy Objects

```python
class QuerysetProxy()
```

Exposes QuerySet methods on relations, but also handles creating and removing
of through Models for m2m relations.

<a name="relations.querysetproxy.QuerysetProxy.queryset"></a>
#### queryset

```python
 | @property
 | queryset() -> "QuerySet"
```

Returns queryset if it's set, AttributeError otherwise.

**Returns**:

`(QuerySet)`: QuerySet

<a name="relations.querysetproxy.QuerysetProxy.queryset"></a>
#### queryset

```python
 | @queryset.setter
 | queryset(value: "QuerySet") -> None
```

Set's the queryset. Initialized in RelationProxy.

**Arguments**:

- `value (QuerySet)`: QuerySet

<a name="relations.querysetproxy.QuerysetProxy._assign_child_to_parent"></a>
#### \_assign\_child\_to\_parent

```python
 | _assign_child_to_parent(child: Optional["Model"]) -> None
```

Registers child in parents RelationManager.

**Arguments**:

- `child (Model)`: child to register on parent side.

<a name="relations.querysetproxy.QuerysetProxy._register_related"></a>
#### \_register\_related

```python
 | _register_related(child: Union["Model", Sequence[Optional["Model"]]]) -> None
```

Registers child/ children in parents RelationManager.

**Arguments**:

- `child (Union[Model,List[Model]])`: child or list of children models to register.

<a name="relations.querysetproxy.QuerysetProxy._clean_items_on_load"></a>
#### \_clean\_items\_on\_load

```python
 | _clean_items_on_load() -> None
```

Cleans the current list of the related models.

<a name="relations.querysetproxy.QuerysetProxy.create_through_instance"></a>
#### create\_through\_instance

```python
 | async create_through_instance(child: "Model", **kwargs: Any) -> None
```

Crete a through model instance in the database for m2m relations.

**Arguments**:

- `kwargs (Any)`: dict of additional keyword arguments for through instance
- `child (Model)`: child model instance

<a name="relations.querysetproxy.QuerysetProxy.update_through_instance"></a>
#### update\_through\_instance

```python
 | async update_through_instance(child: "Model", **kwargs: Any) -> None
```

Updates a through model instance in the database for m2m relations.

**Arguments**:

- `kwargs (Any)`: dict of additional keyword arguments for through instance
- `child (Model)`: child model instance

<a name="relations.querysetproxy.QuerysetProxy.delete_through_instance"></a>
#### delete\_through\_instance

```python
 | async delete_through_instance(child: "Model") -> None
```

Removes through model instance from the database for m2m relations.

**Arguments**:

- `child (Model)`: child model instance

<a name="relations.querysetproxy.QuerysetProxy.exists"></a>
#### exists

```python
 | async exists() -> bool
```

Returns a bool value to confirm if there are rows matching the given criteria
(applied with `filter` and `exclude` if set).

Actual call delegated to QuerySet.

**Returns**:

`(bool)`: result of the check

<a name="relations.querysetproxy.QuerysetProxy.count"></a>
#### count

```python
 | async count() -> int
```

Returns number of rows matching the given criteria
(applied with `filter` and `exclude` if set before).

Actual call delegated to QuerySet.

**Returns**:

`(int)`: number of rows

<a name="relations.querysetproxy.QuerysetProxy.clear"></a>
#### clear

```python
 | async clear(keep_reversed: bool = True) -> int
```

Removes all related models from given relation.

Removes all through models for m2m relation.

For reverse FK relations keep_reversed flag marks if the reversed models
should be kept or deleted from the database too (False means that models
will be deleted, and not only removed from relation).

**Arguments**:

- `keep_reversed (bool)`: flag if reverse models in reverse FK should be deleted
or not, keep_reversed=False deletes them from database.

**Returns**:

`(int)`: number of deleted models

<a name="relations.querysetproxy.QuerysetProxy.first"></a>
#### first

```python
 | async first(**kwargs: Any) -> "Model"
```

Gets the first row from the db ordered by primary key column ascending.

Actual call delegated to QuerySet.

List of related models is cleared before the call.

**Arguments**:

- `kwargs ()`: 

**Returns**:

`(_asyncio.Future)`: 

<a name="relations.querysetproxy.QuerysetProxy.get"></a>
#### get

```python
 | async get(**kwargs: Any) -> "Model"
```

Get's the first row from the db meeting the criteria set by kwargs.

If no criteria set it will return the last row in db sorted by pk.

Passing a criteria is actually calling filter(**kwargs) method described below.

Actual call delegated to QuerySet.

List of related models is cleared before the call.

**Raises**:

- `NoMatch`: if no rows are returned
- `MultipleMatches`: if more than 1 row is returned.

**Arguments**:

- `kwargs (Any)`: fields names and proper value types

**Returns**:

`(Model)`: returned model

<a name="relations.querysetproxy.QuerysetProxy.all"></a>
#### all

```python
 | async all(**kwargs: Any) -> Sequence[Optional["Model"]]
```

Returns all rows from a database for given model for set filter options.

Passing kwargs is a shortcut and equals to calling `filter(**kwrags).all()`.

If there are no rows meeting the criteria an empty list is returned.

Actual call delegated to QuerySet.

List of related models is cleared before the call.

**Arguments**:

- `kwargs (Any)`: fields names and proper value types

**Returns**:

`(List[Model])`: list of returned models

<a name="relations.querysetproxy.QuerysetProxy.create"></a>
#### create

```python
 | async create(**kwargs: Any) -> "Model"
```

Creates the model instance, saves it in a database and returns the updates model
(with pk populated if not passed and autoincrement is set).

The allowed kwargs are `Model` fields names and proper value types.

For m2m relation the through model is created automatically.

Actual call delegated to QuerySet.

**Arguments**:

- `kwargs (Any)`: fields names and proper value types

**Returns**:

`(Model)`: created model

<a name="relations.querysetproxy.QuerysetProxy.update"></a>
#### update

```python
 | async update(each: bool = False, **kwargs: Any) -> int
```

Updates the model table after applying the filters from kwargs.

You have to either pass a filter to narrow down a query or explicitly pass
each=True flag to affect whole table.

**Arguments**:

- `each (bool)`: flag if whole table should be affected if no filter is passed
- `kwargs (Any)`: fields names and proper value types

**Returns**:

`(int)`: number of updated rows

<a name="relations.querysetproxy.QuerysetProxy.get_or_create"></a>
#### get\_or\_create

```python
 | async get_or_create(**kwargs: Any) -> "Model"
```

Combination of create and get methods.

Tries to get a row meeting the criteria fro kwargs
and if `NoMatch` exception is raised
it creates a new one with given kwargs.

**Arguments**:

- `kwargs (Any)`: fields names and proper value types

**Returns**:

`(Model)`: returned or created Model

<a name="relations.querysetproxy.QuerysetProxy.update_or_create"></a>
#### update\_or\_create

```python
 | async update_or_create(**kwargs: Any) -> "Model"
```

Updates the model, or in case there is no match in database creates a new one.

Actual call delegated to QuerySet.

**Arguments**:

- `kwargs (Any)`: fields names and proper value types

**Returns**:

`(Model)`: updated or created model

<a name="relations.querysetproxy.QuerysetProxy.filter"></a>
#### filter

```python
 | filter(**kwargs: Any) -> "QuerysetProxy"
```

Allows you to filter by any `Model` attribute/field
as well as to fetch instances, with a filter across an FK relationship.

You can use special filter suffix to change the filter operands:

*  exact - like `album__name__exact='Malibu'` (exact match)
*  iexact - like `album__name__iexact='malibu'` (exact match case insensitive)
*  contains - like `album__name__contains='Mal'` (sql like)
*  icontains - like `album__name__icontains='mal'` (sql like case insensitive)
*  in - like `album__name__in=['Malibu', 'Barclay']` (sql in)
*  gt - like `position__gt=3` (sql >)
*  gte - like `position__gte=3` (sql >=)
*  lt - like `position__lt=3` (sql <)
*  lte - like `position__lte=3` (sql <=)
*  startswith - like `album__name__startswith='Mal'` (exact start match)
*  istartswith - like `album__name__istartswith='mal'` (case insensitive)
*  endswith - like `album__name__endswith='ibu'` (exact end match)
*  iendswith - like `album__name__iendswith='IBU'` (case insensitive)

Actual call delegated to QuerySet.

**Arguments**:

- `kwargs (Any)`: fields names and proper value types

**Returns**:

`(QuerysetProxy)`: filtered QuerysetProxy

<a name="relations.querysetproxy.QuerysetProxy.exclude"></a>
#### exclude

```python
 | exclude(**kwargs: Any) -> "QuerysetProxy"
```

Works exactly the same as filter and all modifiers (suffixes) are the same,
but returns a *not* condition.

So if you use `filter(name='John')` which is `where name = 'John'` in SQL,
the `exclude(name='John')` equals to `where name <> 'John'`

Note that all conditions are joined so if you pass multiple values it
becomes a union of conditions.

`exclude(name='John', age>=35)` will become
`where not (name='John' and age>=35)`

Actual call delegated to QuerySet.

**Arguments**:

- `kwargs (Any)`: fields names and proper value types

**Returns**:

`(QuerysetProxy)`: filtered QuerysetProxy

<a name="relations.querysetproxy.QuerysetProxy.select_related"></a>
#### select\_related

```python
 | select_related(related: Union[List, str]) -> "QuerysetProxy"
```

Allows to prefetch related models during the same query.

**With `select_related` always only one query is run against the database**,
meaning that one (sometimes complicated) join is generated and later nested
models are processed in python.

To fetch related model use `ForeignKey` names.

To chain related `Models` relation use double underscores between names.

Actual call delegated to QuerySet.

**Arguments**:

- `related (Union[List, str])`: list of relation field names, can be linked by '__' to nest

**Returns**:

`(QuerysetProxy)`: QuerysetProxy

<a name="relations.querysetproxy.QuerysetProxy.prefetch_related"></a>
#### prefetch\_related

```python
 | prefetch_related(related: Union[List, str]) -> "QuerysetProxy"
```

Allows to prefetch related models during query - but opposite to
`select_related` each subsequent model is fetched in a separate database query.

**With `prefetch_related` always one query per Model is run against the
database**, meaning that you will have multiple queries executed one
after another.

To fetch related model use `ForeignKey` names.

To chain related `Models` relation use double underscores between names.

Actual call delegated to QuerySet.

**Arguments**:

- `related (Union[List, str])`: list of relation field names, can be linked by '__' to nest

**Returns**:

`(QuerysetProxy)`: QuerysetProxy

<a name="relations.querysetproxy.QuerysetProxy.paginate"></a>
#### paginate

```python
 | paginate(page: int, page_size: int = 20) -> "QuerysetProxy"
```

You can paginate the result which is a combination of offset and limit clauses.
Limit is set to page size and offset is set to (page-1) * page_size.

Actual call delegated to QuerySet.

**Arguments**:

- `page_size (int)`: numbers of items per page
- `page (int)`: page number

**Returns**:

`(QuerySet)`: QuerySet

<a name="relations.querysetproxy.QuerysetProxy.limit"></a>
#### limit

```python
 | limit(limit_count: int) -> "QuerysetProxy"
```

You can limit the results to desired number of parent models.

Actual call delegated to QuerySet.

**Arguments**:

- `limit_count (int)`: number of models to limit

**Returns**:

`(QuerysetProxy)`: QuerysetProxy

<a name="relations.querysetproxy.QuerysetProxy.offset"></a>
#### offset

```python
 | offset(offset: int) -> "QuerysetProxy"
```

You can also offset the results by desired number of main models.

Actual call delegated to QuerySet.

**Arguments**:

- `offset (int)`: numbers of models to offset

**Returns**:

`(QuerysetProxy)`: QuerysetProxy

<a name="relations.querysetproxy.QuerysetProxy.fields"></a>
#### fields

```python
 | fields(columns: Union[List, str, Set, Dict]) -> "QuerysetProxy"
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

Actual call delegated to QuerySet.

**Arguments**:

- `columns (Union[List, str, Set, Dict])`: columns to include

**Returns**:

`(QuerysetProxy)`: QuerysetProxy

<a name="relations.querysetproxy.QuerysetProxy.exclude_fields"></a>
#### exclude\_fields

```python
 | exclude_fields(columns: Union[List, str, Set, Dict]) -> "QuerysetProxy"
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

Actual call delegated to QuerySet.

**Arguments**:

- `columns (Union[List, str, Set, Dict])`: columns to exclude

**Returns**:

`(QuerysetProxy)`: QuerysetProxy

<a name="relations.querysetproxy.QuerysetProxy.order_by"></a>
#### order\_by

```python
 | order_by(columns: Union[List, str]) -> "QuerysetProxy"
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

Actual call delegated to QuerySet.

**Arguments**:

- `columns (Union[List, str])`: columns by which models should be sorted

**Returns**:

`(QuerysetProxy)`: QuerysetProxy

