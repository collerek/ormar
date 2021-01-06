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

## get

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

## all

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

## create

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


## get_or_create

`get_or_create(**kwargs) -> Model`

!!!tip
    Read more in queries documentation [get_or_create][get_or_create]

## update_or_create

`update_or_create(**kwargs) -> Model`

!!!tip
    Read more in queries documentation [update_or_create][update_or_create]

## filter

`filter(**kwargs) -> QuerySet`

!!!tip
    Read more in queries documentation [filter][filter]

## exclude

`exclude(**kwargs) -> QuerySet`

!!!tip
    Read more in queries documentation [exclude][exclude]

## select_related

`select_related(related: Union[List, str]) -> QuerySet`

!!!tip
    Read more in queries documentation [select_related][select_related]

## prefetch_related

`prefetch_related(related: Union[List, str]) -> QuerySet`

!!!tip
    Read more in queries documentation [prefetch_related][prefetch_related]

## limit

`limit(limit_count: int) -> QuerySet`

!!!tip
    Read more in queries documentation [limit][limit]

## offset

`offset(offset: int) -> QuerySet`

!!!tip
    Read more in queries documentation [offset][offset]

## count

`count() -> int`

!!!tip
    Read more in queries documentation [count][count]

## exists

`exists() -> bool`

!!!tip
    Read more in queries documentation [exists][exists]

## fields

`fields(columns: Union[List, str, set, dict]) -> QuerySet`

!!!tip
    Read more in queries documentation [fields][fields]

## exclude_fields

`exclude_fields(columns: Union[List, str, set, dict]) -> QuerySet`

!!!tip
    Read more in queries documentation [exclude_fields][exclude_fields]

## order_by

`order_by(columns:Union[List, str]) -> QuerySet`

!!!tip
    Read more in queries documentation [order_by][order_by]


[queries]: ../queries.md
[get]: ../queries.md#get
[all]: ../queries.md#all
[create]: ../queries.md#create
[get_or_create]: ../queries.md#get_or_create
[update_or_create]: ../queries.md#update_or_create
[filter]: ../queries.md#filter
[exclude]: ../queries.md#exclude
[select_related]: ../queries.md#select_related
[prefetch_related]: ../queries.md#prefetch_related
[limit]: ../queries.md#limit
[offset]: ../queries.md#offset
[count]: ../queries.md#count
[exists]: ../queries.md#exists
[fields]: ../queries.md#fields
[exclude_fields]: ../queries.md#exclude_fields
[order_by]: ../queries.md#order_by