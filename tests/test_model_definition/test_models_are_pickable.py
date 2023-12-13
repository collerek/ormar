import pickle
from typing import Optional

import databases
import pytest
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class User(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="users",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    properties = ormar.JSON(nullable=True)


class Post(ormar.Model):
    ormar_config = ormar.OrmarConfig(
        tablename="posts",
        metadata=metadata,
        database=database,
    )

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    created_by: Optional[User] = ormar.ForeignKey(User)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_dumping_and_loading_model_works():
    async with database:
        user = await User(name="Test", properties={"aa": "bb"}).save()
        post = Post(name="Test post")
        await user.posts.add(post)
        pickled_value = pickle.dumps(user)
        python_value = pickle.loads(pickled_value)
        assert isinstance(python_value, User)
        assert python_value.name == "Test"
        assert python_value.properties == {"aa": "bb"}
        assert python_value.posts[0].name == "Test post"
        await python_value.load()
        await python_value.update(name="Test2")
        check = await User.objects.get()
        assert check.name == "Test2"
