import random
import string

import pytest

from benchmarks.conftest import Author, Book, Publisher

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("num_models", [10, 20, 40])
async def test_creating_models_individually(aio_benchmark, num_models: int):
    @aio_benchmark
    async def create(num_models: int):
        authors = []
        for idx in range(0, num_models):
            author = await Author.objects.create(
                name="".join(random.sample(string.ascii_letters, 5)),
                score=random.random() * 100,
            )
            authors.append(author)
        return authors

    authors = create(num_models)
    for author in authors:
        assert author.id is not None


@pytest.mark.parametrize("num_models", [10, 20, 40])
async def test_creating_individually_with_related_models(
    aio_benchmark, num_models: int, author: Author, publisher: Publisher
):
    @aio_benchmark
    async def create_with_related_models(
        author: Author, publisher: Publisher, num_models: int
    ):
        books = []
        for idx in range(0, num_models):
            book = await Book.objects.create(
                author=author,
                publisher=publisher,
                title="".join(random.sample(string.ascii_letters, 5)),
                year=random.randint(0, 2000),
            )
            books.append(book)

        return books

    books = create_with_related_models(
        author=author, publisher=publisher, num_models=num_models
    )

    for book in books:
        assert book.id is not None


@pytest.mark.parametrize("num_models", [10, 20, 40])
async def test_get_or_create_when_create(aio_benchmark, num_models: int):
    @aio_benchmark
    async def get_or_create(num_models: int):
        authors = []
        for idx in range(0, num_models):
            author, created = await Author.objects.get_or_create(
                name="".join(random.sample(string.ascii_letters, 5)),
                score=random.random() * 100,
            )
            assert created
            authors.append(author)
        return authors

    authors = get_or_create(num_models)
    for author in authors:
        assert author.id is not None


@pytest.mark.parametrize("num_models", [10, 20, 40])
async def test_update_or_create_when_create(aio_benchmark, num_models: int):
    @aio_benchmark
    async def update_or_create(num_models: int):
        authors = []
        for idx in range(0, num_models):
            author = await Author.objects.update_or_create(
                name="".join(random.sample(string.ascii_letters, 5)),
                score=random.random() * 100,
            )
            authors.append(author)
        return authors

    authors = update_or_create(num_models)
    for author in authors:
        assert author.id is not None
