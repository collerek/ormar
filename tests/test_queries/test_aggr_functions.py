from typing import Optional

import databases
import pytest
import pytest_asyncio
import sqlalchemy

import ormar
from ormar.exceptions import QueryDefinitionError
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Author(ormar.Model):
    class Meta(BaseMeta):
        tablename = "authors"
        order_by = ["-name"]

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Book(ormar.Model):
    class Meta(BaseMeta):
        tablename = "books"
        order_by = ["year", "-ranking"]

    id: int = ormar.Integer(primary_key=True)
    author: Optional[Author] = ormar.ForeignKey(Author)
    title: str = ormar.String(max_length=100)
    year: int = ormar.Integer(nullable=True)
    ranking: int = ormar.Integer(nullable=True)


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest_asyncio.fixture(autouse=True, scope="function")
async def cleanup():
    yield
    async with database:
        await Book.objects.delete(each=True)
        await Author.objects.delete(each=True)


async def sample_data():
    author = await Author(name="Author 1").save()
    await Book(title="Book 1", year=1920, ranking=3, author=author).save()
    await Book(title="Book 2", year=1930, ranking=1, author=author).save()
    await Book(title="Book 3", year=1923, ranking=5, author=author).save()


@pytest.mark.asyncio
async def test_min_method():
    async with database:
        await sample_data()
        assert await Book.objects.min("year") == 1920
        result = await Book.objects.min(["year", "ranking"])
        assert result == dict(year=1920, ranking=1)

        assert await Book.objects.min("title") == "Book 1"

        assert await Author.objects.select_related("books").min("books__year") == 1920
        result = await Author.objects.select_related("books").min(
            ["books__year", "books__ranking"]
        )
        assert result == dict(books__year=1920, books__ranking=1)

        assert (
            await Author.objects.select_related("books")
            .filter(books__year__gt=1925)
            .min("books__year")
            == 1930
        )


@pytest.mark.asyncio
async def test_max_method():
    async with database:
        await sample_data()
        assert await Book.objects.max("year") == 1930
        result = await Book.objects.max(["year", "ranking"])
        assert result == dict(year=1930, ranking=5)

        assert await Book.objects.max("title") == "Book 3"

        assert await Author.objects.select_related("books").max("books__year") == 1930
        result = await Author.objects.select_related("books").max(
            ["books__year", "books__ranking"]
        )
        assert result == dict(books__year=1930, books__ranking=5)

        assert (
            await Author.objects.select_related("books")
            .filter(books__year__lt=1925)
            .max("books__year")
            == 1923
        )


@pytest.mark.asyncio
async def test_sum_method():
    async with database:
        await sample_data()
        assert await Book.objects.sum("year") == 5773
        result = await Book.objects.sum(["year", "ranking"])
        assert result == dict(year=5773, ranking=9)

        with pytest.raises(QueryDefinitionError):
            await Book.objects.sum("title")

        assert await Author.objects.select_related("books").sum("books__year") == 5773
        result = await Author.objects.select_related("books").sum(
            ["books__year", "books__ranking"]
        )
        assert result == dict(books__year=5773, books__ranking=9)

        assert (
            await Author.objects.select_related("books")
            .filter(books__year__lt=1925)
            .sum("books__year")
            == 3843
        )


@pytest.mark.asyncio
async def test_avg_method():
    async with database:
        await sample_data()
        assert round(float(await Book.objects.avg("year")), 2) == 1924.33
        result = await Book.objects.avg(["year", "ranking"])
        assert round(float(result.get("year")), 2) == 1924.33
        assert result.get("ranking") == 3.0

        with pytest.raises(QueryDefinitionError):
            await Book.objects.avg("title")

        result = await Author.objects.select_related("books").avg("books__year")
        assert round(float(result), 2) == 1924.33
        result = await Author.objects.select_related("books").avg(
            ["books__year", "books__ranking"]
        )
        assert round(float(result.get("books__year")), 2) == 1924.33
        assert result.get("books__ranking") == 3.0

        assert (
            await Author.objects.select_related("books")
            .filter(books__year__lt=1925)
            .avg("books__year")
            == 1921.5
        )


@pytest.mark.asyncio
async def test_queryset_method():
    async with database:
        await sample_data()
        author = await Author.objects.select_related("books").get()
        assert await author.books.min("year") == 1920
        assert await author.books.max("year") == 1930
        assert await author.books.sum("ranking") == 9
        assert await author.books.avg("ranking") == 3.0
        assert await author.books.max(["year", "title"]) == dict(
            year=1930, title="Book 3"
        )


@pytest.mark.asyncio
async def test_count_method():
    async with database:
        await sample_data()

        count = await Author.objects.select_related("books").count()
        assert count == 1

        # The legacy functionality
        count = await Author.objects.select_related("books").count(distinct=False)
        assert count == 3
