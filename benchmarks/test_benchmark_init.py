import random
import string

import pytest

from benchmarks.conftest import Author, Book, Publisher

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_initializing_models(aio_benchmark, num_models: int):
    @aio_benchmark
    async def initialize_models(num_models: int):
        authors = [
            Author(
                name="".join(random.sample(string.ascii_letters, 5)),
                score=random.random() * 100,
            )
            for i in range(0, num_models)
        ]
        assert len(authors) == num_models

    initialize_models(num_models)


@pytest.mark.parametrize("num_models", [10, 20, 40])
async def test_initializing_models_with_related_models(aio_benchmark, num_models: int):
    @aio_benchmark
    async def initialize_models_with_related_models(
        author: Author, publisher: Publisher, num_models: int
    ):
        books = [
            Book(
                author=author,
                publisher=publisher,
                title="".join(random.sample(string.ascii_letters, 5)),
                year=random.randint(0, 2000),
            )
            for i in range(0, num_models)
        ]

    author = await Author(name="Author", score=10).save()
    publisher = await Publisher(name="Publisher", prestige=random.randint(0, 10)).save()

    ids = initialize_models_with_related_models(
        author=author, publisher=publisher, num_models=num_models
    )
