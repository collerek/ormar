from typing import List

import pytest

from benchmarks.conftest import Author

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_values(aio_benchmark, num_models: int, authors_in_db: List[Author]):
    @aio_benchmark
    async def get_all_values(authors: List[Author]):
        return await Author.objects.values()

    authors_list = get_all_values(authors_in_db)
    for idx, author in enumerate(authors_in_db):
        assert authors_list[idx]["id"] == author.id


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_values_list(aio_benchmark, num_models: int, authors_in_db: List[Author]):
    @aio_benchmark
    async def get_all_values_list(authors: List[Author]):
        return await Author.objects.values_list()

    authors_list = get_all_values_list(authors_in_db)
    for idx, author in enumerate(authors_in_db):
        assert authors_list[idx][0] == author.id
