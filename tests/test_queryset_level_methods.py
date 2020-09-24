import databases
import pytest
import sqlalchemy

import ormar
from ormar.exceptions import QueryDefinitionError
from tests.settings import DATABASE_URL

database = databases.Database(DATABASE_URL, force_rollback=True)
metadata = sqlalchemy.MetaData()


class Book(ormar.Model):
    class Meta:
        tablename = "books"
        metadata = metadata
        database = database

    id: ormar.Integer(primary_key=True)
    title: ormar.String(max_length=200)
    author: ormar.String(max_length=100)
    genre: ormar.String(max_length=100, default='Fiction', choices=['Fiction', 'Adventure', 'Historic', 'Fantasy'])


@pytest.fixture(autouse=True, scope="module")
def create_test_database():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_delete_and_update():
    async with database:
        async with database.transaction(force_rollback=True):
            await Book.objects.create(title='Tom Sawyer', author="Twain, Mark", genre='Adventure')
            await Book.objects.create(title='War and Peace', author="Tolstoy, Leo", genre='Fiction')
            await Book.objects.create(title='Anna Karenina', author="Tolstoy, Leo", genre='Fiction')
            await Book.objects.create(title='Harry Potter', author="Rowling, J.K.", genre='Fantasy')
            await Book.objects.create(title='Lord of the Rings', author="Tolkien, J.R.", genre='Fantasy')

            all_books = await Book.objects.all()
            assert len(all_books) == 5

            await Book.objects.filter(author="Tolstoy, Leo").update(author="Lenin, Vladimir")
            all_books = await Book.objects.filter(author="Lenin, Vladimir").all()
            assert len(all_books) == 2

            historic_books = await Book.objects.filter(genre='Historic').all()
            assert len(historic_books) == 0

            with pytest.raises(QueryDefinitionError):
                await Book.objects.update(genre='Historic')

            await Book.objects.filter(author="Lenin, Vladimir").update(genre='Historic')

            historic_books = await Book.objects.filter(genre='Historic').all()
            assert len(historic_books) == 2

            await Book.objects.delete(genre='Fantasy')
            all_books = await Book.objects.all()
            assert len(all_books) == 3

            await Book.objects.update(each=True, genre='Fiction')
            all_books = await Book.objects.filter(genre='Fiction').all()
            assert len(all_books) == 3

            with pytest.raises(QueryDefinitionError):
                await Book.objects.delete()

            await Book.objects.delete(each=True)
            all_books = await Book.objects.all()
            assert len(all_books) == 0
