# Inheritance

Out of various types of ORM models inheritance `ormar` currently supports two of them:

* **Mixins**
* **Concrete table inheritance** (with parents set to `abstract=True`)

## Types of inheritance

The short summary of different types of inheritance is:

* **Mixins [SUPPORTED]** - don't subclass `ormar.Model`, just define fields that are later used on different models (like `created_date` and `updated_date` on each model), only actual models create tables, but those fields from mixins are added
* **Concrete table inheritance [SUPPORTED]** - means that parent is marked as abstract and each child has it's own table with columns from parent and own child columns, kind of similar to Mixins but parent also is a Model
* **Single table inheritance [NOT SUPPORTED]** - means that only one table is created with fields that are combination/sum of the parent and all children models but child models use only subset of column in db (all parent and own ones, skipping the other children ones)
* **Multi/ Joined table inheritance [NOT SUPPORTED]** - means that part of the columns is saved on parent model and part is saved on child model that are connected to each other by kind of one to one relation and under the hood you operate on two models at once
* **Proxy models [NOT SUPPORTED]** - means that only parent has an actual table, children just add methods, modify settings etc.

## Mixins

To use Mixins just define a class that is not inheriting from an `ormar.Model` but is defining `ormar.Fields` as class variables.

```python
# a mixin defines the fields but is a normal python class 
class AuditMixin:
    created_by: str = ormar.String(max_length=100)
    updated_by: str = ormar.String(max_length=100, default="Sam")

class DateFieldsMixins:
    created_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)
    updated_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)


# a models can inherit from one or more mixins
class Category(ormar.Model, DateFieldsMixins, AuditMixin):
    class Meta(ormar.ModelMeta):
        tablename = "categories"
        metadata = metadata
        database = db

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)
    code: int = ormar.Integer()
```

!!!note
    Note that Mixins are **not** models, so you still need to inherit from `ormar.Model` as well as define `Meta` class in the final model.

A Category class above will have four additional fields: `created_date`, `updated_date`, `created_by` and `updated_by`.

There will be only one table created for model Category, with `Category` class fields combined with all `Mixins` fields.

Note that Mixin in class name is optional but is a good python practice.

!!!warning
    You cannot declare a field in a `Model` that is already defined in one of the `Mixins` you inherit from.
    
    So in example above `Category` cannot declare it's own `created_date` as this filed will be inherited from `DateFieldsMixins`.
    
    If you try to the `ModelDefinitionError` will be raised.

## Concrete table inheritance

In concept concrete table inheritance is very similar to Mixins, but uses actual `ormar.Models` as base classes.

!!!warning
    Note that base classes have `abstract=True` set in `Meta` class, if you try to inherit from non abstract marked class `ModelDefinitionError` will be raised.

Since this abstract Model will never be initialized you can skip `metadata` and `database` in it's `Meta` definition.

But if you provide it - it will be inherited, that way you do not have to provide `metadata` and `databases` in concrete class

Note that you can always overwrite it in child/concrete class if you need to. 

More over at least one of the classes in inheritance chain have to provide it - otherwise an error will be raised.

```python
# note that base classes have abstract=True
# since this model will never be initialized you can skip metadata and database
class AuditModel(ormar.Model):
    class Meta:
        abstract = True

    created_by: str = ormar.String(max_length=100)
    updated_by: str = ormar.String(max_length=100, default="Sam")

# but if you provide it it will be inherited - DRY (Don't Repeat Yourself) in action
class DateFieldsModel(ormar.Model):
    class Meta:
        abstract = True
        metadata = metadata
        database = db

    created_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)
    updated_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)


# that way you do not have to provide metadata and databases in concrete class
class Category(DateFieldsModel, AuditModel):
    class Meta(ormar.ModelMeta):
        tablename = "categories"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)
    code: int = ormar.Integer()

```

The list of inherited options/settings is as follows: `metadata`, `database` and `constraints`. 

Also methods decorated with `@property_field` decorator will be inherited/recognized.

Of course apart from that all fields from base classes are combined and created in the concrete table of the final Model.

!!!warning
    You cannot declare a field in a `Model` that is already defined in one of the `Mixins` you inherit from.
    
    So in example above `Category` cannot declare it's own `created_date` as this filed will be inherited from `DateFieldsMixins`.
    
    If you try to the `ModelDefinitionError` will be raised.

## Redefining fields in subclasses

Note that you can redefine previously created fields like in normal python class inheritance.

Whenever you define a field with same name and new definition it will completely replace the previously defined one.

```python
# base class
class DateFieldsModel(ormar.Model):
    class Meta:
        abstract = True
        metadata = metadata
        database = db
        # note that UniqueColumns need sqlalchemy db columns names not the ormar one
        constraints = [ormar.UniqueColumns("creation_date", "modification_date")]

    created_date: datetime.datetime = ormar.DateTime(
        default=datetime.datetime.now, name="creation_date"
    )
    updated_date: datetime.datetime = ormar.DateTime(
        default=datetime.datetime.now, name="modification_date"
    )

class RedefinedField(DateFieldsModel):
    class Meta(ormar.ModelMeta):
        tablename = "redefines"
        metadata = metadata
        database = db

    id: int = ormar.Integer(primary_key=True)
    # here the created_date is replaced by the String field
    created_date: str = ormar.String(max_length=200, name="creation_date")

    
# you can verify that the final field is correctly declared and created
changed_field = RedefinedField.Meta.model_fields["created_date"]
assert changed_field.default is None
assert changed_field.alias == "creation_date"
assert any(x.name == "creation_date" for x in RedefinedField.Meta.table.columns)
assert isinstance(
    RedefinedField.Meta.table.columns["creation_date"].type,
    sqlalchemy.sql.sqltypes.String,
)
```

!!!warning
    If you declare `UniqueColumns` constraint with column names, the final model **has to have**
    a column with the same name declared. Otherwise, the `ModelDefinitionError` will be raised.
    
    So in example above if you do not provide `name` for `created_date` in `RedefinedField` model
    ormar will complain.
    
    `created_date: str = ormar.String(max_length=200) # exception`
    
    `created_date: str = ormar.String(max_length=200, name="creation_date2") # exception`


## Relations in inheritance

You can declare relations in every step of inheritance, so both in parent and child classes.

But you always need to be aware of related_name parameter, that has to be unique across a model, 
when you define multiple child classes that inherit the same relation.


