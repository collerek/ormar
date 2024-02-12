import datetime
import uuid
from typing import Dict, Optional, Union

import ormar
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Team(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="team")

    id: uuid.UUID = ormar.UUID(default=uuid.uuid4, primary_key=True, index=True)
    name = ormar.Text(nullable=True)
    client_id = ormar.Text(nullable=True)
    client_secret = ormar.Text(nullable=True)
    created_on = ormar.DateTime(timezone=True, default=datetime.datetime.utcnow())


class User(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="user")

    id: uuid.UUID = ormar.UUID(default=uuid.uuid4, primary_key=True, index=True)
    client_user_id = ormar.Text()
    token = ormar.Text(nullable=True)
    team: Optional[Team] = ormar.ForeignKey(to=Team, name="team_id")


class Order(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="order")

    id: uuid.UUID = ormar.UUID(default=uuid.uuid4, primary_key=True, index=True)
    user: Optional[Union[User, Dict]] = ormar.ForeignKey(User)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_quoting_on_clause_without_prefix():
    async with base_ormar_config.database:
        await User.objects.select_related("orders").all()
