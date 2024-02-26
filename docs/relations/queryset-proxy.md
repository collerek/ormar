# QuerySetProxy

When access directly the related `ManyToMany` field as well as `ReverseForeignKey` returns the list of related models.

But at the same time it exposes subset of QuerySet API, so you can filter, create, select related etc related models directly from parent model.

!!!note
    By default exposed QuerySet is already filtered to return only `Models` related to parent `Model`.

    So if you issue `post.categories.all()` you will get all categories related to that post, not all in table.

!!!note
    Note that when accessing QuerySet API methods through QuerysetProxy you don't
    need to use `objects` attribute like in normal queries.

    So note that it's `post.categories.all()` and **not** `post.categories.objects.all()`.

    To learn more about available QuerySet methods visit [queries][queries]

!!!warning
    Querying related models from ManyToMany cleans list of related models loaded on parent model:

    Example: `post.categories.first()` will set post.categories to list of 1 related model -> the one returned by first()

    Example 2: if post has 4 categories so `len(post.categories) == 4` calling `post.categories.limit(2).all()`
    -> will load only 2 children and now `assert len(post.categories) == 2`

    This happens for all QuerysetProxy methods returning data: `get`, `all` and `first` and in `get_or_create` if model already exists.

    Note that value returned by `create` or created in `get_or_create` and `update_or_create`
    if model does not exist will be added to relation list (not clearing it).

## Read data from database

### get

`get(**kwargs): -> Model`

To grab just one of related models filtered by name you can use `get(**kwargs)` method.

```python
# grab one category
assert news == await post.categories.get(name="News")

# note that method returns the category so you can grab this value
# but it also modifies list of related models in place
# so regardless of what was previously loaded on parent model
# now it has only one value -> just loaded with get() call
assert len(post.categories) == 1
assert post.categories[0] == news

```

!!!tip
    Read more in queries documentation [get][get]

### get_or_create

`get_or_create(_defaults: Optional[Dict[str, Any]] = None, **kwargs) -> Tuple[Model, bool]`

Tries to get a row meeting the criteria and if NoMatch exception is raised it creates a new one with given kwargs and _defaults.

!!!tip
    Read more in queries documentation [get_or_create][get_or_create]

### all

`all(**kwargs) -> List[Optional["Model"]]`

To get a list of related models use `all()` method.

Note that you can filter the queryset, select related, exclude fields etc. like in normal query.

```python
# with all Queryset methods - filtering, selecting columns, counting etc.
await news.posts.filter(title__contains="M2M").all()
await Category.objects.filter(posts__author=guido).get()

# columns models of many to many relation can be prefetched
news_posts = await news.posts.select_related("author").all()
assert news_posts[0].author == guido
```

!!!tip
    Read more in queries documentation [all][all]

### iterate

`iterate(**kwargs) -> AsyncGenerator["Model"]`

To iterate on related models use `iterate()` method.

Note that you can filter the queryset, select related, exclude fields etc. like in normal query.

```python
# iterate on categories of this post with an async generator
async for category in post.categories.iterate():
    print(category.name)
```

!!!tip
    Read more in queries documentation [iterate][iterate]

## Insert/ update data into database

### create

`create(**kwargs): -> Model`

Create related `Model` directly from parent `Model`.

The link table is automatically populated, as well as relation ids in the database.

```python
# Creating columns object from instance:
await post.categories.create(name="Tips")
assert len(await post.categories.all()) == 2
# newly created instance already have relation persisted in the database
```

!!!tip
    Read more in queries documentation [create][create]

For `ManyToMany` relations there is an additional functionality of passing parameters
that will be used to create a through model if you declared additional fields on explicitly
provided Through model.

Given sample like this:

```Python hl_lines="14-20 29"
--8<-- "../docs_src/relations/docs004.py"
```

You can populate fields on through model in the `create()` call in a following way:

```python

post = await Post(title="Test post").save()
await post.categories.create(
    name="Test category1",
    # in arguments pass a dictionary with name of the through field and keys
    # corresponding to through model fields
    postcategory={"sort_order": 1, "param_name": "volume"},
)
```

### get_or_create

`get_or_create(_defaults: Optional[Dict[str, Any]] = None, **kwargs) -> Tuple[Model, bool]`

Tries to get a row meeting the criteria and if NoMatch exception is raised it creates a new one with given kwargs.

!!!tip
    Read more in queries documentation [get_or_create][get_or_create]

### update_or_create

`update_or_create(**kwargs) -> Model`

Updates the model, or in case there is no match in database creates a new one.

!!!tip
    Read more in queries documentation [update_or_create][update_or_create]

### update

`update(**kwargs, each:bool = False) -> int`

Updates the related model with provided keyword arguments, return number of updated rows.

!!!tip
    Read more in queries documentation [update][update]

Note that for `ManyToMany` relations update can also accept an argument with through field
name and a dictionary of fields.

```Python hl_lines="14-20 29"
--8<-- "../docs_src/relations/docs004.py"
```

In example above you can update attributes of `postcategory` in a following call:
```python
await post.categories.filter(name="Test category3").update(
            postcategory={"sort_order": 4}
        )
```

## Filtering and sorting

### filter

`filter(*args, **kwargs) -> QuerySet`

Allows you to filter by any Model attribute/field as well as to fetch instances, with a filter across an FK relationship.

!!!tip
    Read more in queries documentation [filter][filter]

### exclude

`exclude(*args, **kwargs) -> QuerySet`

Works exactly the same as filter and all modifiers (suffixes) are the same, but returns a not condition.

!!!tip
    Read more in queries documentation [exclude][exclude]

### order_by

`order_by(columns:Union[List, str]) -> QuerySet`

With order_by() you can order the results from database based on your choice of fields.

!!!tip
    Read more in queries documentation [order_by][order_by]

## Joins and subqueries

### select_related

`select_related(related: Union[List, str]) -> QuerySet`

Allows to prefetch related models during the same query.

With select_related always only one query is run against the database, meaning that one (sometimes complicated) join is generated and later nested models are processed in python.

!!!tip
    Read more in queries documentation [select_related][select_related]

### prefetch_related

`prefetch_related(related: Union[List, str]) -> QuerySet`

Allows to prefetch related models during query - but opposite to select_related each subsequent model is fetched in a separate database query.

With prefetch_related always one query per Model is run against the database, meaning that you will have multiple queries executed one after another.

!!!tip
    Read more in queries documentation [prefetch_related][prefetch_related]

## Pagination and rows number

### paginate

`paginate(page: int, page_size: int = 20) -> QuerySet`

Combines the offset and limit methods based on page number and size.

!!!tip
    Read more in queries documentation [paginate][paginate]

### limit

`limit(limit_count: int) -> QuerySet`

You can limit the results to desired number of parent models.

!!!tip
    Read more in queries documentation [limit][limit]

### offset

`offset(offset: int) -> QuerySet`

You can offset the results by desired number of main models.

!!!tip
    Read more in queries documentation [offset][offset]

## Selecting subset of columns

### fields

`fields(columns: Union[List, str, set, dict]) -> QuerySet`

With fields() you can select subset of model columns to limit the data load.

!!!tip
    Read more in queries documentation [fields][fields]

### exclude_fields

`exclude_fields(columns: Union[List, str, set, dict]) -> QuerySet`

With exclude_fields() you can select subset of model columns that will be excluded to limit the data load.

!!!tip
    Read more in queries documentation [exclude_fields][exclude_fields]

## Aggregated functions

### count

`count(distinct: bool = True) -> int`

Returns number of rows matching the given criteria (i.e. applied with filter and exclude)

!!!tip
    Read more in queries documentation [count][count]

### exists

`exists() -> bool`

Returns a bool value to confirm if there are rows matching the given criteria (applied with filter and exclude)

!!!tip
    Read more in queries documentation [exists][exists]


[queries]: ../queries/index.md
[get]: ../queries/read.md#get
[all]: ../queries/read.md#all
[iterate]: ../queries/read.md#iterate
[create]: ../queries/create.md#create
[get_or_create]: ../queries/read.md#get_or_create
[update_or_create]: ../queries/update.md#update_or_create
[update]: ../queries/update.md#update
[filter]: ../queries/filter-and-sort.md#filter
[exclude]: ../queries/filter-and-sort.md#exclude
[select_related]: ../queries/joins-and-subqueries.md#select_related
[prefetch_related]: ../queries/joins-and-subqueries.md#prefetch_related
[limit]: ../queries/pagination-and-rows-number.md#limit
[offset]: ../queries/pagination-and-rows-number.md#offset
[paginate]: ../queries/pagination-and-rows-number.md#paginate
[count]: ../queries/aggregations.md#count
[exists]: ../queries/aggregations.md#exists
[fields]: ../queries/select-columns.md#fields
[exclude_fields]: ../queries/select-columns.md#exclude_fields
[order_by]: ../queries/filter-and-sort.md#order_by
