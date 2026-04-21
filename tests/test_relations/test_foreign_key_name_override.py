from typing import Optional

import pytest
import sqlalchemy

import ormar
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="fkn_authors")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class Book(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="fkn_books")

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=100)
    author: Optional[Author] = ormar.ForeignKey(
        Author, foreign_key_name="my_custom_fk_books_author"
    )


class Tag(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="fkn_tags")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=100)


class BookTag(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="fkn_book_tags")

    id: int = ormar.Integer(primary_key=True)


class BookWithTags(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="fkn_books_with_tags")

    id: int = ormar.Integer(primary_key=True)
    title: str = ormar.String(max_length=100)
    tags = ormar.ManyToMany(
        Tag,
        through=BookTag,
        through_foreign_key_name="my_fk_through_to_book",
        through_reverse_foreign_key_name="my_fk_through_to_tag",
    )


create_test_database = init_tests(base_ormar_config)


def _fk_names_for(table: sqlalchemy.Table) -> list:
    names = []
    for col in table.c:
        for fk in col.foreign_keys:
            names.append(fk.name)
    return names


def test_foreign_key_name_overrides_generated_constraint_name():
    names = _fk_names_for(Book.ormar_config.table)
    assert "my_custom_fk_books_author" in names
    assert not any(n.startswith("fk_fkn_books_") for n in names)


def test_foreign_key_name_default_is_generated():
    fk_author = Author.ormar_config.model_fields.get("id")
    assert (
        fk_author.foreign_key_name is None
        if hasattr(fk_author, "foreign_key_name")
        else True
    )

    field = Book.ormar_config.model_fields["author"]
    assert field.foreign_key_name == "my_custom_fk_books_author"


def test_many_to_many_through_foreign_key_name_overrides():
    through_table = BookWithTags.ormar_config.model_fields[
        "tags"
    ].through.ormar_config.table
    names = _fk_names_for(through_table)
    assert "my_fk_through_to_book" in names
    assert "my_fk_through_to_tag" in names


@pytest.mark.asyncio
async def test_model_with_custom_fk_name_still_works_at_runtime():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            author = await Author.objects.create(name="J. Doe")
            book = await Book.objects.create(title="Untitled", author=author)
            fetched = await Book.objects.select_related("author").get(id=book.id)
            assert fetched.author.name == "J. Doe"


@pytest.mark.asyncio
async def test_many_to_many_with_custom_through_fk_names_still_works():
    async with base_ormar_config.database:
        async with base_ormar_config.database.transaction(force_rollback=True):
            tag = await Tag.objects.create(name="scifi")
            book = await BookWithTags.objects.create(title="Dune")
            await book.tags.add(tag)
            fetched = await BookWithTags.objects.select_related("tags").get(id=book.id)
            assert len(fetched.tags) == 1
            assert fetched.tags[0].name == "scifi"
