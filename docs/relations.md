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

!!!tip
    Note how by default the relation is optional, you can require the related `Model` by setting `nullable=False` on the `ForeignKey` field.

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

!!!tip
    This section is more technical so you might want to skip it if you are not interested in implementation details.

### Need for a manager?

Since orm uses Sqlalchemy core under the hood to prepare the queries, 
the orm needs a way to uniquely identify each relationship between the tables to construct working queries.

Imagine that you have models as following:

```Python 
--8<-- "../docs_src/relations/docs003.py"
```

Now imagine that you want to go from school class to student and his category and to teacher and his category.

```Python
classes = await SchoolClass.objects.select_related(
["teachers__category", "students__category"]).all()
```

!!!tip
    To query a chain of models use double underscores between the relation names (`ForeignKeys` or reverse `ForeignKeys`)

!!!note
    To select related models use `select_related` method from `Model` `QuerySet`.
    
    Note that you use relation (`ForeignKey`) names and not the table names.

Since you join two times to the same table (categories) it won't work by default -> you would need to use aliases for category tables and columns.

But don't worry - ormar can handle situations like this, as it uses the Relationship Manager which has it's aliases defined for all relationships.

Each class is registered with the same instance of the RelationshipManager that you can access like this:

```python
SchoolClass._orm_relationship_manager
```

It's the same object for all `Models`

```python
print(Teacher._orm_relationship_manager == Student._orm_relationship_manager)
# will produce: True
```

### Table aliases

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

### Query automatic construction

Ormar is using those aliases during queries to both construct a meaningful and valid sql, 
as well as later use it to extract proper columns for proper nested models.

Running a previously mentioned query to select school classes and related teachers and students: 

```Python
classes = await SchoolClass.objects.select_related(
["teachers__category", "students__category"]).all()
```

Will result in a query like this (run under the hood):

```sql
SELECT schoolclasses.id,
       schoolclasses.name,
       schoolclasses.department,
       NZc8e2_students.id          as NZc8e2_id,
       NZc8e2_students.name        as NZc8e2_name,
       NZc8e2_students.schoolclass as NZc8e2_schoolclass,
       NZc8e2_students.category    as NZc8e2_category,
       MYfe53_categories.id        as MYfe53_id,
       MYfe53_categories.name      as MYfe53_name,
       WA49a3_teachers.id          as WA49a3_id,
       WA49a3_teachers.name        as WA49a3_name,
       WA49a3_teachers.schoolclass as WA49a3_schoolclass,
       WA49a3_teachers.category    as WA49a3_category,
       WZa13b_categories.id        as WZa13b_id,
       WZa13b_categories.name      as WZa13b_name
FROM schoolclasses
         LEFT OUTER JOIN students NZc8e2_students ON NZc8e2_students.schoolclass = schoolclasses.id
         LEFT OUTER JOIN categories MYfe53_categories ON MYfe53_categories.id = NZc8e2_students.category
         LEFT OUTER JOIN teachers WA49a3_teachers ON WA49a3_teachers.schoolclass = schoolclasses.id
         LEFT OUTER JOIN categories WZa13b_categories ON WZa13b_categories.id = WA49a3_teachers.category
ORDER BY schoolclasses.id, NZc8e2_students.id, MYfe53_categories.id, WA49a3_teachers.id, WZa13b_categories.id
```

!!!note
    As mentioned before the aliases are produced dynamically so the actual result might differ.
    
    Note that aliases are assigned to relations and not the tables, therefore the first table is always without an alias.

### Returning related Models

Each object in Relationship Manager is identified by orm_id which you can preview like this

```python
category = Category(name='Math')
print(category._orm_id)
# will produce: c76046d9410c4582a656bf12a44c892c (sample value)
```

Each call to related `Model` is actually coming through the Manager which stores all
the relations in a dictionary and returns related `Models` by relation type (name) and by object _orm_id.

Since we register both sides of the relation the side registering the relation 
is always registering the other side as concrete model, 
while the reverse relation is a weakref.proxy to avoid circular references.

Sounds complicated but in reality it means something like this:

```python
test_class = await SchoolClass.objects.create(name='Test')
student = await Student.objects.create(name='John', schoolclass=test_class)
# the relation to schoolsclass from student (i.e. when you call student.schoolclass) 
# is a concrete one, meaning directy relating the schoolclass `Model` object
# On the other side calling test_class.students will result in a list of wekref.proxy objects
```

!!!tip
    To learn more about queries and available methods please review [queries][queries] section.

All relations are kept in lists, meaning that when you access related object the Relationship Manager is
searching itself for related models and get a list of them. 

But since child to parent relation is a many to one type,
the Manager is unpacking the first (and only) related model from a list and you get an actual `Model` instance instead of a list.

Coming from parent to child relation (one to many) you always get a list of results.

Translating this into concrete sample, the same as above:

```python
test_class = await SchoolClass.objects.create(name='Test')
student = await Student.objects.create(name='John', schoolclass=test_class)

student.schoolclass # return a test_class instance extracted from relationship list
test_class.students # return a list of related wekref.proxy refering related students `Models`

``` 

!!!tip
    You can preview all relations currently registered by accessing Relationship Manager on any class/instance `Student._orm_relationship_manager._relations`

[queries]: ./queries.md