# Models
import uuid
from datetime import date
from enum import Enum
from typing import Optional

import ormar
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config(force_rollback=True)


class PrimaryKeyMixin:
    id: uuid.UUID = ormar.UUID(primary_key=True, default=uuid.uuid4)


class Level(Enum):
    ADMIN = "0"
    STAFF = "1"


class User(PrimaryKeyMixin, ormar.Model):
    """User Model Class to Implement Method for Operations of User Entity"""

    mobile: str = ormar.String(unique=True, index=True, max_length=10)
    password: str = ormar.String(max_length=128)
    level: Level = ormar.Enum(default=Level.STAFF, enum_class=Level)
    email: Optional[str] = ormar.String(max_length=255, nullable=True, default=None)
    avatar: Optional[str] = ormar.String(max_length=255, nullable=True, default=None)
    fullname: Optional[str] = ormar.String(max_length=64, nullable=True, default=None)
    is_active: bool = ormar.Boolean(index=True, nullable=False, default=True)

    ormar_config = base_ormar_config.copy(order_by=["-is_active", "-level"])


class Task(PrimaryKeyMixin, ormar.Model):
    """Task Model Class to Implement Method for Operations of Task Entity"""

    name: str = ormar.String(max_length=64, nullalbe=False)
    description: Optional[str] = ormar.Text(nullable=True, default=None)
    start_date: Optional[date] = ormar.Date(nullable=True, default=None)
    end_date: Optional[date] = ormar.Date(nullable=True, default=None)
    is_halted: bool = ormar.Boolean(index=True, nullable=False, default=True)
    user: User = ormar.ForeignKey(to=User)

    ormar_config = base_ormar_config.copy(
        order_by=["-end_date", "-start_date"],
        constraints=[
            ormar.UniqueColumns("user", "name"),
        ],
    )


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_selecting_related_with_limit():
    async with base_ormar_config.database:
        user1 = await User(mobile="9928917653", password="pass1").save()
        user2 = await User(mobile="9928917654", password="pass2").save()
        await Task(name="one", user=user1).save()
        await Task(name="two", user=user1).save()
        await Task(name="three", user=user2).save()
        await Task(name="four", user=user2).save()

        users = (
            await User.objects.limit(2, limit_raw_sql=True)
            .select_related(User.tasks)
            .all()
        )
        users2 = (
            await User.objects.select_related(User.tasks)
            .limit(2, limit_raw_sql=True)
            .all()
        )
        assert users == users2
        assert len(users) == 1
        assert len(users[0].tasks) == 2

        users3 = await User.objects.limit(2).select_related(User.tasks).all()
        users4 = await User.objects.select_related(User.tasks).limit(2).all()
        assert users3 == users4
        assert len(users3) == 2
        assert len(users3[0].tasks) == 2
        assert len(users3[1].tasks) == 2
