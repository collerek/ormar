from typing import Optional

import ormar
import pytest

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors", schema='s1')

    id = ormar.Integer(primary_key=True)
    name = ormar.String(max_length=100)


class Book(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="books", schema='s2')

    id = ormar.Integer(primary_key=True)
    title = ormar.String(max_length=100)
    author: Optional[Author] = ormar.ForeignKey(Author)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_filter_with_schema():
    async with base_ormar_config.database:
        author1 = await Author.objects.create(name="Tolkien")
        author2 = await Author.objects.create(name="Rowling")

        await Book.objects.create(title="LOTR", author=author1)
        await Book.objects.create(title="Hobbit", author=author1)
        await Book.objects.create(title="HP", author=author2)

        # фильтрация через join к таблице в другой схеме
        books = await Book.objects.filter(author__name="Tolkien").all()

        titles = sorted(b.title for b in books)
        assert titles == ["Hobbit", "LOTR"]


@pytest.mark.asyncio
async def test_filter_with_schema_and_in_lookup():
    async with base_ormar_config.database:
        author1 = await Author.objects.create(name="Asimov")
        author2 = await Author.objects.create(name="Clarke")

        await Book.objects.create(title="Foundation", author=author1)
        await Book.objects.create(title="Robots", author=author1)
        await Book.objects.create(title="Odyssey", author=author2)

        books = await Book.objects.filter(
            author__name__in=["Asimov"]
        ).all()

        assert {b.title for b in books} == {"Foundation", "Robots"}


@pytest.mark.asyncio
async def test_filter_with_schema_and_null_fk():
    async with base_ormar_config.database:
        author = await Author.objects.create(name="Orphan Author")

        await Book.objects.create(title="With Author", author=author)
        await Book.objects.create(title="Without Author", author=None)

        books = await Book.objects.filter(author__isnull=True).all()

        assert len(books) == 1
        assert books[0].title == "Without Author"
