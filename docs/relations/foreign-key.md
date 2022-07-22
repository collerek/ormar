# ForeignKey

`ForeignKey(to: Model, *, name: str = None, unique: bool = False, nullable: bool = True,
related_name: str = None, virtual: bool = False, onupdate: Union[ReferentialAction, str] = None,
ondelete: Union[ReferentialAction, str] = None, **kwargs: Any)`
has required parameters `to` that takes target `Model` class.  

Sqlalchemy column and Type are automatically taken from target `Model`.

* Sqlalchemy column: class of a target `Model` primary key column  
* Type (used for pydantic): type of a target `Model` 

## Defining Models

To define a relation add `ForeignKey` field that points to related `Model`.

```Python hl_lines="29"
--8<-- "../docs_src/fields/docs003.py"
```

## Reverse Relation

`ForeignKey` fields are automatically registering reverse side of the relation.

By default it's child (source) `Model` name + s, like courses in snippet below: 

```Python hl_lines="29 35"
--8<-- "../docs_src/fields/docs001.py"
```

Reverse relation exposes API to manage related objects also from parent side.

### Skipping reverse relation

If you are sure you don't want the reverse relation you can use `skip_reverse=True` 
flag of the `ForeignKey`.

  If you set `skip_reverse` flag internally the field is still registered on the other 
  side of the relationship so you can:
  * `filter` by related models fields from reverse model
  * `order_by` by related models fields from reverse model 
  
  But you cannot:
  * access the related field from reverse model with `related_name`
  * even if you `select_related` from reverse side of the model the returned models won't be populated in reversed instance (the join is not prevented so you still can `filter` and `order_by` over the relation)
  * the relation won't be populated in `dict()` and `json()`
  * you cannot pass the nested related objects when populating from dictionary or json (also through `fastapi`). It will be either ignored or error will be raised depending on `extra` setting in pydantic `Config`.

Example:

```python
class Author(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    first_name: str = ormar.String(max_length=80)
    last_name: str = ormar.String(max_length=80)


class Post(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    author: Optional[Author] = ormar.ForeignKey(Author, skip_reverse=True)

# create sample data
author = Author(first_name="Test", last_name="Author")
post = Post(title="Test Post", author=author)

assert post.author == author  # ok
assert author.posts  # Attribute error!

# but still can use in order_by
authors = (
    await Author.objects.select_related("posts").order_by("posts__title").all()
)
assert authors[0].first_name == "Test"

# note that posts are not populated for author even if explicitly
# included in select_related - note no posts in dict()
assert author.dict(exclude={"id"}) == {"first_name": "Test", "last_name": "Author"}

# still can filter through fields of related model
authors = await Author.objects.filter(posts__title="Test Post").all()
assert authors[0].first_name == "Test"
assert len(authors) == 1
```


### add

Adding child model from parent side causes adding related model to currently loaded parent relation, 
as well as sets child's model foreign key value and updates the model.

```python
department = await Department(name="Science").save()
course = Course(name="Math", completed=False) # note - not saved

await department.courses.add(course)
assert course.pk is not None # child model was saved
# relation on child model is set and FK column saved in db
assert course.department == department
# relation on parent model is also set
assert department.courses[0] == course 
```

!!!warning
    If you want to add child model on related model the primary key value for parent model **has to exist in database**.
    
    Otherwise ormar will raise RelationshipInstanceError as it cannot set child's ForeignKey column value 
    if parent model has no primary key value.
    
    That means that in example above the department has to be saved before you can call `department.courses.add()`.

!!!warning
    This method will not work on `ManyToMany` relations - there, both sides of the relation have to be saved before adding to relation.
    

### remove

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

### clear

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

## QuerysetProxy

Reverse relation exposes QuerysetProxy API that allows you to query related model like you would issue a normal Query.

To read which methods of QuerySet are available read below [querysetproxy][querysetproxy]

## related_name

But you can overwrite this name by providing `related_name` parameter like below:

```Python hl_lines="29 35"
--8<-- "../docs_src/fields/docs002.py"
```

!!!tip
    The reverse relation on access returns list of `wekref.proxy` to avoid circular references.

!!!warning
    When you provide multiple relations to the same model `ormar` can no longer auto generate
    the `related_name` for you. Therefore, in that situation you **have to** provide `related_name`
    for all but one (one can be default and generated) or all related fields.

## Referential Actions

When an object referenced by a ForeignKey is changed (deleted or updated),
ormar will set the SQL constraint specified by the `ondelete` and `onupdate` argument.

The possible values for `ondelete` and `onupdate` are found in `ormar.ReferentialAction`:

!!!note
    Instead of `ormar.ReferentialAction`, you can directly pass string values to these two arguments, but this is not recommended because it will break the integrity.

### CASCADE

Whenever rows in the parent (referenced) table are deleted (or updated), the respective rows of the child (referencing) table with a matching foreign key column will be deleted (or updated) as well. This is called a cascade delete (or update).

### RESTRICT

A value cannot be updated or deleted when a row exists in a referencing or child table that references the value in the referenced table.

Similarly, a row cannot be deleted as long as there is a reference to it from a referencing or child table.

### SET_NULL

Set the ForeignKey to `None`; this is only possible if `nullable` is True.

### SET_DEFAULT

Set the ForeignKey to its default value; a `server_default` for the ForeignKey must be set.

!!!note
      Note that the `default` value is not allowed and you must do this through `server_default`, which you can read about in [this section][server_default].

### DO_NOTHING

Take `NO ACTION`; NO ACTION and RESTRICT are very much alike. The main difference between NO ACTION and RESTRICT is that with NO ACTION the referential integrity check is done after trying to alter the table. RESTRICT does the check before trying to execute the UPDATE or DELETE statement. Both referential actions act the same if the referential integrity check fails: the UPDATE or DELETE statement will result in an error.

## Relation Setup

You have several ways to set-up a relationship connection.

### `Model` instance

The most obvious one is to pass a related `Model` instance to the constructor.

```Python hl_lines="34-35"
--8<-- "../docs_src/relations/docs001.py"
```

### Primary key value

You can setup the relation also with just the pk column value of the related model.

```Python hl_lines="37-38"
--8<-- "../docs_src/relations/docs001.py"
```

### Dictionary

Next option is with a dictionary of key-values of the related model.

You can build the dictionary yourself or get it from existing model with `dict()` method.

```Python hl_lines="40-41"
--8<-- "../docs_src/relations/docs001.py"
```

### None

Finally you can explicitly set it to None (default behavior if no value passed).

```Python hl_lines="43-44"
--8<-- "../docs_src/relations/docs001.py"
```

!!!warning
    In all not None cases the primary key value for related model **has to exist in database**.
    
    Otherwise an IntegrityError will be raised by your database driver library.

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
[server_default]: ../fields/common-parameters.md#server-default