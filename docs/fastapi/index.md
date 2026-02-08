# Fastapi

The use of ormar with fastapi is quite simple.

Apart from connecting to databases at startup everything else 
you need to do is substitute pydantic models with ormar models.

Here you can find a very simple sample application code.

!!!warning
    This example assumes that you already have a database created. If that is not the case please visit [database initialization][database initialization] section.

!!!tip
    The following example (all sections) should be put in one file.
    
    It's divided into subsections for clarity.

!!!note
    If you want to read more on how you can use ormar models in fastapi requests and 
    responses check the [responses](response.md) and [requests](requests.md) documentation.

## Quick Start

!!!note
    Note that you can find the full quick start script in the [github](https://github.com/collerek/ormar) repo under examples.

### Imports and initialization 

Define startup and shutdown procedures using FastAPI lifespan and use is in the
application.
```python
from typing import List, Optional, AsyncIterator

import sqlalchemy
from fastapi import FastAPI

import ormar
from ormar import DatabaseConnection

from contextlib import asynccontextmanager
from fastapi import FastAPI


def get_lifespan(config):
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if not config.database.is_connected:
            await config.database.connect()

        yield

        if config.database.is_connected:
            await config.database.disconnect()
    return lifespan

base_ormar_config = ormar.OrmarConfig(
    metadata=sqlalchemy.MetaData(),
    database=DatabaseConnection("sqlite+aiosqlite:///test.db"),
)

app = FastAPI(lifespan=get_lifespan(base_ormar_config))
```

!!!info
    You can read more on connecting to databases in [fastapi][fastapi] documentation

### Models definition 

Define ormar models with appropriate fields. 

Those models will be used instead of pydantic ones.

```python
base_ormar_config = OrmarConfig(
    metadata = metadata
    database = database
)


class Category(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Item(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    category: Optional[Category] = ormar.ForeignKey(Category, nullable=True)
```

!!!tip
    You can read more on defining `Models` in [models][models] section.

### Fastapi endpoints definition

Define your desired endpoints, note how `ormar` models are used both 
as `response_model` and as a requests parameters.

```python
@app.get("/items/", response_model=List[Item])
async def get_items():
    items = await Item.objects.select_related("category").all()
    return items


@app.post("/items/", response_model=Item)
async def create_item(item: Item):
    await item.save()
    return item


@app.post("/categories/", response_model=Category)
async def create_category(category: Category):
    await category.save()
    return category


@app.put("/items/{item_id}")
async def get_item(item_id: int, item: Item):
    item_db = await Item.objects.get(pk=item_id)
    return await item_db.update(**item.model_dump())


@app.delete("/items/{item_id}")
async def delete_item(item_id: int, item: Item = None):
    if item:
        return {"deleted_rows": await item.delete()}
    item_db = await Item.objects.get(pk=item_id)
    return {"deleted_rows": await item_db.delete()}

```

!!!note
    Note how ormar `Model` methods like save() are available straight out of the box after fastapi initializes it for you.

!!!note
    Note that you can return a `Model` (or list of `Models`) directly - fastapi will jsonize it for you

### Test the application

#### Run fastapi

If you want to run this script and play with fastapi swagger install uvicorn first

`pip install uvicorn`

And launch the fastapi.

`uvicorn <filename_without_extension>:app --reload`

Now you can navigate to your browser (by default fastapi address is `127.0.0.1:8000/docs`) and play with the api.

!!!info
    You can read more about running fastapi in [fastapi][fastapi] docs. 

#### Test with pytest

Here you have a sample test that will prove that everything works as intended.

Be sure to create the tables first. If you are using pytest you can use a fixture.

```python
@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)
```

```python

# here is a sample test to check the working of the ormar with fastapi

from starlette.testclient import TestClient

def test_all_endpoints():
    # note that TestClient is only sync, don't use asyns here
    client = TestClient(app)
    # note that you need to connect to database manually
    # or use client as contextmanager during tests
    with client as client:
        response = client.post("/categories/", json={"name": "test cat"})
        category = response.json()
        response = client.post(
            "/items/", json={"name": "test", "id": 1, "category": category}
        )
        item = Item(**response.json())
        assert item.pk is not None

        response = client.get("/items/")
        items = [Item(**item) for item in response.json()]
        assert items[0] == item

        item.name = "New name"
        response = client.put(f"/items/{item.pk}", json=item.model_dump())
        assert response.json() == item.model_dump()

        response = client.get("/items/")
        items = [Item(**item) for item in response.json()]
        assert items[0].name == "New name"

        response = client.delete(f"/items/{item.pk}", json=item.model_dump())
        assert response.json().get("deleted_rows", "__UNDEFINED__") != "__UNDEFINED__"
        response = client.get("/items/")
        items = response.json()
        assert len(items) == 0
```

!!!tip
    If you want to see more test cases and how to test ormar/fastapi see [tests][tests] directory in the github repo

!!!info
    You can read more on testing fastapi in [fastapi][fastapi] docs. 

[fastapi]: https://fastapi.tiangolo.com/
[models]: ../models/index.md
[database initialization]:  ../models/migrations.md
[tests]: https://github.com/collerek/ormar/tree/master/tests
