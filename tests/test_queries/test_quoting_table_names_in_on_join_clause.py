import datetime
import uuid
from typing import Dict, Optional, Union

import databases
import pytest
import sqlalchemy
from sqlalchemy import create_engine

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
engine = create_engine(DATABASE_URL)


class Team(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "team",
        database = database,
        metadata = metadata,
    )

    id: uuid.UUID = ormar.UUID(default=uuid.uuid4, primary_key=True, index=True)
    name = ormar.Text(nullable=True)
    client_id = ormar.Text(nullable=True)
    client_secret = ormar.Text(nullable=True)
    created_on = ormar.DateTime(timezone=True, default=datetime.datetime.utcnow())


class User(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "user",
        database = database,
        metadata = metadata,
    )

    id: uuid.UUID = ormar.UUID(default=uuid.uuid4, primary_key=True, index=True)
    client_user_id = ormar.Text()
    token = ormar.Text(nullable=True)
    team: Optional[Team] = ormar.ForeignKey(to=Team, name="team_id")


class Order(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename = "order",
        database = database,
        metadata = metadata,
    )

    id: uuid.UUID = ormar.UUID(default=uuid.uuid4, primary_key=True, index=True)
    user: Optional[Union[User, Dict]] = ormar.ForeignKey(User)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_quoting_on_clause_without_prefix():
    async with database:
        await User.objects.select_related("orders").all()
