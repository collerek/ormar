import random
import string
from typing import List

import pytest
import pytest_asyncio

from benchmarks.conftest import Author, Book, Publisher

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture()
async def books(author: Author, publisher: Publisher, num_models: int):
    books = [
        Book(
            author=author,
            publisher=publisher,
            title="".join(random.sample(string.ascii_letters, 5)),
            year=random.randint(0, 2000),
        )
        for _ in range(0, num_models)
    ]
    await Book.objects.bulk_create(books)
    return books


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_get_all(aio_benchmark, num_models: int, authors_in_db: List[Author]):
    @aio_benchmark
    async def get_all(authors: List[Author]):
        return await Author.objects.all()

    authors = get_all(authors_in_db)
    for idx, author in enumerate(authors_in_db):
        assert authors[idx].id == author.id


@pytest.mark.parametrize("num_models", [10, 20, 40])
async def test_get_all_with_related_models(
    aio_benchmark, num_models: int, author: Author, books: List[Book]
):
    @aio_benchmark
    async def get_with_related(author: Author):
        return await Author.objects.select_related("books").all(id=author.id)

    authors = get_with_related(author)
    assert len(authors[0].books) == num_models


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_get_one(aio_benchmark, num_models: int, authors_in_db: List[Author]):
    @aio_benchmark
    async def get_one(authors: List[Author]):
        return await Author.objects.get(id=authors[0].id)

    author = get_one(authors_in_db)
    assert author == authors_in_db[0]


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_get_or_none(aio_benchmark, num_models: int, authors_in_db: List[Author]):
    @aio_benchmark
    async def get_or_none(authors: List[Author]):
        return await Author.objects.get_or_none(id=authors[0].id)

    author = get_or_none(authors_in_db)
    assert author == authors_in_db[0]


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_get_or_create_when_get(
    aio_benchmark, num_models: int, authors_in_db: List[Author]
):
    @aio_benchmark
    async def get_or_create(authors: List[Author]):
        author, created = await Author.objects.get_or_create(id=authors[0].id)
        assert not created
        return author

    author = get_or_create(authors_in_db)
    assert author == authors_in_db[0]


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_first(aio_benchmark, num_models: int, authors_in_db: List[Author]):
    @aio_benchmark
    async def first():
        return await Author.objects.first()

    author = first()
    assert author == authors_in_db[0]


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_exists(aio_benchmark, num_models: int, authors_in_db: List[Author]):
    @aio_benchmark
    async def check_exists(authors: List[Author]):
        return await Author.objects.filter(id=authors[0].id).exists()

    exists = check_exists(authors_in_db)
    assert exists
