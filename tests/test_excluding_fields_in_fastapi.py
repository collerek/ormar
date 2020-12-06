import datetime
import string
import random

import databases
import pydantic
import pytest
import sqlalchemy
from fastapi import FastAPI
from starlette.testclient import TestClient

import ormar
from ormar import property_field
from tests.settings import DATABASE_URL

app = FastAPI()
metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL, force_rollback=True)
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


# note that you can set orm_mode here
# and in this case UserSchema become unnecessary
class UserBase(pydantic.BaseModel):
    class Config:
        orm_mode = True

    email: str
    first_name: str
    last_name: str


class UserCreateSchema(UserBase):
    password: str
    category: str


class UserSchema(UserBase):
    class Config:
        orm_mode = True


def gen_pass():
    choices = string.ascii_letters + string.digits + "!@#$%^&*()"
    return "".join(random.choice(choices) for _ in range(20))


class RandomModel(ormar.Model):
    class Meta:
        tablename: str = "random_users"
        metadata = metadata
        database = database

        include_props_in_dict = True

    id: int = ormar.Integer(primary_key=True)
    password: str = ormar.String(max_length=255, default=gen_pass)
    first_name: str = ormar.String(max_length=255, default="John")
    last_name: str = ormar.String(max_length=255)
    created_date: datetime.datetime = ormar.DateTime(
        server_default=sqlalchemy.func.now()
    )

    @property_field
    def full_name(self) -> str:
        return " ".join([self.first_name, self.last_name])


class User(ormar.Model):
    class Meta:
        tablename: str = "users"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    email: str = ormar.String(max_length=255)
    password: str = ormar.String(max_length=255, nullable=True)
    first_name: str = ormar.String(max_length=255)
    last_name: str = ormar.String(max_length=255)
    category: str = ormar.String(max_length=255, nullable=True)


class User2(ormar.Model):
    class Meta:
        tablename: str = "users2"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    email: str = ormar.String(max_length=255, nullable=False)
    password: str = ormar.String(max_length=255)
    first_name: str = ormar.String(max_length=255)
    last_name: str = ormar.String(max_length=255)
    category: str = ormar.String(max_length=255, nullable=True)
    timestamp: datetime.datetime = ormar.DateTime(
        pydantic_only=True, default=datetime.datetime.now
    )


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@app.post("/users/", response_model=User, response_model_exclude={"password"})
async def create_user(user: User):
    return await user.save()


@app.post("/users2/", response_model=User)
async def create_user2(user: User):
    user = await user.save()
    return user.dict(exclude={"password"})


@app.post("/users3/", response_model=UserBase)
async def create_user3(user: User2):
    return await user.save()


@app.post("/users4/")
async def create_user4(user: User2):
    user = await user.save()
    return user.dict(exclude={"password"})


@app.post("/random/", response_model=RandomModel)
async def create_user5(user: RandomModel):
    user = await user.save()
    return user


@app.post("/random2/", response_model=RandomModel)
async def create_user6(user: RandomModel):
    user = await user.save()
    return user.dict()


@app.post("/random3/", response_model=RandomModel, response_model_exclude={"full_name"})
async def create_user7(user: RandomModel):
    user = await user.save()
    return user.dict()


def test_excluding_fields_in_endpoints():
    client = TestClient(app)
    with client as client:
        user = {
            "email": "test@domain.com",
            "password": "^*^%A*DA*IAAA",
            "first_name": "John",
            "last_name": "Doe",
        }
        response = client.post("/users/", json=user)
        created_user = User(**response.json())
        assert created_user.pk is not None
        assert created_user.password is None

        user2 = {
            "email": "test@domain.com",
            "first_name": "John",
            "last_name": "Doe",
        }

        response = client.post("/users/", json=user2)
        created_user = User(**response.json())
        assert created_user.pk is not None
        assert created_user.password is None

        response = client.post("/users2/", json=user)
        created_user2 = User(**response.json())
        assert created_user2.pk is not None
        assert created_user2.password is None

        # response has only 3 fields from UserBase
        response = client.post("/users3/", json=user)
        assert list(response.json().keys()) == ["email", "first_name", "last_name"]

        timestamp = datetime.datetime.now()

        user3 = {
            "email": "test@domain.com",
            "password": "^*^%A*DA*IAAA",
            "first_name": "John",
            "last_name": "Doe",
            "timestamp": str(timestamp),
        }
        response = client.post("/users4/", json=user3)
        assert list(response.json().keys()) == [
            "id",
            "email",
            "first_name",
            "last_name",
            "category",
            "timestamp",
        ]
        assert response.json().get("timestamp") == str(timestamp).replace(" ", "T")
        resp_dict = response.json()
        resp_dict.update({"password": "random"})
        user_instance = User2(**resp_dict)
        assert user_instance.timestamp is not None
        assert isinstance(user_instance.timestamp, datetime.datetime)
        assert user_instance.timestamp == timestamp

        response = client.post("/users4/", json=user3)
        assert list(response.json().keys()) == [
            "id",
            "email",
            "first_name",
            "last_name",
            "category",
            "timestamp",
        ]
        assert (
            datetime.datetime.strptime(
                response.json().get("timestamp"), "%Y-%m-%dT%H:%M:%S.%f"
            )
            == timestamp
        )


def test_adding_fields_in_endpoints():
    client = TestClient(app)
    with client as client:
        user3 = {"last_name": "Test", "full_name": "deleted"}
        response = client.post("/random/", json=user3)
        assert list(response.json().keys()) == [
            "id",
            "password",
            "first_name",
            "last_name",
            "created_date",
            "full_name",
        ]
        assert response.json().get("full_name") == "John Test"

        RandomModel.Meta.include_props_in_fields = False
        user3 = {"last_name": "Test"}
        response = client.post("/random/", json=user3)
        assert list(response.json().keys()) == [
            "id",
            "password",
            "first_name",
            "last_name",
            "created_date",
            "full_name",
        ]
        assert response.json().get("full_name") == "John Test"


def test_adding_fields_in_endpoints2():
    client = TestClient(app)
    with client as client:
        RandomModel.Meta.include_props_in_dict = True
        user3 = {"last_name": "Test"}
        response = client.post("/random2/", json=user3)
        assert list(response.json().keys()) == [
            "id",
            "password",
            "first_name",
            "last_name",
            "created_date",
            "full_name",
        ]
        assert response.json().get("full_name") == "John Test"


def test_excluding_property_field_in_endpoints2():
    client = TestClient(app)
    with client as client:
        RandomModel.Meta.include_props_in_dict = True
        user3 = {"last_name": "Test"}
        response = client.post("/random3/", json=user3)
        assert list(response.json().keys()) == [
            "id",
            "password",
            "first_name",
            "last_name",
            "created_date",
        ]
        assert response.json().get("full_name") is None
