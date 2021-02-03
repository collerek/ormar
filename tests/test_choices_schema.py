import datetime
import decimal
import uuid
from enum import Enum

import databases
import pydantic
import pytest
import sqlalchemy
from fastapi import FastAPI
from starlette.testclient import TestClient

import ormar
from tests.settings import DATABASE_URL

app = FastAPI()
database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()
app.state.database = database

uuid1 = uuid.uuid4()
uuid2 = uuid.uuid4()


class TestEnum(Enum):
    val1 = "Val1"
    val2 = "Val2"


class Organisation(ormar.Model):
    class Meta:
        tablename = "org"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    ident: str = ormar.String(max_length=100, choices=["ACME Ltd", "Other ltd"])
    priority: int = ormar.Integer(choices=[1, 2, 3, 4, 5])
    priority2: int = ormar.BigInteger(choices=[1, 2, 3, 4, 5])
    expire_date: datetime.date = ormar.Date(
        choices=[datetime.date(2021, 1, 1), datetime.date(2022, 5, 1)]
    )
    expire_time: datetime.time = ormar.Time(
        choices=[datetime.time(10, 0, 0), datetime.time(12, 30)]
    )

    expire_datetime: datetime.datetime = ormar.DateTime(
        choices=[
            datetime.datetime(2021, 1, 1, 10, 0, 0),
            datetime.datetime(2022, 5, 1, 12, 30),
        ]
    )
    random_val: float = ormar.Float(choices=[2.0, 3.5])
    random_decimal: decimal.Decimal = ormar.Decimal(
        scale=2, precision=4, choices=[decimal.Decimal(12.4), decimal.Decimal(58.2)]
    )
    random_json: pydantic.Json = ormar.JSON(choices=["aa", '{"aa":"bb"}'])
    random_uuid: uuid.UUID = ormar.UUID(choices=[uuid1, uuid2])
    enum_string: str = ormar.String(max_length=100, choices=list(TestEnum))


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


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@app.post("/items/", response_model=Organisation)
async def create_item(item: Organisation):
    await item.save()
    return item


def test_all_endpoints():
    client = TestClient(app)
    with client as client:
        response = client.post(
            "/items/",
            json={"id": 1, "ident": "", "priority": 4, "expire_date": "2022-05-01"},
        )

        assert response.status_code == 422
        response = client.post(
            "/items/",
            json={
                "id": 1,
                "ident": "ACME Ltd",
                "priority": 4,
                "priority2": 2,
                "expire_date": "2022-05-01",
                "expire_time": "10:00:00",
                "expire_datetime": "2022-05-01T12:30:00",
                "random_val": 3.5,
                "random_decimal": 12.4,
                "random_json": '{"aa":"bb"}',
                "random_uuid": str(uuid1),
                "enum_string": TestEnum.val1.value,
            },
        )

        assert response.status_code == 200
        item = Organisation(**response.json())
        assert item.pk is not None
        response = client.get("/docs/")
        assert response.status_code == 200
        assert b"<title>FastAPI - Swagger UI</title>" in response.content


def test_schema_modification():
    schema = Organisation.schema()
    for field in ["ident", "priority", "expire_date"]:
        assert field in schema["properties"]
        assert schema["properties"].get(field).get("enum") == list(
            Organisation.Meta.model_fields.get(field).choices
        )
        assert "An enumeration." in schema["properties"].get(field).get("description")


def test_schema_gen():
    schema = app.openapi()
    assert "Organisation" in schema["components"]["schemas"]
    props = schema["components"]["schemas"]["Organisation"]["properties"]
    for field in [k for k in Organisation.Meta.model_fields.keys() if k != "id"]:
        assert "enum" in props.get(field)
        assert "description" in props.get(field)
        assert "An enumeration." in props.get(field).get("description")
