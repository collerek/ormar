import pytest

import ormar
from ormar.models import Model
from tests.lifespan import init_tests
from tests.settings import create_config

base_ormar_config = create_config()


class Author(Model):
    ormar_config = base_ormar_config.copy(tablename="comment_authors")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=80)


class Tag(Model):
    ormar_config = base_ormar_config.copy(tablename="comment_tags")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=40)


class Comment(Model):
    ormar_config = base_ormar_config.copy(tablename="comments")

    test: int = ormar.Integer(primary_key=True, comment="primary key of comments")
    test_string: str = ormar.String(max_length=250, comment="test that it works")
    author: Author = ormar.ForeignKey(Author, comment="author of the comment")
    tags = ormar.ManyToMany(Tag, comment="tags attached to the comment")


create_test_database = init_tests(base_ormar_config)


@pytest.mark.asyncio
async def test_comments_are_set_in_db():
    columns = Comment.ormar_config.table.c
    for c in columns:
        assert c.comment == Comment.ormar_config.model_fields[c.name].comment


def test_foreign_key_comment_reaches_field_and_column():
    assert (
        Comment.ormar_config.model_fields["author"].comment == "author of the comment"
    )
    assert Comment.ormar_config.table.c.author.comment == "author of the comment"


def test_many_to_many_comment_stored_on_field():
    # M2M has no column on the owner model's table and does not propagate the
    # comment to the through model's columns, so the field attribute is the
    # only observable side effect.
    assert (
        Comment.ormar_config.model_fields["tags"].comment
        == "tags attached to the comment"
    )
    through = Comment.ormar_config.model_fields["tags"].through
    assert all(c.comment is None for c in through.ormar_config.table.c)
