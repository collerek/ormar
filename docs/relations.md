# Relations

## Defining a relationship

### ForeignKey

`ForeignKey(to, related_name=None)` has required parameters `to` that takes target `Model` class.  

Sqlalchemy column and Type are automatically taken from target `Model`.

* Sqlalchemy column: class of a target `Model` primary key column  
* Type (used for pydantic): type of a target `Model` 

#### Defining Models

To define a relation add `ForeignKey` field that points to related `Model`.

```Python hl_lines="29"
--8<-- "../docs_src/fields/docs003.py"
```

#### Reverse Relation

`ForeignKey` fields are automatically registering reverse side of the relation.

By default it's child (source) `Model` name + s, like courses in snippet below: 

```Python hl_lines="29 35"
--8<-- "../docs_src/fields/docs001.py"
```

Reverse relation exposes API to manage related objects also from parent side.

##### add

Adding child model from parent side causes adding related model to currently loaded parent relation, 
as well as sets child's model foreign key value and updates the model.

```python
department = await Department(name="Science").save()
course = Course(name="Math", completed=False) # note - not saved

await department.courses.add(course)
assert course.pk is not None # child model was saved
# relation on child model is set and FK column saved in db
assert courses.department == department
# relation on parent model is also set
assert department.courses[0] == course 
```

!!!warning
    If you want to add child model on related model the primary key value for parent model **has to exist in database**.
    
    Otherwise ormar will raise RelationshipInstanceError as it cannot set child's ForeignKey column value 
    if parent model has no primary key value.
    
    That means that in example above the department has to be saved before you can call `department.courses.add()`.

##### remove

Removal of the related model one by one.

In reverse relation calling `remove()` does not remove the child model, but instead nulls it ForeignKey value.

```python
# continuing from above
await department.courses.remove(course)
assert len(department.courses) == 0
# course still exists and was saved in remove
assert course.pk is not None
assert course.department is None

# to remove child from db
await course.delete()
```

But if you want to clear the relation and delete the child at the same time you can issue:

```python
# this will not only clear the relation 
# but also delete related course from db
await department.courses.remove(course, keep_reversed=False)
```

##### clear

Removal of all related models in one call.

Like remove by default `clear()` nulls the ForeigKey column on child model (all, not matter if they are loaded or not).

```python
# nulls department column on all courses related to this department
await department.courses.clear()
```

If you want to remove the children altogether from the database, set `keep_reversed=False`

```python
# deletes from db all courses related to this department 
await department.courses.clear(keep_reversed=False)
```

##### QuerysetProxy

Reverse relation exposes QuerysetProxy API that allows you to query related model like you would issue a normal Query.

To read which methods of QuerySet are available read below [querysetproxy][querysetproxy]

#### related_name

But you can overwrite this name by providing `related_name` parameter like below:

```Python hl_lines="29 35"
--8<-- "../docs_src/fields/docs002.py"
```

!!!tip
    The reverse relation on access returns list of `wekref.proxy` to avoid circular references.
    

### Relation Setup

You have several ways to set-up a relationship connection.

#### `Model` instance

The most obvious one is to pass a related `Model` instance to the constructor.

```Python hl_lines="34-35"
--8<-- "../docs_src/relations/docs001.py"
```

#### Primary key value

You can setup the relation also with just the pk column value of the related model.

```Python hl_lines="37-38"
--8<-- "../docs_src/relations/docs001.py"
```

#### Dictionary

Next option is with a dictionary of key-values of the related model.

You can build the dictionary yourself or get it from existing model with `dict()` method.

```Python hl_lines="40-41"
--8<-- "../docs_src/relations/docs001.py"
```

#### None

Finally you can explicitly set it to None (default behavior if no value passed).

```Python hl_lines="43-44"
--8<-- "../docs_src/relations/docs001.py"
```

!!!warning
    In all not None cases the primary key value for related model **has to exist in database**.
    
    Otherwise an IntegrityError will be raised by your database driver library.


### ManyToMany

`ManyToMany(to, through)` has required parameters `to` and `through` that takes target and relation `Model` classes.  

Sqlalchemy column and Type are automatically taken from target `Model`.

* Sqlalchemy column: class of a target `Model` primary key column  
* Type (used for pydantic): type of a target `Model` 

####Defining `Models`

```Python
--8<-- "../docs_src/relations/docs002.py"
```

Create sample data:
```Python
guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
post = await Post.objects.create(title="Hello, M2M", author=guido)
news = await Category.objects.create(name="News")
```

#### add

```python
# Add a category to a post.
await post.categories.add(news)
# or from the other end:
await news.posts.add(post)
```

!!!warning
    In all not None cases the primary key value for related model **has to exist in database**.
    
    Otherwise an IntegrityError will be raised by your database driver library.

#### remove

Removal of the related model one by one.

Removes also the relation in the database.

```python
await news.posts.remove(post)
```

#### clear

Removal of all related models in one call.

Removes also the relation in the database.

```python
await news.posts.clear()
```

#### QuerysetProxy

Reverse relation exposes QuerysetProxy API that allows you to query related model like you would issue a normal Query.

To read which methods of QuerySet are available read below [querysetproxy][querysetproxy]

### QuerySetProxy

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

#### get

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

#### all

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

#### create

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


#### get_or_create

`get_or_create(**kwargs) -> Model`

!!!tip
    Read more in queries documentation [get_or_create][get_or_create]

#### update_or_create

`update_or_create(**kwargs) -> Model`

!!!tip
    Read more in queries documentation [update_or_create][update_or_create]

#### filter

`filter(**kwargs) -> QuerySet`

!!!tip
    Read more in queries documentation [filter][filter]

#### exclude

`exclude(**kwargs) -> QuerySet`

!!!tip
    Read more in queries documentation [exclude][exclude]

#### select_related

`select_related(related: Union[List, str]) -> QuerySet`

!!!tip
    Read more in queries documentation [select_related][select_related]

#### prefetch_related

`prefetch_related(related: Union[List, str]) -> QuerySet`

!!!tip
    Read more in queries documentation [prefetch_related][prefetch_related]

#### limit

`limit(limit_count: int) -> QuerySet`

!!!tip
    Read more in queries documentation [limit][limit]

#### offset

`offset(offset: int) -> QuerySet`

!!!tip
    Read more in queries documentation [offset][offset]

#### count

`count() -> int`

!!!tip
    Read more in queries documentation [count][count]

#### exists

`exists() -> bool`

!!!tip
    Read more in queries documentation [exists][exists]

#### fields

`fields(columns: Union[List, str, set, dict]) -> QuerySet`

!!!tip
    Read more in queries documentation [fields][fields]

#### exclude_fields

`exclude_fields(columns: Union[List, str, set, dict]) -> QuerySet`

!!!tip
    Read more in queries documentation [exclude_fields][exclude_fields]

#### order_by

`order_by(columns:Union[List, str]) -> QuerySet`

!!!tip
    Read more in queries documentation [order_by][order_by]


[queries]: ./queries.md
[querysetproxy]: ./relations.md#querysetproxy-methods
[get]: ./queries.md#get
[all]: ./queries.md#all
[create]: ./queries.md#create
[get_or_create]: ./queries.md#get_or_create
[update_or_create]: ./queries.md#update_or_create
[filter]: ./queries.md#filter
[exclude]: ./queries.md#exclude
[select_related]: ./queries.md#select_related
[prefetch_related]: ./queries.md#prefetch_related
[limit]: ./queries.md#limit
[offset]: ./queries.md#offset
[count]: ./queries.md#count
[exists]: ./queries.md#exists
[fields]: ./queries.md#fields
[exclude_fields]: ./queries.md#exclude_fields
[order_by]: ./queries.md#order_by