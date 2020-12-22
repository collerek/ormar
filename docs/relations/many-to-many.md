# ManyToMany

`ManyToMany(to, through)` has required parameters `to` and `through` that takes target and relation `Model` classes.  

Sqlalchemy column and Type are automatically taken from target `Model`.

* Sqlalchemy column: class of a target `Model` primary key column  
* Type (used for pydantic): type of a target `Model` 

## Defining Models

```Python hl_lines="32 49-50"
--8<-- "../docs_src/relations/docs002.py"
```

Create sample data:
```Python
guido = await Author.objects.create(first_name="Guido", last_name="Van Rossum")
post = await Post.objects.create(title="Hello, M2M", author=guido)
news = await Category.objects.create(name="News")
```

### add

```python
# Add a category to a post.
await post.categories.add(news)
# or from the other end:
await news.posts.add(post)
```

!!!warning
    In all not None cases the primary key value for related model **has to exist in database**.
    
    Otherwise an IntegrityError will be raised by your database driver library.

### remove

Removal of the related model one by one.

Removes also the relation in the database.

```python
await news.posts.remove(post)
```

### clear

Removal of all related models in one call.

Removes also the relation in the database.

```python
await news.posts.clear()
```

### QuerysetProxy

Reverse relation exposes QuerysetProxy API that allows you to query related model like you would issue a normal Query.

To read which methods of QuerySet are available read below [querysetproxy][querysetproxy]

## related_name

By default, the related_name is generated in the same way as for the `ForeignKey` relation (class.name.lower()+'s'), 
but in the same way you can overwrite this name by providing `related_name` parameter like below:

```Python
categories: Optional[Union[Category, List[Category]]] = ormar.ManyToMany(
        Category, through=PostCategory, related_name="new_categories"
    )
```

!!!warning
    When you provide multiple relations to the same model `ormar` can no longer auto generate
    the `related_name` for you. Therefore, in that situation you **have to** provide `related_name`
    for all but one (one can be default and generated) or all related fields.


[queries]: ./queries.md
[querysetproxy]: ./queryset-proxy.md
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