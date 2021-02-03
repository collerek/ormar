# Fields


There are 12 basic model field types and a special `ForeignKey` and `Many2Many` fields to establish relationships between models.

!!!tip
    For explanation of `ForeignKey` and `Many2Many` fields check [relations][relations].


Each of the `Fields` has assigned both `sqlalchemy` column class and python type that is used to create `pydantic` model.


## Fields Types

### String

`String(max_length, 
        allow_blank: bool = True,
        strip_whitespace: bool = False,
        min_length: int = None,
        max_length: int = None,
        curtail_length: int = None,
        regex: str = None,)` has a required `max_length` parameter.  

* Sqlalchemy column: `sqlalchemy.String`  
* Type (used for pydantic): `str` 

!!!tip
    For explanation of other parameters check [pydantic][pydantic] documentation.

### Text

`Text(allow_blank: bool = True, strip_whitespace: bool = False)` has no required parameters.  

* Sqlalchemy column: `sqlalchemy.Text`  
* Type (used for pydantic): `str` 

!!!tip
    For explanation of other parameters check [pydantic][pydantic] documentation.

### Boolean

`Boolean()` has no required parameters.  

* Sqlalchemy column: `sqlalchemy.Boolean`  
* Type (used for pydantic): `bool` 

### Integer

`Integer(minimum: int = None,
        maximum: int = None,
        multiple_of: int = None)` has no required parameters.  

* Sqlalchemy column: `sqlalchemy.Integer`  
* Type (used for pydantic): `int` 

!!!tip
    For explanation of other parameters check [pydantic][pydantic] documentation.

### BigInteger

`BigInteger(minimum: int = None,
        maximum: int = None,
        multiple_of: int = None)` has no required parameters.  

* Sqlalchemy column: `sqlalchemy.BigInteger`  
* Type (used for pydantic): `int` 

!!!tip
    For explanation of other parameters check [pydantic][pydantic] documentation.

### Float

`Float(minimum: float = None,
        maximum: float = None,
        multiple_of: int = None)` has no required parameters.  

* Sqlalchemy column: `sqlalchemy.Float`  
* Type (used for pydantic): `float` 

!!!tip
    For explanation of other parameters check [pydantic][pydantic] documentation.

### Decimal

`Decimal(minimum: float = None,
        maximum: float = None,
        multiple_of: int = None,
        precision: int = None,
        scale: int = None,
        max_digits: int = None,
        decimal_places: int = None)` has no required parameters
        
You can use either `length` and `precision` parameters or `max_digits` and `decimal_places`.  

* Sqlalchemy column: `sqlalchemy.DECIMAL`  
* Type (used for pydantic): `decimal.Decimal` 

!!!tip
    For explanation of other parameters check [pydantic][pydantic] documentation.

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

### UUID

`UUID(uuid_format: str = 'hex')` has no required parameters.  

* Sqlalchemy column: `ormar.UUID` based on `sqlalchemy.CHAR(36)` or `sqlalchemy.CHAR(32)` field (for string or hex format respectively)  
* Type (used for pydantic): `uuid.UUID` 

`uuid_format` parameters allow 'hex'(default) or 'string' values.

Depending on the format either 32 or 36 char is used in the database.

Sample:

*  'hex' format value = `c616ab438cce49dbbf4380d109251dce` (CHAR(32))
*  'string' value = `c616ab43-8cce-49db-bf43-80d109251dce` (CHAR(36))  

When loaded it's always python UUID so you can compare it and compare two formats values between each other.

### Enum

Although there is no dedicated field type for Enums in `ormar` you can change any
field into `Enum` like field by passing a `choices` list that is accepted by all Field types.

It will add both: validation in `pydantic` model and will display available options in schema,
therefore it will be available in docs of `fastapi`.

If you still want to use `Enum` in your application you can do this by passing a `Enum` into choices
and later pass value of given option to a given field (note tha Enum is not JsonSerializable).

```python
# not that imports and endpoints declaration 
# is skipped here for brevity
from enum import Enum
class TestEnum(Enum):
    val1 = 'Val1'
    val2 = 'Val2'

class TestModel(ormar.Model):
    class Meta:
        tablename = "org"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    # pass list(Enum) to choices
    enum_string: str = ormar.String(max_length=100, choices=list(TestEnum))

# sample payload coming to fastapi
response = client.post(
    "/test_models/",
    json={
        "id": 1,
        # you need to refer to the value of the `Enum` option
        # if called like this, alternatively just use value
        # string "Val1" in this case
        "enum_string": TestEnum.val1.value
    },
)

```

[relations]: ../relations/index.md
[queries]: ../queries.md
[pydantic]: https://pydantic-docs.helpmanual.io/usage/types/#constrained-types
[server default]: https://docs.sqlalchemy.org/en/13/core/defaults.html#server-invoked-ddl-explicit-default-expressions