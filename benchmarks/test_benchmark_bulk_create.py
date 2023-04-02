import random
import string

import pytest

from benchmarks.conftest import Author

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("num_models", [10, 20, 40])
async def test_making_and_inserting_models_in_bulk(aio_benchmark, num_models: int):
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

        await Author.objects.bulk_create(authors)

    make_and_insert(num_models)
