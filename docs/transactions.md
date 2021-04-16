# Transactions

Database transactions are supported thanks to `encode/databases` which is used to issue async queries.

## Basic usage

To use transactions use `database.transaction` as async context manager:

```python
async with database.transaction():
    # everyting called here will be one transaction
    await Model1().save()
    await Model2().save()
    ...
```

!!!note
    Note that it has to be the same `database` that the one used in Model's `Meta` class.

To avoid passing `database` instance around in your code you can extract the instance from each `Model`.
Database provided during declaration of `ormar.Model` is available through `Meta.database` and can
be reached from both class and instance.

```python
import databases
import sqlalchemy
import ormar

metadata = sqlalchemy.MetaData()
database = databases.Database("sqlite:///")

class Author(ormar.Model):
    class Meta:
        database=database
        metadata=metadata
    
    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=255)

# database is accessible from class
database = Author.Meta.database

# as well as from instance
author = Author(name="Stephen King")
database = author.Meta.database

```

You can also use `.transaction()` as a function decorator on any async function:

```python
@database.transaction()
async def create_users(request):
    ...
```

Transaction blocks are managed as task-local state. Nested transactions
are fully supported, and are implemented using database savepoints.

## Manual commits/ rollbacks

For a lower-level transaction API you can trigger it manually

```python
transaction = await database.transaction()
try:
    await transaction.start()
    ...
except:
    await transaction.rollback()
else:
    await transaction.commit()
```


## Testing

Transactions can also be useful during testing when you can apply force rollback 
and you do not have to clean the data after each test.

```python
@pytest.mark.asyncio
async def sample_test():
    async with database:
        async with database.transaction(force_rollback=True):
            # your test code here
            ...
```