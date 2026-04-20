from typing import Optional

import pytest

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config(force_rollback=True)


class User(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="user")

    id: int = ormar.Integer(primary_key=True, autoincrement=True, nullable=False)
    user: str = ormar.String(
        unique=True, index=True, nullable=False, max_length=255
    )  # ID of the user on auth0
    first: str = ormar.String(nullable=False, max_length=255)
    last: str = ormar.String(nullable=False, max_length=255)
    email: str = ormar.String(unique=True, index=True, nullable=False, max_length=255)
    display_name: str = ormar.String(
        unique=True, index=True, nullable=False, max_length=255
    )
    pic_url: Optional[str] = ormar.Text(nullable=True)


class Task(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="task")

    id: int = ormar.Integer(primary_key=True, autoincrement=True, nullable=False)
    from_: Optional[str] = ormar.String(name="from", nullable=True, max_length=200)
    user = ormar.ForeignKey(User)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_single_model_quotes():
    async with base_ormar_config.database:
        await User.objects.create(
            user="test",
            first="first",
            last="last",
            email="email@com.com",
            display_name="first last",
        )

        user = await User.objects.order_by("user").get(first="first")
        assert user.last == "last"
        assert user.email == "email@com.com"


@pytest.mark.asyncio
async def test_two_model_quotes():
    async with base_ormar_config.database:
        user = await User.objects.create(
            user="test",
            first="first",
            last="last",
            email="email@com.com",
            display_name="first last",
        )

        await Task(user=user, from_="aa").save()
        await Task(user=user, from_="bb").save()

        task = (
            await Task.objects.select_related("user")
            .order_by("user__user")
            .get(from_="aa")
        )
        assert task.user.last == "last"
        assert task.user.email == "email@com.com"

        tasks = await Task.objects.select_related("user").order_by("-from").all()
        assert len(tasks) == 2
        assert tasks[0].user.last == "last"
        assert tasks[0].user.email == "email@com.com"
        assert tasks[0].from_ == "bb"

        assert tasks[1].user.last == "last"
        assert tasks[1].user.email == "email@com.com"
        assert tasks[1].from_ == "aa"
