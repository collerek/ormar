import asyncio
import random
import string
import time

import databases
import nest_asyncio
import pytest
import pytest_asyncio
import sqlalchemy

import ormar
from tests.settings import DATABASE_URL

nest_asyncio.apply()


database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
pytestmark = pytest.mark.asyncio


class BaseMeta(ormar.ModelMeta):
    metadata = metadata
    database = database


class Author(ormar.Model):
    class Meta(BaseMeta):
        tablename = "authors"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    score: float = ormar.Integer(minimum=0, maximum=100)


class AuthorWithManyFields(Author):
    year_born: int = ormar.Integer()
    year_died: int = ormar.Integer(nullable=True)
    birthplace: str = ormar.String(max_length=255)


class Publisher(ormar.Model):
    class Meta(BaseMeta):
        tablename = "publishers"

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)
    prestige: int = ormar.Integer(minimum=0, maximum=10)


class Book(ormar.Model):
    class Meta(BaseMeta):
        tablename = "books"

    id: int = ormar.Integer(primary_key=True)
    author: Author = ormar.ForeignKey(Author, index=True)
    publisher: Publisher = ormar.ForeignKey(Publisher, index=True)
    title: str = ormar.String(max_length=100)
    year: int = ormar.Integer(nullable=True)


@pytest.fixture(autouse=True, scope="function")  # TODO: fix this to be module
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest_asyncio.fixture
async def author():
    author = await Author(name="Author", score=10).save()
    return author


@pytest_asyncio.fixture
async def publisher():
    publisher = await Publisher(name="Publisher", prestige=random.randint(0, 10)).save()
    return publisher


@pytest_asyncio.fixture
async def authors_in_db(num_models: int):
    authors = [
        Author(
            name="".join(random.sample(string.ascii_letters, 5)),
            score=random.random() * 100,
        )
        for i in range(0, num_models)
    ]
    await Author.objects.bulk_create(authors)
    return await Author.objects.all()


@pytest_asyncio.fixture
@pytest.mark.benchmark(
    min_rounds=1, timer=time.process_time, disable_gc=True, warmup=False
)
async def aio_benchmark(benchmark, event_loop: asyncio.BaseEventLoop):
    def _fixture_wrapper(func):
        def _func_wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):

                @benchmark
                def benchmarked_func():
                    a = event_loop.run_until_complete(func(*args, **kwargs))
                    return a

                return benchmarked_func
            else:
                return benchmark(func, *args, **kwargs)

        return _func_wrapper

    return _fixture_wrapper
