import datetime
from typing import List

import pytest
import sqlalchemy
from fastapi import FastAPI
from starlette.testclient import TestClient

from tests.settings import DATABASE_URL
from tests.test_inheritance_and_pydantic_generation.test_inheritance_concrete import (  # type: ignore
    Category,
    Subject,
    Person,
    Bus,
    Truck,
    Bus2,
    Truck2,
    db as database,
    metadata,
)

app = FastAPI()
app.state.database = database


@app.on_event("startup")
async def startup() -> None:
    database_ = app.state.database
    if not database_.is_connected:
        await database_.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    database_ = app.state.database
    if database_.is_connected:
        await database_.disconnect()


@app.post("/subjects/", response_model=Subject)
async def create_item(item: Subject):
    return item


@app.post("/categories/", response_model=Category)
async def create_category(category: Category):
    await category.save()
    return category


@app.post("/buses/", response_model=Bus)
async def create_bus(bus: Bus):
    await bus.save()
    return bus


@app.get("/buses/{item_id}", response_model=Bus)
async def get_bus(item_id: int):
    bus = await Bus.objects.select_related(["owner", "co_owner"]).get(pk=item_id)
    return bus


@app.get("/buses/", response_model=List[Bus])
async def get_buses():
    buses = await Bus.objects.select_related(["owner", "co_owner"]).all()
    return buses


@app.post("/trucks/", response_model=Truck)
async def create_truck(truck: Truck):
    await truck.save()
    return truck


@app.post("/persons/", response_model=Person)
async def create_person(person: Person):
    await person.save()
    return person


@app.post("/buses2/", response_model=Bus2)
async def create_bus2(bus: Bus2):
    await bus.save()
    return bus


@app.post("/buses2/{item_id}/add_coowner/", response_model=Bus2)
async def add_bus_coowner(item_id: int, person: Person):
    bus = await Bus2.objects.select_related(["owner", "co_owners"]).get(pk=item_id)
    await bus.co_owners.add(person)
    return bus


@app.get("/buses2/", response_model=List[Bus2])
async def get_buses2():
    buses = await Bus2.objects.select_related(["owner", "co_owners"]).all()
    return buses


@app.post("/trucks2/", response_model=Truck2)
async def create_truck2(truck: Truck2):
    await truck.save()
    return truck


@app.post("/trucks2/{item_id}/add_coowner/", response_model=Truck2)
async def add_truck_coowner(item_id: int, person: Person):
    truck = await Truck2.objects.select_related(["owner", "co_owners"]).get(pk=item_id)
    await truck.co_owners.add(person)
    return truck


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


def test_read_main():
    client = TestClient(app)
    with client as client:
        test_category = dict(name="Foo", code=123, created_by="Sam", updated_by="Max")
        test_subject = dict(name="Bar")

        response = client.post("/categories/", json=test_category)
        assert response.status_code == 200
        cat = Category(**response.json())
        assert cat.name == "Foo"
        assert cat.created_by == "Sam"
        assert cat.created_date is not None
        assert cat.id == 1

        cat_dict = cat.dict()
        cat_dict["updated_date"] = cat_dict["updated_date"].strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        cat_dict["created_date"] = cat_dict["created_date"].strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        test_subject["category"] = cat_dict
        response = client.post("/subjects/", json=test_subject)
        assert response.status_code == 200
        sub = Subject(**response.json())
        assert sub.name == "Bar"
        assert sub.category.pk == cat.pk
        assert isinstance(sub.updated_date, datetime.datetime)


def test_inheritance_with_relation():
    client = TestClient(app)
    with client as client:
        sam = Person(**client.post("/persons/", json={"name": "Sam"}).json())
        joe = Person(**client.post("/persons/", json={"name": "Joe"}).json())

        truck_dict = dict(
            name="Shelby wanna be",
            max_capacity=1400,
            owner=sam.dict(),
            co_owner=joe.dict(),
        )
        bus_dict = dict(
            name="Unicorn", max_persons=50, owner=sam.dict(), co_owner=joe.dict()
        )
        unicorn = Bus(**client.post("/buses/", json=bus_dict).json())
        shelby = Truck(**client.post("/trucks/", json=truck_dict).json())

        assert shelby.name == "Shelby wanna be"
        assert shelby.owner.name == "Sam"
        assert shelby.co_owner.name == "Joe"
        assert shelby.co_owner == joe
        assert shelby.max_capacity == 1400

        assert unicorn.name == "Unicorn"
        assert unicorn.owner == sam
        assert unicorn.owner.name == "Sam"
        assert unicorn.co_owner.name == "Joe"
        assert unicorn.max_persons == 50

        unicorn2 = Bus(**client.get(f"/buses/{unicorn.pk}").json())
        assert unicorn2.name == "Unicorn"
        assert unicorn2.owner == sam
        assert unicorn2.owner.name == "Sam"
        assert unicorn2.co_owner.name == "Joe"
        assert unicorn2.max_persons == 50

        buses = [Bus(**x) for x in client.get("/buses/").json()]
        assert len(buses) == 1
        assert buses[0].name == "Unicorn"


def test_inheritance_with_m2m_relation():
    client = TestClient(app)
    with client as client:
        sam = Person(**client.post("/persons/", json={"name": "Sam"}).json())
        joe = Person(**client.post("/persons/", json={"name": "Joe"}).json())
        alex = Person(**client.post("/persons/", json={"name": "Alex"}).json())

        truck_dict = dict(name="Shelby wanna be", max_capacity=2000, owner=sam.dict())
        bus_dict = dict(name="Unicorn", max_persons=80, owner=sam.dict())

        unicorn = Bus2(**client.post("/buses2/", json=bus_dict).json())
        shelby = Truck2(**client.post("/trucks2/", json=truck_dict).json())

        unicorn = Bus2(
            **client.post(f"/buses2/{unicorn.pk}/add_coowner/", json=joe.dict()).json()
        )
        unicorn = Bus2(
            **client.post(f"/buses2/{unicorn.pk}/add_coowner/", json=alex.dict()).json()
        )

        assert shelby.name == "Shelby wanna be"
        assert shelby.owner.name == "Sam"
        assert len(shelby.co_owners) == 0
        assert shelby.max_capacity == 2000

        assert unicorn.name == "Unicorn"
        assert unicorn.owner == sam
        assert unicorn.owner.name == "Sam"
        assert unicorn.co_owners[0].name == "Joe"
        assert unicorn.co_owners[1] == alex
        assert unicorn.max_persons == 80

        client.post(f"/trucks2/{shelby.pk}/add_coowner/", json=alex.dict())

        shelby = Truck2(
            **client.post(f"/trucks2/{shelby.pk}/add_coowner/", json=joe.dict()).json()
        )

        assert shelby.name == "Shelby wanna be"
        assert shelby.owner.name == "Sam"
        assert len(shelby.co_owners) == 2
        assert shelby.co_owners[0] == alex
        assert shelby.co_owners[1] == joe
        assert shelby.max_capacity == 2000

        buses = [Bus2(**x) for x in client.get("/buses2/").json()]
        assert len(buses) == 1
        assert buses[0].name == "Unicorn"
