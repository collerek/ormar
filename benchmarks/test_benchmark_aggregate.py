from typing import List

import pytest

from benchmarks.conftest import Author

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_count(aio_benchmark, num_models: int, authors_in_db: List[Author]):
    @aio_benchmark
    async def count():
        return await Author.objects.count()

    c = count()
    assert c == len(authors_in_db)


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_avg(aio_benchmark, num_models: int, authors_in_db: List[Author]):
    @aio_benchmark
    async def avg():
        return await Author.objects.avg("score")

    average = avg()
    assert 0 <= average <= 100


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_sum(aio_benchmark, num_models: int, authors_in_db: List[Author]):
    @aio_benchmark
    async def sum_():
        return await Author.objects.sum("score")

    s = sum_()
    assert 0 <= s <= 100 * num_models


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_min(aio_benchmark, num_models: int, authors_in_db: List[Author]):
    @aio_benchmark
    async def min_():
        return await Author.objects.min("score")

    m = min_()
    assert 0 <= m <= 100


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_max(aio_benchmark, num_models: int, authors_in_db: List[Author]):
    @aio_benchmark
    async def max_():
        return await Author.objects.max("score")

    m = max_()
    assert 0 <= m <= 100
