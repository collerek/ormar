# ForeignKey

`ForeignKey(to, related_name=None)` has required parameters `to` that takes target `Model` class.  

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

### add

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