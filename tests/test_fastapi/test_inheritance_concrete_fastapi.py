import datetime
from typing import List, Optional

import ormar
import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from ormar.relations.relation_proxy import RelationProxy
from pydantic import computed_field

from tests.lifespan import init_tests, lifespan
from tests.settings import create_config

base_ormar_config = create_config()
app = FastAPI(lifespan=lifespan(base_ormar_config))


class AuditModel(ormar.Model):
    ormar_config = base_ormar_config.copy(abstract=True)

    created_by: str = ormar.String(max_length=100)
    updated_by: str = ormar.String(max_length=100, default="Sam")

    @computed_field
    def audit(self) -> str:  # pragma: no cover
        return f"{self.created_by} {self.updated_by}"


class DateFieldsModelNoSubclass(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="test_date_models")

    date_id: int = ormar.Integer(primary_key=True)
    created_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)
    updated_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)


class DateFieldsModel(ormar.Model):
    ormar_config = base_ormar_config.copy(
        abstract=True,
        constraints=[
            ormar.fields.constraints.UniqueColumns(
                "creation_date",
                "modification_date",
            ),
            ormar.fields.constraints.CheckColumns(
                "creation_date <= modification_date",
            ),
        ],
    )

    created_date: datetime.datetime = ormar.DateTime(
        default=datetime.datetime.now, name="creation_date"
    )
    updated_date: datetime.datetime = ormar.DateTime(
        default=datetime.datetime.now, name="modification_date"
    )


class Person(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Car(ormar.Model):
    ormar_config = base_ormar_config.copy(abstract=True)

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50)
    owner: Person = ormar.ForeignKey(Person)
    co_owner: Person = ormar.ForeignKey(Person, related_name="coowned")
    created_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)


class Car2(ormar.Model):
    ormar_config = base_ormar_config.copy(abstract=True)

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50)
    owner: Person = ormar.ForeignKey(Person, related_name="owned")
    co_owners: RelationProxy[Person] = ormar.ManyToMany(Person, related_name="coowned")
    created_date: datetime.datetime = ormar.DateTime(default=datetime.datetime.now)


class Bus(Car):
    ormar_config = base_ormar_config.copy(tablename="buses")

    owner: Person = ormar.ForeignKey(Person, related_name="buses")
    max_persons: int = ormar.Integer()


class Bus2(Car2):
    ormar_config = base_ormar_config.copy(tablename="buses2")

    max_persons: int = ormar.Integer()


class Category(DateFieldsModel, AuditModel):
    ormar_config = base_ormar_config.copy(tablename="categories")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)
    code: int = ormar.Integer()

    @computed_field
    def code_name(self) -> str:
        return f"{self.code}:{self.name}"

    @computed_field
    def audit(self) -> str:
        return f"{self.created_by} {self.updated_by}"


class Subject(DateFieldsModel):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=50, unique=True, index=True)
    category: Optional[Category] = ormar.ForeignKey(Category)


class Truck(Car):
    ormar_config = base_ormar_config.copy()

    max_capacity: int = ormar.Integer()


class Truck2(Car2):
    ormar_config = base_ormar_config.copy(tablename="trucks2")

    max_capacity: int = ormar.Integer()


create_test_database = init_tests(base_ormar_config)


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


@pytest.mark.asyncio
async def test_read_main():
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        test_category = dict(name="Foo", code=123, created_by="Sam", updated_by="Max")
        test_subject = dict(name="Bar")

        response = await client.post("/categories/", json=test_category)
        assert response.status_code == 200
        cat = Category(**response.json())
        assert cat.name == "Foo"
        assert cat.created_by == "Sam"
        assert cat.created_date is not None
        assert cat.id == 1

        cat_dict = cat.model_dump()
        cat_dict["updated_date"] = cat_dict["updated_date"].strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        cat_dict["created_date"] = cat_dict["created_date"].strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        test_subject["category"] = cat_dict
        response = await client.post("/subjects/", json=test_subject)
        assert response.status_code == 200
        sub = Subject(**response.json())
        assert sub.name == "Bar"
        assert sub.category.pk == cat.pk
        assert isinstance(sub.updated_date, datetime.datetime)


@pytest.mark.asyncio
async def test_inheritance_with_relation():
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        sam = Person(**(await client.post("/persons/", json={"name": "Sam"})).json())
        joe = Person(**(await client.post("/persons/", json={"name": "Joe"})).json())

        truck_dict = dict(
            name="Shelby wanna be",
            max_capacity=1400,
            owner=sam.model_dump(),
            co_owner=joe.model_dump(),
        )
        bus_dict = dict(
            name="Unicorn",
            max_persons=50,
            owner=sam.model_dump(),
            co_owner=joe.model_dump(),
        )
        unicorn = Bus(**(await client.post("/buses/", json=bus_dict)).json())
        shelby = Truck(**(await client.post("/trucks/", json=truck_dict)).json())

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

        unicorn2 = Bus(**(await client.get(f"/buses/{unicorn.pk}")).json())
        assert unicorn2.name == "Unicorn"
        assert unicorn2.owner == sam
        assert unicorn2.owner.name == "Sam"
        assert unicorn2.co_owner.name == "Joe"
        assert unicorn2.max_persons == 50

        buses = [Bus(**x) for x in (await client.get("/buses/")).json()]
        assert len(buses) == 1
        assert buses[0].name == "Unicorn"


@pytest.mark.asyncio
async def test_inheritance_with_m2m_relation():
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        sam = Person(**(await client.post("/persons/", json={"name": "Sam"})).json())
        joe = Person(**(await client.post("/persons/", json={"name": "Joe"})).json())
        alex = Person(**(await client.post("/persons/", json={"name": "Alex"})).json())

        truck_dict = dict(
            name="Shelby wanna be", max_capacity=2000, owner=sam.model_dump()
        )
        bus_dict = dict(name="Unicorn", max_persons=80, owner=sam.model_dump())

        unicorn = Bus2(**(await client.post("/buses2/", json=bus_dict)).json())
        shelby = Truck2(**(await client.post("/trucks2/", json=truck_dict)).json())

        unicorn = Bus2(
            **(
                await client.post(
                    f"/buses2/{unicorn.pk}/add_coowner/", json=joe.model_dump()
                )
            ).json()
        )
        unicorn = Bus2(
            **(
                await client.post(
                    f"/buses2/{unicorn.pk}/add_coowner/", json=alex.model_dump()
                )
            ).json()
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

        await client.post(f"/trucks2/{shelby.pk}/add_coowner/", json=alex.model_dump())

        shelby = Truck2(
            **(
                await client.post(
                    f"/trucks2/{shelby.pk}/add_coowner/", json=joe.model_dump()
                )
            ).json()
        )

        assert shelby.name == "Shelby wanna be"
        assert shelby.owner.name == "Sam"
        assert len(shelby.co_owners) == 2
        assert shelby.co_owners[0] == alex
        assert shelby.co_owners[1] == joe
        assert shelby.max_capacity == 2000

        buses = [Bus2(**x) for x in (await client.get("/buses2/")).json()]
        assert len(buses) == 1
        assert buses[0].name == "Unicorn"
