from typing import List

import pytest

from benchmarks.conftest import Author

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_iterate(aio_benchmark, num_models: int, authors_in_db: List[Author]):
    @aio_benchmark
    async def iterate_over_all(authors: List[Author]):
        authors = []
        async for author in Author.objects.iterate():
            authors.append(author)
        return authors

    authors = iterate_over_all(authors_in_db)
    for idx, author in enumerate(authors_in_db):
        assert authors[idx].id == author.id
