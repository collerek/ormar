import databases
import pytest
import sqlalchemy

import ormar

from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


base_ormar_config = ormar.OrmarConfig(
    metadata=metadata,
    database=database,
)

class User(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename = "user")

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
    pic_url: str = ormar.Text(nullable=True)


class Task(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename = "task")

    id: int = ormar.Integer(primary_key=True, autoincrement=True, nullable=False)
    from_: str = ormar.String(name="from", nullable=True, max_length=200)
    user = ormar.ForeignKey(User)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_single_model_quotes():
    async with database:
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
    async with database:
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
