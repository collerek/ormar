# Pydantic only fields

Ormar allows you to declare normal `pydantic` fields in its model, so you have access to
all basic and custom pydantic fields like `str`, `int`, `HttpUrl`, `PaymentCardNumber` etc.

You can even declare fields leading to nested pydantic only Models, not only single fields.

Since those fields are not stored in database (that's the whole point of those fields),
you have to provide a meaningful value for them, either by setting a default one or 
providing one during model initialization.

If `ormar` cannot resolve the value for pydantic field it will fail during loading data from the database,
with missing required value for declared pydantic field.

Options to provide a value are described below.

Of course you can combine few or all of them in one model.

## Optional field

If you set a field as `Optional`, it defaults to `None` if not provided and that's 
exactly what's going to happen during loading from database.

```python
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database
    
class ModelTest(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200)
    number: Optional[PaymentCardNumber]

test = ModelTest(name="Test")
assert test.name == "Test"
assert test.number is None
test.number = "123456789015"

await test.save()
test_check = await ModelTest.objects.get()

assert test_check.name == "Test"
# after load it's back to None
assert test_check.number is None
```

## Field with default value

By setting a default value, this value will be set on initialization and database load. 
Note that setting a default to `None` is the same as setting the field to `Optional`.

```python
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database
    
class ModelTest(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200)
    url: HttpUrl = "https://www.example.com"

test = ModelTest(name="Test")
assert test.name == "Test"
assert test.url == "https://www.example.com"

test.url = "https://www.sdta.ada.pt"
assert test.url == "https://www.sdta.ada.pt"

await test.save()
test_check = await ModelTest.objects.get()

assert test_check.name == "Test"
# after load it's back to default
assert test_check.url == "https://www.example.com"
```

## Default factory function

By setting a `default_factory` function, this result of the function call will be set 
on initialization and each database load.

```python
from pydantic import Field, PaymentCardNumber
# ...

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database

CARD_NUMBERS = [
    "123456789007",
    "123456789015",
    "123456789023",
    "123456789031",
    "123456789049",
]


def get_number():
    return random.choice(CARD_NUMBERS)


class ModelTest2(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200)
    # note that you do not call the function, just pass reference
    number: PaymentCardNumber = Field(default_factory=get_number)

# note that you still CAN provide a value 
test = ModelTest2(name="Test2", number="4000000000000002")
assert test.name == "Test2"
assert test.number == "4000000000000002"

await test.save()
test_check = await ModelTest2.objects.get()

assert test_check.name == "Test2"
# after load value is set to be one of the CARD_NUMBERS
assert test_check.number in CARD_NUMBERS
assert test_check.number != test.number
```

## Custom setup in `__init__`

You can provide a value for the field in your `__init__()` method before calling a `super()` init method.

```python
from pydantic import BaseModel
# ...

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database

class PydanticTest(BaseModel):
    aa: str
    bb: int


class ModelTest3(ormar.Model):
    class Meta(BaseMeta):
        pass

    # provide your custom init function
    def __init__(self, **kwargs):
        # add value for required field without default value
        kwargs["pydantic_test"] = PydanticTest(aa="random", bb=42)
        # remember to call ormar.Model init!
        super().__init__(**kwargs)

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=200)
    pydantic_test: PydanticTest

test = ModelTest3(name="Test3")
assert test.name == "Test3"
assert test.pydantic_test.bb == 42
test.pydantic.aa = "new value"
assert test.pydantic.aa == "new value"

await test.save()
test_check = await ModelTest3.objects.get()

assert test_check.name == "Test3"
# after load it's back to value provided in init
assert test_check.pydantic_test.aa == "random"
```

!!!warning
        If you do not provide a value in one of the above ways `ValidationError` will be raised on load from database.