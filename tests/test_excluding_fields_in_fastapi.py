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

    id: int = ormar.Integer(primary_key=True)
    password: str = ormar.String(max_length=255, default=gen_pass)
    first_name: str = ormar.String(max_length=255, default="John")
    last_name: str = ormar.String(max_length=255)
    created_date: datetime.datetime = ormar.DateTime(
        server_default=sqlalchemy.func.now()
    )


class User(ormar.Model):
    class Meta:
        tablename: str = "users"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    email: str = ormar.String(max_length=255, nullable=False)
    password: str = ormar.String(max_length=255, nullable=True)
    first_name: str = ormar.String(max_length=255, nullable=False)
    last_name: str = ormar.String(max_length=255, nullable=False)
    category: str = ormar.String(max_length=255, nullable=True)


class User2(ormar.Model):
    class Meta:
        tablename: str = "users2"
        metadata = metadata
        database = database

    id: int = ormar.Integer(primary_key=True)
    email: str = ormar.String(max_length=255, nullable=False)
    password: str = ormar.String(max_length=255, nullable=False)
    first_name: str = ormar.String(max_length=255, nullable=False)
    last_name: str = ormar.String(max_length=255, nullable=False)
    category: str = ormar.String(max_length=255, nullable=True)


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
    return await user.save()


def test_all_endpoints():
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

        response = client.post("/users4/", json=user)
        assert list(response.json().keys()) == [
            "id",
            "email",
            "first_name",
            "last_name",
            "category",
        ]

        user3 = {"last_name": "Test"}
        response = client.post("/random/", json=user3)
        assert list(response.json().keys()) == [
            "id",
            "password",
            "first_name",
            "last_name",
            "created_date",
        ]
