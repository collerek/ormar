# Relations

## Defining a relationship

### Foreign Key

To define a relationship you simply need to create a ForeignKey field on one `Model` and point it to another `Model`.

```Python hl_lines="24"
--8<-- "../docs_src/relations/docs001.py"
```

It automatically creates an sql foreign key constraint on a underlying table as well as nested pydantic model in the definition.


```Python hl_lines="29 33"
--8<-- "../docs_src/relations/docs002.py"
```

Of course it's handled for you so you don't have to delve deep into this but you can.

### Reverse Relation

At the same time the reverse relationship is registered automatically on parent model (target of `ForeignKey`).

By default it's child (source) `Model` name + 's', like courses in snippet below: 

```Python hl_lines="25 31"
--8<-- "../docs_src/fields/docs001.py"
```

But you can overwrite this name by providing `related_name` parameter like below:

```Python hl_lines="25 30"
--8<-- "../docs_src/fields/docs002.py"
```

!!!tip
    Since related models are coming from Relationship Manager the reverse relation on access returns list of `wekref.proxy` to avoid circular references.

## Relationship Manager

Since orm uses Sqlalchemy core under the hood to prepare the queries, 
the orm needs a way to uniquely identify each relationship between to tables to construct working queries.

Imagine that you have models as following:

```Python 
--8<-- "../docs_src/relations/docs003.py"
```

Now imagine that you want to go from school class to student and his category and to teacher and his category.

```Python
classes = await SchoolClass.objects.select_related(
["teachers__category", "students__category"]).all()
```

!!!note
    To select related models use `select_related` method from `Model` `QuerySet`.
    
    Note that you use relation (`ForeignKey`) names and not the table names.

Since you join two times to the same table it won't work by default -> you would need to use aliases for category tables and columns.

But don't worry - orm can handle situations like this, as it uses the Relationship Manager which has it's aliases defined for all relationships.

Each class is registered with the same instance of the RelationshipManager that you can access like this:

```python
SchoolClass._orm_relationship_manager
```

It's the same object for all `Models`

```python
print(Teacher._orm_relationship_manager == Student._orm_relationship_manager)
# will produce: True
```

You can even preview the alias used for any relation by passing two tables names.

```python
print(Teacher._orm_relationship_manager.resolve_relation_join(
'students', 'categories'))
# will produce: KId1c6 (sample value)

print(Teacher._orm_relationship_manager.resolve_relation_join(
'categories', 'students'))
# will produce: EFccd5 (sample value)
```

!!!note
    The order that you pass the names matters -> as those are 2 different relationships depending on join order.
    
    As aliases are produced randomly you can be presented with different results.
