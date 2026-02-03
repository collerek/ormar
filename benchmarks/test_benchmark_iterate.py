import pytest

from benchmarks.conftest import Author

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("num_models", [250, 500, 1000])
async def test_iterate(aio_benchmark, num_models: int, authors_in_db: list[Author]):
    @aio_benchmark
    async def iterate_over_all(authors: list[Author]):
        authors = []
        async for author in Author.objects.iterate():
            authors.append(author)
        return authors

    authors = iterate_over_all(authors_in_db)
    for idx, author in enumerate(authors_in_db):
        assert authors[idx].id == author.id
