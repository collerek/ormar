import datetime
import random
import string

import ormar
import pydantic
import pytest
import sqlalchemy
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient
from ormar import post_save
from pydantic import ConfigDict, computed_field

from tests.lifespan import init_tests, lifespan
from tests.settings import create_config

base_ormar_config = create_config()
app = FastAPI(lifespan=lifespan(base_ormar_config))


# note that you can set orm_mode here
# and in this case UserSchema become unnecessary
class UserBase(pydantic.BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    first_name: str
    last_name: str


class UserCreateSchema(UserBase):
    password: str
    category: str


class UserSchema(UserBase):
    model_config = ConfigDict(from_attributes=True)


def gen_pass():
    choices = string.ascii_letters + string.digits + "!@#$%^&*()"
    return "".join(random.choice(choices) for _ in range(20))


class RandomModel(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="random_users")

    id: int = ormar.Integer(primary_key=True)
    password: str = ormar.String(max_length=255, default=gen_pass)
    first_name: str = ormar.String(max_length=255, default="John")
    last_name: str = ormar.String(max_length=255)
    created_date: datetime.datetime = ormar.DateTime(
        server_default=sqlalchemy.func.now()
    )

    @computed_field
    def full_name(self) -> str:
        return " ".join([self.first_name, self.last_name])


class User(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="users")

    id: int = ormar.Integer(primary_key=True)
    email: str = ormar.String(max_length=255)
    password: str = ormar.String(max_length=255, nullable=True)
    first_name: str = ormar.String(max_length=255)
    last_name: str = ormar.String(max_length=255)
    category: str = ormar.String(max_length=255, nullable=True)


class User2(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="users2")

    id: int = ormar.Integer(primary_key=True)
    email: str = ormar.String(max_length=255, nullable=False)
    password: str = ormar.String(max_length=255)
    first_name: str = ormar.String(max_length=255)
    last_name: str = ormar.String(max_length=255)
    category: str = ormar.String(max_length=255, nullable=True)
    timestamp: datetime.datetime = pydantic.Field(default=datetime.datetime.now)


create_test_database = init_tests(base_ormar_config)


@app.post("/users/", response_model=User, response_model_exclude={"password"})
async def create_user(user: User):
    return await user.save()


@app.post("/users2/", response_model=User)
async def create_user2(user: User):
    user = await user.save()
    return user.model_dump(exclude={"password"})


@app.post("/users3/", response_model=UserBase)
async def create_user3(user: User2):
    return await user.save()


@app.post("/users4/")
async def create_user4(user: User2):
    return (await user.save()).model_dump(exclude={"password"})


@app.post("/random/", response_model=RandomModel)
async def create_user5(user: RandomModel):
    return await user.save()


@app.post("/random2/", response_model=RandomModel)
async def create_user6(user: RandomModel):
    return await user.save()


@app.post("/random3/", response_model=RandomModel, response_model_exclude={"full_name"})
async def create_user7(user: RandomModel):
    return await user.save()


@pytest.mark.asyncio
async def test_excluding_fields_in_endpoints():
    client = AsyncClient(app=app, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        user = {
            "email": "test@domain.com",
            "password": "^*^%A*DA*IAAA",
            "first_name": "John",
            "last_name": "Doe",
        }
        response = await client.post("/users/", json=user)
        created_user = User(**response.json())
        assert created_user.pk is not None
        assert created_user.password is None

        user2 = {"email": "test@domain.com", "first_name": "John", "last_name": "Doe"}

        response = await client.post("/users/", json=user2)
        created_user = User(**response.json())
        assert created_user.pk is not None
        assert created_user.password is None

        response = await client.post("/users2/", json=user)
        created_user2 = User(**response.json())
        assert created_user2.pk is not None
        assert created_user2.password is None

        # response has only 3 fields from UserBase
        response = await client.post("/users3/", json=user)
        assert list(response.json().keys()) == ["email", "first_name", "last_name"]

        timestamp = datetime.datetime.now()

        user3 = {
            "email": "test@domain.com",
            "password": "^*^%A*DA*IAAA",
            "first_name": "John",
            "last_name": "Doe",
            "timestamp": str(timestamp),
        }
        response = await client.post("/users4/", json=user3)
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

        response = await client.post("/users4/", json=user3)
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


@pytest.mark.asyncio
async def test_adding_fields_in_endpoints():
    client = AsyncClient(app=app, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        user3 = {"last_name": "Test", "full_name": "deleted"}
        response = await client.post("/random/", json=user3)
        assert list(response.json().keys()) == [
            "id",
            "password",
            "first_name",
            "last_name",
            "created_date",
            "full_name",
        ]
        assert response.json().get("full_name") == "John Test"

        user3 = {"last_name": "Test"}
        response = await client.post("/random/", json=user3)
        assert list(response.json().keys()) == [
            "id",
            "password",
            "first_name",
            "last_name",
            "created_date",
            "full_name",
        ]
        assert response.json().get("full_name") == "John Test"


@pytest.mark.asyncio
async def test_adding_fields_in_endpoints2():
    client = AsyncClient(app=app, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        user3 = {"last_name": "Test"}
        response = await client.post("/random2/", json=user3)
        assert list(response.json().keys()) == [
            "id",
            "password",
            "first_name",
            "last_name",
            "created_date",
            "full_name",
        ]
        assert response.json().get("full_name") == "John Test"


@pytest.mark.asyncio
async def test_excluding_property_field_in_endpoints2():
    dummy_registry = {}

    @post_save(RandomModel)
    async def after_save(sender, instance, **kwargs):
        dummy_registry[instance.pk] = instance.model_dump()

    client = AsyncClient(app=app, base_url="http://testserver")
    async with client as client, LifespanManager(app):
        user3 = {"last_name": "Test"}
        response = await client.post("/random3/", json=user3)
        assert list(response.json().keys()) == [
            "id",
            "password",
            "first_name",
            "last_name",
            "created_date",
        ]
        assert response.json().get("full_name") is None
        assert len(dummy_registry) == 1
        check_dict = dummy_registry.get(response.json().get("id"))
        check_dict.pop("full_name")
        assert response.json().get("password") == check_dict.get("password")
