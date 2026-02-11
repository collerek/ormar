import ormar
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors")
    id: int = ormar.Integer(primary_key=True)


class Book(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="books")
    id: int = ormar.Integer(primary_key=True)
    author: Author = ormar.ForeignKey(Author, name="author_id")
    my_data: dict | None = ormar.JSON(nullable=True)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_construct_with_empty_relation():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            author = await Author.objects.create()
            await Book.objects.create(author=author, my_data={"aa": 1})
            # this should not error out
            await Author.objects.select_related(Author.books).all()
            # this should also not error out
            await Author.objects.select_all().all()
