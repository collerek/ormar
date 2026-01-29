import ormar
import pytest
from typing import Optional

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors", schema='s1')

    id = ormar.Integer(primary_key=True)
    name = ormar.String(max_length=100)


class Book(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="books", schema="s2")

    id = ormar.Integer(primary_key=True)
    title = ormar.String(max_length=100)

    author: Optional[Author] = ormar.ForeignKey(
        Author,
        related_name="written_books",
    )

    editor: Optional[Author] = ormar.ForeignKey(
        Author,
        related_name="edited_books",
        nullable=True,
    )



create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_multiple_joins_same_table_filter():
    async with base_ormar_config.database:
        author = await Author.objects.create(name="Author A")
        editor = await Author.objects.create(name="Editor B")

        await Book.objects.create(
            title="Book 1",
            author=author,
            editor=editor,
        )

        await Book.objects.create(
            title="Book 2",
            author=author,
            editor=None,
        )

        # JOIN authors: author + editor
        books = await Book.objects.filter(
            author__name="Author A",
            editor__name="Editor B",
        ).all()

        assert len(books) == 1
        assert books[0].title == "Book 1"


@pytest.mark.asyncio
async def test_multiple_joins_same_table_select_related():
    async with base_ormar_config.database:
        author = await Author.objects.create(name="Author X")
        editor = await Author.objects.create(name="Editor Y")

        book = await Book.objects.create(
            title="Deep ORM",
            author=author,
            editor=editor,
        )

        fetched = (
            await Book.objects
            .select_related(["author", "editor"])
            .get(id=book.id)
        )

        assert fetched.author.name == "Author X"
        assert fetched.editor.name == "Editor Y"
