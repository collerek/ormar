from typing import Optional

import ormar
import pytest
from ormar.exceptions import QueryDefinitionError

from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="authors")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Book(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="books")

    id: int = ormar.Integer(primary_key=True)
    author: Optional[Author] = ormar.ForeignKey(Author)
    title: str = ormar.String(max_length=100)
    year: int = ormar.Integer(nullable=True)


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_or_filters():
    async with base_ormar_config.database:
        tolkien = await Author(name="J.R.R. Tolkien").save()
        await Book(author=tolkien, title="The Hobbit", year=1933).save()
        await Book(author=tolkien, title="The Lord of the Rings", year=1955).save()
        await Book(author=tolkien, title="The Silmarillion", year=1977).save()
        sapkowski = await Author(name="Andrzej Sapkowski").save()
        await Book(author=sapkowski, title="The Witcher", year=1990).save()
        await Book(author=sapkowski, title="The Tower of Fools", year=2002).save()

        books = (
            await Book.objects.select_related("author")
            .filter(ormar.or_(author__name="J.R.R. Tolkien", year__gt=1970))
            .all()
        )
        assert len(books) == 5

        books = (
            await Book.objects.select_related("author")
            .filter(ormar.or_(author__name="J.R.R. Tolkien", year__lt=1995))
            .all()
        )
        assert len(books) == 4
        assert not any([x.title == "The Tower of Fools" for x in books])

        books = (
            await Book.objects.select_related("author")
            .filter((Book.author.name == "J.R.R. Tolkien") | (Book.year < 1995))
            .all()
        )
        assert len(books) == 4
        assert not any([x.title == "The Tower of Fools" for x in books])

        books = (
            await Book.objects.select_related("author")
            .filter(ormar.or_(year__gt=1960, year__lt=1940))
            .filter(author__name="J.R.R. Tolkien")
            .all()
        )
        assert len(books) == 2
        assert books[0].title == "The Hobbit"
        assert books[1].title == "The Silmarillion"

        books = (
            await Book.objects.select_related("author")
            .filter(
                ormar.and_(
                    ormar.or_(year__gt=1960, year__lt=1940),
                    author__name="J.R.R. Tolkien",
                )
            )
            .all()
        )

        assert len(books) == 2
        assert books[0].title == "The Hobbit"
        assert books[1].title == "The Silmarillion"

        books = (
            await Book.objects.select_related("author")
            .filter(
                ormar.or_(
                    ormar.and_(year__gt=1960, author__name="J.R.R. Tolkien"),
                    ormar.and_(year__lt=2000, author__name="Andrzej Sapkowski"),
                )
            )
            .filter(title__startswith="The")
            .all()
        )
        assert len(books) == 2
        assert books[0].title == "The Silmarillion"
        assert books[1].title == "The Witcher"

        books = (
            await Book.objects.select_related("author")
            .filter(
                (
                    (
                        (Book.year > 1960) & (Book.author.name == "J.R.R. Tolkien")
                        | (
                            (Book.year < 2000)
                            & (Book.author.name == "Andrzej Sapkowski")
                        )
                    )
                    & (Book.title.startswith("The"))
                )
            )
            .all()
        )
        assert len(books) == 2
        assert books[0].title == "The Silmarillion"
        assert books[1].title == "The Witcher"

        books = (
            await Book.objects.select_related("author")
            .filter(
                ormar.or_(
                    ormar.and_(
                        ormar.or_(year__gt=1960, year__lt=1940),
                        author__name="J.R.R. Tolkien",
                    ),
                    ormar.and_(year__lt=2000, author__name="Andrzej Sapkowski"),
                )
            )
            .all()
        )
        assert len(books) == 3
        assert books[0].title == "The Hobbit"
        assert books[1].title == "The Silmarillion"
        assert books[2].title == "The Witcher"

        books = (
            await Book.objects.select_related("author")
            .exclude(
                ormar.or_(
                    ormar.and_(year__gt=1960, author__name="J.R.R. Tolkien"),
                    ormar.and_(year__lt=2000, author__name="Andrzej Sapkowski"),
                )
            )
            .filter(title__startswith="The")
            .all()
        )
        assert len(books) == 3
        assert not any([x.title in ["The Silmarillion", "The Witcher"] for x in books])

        books = (
            await Book.objects.select_related("author")
            .filter(
                ormar.or_(
                    ormar.and_(year__gt=1960, author__name="J.R.R. Tolkien"),
                    ormar.and_(year__lt=2000, author__name="Andrzej Sapkowski"),
                    title__icontains="hobbit",
                )
            )
            .filter(title__startswith="The")
            .all()
        )
        assert len(books) == 3
        assert not any(
            [x.title in ["The Tower of Fools", "The Lord of the Rings"] for x in books]
        )

        books = (
            await Book.objects.select_related("author")
            .filter(ormar.or_(year__gt=1980, year__lt=1910))
            .filter(title__startswith="The")
            .limit(1)
            .all()
        )
        assert len(books) == 1
        assert books[0].title == "The Witcher"

        books = (
            await Book.objects.select_related("author")
            .filter(ormar.or_(year__gt=1980, author__name="Andrzej Sapkowski"))
            .filter(title__startswith="The")
            .limit(1)
            .all()
        )
        assert len(books) == 1
        assert books[0].title == "The Witcher"

        books = (
            await Book.objects.select_related("author")
            .filter(ormar.or_(year__gt=1980, author__name="Andrzej Sapkowski"))
            .filter(title__startswith="The")
            .limit(1)
            .offset(1)
            .all()
        )
        assert len(books) == 1
        assert books[0].title == "The Tower of Fools"

        books = (
            await Book.objects.select_related("author")
            .filter(ormar.or_(year__gt=1980, author__name="Andrzej Sapkowski"))
            .filter(title__startswith="The")
            .limit(1)
            .offset(1)
            .order_by("-id")
            .all()
        )
        assert len(books) == 1
        assert books[0].title == "The Witcher"

        with pytest.raises(QueryDefinitionError):
            await Book.objects.select_related("author").filter("wrong").all()

        books = await tolkien.books.filter(
            ormar.or_(year__lt=1940, year__gt=1960)
        ).all()
        assert len(books) == 2

        books = await tolkien.books.filter(
            ormar.and_(
                ormar.or_(year__lt=1940, year__gt=1960), title__icontains="hobbit"
            )
        ).all()
        assert len(books) == 1
        assert tolkien.books[0].title == "The Hobbit"

        books = (
            await Book.objects.select_related("author")
            .filter(ormar.or_(author__name="J.R.R. Tolkien"))
            .all()
        )
        assert len(books) == 3

        books = (
            await Book.objects.select_related("author")
            .filter(
                ormar.or_(
                    ormar.and_(author__name__icontains="tolkien"),
                    ormar.and_(author__name__icontains="sapkowski"),
                )
            )
            .all()
        )
        assert len(books) == 5
