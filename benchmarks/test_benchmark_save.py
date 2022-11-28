import random
import string

import pytest

from benchmarks.conftest import Author, Book, Publisher

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("num_models", [10, 20, 40])
async def test_saving_models_individually(aio_benchmark, num_models: int):
    @aio_benchmark
    async def make_and_insert(num_models: int):
        authors = [
            Author(
                name="".join(random.sample(string.ascii_letters, 5)),
                score=random.random() * 100,
            )
            for i in range(0, num_models)
        ]
        assert len(authors) == num_models

        ids = []
        for author in authors:
            a = await author.save()
            ids.append(a)
        return ids

    ids = make_and_insert(num_models)
    for id in ids:
        assert id is not None


@pytest.mark.parametrize("num_models", [10, 20, 40])
async def test_saving_models_individually_with_related_models(
    aio_benchmark, num_models: int, author: Author, publisher: Publisher
):
    @aio_benchmark
    async def making_and_inserting_related_models_one_by_one(
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

        ids = []
        for book in books:
            await book.save()
            ids.append(book.id)

        return ids

    ids = making_and_inserting_related_models_one_by_one(
        author=author, publisher=publisher, num_models=num_models
    )

    for id in ids:
        assert id is not None
