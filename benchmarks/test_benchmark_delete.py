from typing import List

import pytest

from benchmarks.conftest import Author

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_deleting_all(
    aio_benchmark, num_models: int, authors_in_db: List[Author]
):
    @aio_benchmark
    async def delete_all():
        await Author.objects.delete(each=True)

    delete_all()

    num = await Author.objects.count()
    assert num == 0


@pytest.mark.parametrize("num_models", [10, 20, 40])
async def test_deleting_individually(
    aio_benchmark, num_models: int, authors_in_db: List[Author]
):
    @aio_benchmark
    async def delete_one_by_one(authors: List[Author]):
        for author in authors:
            await Author.objects.filter(id=author.id).delete()

    delete_one_by_one(authors_in_db)

    num = await Author.objects.count()
    assert num == 0
