import ormar
import pytest
from typing import Optional

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
async def test_join_model_with_schema():
    async with base_ormar_config.database:
        
        tolkien = await Author.objects.create(name="Tolkien")
        await Book.objects.create(title="Hobbit", author=tolkien)
        await Book.objects.create(title="LOTR", author=tolkien)

        book = await Book.objects.select_related("author").get(title="Hobbit")
        assert book.author.name == "Tolkien"

@pytest.mark.asyncio
async def test_prefetch_related():
    async with base_ormar_config.database:
        author = await Author.objects.prefetch_related("books").get(name="Tolkien")
        assert len(author.books) >= 2

@pytest.mark.asyncio
async def test_multiple_select_related():
    async with base_ormar_config.database:
        books = await Book.objects.select_related("author").select_related("author").all()
        assert all(b.author.name == "Tolkien" for b in books)

@pytest.mark.asyncio
async def test_filter_on_related_field():
    async with base_ormar_config.database:
        books = await Book.objects.filter(author__name="Tolkien").all()
        assert len(books) >= 2