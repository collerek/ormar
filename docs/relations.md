# Relations

## Defining a relationship

### ForeignKey

`ForeignKey(to, related_name=None)` has required parameters `to` that takes target `Model` class.  

Sqlalchemy column and Type are automatically taken from target `Model`.

* Sqlalchemy column: class of a target `Model` primary key column  
* Type (used for pydantic): type of a target `Model` 

#### Defining Models

To define a relation add `ForeignKey` field that points to related `Model`.

```Python hl_lines="27"
--8<-- "../docs_src/fields/docs003.py"
```

#### Reverse Relation

`ForeignKey` fields are automatically registering reverse side of the relation.

By default it's child (source) `Model` name + s, like courses in snippet below: 

```Python hl_lines="27 33"
--8<-- "../docs_src/fields/docs001.py"
```

#### related_name

But you can overwrite this name by providing `related_name` parameter like below:

```Python hl_lines="27 33"
--8<-- "../docs_src/fields/docs002.py"
```

!!!tip
    The reverse relation on access returns list of `wekref.proxy` to avoid circular references.
    

### Relation Setup

You have several ways to set-up a relationship connection.

#### `Model` instance

The most obvious one is to pass a related `Model` instance to the constructor.

```Python hl_lines="32-33"
--8<-- "../docs_src/relations/docs001.py"
```

#### Primary key value

You can setup the relation also with just the pk column value of the related model.

```Python hl_lines="35-36"
--8<-- "../docs_src/relations/docs001.py"
```

#### Dictionary

Next option is with a dictionary of key-values of the related model.

You can build the dictionary yourself or get it from existing model with `dict()` method.

```Python hl_lines="38-39"
--8<-- "../docs_src/relations/docs001.py"
```

#### None

Finally you can explicitly set it to None (default behavior if no value passed).

```Python hl_lines="41-42"
--8<-- "../docs_src/relations/docs001.py"
```

!!!warning
    In all not None cases the primary key value for related model **has to exist in database**.
    
    Otherwise an IntegrityError will be raised by your database driver library.


### Many2Many

`Many2Many(to, through)` has required parameters `to` and `through` that takes target and relation `Model` classes.  

Sqlalchemy column and Type are automatically taken from target `Model`.

* Sqlalchemy column: class of a target `Model` primary key column  
* Type (used for pydantic): type of a target `Model` 

####Defining `Models`:

```Python
--8<-- "../docs_src/relations/docs002.py"
```

Create sample data:
```Python
guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
post = await Post.objects.create(title="Hello, M2M", author=guido)
news = await Category.objects.create(name="News")
```

#### Adding related models

```python
# Add a category to a post.
await post.categories.add(news)
# or from the other end:
await news.posts.add(post)
```

!!!warning
    In all not None cases the primary key value for related model **has to exist in database**.
    
    Otherwise an IntegrityError will be raised by your database driver library.

#### Creating new related `Model` instances

```python
# Creating columns object from instance:
await post.categories.create(name="Tips")
assert len(await post.categories.all()) == 2
# newly created instance already have relation persisted in the database
```

!!!note
    Note that when accessing QuerySet API methods through Many2Many relation you don't 
    need to use objects attribute like in normal queries.
    
    To learn more about available QuerySet methods visit [queries][queries]

#### Removing related models
```python
# Removal of the relationship by one
await news.posts.remove(post)
# or all at once
await news.posts.clear()
```

#### All other queryset methods

When access directly the related `Many2Many` field returns the list of related models.

But at the same time it exposes full QuerySet API, so you can filter, create, select related etc.

```python
# Many to many relation exposes a list of columns models
# and an API of the Queryset:
assert news == await post.categories.get(name="News")

# with all Queryset methods - filtering, selecting columns, counting etc.
await news.posts.filter(title__contains="M2M").all()
await Category.objects.filter(posts__author=guido).get()

# columns models of many to many relation can be prefetched
news_posts = await news.posts.select_related("author").all()
assert news_posts[0].author == guido
```

!!!tip
    To learn more about available QuerySet methods visit [queries][queries]

[queries]: ./queries.md