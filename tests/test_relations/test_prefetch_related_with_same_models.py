from random import randint
from typing import Optional

import ormar
import pytest
from faker import Faker

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=256)


class BookAuthor(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="book_authors")

    id: int = ormar.Integer(primary_key=True)


class BookCoAuthor(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="book_co_authors")

    id: int = ormar.Integer(primary_key=True)


class Book(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="books")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=256)
    description: Optional[str] = ormar.String(max_length=256, nullable=True)
    authors: Optional[list[Author]] = ormar.ManyToMany(
        Author, related_name="author_books", through=BookAuthor
    )
    co_authors: Optional[list[Author]] = ormar.ManyToMany(
        Author, related_name="co_author_books", through=BookCoAuthor
    )


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_db():
    fake = Faker()
    async with base_ormar_config.database:
        for _ in range(6):
            await Author.objects.create(name=fake.name())

        book = await Book.objects.create(name=fake.sentence(nb_words=randint(1, 4)))
        for i in range(1, 3):
            await book.authors.add(await Author.objects.get(id=i))
        for i in range(3, 6):
            await book.co_authors.add(await Author.objects.get(id=i))

        prefetch_result = await Book.objects.prefetch_related(
            ["authors", "co_authors"]
        ).all()
        prefetch_dict_result = [x.dict() for x in prefetch_result if x.id == 1][0]
        select_result = await Book.objects.select_related(
            ["authors", "co_authors"]
        ).all()
        select_dict_result = [
            x.dict(
                exclude={
                    "authors": {"bookauthor": ...},
                    "co_authors": {"bookcoauthor": ...},
                }
            )
            for x in select_result
            if x.id == 1
        ][0]
        assert prefetch_dict_result == select_dict_result
