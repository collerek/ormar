import pickle
from typing import Optional

import pytest

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class User(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="users")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    properties = ormar.JSON(nullable=True)


class Post(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="posts")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    created_by: Optional[User] = ormar.ForeignKey(User)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_dumping_and_loading_model_works():
    async with base_ormar_config.database:
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
