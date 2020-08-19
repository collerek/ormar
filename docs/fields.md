# Fields


There are 11 basic model field types and a special `ForeignKey` field to establish relationships between models.

Each of the `Fields` has assigned both `sqlalchemy` column class and python type that is used to create `pydantic` model.


## Common Parameters

All `Field` types have a set of common parameters.

### primary_key

`primary_key`: `bool` = `False` -> by default False.

Sets the primary key column on a table, foreign keys always refer to the pk of the `Model`.

Used in sql only.

### autoincrement

`autoincrement`: `bool` = `primary_key and type == int` -> defaults to True if column is a primary key and of type Integer, otherwise False.

Can be only used with int fields.

If a field has autoincrement it becomes optional.

Used only in sql.

### nullable

`nullable`: `bool` = `not primary_key` -> defaults to False for primary key column, and True for all other. 

Specifies if field is optional or required, used both with sql and pydantic.

!!!note
    By default all `ForeignKeys` are also nullable, meaning the related `Model` is not required.
    
    If you change the `ForeignKey` column to `nullable`, it not only becomes required, it changes also the way in which data is loaded in queries.
    
    If you select `Model` without explicitly adding related `Model` assigned by not nullable `ForeignKey`, the `Model` is still gona be appended automatically, see example below.

```Python hl_lines="24 32 33 34 35 37 38 39 40 41"
--8<-- "../docs_src/fields/docs003.py"
```

!!!info
    If you want to know more about how you can preload related models during queries and how the relations work read the [queries][queries] and [relations][relations] sections. 


### default

`default`: `Any` = `None` -> defaults to None. 

A default value used if no other value is passed.

In sql invoked on an insert, used during pydantic model definition.

If the field has a default value it becomes optional.

You can pass a static value or a Callable (function etc.)

Used both in sql and pydantic.

### server default

`server_default`: `Any` = `None`  -> defaults to None. 

A default value used if no other value is passed.

In sql invoked on the server side so you can pass i.e. sql function (like now() wrapped in sqlalchemy text() clause).

If the field has a server_default value it becomes optional.

You can pass a static value or a Callable (function etc.)

Used in sql only.
 
### index

`index`: `bool` = `False` -> by default False, 

Sets the index on a table's column.

Used in sql only.

### unique

`unique`: `bool` = `False` 

Sets the unique constraint on a table's column.

Used in sql only.

## Fields Types

### String

`String(length)` has a required `length` parameter.  

* Sqlalchemy column: `sqlalchemy.String`  
* Type (used for pydantic): `str` 

### Text

`Text()` has no required parameters.  

* Sqlalchemy column: `sqlalchemy.Text`  
* Type (used for pydantic): `str` 

### Boolean

`Boolean()` has no required parameters.  

* Sqlalchemy column: `sqlalchemy.Boolean`  
* Type (used for pydantic): `bool` 

### Integer

`Integer()` has no required parameters.  

* Sqlalchemy column: `sqlalchemy.Integer`  
* Type (used for pydantic): `int` 

### BigInteger

`BigInteger()` has no required parameters.  

* Sqlalchemy column: `sqlalchemy.BigInteger`  
* Type (used for pydantic): `int` 

### Float

`Float()` has no required parameters.  

* Sqlalchemy column: `sqlalchemy.Float`  
* Type (used for pydantic): `float` 

### Decimal

`Decimal(lenght, precision)` has required `length` and `precision` parameters.  

* Sqlalchemy column: `sqlalchemy.DECIMAL`  
* Type (used for pydantic): `decimal.Decimal` 

### Date

`Date()` has no required parameters.  

* Sqlalchemy column: `sqlalchemy.Date`  
* Type (used for pydantic): `datetime.date` 

### Time

`Time()` has no required parameters.  

* Sqlalchemy column: `sqlalchemy.Time`  
* Type (used for pydantic): `datetime.time` 

### DateTime

`DateTime()` has no required parameters.  

* Sqlalchemy column: `sqlalchemy.DateTime`  
* Type (used for pydantic): `datetime.datetime` 

### JSON

`JSON()` has no required parameters.  

* Sqlalchemy column: `sqlalchemy.JSON`  
* Type (used for pydantic): `pydantic.Json` 

### ForeignKey

`ForeignKey(to, related_name=None)` has required parameters `to` that takes target `Model` class.  

Sqlalchemy column and Type are automatically taken from target `Model`.

* Sqlalchemy column: class of a target `Model` primary key column  
* Type (used for pydantic): type of a target `Model` primary key column 

`ForeignKey` fields are automatically registering reverse side of the relation.

By default it's child (source) `Model` name + s, like courses in snippet below: 

```Python hl_lines="25 31"
--8<-- "../docs_src/fields/docs001.py"
```

But you can overwrite this name by providing `related_name` parameter like below:

```Python hl_lines="25 30"
--8<-- "../docs_src/fields/docs002.py"
```

!!!tip
    Since related models are coming from Relationship Manager the reverse relation on access returns list of `wekref.proxy` to avoid circular references.

!!!info
    All relations are stored in lists, but when you access parent `Model` the ormar is unpacking the value for you. 
    Read more in [relations][relations].

[relations]: ./relations.md
[queries]: ./queries.md