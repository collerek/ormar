import pytest

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors")

    id = ormar.Integer(primary_key=True)
    name = ormar.String(max_length=100)


class Book(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="books")

    id = ormar.Integer(primary_key=True)
    title = ormar.String(max_length=100)
    author = ormar.ManyToMany(
        Author,
    )
    year = ormar.Integer(nullable=True)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_tables_are_created():
    async with base_ormar_config.database:
        assert await Book.objects.all() == []
