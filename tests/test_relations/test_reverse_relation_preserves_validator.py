from typing import List, Optional, Union

import pytest_asyncio
from pydantic import field_validator

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=80)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: Union[str, List[str]]) -> str:
        if isinstance(v, list):
            v = " ".join(v)
        return v


class Post(ormar.Model):
    ormar_config = base_ormar_config.copy()

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=200)
    author: Optional[Author] = ormar.ForeignKey(Author)


create_test_database = init_tests(base_ormar_config)


@pytest_asyncio.fixture(scope="function")
async def cleanup():
    yield
    async with base_ormar_config.database:
        await Post.objects.delete(each=True)
        await Author.objects.delete(each=True)


def test_validator():
    author = Author(name=["Test", "Author"])
    assert author.name == "Test Author"
