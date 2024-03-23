# Postponed annotations

## Self-referencing Models

When you want to reference the same model during declaration to create a 
relation you need to declare the referenced model as a `ForwardRef`, as during the declaration
the class is not yet ready and python by default won't let you reference it.

Although you might be tempted to use __future__ annotations or simply quote the name with `""` it won't work
as `ormar` is designed to work with explicitly declared `ForwardRef`.

First, you need to import the required ref from typing.
```python
from typing import ForwardRef
```

Now we need a sample model and a reference to the same model, 
which will be used to create a self referencing relation.

```python
# create the forwardref to model Person
PersonRef = ForwardRef("Person")


class Person(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    # use the forwardref as to parameter
    supervisor: PersonRef = ormar.ForeignKey(PersonRef, related_name="employees")

```

That's so simple. But before you can use the model you need to manually update the references
so that they lead to the actual models.

!!!warning
    If you try to use the model without updated references, `ModelError` exception will be raised.
    So in our example above any call like following will cause exception
    ```python
    # creation of model - exception
    await Person.objects.create(name="Test")
    # initialization of model - exception
    Person2(name="Test")
    # usage of model's QuerySet - exception
    await Person2.objects.get()
    ```

To update the references call the `update_forward_refs` method on **each model** 
with forward references, only **after all related models were declared.**

So in order to make our previous example work we need just one extra line.

```python hl_lines="14"
PersonRef = ForwardRef("Person")


class Person(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    supervisor: PersonRef = ormar.ForeignKey(PersonRef, related_name="employees")


Person.update_forward_refs()

```

Of course the same can be done with ManyToMany relations in exactly same way, both for to
and through parameters.

```python
# declare the reference
ChildRef = ForwardRef("Child")

class ChildFriend(ormar.Model):
    ormar_config = base_ormar_config.copy()

class Child(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    # use it in relation
    friends = ormar.ManyToMany(ChildRef, through=ChildFriend,
                               related_name="also_friends")


Child.update_forward_refs()
```

## Cross model relations

The same mechanism and logic as for self-reference model can be used to link multiple different
models between each other.

Of course `ormar` links both sides of relation for you, 
creating a reverse relation with specified (or default) `related_name`.

But if you need two (or more) relations between any two models, that for whatever reason
should be stored on both sides (so one relation is declared on one model, 
and other on the second model), you need to use `ForwardRef` to achieve that.

Look at the following simple example.

```python
# teacher is not yet defined
TeacherRef = ForwardRef("Teacher")


class Student(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    # so we use reference instead of actual model
    primary_teacher: TeacherRef = ormar.ForeignKey(TeacherRef,
                                                   related_name="own_students")


class StudentTeacher(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename='students_x_teachers')


class Teacher(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    # we need students for other relation hence the order
    students = ormar.ManyToMany(Student, through=StudentTeacher,
                                related_name="teachers")

# now the Teacher model is already defined we can update references
Student.update_forward_refs()

```

!!!warning
    Remember that `related_name` needs to be unique across related models regardless 
    of how many relations are defined. 
