
The use of ormar with fastapi is quite simple.

Apart from connecting to databases at startup everything else 
you need to do is substitute pydantic models with ormar models.

Here you can find a very simple sample application code.

## Imports and initialization 

First take care of the imports and initialization 
```python hl_lines="1-12"
--8<-- "../docs_src/fastapi/docs001.py"
```

## Database connection 

Next define startup and shutdown events (or use middleware)
- note that this is `databases` specific setting not the ormar one
```python hl_lines="15-26"
--8<-- "../docs_src/fastapi/docs001.py"
```

!!!info
    You can read more on connecting to databases in [fastapi][fastapi] documentation

## Models definition 

Define ormar models with appropriate fields. 

Those models will be used insted of pydantic ones.
```python hl_lines="29-47"
--8<-- "../docs_src/fastapi/docs001.py"
```

!!!tip
    You can read more on defining `Models` in [models][models] section.

## Fastapi endpoints definition

Define your desired endpoints, note how `ormar` models are used both 
as `response_model` and as a requests parameters.

```python hl_lines="50-77"
--8<-- "../docs_src/fastapi/docs001.py"
```

!!!note
    Note how ormar `Model` methods like save() are available straight out of the box after fastapi initializes it for you.

!!!note
    Note that you can return a `Model` (or list of `Models`) directly - fastapi will jsonize it for you

## Test the application

Here you have a sample test that will prove that everything works as intended.

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
        response = client.put(f"/items/{item.pk}", json=item.dict())
        assert response.json() == item.dict()

        response = client.get("/items/")
        items = [Item(**item) for item in response.json()]
        assert items[0].name == "New name"

        response = client.delete(f"/items/{item.pk}", json=item.dict())
        assert response.json().get("deleted_rows", "__UNDEFINED__") != "__UNDEFINED__"
        response = client.get("/items/")
        items = response.json()
        assert len(items) == 0
```

!!!info
    You can read more on testing fastapi in [fastapi][fastapi] docs. 

[fastapi]: https://fastapi.tiangolo.com/
[models]: ./models.md